"""Validator functions for the TQL query language.

This module provides functions to validate field values against provided validators.
Validators can be provided as:
  - A Python type (e.g. int, float, str, bool, list, dict).
  - A tuple of the form (container_type, element_type) to check container element types.
  - A callable that accepts the field value and returns a boolean.
  - A string representing a type (for backward compatibility) like "int", "string", etc.
"""

import ipaddress
from typing import Any, Callable, List, Optional, Union


def validate_field_with_validator(  # noqa: C901
    field: Any, validator: Union[type, tuple, Callable[[Any], bool], str]
) -> bool:
    """
    Validate a field value against a single validator.

    The validator may be:
      - A Python type, e.g. int, float, str, bool, list, dict.
      - A tuple (container_type, element_type) to ensure that the field is a container of the element type.
      - A callable that accepts the field and returns a boolean.
      - A string shorthand for a type check (e.g. "int", "string", "list", "ip", "ipv4", "ipv6").

    Args:
        field: The field value to validate.
        validator: The validator to apply.

    Returns:
        True if the field passes the validator, False otherwise.

    Raises:
        ValueError: If the validator is not of a supported form.
    """
    # If validator is a string, map it to a type check.
    if isinstance(validator, str):
        val = validator.lower()
        if val == "int":
            return isinstance(field, int)
        if val == "float":
            return isinstance(field, float)
        if val == "string":
            return isinstance(field, str)
        if val == "bool":
            return isinstance(field, bool)
        if val == "list":
            return isinstance(field, list)
        if val == "dict":
            return isinstance(field, dict)
        if val == "none":
            return field is None
        if val == "ip":
            try:
                ipaddress.ip_address(field)
                return True
            except ValueError:
                return False
        if val == "ipv4":
            try:
                ipaddress.IPv4Address(field)
                return True
            except ValueError:
                return False
        if val == "ipv6":
            try:
                ipaddress.IPv6Address(field)
                return True
            except ValueError:
                return False
        raise ValueError(f"Unknown string validator: {validator}")

    # If validator is a type, use isinstance.
    if isinstance(validator, type):
        return isinstance(field, validator)

    # If validator is a tuple of (container_type, element_type)
    if isinstance(validator, tuple) and len(validator) == 2:
        container_type, element_type = validator
        if not isinstance(field, container_type):
            return False
        return all(isinstance(item, element_type) for item in field)

    # If validator is callable, use it.
    if callable(validator):
        return bool(validator(field))

    raise ValueError("Validator must be a type, a tuple, a callable, or a recognized string.")


def validate_field(
    field: Any, validators: Optional[List[Union[type, tuple, Callable[[Any], bool], str]]] = None
) -> bool:
    """
    Validate a field value against a list of validators.

    Args:
        field: The field value to validate.
        validators: A list of validators to apply.

    Returns:
        True if the field passes all validators, False otherwise.
    """
    if validators is None:
        return True
    for v in validators:
        if not validate_field_with_validator(field, v):
            return False
    return True
