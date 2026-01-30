"""String manipulation mutators."""

from typing import Any, Dict, Optional

from .base import BaseMutator, PerformanceClass, append_to_result


class LowercaseMutator(BaseMutator):
    """Mutator that converts a string value to lowercase.

    Performance Characteristics:
    - In-memory: FAST - Simple string operation with minimal overhead
    - OpenSearch: MODERATE - Requires post-processing of all results

    Example:
        field | lowercase eq 'hello'
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        # String operations are very fast in memory
        self.performance_in_memory = PerformanceClass.FAST
        # Post-processing in OpenSearch has moderate impact due to result set iteration
        self.performance_opensearch = PerformanceClass.MODERATE

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:
        if isinstance(value, str):
            return value.lower()
        elif isinstance(value, (list, tuple)):
            # Apply lowercase to each element in the array
            return [self.apply(field_name, record, item) if isinstance(item, str) else item for item in value]
        else:
            # For non-string values, return as-is
            return value


class UppercaseMutator(BaseMutator):
    """Mutator that converts a string value to uppercase.

    Performance Characteristics:
    - In-memory: FAST - Simple string operation with minimal overhead
    - OpenSearch: MODERATE - Requires post-processing of all results

    Example:
        field | uppercase eq 'HELLO'
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.performance_in_memory = PerformanceClass.FAST
        self.performance_opensearch = PerformanceClass.MODERATE

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:
        if isinstance(value, str):
            return value.upper()
        elif isinstance(value, (list, tuple)):
            # Apply uppercase to each element in the array
            return [self.apply(field_name, record, item) if isinstance(item, str) else item for item in value]
        else:
            # For non-string values, return as-is
            return value


class TrimMutator(BaseMutator):
    """Mutator that trims whitespace from a string value.

    Performance Characteristics:
    - In-memory: FAST - Simple string operation with minimal overhead
    - OpenSearch: MODERATE - Requires post-processing of all results

    Example:
        field | trim eq 'hello world'
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.performance_in_memory = PerformanceClass.FAST
        self.performance_opensearch = PerformanceClass.MODERATE

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        elif isinstance(value, (list, tuple)):
            # Apply trim to each element in the array
            return [self.apply(field_name, record, item) if isinstance(item, str) else item for item in value]
        else:
            # For non-string values, return as-is
            return value


class SplitMutator(BaseMutator):
    """Mutator that splits a string value on a delimiter."""

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:
        """Apply the split transformation."""
        delimiter = self.params.get("delimiter", " ")
        append_field = self.params.get("field")

        # Perform the split operation
        if value is None:
            # Handle None - return empty list
            split_result = []
        elif isinstance(value, str):
            split_result = value.split(delimiter)
        elif isinstance(value, list):
            # Split each string in the list
            split_result = []
            for item in value:
                if isinstance(item, str):
                    split_result.extend(item.split(delimiter))
                else:
                    # Keep non-string items as-is
                    split_result.append(item)
        elif isinstance(value, (int, float, bool)):
            # Convert to string first, then split
            split_result = str(value).split(delimiter)
        else:
            # For other types (dict, etc), return as single-item list
            # This maintains list type consistency for the split operation
            split_result = [value]

        # If append_field is specified, add to record and return original value
        if append_field:
            append_to_result(record, append_field, split_result)
            return value
        else:
            # Return the split result directly
            return split_result


class LengthMutator(BaseMutator):
    """Mutator that returns the length of a string or list."""

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:
        """Apply the length transformation."""
        append_field = self.params.get("field")

        # Calculate length
        if value is None:
            # Handle None gracefully - treat as empty
            length_value = 0
        elif isinstance(value, (str, list, dict, tuple, set)):
            length_value = len(value)
        elif isinstance(value, (int, float)):
            # For numbers, convert to string and get length
            # This allows checking number of digits
            length_value = len(str(value))
        elif isinstance(value, bool):
            # For booleans, return length of string representation
            length_value = len(str(value))
        else:
            # For other types, try to get length or return 0
            try:
                length_value = len(value)
            except TypeError:
                # If object doesn't support len(), return 0
                length_value = 0

        # If append_field is specified, add to record and return original value
        if append_field:
            append_to_result(record, append_field, length_value)
            return value
        else:
            # Return the length value directly
            return length_value


class ReplaceMutator(BaseMutator):
    """Mutator that replaces all occurrences of a string with another string.

    Performance Characteristics:
    - In-memory: FAST - Simple string operation with minimal overhead
    - OpenSearch: MODERATE - Requires post-processing of all results

    Parameters:
    - find: The string to find (required)
    - replace: The string to replace with (required)
    - field: Optional field to append result to

    Examples:
        # Replace all occurrences
        field | replace(find='old', replace='new')

        # Use as a filter
        field | replace(find='error', replace='warning') contains 'warning'

        # Append to another field
        field | replace(find='/', replace='_', field='sanitized_field')
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.performance_in_memory = PerformanceClass.FAST
        self.performance_opensearch = PerformanceClass.MODERATE

        # Validate required parameters
        if not params:
            raise ValueError("Replace mutator requires 'find' and 'replace' parameters")
        if "find" not in params:
            raise ValueError("Replace mutator requires 'find' parameter")
        if "replace" not in params:
            raise ValueError("Replace mutator requires 'replace' parameter")

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:
        """Apply the replace transformation."""
        find_str = str(self.params["find"])
        replace_str = str(self.params["replace"])
        append_field = self.params.get("field")

        # Perform the replace operation
        result: Any  # Declare result with Any type to handle different types
        if value is None:
            # Handle None - return as is
            result = value
        elif isinstance(value, str):
            result = value.replace(find_str, replace_str)
        elif isinstance(value, (list, tuple)):
            # Apply replace to each string element in the array
            result = []
            for item in value:
                if isinstance(item, str):
                    result.append(item.replace(find_str, replace_str))
                else:
                    # Keep non-string items as-is
                    result.append(item)
        elif isinstance(value, (int, float, bool)):
            # Convert to string first, then replace, then keep as string
            result = str(value).replace(find_str, replace_str)
        else:
            # For other types, return as-is
            result = value

        # If append_field is specified, add to record and return original value
        if append_field:
            append_to_result(record, append_field, result)
            return value
        else:
            # Return the replaced result directly
            return result
