"""List evaluation mutators for aggregate operations."""

from typing import Any, Dict

from .base import BaseMutator


class AnyMutator(BaseMutator):
    """
    Mutator that evaluates if any element in a list is truthy.

    For lists: Returns True if any element is truthy.
    For single values: Returns the truthiness of the value.
    For None/empty: Returns False.
    """

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:  # noqa: C901
        """Apply the any transformation."""
        if value is None:
            return False
        elif isinstance(value, list):
            return any(value)
        else:
            # For single values, return truthiness
            return bool(value)


class AllMutator(BaseMutator):
    """
    Mutator that evaluates if all elements in a list are truthy.

    For lists: Returns True if all elements are truthy.
    For single values: Returns the truthiness of the value.
    For None: Returns False.
    For empty lists: Returns True (following Python's all() behavior).
    """

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:  # noqa: C901
        """Apply the all transformation."""
        if value is None:
            return False
        elif isinstance(value, list):
            return all(value)
        else:
            # For single values, return truthiness
            return bool(value)


class AvgMutator(BaseMutator):
    """
    Mutator that calculates the average of numeric values.

    For lists: Returns the average of numeric elements.
    For single numeric values: Returns the value itself.
    For non-numeric or empty: Returns None.
    """

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:  # noqa: C901
        """Apply the average transformation."""
        if value is None:
            return None
        elif isinstance(value, list):
            numeric_values = []
            for item in value:
                if isinstance(item, (int, float)) and not isinstance(item, bool):
                    numeric_values.append(item)
                elif isinstance(item, str):
                    # Try to convert string to number
                    try:
                        numeric_values.append(float(item))
                    except ValueError:
                        pass

            if numeric_values:
                return sum(numeric_values) / len(numeric_values)
            else:
                return None
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
        elif isinstance(value, str):
            # Try to convert string to number
            try:
                return float(value)
            except ValueError:
                return None
        else:
            return None


# Alias for AvgMutator
class AverageMutator(AvgMutator):
    """Alias for AvgMutator."""


class SumMutator(BaseMutator):
    """
    Mutator that calculates the sum of numeric values.

    For lists: Returns the sum of numeric elements.
    For single numeric values: Returns the value itself.
    For non-numeric or empty: Returns 0.
    """

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:  # noqa: C901
        """Apply the sum transformation."""
        if value is None:
            return 0
        elif isinstance(value, list):
            numeric_values = []
            for item in value:
                if isinstance(item, (int, float)) and not isinstance(item, bool):
                    numeric_values.append(item)
                elif isinstance(item, str):
                    # Try to convert string to number
                    try:
                        numeric_values.append(float(item))
                    except ValueError:
                        pass

            return sum(numeric_values) if numeric_values else 0
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
        elif isinstance(value, str):
            # Try to convert string to number
            try:
                return float(value)
            except ValueError:
                return 0
        else:
            return 0


class MaxMutator(BaseMutator):
    """
    Mutator that finds the maximum value.

    For lists: Returns the maximum of comparable elements.
    For single values: Returns the value itself.
    For empty or incomparable: Returns None.
    """

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:  # noqa: C901
        """Apply the max transformation."""
        if value is None:
            return None
        elif isinstance(value, list):
            if not value:
                return None

            # Filter out None values
            filtered_values = [v for v in value if v is not None]
            if not filtered_values:
                return None

            try:
                return max(filtered_values)
            except (TypeError, ValueError):
                # If values aren't comparable, try numeric conversion
                numeric_values = []
                for item in filtered_values:
                    if isinstance(item, (int, float)) and not isinstance(item, bool):
                        numeric_values.append(item)
                    elif isinstance(item, str):
                        try:
                            numeric_values.append(float(item))
                        except ValueError:
                            pass

                return max(numeric_values) if numeric_values else None
        else:
            return value


class MinMutator(BaseMutator):
    """
    Mutator that finds the minimum value.

    For lists: Returns the minimum of comparable elements.
    For single values: Returns the value itself.
    For empty or incomparable: Returns None.
    """

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:  # noqa: C901
        """Apply the min transformation."""
        if value is None:
            return None
        elif isinstance(value, list):
            if not value:
                return None

            # Filter out None values
            filtered_values = [v for v in value if v is not None]
            if not filtered_values:
                return None

            try:
                return min(filtered_values)
            except (TypeError, ValueError):
                # If values aren't comparable, try numeric conversion
                numeric_values = []
                for item in filtered_values:
                    if isinstance(item, (int, float)) and not isinstance(item, bool):
                        numeric_values.append(item)
                    elif isinstance(item, str):
                        try:
                            numeric_values.append(float(item))
                        except ValueError:
                            pass

                return min(numeric_values) if numeric_values else None
        else:
            return value
