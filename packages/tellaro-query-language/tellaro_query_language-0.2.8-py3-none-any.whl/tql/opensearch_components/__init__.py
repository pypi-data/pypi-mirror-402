"""OpenSearch backend components for TQL.

This package contains modular components for OpenSearch integration:
- field_mapping: Field mapping and intelligent field selection
- query_converter: TQL AST to OpenSearch Query DSL conversion
- lucene_converter: TQL AST to Lucene query string conversion
"""

from .field_mapping import FieldMapping
from .lucene_converter import LuceneConverter
from .query_converter import QueryConverter

__all__ = [
    "FieldMapping",
    "QueryConverter",
    "LuceneConverter",
]
