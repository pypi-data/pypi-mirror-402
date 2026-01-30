"""Statistics operations for TQL.

This module handles statistical aggregations and analysis for TQL queries.
"""

from typing import Any, Dict, List, Optional, Union

from ..exceptions import TQLParseError, TQLValueError
from ..parser import TQLParser
from ..stats_evaluator import TQLStatsEvaluator


class StatsOperations:
    """Handles statistics operations for TQL."""

    def __init__(self, parser: TQLParser, field_mappings: Optional[Dict[str, Any]] = None):
        """Initialize statistics operations.

        Args:
            parser: TQL parser instance
            field_mappings: Field mappings for evaluation
        """
        self.parser = parser
        self.stats_evaluator = TQLStatsEvaluator()
        self.field_mappings = field_mappings or {}

    def stats(self, data: Union[List[Dict], str], stats_query: str) -> Dict[str, Any]:
        """Execute a statistics query on data.

        Args:
            data: List of records or file path
            stats_query: Stats query string (e.g., "| stats count() by status")

        Returns:
            Dictionary containing aggregation results

        Raises:
            TQLParseError: If query parsing fails
            TQLValueError: If query is invalid
        """
        # First try to parse as-is
        try:
            parsed = self.parser.parse(stats_query)
            # If it's already a stats expression, use it
            if parsed.get("type") == "stats_expr":
                # Already a valid stats expression, proceed
                pass
            else:
                # Not a stats expression, try adding | stats prefix
                stats_query_with_pipe = "| stats " + stats_query.strip()
                parsed = self.parser.parse(stats_query_with_pipe)
        except TQLParseError:
            # If parsing failed, try with | stats prefix
            if not stats_query.strip().startswith("| stats"):
                stats_query_with_pipe = "| stats " + stats_query.strip()
                try:
                    parsed = self.parser.parse(stats_query_with_pipe)
                except TQLParseError as e:
                    raise TQLParseError(f"Invalid stats query: {str(e)}")
            else:
                raise

        # Verify it's a stats expression
        if parsed.get("type") != "stats_expr":
            raise TQLValueError("Query must be a stats expression starting with '| stats'")

        # Load data if it's a file path
        if isinstance(data, str):
            from .file_operations import FileOperations

            file_ops = FileOperations()
            records = file_ops.load_file(data)
        else:
            records = data

        # Execute the stats query
        return self.stats_evaluator.evaluate_stats(records, parsed)

    def query_stats(self, data: Union[List[Dict], str], query: str) -> Dict[str, Any]:
        """Execute a TQL query with stats aggregation.

        This combines filtering and statistical aggregation in one query.

        Args:
            data: List of records or file path
            query: Combined query string (e.g., "status = 'active' | stats count() by type")

        Returns:
            Dictionary containing aggregation results

        Raises:
            TQLParseError: If query parsing fails
        """
        # Parse the combined query
        parsed = self.parser.parse(query)

        # Check if it's a query with stats
        if parsed.get("type") != "query_with_stats":
            raise TQLValueError("Query must contain both filter and stats parts separated by |")

        # Load data if it's a file path
        if isinstance(data, str):
            from .file_operations import FileOperations

            file_ops = FileOperations()
            records = file_ops.load_file(data)
        else:
            records = data

        # First apply the filter
        from ..evaluator import TQLEvaluator

        evaluator = TQLEvaluator()
        filtered_records = []
        filter_ast = parsed["filter"]

        for record in records:
            if evaluator._evaluate_node(filter_ast, record, self.field_mappings):
                filtered_records.append(record)

        # Then apply stats
        stats_ast = parsed["stats"]
        return self.stats_evaluator.evaluate_stats(filtered_records, stats_ast)

    def analyze_stats_query(self, query: str) -> Dict[str, Any]:  # noqa: C901
        """Analyze a stats query for performance and correctness.

        Args:
            query: Stats query string

        Returns:
            Analysis results including AST and any warnings
        """
        # Parse the query
        try:
            # Don't add prefix if query already starts with "stats"
            if not query.strip().startswith("| stats") and not query.strip().startswith("stats") and "|" not in query:
                query = "| stats " + query.strip()

            ast = self.parser.parse(query)
        except TQLParseError as e:
            return {"valid": False, "error": str(e), "type": "parse_error"}

        # Determine query type
        if ast.get("type") == "stats_expr":
            query_type = "stats_only"
            stats_ast = ast
            filter_ast = None
        elif ast.get("type") == "query_with_stats":
            query_type = "filter_and_stats"
            stats_ast = ast["stats"]
            filter_ast = ast["filter"]
        else:
            return {"valid": False, "error": "Query must be a stats expression", "type": "invalid_query_type"}

        # Analyze the stats portion
        aggregations = stats_ast.get("aggregations", [])
        group_by = stats_ast.get("group_by", [])

        warnings = []
        suggestions = []

        # Check for common issues
        if not aggregations:
            warnings.append("No aggregation functions specified")
            suggestions.append("Add aggregation functions like count(), sum(field), avg(field)")

        # Check for duplicate aggregations without aliases
        agg_fields = []
        for agg in aggregations:
            if not agg.get("alias"):
                key = f"{agg['function']}({agg['field']})"
                if key in agg_fields:
                    warnings.append(f"Duplicate aggregation without alias: {key}")
                    suggestions.append(f"Use aliases to distinguish: {key} as alias1, {key} as alias2")
                agg_fields.append(key)

        # Normalize group_by to extract just field names for compatibility
        normalized_group_by = []
        for field in group_by:
            if isinstance(field, str):
                normalized_group_by.append(field)
            elif isinstance(field, dict) and "field" in field:
                normalized_group_by.append(field["field"])
            else:
                normalized_group_by.append(str(field))

        # Build analysis result
        result = {
            "valid": True,
            "type": query_type,
            "query": query,
            "ast": ast,
            "aggregations": aggregations,
            "group_by": normalized_group_by,
            "warnings": warnings,
            "suggestions": suggestions,
        }

        if filter_ast:
            result["filter"] = self._analyze_filter(filter_ast)

        return result

    def _analyze_filter(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the filter portion of a query."""
        fields = []
        operators = []

        def traverse(node):
            if isinstance(node, dict):
                node_type = node.get("type")
                if node_type == "comparison":
                    fields.append(node.get("field"))
                    operators.append(node.get("operator"))
                elif node_type == "logical_op":
                    operators.append(node.get("operator"))
                    traverse(node.get("left"))
                    traverse(node.get("right"))

        traverse(ast)

        return {"fields": list(set(fields)), "operators": list(set(operators))}
