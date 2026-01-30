"""Field extraction utilities for TQL parser."""

from typing import Any, Dict, List, Set


class FieldExtractor:
    """Extracts field references from TQL AST."""

    @staticmethod
    def extract_fields(ast: Dict[str, Any]) -> List[str]:
        """Extract all unique field references from a TQL AST.

        Args:
            ast: The parsed AST

        Returns:
            Sorted list of unique field names referenced in the query
        """
        # Use a set to collect unique field names
        fields: Set[str] = set()
        FieldExtractor._collect_fields_from_node(ast, fields)

        # Return sorted list of field names
        return sorted(fields)

    @staticmethod
    def _collect_fields_from_node(node: Dict[str, Any], fields: Set[str]) -> None:  # noqa: C901
        """Recursively collect field names from an AST node.

        Args:
            node: The AST node to extract fields from
            fields: Set to collect unique field names
        """
        if not isinstance(node, dict):
            return

        node_type = node.get("type")

        if node_type == "comparison":
            # Standard comparison, add the field
            if "field" in node:
                field = node["field"]
                # Handle case where field might be a list (should not happen with valid queries)
                if isinstance(field, list):
                    # This indicates a malformed query - skip it
                    pass
                else:
                    fields.add(field)

        elif node_type == "collection_op":
            # Collection operation (ANY, ALL)
            if "field" in node:
                fields.add(node["field"])

        elif node_type == "logical_op":
            # Logical operation (AND, OR), process both sides
            if "left" in node:
                FieldExtractor._collect_fields_from_node(node["left"], fields)
            if "right" in node:
                FieldExtractor._collect_fields_from_node(node["right"], fields)

        elif node_type == "unary_op":
            # Unary operation (NOT), process the operand
            if "operand" in node:
                FieldExtractor._collect_fields_from_node(node["operand"], fields)

        elif node_type == "geo_expr":
            # Geo expression, add the field being geo-looked up
            if "field" in node:
                fields.add(node["field"])
            # Also process any conditions inside the geo expression
            if "conditions" in node:
                FieldExtractor._collect_fields_from_node(node["conditions"], fields)

        elif node_type == "nslookup_expr":
            # NSLookup expression, add the field being looked up
            if "field" in node:
                fields.add(node["field"])
            # Also process any conditions inside the nslookup expression
            if "conditions" in node:
                FieldExtractor._collect_fields_from_node(node["conditions"], fields)

        elif node_type == "query_with_stats":
            # Query with stats, process the filter part
            if "filter" in node:
                FieldExtractor._collect_fields_from_node(node["filter"], fields)
            # Also collect fields from stats if needed
            if "stats" in node:
                FieldExtractor._collect_fields_from_stats(node["stats"], fields)

        elif node_type == "stats_expr":
            # Stats expression
            FieldExtractor._collect_fields_from_stats(node, fields)

    @staticmethod
    def _collect_fields_from_stats(stats_node: Dict[str, Any], fields: Set[str]) -> None:
        """Collect field names from stats expressions.

        Args:
            stats_node: Stats AST node
            fields: Set to collect unique field names
        """
        # Collect fields from aggregations
        if "aggregations" in stats_node:
            for agg in stats_node["aggregations"]:
                if "field" in agg and agg["field"] != "*":
                    fields.add(agg["field"])

        # Collect fields from group by
        if "group_by" in stats_node:
            for field in stats_node["group_by"]:
                if isinstance(field, dict) and "field" in field:
                    # Normalized format: {"field": "name", "bucket_size": N|None}
                    fields.add(field["field"])
                elif isinstance(field, str):
                    # Legacy format: just field name (for backward compatibility)
                    fields.add(field)
                else:
                    # Handle any other format gracefully
                    fields.add(str(field))
