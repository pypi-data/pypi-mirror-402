"""Post-processor for applying mutators to OpenSearch query results.

This module handles the application of mutators that cannot be pre-processed
by OpenSearch field mappings/analyzers and must be applied to results after
they are returned from OpenSearch.
"""

import copy
from typing import Any, Dict, List, Optional

from .mutator_analyzer import PostProcessingRequirement
from .mutators import apply_mutators


class QueryPostProcessor:
    """Applies post-processing mutators to OpenSearch query results."""

    def __init__(self):
        """Initialize the post-processor."""

    def filter_results(  # noqa: C901
        self, results: List[Dict[str, Any]], requirements: List[PostProcessingRequirement]
    ) -> List[Dict[str, Any]]:
        """Filter results based on post-processing requirements.

        This method handles operator-based filtering for all operators that require
        post-processing evaluation.

        Args:
            results: List of result records from OpenSearch
            requirements: List of post-processing requirements

        Returns:
            Filtered list of results
        """
        if not requirements:
            return results

        filtered_results = []

        # Check if we have a logical expression requirement
        has_logical_expr_req = any(req.applies_to == "logical_expression" for req in requirements)

        for result in results:
            should_include = True

            # If we have a logical expression requirement, use only that for filtering
            if has_logical_expr_req:
                # Only apply logical expression requirements
                for requirement in requirements:
                    if requirement.applies_to == "logical_expression":
                        expression = requirement.metadata.get("expression", {}) if requirement.metadata else {}
                        if not self._evaluate_logical_expression(result, expression):
                            should_include = False
                            break
            else:
                # Apply other requirements normally
                for requirement in requirements:
                    # Handle nslookup expressions with conditions
                    if (
                        requirement.applies_to == "nslookup_expr"
                        and requirement.metadata
                        and "conditions" in requirement.metadata
                    ):
                        # Create evaluator components for nslookup expression evaluation
                        from tql.evaluator import TQLEvaluator
                        from tql.evaluator_components.field_access import FieldAccessor
                        from tql.evaluator_components.special_expressions import SpecialExpressionEvaluator

                        field_accessor = FieldAccessor()
                        evaluator = TQLEvaluator()
                        special_evaluator = SpecialExpressionEvaluator(
                            field_accessor.get_field_value, evaluator._evaluate_node
                        )

                        # Safe access with validation
                        # conditions is guaranteed to exist by the if check above
                        conditions = requirement.metadata["conditions"]
                        nslookup_params = requirement.metadata.get("nslookup_params", {})

                        # Build node for evaluation
                        node = {
                            "type": "nslookup_expr",
                            "field": requirement.field_name,
                            "conditions": conditions,
                            "nslookup_params": nslookup_params,
                        }

                        # Evaluate the nslookup expression
                        if not special_evaluator.evaluate_nslookup_expr(node, result, {}):
                            should_include = False
                            break
                    # Handle geo expressions with conditions
                    elif (
                        requirement.applies_to == "geo_expr"
                        and requirement.metadata
                        and "conditions" in requirement.metadata
                    ):
                        # Safe access - conditions is guaranteed to exist by the if check
                        conditions = requirement.metadata["conditions"]
                        if conditions:
                            # Get the geo data that was enriched
                            geo_data = None
                            if "." in requirement.field_name:
                                # For nested fields like destination.ip, check destination.geo
                                parent_path = requirement.field_name.rsplit(".", 1)[0]
                                parent = self._get_field_value(result, parent_path)
                                if isinstance(parent, dict):
                                    geo_data = parent
                            else:
                                # For top-level fields, check enrichment
                                if "enrichment" in result and isinstance(result["enrichment"], dict):
                                    geo_data = result["enrichment"]

                            # Evaluate conditions against the geo data
                            if geo_data:
                                # Create a temporary record with the geo data
                                temp_record = geo_data.get("geo", {})
                                # Also include AS data if present
                                if "as" in geo_data:
                                    temp_record["as"] = geo_data["as"]

                                # Evaluate the conditions using the same evaluator
                                from tql.evaluator import TQLEvaluator

                                evaluator = TQLEvaluator()
                                if not evaluator._evaluate_node(conditions, temp_record, {}):
                                    should_include = False
                                    break
                            else:
                                # No geo data found, exclude the result
                                should_include = False
                                break
                    elif requirement.metadata and "operator" in requirement.metadata:
                        # Check if this is an array operator with comparison
                        if "comparison_operator" in requirement.metadata:
                            # This is a special case: field | any/all/none eq value
                            # Safe access - both keys are guaranteed to exist by the if checks
                            array_operator = requirement.metadata["operator"]  # exists from line 128 check
                            comparison_operator = requirement.metadata[
                                "comparison_operator"
                            ]  # exists from line 135 check
                            value = requirement.metadata.get("value")

                            # Get the field value with proper nested field handling
                            temp_field_name = self._get_mutated_field_name(requirement.field_name)
                            field_value = self._get_field_value(result, temp_field_name)
                            if field_value is None:
                                # No mutated value, get original
                                field_value = self._get_field_value(result, requirement.field_name)

                            # Apply array operator with comparison
                            if not self._check_array_operator_with_comparison(
                                field_value, array_operator, comparison_operator, value
                            ):
                                should_include = False
                                break
                        else:
                            # Regular operator check
                            # Safe access - operator is guaranteed to exist by the if check at line 134
                            operator = requirement.metadata["operator"]
                            value = requirement.metadata.get("value")

                            # Check if this was originally a different operator (for type-changing mutators)
                            if requirement.metadata.get("_original_comparison"):
                                # Safe access - validated by .get() check above
                                original = requirement.metadata["_original_comparison"]
                                # Validate that operator exists in original
                                operator = original.get("operator", operator)
                                value = original.get("value", value)

                            # Get the field value - either mutated or original
                            # First check for mutated value in temp field
                            temp_field_name = self._get_mutated_field_name(requirement.field_name)
                            field_value = self._get_field_value(result, temp_field_name)
                            if field_value is None:
                                # No mutated value, get original
                                field_value = self._get_field_value(result, requirement.field_name)

                            # Apply the operator check
                            if not self._check_operator(field_value, operator, value):
                                should_include = False
                                break

            if should_include:
                filtered_results.append(result)

        return filtered_results

    def _check_operator(self, field_value: Any, operator: str, value: Any) -> bool:  # noqa: C901
        """Check if a field value matches the given operator and value.

        Args:
            field_value: The field value to check
            operator: The operator to apply
            value: The value to compare against

        Returns:
            True if the operator check passes, False otherwise
        """
        # Unwrap single-element lists for comparison
        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        # Handle None/missing fields
        if field_value is None:
            # Most operators should return False for missing fields
            return False

        # String operators
        if operator == "contains":
            return str(value).lower() in str(field_value).lower()
        elif operator == "not_contains":
            return str(value).lower() not in str(field_value).lower()
        elif operator == "startswith":
            return str(field_value).lower().startswith(str(value).lower())
        elif operator == "not_startswith":
            return not str(field_value).lower().startswith(str(value).lower())
        elif operator == "endswith":
            return str(field_value).lower().endswith(str(value).lower())
        elif operator == "not_endswith":
            return not str(field_value).lower().endswith(str(value).lower())

        # Equality operators
        elif operator in ["eq", "="]:
            # Handle boolean comparisons
            if isinstance(field_value, bool) and isinstance(value, str):
                # Convert string to boolean for comparison
                if value.lower() == "true":
                    return field_value is True
                elif value.lower() == "false":
                    return field_value is False
            # Handle numeric comparisons
            if isinstance(field_value, (int, float)) and isinstance(value, str):
                try:
                    return field_value == float(value)
                except (ValueError, TypeError):
                    pass
            elif isinstance(value, (int, float)) and isinstance(field_value, str):
                try:
                    return float(field_value) == value
                except (ValueError, TypeError):
                    pass
            return field_value == value
        elif operator in ["ne", "!="]:
            # Handle boolean comparisons
            if isinstance(field_value, bool) and isinstance(value, str):
                # Convert string to boolean for comparison
                if value.lower() == "true":
                    return field_value is not True
                elif value.lower() == "false":
                    return field_value is not False
            # Handle numeric comparisons
            if isinstance(field_value, (int, float)) and isinstance(value, str):
                try:
                    return field_value != float(value)
                except (ValueError, TypeError):
                    pass
            elif isinstance(value, (int, float)) and isinstance(field_value, str):
                try:
                    return float(field_value) != value
                except (ValueError, TypeError):
                    pass
            return field_value != value

        # Comparison operators
        elif operator in ["gt", ">"]:
            try:
                return float(field_value) > float(value)
            except (ValueError, TypeError):
                return str(field_value) > str(value)
        elif operator in ["gte", ">="]:
            try:
                return float(field_value) >= float(value)
            except (ValueError, TypeError):
                return str(field_value) >= str(value)
        elif operator in ["lt", "<"]:
            try:
                return float(field_value) < float(value)
            except (ValueError, TypeError):
                return str(field_value) < str(value)
        elif operator in ["lte", "<="]:
            try:
                return float(field_value) <= float(value)
            except (ValueError, TypeError):
                return str(field_value) <= str(value)

        # Array operators
        elif operator == "any":
            if isinstance(field_value, (list, tuple)):
                # For arrays, ANY element must equal the value
                return any(elem == value for elem in field_value)
            else:
                # For single values, simple equality
                return field_value == value
        elif operator == "not_any":
            if isinstance(field_value, (list, tuple)):
                # For arrays, if ANY element equals the value, fail
                return not any(elem == value for elem in field_value)
            else:
                # For single values, if equal, fail
                return field_value != value
        elif operator == "all":
            if isinstance(field_value, (list, tuple)):
                # For arrays, ALL elements must equal the value
                # Empty arrays should not pass ALL
                return len(field_value) > 0 and all(elem == value for elem in field_value)
            else:
                # For single values, simple equality
                return field_value == value
        elif operator == "not_all":
            if isinstance(field_value, (list, tuple)):
                # For arrays, if ALL elements equal the value, fail
                # Empty arrays should pass NOT_ALL
                return len(field_value) == 0 or not all(elem == value for elem in field_value)
            else:
                # For single values, if equal, fail
                return field_value != value
        elif operator == "none":
            if isinstance(field_value, (list, tuple)):
                # For arrays, NO element must equal the value (same as not_any)
                return not any(elem == value for elem in field_value)
            else:
                # For single values, must not equal
                return field_value != value

        # Existence operators
        elif operator == "exists":
            # For exists, we just check that the field has a value
            # The actual exists check was already done by OpenSearch
            return field_value is not None
        elif operator == "not_exists":
            # This shouldn't normally reach post-processing, but handle it
            return field_value is None

        # Default to False for unknown operators
        return False

    def _evaluate_logical_expression(self, result: Dict[str, Any], expression: Dict[str, Any]) -> bool:  # noqa: C901
        """Evaluate a logical expression (AND/OR) against a result.

        Args:
            result: The result record to check
            expression: The logical expression AST node

        Returns:
            True if the expression matches, False otherwise
        """
        if not expression or "type" not in expression:
            return True

        expr_type = expression.get("type")

        if expr_type == "logical_expression":
            operator = expression.get("operator", "").upper()
            left = expression.get("left", {})
            right = expression.get("right", {})

            # Recursively evaluate left and right
            left_result = self._evaluate_logical_expression(result, left)

            # Short-circuit evaluation
            if operator == "OR" and left_result:
                return True
            elif operator == "AND" and not left_result:
                return False

            right_result = self._evaluate_logical_expression(result, right)

            if operator == "OR":
                return left_result or right_result
            elif operator == "AND":
                return left_result and right_result
            else:
                return False

        elif expr_type == "comparison":
            # Evaluate a comparison expression
            field_name = expression.get("field")
            operator = expression.get("operator")
            value = expression.get("value")
            field_mutators = expression.get("field_mutators", [])

            if not field_name:
                return False

            # Get the field value
            temp_field_name = self._get_mutated_field_name(field_name)
            field_value = self._get_field_value(result, temp_field_name)
            if field_value is None:
                # No mutated value, get original
                field_value = self._get_field_value(result, field_name)

            # Check for array operators in field_mutators
            array_operator = None
            for mutator in field_mutators:
                mutator_name = mutator.get("name", "").lower()
                if mutator_name in ["any", "all", "none"]:
                    array_operator = mutator_name
                    break

            if array_operator:
                # Use array operator comparison
                if operator is None:
                    return False
                return self._check_array_operator_with_comparison(field_value, array_operator, operator, value)
            else:
                # Regular operator check
                if operator is None:
                    return False
                return self._check_operator(field_value, operator, value)

        else:
            # Unknown expression type
            return True

    def _check_array_operator_with_comparison(  # noqa: C901
        self, field_value: Any, array_operator: str, comparison_operator: str, value: Any
    ) -> bool:
        """Check if a field value matches the array operator with comparison.

        Handles cases like: field | any eq value, field | all gt value, etc.

        Args:
            field_value: The field value to check (can be array or single value)
            array_operator: The array operator (any, all, none)
            comparison_operator: The comparison operator (eq, gt, contains, etc.)
            value: The value to compare against

        Returns:
            True if the check passes, False otherwise
        """
        # Unwrap single-element lists for comparison value
        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        # Handle None/missing fields
        if field_value is None:
            return False

        # Convert single values to list for uniform processing
        if not isinstance(field_value, (list, tuple)):
            field_value = [field_value]

        # Apply the array operator with comparison
        if array_operator == "any":
            # ANY element must match the comparison
            for elem in field_value:
                if self._check_single_value_operator(elem, comparison_operator, value):
                    return True
            return False

        elif array_operator == "all":
            # ALL elements must match the comparison
            if len(field_value) == 0:
                return False  # Empty arrays fail ALL checks
            for elem in field_value:
                if not self._check_single_value_operator(elem, comparison_operator, value):
                    return False
            return True

        elif array_operator == "none":
            # NO element must match the comparison
            for elem in field_value:
                if self._check_single_value_operator(elem, comparison_operator, value):
                    return False
            return True

        # Unknown array operator
        return False

    def _check_single_value_operator(self, field_value: Any, operator: str, value: Any) -> bool:  # noqa: C901
        """Check if a single value matches the given operator and value.

        This is a helper for array operator checks.
        """
        # Handle None/missing values
        if field_value is None:
            return False

        # Reuse existing operator logic
        # String operators
        if operator == "contains":
            return str(value).lower() in str(field_value).lower()
        elif operator == "not_contains":
            return str(value).lower() not in str(field_value).lower()
        elif operator == "startswith":
            return str(field_value).lower().startswith(str(value).lower())
        elif operator == "not_startswith":
            return not str(field_value).lower().startswith(str(value).lower())
        elif operator == "endswith":
            return str(field_value).lower().endswith(str(value).lower())
        elif operator == "not_endswith":
            return not str(field_value).lower().endswith(str(value).lower())

        # Equality operators
        elif operator in ["eq", "="]:
            return field_value == value
        elif operator in ["ne", "!="]:
            return field_value != value

        # Comparison operators
        elif operator in ["gt", ">"]:
            try:
                return float(field_value) > float(value)
            except (ValueError, TypeError):
                return str(field_value) > str(value)
        elif operator in ["gte", ">="]:
            try:
                return float(field_value) >= float(value)
            except (ValueError, TypeError):
                return str(field_value) >= str(value)
        elif operator in ["lt", "<"]:
            try:
                return float(field_value) < float(value)
            except (ValueError, TypeError):
                return str(field_value) < str(value)
        elif operator in ["lte", "<="]:
            try:
                return float(field_value) <= float(value)
            except (ValueError, TypeError):
                return str(field_value) <= str(value)

        # Default to False for unknown operators
        return False

    def process_results(
        self,
        results: List[Dict[str, Any]],
        requirements: List[PostProcessingRequirement],
        track_enrichments: bool = False,
    ) -> List[Dict[str, Any]]:
        """Apply post-processing mutators to query results.

        Args:
            results: List of result records from OpenSearch
            requirements: List of post-processing requirements
            track_enrichments: If True, track which records were enriched

        Returns:
            List of processed results with mutators applied.
            If track_enrichments is True, each result will have a '_enriched' flag.
        """
        if not requirements:
            return results

        processed_results = []

        for result in results:
            # Deep copy to avoid modifying original
            processed_result = copy.deepcopy(result)
            enriched = False

            # Apply each post-processing requirement
            for requirement in requirements:
                try:
                    was_enriched = self._apply_requirement(processed_result, requirement)
                    if was_enriched:
                        enriched = True
                except Exception:
                    # Log error but continue processing
                    # In a production system, you might want to log this
                    continue

            # Track enrichment status if requested
            if track_enrichments:
                processed_result["_enriched"] = enriched

            processed_results.append(processed_result)

        return processed_results

    def _apply_requirement(self, result: Dict[str, Any], requirement: PostProcessingRequirement) -> bool:
        """Apply a single post-processing requirement to a result.

        Args:
            result: The result record to modify
            requirement: The post-processing requirement to apply

        Returns:
            True if the record was enriched, False otherwise
        """
        if requirement.applies_to == "field":
            return self._apply_field_mutators(result, requirement)
        elif requirement.applies_to == "value":
            return self._apply_value_mutators(result, requirement)
        elif requirement.applies_to == "geo_expr":
            return self._apply_geo_expression(result, requirement)
        elif requirement.applies_to == "nslookup_expr":
            return self._apply_nslookup_expression(result, requirement)
        return False

    def _apply_field_mutators(  # noqa: C901
        self, result: Dict[str, Any], requirement: PostProcessingRequirement
    ) -> bool:
        """Apply field mutators to a result record.

        Args:
            result: The result record to modify
            requirement: The field mutator requirement

        Returns:
            True if enrichment occurred, False otherwise
        """
        # Check if this is an operator-only requirement (like ALL operator with no mutators)
        if requirement.metadata and "operator" in requirement.metadata and not requirement.mutators:
            # This is handled separately in filter_results
            return False

        # Get the field value using the mapped field name
        field_value = self._get_field_value(result, requirement.mapped_field_name)

        if field_value is None:
            return False

        # Apply mutators to the field value
        try:
            mutated_value = apply_mutators(field_value, requirement.mutators, requirement.field_name, result)

            # Check if this is a type-changing mutator that should not replace the field
            # These mutators are used for filtering, not transforming the field value
            TYPE_CHANGING_FILTER_MUTATORS = {
                "is_private",
                "is_global",
                "length",
                "any",
                "all",
                "avg",
                "average",
                "sum",
                "max",
                "min",
                "split",
            }

            # Transform mutators that should always transform the output field
            TRANSFORM_MUTATORS = {
                "lowercase",
                "uppercase",
                "trim",
                "replace",
                "refang",
                "defang",
                "b64encode",
                "b64decode",
                "urldecode",
            }

            mutator_names = {m.get("name", "").lower() for m in requirement.mutators}

            # Check the operator from metadata to determine if this is for filtering only
            operator = requirement.metadata.get("operator", "") if requirement.metadata else ""
            is_filtering_operation = operator in [
                "contains",
                "not_contains",
                "startswith",
                "endswith",
                "not_startswith",
                "not_endswith",
                "eq",
                "=",
                "ne",
                "!=",
                ">",
                ">=",
                "<",
                "<=",
                "gt",
                "gte",
                "lt",
                "lte",
            ]

            # Check the LAST mutator to determine output behavior
            last_mutator_name = None
            if requirement.mutators:
                last_mutator_name = requirement.mutators[-1].get("name", "").lower()

            # Special case: exists operator with non-type-changing mutators should transform output
            is_exists_with_transform_mutators = operator == "exists" and not mutator_names.intersection(
                TYPE_CHANGING_FILTER_MUTATORS
            )

            # Determine whether to transform the field or store in temp field
            # The key is: what does the LAST mutator do?
            if last_mutator_name in TYPE_CHANGING_FILTER_MUTATORS:
                # Last mutator changes type - always store in temp field
                should_transform_output = False
            elif last_mutator_name in TRANSFORM_MUTATORS:
                # Last mutator is a transformer - always transform output
                should_transform_output = True
            else:
                # Fall back to previous logic
                should_transform_output = (
                    # Exists operator with non-type-changing mutators
                    is_exists_with_transform_mutators
                    # No filtering operation and no type-changing mutators
                    or (not is_filtering_operation and not mutator_names.intersection(TYPE_CHANGING_FILTER_MUTATORS))
                )

            # Check if this is an enrichment mutator first
            from .mutators import ENRICHMENT_MUTATORS

            # Check if we have geo/geoip_lookup enrichment mutator
            is_geo_enrichment = False
            for mutator in requirement.mutators:
                mutator_name = mutator.get("name", "").lower()
                if mutator_name in ["geo", "geoip_lookup"]:
                    is_geo_enrichment = True
                    break

            if should_transform_output and not is_geo_enrichment:
                # Update the result with the mutated value
                # Use the original field name for the output
                self._set_field_value(result, requirement.field_name, mutated_value)
            elif not is_geo_enrichment:
                # For type-changing mutators with filtering operations, store in temp field
                temp_field_name = self._get_mutated_field_name(requirement.field_name)
                self._set_field_value(result, temp_field_name, mutated_value)

            # Check if we have any enrichment mutators
            enrichment_mutator_found = False
            for mutator in requirement.mutators:
                if mutator.get("name", "").lower() in ENRICHMENT_MUTATORS:
                    enrichment_mutator_found = True
                    break

            # Handle enrichment mutators specially for geo/geoip_lookup
            if enrichment_mutator_found and last_mutator_name in ["geo", "geoip_lookup"]:
                # For geo enrichment mutators applied as field mutators,
                # we need to store the enrichment data at the parent level
                if isinstance(mutated_value, dict) and "geo" in mutated_value:
                    if "." in requirement.field_name:
                        # Nested field like destination.ip
                        parent_path = requirement.field_name.rsplit(".", 1)[0]
                        parent = self._get_or_create_parent(result, parent_path)

                        # Add geo and as data under the parent
                        if "geo" in mutated_value:
                            parent["geo"] = mutated_value["geo"]
                        if "as" in mutated_value:
                            parent["as"] = mutated_value["as"]
                    else:
                        # Top-level field - use enrichment parent
                        if "enrichment" not in result:
                            result["enrichment"] = {}

                        if "geo" in mutated_value:
                            result["enrichment"]["geo"] = mutated_value["geo"]
                        if "as" in mutated_value:
                            result["enrichment"]["as"] = mutated_value["as"]

            return enrichment_mutator_found

        except Exception:
            # If mutation fails, leave original value
            pass

        return False

    def _apply_value_mutators(self, result: Dict[str, Any], requirement: PostProcessingRequirement) -> bool:
        """Apply value mutators to a result record.

        Note: Value mutators are typically applied during query evaluation,
        not to results. This method is included for completeness but may
        not be commonly used.

        Args:
            result: The result record to modify
            requirement: The value mutator requirement

        Returns:
            False (value mutators do not enrich records)
        """
        # Value mutators are typically applied to query values, not result values
        # This method is included for completeness but may not be used in practice
        return False

    def _apply_geo_expression(  # noqa: C901
        self, result: Dict[str, Any], requirement: PostProcessingRequirement
    ) -> bool:
        """Apply geo expression enrichment and filtering to a result.

        Args:
            result: The result record to modify
            requirement: The geo expression requirement

        Returns:
            True if geo enrichment occurred, False otherwise
        """
        # Get the IP field value
        ip_value = self._get_field_value(result, requirement.field_name)

        if not ip_value:
            # No IP value, nothing to enrich
            return False

        # Apply geoip_lookup mutator for enrichment
        try:
            geo_data = apply_mutators(
                ip_value, requirement.mutators, requirement.field_name, result  # Contains geoip_lookup mutator
            )

            # The geo data is returned as a dict with geo.* and as.* fields
            # We need to nest it under the parent of the IP field
            if isinstance(geo_data, dict) and geo_data:
                # Check if a custom field location was specified
                custom_field = None
                for mutator in requirement.mutators:
                    if "params" in mutator:
                        params = mutator["params"]
                        # Convert params from list format to dict if needed
                        if isinstance(params, list):
                            params_dict = {}
                            for param in params:
                                if len(param) == 2:
                                    params_dict[param[0]] = param[1]
                            params = params_dict

                        if "field" in params:
                            custom_field = params["field"]
                            break

                if custom_field:
                    # Use the custom field location
                    parent = self._get_or_create_parent(result, custom_field)
                    # Store geo data directly at the custom location
                    if "geo" in geo_data:
                        parent.update(geo_data["geo"])
                    # Store AS data separately if present
                    if "as" in geo_data and custom_field:
                        # If custom field has a parent, store AS data as sibling
                        if "." in custom_field:
                            as_parent_path = custom_field.rsplit(".", 1)[0]
                            as_parent = self._get_or_create_parent(result, as_parent_path)
                            as_parent["as"] = geo_data["as"]
                        else:
                            # Store at root level
                            result["as"] = geo_data["as"]
                else:
                    # Default behavior: store under parent.geo and parent.as
                    if "." in requirement.field_name:
                        # Nested field like destination.ip or source.ip
                        parent_path = requirement.field_name.rsplit(".", 1)[0]
                        parent = self._get_or_create_parent(result, parent_path)

                        # Add geo and as data under the parent
                        if "geo" in geo_data:
                            parent["geo"] = geo_data["geo"]
                        if "as" in geo_data:
                            parent["as"] = geo_data["as"]
                    else:
                        # Top-level field like 'ip' - use generic enrichment parent
                        if "enrichment" not in result:
                            result["enrichment"] = {}

                        if "geo" in geo_data:
                            result["enrichment"]["geo"] = geo_data["geo"]
                        if "as" in geo_data:
                            result["enrichment"]["as"] = geo_data["as"]

            # Note: Filtering based on conditions is handled separately
            # during the filter_results phase, not here
            return True  # Geo enrichment occurred

        except Exception:
            # If geo lookup fails, continue without enrichment
            pass

        return False

    def _apply_nslookup_expression(  # noqa: C901
        self, result: Dict[str, Any], requirement: PostProcessingRequirement
    ) -> bool:
        """Apply nslookup expression enrichment and filtering to a result.

        Args:
            result: The result record to modify
            requirement: The nslookup expression requirement

        Returns:
            True if DNS enrichment occurred, False otherwise
        """
        # Get the field value (IP or hostname)
        field_value = self._get_field_value(result, requirement.field_name)

        if not field_value:
            # No value, nothing to enrich
            return False

        # Check if DNS data already exists (from evaluation phase)
        existing_dns_data = None
        if "." in requirement.field_name:
            # Check nested field location
            parent_path = requirement.field_name.rsplit(".", 1)[0]
            parent = self._get_field_value(result, parent_path)
            if isinstance(parent, dict) and "domain" in parent:
                existing_dns_data = parent["domain"]
        else:
            # Check top-level enrichment location
            if "enrichment" in result and isinstance(result["enrichment"], dict):
                existing_dns_data = result["enrichment"].get("domain")

        # Check if we should force a new lookup
        force_lookup = False
        for mutator in requirement.mutators:
            if "params" in mutator:
                params = mutator["params"]
                if isinstance(params, list):
                    for param in params:
                        if len(param) == 2 and param[0] == "force" and param[1]:
                            force_lookup = True
                            break

        # If DNS data already exists and we're not forcing, skip
        if existing_dns_data and not force_lookup:
            return False

        # Apply nslookup mutator for enrichment
        try:
            dns_data = apply_mutators(
                field_value, requirement.mutators, requirement.field_name, result  # Contains nslookup mutator
            )

            # The DNS data is returned as a dict with the query value as key
            # Each value contains ECS-compliant DNS data
            if isinstance(dns_data, dict) and dns_data:
                # DNS data should have one entry for the queried value
                # Extract the ECS data for the field value
                ecs_dns_data = None
                if field_value in dns_data:
                    ecs_dns_data = dns_data[field_value]
                elif len(dns_data) == 1:
                    # If there's only one entry, use it
                    ecs_dns_data = next(iter(dns_data.values()))

                if ecs_dns_data:
                    # Check if a custom field location was specified
                    custom_field = None
                    for mutator in requirement.mutators:
                        if "params" in mutator:
                            params = mutator["params"]
                            # Convert params from list format to dict if needed
                            if isinstance(params, list):
                                params_dict = {}
                                for param in params:
                                    if len(param) == 2:
                                        params_dict[param[0]] = param[1]
                                params = params_dict

                            if "field" in params:
                                custom_field = params["field"]
                                break

                    if custom_field:
                        # Use the custom field location
                        parent = self._get_or_create_parent(result, custom_field)
                        # Store DNS data directly at the custom location
                        parent.update(ecs_dns_data)
                    else:
                        # Default behavior: store at parent.domain
                        if "." in requirement.field_name:
                            # Nested field like destination.ip or source.hostname
                            parent_path = requirement.field_name.rsplit(".", 1)[0]
                            parent = self._get_or_create_parent(result, parent_path)

                            # Add ECS DNS data under the parent
                            parent["domain"] = ecs_dns_data
                        else:
                            # Top-level field like 'ip' - use generic enrichment parent
                            if "enrichment" not in result:
                                result["enrichment"] = {}

                            result["enrichment"]["domain"] = ecs_dns_data

            # Enrichment successful
            # Note: Filtering based on conditions is handled in filter_results phase
            return True  # DNS enrichment occurred

        except Exception:
            # If DNS lookup fails, continue without enrichment
            pass

        return False

    def _get_or_create_parent(self, record: Dict[str, Any], parent_path: str) -> Dict[str, Any]:
        """Get or create a parent object in the record.

        Args:
            record: The record to modify
            parent_path: Dot-separated path to the parent

        Returns:
            The parent dictionary
        """
        parts = parent_path.split(".")
        current = record

        for part in parts:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                # If the parent exists but isn't a dict, we can't add to it
                raise ValueError(f"Cannot add geo data: {parent_path} is not an object")
            current = current[part]

        return current

    def _get_mutated_field_name(self, field_name: str) -> str:
        """Generate the correct mutated field name for nested or flat fields.

        Args:
            field_name: The original field name (e.g., "user.address.zip" or "status")

        Returns:
            Mutated field name with proper nesting:
            - "user.address.zip" -> "user.address.__zip_mutated__"
            - "status" -> "__status_mutated__"
        """
        field_parts = field_name.split(".")
        if len(field_parts) > 1:
            # For nested fields, only mutate the leaf field name
            return ".".join(field_parts[:-1] + [f"__{field_parts[-1]}_mutated__"])
        else:
            # For flat fields, mutate the entire name
            return f"__{field_name}_mutated__"

    def _get_field_value(self, record: Dict[str, Any], field_path: str) -> Any:
        """Get a field value from a record, supporting nested fields.

        Args:
            record: The record dictionary
            field_path: Dot-separated field path or literal field name

        Returns:
            The field value, or None if not found
        """
        # First try the field_path as a literal key
        if isinstance(record, dict) and field_path in record:
            return record[field_path]

        # If not found as literal, try as dot-separated nested path
        parts = field_path.split(".")
        current = record

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _set_field_value(self, record: Dict[str, Any], field_path: str, value: Any) -> None:
        """Set a field value in a record, supporting nested fields.

        Args:
            record: The record dictionary to modify
            field_path: Dot-separated field path or literal field name
            value: The value to set
        """
        # For setting values, we'll use the dot-separated path approach
        # and create nested structures as needed
        parts = field_path.split(".")
        current = record

        # Navigate to the parent of the target field
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set the final value
        current[parts[-1]] = value


