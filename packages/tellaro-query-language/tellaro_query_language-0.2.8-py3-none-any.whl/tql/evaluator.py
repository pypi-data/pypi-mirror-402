"""TQL query evaluator.

This module provides the TQLEvaluator class for executing TQL queries against
data records in memory.
"""

from typing import Any, Dict, List, Optional

from .evaluator_components import FieldAccessor, SpecialExpressionEvaluator, ValueComparator
from .mutators import apply_mutators


class TQLEvaluator:
    """Evaluates TQL queries against data records.

    This class takes parsed TQL ASTs and evaluates them against Python
    dictionaries representing data records.
    """

    # Sentinel value to distinguish missing fields from None values
    _MISSING_FIELD = object()

    def __init__(self):
        """Initialize the evaluator."""
        # Initialize component evaluators
        self.field_accessor = FieldAccessor()
        self.value_comparator = ValueComparator()
        # Pass sentinel value to components
        self.field_accessor._MISSING_FIELD = self._MISSING_FIELD
        self.value_comparator._MISSING_FIELD = self._MISSING_FIELD
        # Initialize special expression evaluator with callbacks
        self.special_evaluator = SpecialExpressionEvaluator(self._get_field_value, self._evaluate_node)
        self.special_evaluator._MISSING_FIELD = self._MISSING_FIELD

    def evaluate(
        self, ast: Dict[str, Any], records: List[Dict[str, Any]], field_mappings: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Evaluate a TQL query against a list of records.

        Args:
            ast: The parsed TQL query AST
            records: List of dictionaries to evaluate against
            field_mappings: Optional field name mappings

        Returns:
            List of records that match the query
        """
        results = []
        for record in records:
            if self.evaluate_single(ast, record, field_mappings):
                results.append(record)
        return results

    def evaluate_single(
        self, ast: Dict[str, Any], record: Dict[str, Any], field_mappings: Optional[Dict[str, str]] = None
    ) -> bool:
        """Evaluate a TQL query against a single record.

        Args:
            ast: The parsed TQL query AST
            record: Dictionary to evaluate against
            field_mappings: Optional field name mappings

        Returns:
            True if the record matches the query
        """
        field_mappings = field_mappings or {}
        return self._evaluate_node(ast, record, field_mappings)

    def _evaluate_node(self, node: Any, record: Dict[str, Any], field_mappings: Dict[str, str]) -> bool:  # noqa: C901
        """Evaluate a single AST node against a record.

        Args:
            node: AST node to evaluate
            record: Record to evaluate against
            field_mappings: Field name mappings

        Returns:
            Boolean result of evaluation
        """
        if isinstance(node, dict):
            node_type = node.get("type")

            if node_type == "match_all":
                # Empty query matches all records
                return True
            elif node_type == "comparison":
                return self._evaluate_comparison(node, record, field_mappings)
            elif node_type == "logical_op":
                return self._evaluate_logical_op(node, record, field_mappings)
            elif node_type == "unary_op":
                return self._evaluate_unary_op(node, record, field_mappings)
            elif node_type == "collection_op":
                return self._evaluate_collection_op(node, record, field_mappings)
            elif node_type == "geo_expr":
                return self.special_evaluator.evaluate_geo_expr(node, record, field_mappings)
            elif node_type == "nslookup_expr":
                return self.special_evaluator.evaluate_nslookup_expr(node, record, field_mappings)
            elif node_type == "query_with_stats":
                # For query_with_stats, only evaluate the filter part
                # The stats part is handled separately
                filter_node = node.get("filter")
                if filter_node:
                    return self._evaluate_node(filter_node, record, field_mappings)
                else:
                    return True  # No filter means match all
            elif node_type == "stats_expr":
                # Pure stats queries match all records
                # The aggregations are handled separately
                return True

        # Unknown node type
        return False

    def _evaluate_comparison(
        self, node: Dict[str, Any], record: Dict[str, Any], field_mappings: Dict[str, str]
    ) -> bool:
        """Evaluate a comparison operation.

        Args:
            node: Comparison node with field, operator, and value
            record: Record to evaluate against
            field_mappings: Field name mappings

        Returns:
            Boolean result of comparison
        """
        field_name = node["field"]
        operator = node["operator"]
        # For exists/not_exists operators, value is None
        expected_value = node.get("value") if operator not in ["exists", "not_exists"] else None
        field_mutators = node.get("field_mutators", [])
        value_mutators = node.get("value_mutators", [])
        type_hint = node.get("type_hint")

        # Apply field mapping
        actual_field = self.field_accessor.apply_field_mapping(field_name, field_mappings)

        # Get the field value
        field_value = self._get_field_value(record, actual_field)

        # Apply field mutators if any
        if field_mutators and field_value is not self._MISSING_FIELD:
            try:
                field_value = apply_mutators(field_value, field_mutators, field_name, record)
            except (ValueError, TypeError):
                # If mutators fail, treat as missing field for exists/not_exists checks
                if operator in ["exists", "not_exists"]:
                    field_value = self._MISSING_FIELD
                else:
                    # For other operators, the comparison will fail naturally
                    return False

        # Apply value mutators if any
        if value_mutators:
            expected_value = apply_mutators(expected_value, value_mutators, field_name, record)

        # Apply type hint if specified
        if type_hint and field_value is not self._MISSING_FIELD:
            field_value = self.field_accessor.apply_type_hint(
                field_value, type_hint, field_name, operator, field_mappings
            )

        # Perform the comparison
        return self.value_comparator.compare_values(field_value, operator, expected_value)

    def _evaluate_logical_op(
        self, node: Dict[str, Any], record: Dict[str, Any], field_mappings: Dict[str, str]
    ) -> bool:
        """Evaluate a logical operation (AND/OR).

        Args:
            node: Logical operation node
            record: Record to evaluate against
            field_mappings: Field name mappings

        Returns:
            Boolean result of logical operation
        """
        operator = node["operator"]
        left = node["left"]
        right = node["right"]

        if operator == "and":
            # Short-circuit evaluation for AND
            left_result = self._evaluate_node(left, record, field_mappings)
            if not left_result:
                return False
            return self._evaluate_node(right, record, field_mappings)
        elif operator == "or":
            # Short-circuit evaluation for OR
            left_result = self._evaluate_node(left, record, field_mappings)
            if left_result:
                return True
            return self._evaluate_node(right, record, field_mappings)
        else:
            raise ValueError(f"Unknown logical operator: {operator}")

    def _evaluate_unary_op(self, node: Dict[str, Any], record: Dict[str, Any], field_mappings: Dict[str, str]) -> bool:
        """Evaluate a unary operation (NOT).

        Args:
            node: Unary operation node
            record: Record to evaluate against
            field_mappings: Field name mappings

        Returns:
            Boolean result of unary operation
        """
        operator = node["operator"]
        operand = node["operand"]

        if operator == "not":
            # Handle special optimizations for NOT operations
            # NOT (field exists) and NOT (field is null) need special handling

            # First check if the operand would fail due to missing fields
            # But NOT of an exists check on a missing field should still be True
            if self._is_exists_operation(operand):
                # NOT EXISTS check - return opposite of exists
                return not self._evaluate_node(operand, record, field_mappings)
            elif self._is_null_operation(operand):
                # NOT (field IS NULL) check
                return not self._evaluate_node(operand, record, field_mappings)
            elif self._is_not_null_operation(operand):
                # NOT (field IS NOT NULL) - double negative
                # This should only be True if the field exists with a null value
                # For missing fields, it should remain False
                # field = operand.get("field")  # Not needed - handled by _operand_has_missing_fields
                if self._operand_has_missing_fields(operand, record, field_mappings):
                    # Missing field - NOT (IS NOT NULL) is False
                    return False
                else:
                    # Field exists - evaluate normally
                    return not self._evaluate_node(operand, record, field_mappings)
            elif self._is_logical_operation(operand):
                # For logical operations (AND/OR), always evaluate normally
                # They can handle missing fields correctly
                return not self._evaluate_node(operand, record, field_mappings)
            elif self._operand_has_missing_fields(operand, record, field_mappings):
                # For operations on missing fields (except exists/null checks), NOT returns True
                # This matches OpenSearch behavior where must_not includes docs with missing fields
                # However, for collection operators, we should evaluate normally since they handle missing fields
                operand_type = operand.get("type")
                operand_operator = operand.get("operator", "")
                if operand_type == "comparison" and operand_operator in ["any", "all", "none"]:
                    # Collection operators handle missing fields in their own evaluation
                    return not self._evaluate_node(operand, record, field_mappings)
                return True
            else:
                # Standard NOT operation
                return not self._evaluate_node(operand, record, field_mappings)
        else:
            raise ValueError(f"Unknown unary operator: {operator}")

    def _evaluate_collection_op(  # noqa: C901
        self, node: Dict[str, Any], record: Dict[str, Any], field_mappings: Dict[str, str]
    ) -> bool:
        """Evaluate a collection operation (ANY/ALL).

        Args:
            node: Collection operation node
            record: Record to evaluate against
            field_mappings: Field name mappings

        Returns:
            Boolean result of collection operation
        """
        operator = node["operator"]
        field_name = node["field"]
        comparison_operator = node["comparison_operator"]
        expected_value = node["value"]
        field_mutators = node.get("field_mutators", [])

        # Apply field mapping
        actual_field = self.field_accessor.apply_field_mapping(field_name, field_mappings)

        # Get the field value
        field_value = self._get_field_value(record, actual_field)

        # If field is missing, return False
        if field_value is self._MISSING_FIELD:
            return False

        # Apply mutators if any
        if field_mutators:
            field_value = self._apply_collection_mutators(field_value, field_mutators, field_name, record)

        # For non-list values, convert to single-element list
        if not isinstance(field_value, (list, tuple, set)):
            field_value = [field_value]

        # Evaluate the collection operation
        if operator == "any":
            # ANY: at least one element must match
            for element in field_value:
                if self.value_comparator.compare_values(element, comparison_operator, expected_value):
                    return True
            return False
        elif operator == "all":
            # ALL: all elements must match
            if not field_value:  # Empty collection
                return False
            for element in field_value:
                if not self.value_comparator.compare_values(element, comparison_operator, expected_value):
                    return False
            return True
        else:
            raise ValueError(f"Unknown collection operator: {operator}")

    def _get_field_value(self, record: Dict[str, Any], field_path: str) -> Any:
        """Get a field value from a record, supporting nested field access.

        Args:
            record: The record dictionary
            field_path: Dot-separated field path (e.g., "user.name")

        Returns:
            The field value or _MISSING_FIELD if not found
        """
        return self.field_accessor.get_field_value(record, field_path)

    def _operand_has_missing_fields(self, node: Any, record: Dict[str, Any], field_mappings: Dict[str, str]) -> bool:
        """Check if an operand references missing fields.

        This is used for NOT operations to handle missing field cases properly.

        Args:
            node: AST node to check
            record: Record to check against
            field_mappings: Field name mappings

        Returns:
            True if the operand references any missing fields
        """
        if isinstance(node, dict):
            node_type = node.get("type")

            if node_type == "comparison":
                field_name = node["field"]
                # Apply field mapping
                actual_field = self.field_accessor.apply_field_mapping(field_name, field_mappings)
                # Check if the field exists
                field_value = self._get_field_value(record, actual_field)
                return field_value is self._MISSING_FIELD
            elif node_type == "logical_op":
                # For logical operations, check both sides
                left_missing = self._operand_has_missing_fields(node["left"], record, field_mappings)
                right_missing = self._operand_has_missing_fields(node["right"], record, field_mappings)
                return left_missing or right_missing
            elif node_type == "unary_op":
                # Don't recurse through NOT operators - they handle missing fields themselves
                # The NOT operator has special logic at lines 213-254 that handles missing fields correctly
                # Recursing here would cause double-handling and incorrect results
                return False
            elif node_type == "collection_op":
                field_name = node["field"]
                # Apply field mapping
                actual_field = self.field_accessor.apply_field_mapping(field_name, field_mappings)
                # Check if the field exists
                field_value = self._get_field_value(record, actual_field)
                return field_value is self._MISSING_FIELD

        return False

    def _is_exists_operation(self, node: Any) -> bool:
        """Check if a node is an exists operation."""
        if isinstance(node, dict) and node.get("type") == "comparison":
            return node.get("operator") in ["exists", "not_exists"]
        return False

    def _is_null_operation(self, node: Any) -> bool:
        """Check if a node is checking for null (field IS NULL)."""
        if isinstance(node, dict) and node.get("type") == "comparison":
            if node.get("operator") == "is":
                value = node.get("value")
                return value is None or (isinstance(value, str) and value.lower() == "null")
        return False

    def _is_not_null_operation(self, node: Any) -> bool:
        """Check if a node is checking for not null (field IS NOT NULL)."""
        if isinstance(node, dict) and node.get("type") == "comparison":
            if node.get("operator") == "is_not":
                value = node.get("value")
                return value is None or (isinstance(value, str) and value.lower() == "null")
        return False

    def _is_logical_operation(self, node: Any) -> bool:
        """Check if a node is a logical operation (AND/OR)."""
        if isinstance(node, dict) and node.get("type") == "logical_op":
            return node.get("operator") in ["and", "or"]
        return False

    def _apply_collection_mutators(
        self, field_value: Any, mutators: List[Dict[str, Any]], field_name: str, record: Dict[str, Any]
    ) -> Any:
        """Apply mutators that work on collections.

        Some mutators like split() can convert single values to arrays.

        Args:
            field_value: Original field value
            mutators: List of mutators to apply
            field_name: The field name
            record: The record being processed

        Returns:
            Mutated value
        """
        # Apply mutators
        result = apply_mutators(field_value, mutators, field_name, record)

        # Check if any mutator converted to array
        for mutator in mutators:
            if mutator.get("name") == "split":
                # Split always returns a list
                if not isinstance(result, (list, tuple)):
                    result = [result]
                break

        return result
