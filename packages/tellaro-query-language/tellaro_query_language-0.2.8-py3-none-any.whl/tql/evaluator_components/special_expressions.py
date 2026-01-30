"""Special expression evaluators for TQL.

This module handles evaluation of special expressions like geo() and nslookup()
that require external lookups or enrichment.
"""

from typing import Any, Dict, Optional

from ..mutators import apply_mutators


class SpecialExpressionEvaluator:
    """Evaluates special TQL expressions like geo() and nslookup()."""

    # Sentinel value to distinguish missing fields from None values
    _MISSING_FIELD = object()

    def __init__(self, get_field_value_func, evaluate_node_func, set_field_value_func=None):
        """Initialize the special expression evaluator.

        Args:
            get_field_value_func: Function to get field values from records
            evaluate_node_func: Function to evaluate AST nodes
            set_field_value_func: Optional function to set field values in records
        """
        self._get_field_value = get_field_value_func
        self._evaluate_node = evaluate_node_func
        self._set_field_value = set_field_value_func or self._default_set_field_value

    def _default_set_field_value(self, record: Dict[str, Any], field_path: str, value: Any) -> None:
        """Default implementation of set_field_value for nested field assignment."""
        parts = field_path.split(".")
        current = record
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def evaluate_geo_expr(  # noqa: C901
        self, node: Dict[str, Any], record: Dict[str, Any], field_mappings: Dict[str, str]
    ) -> bool:
        """Evaluate a geo() expression.

        Args:
            node: Geo expression AST node
            record: Record to evaluate against
            field_mappings: Field name mappings

        Returns:
            Boolean result of the geo expression
        """
        field_name = node["field"]
        field_mutators = node.get("field_mutators", [])
        conditions = node["conditions"]
        geo_params = node.get("geo_params", {})

        # Apply field mapping if available
        actual_field = field_name
        if field_name in field_mappings:
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
                    actual_field = mapping
            elif isinstance(mapping, dict) and mapping:
                # Intelligent mapping - extract the base field
                if "type" in mapping and len(mapping) == 1:
                    # Just a type specification, use original field
                    actual_field = field_name
                else:
                    # Find the first field that's not a meta field
                    for key in mapping:
                        if key != "analyzer" and key != "type":
                            actual_field = key
                            break

        # Get the field value (IP address)
        field_value = self._get_field_value(record, actual_field)

        # If field is missing or None, return False
        if field_value is self._MISSING_FIELD or field_value is None:
            return False

        # Check if the record already has geo data (from post-processing)
        # Geo data would be nested under the parent of the IP field
        geo_data = None

        # Check if a custom field location was specified
        custom_field = geo_params.get("field")

        if custom_field:
            # Check the custom field location
            custom_data = self._get_field_value(record, custom_field)
            if custom_data is not self._MISSING_FIELD and isinstance(custom_data, dict):
                # Check if this looks like geo data
                if any(key in custom_data for key in ["country_iso_code", "city_name", "location"]):
                    geo_data = {"geo": custom_data}
                    # Also check for AS data as sibling
                    if "." in custom_field:
                        as_parent_path = custom_field.rsplit(".", 1)[0]
                        as_parent = self._get_field_value(record, as_parent_path)
                        if isinstance(as_parent, dict) and "as" in as_parent:
                            geo_data["as"] = as_parent["as"]
                    elif "as" in record:
                        geo_data["as"] = record["as"]
        else:
            # Default locations (ECS style)
            if "." in actual_field:
                # For nested fields like destination.ip, check destination.geo and destination.as
                parent_path = actual_field.rsplit(".", 1)[0]
                parent = self._get_field_value(record, parent_path)
                if isinstance(parent, dict) and ("geo" in parent or "as" in parent):
                    # Found geo/as data under parent
                    geo_data = {}
                    if "geo" in parent:
                        geo_data["geo"] = parent["geo"]
                    if "as" in parent:
                        geo_data["as"] = parent["as"]
            else:
                # For top-level fields like ip, check top-level geo and as fields (ECS style)
                if "geo" in record or "as" in record:
                    geo_data = {}
                    if "geo" in record:
                        geo_data["geo"] = record["geo"]
                    if "as" in record:
                        geo_data["as"] = record["as"]

        # Check if we should use existing geo data or force a new lookup
        force_lookup = geo_params.get("force", False)

        if geo_data and not force_lookup:
            # Use existing geo data
            pass
        else:
            # Apply the geo mutator to get geo data
            # Build mutator params from geo_params
            mutator_params = []
            for param_name, param_value in geo_params.items():
                mutator_params.append([param_name, param_value])

            # If no force parameter was specified, add the default
            if "force" not in geo_params:
                mutator_params.append(["force", force_lookup])

            geo_mutator: Dict[str, Any] = {"name": "geoip_lookup"}
            if mutator_params:
                geo_mutator["params"] = mutator_params

            # Apply any field mutators before the geo lookup
            if field_mutators:
                field_value = apply_mutators(field_value, field_mutators, actual_field, record)

            # Apply geo lookup
            geo_data = apply_mutators(field_value, [geo_mutator], actual_field, record)

        # Always include enrichment in query results (save=True adds to record for output)
        # Note: This does not modify source files - enrichment only appears in query results
        save_enrichment = geo_params.get("save", True)
        if save_enrichment and geo_data and isinstance(geo_data, dict):
            # Determine where to save the enrichment
            if custom_field:
                # Save to custom field location
                self._set_field_value(record, custom_field, geo_data.get("geo"))
                if "as" in geo_data:
                    # Save AS data as sibling to geo field
                    if "." in custom_field:
                        as_parent_path = custom_field.rsplit(".", 1)[0]
                        parent = self._get_field_value(record, as_parent_path)
                        if isinstance(parent, dict):
                            parent["as"] = geo_data["as"]
                    else:
                        record["as"] = geo_data["as"]
            elif "." in actual_field:
                # For nested fields like destination.ip, save to destination.geo and destination.as (ECS style)
                parent_path = actual_field.rsplit(".", 1)[0]
                parent = self._get_field_value(record, parent_path)
                if isinstance(parent, dict):
                    if "geo" in geo_data:
                        parent["geo"] = geo_data["geo"]
                    if "as" in geo_data:
                        parent["as"] = geo_data["as"]
            else:
                # For top-level fields like ip, save to top-level geo and as fields (ECS style)
                if "geo" in geo_data:
                    record["geo"] = geo_data["geo"]
                if "as" in geo_data:
                    record["as"] = geo_data["as"]

        # Now evaluate the conditions against the geo data
        if conditions:
            # Handle None geo_data (e.g., private IPs or lookup failures)
            if geo_data is None:
                geo_data = {}

            # Create a temporary record with the geo data
            # The conditions are evaluated against the geo fields directly
            temp_record = geo_data.get("geo", {})
            # Also include AS data if present
            if "as" in geo_data:
                temp_record["as"] = geo_data["as"]
            return self._evaluate_node(conditions, temp_record, {})
        else:
            # No conditions, enrichment-only - always return True
            return True

    def evaluate_nslookup_expr(  # noqa: C901
        self, node: Dict[str, Any], record: Dict[str, Any], field_mappings: Dict[str, str]
    ) -> bool:
        """Evaluate a nslookup() expression.

        Args:
            node: NSLookup expression AST node
            record: Record to evaluate against
            field_mappings: Field name mappings

        Returns:
            Boolean result of the nslookup expression
        """
        field_name = node["field"]
        field_mutators = node.get("field_mutators", [])
        conditions = node["conditions"]
        nslookup_params = node.get("nslookup_params", {})

        # Apply field mapping if available
        actual_field = field_name
        if field_name in field_mappings:
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
                    actual_field = mapping
            elif isinstance(mapping, dict) and mapping:
                # Intelligent mapping - extract the base field
                if "type" in mapping and len(mapping) == 1:
                    # Just a type specification, use original field
                    actual_field = field_name
                else:
                    # Find the first field that's not a meta field
                    for key in mapping:
                        if key != "analyzer" and key != "type":
                            actual_field = key
                            break

        # Get the field value (hostname or IP)
        field_value = self._get_field_value(record, actual_field)

        # If field is missing or None, return False
        if field_value is self._MISSING_FIELD or field_value is None:
            return False

        # Check if the record already has DNS data (from post-processing)
        dns_data = None

        # Check if a custom field location was specified
        custom_field = nslookup_params.get("field")

        if custom_field:
            # Check the custom field location
            custom_data = self._get_field_value(record, custom_field)
            if custom_data is not self._MISSING_FIELD and isinstance(custom_data, dict):
                # Check if this looks like DNS data
                if any(key in custom_data for key in ["question", "answers", "resolved_ip"]):
                    dns_data = custom_data
        else:
            # Default locations
            # If field is like "destination.ip", DNS data should be in "destination.domain"
            if "." in field_name:
                # Nested field like destination.ip or source.hostname
                parent_path = field_name.rsplit(".", 1)[0]
                parent: Optional[Dict[str, Any]] = record
                for part in parent_path.split("."):
                    if isinstance(parent, dict) and part in parent:
                        parent = parent[part]
                    else:
                        parent = None
                        break

                if parent and isinstance(parent, dict) and "domain" in parent:
                    dns_data = parent["domain"]
            else:
                # Top-level field - check enrichment.domain
                enrichment = record.get("enrichment", {})
                if "domain" in enrichment:
                    dns_data = enrichment["domain"]

        # Check if we should use existing DNS data or force a new lookup
        force_lookup = nslookup_params.get("force", False)

        if dns_data and not force_lookup:
            # Use existing DNS data
            pass
        else:
            # Apply the nslookup mutator to get DNS data
            # Build mutator params from nslookup_params
            mutator_params = []
            for param_name, param_value in nslookup_params.items():
                mutator_params.append([param_name, param_value])

            # If no force parameter was specified, add the default
            if "force" not in nslookup_params:
                mutator_params.append(["force", force_lookup])

            nslookup_mutator: Dict[str, Any] = {"name": "nslookup"}
            if mutator_params:
                nslookup_mutator["params"] = mutator_params

            # Apply any field mutators before the nslookup
            if field_mutators:
                field_value = apply_mutators(field_value, field_mutators, field_name, record)

            # Apply nslookup (this enriches the record)
            apply_mutators(field_value, [nslookup_mutator], field_name, record)

            # Now get the DNS data from where it was stored
            if "." in field_name:
                # Nested field like destination.ip
                parent_path = field_name.rsplit(".", 1)[0]
                parent = record
                for part in parent_path.split("."):
                    if isinstance(parent, dict) and part in parent:
                        parent = parent[part]
                    else:
                        parent = None
                        break
                if parent and isinstance(parent, dict) and "domain" in parent:
                    dns_data = parent["domain"]
                else:
                    dns_data = None
            else:
                # Top-level field
                dns_data = record.get("enrichment", {}).get("domain")

        # Now evaluate the conditions against the DNS data
        if conditions:
            # Create a temporary record with the DNS data at root level
            temp_record = dns_data if dns_data else {}
            return self._evaluate_node(conditions, temp_record, {})
        else:
            # No conditions, enrichment-only - always return True
            return True
