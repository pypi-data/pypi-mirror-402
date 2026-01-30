"""Clean, user-friendly stats result transformation."""

from typing import Any, Dict, List, Union


class StatsResultTransformer:
    """Transform OpenSearch aggregation results into clean, user-friendly format."""

    def transform(self, response: Dict[str, Any], stats_ast: Dict[str, Any]) -> Dict[str, Any]:
        """Transform OpenSearch response to clean format.

        Args:
            response: Raw OpenSearch response
            stats_ast: Stats AST for context

        Returns:
            Structured results with metadata
        """
        aggregations = stats_ast.get("aggregations", [])
        group_by_fields = stats_ast.get("group_by", [])

        # Build result structure
        result: Dict[str, Any] = {"type": "stats"}

        # Add operation info
        if len(aggregations) == 1:
            result["operation"] = aggregations[0]["function"]
            result["field"] = aggregations[0]["field"]
        else:
            result["operations"] = [{"function": agg["function"], "field": agg["field"]} for agg in aggregations]

        # Add group_by info if present
        if group_by_fields:
            result["group_by"] = group_by_fields

        # Transform the actual data
        if not group_by_fields:
            # Simple aggregation (no grouping)
            result["values"] = self._transform_simple(response, aggregations)
        else:
            # Grouped aggregation
            result["values"] = self._transform_grouped(response, aggregations, group_by_fields)

        return result

    def _transform_simple(
        self, response: Dict[str, Any], aggregations: List[Dict[str, Any]]
    ) -> Union[int, float, Dict[str, Union[int, float, None]], None]:
        """Transform simple aggregation (no grouping).

        For single aggregation: returns the value directly
        For multiple aggregations: returns a dict of function->value
        """
        aggs_data = response.get("aggregations", {})

        if len(aggregations) == 1:
            # Single aggregation - return just the value
            agg = aggregations[0]
            agg_key = self._get_agg_key(agg)
            return self._extract_value(aggs_data.get(agg_key, {}), agg["function"])
        else:
            # Multiple aggregations - return dict
            result: Dict[str, Union[int, float, None]] = {}
            for i, agg in enumerate(aggregations):
                agg_key = self._get_agg_key(agg, i)
                value = self._extract_value(aggs_data.get(agg_key, {}), agg["function"])
                # Use clean key: just function name or alias
                clean_key = agg.get("alias") or agg["function"]
                result[clean_key] = value
            return result

    def _transform_grouped(
        self, response: Dict[str, Any], aggregations: List[Dict[str, Any]], group_by_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """Transform grouped aggregation.

        Returns a list of dictionaries, each containing:
        - The grouping field value(s)
        - The aggregation result(s)
        """
        aggs_data = response.get("aggregations", {})

        # Get the first grouping key
        first_group_key = f"group_by_{group_by_fields[0]}"
        grouped_data = aggs_data.get(first_group_key, {})
        buckets = grouped_data.get("buckets", [])

        results = []
        for bucket in buckets:
            if len(group_by_fields) == 1:
                # Single group by - simple case
                entry = {group_by_fields[0]: bucket.get("key")}

                # Add aggregation values
                self._add_aggregation_values(entry, bucket, aggregations)
                results.append(entry)
            else:
                # Multiple group by - process nested buckets
                nested_results = self._process_nested_buckets(bucket, group_by_fields, aggregations)
                results.extend(nested_results)

        return results

    def _process_nested_buckets(
        self, bucket: Dict[str, Any], group_by_fields: List[str], aggregations: List[Dict[str, Any]], level: int = 0
    ) -> List[Dict[str, Any]]:
        """Process nested buckets for multi-field grouping."""
        results = []

        if level >= len(group_by_fields) - 1:
            # We're at the last level, return single entry
            entry = {}
            # Add all group keys up to this level
            entry[group_by_fields[level]] = bucket.get("key")
            self._add_aggregation_values(entry, bucket, aggregations)
            return [entry]

        # Get current field key
        current_field = group_by_fields[level]
        current_key = bucket.get("key")

        # Look for next level
        next_field = group_by_fields[level + 1]
        next_group_key = f"group_by_{next_field}"

        if next_group_key in bucket:
            sub_buckets = bucket[next_group_key].get("buckets", [])
            for sub_bucket in sub_buckets:
                # Process each sub-bucket recursively
                sub_results = self._process_nested_buckets(sub_bucket, group_by_fields, aggregations, level + 1)
                # Add current field to each result
                for result in sub_results:
                    result[current_field] = current_key
                results.extend(sub_results)

        return results

    def _add_aggregation_values(
        self, entry: Dict[str, Any], bucket: Dict[str, Any], aggregations: List[Dict[str, Any]]
    ) -> None:
        """Add aggregation values to an entry."""
        if len(aggregations) == 1:
            # Single aggregation
            agg = aggregations[0]
            agg_key = self._get_agg_key(agg)
            value = self._extract_value(bucket.get(agg_key, {}), agg["function"])
            value_key = agg.get("alias") or agg["function"]
            entry[value_key] = value
        else:
            # Multiple aggregations
            for i, agg in enumerate(aggregations):
                agg_key = self._get_agg_key(agg, i)
                value = self._extract_value(bucket.get(agg_key, {}), agg["function"])
                value_key = agg.get("alias") or agg["function"]
                entry[value_key] = value

    def _get_agg_key(self, agg: Dict[str, Any], index: int = 0) -> str:
        """Get the OpenSearch aggregation key."""
        return agg.get("alias") or f"{agg['function']}_{agg['field']}_{index}"

    def _extract_value(self, agg_result: Dict[str, Any], function: str) -> Union[int, float, None]:
        """Extract clean value from OpenSearch aggregation result."""
        if function in ["count", "unique_count"]:
            # Count functions default to 0 if missing
            return agg_result.get("value", 0)
        elif function in ["sum", "min", "max", "average", "avg"]:
            # Numeric functions return None if missing (no default)
            return agg_result.get("value")
        elif function == "median":
            values = agg_result.get("values", {})
            return values.get("50.0") or values.get("50")
        elif function == "percentile":
            # Percentiles return a values dict with keys as percentile strings
            values = agg_result.get("values", {})
            # Get the first (and usually only) percentile value
            if values:
                # Keys are like "50.0", "95.0", etc.
                first_key = list(values.keys())[0]
                return values.get(first_key)
            return None
        elif function == "std":
            return agg_result.get("std_deviation")
        else:
            return None
