"""Query conversion logic for OpenSearch backend.

This module handles the conversion of TQL AST nodes to OpenSearch Query DSL.
"""

from typing import Any, Dict, List, Optional

from ..exceptions import TQLUnsupportedOperationError, TQLValidationError
from .field_mapping import FieldMapping


class QueryConverter:
    """Handles conversion of TQL AST to OpenSearch Query DSL."""

    def __init__(self, field_mappings: Dict[str, FieldMapping], simple_mappings: Dict[str, str]):
        """Initialize query converter.

        Args:
            field_mappings: Intelligent field mappings
            simple_mappings: Simple field name mappings
        """
        self.intelligent_mappings = field_mappings
        self.simple_mappings = simple_mappings

    def convert_node(self, node: Any) -> Dict[str, Any]:  # noqa: C901
        """Convert a single AST node to OpenSearch query fragment."""
        if isinstance(node, dict):
            node_type = node.get("type")

            if node_type == "match_all":
                # Empty query matches all documents
                return {"match_all": {}}
            elif node_type == "comparison":
                return self._convert_comparison(node)
            elif node_type == "logical_op":
                return self._convert_logical_op(node)
            elif node_type == "unary_op":
                return self._convert_unary_op(node)
            elif node_type == "collection_op":
                return self._convert_collection_op(node)
            elif node_type == "geo_expr":
                return self._convert_geo_expr(node)
            elif node_type == "nslookup_expr":
                return self._convert_nslookup_expr(node)
            elif node_type == "query_with_stats":
                # For query_with_stats, only convert the filter part
                # The stats part is handled by the stats engine
                filter_node = node.get("filter")
                if filter_node:
                    return self.convert_node(filter_node)
                else:
                    return {"match_all": {}}
            elif node_type == "stats_expr":
                # Pure stats queries match all documents
                # The aggregations are handled by the stats engine
                return {"match_all": {}}

        raise TQLValidationError(f"Unknown node type: {node}")

    def _get_effective_field_type(self, field_name: str, mutators: List[Dict[str, Any]]) -> Optional[str]:
        """Determine the effective field type after applying mutators.

        Args:
            field_name: Original field name
            mutators: List of mutators applied to the field

        Returns:
            The effective field type after mutator transformations, or None if unchanged
        """
        if not mutators:
            return None

        # Define mutators that change field types
        type_changing_mutators = {
            "length": "integer",  # Returns integer count
            "avg": "float",  # Returns float average
            "average": "float",  # Alias for avg
            "sum": "float",  # Returns numeric sum
            "max": "float",  # Returns maximum value
            "min": "float",  # Returns minimum value
            "any": "boolean",  # Returns boolean
            "all": "boolean",  # Returns boolean
            "is_private": "boolean",  # Returns boolean
            "is_global": "boolean",  # Returns boolean
        }

        # Check mutators from left to right to find final type
        for mutator in mutators:
            mutator_name = mutator.get("name", "").lower()
            if mutator_name in type_changing_mutators:
                return type_changing_mutators[mutator_name]
            elif mutator_name == "split":
                # Split converts to array, but we need to know what comes after
                continue

        return None

    def _convert_comparison(self, node: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
        """Convert a comparison operation to OpenSearch query."""
        field_name = node["field"]
        operator = node["operator"]
        # For exists/not_exists operators, value is None
        value = node.get("value") if operator not in ["exists", "not_exists"] else None
        field_mutators = node.get("field_mutators", [])

        # Check if mutators change the field type
        effective_field_type = self._get_effective_field_type(field_name, field_mutators)

        # Check if field has mutators that will be post-processed
        has_post_process_mutators = bool(field_mutators)

        # Check if node has type-changing mutators (marked by mutator analyzer)
        has_type_changing_mutators = node.get("has_type_changing_mutators", False)

        # Check for intelligent mappings and validate type compatibility
        if (
            field_name in self.intelligent_mappings
            and effective_field_type is None
            and not has_post_process_mutators
            and not has_type_changing_mutators
        ):
            # Only validate original field type if no type-changing mutators and no post-processing
            mapping = self.intelligent_mappings[field_name]
            # This will raise TQLTypeError if incompatible
            mapping.validate_operator_for_field_type(operator)

        # Get the actual field name to use (could be enhanced to extract analyzer from query context)
        # For type-changing mutators, bypass field resolution since the field type doesn't matter
        if has_type_changing_mutators:
            # Just use the field name as-is since it will be post-processed
            opensearch_field = field_name
            use_wildcard = False
        else:
            opensearch_field, use_wildcard = self._resolve_field_name(field_name, operator)

        # Convert value types for OpenSearch
        value = self._convert_value(value)

        # Check if this comparison requires post-processing due to value mutators or type-changing mutators
        # Note: ALL and NOT_ALL operators are handled with script queries and don't need post-processing
        requires_post_processing = node.get("post_process_value", False) or has_type_changing_mutators

        # Also check if we have transform mutators with filtering operators
        # Transform mutators change the field value, so we need to use exists query
        has_transform_mutators_with_filter = node.get("has_transform_mutators_with_filter", False)

        # Also check field_mutators directly in case the flag wasn't set
        if (
            not has_transform_mutators_with_filter
            and field_mutators
            and operator
            in [
                "eq",
                "=",
                "ne",
                "!=",
                "contains",
                "not_contains",
                "startswith",
                "endswith",
                "not_startswith",
                "not_endswith",
                ">",
                ">=",
                "<",
                "<=",
                "gt",
                "gte",
                "lt",
                "lte",
                "between",
                "not_between",
            ]
        ):
            # Check if any of the mutators are transform mutators
            TRANSFORM_MUTATORS = {
                "lowercase",
                "uppercase",
                "trim",
                "replace",
                "refang",
                "defang",
                "b64encode",
                "b64decode",
                "urldecode",
            }
            for mutator in field_mutators:
                if mutator.get("name", "").lower() in TRANSFORM_MUTATORS:
                    has_transform_mutators_with_filter = True
                    break

        if requires_post_processing or has_transform_mutators_with_filter:
            # For value mutators, type-changing field mutators, or transform mutators that require post-processing, use exists query
            # But NOT for field mutators like any/all/none - those should not affect the query
            if node.get("value_mutators") or has_type_changing_mutators or has_transform_mutators_with_filter:
                # Only for these mutators do we need to broaden the search
                if operator in [
                    "eq",
                    "=",
                    "ne",
                    "!=",
                    "contains",
                    "not_contains",
                    "startswith",
                    "endswith",
                    "not_startswith",
                    "not_endswith",
                    ">",
                    ">=",
                    "<",
                    "<=",
                    "gt",
                    "gte",
                    "lt",
                    "lte",
                    "between",
                    "not_between",
                ]:
                    # For these operators with mutators, use exists query to get all docs with the field
                    # The actual filtering will happen in post-processing
                    return {"exists": {"field": opensearch_field}}

        # Handle special wildcard conversion for keyword fields
        if use_wildcard and operator == "contains":
            return {"wildcard": {opensearch_field: f"*{value}*"}}

        # Convert operator to OpenSearch query
        if operator in ["eq", "="]:
            # For fields with mappings, use the optimized query type
            if field_name in self.intelligent_mappings or field_name in self.simple_mappings:
                # Check if we're using a text field
                is_text_field = self._is_text_field(field_name, opensearch_field)
                if is_text_field:
                    return {"match": {opensearch_field: value}}
                else:
                    return {"term": {opensearch_field: value}}
            else:
                # For unmapped fields, use match_phrase for strings (safer default)
                # This ensures compatibility with both text and keyword fields
                if isinstance(value, str):
                    return {"match_phrase": {opensearch_field: value}}
                else:
                    # For non-string values (numbers, booleans), use term query
                    return {"term": {opensearch_field: value}}
        elif operator in ["ne", "!="]:
            # For fields with mappings, use the optimized query type
            if field_name in self.intelligent_mappings or field_name in self.simple_mappings:
                # Check if we're using a text field
                is_text_field = self._is_text_field(field_name, opensearch_field)
                if is_text_field:
                    return {"bool": {"must_not": {"match": {opensearch_field: value}}}}
                else:
                    return {"bool": {"must_not": {"term": {opensearch_field: value}}}}
            else:
                # For unmapped fields, use match_phrase for strings (safer default)
                if isinstance(value, str):
                    return {"bool": {"must_not": {"match_phrase": {opensearch_field: value}}}}
                else:
                    # For non-string values (numbers, booleans), use term query
                    return {"bool": {"must_not": {"term": {opensearch_field: value}}}}
        elif operator in ["gt", ">"]:
            return {"range": {opensearch_field: {"gt": value}}}
        elif operator in ["gte", ">="]:
            return {"range": {opensearch_field: {"gte": value}}}
        elif operator in ["lt", "<"]:
            return {"range": {opensearch_field: {"lt": value}}}
        elif operator in ["lte", "<="]:
            return {"range": {opensearch_field: {"lte": value}}}
        elif operator == "contains":
            # Unwrap single-element lists for string operators
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            if use_wildcard:
                # Keyword field needs wildcard conversion
                return {"wildcard": {opensearch_field: f"*{value}*"}}
            else:
                # For unmapped fields or when we have a text field, decide based on context
                # If we have intelligent mapping and selected a text field, use match
                # Otherwise default to wildcard for broader compatibility
                if field_name in self.intelligent_mappings:
                    # Use match query for text fields in intelligent mappings
                    return {"match": {opensearch_field: value}}
                else:
                    # Default to wildcard for unmapped fields
                    return {"wildcard": {opensearch_field: f"*{value}*"}}
        elif operator == "startswith":
            # Unwrap single-element lists for string operators
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            # For text fields, use wildcard query as prefix doesn't work well with analyzed text
            if field_name in self.intelligent_mappings:
                field_mapping = self.intelligent_mappings[field_name]
                if isinstance(field_mapping, FieldMapping):
                    # Check if we're using a text field
                    selected_field = field_mapping.get_field_for_operator(operator)
                    if selected_field in field_mapping.text_fields.values():
                        # Use wildcard for analyzed text fields with lowercase value
                        # Text analyzers typically lowercase the text
                        return {"wildcard": {opensearch_field: f"{value.lower()}*"}}
            return {"prefix": {opensearch_field: value}}
        elif operator == "endswith":
            # Unwrap single-element lists for string operators
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            # For text fields, lowercase the value as text analyzers typically lowercase
            if field_name in self.intelligent_mappings:
                field_mapping = self.intelligent_mappings[field_name]
                if isinstance(field_mapping, FieldMapping):
                    selected_field = field_mapping.get_field_for_operator(operator)
                    if selected_field in field_mapping.text_fields.values():
                        return {"wildcard": {opensearch_field: f"*{value.lower()}"}}
            return {"wildcard": {opensearch_field: f"*{value}"}}
        elif operator == "in":
            if isinstance(value, list):
                return {"terms": {opensearch_field: value}}
            else:
                return {"term": {opensearch_field: value}}
        elif operator == "regexp":
            # Unwrap single-element lists for string operators
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            return {"regexp": {opensearch_field: value}}
        elif operator == "exists":
            return {"exists": {"field": opensearch_field}}
        elif operator == "is":
            if value is None:
                return {"bool": {"must_not": {"exists": {"field": opensearch_field}}}}
            else:
                return {"term": {opensearch_field: value}}
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

                return {"range": {opensearch_field: {"gte": lower, "lte": upper}}}
            else:
                raise TQLValidationError(f"Between operator requires a list with two values, got: {value}")
        elif operator == "cidr":
            # Unwrap single-element lists for CIDR
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            # OpenSearch uses special syntax for CIDR queries on IP fields
            # Format: field: "192.168.0.0/24"
            return {"term": {opensearch_field: value}}
        # Negated operators
        elif operator == "not_in":
            if isinstance(value, list):
                return {"bool": {"must_not": {"terms": {opensearch_field: value}}}}
            else:
                return {"bool": {"must_not": {"term": {opensearch_field: value}}}}
        elif operator == "not_contains":
            # Unwrap single-element lists for string operators
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            if use_wildcard:
                return {"bool": {"must_not": {"wildcard": {opensearch_field: f"*{value}*"}}}}
            else:
                if field_name in self.intelligent_mappings:
                    return {"bool": {"must_not": {"match": {opensearch_field: value}}}}
                else:
                    return {"bool": {"must_not": {"wildcard": {opensearch_field: f"*{value}*"}}}}
        elif operator == "not_startswith":
            # Unwrap single-element lists for string operators
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            return {"bool": {"must_not": {"prefix": {opensearch_field: value}}}}
        elif operator == "not_endswith":
            # Unwrap single-element lists for string operators
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            return {"bool": {"must_not": {"wildcard": {opensearch_field: f"*{value}"}}}}
        elif operator == "not_regexp":
            # Unwrap single-element lists for string operators
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            return {"bool": {"must_not": {"regexp": {opensearch_field: value}}}}
        elif operator == "not_exists":
            return {"bool": {"must_not": {"exists": {"field": opensearch_field}}}}
        elif operator == "not_between":
            if isinstance(value, list) and len(value) == 2:
                val1 = self._convert_value(value[0])
                val2 = self._convert_value(value[1])
                lower = (
                    min(val1, val2) if isinstance(val1, (int, float)) and isinstance(val2, (int, float)) else value[0]
                )
                upper = (
                    max(val1, val2) if isinstance(val1, (int, float)) and isinstance(val2, (int, float)) else value[1]
                )
                if not isinstance(val1, (int, float)) or not isinstance(val2, (int, float)):
                    try:
                        if val1 > val2:
                            lower, upper = val2, val1
                        else:
                            lower, upper = val1, val2
                    except TypeError:
                        lower, upper = value[0], value[1]
                return {"bool": {"must_not": {"range": {opensearch_field: {"gte": lower, "lte": upper}}}}}
            else:
                raise TQLValidationError(f"Not between operator requires a list with two values, got: {value}")
        elif operator == "not_cidr":
            # Unwrap single-element lists for CIDR
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            # Negated CIDR query
            return {"bool": {"must_not": {"term": {opensearch_field: value}}}}
        elif operator == "is_not":
            if value is None:
                return {"exists": {"field": opensearch_field}}
            else:
                return {"bool": {"must_not": {"term": {opensearch_field: value}}}}
        elif operator == "any":
            # ANY operator - matches if any element equals the value (default OpenSearch behavior)
            # Works for both single values and arrays
            # Handle case where value might be wrapped in a list from parsing
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            return {"term": {opensearch_field: value}}
        elif operator == "all":
            # ALL operator - for arrays, all elements must match
            # OpenSearch doesn't have a native "all elements must equal X" query
            # We can use a script query to check this
            return {
                "script": {
                    "script": {
                        "source": """
                            if (!doc.containsKey(params.field) || doc[params.field].size() == 0) {
                                return false;
                            }
                            for (value in doc[params.field]) {
                                if (value != params.value) {
                                    return false;
                                }
                            }
                            return true;
                        """,
                        "params": {"field": opensearch_field, "value": value},
                    }
                }
            }
        elif operator == "not_any":
            # NOT ANY - no element should match
            # Handle case where value might be wrapped in a list from parsing
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            return {"bool": {"must_not": {"term": {opensearch_field: value}}}}
        elif operator == "not_all":
            # NOT ALL - not all elements equal the value
            # This means: field doesn't exist OR array is empty OR at least one element is different
            # Handle case where value might be wrapped in a list from parsing
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            return {
                "script": {
                    "script": {
                        "source": """
                            // Check if field exists in the document mapping
                            if (!doc.containsKey(params.field)) {
                                // Field doesn't exist, so NOT ALL is true
                                return true;
                            }

                            // Get field values
                            def values = doc[params.field];

                            // Empty array means not all elements are the value (vacuously true)
                            if (values.size() == 0) {
                                return true;
                            }

                            // Check if all elements match
                            for (value in values) {
                                if (value != params.value) {
                                    // Found an element that doesn't match
                                    return true;
                                }
                            }

                            // All elements match, so NOT all is false
                            return false;
                        """,
                        "params": {"field": opensearch_field, "value": value},
                    }
                }
            }
        else:
            raise TQLUnsupportedOperationError(f"Operator '{operator}' not supported for OpenSearch")

    def _convert_logical_op(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a logical operation to OpenSearch query."""
        operator = node["operator"]
        left_query = self.convert_node(node["left"])
        right_query = self.convert_node(node["right"])

        if operator == "and":
            # Collect all must clauses, flattening where appropriate
            must_clauses = []

            # Helper function to extract clauses
            def extract_must_clauses(query):
                if isinstance(query, dict) and "bool" in query:
                    bool_query = query["bool"]
                    # If it only has must clauses, extract them
                    if set(bool_query.keys()) == {"must"} and isinstance(bool_query["must"], list):
                        return bool_query["must"]
                return [query]

            # Extract and flatten must clauses
            must_clauses.extend(extract_must_clauses(left_query))
            must_clauses.extend(extract_must_clauses(right_query))

            return {"bool": {"must": must_clauses}}
        elif operator == "or":
            # OR still needs should clause
            return {"bool": {"should": [left_query, right_query], "minimum_should_match": 1}}
        else:
            raise TQLUnsupportedOperationError(f"Logical operator '{operator}' not supported for OpenSearch")

    def _convert_unary_op(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a unary operation to OpenSearch query."""
        operator = node["operator"]

        if operator == "not":
            operand = node["operand"]

            # Optimize double negation: NOT (NOT X) -> X
            if isinstance(operand, dict) and operand.get("type") == "unary_op" and operand.get("operator") == "not":
                return self.convert_node(operand["operand"])

            # Optimize negated operators: NOT (field not_in [values]) -> field in [values]
            if isinstance(operand, dict) and operand.get("type") == "comparison":
                op = operand.get("operator")
                if op == "not_in":
                    # Convert NOT (field not_in values) to (field in values)
                    field = operand["field"]
                    value = operand["value"]
                    opensearch_field, _ = self._resolve_field_name(field, "in")
                    if isinstance(value, list):
                        return {"terms": {opensearch_field: value}}
                    else:
                        return {"term": {opensearch_field: value}}
                elif op == "not_contains":
                    # Convert NOT (field not_contains value) to (field contains value)
                    field = operand["field"]
                    value = operand["value"]
                    # Unwrap single-element lists for string operators
                    if isinstance(value, list) and len(value) == 1:
                        value = value[0]
                    opensearch_field, use_wildcard = self._resolve_field_name(field, "contains")
                    if use_wildcard:
                        return {"wildcard": {opensearch_field: f"*{value}*"}}
                    else:
                        if field in self.intelligent_mappings:
                            return {"match": {opensearch_field: value}}
                        else:
                            return {"wildcard": {opensearch_field: f"*{value}*"}}
                # Add more optimizations for other negated operators as needed

            operand_query = self.convert_node(operand)
            return {"bool": {"must_not": operand_query}}
        else:
            raise TQLUnsupportedOperationError(f"Unary operator '{operator}' not supported for OpenSearch")

    def _convert_collection_op(self, node: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
        """Convert a collection operation (ANY/ALL) to OpenSearch query."""
        operator = node["operator"]
        field_name = node["field"]
        comparison_operator = node["comparison_operator"]
        value = node["value"]

        # Get the mapped field name
        opensearch_field, _ = self._resolve_field_name(field_name, comparison_operator)

        # For OpenSearch, we're essentially doing a nested query or terms lookup
        # This would ideally use the nested query type, but we'll create a simplified version
        # that works for basic array fields

        if operator == "any":
            # ANY operator is like checking if any array element matches
            # For basic equality/comparison, we can use a term/terms query directly
            if comparison_operator in ["eq", "="]:
                return {"term": {opensearch_field: value}}
            elif comparison_operator in ["ne", "!="]:
                return {"bool": {"must_not": {"term": {opensearch_field: value}}}}
            elif comparison_operator in ["in"]:
                if isinstance(value, list):
                    return {"terms": {opensearch_field: value}}
                else:
                    return {"term": {opensearch_field: value}}
            # For other comparisons, we create a range query
            elif comparison_operator in ["gt", ">"]:
                return {"range": {opensearch_field: {"gt": value}}}
            elif comparison_operator in ["gte", ">="]:
                return {"range": {opensearch_field: {"gte": value}}}
            elif comparison_operator in ["lt", "<"]:
                return {"range": {opensearch_field: {"lt": value}}}
            elif comparison_operator in ["lte", "<="]:
                return {"range": {opensearch_field: {"lte": value}}}
            # For string operations, we use the appropriate query type
            elif comparison_operator == "contains":
                return {"wildcard": {opensearch_field: f"*{value}*"}}
            elif comparison_operator == "startswith":
                return {"prefix": {opensearch_field: value}}
            elif comparison_operator == "endswith":
                return {"wildcard": {opensearch_field: f"*{value}"}}
            elif comparison_operator == "regexp":
                return {"regexp": {opensearch_field: value}}
            else:
                raise TQLUnsupportedOperationError(
                    f"Operator '{comparison_operator}' not supported for ANY collection operator in OpenSearch"
                )
        elif operator == "all":
            # ALL operator is more complex as we need to ensure all elements match
            # We'll use a must_not exists approach with a filter for elements that don't match

            # Create the negated condition
            if comparison_operator in ["eq", "="]:
                negated_condition = {"bool": {"must_not": {"term": {opensearch_field: value}}}}
            elif comparison_operator in ["ne", "!="]:
                negated_condition = {"term": {opensearch_field: value}}
            elif comparison_operator in ["in"]:
                if isinstance(value, list):
                    negated_condition = {"bool": {"must_not": {"terms": {opensearch_field: value}}}}
                else:
                    negated_condition = {"bool": {"must_not": {"term": {opensearch_field: value}}}}
            elif comparison_operator in ["gt", ">"]:
                negated_condition = {"range": {opensearch_field: {"lte": value}}}
            elif comparison_operator in ["gte", ">="]:
                negated_condition = {"range": {opensearch_field: {"lt": value}}}
            elif comparison_operator in ["lt", "<"]:
                negated_condition = {"range": {opensearch_field: {"gte": value}}}
            elif comparison_operator in ["lte", "<="]:
                negated_condition = {"range": {opensearch_field: {"gt": value}}}
            elif comparison_operator == "contains":
                negated_condition = {"bool": {"must_not": {"wildcard": {opensearch_field: f"*{value}*"}}}}
            elif comparison_operator == "startswith":
                negated_condition = {"bool": {"must_not": {"prefix": {opensearch_field: value}}}}
            elif comparison_operator == "endswith":
                negated_condition = {"bool": {"must_not": {"wildcard": {opensearch_field: f"*{value}"}}}}
            elif comparison_operator == "regexp":
                negated_condition = {"bool": {"must_not": {"regexp": {opensearch_field: value}}}}
            else:
                raise TQLUnsupportedOperationError(
                    f"Operator '{comparison_operator}' not supported for ALL collection operator in OpenSearch"
                )

            # For ALL to be true, there must not be any elements that don't match the condition
            return {"bool": {"must_not": negated_condition}}
        else:
            raise TQLUnsupportedOperationError(f"Collection operator '{operator}' not supported for OpenSearch")

    def _has_filtering_conditions(self, node: Any) -> bool:
        """Check if an AST node contains actual filtering conditions.

        Args:
            node: AST node to check

        Returns:
            True if the node contains filtering conditions, False otherwise
        """
        if not isinstance(node, dict):
            return False

        node_type = node.get("type")

        if node_type == "comparison":
            # All comparisons are filtering conditions
            return True
        elif node_type == "logical_op":
            # Check both sides of logical operation
            left_has = self._has_filtering_conditions(node.get("left"))
            right_has = self._has_filtering_conditions(node.get("right"))
            return left_has or right_has
        elif node_type == "unary_op":
            # Check the operand
            return self._has_filtering_conditions(node.get("operand"))
        elif node_type == "collection_op":
            # Collection operations are filtering conditions
            return True
        elif node_type == "geo_expr":
            # Check nested geo conditions
            return self._has_filtering_conditions(node.get("conditions"))
        elif node_type == "nslookup_expr":
            # Check nested nslookup conditions
            return self._has_filtering_conditions(node.get("conditions"))

        return False

    def _convert_geo_expr(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a geo expression to OpenSearch query.

        Note: Geo expressions require post-processing since the geoip_lookup
        must be applied to results after they return from OpenSearch.

        The OpenSearch query depends on whether there are geo conditions:
        - If there are geo conditions, we need an exists query on the IP field
          (since we can only apply geo filters to IPs that exist)
        - If there are no conditions (just enrichment), we return match_all

        Args:
            node: Geo expression AST node

        Returns:
            OpenSearch query
        """
        field_name = node["field"]
        conditions = node.get("conditions")

        # Check if there are actual filtering conditions
        if conditions and self._has_filtering_conditions(conditions):
            # We have geo conditions that will filter results, so we need exists query
            # Try to resolve the field name, but if it fails, use the original
            try:
                opensearch_field, _ = self._resolve_field_name(field_name, "exists")
            except TQLUnsupportedOperationError:
                # Field might not have mappings or exists might not be supported
                # Use the original field name
                opensearch_field = field_name

            return {"exists": {"field": opensearch_field}}
        else:
            # No filtering conditions, just enrichment - match all documents
            return {"match_all": {}}

    def _convert_nslookup_expr(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an nslookup expression to OpenSearch query.

        Note: NSLookup expressions require post-processing since the DNS lookup
        must be applied to results after they return from OpenSearch.

        The OpenSearch query depends on whether there are DNS conditions:
        - If there are DNS conditions, we need an exists query on the field
          (since we can only apply DNS filters to fields that exist)
        - If there are no conditions (just enrichment), we return match_all

        Args:
            node: NSLookup expression AST node

        Returns:
            OpenSearch query
        """
        field_name = node["field"]
        conditions = node.get("conditions")

        # Check if there are actual filtering conditions
        if conditions and self._has_filtering_conditions(conditions):
            # We have DNS conditions that will filter results, so we need exists query
            # Try to resolve the field name, but if it fails, use the original
            try:
                opensearch_field, _ = self._resolve_field_name(field_name, "exists")
            except TQLUnsupportedOperationError:
                # Field might not have mappings or exists might not be supported
                # Use the original field name
                opensearch_field = field_name

            return {"exists": {"field": opensearch_field}}
        else:
            # No filtering conditions, just enrichment - match all documents
            return {"match_all": {}}

    def _resolve_field_name(
        self, field_name: str, operator: str, preferred_analyzer: Optional[str] = None
    ) -> tuple[str, bool]:
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
        """Convert value types for OpenSearch compatibility.

        Args:
            value: Value to convert

        Returns:
            Converted value (bool, None, numeric, or original)
        """
        if isinstance(value, str):
            # Check for boolean values
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
            elif value.lower() == "null":
                return None
            # Check if it's a numeric string
            elif value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                # Convert to integer
                return int(value)
            else:
                # Try to parse as float
                try:
                    # Check if it has a decimal point
                    if "." in value:
                        return float(value)
                except ValueError:
                    pass
        return value

    def _is_text_field(self, field_name: str, opensearch_field: str) -> bool:
        """Check if the resolved field is a text field.

        Args:
            field_name: Original field name
            opensearch_field: Resolved OpenSearch field name

        Returns:
            True if it's a text field, False otherwise
        """
        # Method 1: Check if field is in intelligent mappings
        if field_name in self.intelligent_mappings:
            mapping = self.intelligent_mappings[field_name]
            # Check if the selected field is a text field
            field_type = mapping.field_types.get(opensearch_field, "keyword")
            if field_type == "text":
                return True

        # Method 2: Check if the opensearch_field is a variant of a mapped field
        # Extract base field name (e.g., "winlog.computer_name" from "winlog.computer_name.text")
        base_field = opensearch_field
        field_suffix = ""

        if "." in opensearch_field:
            parts = opensearch_field.rsplit(".", 1)
            possible_base = parts[0]
            possible_suffix = parts[1]

            # Check if this looks like a field variant
            if possible_suffix in ["text", "keyword", "lowercase", "english", "standard"]:
                base_field = possible_base
                field_suffix = possible_suffix

        # Check if base field is in mappings
        if base_field in self.intelligent_mappings:
            mapping = self.intelligent_mappings[base_field]
            # Check the field type of the specific variant
            variant_type = mapping.field_types.get(opensearch_field, None)
            if variant_type == "text":
                return True
            elif field_suffix == "text" and variant_type is None:
                # If suffix is "text" and we don't have explicit type info, assume it's a text field
                return True

        return False
