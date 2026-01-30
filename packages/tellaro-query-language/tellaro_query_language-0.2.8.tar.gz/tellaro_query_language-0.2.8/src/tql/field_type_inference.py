"""Field type inference for CSV and other structured data files.

This module provides utilities to automatically detect field types from sample data,
supporting various data formats including numbers, booleans, dates, and strings.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class FieldTypeInferencer:
    """Infers field types from sample data records."""

    # Common date/timestamp patterns
    DATE_PATTERNS = [
        (r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "%Y-%m-%dT%H:%M:%S"),  # ISO 8601
        (r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "%Y-%m-%d %H:%M:%S"),  # SQL datetime
        (r"^\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),  # Date only
        (r"^\d{2}/\d{2}/\d{4}", "%m/%d/%Y"),  # US date
        (r"^\d{2}-\d{2}-\d{4}", "%d-%m-%Y"),  # EU date
    ]

    # Boolean value mappings
    BOOLEAN_VALUES = {
        "true": True,
        "false": False,
        "yes": True,
        "no": False,
        "t": True,
        "f": False,
        "y": True,
        "n": False,
        "1": True,
        "0": False,
        "on": True,
        "off": False,
    }

    def __init__(self, sample_size: int = 100):
        """Initialize the inferencer.

        Args:
            sample_size: Number of records to sample for type inference
        """
        self.sample_size = sample_size

    def infer_from_records(
        self, records: List[Dict[str, Any]], field_overrides: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Infer field types from a list of records.

        Args:
            records: List of dictionaries representing records
            field_overrides: Optional manual field type overrides

        Returns:
            Dictionary mapping field names to inferred types
        """
        if not records:
            return {}

        # Sample records if we have more than sample_size
        sample = records[: self.sample_size] if len(records) > self.sample_size else records

        # Collect all field names
        all_fields: set[str] = set()
        for record in sample:
            all_fields.update(record.keys())

        # Infer type for each field
        field_types = {}
        for field in all_fields:
            # Check for manual override first
            if field_overrides and field in field_overrides:
                field_types[field] = field_overrides[field]
            else:
                field_types[field] = self._infer_field_type(field, sample)

        return field_types

    def _infer_field_type(self, field: str, records: List[Dict[str, Any]]) -> str:  # noqa: C901
        """Infer the type of a single field from sample records.

        Args:
            field: Field name
            records: Sample records

        Returns:
            Inferred type string ('integer', 'float', 'boolean', 'date', 'string')
        """
        # Collect non-null values
        values = []
        for record in records:
            if field in record and record[field] is not None and record[field] != "":
                values.append(record[field])

        if not values:
            return "string"  # Default for empty fields

        # If values are already typed (from JSON), use those types
        if all(isinstance(v, bool) for v in values):
            return "boolean"
        if all(isinstance(v, int) for v in values):
            return "integer"
        if all(isinstance(v, (int, float)) for v in values):
            return "float"

        # For string values, try to infer more specific types
        string_values = [str(v) for v in values]

        # Try boolean detection
        if self._is_boolean_field(string_values):
            return "boolean"

        # Try integer detection
        if self._is_integer_field(string_values):
            return "integer"

        # Try float detection
        if self._is_float_field(string_values):
            return "float"

        # Try date detection
        if self._is_date_field(string_values):
            return "date"

        # Default to string
        return "string"

    def _is_boolean_field(self, values: List[str]) -> bool:
        """Check if values represent boolean data."""
        # At least 80% of values should be recognizable boolean values
        boolean_count = sum(1 for v in values if v.lower() in self.BOOLEAN_VALUES)
        return boolean_count / len(values) >= 0.8

    def _is_integer_field(self, values: List[str]) -> bool:
        """Check if values represent integer data."""
        try:
            for v in values:
                int(v)
            return True
        except (ValueError, TypeError):
            return False

    def _is_float_field(self, values: List[str]) -> bool:
        """Check if values represent floating point data."""
        try:
            for v in values:
                float(v)
            return True
        except (ValueError, TypeError):
            return False

    def _is_date_field(self, values: List[str]) -> bool:
        """Check if values represent date/timestamp data."""
        # Try each date pattern
        match_counts = []
        for pattern, _ in self.DATE_PATTERNS:
            matches = sum(1 for v in values if re.match(pattern, v))
            match_counts.append(matches)

        # If any pattern matches at least 80% of values, consider it a date field
        best_match_rate = max(match_counts) / len(values) if match_counts else 0
        return best_match_rate >= 0.8

    def detect_csv_headers(self, first_row: List[str], second_row: List[str]) -> bool:
        """Detect if the first row of a CSV is a header row.

        Uses heuristics to determine if first row looks like column names.

        Args:
            first_row: First row values
            second_row: Second row values

        Returns:
            True if first row appears to be headers
        """
        if not first_row or not second_row:
            return False

        # Heuristic 1: First row all strings, second row has numbers
        first_row_all_alpha = all(self._is_mostly_alpha(val) for val in first_row)
        second_row_has_numbers = any(self._is_numeric(val) for val in second_row)

        if first_row_all_alpha and second_row_has_numbers:
            return True

        # Heuristic 2: First row has no duplicates (headers should be unique)
        if len(first_row) != len(set(first_row)):
            return False

        # Heuristic 3: First row values look like identifiers (snake_case, camelCase, etc.)
        identifier_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        identifier_count = sum(1 for val in first_row if identifier_pattern.match(val))
        if identifier_count / len(first_row) >= 0.7:
            return True

        # Heuristic 4: Second row has more varied types than first row
        first_row_types = self._get_value_types(first_row)
        second_row_types = self._get_value_types(second_row)

        if len(second_row_types) > len(first_row_types):
            return True

        # Default to no header if inconclusive
        return False

    def _is_mostly_alpha(self, value: str) -> bool:
        """Check if value is mostly alphabetic (for header detection)."""
        if not value:
            return False
        alpha_count = sum(1 for c in value if c.isalpha() or c in "_- ")
        return alpha_count / len(value) >= 0.5

    def _is_numeric(self, value: str) -> bool:
        """Check if value is numeric."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def _get_value_types(self, values: List[str]) -> set:
        """Get set of value types in a list."""
        types = set()
        for val in values:
            if self._is_numeric(val):
                types.add("numeric")
            elif val.lower() in self.BOOLEAN_VALUES:
                types.add("boolean")
            elif any(re.match(pattern, val) for pattern, _ in self.DATE_PATTERNS):
                types.add("date")
            else:
                types.add("string")
        return types

    def convert_value(self, value: Any, field_type: str) -> Any:
        """Convert a value to its inferred type.

        Args:
            value: Raw value (usually string from CSV)
            field_type: Target type

        Returns:
            Converted value
        """
        if value is None or value == "":
            return None

        try:
            if field_type == "integer":
                return int(value)
            elif field_type == "float":
                return float(value)
            elif field_type == "boolean":
                str_val = str(value).lower()
                return self.BOOLEAN_VALUES.get(str_val, bool(value))
            elif field_type == "date":
                # Try to parse as datetime
                return self._parse_date(str(value))
            else:
                return str(value)
        except (ValueError, TypeError):
            # If conversion fails, return as string
            return str(value)

    def _parse_date(self, value: str) -> Optional[str]:
        """Parse date string and return in ISO format.

        Args:
            value: Date string

        Returns:
            ISO formatted date string or original if parsing fails
        """
        for pattern, date_format in self.DATE_PATTERNS:
            if re.match(pattern, value):
                try:
                    dt = datetime.strptime(value, date_format)
                    return dt.isoformat()
                except ValueError:
                    continue
        # Return original if no pattern matches
        return value
