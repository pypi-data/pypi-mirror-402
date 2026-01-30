"""Base mutator class and utilities."""

from enum import Enum
from typing import Any, Dict, Optional


class PerformanceClass(Enum):
    """Performance classification for mutators."""

    FAST = "fast"  # Minimal performance impact
    MODERATE = "moderate"  # Noticeable but acceptable impact
    SLOW = "slow"  # Significant performance impact


def append_to_result(record: Dict[str, Any], dotted_field_name: str, value: Any) -> None:
    """
    Append a value to a record at the location specified by a dotted field name.
    This function traverses the record, creating any missing parent keys,
    and then sets the final key to the given value.

    Args:
        record: The record dictionary.
        dotted_field_name: The dotted path (e.g., "dns.answers.class").
        value: The value to set.
    """
    parts = dotted_field_name.split(".")
    d = record
    for part in parts[:-1]:
        if part not in d or not isinstance(d[part], dict):
            d[part] = {}
        d = d[part]
    d[parts[-1]] = value


class BaseMutator:
    """Base class for all mutators."""

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize a mutator.

        Args:
            params: Optional parameters for the mutator.
        """
        self.params = params or {}
        self.is_enrichment = False  # Override in enrichment mutators

        # Performance characteristics - override in subclasses
        # These represent the performance impact in different contexts
        self.performance_in_memory = PerformanceClass.FAST
        self.performance_opensearch = PerformanceClass.MODERATE

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:
        """
        Apply the mutator to a value.

        Args:
            field_name: The name of the field being processed.
            record: The full record (may be modified for enrichment mutators).
            value: The current field value.

        Returns:
            The transformed value.
        """
        return value

    def get_performance_class(self, context: str = "in_memory") -> PerformanceClass:
        """Get the performance classification for this mutator in a specific context.

        Args:
            context: Execution context ("in_memory" or "opensearch")

        Returns:
            Performance classification
        """
        if context == "opensearch":
            return self.performance_opensearch
        return self.performance_in_memory
