"""Field mapping support for OpenSearch backend.

This module provides the FieldMapping class for intelligent field selection
based on operators and field types in OpenSearch.
"""

from typing import Any, Dict, Optional

from ..exceptions import TQLTypeError, TQLUnsupportedOperationError


class FieldMapping:
    """Represents field mapping information for intelligent field selection."""

    def __init__(self, mapping_info: Dict[str, Any]):  # noqa: C901
        """Initialize field mapping.

        Args:
            mapping_info: Dictionary containing field mapping information.
                         Supports multiple formats:

                         1. OpenSearch-style mapping with subfields:
                         {
                             "type": "text",
                             "fields": {
                                 "keyword": {"type": "keyword"},
                                 "english": {"type": "text", "analyzer": "english"}
                             }
                         }

                         2. Flat format with field variants:
                         {
                             "field_name": "keyword",
                             "field_name.text": {"type": "text", "analyzer": "standard"},
                             "field_name.english": {"type": "text", "analyzer": "english"}
                         }

                         3. Legacy format:
                         {
                             "field_name": "keyword",
                             "field_name.text": "text",
                             "analyzer": "standard"
                         }
        """
        self.mappings = mapping_info
        self.keyword_field = None
        self.text_fields = {}  # analyzer -> field_name mapping
        self.default_analyzer = mapping_info.get("analyzer", "standard")
        self.field_types = {}  # field_name -> type mapping for all fields
        self.base_field_name = None  # The main field name without suffixes

        # Check if this is an OpenSearch-style mapping with "type"
        if "type" in mapping_info and not any(
            k for k in mapping_info.keys() if k not in ["type", "fields", "analyzer"]
        ):
            # This is an OpenSearch-style single field mapping
            base_type = mapping_info["type"]
            subfields = mapping_info.get("fields", {})

            # Determine base field name from context (will be set by backend)
            # For now, use empty string as placeholder
            self.base_field_name = ""

            # Process base field
            if base_type == "keyword":
                self.keyword_field = self.base_field_name
                self.field_types[self.base_field_name] = "keyword"
            elif base_type == "text":
                analyzer = mapping_info.get("analyzer", "standard")
                # If analyzer is a dict (custom analyzer), use "custom" as key
                analyzer_key = "custom" if isinstance(analyzer, dict) else analyzer
                self.text_fields[analyzer_key] = self.base_field_name
                self.field_types[self.base_field_name] = "text"
            else:
                self.field_types[self.base_field_name] = base_type

            # Process subfields
            for subfield_name, subfield_config in subfields.items():
                if isinstance(subfield_config, dict):
                    subfield_type = subfield_config.get("type")
                    field_path = (
                        f"{self.base_field_name}.{subfield_name}" if self.base_field_name else f".{subfield_name}"
                    )

                    if subfield_type == "keyword":
                        self.keyword_field = field_path
                        self.field_types[field_path] = "keyword"
                    elif subfield_type == "text":
                        analyzer = subfield_config.get("analyzer", "standard")
                        # If analyzer is a dict (custom analyzer), use "custom" as key
                        analyzer_key = "custom" if isinstance(analyzer, dict) else analyzer
                        self.text_fields[analyzer_key] = field_path
                        self.field_types[field_path] = "text"
                    elif subfield_type:
                        self.field_types[field_path] = subfield_type
        else:
            # Original flat format parsing
            for field_name, field_config in mapping_info.items():
                if field_name == "analyzer":
                    continue

                # Extract base field name (without .text, .keyword suffixes)
                if not self.base_field_name and not field_name.startswith("_"):
                    if "." not in field_name:
                        self.base_field_name = field_name
                    else:
                        # Get the part before the first dot
                        self.base_field_name = field_name.split(".")[0]

                if isinstance(field_config, dict):
                    # New format: {"type": "text", "analyzer": "english"}
                    field_type = field_config.get("type")
                    analyzer = field_config.get("analyzer", "standard")

                    if field_type:
                        self.field_types[field_name] = field_type

                    if field_type == "keyword":
                        self.keyword_field = field_name
                    elif field_type == "text":
                        # If analyzer is a dict (custom analyzer), use "custom" as key
                        analyzer_key = "custom" if isinstance(analyzer, dict) else analyzer
                        self.text_fields[analyzer_key] = field_name
                else:
                    # Legacy format: "keyword" or "text" or other types
                    field_type = field_config
                    self.field_types[field_name] = field_type

                    if field_type == "keyword":
                        self.keyword_field = field_name
                    elif field_type == "text":
                        # Use default analyzer for legacy text fields
                        self.text_fields[self.default_analyzer] = field_name

    def set_base_field_name(self, base_field_name: str):  # noqa: C901
        """Set the base field name and update field paths for OpenSearch-style mappings.

        Args:
            base_field_name: The base field name to use
        """
        if self.base_field_name == "":  # Only update if it was a placeholder
            old_base = self.base_field_name
            self.base_field_name = base_field_name

            # Update all field paths
            new_field_types = {}
            for field_path, field_type in self.field_types.items():
                if field_path == old_base:
                    new_field_types[base_field_name] = field_type
                elif field_path.startswith("."):
                    new_field_types[f"{base_field_name}{field_path}"] = field_type
                else:
                    new_field_types[field_path] = field_type
            self.field_types = new_field_types

            # Update keyword field
            if self.keyword_field == old_base:
                self.keyword_field = base_field_name
            elif self.keyword_field is not None and self.keyword_field.startswith("."):
                self.keyword_field = f"{base_field_name}{self.keyword_field}"
            elif self.keyword_field == "":
                # If keyword field is empty string (from base type), set it to the base field name
                self.keyword_field = base_field_name

            # Update text fields
            new_text_fields = {}
            for analyzer, field_path in self.text_fields.items():
                if field_path == old_base:
                    new_text_fields[analyzer] = base_field_name
                elif field_path.startswith("."):
                    new_text_fields[analyzer] = f"{base_field_name}{field_path}"
                else:
                    new_text_fields[analyzer] = field_path
            self.text_fields = new_text_fields

    def get_text_field_for_analyzer(self, preferred_analyzer: Optional[str] = None) -> Optional[str]:
        """Get the best text field for the given analyzer preference.

        Args:
            preferred_analyzer: Preferred analyzer (e.g., 'english', 'autocomplete')

        Returns:
            Field name for the best matching text field, or None if no text fields
        """
        if not self.text_fields:
            return None

        # Try exact match first
        if preferred_analyzer and preferred_analyzer in self.text_fields:
            return self.text_fields[preferred_analyzer]

        # Try default analyzer
        if self.default_analyzer in self.text_fields:
            return self.text_fields[self.default_analyzer]

        # Try standard analyzer as fallback
        if "standard" in self.text_fields:
            return self.text_fields["standard"]

        # Return any available text field
        return next(iter(self.text_fields.values()))

    def get_field_for_operator(self, operator: str, preferred_analyzer: Optional[str] = None) -> str:  # noqa: C901
        """Get the appropriate field name for the given operator.

        Args:
            operator: The TQL operator being used
            preferred_analyzer: Preferred analyzer for text operations

        Returns:
            The field name to use

        Raises:
            TQLUnsupportedOperationError: If operator is not supported for available fields
        """
        # Operators that work best with keyword fields (exact matching)
        keyword_operators = {
            "eq",
            "=",
            "ne",
            "!=",
            "in",
            "not_in",
            "exists",
            "not_exists",
            "is",
            "any",
            "all",
            "not_any",
            "not_all",
        }

        # Operators that work best with text fields (full-text search)
        text_operators = {"contains", "regexp", "not_regexp"}

        # Operators that require numeric/date fields
        range_operators = {">", ">=", "<", "<=", "gt", "gte", "lt", "lte", "between", "not_between"}

        # Operators that work with both but prefer keyword
        wildcard_operators = {"startswith", "endswith"}

        if operator in keyword_operators:
            if self.keyword_field:
                # Return base field name if keyword field is empty (happens with simple type mappings)
                return self.keyword_field
            else:
                # Check if we have numeric/IP fields - they also support equality
                for field_name, field_type in self.field_types.items():
                    if field_type in {"integer", "long", "float", "double", "boolean", "date", "ip"}:
                        return field_name
                # Fallback to any available text field
                text_field = self.get_text_field_for_analyzer(preferred_analyzer)
                if text_field:
                    return text_field
                # If we have any field types at all, return the first one
                # This handles cases where we have fields but they don't match the above categories
                if self.field_types:
                    # Return the first non-empty field name
                    for field_name in self.field_types.keys():
                        if field_name:  # Skip empty string keys
                            return field_name
                # If no fields at all, return the base field name
                if self.base_field_name:
                    return self.base_field_name
                # Last resort - return empty string
                return ""
        elif operator in text_operators:
            # Try to get text field with preferred analyzer
            text_field = self.get_text_field_for_analyzer(preferred_analyzer)
            if text_field:
                return text_field
            elif self.keyword_field:
                # Will need special handling for wildcard conversion
                # Return base field name if keyword field is empty
                return self.keyword_field
        elif operator in wildcard_operators:
            # Prefer keyword for wildcard operations
            if self.keyword_field:
                # Return base field name if keyword field is empty
                return self.keyword_field
            else:
                text_field = self.get_text_field_for_analyzer(preferred_analyzer)
                if text_field:
                    return text_field
        elif operator in range_operators:
            # Range operators prefer numeric/date fields but can work with keyword fields
            # Check what field types we have
            has_numeric_or_date = any(
                ft in {"integer", "long", "float", "double", "date"} for ft in self.field_types.values()
            )

            if has_numeric_or_date:
                # Return the first numeric/date field found
                for field_name, field_type in self.field_types.items():
                    if field_type in {"integer", "long", "float", "double", "date"}:
                        return field_name

            # No numeric fields - try keyword field (OpenSearch supports range queries on keywords)
            if self.keyword_field:
                # Return base field name if keyword field is empty
                return self.keyword_field

            # Only text fields available - this won't work
            if self.text_fields:
                field_name = self.base_field_name or "field"
                raise TQLTypeError(
                    field=field_name,
                    field_type="text",
                    operator=operator,
                    valid_operators=["=", "!=", "contains", "startswith", "endswith"],
                )
        elif operator in {"cidr", "not_cidr"}:
            # CIDR works best with IP field type
            # First check for IP fields
            for field_name, field_type in self.field_types.items():
                if field_type == "ip":
                    return field_name

            # Fallback to keyword field
            if self.keyword_field:
                # Return base field name if keyword field is empty
                return self.keyword_field
            else:
                raise TQLUnsupportedOperationError("CIDR operator requires keyword or IP field type")

        # If we get here, no suitable field was found
        available_types = []
        if self.keyword_field:
            available_types.append(f"{self.keyword_field}(keyword)")
        for analyzer, field_name in self.text_fields.items():
            available_types.append(f"{field_name}(text:{analyzer})")

        raise TQLUnsupportedOperationError(
            f"Operator '{operator}' is not supported for available field types: {available_types}"
        )

    def needs_wildcard_conversion(self, operator: str, preferred_analyzer: Optional[str] = None) -> bool:
        """Check if operator needs wildcard conversion for keyword fields.

        Args:
            operator: The TQL operator
            preferred_analyzer: Preferred analyzer for text operations

        Returns:
            True if wildcard conversion is needed
        """
        text_operators = {"contains"}
        selected_field = self.get_field_for_operator(operator, preferred_analyzer)

        return operator in text_operators and selected_field == self.keyword_field and not self.text_fields

    def validate_operator_for_field_type(self, operator: str, raise_on_error: bool = True) -> bool:
        """Validate if an operator is compatible with available field types.

        Args:
            operator: The TQL operator to validate
            raise_on_error: If True, raise TQLTypeError on incompatibility

        Returns:
            True if operator is compatible, False otherwise

        Raises:
            TQLTypeError: If operator is incompatible and raise_on_error is True
        """
        # Define operator compatibility rules
        numeric_types = {"integer", "long", "float", "double"}
        range_operators = {">", ">=", "<", "<=", "gt", "gte", "lt", "lte", "between", "not_between"}

        # Check if we have appropriate fields for range operators
        if operator in range_operators:
            has_numeric = any(ft in numeric_types for ft in self.field_types.values())
            has_keyword = self.keyword_field is not None

            # Range operators work best with numeric fields, but OpenSearch also supports them on keyword fields
            # Only fail if we have text fields only
            if not has_numeric and not has_keyword:
                if self.text_fields and raise_on_error:
                    field_name = self.base_field_name or "field"
                    raise TQLTypeError(
                        field=field_name,
                        field_type="text",
                        operator=operator,
                        valid_operators=["=", "!=", "contains", "startswith", "endswith"],
                    )
                elif not raise_on_error:
                    return False

        # CIDR operator requires IP or keyword field
        if operator == "cidr":
            has_ip = any(ft == "ip" for ft in self.field_types.values())
            has_keyword = self.keyword_field is not None

            if not has_ip and not has_keyword:
                if raise_on_error:
                    field_name = self.base_field_name or "field"
                    field_type = next(iter(self.field_types.values()), "unknown")
                    raise TQLTypeError(
                        field=field_name,
                        field_type=field_type,
                        operator=operator,
                        valid_operators=["=", "!=", "contains"] if field_type == "text" else [],
                    )
                return False

        return True
