"""Evaluator components for TQL.

This package contains modular components for TQL evaluation:
- field_access: Field value extraction and type handling
- value_comparison: Value comparison operations and operator implementations
- special_expressions: Geo and NSLookup expression evaluators
"""

from .field_access import FieldAccessor
from .special_expressions import SpecialExpressionEvaluator
from .value_comparison import ValueComparator

__all__ = [
    "FieldAccessor",
    "ValueComparator",
    "SpecialExpressionEvaluator",
]
