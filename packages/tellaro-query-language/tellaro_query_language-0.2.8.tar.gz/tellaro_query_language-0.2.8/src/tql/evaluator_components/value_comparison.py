"""Value comparison operations for TQL evaluator.

This module handles all value comparison operations including type conversions,
operator implementations, and special cases like CIDR matching.
"""

import ipaddress
import re
from functools import lru_cache
from typing import Any


class ValueComparator:
    """Handles value comparison operations for TQL evaluation."""

    # Sentinel value to distinguish missing fields from None values
    _MISSING_FIELD = object()

    @staticmethod
    @lru_cache(maxsize=256)
    def _compile_regex(pattern: str) -> re.Pattern:
        """Compile and cache regex patterns for performance.

        Args:
            pattern: Regex pattern string

        Returns:
            Compiled regex pattern

        Note:
            Uses LRU cache with max 256 patterns. This significantly improves
            performance when the same regex patterns are used repeatedly in queries.
        """
        return re.compile(pattern)

    def compare_values(self, field_value: Any, operator: str, expected_value: Any) -> bool:  # noqa: C901
        """Compare a field value against an expected value using the given operator.

        Args:
            field_value: Value from the record
            operator: Comparison operator
            expected_value: Expected value from the query

        Returns:
            Boolean result of comparison
        """
        # Handle missing fields
        if field_value is self._MISSING_FIELD:
            if operator in ["exists"]:
                return False
            elif operator in ["not_exists"]:
                return True  # Field doesn't exist, so "not exists" is true
            elif operator == "is_not":
                # For "is not null", missing fields should return False (to match OpenSearch behavior)
                # OpenSearch "is not null" translates to "exists", which only matches if field is present
                return False  # Missing fields return False for all "is not" comparisons
            # For negated string operators, missing fields should return True
            # (e.g., if field doesn't exist, it doesn't contain/start with/end with the value)
            elif operator in ["not_contains", "not_startswith", "not_endswith", "not_regexp"]:
                return True
            # For not_cidr, missing fields should return False (can't check CIDR on missing IP)
            elif operator in ["cidr", "not_cidr"]:
                return False
            # Note: for is_not operations, missing fields are treated as non-matching
            else:
                # Missing fields return False for all other operators
                return False

        # Handle None field values (field exists but is None)
        # IMPORTANT: None is a valid value, distinct from missing fields.
        # For 'exists' operator: This code path should NOT be reached because 'exists'
        # checks field presence in the record, not the value. The evaluator handles
        # 'exists' before calling compare_values. If we reach here with None, it means
        # the field exists but has None value, which should NOT match 'exists'.
        if field_value is None:
            if operator in ["exists"]:
                # Field key exists in record but value is None
                # Semantics: 'exists' means "field has a non-null value"
                # This matches database behavior where NULL != EXISTS
                return False  # None value does not satisfy 'exists'
            elif operator in ["is"]:
                # Check for null comparison - expected_value can be None or "null"
                return expected_value is None or (isinstance(expected_value, str) and expected_value.lower() == "null")
            else:
                return False

        # Convert numeric strings to numbers for comparison
        field_value = self._convert_numeric(field_value)
        expected_value = self._convert_numeric(expected_value)

        # Convert boolean strings to booleans for comparison
        if isinstance(expected_value, str) and expected_value.lower() in ["true", "false"]:
            expected_value = expected_value.lower() == "true"
        if isinstance(field_value, str) and field_value.lower() in ["true", "false"]:
            field_value = field_value.lower() == "true"

        # Type compatibility check for numeric operators
        # If operator requires numeric comparison, both values must be numeric
        # Exception: Arrays are handled specially in the operator logic below
        if operator in ["gt", "gte", "lt", "lte", ">", ">=", "<", "<="]:
            # Skip check if field_value is an array - handled by array logic below
            if not isinstance(field_value, (list, tuple)):
                field_is_numeric = isinstance(field_value, (int, float)) and not isinstance(field_value, bool)
                expected_is_numeric = isinstance(expected_value, (int, float)) and not isinstance(expected_value, bool)

                if not (field_is_numeric and expected_is_numeric):
                    # At least one value failed numeric conversion
                    # Cannot perform numeric comparison - return False
                    return False

        try:
            if operator in ["eq", "="]:
                # Handle array fields - check if ANY element equals expected value
                if isinstance(field_value, (list, tuple)):
                    return expected_value in field_value
                return field_value == expected_value
            elif operator in ["ne", "!="]:
                # Handle array fields - check if expected value is NOT in array
                if isinstance(field_value, (list, tuple)):
                    return expected_value not in field_value
                return field_value != expected_value
            elif operator in ["gt", ">"]:
                # Handle array fields - check if ANY element is greater than expected value
                if isinstance(field_value, (list, tuple)):
                    return any(self._convert_numeric(elem) > expected_value for elem in field_value)
                return field_value > expected_value
            elif operator in ["gte", ">="]:
                # Handle array fields - check if ANY element is greater than or equal to expected value
                if isinstance(field_value, (list, tuple)):
                    return any(self._convert_numeric(elem) >= expected_value for elem in field_value)
                return field_value >= expected_value
            elif operator in ["lt", "<"]:
                # Handle array fields - check if ANY element is less than expected value
                if isinstance(field_value, (list, tuple)):
                    return any(self._convert_numeric(elem) < expected_value for elem in field_value)
                return field_value < expected_value
            elif operator in ["lte", "<="]:
                # Handle array fields - check if ANY element is less than or equal to expected value
                if isinstance(field_value, (list, tuple)):
                    return any(self._convert_numeric(elem) <= expected_value for elem in field_value)
                return field_value <= expected_value
            elif operator == "contains":
                # Unwrap single-element lists for string operators
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]
                # Handle list fields by checking if ANY element contains the expected value
                # Case-insensitive comparison to match post-processor behavior
                if isinstance(field_value, list):
                    # For arrays, check if ANY element contains the expected value
                    return any(str(expected_value).lower() in str(elem).lower() for elem in field_value)
                else:
                    return str(expected_value).lower() in str(field_value).lower()
            elif operator == "startswith":
                # Unwrap single-element lists for string operators
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]
                # Handle array fields - check if ANY element starts with expected value
                # Case-insensitive comparison to match post-processor behavior
                if isinstance(field_value, (list, tuple)):
                    return any(str(elem).lower().startswith(str(expected_value).lower()) for elem in field_value)
                return str(field_value).lower().startswith(str(expected_value).lower())
            elif operator == "endswith":
                # Unwrap single-element lists for string operators
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]
                # Handle array fields - check if ANY element ends with expected value
                # Case-insensitive comparison to match post-processor behavior
                if isinstance(field_value, (list, tuple)):
                    return any(str(elem).lower().endswith(str(expected_value).lower()) for elem in field_value)
                return str(field_value).lower().endswith(str(expected_value).lower())
            elif operator == "in":
                if isinstance(expected_value, list):
                    # Convert list elements to appropriate types for comparison
                    converted_list = [self._convert_numeric(val) for val in expected_value]

                    if isinstance(field_value, (list, tuple)):
                        # Field is an array - check if ANY element of field equals ANY value in list
                        # This handles both:
                        # - "value" in field (single expected value, array field)
                        # - field in ["val1", "val2"] (multiple expected values, array field)
                        return any(elem in converted_list for elem in field_value)
                    else:
                        # Scalar field - check if field_value is in the list
                        return field_value in converted_list
                else:
                    return field_value == expected_value
            elif operator == "regexp":
                # Unwrap single-element lists for string operators
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]
                # Use cached regex compilation for performance
                try:
                    pattern = self._compile_regex(str(expected_value))
                    return bool(pattern.search(str(field_value)))
                except (re.error, TypeError):
                    # Invalid regex pattern, fall back to no match
                    return False
            elif operator == "cidr":
                # Unwrap single-element lists for CIDR
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]
                return self._check_cidr(field_value, expected_value)
            elif operator == "exists":
                return True  # If we got here, field exists
            elif operator == "is":
                # Handle null comparison specially
                if isinstance(expected_value, str) and expected_value.lower() == "null":
                    return field_value is None
                # Handle boolean and other literal comparisons
                return field_value is expected_value
            elif operator == "between":
                # between requires a list with two values
                if isinstance(expected_value, list) and len(expected_value) == 2:
                    # Convert string values to appropriate numeric types if needed
                    val1 = self._convert_numeric(expected_value[0])
                    val2 = self._convert_numeric(expected_value[1])

                    # Allow values in any order (determine lower and upper bounds)
                    lower_bound = min(val1, val2)
                    upper_bound = max(val1, val2)

                    # Perform range check
                    return lower_bound <= field_value <= upper_bound
                else:
                    return False

            # Negated operators - return the opposite of the base operator
            elif operator == "not_exists":
                # Field should not exist (handled earlier for missing fields)
                return False  # If we got here, field exists, so return False
            elif operator == "is_not":
                # Handle null comparison specially
                if isinstance(expected_value, str) and expected_value.lower() == "null":
                    return field_value is not None
                # Handle boolean and other literal comparisons
                return field_value is not expected_value
            elif operator == "not_in":
                if isinstance(expected_value, list):
                    # Convert list elements to appropriate types for comparison
                    converted_list = [self._convert_numeric(val) for val in expected_value]
                    return field_value not in converted_list
                else:
                    return field_value != expected_value
            elif operator == "not_contains":
                # Unwrap single-element lists for string operators
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]
                # Case-insensitive comparison to match post-processor behavior
                return str(expected_value).lower() not in str(field_value).lower()
            elif operator == "not_startswith":
                # Unwrap single-element lists for string operators
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]
                # Case-insensitive comparison to match post-processor behavior
                return not str(field_value).lower().startswith(str(expected_value).lower())
            elif operator == "not_endswith":
                # Unwrap single-element lists for string operators
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]
                # Case-insensitive comparison to match post-processor behavior
                return not str(field_value).lower().endswith(str(expected_value).lower())
            elif operator == "not_regexp":
                # Unwrap single-element lists for string operators
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]
                # Use cached regex compilation for performance
                try:
                    pattern = self._compile_regex(str(expected_value))
                    return not bool(pattern.search(str(field_value)))
                except (re.error, TypeError):
                    # Invalid regex pattern, fall back to match (not regexp succeeds)
                    return True
            elif operator == "not_cidr":
                # Unwrap single-element lists for CIDR
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]
                return not self._check_cidr(field_value, expected_value)
            elif operator == "not_between":
                # not between requires a list with two values
                if isinstance(expected_value, list) and len(expected_value) == 2:
                    # Convert string values to appropriate numeric types if needed
                    val1 = self._convert_numeric(expected_value[0])
                    val2 = self._convert_numeric(expected_value[1])

                    # Allow values in any order (determine lower and upper bounds)
                    lower_bound = min(val1, val2)
                    upper_bound = max(val1, val2)

                    # Perform range check (opposite of between)
                    return not lower_bound <= field_value <= upper_bound
                else:
                    return False
            elif operator == "any":
                # ANY operator - matches if the value equals any element (for arrays)
                # or equals the value (for single values)
                # Handle case where expected_value might be wrapped in a list
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]

                if isinstance(field_value, (list, tuple, set)):
                    # For arrays, check if expected value is in the array
                    return expected_value in field_value
                else:
                    # For single values, just check equality
                    return field_value == expected_value
            elif operator == "all":
                # ALL operator - for arrays, all elements must equal the value
                # For single values, it's just equality
                # Handle case where expected_value might be wrapped in a list
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]

                if isinstance(field_value, (list, tuple, set)):
                    # For arrays, all elements must equal the expected value
                    return all(elem == expected_value for elem in field_value) if field_value else False
                else:
                    # For single values, just check equality
                    return field_value == expected_value
            elif operator == "not_any":
                # NOT ANY - the value should not equal any element
                # Handle case where expected_value might be wrapped in a list
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]

                if isinstance(field_value, (list, tuple, set)):
                    # For arrays, expected value should not be in the array
                    return expected_value not in field_value
                else:
                    # For single values, check inequality
                    return field_value != expected_value
            elif operator == "not_all":
                # NOT ALL - at least one element doesn't equal the value
                # Handle case where expected_value might be wrapped in a list
                if isinstance(expected_value, list) and len(expected_value) == 1:
                    expected_value = expected_value[0]

                if isinstance(field_value, (list, tuple, set)):
                    # For arrays, at least one element must not equal the expected value
                    # This is true if ANY element doesn't match
                    return any(elem != expected_value for elem in field_value) if field_value else True
                else:
                    # For single values, NOT ALL means the opposite of ALL
                    # If the single value matches, then ALL match, so NOT ALL is false
                    return field_value != expected_value
            else:
                raise ValueError(f"Unknown operator: {operator}")
        except (TypeError, ValueError):
            # Type mismatch or conversion error
            return False

    def _convert_numeric(self, value: Any) -> Any:
        """Convert string numbers and booleans to appropriate types.

        Args:
            value: Value to convert

        Returns:
            Converted value (int, float, bool, or original)
        """
        if isinstance(value, str):
            # Try to convert to int
            try:
                # Check if it's a valid integer
                if "." not in value and "e" not in value.lower() and "E" not in value:
                    return int(value)
            except ValueError:
                pass

            # Try to convert to float
            try:
                return float(value)
            except ValueError:
                pass

            # Try to convert to boolean
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False

        return value

    def _check_cidr(self, ip_value: Any, cidr: str) -> bool:
        """Check if an IP address matches a CIDR pattern.

        Args:
            ip_value: IP address to check
            cidr: CIDR pattern

        Returns:
            True if IP is in CIDR range
        """
        try:
            # Convert IP value to string if needed
            ip_str = str(ip_value)
            # Create network from CIDR
            network = ipaddress.ip_network(cidr, strict=False)
            # Check if IP is in network
            ip = ipaddress.ip_address(ip_str)
            return ip in network
        except (ValueError, TypeError):
            # Invalid IP or CIDR
            return False