class PostProcessingContext:
    """Context information for post-processing operations."""

    def __init__(self, query: str, field_mappings: Dict[str, Any], requirements: List[PostProcessingRequirement]):
        """Initialize post-processing context.

        Args:
            query: Original TQL query string
            field_mappings: Field mappings used in the query
            requirements: Post-processing requirements
        """
        self.query = query
        self.field_mappings = field_mappings
        self.requirements = requirements
        self.stats = PostProcessingStats()

    def get_performance_impact(self) -> Dict[str, Any]:
        """Get information about the performance impact of post-processing.

        Returns:
            Dictionary with performance impact information
        """
        impact: Dict[str, Any] = {
            "has_post_processing": bool(self.requirements),
            "requirement_count": len(self.requirements),
            "impacted_fields": list(set(req.field_name for req in self.requirements)),
            "mutator_types": [],
            "estimated_overhead": "low",
        }

        # Analyze mutator types for performance estimation
        mutator_counts: Dict[str, int] = {}
        for req in self.requirements:
            for mutator in req.mutators:
                mutator_name = mutator.get("name", "unknown")
                mutator_counts[mutator_name] = mutator_counts.get(mutator_name, 0) + 1
                if mutator_name not in impact["mutator_types"]:
                    impact["mutator_types"].append(mutator_name)

        # Estimate overhead based on mutator types
        expensive_mutators = {"geoip_lookup", "nslookup", "geo"}
        if any(mutator in expensive_mutators for mutator in mutator_counts):
            impact["estimated_overhead"] = "high"
        elif len(self.requirements) > 5:
            impact["estimated_overhead"] = "medium"

        impact["mutator_usage"] = mutator_counts

        return impact


