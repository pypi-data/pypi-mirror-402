"""Lucene query string converter for OpenSearch backend.

This module handles conversion of TQL AST to Lucene query strings.
"""

from typing import Any, Dict, Optional, Tuple

from ..exceptions import TQLUnsupportedOperationError, TQLValidationError
from .field_mapping import FieldMapping


class LuceneConverter:
    """Handles conversion of TQL AST to Lucene query strings."""

    def __init__(self, field_mappings: Dict[str, FieldMapping], simple_mappings: Dict[str, str]):
        """Initialize Lucene converter.

        Args:
            field_mappings: Intelligent field mappings
            simple_mappings: Simple field name mappings
        """
        self.intelligent_mappings = field_mappings
        self.simple_mappings = simple_mappings

    def convert_lucene(self, ast: Dict[str, Any]) -> str:
        """Convert a TQL AST to Lucene query string."""
        return self._convert_node_to_lucene(ast)

    def _convert_node_to_lucene(self, node: Any) -> str:
        """Convert a single AST node to Lucene query string."""
        if isinstance(node, dict):
            node_type = node.get("type")

            if node_type == "match_all":
                # Empty query matches all documents in Lucene
                return "*:*"
            elif node_type == "comparison":
                return self._convert_comparison_to_lucene(node)
            elif node_type == "logical_op":
                return self._convert_logical_op_to_lucene(node)
            elif node_type == "unary_op":
                return self._convert_unary_op_to_lucene(node)
            elif node_type == "collection_op":
                return self._convert_collection_op_to_lucene(node)
            elif node_type == "query_with_stats":
                # For query_with_stats, only convert the filter part to Lucene
                # The stats part is handled by the stats engine
                filter_node = node.get("filter")
                if filter_node:
                    return self._convert_node_to_lucene(filter_node)
                else:
                    return "*:*"
            elif node_type == "stats_expr":
                # Pure stats queries match all documents in Lucene
                # The aggregations are handled by the stats engine
                return "*:*"

        raise TQLValidationError(f"Unknown node type: {node}")

    def _convert_comparison_to_lucene(self, node: Dict[str, Any]) -> str:  # noqa: C901
        """Convert a comparison operation to Lucene query string."""
        field_name = node["field"]
        operator = node["operator"]
        value = node["value"]

        # Get the actual field name to use (could be enhanced to extract analyzer from query context)
        lucene_field, use_wildcard = self._resolve_field_name(field_name, operator)

        # Escape special characters in values
        if isinstance(value, str):
            escaped_value = self._escape_lucene_value(value)
        else:
            escaped_value = str(value)

        # Handle special wildcard conversion for keyword fields
        if use_wildcard and operator == "contains":
            return f"{lucene_field}:*{escaped_value}*"

        # Convert operator to Lucene syntax
        if operator in ["eq", "="]:
            return f"{lucene_field}:{escaped_value}"
        elif operator in ["ne", "!="]:
            return f"NOT {lucene_field}:{escaped_value}"
        elif operator in ["gt", ">"]:
            return f"{lucene_field}:>{escaped_value}"
        elif operator in ["gte", ">="]:
            return f"{lucene_field}:>={escaped_value}"
        elif operator in ["lt", "<"]:
            return f"{lucene_field}:<{escaped_value}"
        elif operator in ["lte", "<="]:
            return f"{lucene_field}:<={escaped_value}"
        elif operator == "contains":
            if use_wildcard:
                return f"{lucene_field}:*{escaped_value}*"
            else:
                # For text fields, use quoted phrase
                return f'{lucene_field}:"{escaped_value}"'
        elif operator == "startswith":
            return f"{lucene_field}:{escaped_value}*"
        elif operator == "endswith":
            return f"{lucene_field}:*{escaped_value}"
        elif operator == "in":
            if isinstance(value, list):
                escaped_values = [self._escape_lucene_value(str(v)) for v in value]
                return f"{lucene_field}:({' OR '.join(escaped_values)})"
            else:
                return f"{lucene_field}:{escaped_value}"
        elif operator == "regexp":
            return f"{lucene_field}:/{escaped_value}/"
        elif operator == "exists":
            return f"_exists_:{lucene_field}"
        elif operator == "is":
            if value is None:
                return f"NOT _exists_:{lucene_field}"
            else:
                return f"{lucene_field}:{escaped_value}"
        elif operator == "between":
            if isinstance(value, list) and len(value) == 2:
                # Convert values to appropriate types
                val1 = self._convert_value(value[0])
                val2 = self._convert_value(value[1])

                # Allow values in any order
                lower = (
                    min(val1, val2) if isinstance(val1, (int, float)) and isinstance(val2, (int, float)) else value[0]
                )
                upper = (
                    max(val1, val2) if isinstance(val1, (int, float)) and isinstance(val2, (int, float)) else value[1]
                )

                # For non-numeric values (like dates), we use the original order if we can't determine min/max
                if not isinstance(val1, (int, float)) or not isinstance(val2, (int, float)):
                    try:
                        # If values can be compared (like strings), try to determine order
                        if val1 > val2:
                            lower, upper = val2, val1
                        else:
                            lower, upper = val1, val2
                    except TypeError:
                        # If comparison fails, use the original order
                        lower, upper = value[0], value[1]

                return f"{lucene_field}:[{lower} TO {upper}]"
            else:
                raise TQLValidationError(f"Between operator requires a list with two values, got: {value}")
        elif operator == "cidr":
            return f"{lucene_field}:{escaped_value}"
        else:
            raise TQLUnsupportedOperationError(f"Operator '{operator}' not supported for Lucene")

    def _convert_logical_op_to_lucene(self, node: Dict[str, Any]) -> str:
        """Convert a logical operation to Lucene query string."""
        operator = node["operator"]
        left_query = self._convert_node_to_lucene(node["left"])
        right_query = self._convert_node_to_lucene(node["right"])

        if operator == "and":
            return f"({left_query}) AND ({right_query})"
        elif operator == "or":
            return f"({left_query}) OR ({right_query})"
        else:
            raise TQLUnsupportedOperationError(f"Logical operator '{operator}' not supported for Lucene")

    def _convert_unary_op_to_lucene(self, node: Dict[str, Any]) -> str:
        """Convert a unary operation to Lucene query string."""
        operator = node["operator"]
        operand_query = self._convert_node_to_lucene(node["operand"])

        if operator == "not":
            return f"NOT ({operand_query})"
        else:
            raise TQLUnsupportedOperationError(f"Unary operator '{operator}' not supported for Lucene")

    def _convert_collection_op_to_lucene(self, node: Dict[str, Any]) -> str:  # noqa: C901
        """Convert a collection operation to Lucene query string."""
        operator = node["operator"]
        field_name = node["field"]
        comparison_operator = node["comparison_operator"]
        value = node["value"]

        # Get the actual field name to use
        lucene_field, use_wildcard = self._resolve_field_name(field_name, comparison_operator)

        # Convert value
        if isinstance(value, str):
            escaped_value = self._escape_lucene_value(value)
        else:
            escaped_value = str(value)

        # Build the appropriate comparison based on the operator
        if comparison_operator in ["eq", "="]:
            comparison = f"{lucene_field}:{escaped_value}"
        elif comparison_operator in ["ne", "!="]:
            comparison = f"NOT {lucene_field}:{escaped_value}"
        elif comparison_operator in ["gt", ">"]:
            comparison = f"{lucene_field}:>{escaped_value}"
        elif comparison_operator in ["gte", ">="]:
            comparison = f"{lucene_field}:>={escaped_value}"
        elif comparison_operator in ["lt", "<"]:
            comparison = f"{lucene_field}:<{escaped_value}"
        elif comparison_operator in ["lte", "<="]:
            comparison = f"{lucene_field}:<={escaped_value}"
        elif comparison_operator == "contains":
            if use_wildcard:
                comparison = f"{lucene_field}:*{escaped_value}*"
            else:
                comparison = f'{lucene_field}:"{escaped_value}"'
        elif comparison_operator == "startswith":
            comparison = f"{lucene_field}:{escaped_value}*"
        elif comparison_operator == "endswith":
            comparison = f"{lucene_field}:*{escaped_value}"
        elif comparison_operator == "regexp":
            comparison = f"{lucene_field}:/{escaped_value}/"
        elif comparison_operator == "in":
            if isinstance(value, list):
                escaped_values = [self._escape_lucene_value(str(v)) for v in value]
                comparison = f"{lucene_field}:({' OR '.join(escaped_values)})"
            else:
                comparison = f"{lucene_field}:{escaped_value}"
        else:
            raise TQLUnsupportedOperationError(
                f"Operator '{comparison_operator}' not supported for collection operators in Lucene"
            )

        # For ANY, this is straightforward - we're checking if any element matches
        if operator == "any":
            return comparison
        # For ALL, we need to negate the negated comparison
        elif operator == "all":
            # Not(Not(comparison)) is semantically equivalent to requiring ALL elements match
            return f"NOT (_exists_:{lucene_field} AND NOT ({comparison}))"
        else:
            raise TQLUnsupportedOperationError(f"Collection operator '{operator}' not supported for Lucene")

    def _escape_lucene_value(self, value: str) -> str:
        """Escape special characters in Lucene query values."""
        # Lucene special characters: + - = && || > < ! ( ) { } [ ] ^ " ~ * ? : \ /
        special_chars = [
            "+",
            "-",
            "=",
            "&",
            "|",
            ">",
            "<",
            "!",
            "(",
            ")",
            "{",
            "}",
            "[",
            "]",
            "^",
            '"',
            "~",
            "*",
            "?",
            ":",
            "\\",
            "/",
        ]

        escaped = value
        for char in special_chars:
            escaped = escaped.replace(char, f"\\{char}")

        # Quote the value if it contains spaces
        if " " in escaped:
            escaped = f'"{escaped}"'

        return escaped

    def _resolve_field_name(
        self, field_name: str, operator: str, preferred_analyzer: Optional[str] = None
    ) -> Tuple[str, bool]:
        """Resolve field name based on mappings and operator.

        Args:
            field_name: The TQL field name
            operator: The operator being used
            preferred_analyzer: Preferred analyzer for text operations

        Returns:
            Tuple of (resolved_field_name, use_wildcard_conversion)
        """
        # Check intelligent mappings first
        if field_name in self.intelligent_mappings:
            field_mapping = self.intelligent_mappings[field_name]
            resolved_field = field_mapping.get_field_for_operator(operator, preferred_analyzer)
            use_wildcard = field_mapping.needs_wildcard_conversion(operator, preferred_analyzer)
            # If resolved field is empty, use the original field name
            if not resolved_field:
                resolved_field = field_name
            return resolved_field, use_wildcard

        # Check simple mappings
        elif field_name in self.simple_mappings:
            return self.simple_mappings[field_name], False

        # No mapping, use field name as-is
        else:
            return field_name, False

    def _convert_value(self, value: Any) -> Any:
        """Convert value types for Lucene compatibility.

        Args:
            value: Value to convert

        Returns:
            Converted value (bool, None, or original)
        """
        if isinstance(value, str):
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
            elif value.lower() == "null":
                return None
        return value
