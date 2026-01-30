"""Field access utilities for TQL evaluator.

This module provides utilities for accessing nested fields in records,
handling field mappings, and type conversions.
"""

from typing import Any, Dict


class FieldAccessor:
    """Handles field access operations for TQL evaluation."""

    # Sentinel value to distinguish missing fields from None values
    _MISSING_FIELD = object()

    def get_field_value(self, record: Dict[str, Any], field_path: str) -> Any:  # noqa: C901
        """Get a field value from a record, supporting nested field access.

        Args:
            record: The record dictionary
            field_path: Dot-separated field path (e.g., "user.name")

        Returns:
            The field value or _MISSING_FIELD if not found
        """
        # Split the field path into parts
        parts = field_path.split(".")
        current = record

        for part in parts:
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                elif part.isdigit() and isinstance(current, (list, tuple)):
                    # Support array indexing like "items.0"
                    try:
                        index = int(part)
                        if 0 <= index < len(current):
                            current = current[index]
                        else:
                            return self._MISSING_FIELD
                    except (ValueError, IndexError):
                        return self._MISSING_FIELD
                else:
                    return self._MISSING_FIELD
            elif isinstance(current, (list, tuple)) and part.isdigit():
                # Support direct array indexing
                try:
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return self._MISSING_FIELD
                except (ValueError, IndexError):
                    return self._MISSING_FIELD
            else:
                return self._MISSING_FIELD

        return current

    def apply_field_mapping(self, field_name: str, field_mappings: Dict[str, Any]) -> str:
        """Apply field mapping to get the actual field name.

        Args:
            field_name: Original field name from query
            field_mappings: Field mapping configuration

        Returns:
            Mapped field name
        """
        if field_name not in field_mappings:
            return field_name

        mapping = field_mappings[field_name]

        if isinstance(mapping, str):
            # Simple string mapping
            if mapping not in [
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
                # This is a field name mapping, not a type
                return mapping
            else:
                # This is a type specification, use original field
                return field_name
        elif isinstance(mapping, dict) and mapping:
            # Intelligent mapping - extract the base field
            if "type" in mapping and len(mapping) == 1:
                # Just a type specification, use original field
                return field_name
            else:
                # Find the first field that's not a meta field
                for key in mapping:
                    if key not in ["analyzer", "type", "fields"]:
                        return key

        return field_name

    def apply_type_hint(  # noqa: C901
        self, value: Any, type_hint: str, field_name: str, operator: str, field_mappings: Dict[str, str]
    ) -> Any:
        """Apply type hint to convert value to the appropriate type.

        Args:
            value: Value to convert
            type_hint: Type hint (e.g., 'ip', 'integer', 'boolean')
            field_name: Field name for error messages
            operator: Operator being used
            field_mappings: Field mappings

        Returns:
            Converted value

        Raises:
            TQLError: If conversion fails
        """
        from ..exceptions import TQLError

        if value is None or value is self._MISSING_FIELD:
            return value

        if type_hint == "ip":
            # For IP type hint, validate the IP address format
            import ipaddress

            try:
                # Try to parse as IP address to validate format
                ipaddress.ip_address(str(value))
                # Return as string for comparison
                return str(value)
            except ValueError:
                # For CIDR operator, allow CIDR notation
                if operator in ["cidr", "not_cidr"]:
                    try:
                        ipaddress.ip_network(str(value), strict=False)
                        return str(value)
                    except ValueError:
                        pass
                raise TQLError(f"Invalid IP address format for field '{field_name}': {value}")
        elif type_hint == "integer":
            try:
                return int(value)
            except (ValueError, TypeError):
                raise TQLError(f"Cannot convert value to integer for field '{field_name}': {value}")
        elif type_hint == "float":
            try:
                return float(value)
            except (ValueError, TypeError):
                raise TQLError(f"Cannot convert value to float for field '{field_name}': {value}")
        elif type_hint == "boolean" or type_hint == "bool":
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                if value.lower() == "true" or value == "1":
                    return True
                elif value.lower() == "false" or value == "0":
                    return False
                else:
                    raise TQLError(f"Cannot convert value to boolean for field '{field_name}': {value}")
            else:
                raise TQLError(f"Cannot convert value to boolean for field '{field_name}': {value}")
        elif type_hint == "string":
            return str(value)
        else:
            # Unknown type hint, return value as-is
            return value
