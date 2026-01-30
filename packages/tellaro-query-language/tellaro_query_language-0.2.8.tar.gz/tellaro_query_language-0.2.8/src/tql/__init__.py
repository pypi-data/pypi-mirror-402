"""Tellaro Query Language package.

A flexible, human-friendly query language for searching and filtering structured data.
TQL provides a unified syntax for expressing complex queries with support for:
- Field selection (including nested fields)
- Comparison and logical operators
- String, number, and list values
- Mutators for field transformation
- Direct file operations and OpenSearch integration
"""

from .core import TQL
from .exceptions import (
    TQLExecutionError,
    TQLFieldError,
    TQLOperatorError,
    TQLParseError,
    TQLSyntaxError,
    TQLTypeError,
    TQLUnsupportedOperationError,
    TQLValidationError,
    TQLValueError,
)
from .opensearch import OpenSearchBackend
from .opensearch_mappings import (
    discover_field_mappings_for_query,
    extract_field_mappings_from_opensearch,
    get_sample_data_from_index,
)

__version__ = "0.2.2"
__all__ = [
    "TQL",
    "TQLParseError",
    "TQLExecutionError",
    "TQLValidationError",
    "TQLSyntaxError",
    "TQLTypeError",
    "TQLFieldError",
    "TQLOperatorError",
    "TQLValueError",
    "TQLUnsupportedOperationError",
    "OpenSearchBackend",
    "extract_field_mappings_from_opensearch",
    "discover_field_mappings_for_query",
    "get_sample_data_from_index",
]
