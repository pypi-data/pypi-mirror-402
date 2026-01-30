"""Encoding and decoding mutators."""

from typing import Any, Dict, Optional

from .base import BaseMutator, append_to_result


class Base64EncodeMutator(BaseMutator):
    """
    Mutator that encodes values to base64.

    This is an enrichment mutator that can encode strings to base64
    format. It supports encoding individual strings or lists of strings.

    Parameters:
        field: Optional field to store the encoded value
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.is_enrichment = True

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:  # noqa: C901
        """Apply the base64 encode transformation."""
        import base64

        append_field = self.params.get("field")

        # Handle different input types
        encoded_value: Any
        if value is None:
            encoded_value = None
        elif isinstance(value, str):
            # Encode string to base64
            try:
                encoded_value = base64.b64encode(value.encode("utf-8")).decode("ascii")
            except Exception:
                encoded_value = None
        elif isinstance(value, bytes):
            # Already bytes, encode directly
            try:
                encoded_value = base64.b64encode(value).decode("ascii")
            except Exception:
                encoded_value = None
        elif isinstance(value, list):
            # Encode each item in the list
            encoded_value = []
            for item in value:
                if isinstance(item, str):
                    try:
                        encoded = base64.b64encode(item.encode("utf-8")).decode("ascii")
                        encoded_value.append(encoded)
                    except Exception:
                        encoded_value.append(None)
                elif isinstance(item, bytes):
                    try:
                        encoded = base64.b64encode(item).decode("ascii")
                        encoded_value.append(encoded)
                    except Exception:
                        encoded_value.append(None)
                else:
                    # For None, keep as None
                    if item is None:
                        encoded_value.append(None)
                    else:
                        # Convert to string first
                        try:
                            encoded = base64.b64encode(str(item).encode("utf-8")).decode("ascii")
                            encoded_value.append(encoded)
                        except Exception:
                            encoded_value.append(None)
        else:
            # For other types, convert to string and encode
            try:
                encoded_value = base64.b64encode(str(value).encode("utf-8")).decode("ascii")
            except Exception:
                encoded_value = None

        # If field is specified, add to record and return original value
        if append_field:
            append_to_result(record, append_field, encoded_value)
            return value
        else:
            # Return the encoded value directly
            return encoded_value


class Base64DecodeMutator(BaseMutator):
    """
    Mutator that decodes base64 values.

    This is an enrichment mutator that can decode base64-encoded strings
    back to their original form. It supports decoding individual strings
    or lists of strings.

    Parameters:
        field: Optional field to store the decoded value
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.is_enrichment = True

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:  # noqa: C901
        """Apply the base64 decode transformation."""
        import base64

        append_field = self.params.get("field")

        # Handle different input types
        decoded_value: Any
        if value is None:
            decoded_value = None
        elif isinstance(value, str):
            # Decode base64 string
            try:
                # Handle padding if missing
                padding = 4 - (len(value) % 4)
                if padding and padding != 4:
                    value += "=" * padding
                decoded_value = base64.b64decode(value).decode("utf-8")
            except Exception:
                # If decoding fails, return None or original
                decoded_value = None
        elif isinstance(value, list):
            # Decode each item in the list
            decoded_value = []
            for item in value:
                if isinstance(item, str):
                    try:
                        # Handle padding if missing
                        padding = 4 - (len(item) % 4)
                        if padding and padding != 4:
                            item += "=" * padding
                        decoded = base64.b64decode(item).decode("utf-8")
                        decoded_value.append(decoded)
                    except Exception:
                        decoded_value.append(None)
                else:
                    decoded_value.append(item)
        else:
            # For other types, try to decode as string
            try:
                value_str = str(value)
                padding = 4 - (len(value_str) % 4)
                if padding and padding != 4:
                    value_str += "=" * padding
                decoded_value = base64.b64decode(value_str).decode("utf-8")
            except Exception:
                decoded_value = None

        # If field is specified, add to record and return original value
        if append_field:
            append_to_result(record, append_field, decoded_value)
            return value
        else:
            # Return the decoded value directly
            return decoded_value


class URLDecodeMutator(BaseMutator):
    """
    Mutator that decodes URL-encoded values.

    This is an enrichment mutator that decodes URL-encoded strings
    (e.g., %20 -> space, %2F -> /). It supports decoding individual
    strings or lists of strings.

    Parameters:
        field: Optional field to store the decoded value
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.is_enrichment = True

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:  # noqa: C901
        """Apply the URL decode transformation."""
        import urllib.parse

        append_field = self.params.get("field")

        # Handle different input types
        decoded_value: Any
        if value is None:
            decoded_value = None
        elif isinstance(value, str):
            # Decode URL-encoded string
            try:
                decoded_value = urllib.parse.unquote(value)
            except Exception:
                decoded_value = value  # Return original if decode fails
        elif isinstance(value, list):
            # Decode each item in the list
            decoded_value = []
            for item in value:
                if isinstance(item, str):
                    try:
                        decoded = urllib.parse.unquote(item)
                        decoded_value.append(decoded)
                    except Exception:
                        decoded_value.append(item)
                else:
                    decoded_value.append(item)
        else:
            # For other types, convert to string and decode
            try:
                decoded_value = urllib.parse.unquote(str(value))
            except Exception:
                decoded_value = str(value)

        # If field is specified, add to record and return original value
        if append_field:
            append_to_result(record, append_field, decoded_value)
            return value
        else:
            # Return the decoded value directly
            return decoded_value
