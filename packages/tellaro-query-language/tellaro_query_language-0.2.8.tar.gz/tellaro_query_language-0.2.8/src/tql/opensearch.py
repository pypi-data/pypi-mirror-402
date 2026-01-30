"""OpenSearch backend for TQL.

This module provides OpenSearch integration for TQL, converting TQL queries
to OpenSearch Query DSL with intelligent field selection based on operators.
"""

from typing import Any, Dict, Optional, Union

from .opensearch_components import FieldMapping, LuceneConverter, QueryConverter


class OpenSearchBackend:
    """OpenSearch backend for TQL query conversion with intelligent field selection."""

    def __init__(self, field_mappings: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None):
        """Initialize the OpenSearch backend.

        Args:
            field_mappings: Field mappings in two formats:
                          1. Simple: {"field_name": "target_field_name"}
                          2. Intelligent: {"field_name": {"field_name": "keyword", "field_name.text": "text"}}
        """
        self.field_mappings = field_mappings or {}
        self.intelligent_mappings = {}
        self.simple_mappings = {}

        # Parse field mappings
        for field_name, mapping in self.field_mappings.items():
            if isinstance(mapping, dict):
                # Check if this is an OpenSearch-style mapping with "type" and "fields"
                if "type" in mapping and not any(k for k in mapping.keys() if k not in ["type", "fields", "analyzer"]):
                    # This is an OpenSearch-style mapping for a single field
                    field_mapping = FieldMapping(mapping)
                    field_mapping.set_base_field_name(field_name)
                    self.intelligent_mappings[field_name] = field_mapping
                else:
                    # Traditional intelligent mapping with multiple field variants
                    self.intelligent_mappings[field_name] = FieldMapping(mapping)
            elif isinstance(mapping, str):
                # Check if this looks like a type specification (common OpenSearch types)
                if mapping in [
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
                    # This is a type specification, create an intelligent mapping
                    self.intelligent_mappings[field_name] = FieldMapping({field_name: mapping})
                else:
                    # Simple field name mapping (backward compatibility)
                    self.simple_mappings[field_name] = mapping

        # Initialize converters
        self.query_converter = QueryConverter(self.intelligent_mappings, self.simple_mappings)
        self.lucene_converter = LuceneConverter(self.intelligent_mappings, self.simple_mappings)

    def convert(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a TQL AST to OpenSearch Query DSL.

        Args:
            ast: The parsed TQL query AST

        Returns:
            OpenSearch Query DSL as a dictionary
        """
        query_dsl = {"query": self.query_converter.convert_node(ast)}
        return query_dsl

    def convert_lucene(self, ast: Dict[str, Any]) -> str:
        """Convert a TQL AST to Lucene query string."""
        return self.lucene_converter.convert_lucene(ast)
