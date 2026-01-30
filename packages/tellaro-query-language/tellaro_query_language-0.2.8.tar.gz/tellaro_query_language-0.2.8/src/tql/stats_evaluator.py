"""Stats evaluator for TQL aggregation queries.

This module provides the TQLStatsEvaluator class for executing statistical
aggregation queries against data records in memory.
"""

import statistics
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .exceptions import TQLError


class TQLStatsEvaluator:
    """Evaluates TQL stats queries against data records.

    This class handles statistical aggregations, grouping, and produces
    results in a UI-friendly format.
    """

    # Aggregation functions that require numeric fields
    NUMERIC_AGGREGATIONS = {
        "sum",
        "min",
        "max",
        "average",
        "avg",
        "median",
        "med",
        "std",
        "standard_deviation",
        "percentile",
        "percentiles",
        "p",
        "pct",
        "percentile_rank",
        "percentile_ranks",
        "pct_rank",
        "pct_ranks",
    }

    # Aggregation functions that work with any field type
    ANY_TYPE_AGGREGATIONS = {"count", "unique_count", "values", "unique", "cardinality"}

    # Numeric types supported by OpenSearch
    NUMERIC_TYPES = {
        "long",
        "integer",
        "short",
        "byte",
        "double",
        "float",
        "half_float",
        "scaled_float",
        "unsigned_long",
    }

    def __init__(self):
        """Initialize the stats evaluator."""

    def evaluate_stats_streaming(
        self,
        record_iterator: Any,
        stats_ast: Dict[str, Any],
        field_mappings: Optional[Union[Dict[str, str], Dict[str, Union[str, Dict[str, Any]]]]] = None,
    ) -> Dict[str, Any]:
        """Evaluate stats query against streaming records.

        This method processes records incrementally using accumulators to minimize
        memory usage for large datasets.

        Args:
            record_iterator: Iterator/generator yielding records
            stats_ast: Stats AST from parser
            field_mappings: Optional field type mappings

        Returns:
            Aggregated results in UI-friendly format
        """
        aggregations = stats_ast.get("aggregations", [])
        group_by_fields = stats_ast.get("group_by", [])

        # Validate aggregation types against field mappings if provided
        if field_mappings:
            self._validate_aggregations(aggregations, field_mappings)

        if not group_by_fields:
            # Simple aggregation without grouping (streaming accumulators)
            return self._streaming_simple_aggregation(record_iterator, aggregations)
        else:
            # Grouped aggregation (still needs to track groups)
            return self._streaming_grouped_aggregation(record_iterator, aggregations, group_by_fields)

    def _streaming_simple_aggregation(  # noqa: C901
        self, record_iterator: Any, aggregations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform streaming aggregation without grouping.

        Args:
            record_iterator: Iterator yielding records
            aggregations: Aggregation specifications

        Returns:
            Aggregated results
        """
        # Initialize accumulators for each aggregation
        accumulators = {}
        for agg in aggregations:
            func = agg["function"]
            field = agg["field"]
            key = f"{func}_{field}"

            accumulators[key] = {
                "function": func,
                "field": field,
                "count": 0,
                "sum": 0,
                "min": None,
                "max": None,
                "values": [],  # For unique, values, percentiles
                "unique_set": set(),  # For unique_count
            }

        # Process records
        for record in record_iterator:
            for agg in aggregations:
                func = agg["function"]
                field = agg["field"]
                key = f"{func}_{field}"
                acc = accumulators[key]

                # Handle count(*)
                if func == "count" and field == "*":
                    acc["count"] += 1
                    continue

                # Get field value
                value = self._get_field_value(record, field)
                if value is None:
                    continue

                # Update accumulator based on function
                if func == "count":
                    acc["count"] += 1
                elif func == "unique_count":
                    try:
                        acc["unique_set"].add(value)
                    except TypeError:
                        # Unhashable type, use string representation
                        acc["unique_set"].add(str(value))
                elif func in ["sum", "min", "max", "average", "avg"]:
                    numeric_value = self._to_numeric(value)
                    acc["sum"] += numeric_value
                    acc["count"] += 1
                    if acc["min"] is None or numeric_value < acc["min"]:
                        acc["min"] = numeric_value
                    if acc["max"] is None or numeric_value > acc["max"]:
                        acc["max"] = numeric_value
                elif func in ["median", "med", "percentile", "percentiles", "p", "pct", "std", "standard_deviation"]:
                    # Need to store all values for these
                    acc["values"].append(self._to_numeric(value))
                elif func in ["values", "unique", "cardinality"]:
                    # Store unique values
                    if value not in acc["values"]:
                        acc["values"].append(value)

        # Calculate final results
        if len(aggregations) == 1:
            agg = aggregations[0]
            value = self._finalize_accumulator(accumulators[f"{agg['function']}_{agg['field']}"], agg)
            return {
                "type": "simple_aggregation",
                "function": agg["function"],
                "field": agg["field"],
                "alias": agg.get("alias"),
                "value": value,
            }
        else:
            results = {}
            for agg in aggregations:
                value = self._finalize_accumulator(accumulators[f"{agg['function']}_{agg['field']}"], agg)
                key = agg.get("alias") or f"{agg['function']}_{agg['field']}"
                results[key] = value
            return {"type": "multiple_aggregations", "results": results}

    def _streaming_grouped_aggregation(  # noqa: C901
        self, record_iterator: Any, aggregations: List[Dict[str, Any]], group_by_fields: List[Any]
    ) -> Dict[str, Any]:
        """Perform streaming grouped aggregation.

        For grouped aggregations, we still need to track groups in memory,
        but we process records one at a time.

        Args:
            record_iterator: Iterator yielding records
            aggregations: Aggregation specifications
            group_by_fields: Fields to group by

        Returns:
            Grouped aggregation results
        """
        # Normalize group_by_fields
        normalized_fields = []
        for field in group_by_fields:
            if isinstance(field, str):
                normalized_fields.append({"field": field, "bucket_size": None})
            elif isinstance(field, dict):
                normalized_fields.append(field)
            else:
                normalized_fields.append({"field": str(field), "bucket_size": None})

        # Track groups with accumulators
        groups: Dict[Tuple[Any, ...], Dict[str, Any]] = defaultdict(
            lambda: self._create_group_accumulators(aggregations)
        )
        key_mapping: Dict[Tuple[Any, ...], List[Tuple[str, Any]]] = {}

        # Process records
        for record in record_iterator:
            # Build group key
            key_parts = []
            for field_spec in normalized_fields:
                field_name = field_spec.get("field")
                if field_name is None:
                    continue
                value = self._get_field_value(record, field_name)
                key_parts.append((field_name, value))

            hashable_key = self._make_hashable_key(key_parts)

            # Store key mapping
            if hashable_key not in key_mapping:
                key_mapping[hashable_key] = key_parts

            # Update accumulators for this group
            group_accs = groups[hashable_key]
            self._update_group_accumulators(group_accs, record, aggregations)

        # Finalize results
        results = []
        for hashable_key, group_accs in groups.items():
            original_key = key_mapping[hashable_key]
            group_result = {"key": dict(original_key), "doc_count": group_accs["doc_count"]}

            if len(aggregations) == 1:
                agg = aggregations[0]
                value = self._finalize_accumulator(group_accs[f"{agg['function']}_{agg['field']}"], agg)
                agg_key = agg.get("alias") or agg["function"]
                group_result[agg_key] = value
            else:
                group_result["aggregations"] = {}
                for agg in aggregations:
                    value = self._finalize_accumulator(group_accs[f"{agg['function']}_{agg['field']}"], agg)
                    agg_key = agg.get("alias") or f"{agg['function']}_{agg['field']}"
                    group_result["aggregations"][agg_key] = value

            results.append(group_result)

        # Apply modifiers and bucket limits
        results = self._apply_modifiers(results, aggregations)
        results = self._apply_bucket_limits(results, normalized_fields)

        # Extract field names for response
        group_by_field_names = []
        for field in group_by_fields:
            if isinstance(field, str):
                group_by_field_names.append(field)
            elif isinstance(field, dict) and "field" in field:
                group_by_field_names.append(field["field"])
            else:
                group_by_field_names.append(str(field))

        return {"type": "grouped_aggregation", "group_by": group_by_field_names, "results": results}

    def _create_group_accumulators(self, aggregations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create accumulator structure for a single group.

        Args:
            aggregations: Aggregation specifications

        Returns:
            Dictionary of accumulators
        """
        accumulators: Dict[str, Any] = {"doc_count": 0}
        for agg in aggregations:
            func = agg["function"]
            field = agg["field"]
            key = f"{func}_{field}"

            acc_value: Dict[str, Any] = {
                "function": func,
                "field": field,
                "count": 0,
                "sum": 0,
                "min": None,
                "max": None,
                "values": [],
                "unique_set": set(),
            }
            accumulators[key] = acc_value
        return accumulators

    def _update_group_accumulators(  # noqa: C901
        self, group_accs: Dict[str, Any], record: Dict[str, Any], aggregations: List[Dict[str, Any]]
    ) -> None:
        """Update group accumulators with a new record.

        Args:
            group_accs: Group accumulators dictionary
            record: Record to process
            aggregations: Aggregation specifications
        """
        group_accs["doc_count"] += 1

        for agg in aggregations:
            func = agg["function"]
            field = agg["field"]
            key = f"{func}_{field}"
            acc = group_accs[key]

            # Handle count(*)
            if func == "count" and field == "*":
                acc["count"] += 1
                continue

            # Get field value
            value = self._get_field_value(record, field)
            if value is None:
                continue

            # Update accumulator
            if func == "count":
                acc["count"] += 1
            elif func == "unique_count":
                try:
                    acc["unique_set"].add(value)
                except TypeError:
                    acc["unique_set"].add(str(value))
            elif func in ["sum", "min", "max", "average", "avg"]:
                numeric_value = self._to_numeric(value)
                acc["sum"] += numeric_value
                acc["count"] += 1
                if acc["min"] is None or numeric_value < acc["min"]:
                    acc["min"] = numeric_value
                if acc["max"] is None or numeric_value > acc["max"]:
                    acc["max"] = numeric_value
            elif func in ["median", "med", "percentile", "percentiles", "p", "pct", "std", "standard_deviation"]:
                acc["values"].append(self._to_numeric(value))
            elif func in ["values", "unique", "cardinality"]:
                if value not in acc["values"]:
                    acc["values"].append(value)

    def _finalize_accumulator(self, acc: Dict[str, Any], agg_spec: Dict[str, Any]) -> Any:  # noqa: C901
        """Finalize an accumulator to produce the final aggregation value.

        Args:
            acc: Accumulator dictionary
            agg_spec: Aggregation specification

        Returns:
            Final aggregated value
        """
        func = agg_spec["function"]

        if func == "count":
            return acc["count"]
        elif func == "unique_count":
            return len(acc["unique_set"])
        elif func == "sum":
            return acc["sum"]
        elif func == "min":
            return acc["min"]
        elif func == "max":
            return acc["max"]
        elif func in ["average", "avg"]:
            return acc["sum"] / acc["count"] if acc["count"] > 0 else None
        elif func in ["median", "med"]:
            if not acc["values"]:
                return None
            sorted_values = sorted(acc["values"])
            return statistics.median(sorted_values)
        elif func in ["std", "standard_deviation"]:
            if len(acc["values"]) < 2:
                return None
            return statistics.stdev(acc["values"])
        elif func in ["percentile", "percentiles", "p", "pct"]:
            if not acc["values"]:
                return None
            sorted_values = sorted(acc["values"])
            percentile_values = agg_spec.get("percentile_values", [50])

            if len(percentile_values) == 1:
                return self._calculate_percentile(sorted_values, percentile_values[0])
            else:
                result = {}
                for p in percentile_values:
                    result[f"p{int(p)}"] = self._calculate_percentile(sorted_values, p)
                return result
        elif func in ["values", "unique", "cardinality"]:
            unique_values = acc["values"]
            try:
                unique_values.sort()
            except TypeError:
                pass
            return unique_values
        else:
            return None

    def evaluate_stats(
        self, records: List[Dict[str, Any]], stats_ast: Dict[str, Any], field_mappings: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Evaluate stats query against records.

        Args:
            records: List of records to aggregate
            stats_ast: Stats AST from parser
            field_mappings: Optional field type mappings

        Returns:
            Aggregated results in UI-friendly format
        """
        aggregations = stats_ast.get("aggregations", [])
        group_by_fields = stats_ast.get("group_by", [])

        # Validate aggregation types against field mappings if provided
        if field_mappings:
            self._validate_aggregations(aggregations, field_mappings)

        if not group_by_fields:
            # Simple aggregation without grouping
            return self._simple_aggregation(records, aggregations)
        else:
            # Grouped aggregation
            return self._grouped_aggregation(records, aggregations, group_by_fields)

    def _validate_aggregations(
        self,
        aggregations: List[Dict[str, Any]],
        field_mappings: Union[Dict[str, str], Dict[str, Union[str, Dict[str, Any]]]],
    ) -> None:
        """Validate that aggregation functions are compatible with field types.

        Args:
            aggregations: List of aggregation specifications
            field_mappings: Field type mappings

        Raises:
            TQLError: If aggregation is incompatible with field type
        """
        for agg in aggregations:
            func = agg["function"]
            field = agg["field"]

            # Skip validation for count(*)
            if field == "*":
                continue

            # Check if function requires numeric type
            if func in self.NUMERIC_AGGREGATIONS:
                field_type = field_mappings.get(field, "unknown")

                if field_type not in self.NUMERIC_TYPES and field_type != "unknown":
                    raise TQLError(
                        f"Cannot perform {func}() on non-numeric field '{field}' (type: {field_type}). "
                        f"Use count() or unique_count() for non-numeric fields, or ensure '{field}' "
                        f"is mapped as a numeric type."
                    )

    def _simple_aggregation(self, records: List[Dict[str, Any]], aggregations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform aggregation without grouping.

        Args:
            records: Records to aggregate
            aggregations: Aggregation specifications

        Returns:
            Aggregated results
        """
        if len(aggregations) == 1:
            # Single aggregation
            agg = aggregations[0]
            value = self._calculate_aggregation(records, agg)

            return {
                "type": "simple_aggregation",
                "function": agg["function"],
                "field": agg["field"],
                "alias": agg.get("alias"),
                "value": value,
            }
        else:
            # Multiple aggregations
            results = {}
            for agg in aggregations:
                value = self._calculate_aggregation(records, agg)
                key = agg.get("alias") or f"{agg['function']}_{agg['field']}"
                results[key] = value

            return {"type": "multiple_aggregations", "results": results}

    def _grouped_aggregation(  # noqa: C901
        self, records: List[Dict[str, Any]], aggregations: List[Dict[str, Any]], group_by_fields: List[Any]
    ) -> Dict[str, Any]:
        """Perform aggregation with grouping.

        Args:
            records: Records to aggregate
            aggregations: Aggregation specifications
            group_by_fields: Fields to group by (can be strings or dicts with bucket_size)

        Returns:
            Grouped aggregation results
        """
        # Normalize group_by_fields to handle both old (string) and new (dict) formats
        normalized_fields = []
        for field in group_by_fields:
            if isinstance(field, str):
                # Old format: just field name
                normalized_fields.append({"field": field, "bucket_size": None})
            elif isinstance(field, dict):
                # New format: {"field": "name", "bucket_size": N}
                normalized_fields.append(field)
            else:
                # Shouldn't happen but handle gracefully
                normalized_fields.append({"field": str(field), "bucket_size": None})

        # Group records
        groups = defaultdict(list)
        key_mapping = {}  # Maps hashable key to original key

        for record in records:
            # Build group key
            key_parts = []
            for field_spec in normalized_fields:
                field_name = field_spec.get("field")
                if field_name is None:
                    continue
                value = self._get_field_value(record, field_name)
                key_parts.append((field_name, value))

            # Create hashable key - convert unhashable values to strings
            hashable_key = self._make_hashable_key(key_parts)
            groups[hashable_key].append(record)

            # Store mapping from hashable key to original key
            if hashable_key not in key_mapping:
                key_mapping[hashable_key] = key_parts

        # Calculate aggregations for each group
        results = []
        for hashable_key, group_records in groups.items():
            original_key = key_mapping[hashable_key]
            group_result: Dict[str, Any] = {"key": dict(original_key), "doc_count": len(group_records)}

            if len(aggregations) == 1:
                # Single aggregation
                agg = aggregations[0]
                value = self._calculate_aggregation(group_records, agg)
                agg_key = agg.get("alias") or agg["function"]
                group_result[agg_key] = value
            else:
                # Multiple aggregations
                group_result["aggregations"] = {}
                for agg in aggregations:
                    value = self._calculate_aggregation(group_records, agg)
                    agg_key = agg.get("alias") or f"{agg['function']}_{agg['field']}"
                    group_result["aggregations"][agg_key] = value

            results.append(group_result)

        # Apply modifiers (top/bottom)
        results = self._apply_modifiers(results, aggregations)

        # Apply per-field bucket limits
        results = self._apply_bucket_limits(results, normalized_fields)

        # Extract just the field names for the response to ensure compatibility
        # with frontend code that expects strings, not dictionaries
        group_by_field_names = []
        for field in group_by_fields:
            if isinstance(field, str):
                group_by_field_names.append(field)
            elif isinstance(field, dict) and "field" in field:
                group_by_field_names.append(field["field"])
            else:
                # Fallback for unexpected formats
                group_by_field_names.append(str(field))

        # Return group_by fields as strings for frontend compatibility
        return {"type": "grouped_aggregation", "group_by": group_by_field_names, "results": results}

    def _calculate_aggregation(  # noqa: C901
        self, records: List[Dict[str, Any]], agg_spec: Dict[str, Any]
    ) -> Union[int, float, Dict[str, Any], List[Any], None]:
        """Calculate a single aggregation value.

        Args:
            records: Records to aggregate
            agg_spec: Aggregation specification

        Returns:
            Aggregated value
        """
        func = agg_spec["function"]
        field = agg_spec["field"]

        # Handle count(*)
        if func == "count" and field == "*":
            return len(records)

        # Extract field values
        values = []
        for record in records:
            value = self._get_field_value(record, field)
            if value is not None:
                values.append(value)

        # Calculate aggregation
        if func == "count":
            return len(values)
        elif func == "unique_count":
            return len(self._get_unique_values(values))
        elif func == "sum":
            return sum(self._to_numeric(v) for v in values) if values else 0
        elif func == "min":
            return min(self._to_numeric(v) for v in values) if values else None
        elif func == "max":
            return max(self._to_numeric(v) for v in values) if values else None
        elif func in ["average", "avg"]:
            if not values:
                return None
            numeric_values = [self._to_numeric(v) for v in values]
            return statistics.mean(numeric_values)
        elif func in ["median", "med"]:
            if not values:
                return None
            numeric_values = [self._to_numeric(v) for v in values]
            return statistics.median(numeric_values)
        elif func in ["std", "standard_deviation"]:
            if len(values) < 2:
                return None
            numeric_values = [self._to_numeric(v) for v in values]
            return statistics.stdev(numeric_values)
        elif func in ["percentile", "percentiles", "p", "pct"]:
            if not values:
                return None
            numeric_values = sorted([self._to_numeric(v) for v in values])
            percentile_values = agg_spec.get("percentile_values", [50])  # Default to median

            if len(percentile_values) == 1:
                # Single percentile
                return self._calculate_percentile(numeric_values, percentile_values[0])
            else:
                # Multiple percentiles - return dict
                result = {}
                for p in percentile_values:
                    result[f"p{int(p)}"] = self._calculate_percentile(numeric_values, p)
                return result
        elif func in ["percentile_rank", "percentile_ranks", "pct_rank", "pct_ranks"]:
            if not values:
                return None
            numeric_values = sorted([self._to_numeric(v) for v in values])
            rank_values = agg_spec.get("rank_values", [])

            if not rank_values:
                raise TQLError("percentile_rank requires at least one value")

            if len(rank_values) == 1:
                # Single rank value
                return self._calculate_percentile_rank(numeric_values, rank_values[0])
            else:
                # Multiple rank values - return dict
                result = {}
                for v in rank_values:
                    result[f"rank_{v}"] = self._calculate_percentile_rank(numeric_values, v)
                return result
        elif func in ["values", "unique", "cardinality"]:
            # Return unique values from the field
            unique_values = self._get_unique_values(values)
            # Sort the values for consistent output
            try:
                # Try to sort if values are comparable
                unique_values.sort()
            except TypeError:
                # If values aren't comparable (mixed types), just return unsorted
                pass
            return unique_values
        else:
            raise TQLError(f"Unsupported aggregation function: {func}")

    def _apply_modifiers(
        self, results: List[Dict[str, Any]], aggregations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply top/bottom modifiers to results.

        Args:
            results: Aggregation results
            aggregations: Aggregation specifications with modifiers

        Returns:
            Modified results
        """
        # Check if any aggregation has modifiers
        for agg in aggregations:
            if "modifier" in agg:
                # Sort results based on the aggregation value
                agg_key = agg.get("alias") or agg["function"]

                # Get the value from the result
                def get_sort_value(result, key=agg_key):
                    if "aggregations" in result:
                        return result["aggregations"].get(key, 0)
                    else:
                        return result.get(key, 0)

                # Sort
                reverse = agg["modifier"] == "top"
                results = sorted(results, key=get_sort_value, reverse=reverse)

                # Limit
                limit = agg.get("limit", 10)
                results = results[:limit]

                break  # Only apply first modifier found

        return results

    def _apply_bucket_limits(  # noqa: C901
        self, results: List[Dict[str, Any]], normalized_fields: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply per-field bucket size limits to results.

        Args:
            results: Aggregation results
            normalized_fields: Group by fields with bucket_size specifications

        Returns:
            Results with bucket limits applied
        """
        # Check if we have any bucket size limits
        has_limits = any(field.get("bucket_size") is not None for field in normalized_fields)
        if not has_limits:
            return results

        # For single-level grouping, apply the limit directly
        if len(normalized_fields) == 1:
            bucket_size = normalized_fields[0].get("bucket_size")
            if bucket_size:
                # Sort by doc_count (most common pattern) and limit
                results = sorted(results, key=lambda x: x.get("doc_count", 0), reverse=True)
                results = results[:bucket_size]
            return results

        # For multi-level grouping, we need to apply limits hierarchically
        # First, group results by each level and apply limits

        # Sort all results by doc_count first
        results = sorted(results, key=lambda x: x.get("doc_count", 0), reverse=True)

        # Build a hierarchical structure to apply limits at each level
        filtered_results = []

        # Track unique values at each level
        level_values: Dict[int, Dict[Any, Set[Any]]] = {}
        for level, _field_spec in enumerate(normalized_fields):
            level_values[level] = {}

        for result in results:
            # Check if this result should be included based on bucket limits at each level
            should_include = True

            # Build the key path for this result
            key_path = []
            for level, field_spec in enumerate(normalized_fields):
                field_name = field_spec["field"]
                field_value = result["key"].get(field_name)
                key_path.append(field_value)

                # For each level, check if we've hit the bucket limit
                bucket_size = field_spec.get("bucket_size")
                if bucket_size is not None:
                    # Build parent key (all fields up to but not including current level)
                    parent_key = tuple(key_path[:level]) if level > 0 else ()

                    # Initialize tracking for this parent if needed
                    if parent_key not in level_values[level]:
                        level_values[level][parent_key] = set()

                    # Check if adding this value would exceed the bucket limit
                    if field_value not in level_values[level][parent_key]:
                        if len(level_values[level][parent_key]) >= bucket_size:
                            should_include = False
                            break
                        else:
                            # Reserve this slot
                            level_values[level][parent_key].add(field_value)

            if should_include:
                filtered_results.append(result)

        return filtered_results

    def _get_field_value(self, record: Dict[str, Any], field_path: str) -> Any:
        """Get a field value from a record, supporting nested fields.

        Args:
            record: The record dictionary
            field_path: Dot-separated field path

        Returns:
            The field value or None if not found
        """
        parts = field_path.split(".")
        current = record

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _to_numeric(self, value: Any) -> Union[int, float]:
        """Convert value to numeric type.

        Args:
            value: Value to convert

        Returns:
            Numeric value

        Raises:
            TQLError: If value cannot be converted
        """
        if isinstance(value, (int, float)):
            return value

        if isinstance(value, str):
            try:
                # Try int first
                if "." not in value:
                    return int(value)
                else:
                    return float(value)
            except ValueError:
                raise TQLError(
                    f"Cannot convert '{value}' to numeric value. " f"Ensure the field contains numeric data."
                )

        raise TQLError(
            f"Cannot convert {type(value).__name__} to numeric value. " f"Ensure the field contains numeric data."
        )

    def _calculate_percentile(self, sorted_values: List[Union[int, float]], percentile: float) -> Optional[float]:
        """Calculate the percentile value for a sorted list of values.

        Args:
            sorted_values: Sorted list of numeric values
            percentile: Percentile to calculate (0-100)

        Returns:
            The percentile value
        """
        if not sorted_values:
            return None

        if percentile < 0 or percentile > 100:
            raise TQLError(f"Percentile must be between 0 and 100, got {percentile}")

        n = len(sorted_values)
        if n == 1:
            return sorted_values[0]

        # Calculate the position using linear interpolation
        pos = (n - 1) * (percentile / 100.0)
        lower_idx = int(pos)
        upper_idx = min(lower_idx + 1, n - 1)

        if lower_idx == upper_idx:
            return sorted_values[lower_idx]

        # Linear interpolation between two values
        lower_value = sorted_values[lower_idx]
        upper_value = sorted_values[upper_idx]
        fraction = pos - lower_idx

        return lower_value + fraction * (upper_value - lower_value)

    def _calculate_percentile_rank(self, sorted_values: List[Union[int, float]], value: float) -> Optional[float]:
        """Calculate the percentile rank of a value within a sorted list.

        Args:
            sorted_values: Sorted list of numeric values
            value: Value to find percentile rank for

        Returns:
            The percentile rank (0-100)
        """
        if not sorted_values:
            return None

        n = len(sorted_values)

        # Count how many values are less than the target value
        count_less = 0
        count_equal = 0

        for v in sorted_values:
            if v < value:
                count_less += 1
            elif v == value:
                count_equal += 1

        # Calculate percentile rank
        # If value is in the list, use midpoint of its range
        if count_equal > 0:
            rank = (count_less + count_equal / 2.0) / n * 100
        else:
            # Value not in list, interpolate
            rank = count_less / n * 100

        return round(rank, 2)

    def _get_unique_values(self, values: List[Any]) -> List[Any]:
        """Get unique values from a list, handling unhashable types like dicts.

        Args:
            values: List of values that may contain unhashable types

        Returns:
            List of unique values
        """
        if not values:
            return []

        # Try the fast path first - use set if all values are hashable
        try:
            return list(set(values))
        except TypeError:
            # Some values are unhashable, use slower but safe approach
            unique_values = []
            for value in values:
                if value not in unique_values:
                    unique_values.append(value)
            return unique_values

    def _make_hashable_key(self, key_parts: List[tuple]) -> tuple:
        """Convert a key with potentially unhashable values to a hashable key.

        Args:
            key_parts: List of (field_name, value) tuples

        Returns:
            Hashable tuple that can be used as a dictionary key
        """
        hashable_parts = []
        for field_name, value in key_parts:
            try:
                # Try to hash the value - if it works, use it as-is
                hash(value)
                hashable_parts.append((field_name, value))
            except TypeError:
                # Value is unhashable (like dict), convert to string representation
                hashable_parts.append((field_name, str(value)))

        return tuple(hashable_parts)
