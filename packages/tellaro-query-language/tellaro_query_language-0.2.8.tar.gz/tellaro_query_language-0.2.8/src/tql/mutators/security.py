"""Security-related mutators for defanging and refanging URLs and indicators."""

from typing import Any, Dict

from .base import BaseMutator, append_to_result


class RefangMutator(BaseMutator):
    """
    Mutator that refangs (un-defangs) URLs and indicators.

    This mutator reverses common defanging patterns to make URLs and
    indicators clickable/active again. It handles various defanging patterns:
    - hXXp:// -> http://
    - hXXps:// -> https://
    - [.]  -> .
    - [.] -> .
    - [:]  -> :
    - [:] -> :
    - fXp:// -> ftp://
    - [at] -> @
    - [@] -> @

    Parameters:
        field: Optional field to store the refanged value
    """

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:
        """Apply the refang transformation."""
        append_field = self.params.get("field")

        # Handle different input types
        refanged_value: Any
        if value is None:
            refanged_value = None
        elif isinstance(value, str):
            refanged_value = self._refang_string(value)
        elif isinstance(value, list):
            # Refang each string in the list
            refanged_value = []
            for item in value:
                if isinstance(item, str):
                    refanged_value.append(self._refang_string(item))
                else:
                    refanged_value.append(item)
        elif isinstance(value, (int, float, bool)):
            # Convert to string, refang, then return
            refanged_value = self._refang_string(str(value))
        else:
            # For other types, return as-is
            refanged_value = value

        # If append_field is specified, add to record and return original value
        if append_field:
            append_to_result(record, append_field, refanged_value)
            return value
        else:
            # Return the refanged value directly
            return refanged_value

    def _refang_string(self, s: str) -> str:
        """Refang a single string."""
        import re

        result = s

        # Apply replacements for common defanging patterns
        # Handle various protocol defanging patterns (case insensitive)
        # Important: Check for 'ps' suffix first to avoid false matches
        result = re.sub(r"h[xX]{1,2}ps://", "https://", result, flags=re.IGNORECASE)
        result = re.sub(r"h[xX]{1,2}p://", "http://", result, flags=re.IGNORECASE)
        result = re.sub(r"f[xX]p://", "ftp://", result, flags=re.IGNORECASE)

        # Handle bracketed replacements with optional spaces
        result = re.sub(r"\s*\[\.\]\s*", ".", result)
        result = re.sub(r"\s*\[:\]\s*", ":", result)
        result = re.sub(r"\s*\[at\]\s*", "@", result, flags=re.IGNORECASE)
        result = re.sub(r"\s*\[@\]\s*", "@", result)
        result = re.sub(r"\s*\[/\]\s*", "/", result)

        # Handle parentheses replacements
        result = re.sub(r"\s*\(\.\)\s*", ".", result)
        result = re.sub(r"\s*\(:\)\s*", ":", result)
        result = re.sub(r"\s*\(at\)\s*", "@", result, flags=re.IGNORECASE)
        result = re.sub(r"\s*\(@\)\s*", "@", result)
        result = re.sub(r"\s*\(/\)\s*", "/", result)

        # Handle braces replacements
        result = re.sub(r"\s*\{\.\}\s*", ".", result)
        result = re.sub(r"\s*\{:\}\s*", ":", result)
        result = re.sub(r"\s*\{at\}\s*", "@", result, flags=re.IGNORECASE)
        result = re.sub(r"\s*\{@\}\s*", "@", result)
        result = re.sub(r"\s*\{/\}\s*", "/", result)

        # Handle word replacements with optional brackets/parentheses/braces
        result = re.sub(r"\s*\[dot\]\s*", ".", result, flags=re.IGNORECASE)
        result = re.sub(r"\s*\(dot\)\s*", ".", result, flags=re.IGNORECASE)
        result = re.sub(r"\s*\{dot\}\s*", ".", result, flags=re.IGNORECASE)

        return result