class PostProcessingStats:
    """Statistics tracking for post-processing operations."""

    def __init__(self):
        """Initialize stats tracking."""
        self.processed_records = 0
        self.failed_records = 0
        self.mutator_applications = 0
        self.errors = []

    def record_success(self):
        """Record a successful record processing."""
        self.processed_records += 1

    def record_failure(self, error: str):
        """Record a failed record processing."""
        self.failed_records += 1
        self.errors.append(error)

    def record_mutator_application(self):
        """Record a mutator application."""
        self.mutator_applications += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of processing statistics.

        Returns:
            Dictionary with processing statistics
        """
        total_records = self.processed_records + self.failed_records
        success_rate = (self.processed_records / total_records * 100) if total_records > 0 else 0

        return {
            "total_records": total_records,
            "processed_successfully": self.processed_records,
            "failed_records": self.failed_records,
            "success_rate_percent": round(success_rate, 2),
            "mutator_applications": self.mutator_applications,
            "error_count": len(self.errors),
            "recent_errors": self.errors[-5:] if self.errors else [],  # Last 5 errors
        }


class PostProcessingError(Exception):
    """Exception raised during post-processing operations."""

    def __init__(  # noqa: B042
        self, message: str, field_name: Optional[str] = None, mutator_name: Optional[str] = None
    ):
        """Initialize post-processing error.

        Args:
            message: Error message
            field_name: Field name where error occurred
            mutator_name: Mutator name that caused the error
        """
        super().__init__(message)
        self.field_name = field_name
        self.mutator_name = mutator_name


class BatchPostProcessor(QueryPostProcessor):
    """Post-processor optimized for large batches of results."""

    def __init__(self, batch_size: int = 1000):
        """Initialize batch post-processor.

        Args:
            batch_size: Number of records to process in each batch
        """
        super().__init__()
        self.batch_size = batch_size

    def process_results(
        self,
        results: List[Dict[str, Any]],
        requirements: List[PostProcessingRequirement],
        track_enrichments: bool = False,
    ) -> List[Dict[str, Any]]:
        """Process results in batches for better memory efficiency.

        Args:
            results: List of result records from OpenSearch
            requirements: List of post-processing requirements
            track_enrichments: Whether to track enrichment operations

        Returns:
            List of processed results with mutators applied
        """
        if not requirements:
            return results

        processed_results = []

        # Process in batches
        for i in range(0, len(results), self.batch_size):
            batch = results[i : i + self.batch_size]
            processed_batch = super().process_results(batch, requirements, track_enrichments)
            processed_results.extend(processed_batch)

        return processed_results
