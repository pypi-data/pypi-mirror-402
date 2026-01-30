"""Validation operations for TQL.

This module handles query validation, type checking, and performance analysis.
"""

from typing import Any, Dict, List, Optional

from ..exceptions import TQLFieldError, TQLTypeError, TQLValidationError
from ..parser import TQLParser


class ValidationOperations:
    """Handles validation operations for TQL."""

    def __init__(self, parser: TQLParser, field_mappings: Dict[str, Any]):
        """Initialize validation operations.

        Args:
            parser: TQL parser instance
            field_mappings: Field mapping configuration
        """
        self.parser = parser
        self.field_mappings = field_mappings

    def validate(self, query: str, validate_fields: bool = False) -> bool:
        """Validate a TQL query for syntax and optionally field names.

        Args:
            query: TQL query string
            validate_fields: Whether to validate field names against mappings

        Returns:
            True if query is valid

        Raises:
            Various TQL exceptions if validation fails
        """
        # Parse the query
        ast = self.parser.parse(query)

        # Validate field names if requested
        if validate_fields:
            self._validate_fields_in_ast(ast)

        # Always check type compatibility
        self._check_type_compatibility(ast)

        return True

    def _validate_fields_in_ast(self, ast: Dict[str, Any]) -> None:
        """Recursively validate field names in AST against field mappings."""
        if isinstance(ast, dict):
            if ast.get("type") == "comparison" and "field" in ast:
                field = ast["field"]
                if field not in self.field_mappings:
                    raise TQLFieldError(field=field, available_fields=sorted(self.field_mappings.keys()))
            elif ast.get("type") == "logical_op":
                left = ast.get("left")
                right = ast.get("right")
                if left:
                    self._validate_fields_in_ast(left)
                if right:
                    self._validate_fields_in_ast(right)
            elif ast.get("type") == "unary_op":
                operand = ast.get("operand")
                if operand:
                    self._validate_fields_in_ast(operand)

    def _check_type_compatibility(self, ast: Dict[str, Any]) -> None:  # noqa: C901
        """Check type compatibility between fields, operators, and values.

        Args:
            ast: The AST to validate

        Raises:
            TQLTypeError: If type incompatibilities are found
            TQLOperatorError: If operators are used incorrectly
        """
        if not isinstance(ast, dict):
            return

        node_type = ast.get("type")

        if node_type == "comparison":
            field = ast.get("field")
            operator = ast.get("operator")
            value = ast.get("value")
            type_hint = ast.get("type_hint")

            # Only proceed if we have required fields
            if not field or not operator:
                return

            # Handle multi-field scenarios first (for 'in' operator with field list)
            if operator == "in" and isinstance(ast.get("original_fields"), list):
                # This is a "value in [field1, field2, ...]" that was expanded
                # Check each field's type
                for check_field in ast.get("original_fields", [field]):
                    field_info = self.field_mappings.get(check_field, {})
                    if field_info:
                        self._validate_comparison_for_field(check_field, field_info, operator, value, type_hint)
                return

            # Get field type from mappings
            field_info = self.field_mappings.get(field, {})
            if field_info:
                self._validate_comparison_for_field(field, field_info, operator, value, type_hint)

        elif node_type == "logical_op":
            left = ast.get("left")
            right = ast.get("right")
            if left:
                self._check_type_compatibility(left)
            if right:
                self._check_type_compatibility(right)

        elif node_type == "unary_op":
            operand = ast.get("operand")
            if operand:
                self._check_type_compatibility(operand)

        elif node_type == "query_with_stats":
            if "filter" in ast:
                self._check_type_compatibility(ast["filter"])

    def _validate_comparison_for_field(  # noqa: C901
        self, field: str, field_info: Any, operator: str, value: Any, type_hint: Optional[str]
    ) -> None:
        """Validate a comparison for a specific field.

        Args:
            field: Field name
            field_info: Field mapping information
            operator: Comparison operator
            value: Comparison value
            type_hint: Optional type hint from query
        """
        # Determine the field type
        field_type: Optional[str] = None
        if isinstance(field_info, str):
            # Simple mapping: could be a field name or a type
            if field_info in [
                "keyword",
                "text",
                "long",
                "integer",
                "short",
                "byte",
                "double",
                "float",
                "boolean",
                "date",
                "ip",
            ]:
                field_type = field_info
            else:
                # It's a mapped field name, we don't know the type
                return
        elif isinstance(field_info, dict):
            # Complex mapping
            field_type = field_info.get("type")
            if not field_type:
                # Check if it's an OpenSearch-style mapping with nested field definition
                # e.g., {"message": {"type": "text", "analyzer": "standard"}}
                if field in field_info and isinstance(field_info[field], dict):
                    field_type = field_info[field].get("type")
                # Check if it's a multi-field mapping
                elif "fields" in field_info:
                    # Multi-field, check the main field type
                    field_type = field_info.get("type", "text")
                else:
                    # No type info available
                    return
        else:
            # No type info available
            return

        # Apply type hint override if provided
        if type_hint and field_type:
            self._validate_type_hint_compatibility(field, field_type, type_hint)
            # Use the type hint for validation
            validation_type = self._map_type_hint_to_es_type(type_hint)
        else:
            validation_type = field_type

        # Validate based on field type
        if validation_type:
            self._validate_simple_type_compatibility(field, validation_type, operator)

        # Additional validation for type mismatches
        # Check if we're using comparison operators with incompatible value types
        if validation_type in ["text", "keyword"] and operator in [">", "<", ">=", "<=", "gt", "lt", "gte", "lte"]:
            # String comparison operators require string values
            # Check if value looks like a number (parser returns all values as strings)
            if isinstance(value, str) and value.replace(".", "", 1).replace("-", "", 1).isdigit():
                raise TQLTypeError(
                    field=field,
                    field_type=validation_type,
                    operator=operator,
                    suggestions=["Use a string value for comparison, or use a numeric field"],
                )

    def _validate_type_hint_compatibility(self, field: str, field_type: str, type_hint: str) -> None:
        """Validate that a type hint is compatible with the field's actual type."""
        # Map type hints to ES types
        hint_es_type = self._map_type_hint_to_es_type(type_hint)

        # Check compatibility
        compatible = False

        # Numeric types can be cast between each other
        numeric_types = {"long", "integer", "short", "byte", "double", "float"}
        if field_type in numeric_types and hint_es_type in numeric_types:
            compatible = True
        # String types
        elif field_type in {"text", "keyword"} and hint_es_type in {"text", "keyword"}:
            compatible = True
        # Boolean
        elif field_type == "boolean" and hint_es_type == "boolean":
            compatible = True
        # Date
        elif field_type == "date" and hint_es_type == "date":
            compatible = True
        # IP
        elif field_type == "ip" and hint_es_type == "ip":
            compatible = True
        # Geo point
        elif field_type == "geo_point" and hint_es_type == "geo_point":
            compatible = True
        # Object/nested
        elif field_type in {"object", "nested"} and hint_es_type == "object":
            compatible = True

        if not compatible:
            # Use TQLValidationError instead since TQLTypeError requires operator
            raise TQLValidationError(
                f"Type hint '{type_hint}' is incompatible with field '{field}' of type '{field_type}'"
            )

    def _map_type_hint_to_es_type(self, type_hint: str) -> str:
        """Map TQL type hints to Elasticsearch/OpenSearch types."""
        mapping = {
            "number": "double",
            "int": "long",
            "float": "double",
            "decimal": "double",
            "string": "keyword",
            "text": "text",
            "bool": "boolean",
            "boolean": "boolean",
            "date": "date",
            "array": "keyword",  # Arrays don't have a specific type
            "geo": "geo_point",
            "object": "object",
            "ip": "ip",
        }
        return mapping.get(type_hint.lower(), "keyword")

    def _validate_simple_type_compatibility(self, field: str, field_type: str, operator: str) -> None:
        """Validate operator compatibility with field type.

        Args:
            field: Field name for error messages
            field_type: The field's data type
            operator: The operator being used

        Raises:
            TQLOperatorError: If operator is incompatible with field type
        """
        # Define operator compatibility by type
        numeric_ops = {
            "eq",
            "=",
            "ne",
            "!=",
            "gt",
            ">",
            "gte",
            ">=",
            "lt",
            "<",
            "lte",
            "<=",
            "between",
            "not_between",
            "in",
            "not_in",
            "exists",
            "not_exists",
        }

        # Text fields (analyzed) should not use range operators
        text_ops = {
            "eq",
            "=",
            "ne",
            "!=",
            "contains",
            "not_contains",
            "startswith",
            "not_startswith",
            "endswith",
            "not_endswith",
            "regexp",
            "not_regexp",
            "in",
            "not_in",
            "exists",
            "not_exists",
        }

        # Keyword fields can use range operators for lexicographic comparison
        keyword_ops = {
            "eq",
            "=",
            "ne",
            "!=",
            "contains",
            "not_contains",
            "startswith",
            "not_startswith",
            "endswith",
            "not_endswith",
            "regexp",
            "not_regexp",
            "in",
            "not_in",
            "exists",
            "not_exists",
            "gt",
            ">",
            "gte",
            ">=",
            "lt",
            "<",
            "lte",
            "<=",
        }

        boolean_ops = {"eq", "=", "ne", "!=", "exists", "not_exists", "is", "is_not"}

        date_ops = {
            "eq",
            "=",
            "ne",
            "!=",
            "gt",
            ">",
            "gte",
            ">=",
            "lt",
            "<",
            "lte",
            "<=",
            "between",
            "not_between",
            "exists",
            "not_exists",
        }

        ip_ops = {"eq", "=", "ne", "!=", "cidr", "not_cidr", "in", "not_in", "exists", "not_exists"}

        # Determine allowed operators based on type
        if field_type in ["long", "integer", "short", "byte", "double", "float"]:
            allowed_ops = numeric_ops
            # type_desc = "numeric"  # Not used
        elif field_type == "text":
            allowed_ops = text_ops
            # type_desc = "text"  # Not used
        elif field_type == "keyword":
            allowed_ops = keyword_ops
            # type_desc = "keyword"  # Not used
        elif field_type == "boolean":
            allowed_ops = boolean_ops
            # type_desc = "boolean"  # Not used
        elif field_type == "date":
            allowed_ops = date_ops
            # type_desc = "date"  # Not used
        elif field_type == "ip":
            allowed_ops = ip_ops
            # type_desc = "IP"  # Not used
        else:
            # Unknown type, allow all operators
            return

        # Check if operator is allowed
        if operator not in allowed_ops:
            # Create validation error with proper message
            if field_type == "text" and operator in ["gt", ">", "gte", ">=", "lt", "<", "lte", "<="]:
                pass  # Error will be raised with proper message below
            else:
                pass  # Error will be raised with proper message below

            # Use TQLTypeError since it's about operator-field type compatibility
            raise TQLTypeError(field=field, field_type=field_type, operator=operator, valid_operators=list(allowed_ops))

    def check_performance_issues(self, ast: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Check for potential performance issues in the query.

        Args:
            ast: Parsed AST
            query: Original query string

        Returns:
            List of performance issues found
        """
        issues: List[Dict[str, Any]] = []
        self._traverse_ast_for_performance(ast, issues, query)
        return issues

    def _traverse_ast_for_performance(  # noqa: C901
        self, node: Dict[str, Any], issues: List[Dict[str, Any]], query: str
    ) -> None:
        """Traverse AST looking for performance issues."""
        if not isinstance(node, dict):
            return

        node_type = node.get("type")

        if node_type == "comparison":
            operator = node.get("operator")
            field = node.get("field")
            value = node.get("value", "")

            # Skip if no field or operator
            if not field or not operator:
                return

            # Check for expensive operations
            if operator in ["regexp", "not_regexp"]:
                # Format query part
                query_part = f"{field} {operator}"
                if isinstance(value, str):
                    # Remove quotes from value for display
                    clean_value = value.strip("\"'")
                    query_part = f"{field} {operator} {clean_value}"

                issues.append(
                    {
                        "type": "expensive_operator",
                        "severity": "warning",
                        "field": field,
                        "operator": operator,
                        "query_part": query_part,
                        "message": "Regular expression (Lucene syntax) operations can be slow on large datasets",
                        "suggestion": "Consider using 'contains' or 'startswith' if possible",
                    }
                )

            # Check for wildcard patterns
            if operator in ["=", "eq", "!=", "ne"] and isinstance(value, str):
                # Check for leading wildcard
                if value.startswith("*"):
                    # Only flag for text fields
                    field_type = self._get_field_type(field)
                    if field_type in ["text", "keyword", None]:  # None means unknown type
                        # Format query part similar to regexp
                        clean_value = value.strip("\"'")
                        query_part = f"{field} {operator} {clean_value}"
                        issues.append(
                            {
                                "type": "leading_wildcard",
                                "severity": "warning",
                                "field": field,
                                "operator": operator,
                                "query_part": query_part,
                                "message": "Leading wildcard in search field can be slow",
                                "suggestion": "Consider using a different search pattern if possible",
                            }
                        )

                # Check for fuzzy search
                if "~" in value:
                    # Extract fuzzy distance
                    parts = value.split("~")
                    if len(parts) == 2 and parts[1].isdigit():
                        distance = int(parts[1])
                        if distance > 2:
                            issues.append(
                                {
                                    "type": "high_fuzzy_distance",
                                    "severity": "warning",
                                    "field": field,
                                    "operator": operator,
                                    "message": f"Fuzzy query with distance {distance} can be expensive",
                                    "suggestion": "Consider using fuzzy distance <= 2 for better performance",
                                }
                            )

            # Check for collection operations on high cardinality fields
            if operator in ["any", "all"] and field in self.field_mappings:
                field_info = self.field_mappings[field]
                # Assume keyword fields could be high cardinality
                if isinstance(field_info, str) and field_info == "keyword":
                    issues.append(
                        {
                            "type": "collection_operation_high_cardinality",
                            "severity": "warning",
                            "field": field,
                            "operator": operator,
                            "message": f"Collection operator '{operator}' on potentially high cardinality field",
                            "suggestion": "Ensure the field has reasonable cardinality for collection operations",
                        }
                    )

            # Check for negated operations on text fields
            if isinstance(operator, str) and operator.startswith("not_") and field in self.field_mappings:
                field_info = self.field_mappings[field]
                if isinstance(field_info, dict) and field_info.get("type") == "text":
                    issues.append(
                        {
                            "type": "negated_text_search",
                            "severity": "warning",
                            "field": field,
                            "operator": operator,
                            "message": "Negated operations on text fields can be inefficient",
                            "suggestion": "Consider restructuring the query to use positive matches",
                        }
                    )

        elif node_type == "logical_op":
            # Check for deeply nested OR operations
            or_depth = self._count_or_depth(node)
            if or_depth > 3:
                issues.append(
                    {
                        "type": "deep_or_nesting",
                        "severity": "warning",
                        "depth": or_depth,
                        "message": f"Query has {or_depth} levels of OR operations which can impact performance",
                        "suggestion": "Consider simplifying the query or using terms queries",
                    }
                )

            # Recurse
            left = node.get("left")
            right = node.get("right")
            if left:
                self._traverse_ast_for_performance(left, issues, query)
            if right:
                self._traverse_ast_for_performance(right, issues, query)

        elif node_type == "unary_op":
            operand = node.get("operand")
            if operand:
                self._traverse_ast_for_performance(operand, issues, query)

    def _count_or_depth(self, node: Dict[str, Any], current_depth: int = 0) -> int:
        """Count the maximum depth of OR operations."""
        if not isinstance(node, dict):
            return current_depth

        if node.get("type") == "logical_op" and node.get("operator") == "or":
            left = node.get("left")
            right = node.get("right")
            left_depth = self._count_or_depth(left, current_depth + 1) if left else current_depth
            right_depth = self._count_or_depth(right, current_depth + 1) if right else current_depth
            return max(left_depth, right_depth)

        return current_depth

    def _get_field_type(self, field: str) -> Optional[str]:
        """Get the type of a field from mappings.

        Args:
            field: Field name

        Returns:
            Field type or None if unknown
        """
        if field not in self.field_mappings:
            return None

        field_info = self.field_mappings[field]

        if isinstance(field_info, str):
            # Simple type string
            if field_info in [
                "keyword",
                "text",
                "long",
                "integer",
                "short",
                "byte",
                "double",
                "float",
                "boolean",
                "date",
                "ip",
            ]:
                return field_info
            else:
                # It's a field name mapping, we don't know the type
                return None
        elif isinstance(field_info, dict):
            # Complex mapping - try to get type
            return field_info.get("type")

        return None