class DefangMutator(BaseMutator):
    """
    Mutator that defangs URLs and indicators to make them unclickable.

    This mutator applies common defanging patterns to URLs and indicators
    to prevent accidental clicks or automatic processing:
    - http:// -> hXXp://
    - https:// -> hXXps://
    - . -> [.]
    - : -> [:]
    - @ -> [at]
    - ftp:// -> fXp://

    Parameters:
        field: Optional field to store the defanged value
    """

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:
        """Apply the defang transformation."""
        append_field = self.params.get("field")

        # Handle different input types
        defanged_value: Any
        if value is None:
            defanged_value = None
        elif isinstance(value, str):
            defanged_value = self._defang_string(value)
        elif isinstance(value, list):
            # Defang each string in the list
            defanged_value = []
            for item in value:
                if isinstance(item, str):
                    defanged_value.append(self._defang_string(item))
                else:
                    defanged_value.append(item)
        elif isinstance(value, (int, float, bool)):
            # Convert to string, defang, then return
            defanged_value = self._defang_string(str(value))
        else:
            # For other types, return as-is
            defanged_value = value

        # If append_field is specified, add to record and return original value
        if append_field:
            append_to_result(record, append_field, defanged_value)
            return value
        else:
            # Return the defanged value directly
            return defanged_value

    def _defang_string(self, s: str) -> str:  # noqa: C901
        """Defang a single string."""
        import re

        result = s

        # Check if fully defanged to avoid double-defanging
        # Only return early if all components are already defanged
        has_defanged_protocol = "hxxp" in result.lower() or "fxp" in result.lower()
        has_defanged_dots = "[.]" in result
        has_defanged_at = "[at]" in result

        # If it's a URL with protocol, check if dots are defanged
        if has_defanged_protocol and "://" in result:
            # Extract the part after protocol
            _, after_protocol = result.split("://", 1)
            # If dots in the URL part are already defanged, return as-is
            if "." not in after_protocol or has_defanged_dots:
                return result
        # For non-URLs, if already has defanged components, return
        elif has_defanged_dots and has_defanged_at:
            return result

        # First, replace protocols (case-insensitive) with lowercase hxxp/hxxps/fxp
        result = re.sub(r"https://", "hxxps://", result, flags=re.IGNORECASE)
        result = re.sub(r"http://", "hxxp://", result, flags=re.IGNORECASE)
        result = re.sub(r"ftp://", "fxp://", result, flags=re.IGNORECASE)

        # Split the string to process URLs, emails, and domains separately
        # Match URLs first since they're more specific
        url_pattern = r"((?:hxxps?|fxp|https?|ftp)://[^\s]+)"
        parts = re.split(url_pattern, result)

        defanged_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 1:  # This is a URL match
                # For URLs, defang the domain part only
                if "://" in part:
                    protocol, rest = part.split("://", 1)
                    # Defang dots in the domain/path (avoid double-defanging)
                    if "[.]" not in rest:
                        rest = rest.replace(".", "[.]")
                    # Defang @ if present (for URLs with auth)
                    if "[at]" not in rest:
                        rest = rest.replace("@", "[at]")
                    # Defang colons in port numbers (e.g., :8080)
                    rest = re.sub(r":(\d+)", r"[:]\1", rest)
                    defanged_parts.append(f"{protocol}://{rest}")
                else:
                    defanged_parts.append(part)
            else:
                # For non-URL text, handle email addresses and domain patterns
                # First, handle email addresses
                email_pattern = r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
                part = re.sub(email_pattern, lambda m: f"{m.group(1)}[at]{m.group(2).replace('.', '[.]')}", part)  # type: ignore[arg-type, str-bytes-safe]

                # Then handle standalone IP addresses
                ip_pattern = r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b"
                part = re.sub(ip_pattern, lambda m: m.group(0).replace(".", "[.]"), part)  # type: ignore[arg-type]

                # Finally handle standalone domain patterns (but not IPs)
                domain_pattern = r"\b([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)\b"

                def defang_domain(match):
                    domain = match.group(0)
                    # Only defang if not already defanged and not an IP address
                    if "[.]" not in domain and not re.match(r"^\d+\.\d+\.\d+\.\d+$", domain):
                        return domain.replace(".", "[.]")
                    return domain

                part = re.sub(domain_pattern, defang_domain, part)
                defanged_parts.append(part)

        return "".join(defanged_parts)
