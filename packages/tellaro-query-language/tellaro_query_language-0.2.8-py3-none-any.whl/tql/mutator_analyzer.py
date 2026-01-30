"""Mutator analysis for determining pre vs post-processing requirements.

This module analyzes TQL queries with mutators to determine which mutators can be
handled by OpenSearch field mappings/analyzers (pre-processing) and which must be
applied to results after they return from OpenSearch (post-processing).
"""

import copy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

# from .exceptions import TQLFieldError  # Reserved for future use
from .mutators import create_mutator
from .mutators.base import PerformanceClass
from .opensearch import FieldMapping


class MutatorType(Enum):
    """Classification of mutator processing types."""

    PRE_PROCESSABLE = "pre"  # Can be handled by field mappings/analyzers
    POST_PROCESSABLE = "post"  # Must be applied to results
    CONDITIONAL = "conditional"  # Depends on field mapping availability


# Classification of built-in mutators
MUTATOR_CLASSIFICATIONS: Dict[str, MutatorType] = {
    "lowercase": MutatorType.POST_PROCESSABLE,  # Always post-process (transforms result)
    "uppercase": MutatorType.POST_PROCESSABLE,  # Always post-process (transforms result)
    "trim": MutatorType.POST_PROCESSABLE,  # Always post-process (transforms result)
    "split": MutatorType.POST_PROCESSABLE,  # Always post-process (returns array)
    "replace": MutatorType.POST_PROCESSABLE,  # Always post-process (transforms result)
    "nslookup": MutatorType.POST_PROCESSABLE,  # Always post-process (enrichment)
    "geoip_lookup": MutatorType.POST_PROCESSABLE,  # Always post-process (enrichment)
    "geo": MutatorType.POST_PROCESSABLE,  # Always post-process (enrichment)
    "length": MutatorType.POST_PROCESSABLE,  # Always post-process (returns int)
    "refang": MutatorType.POST_PROCESSABLE,  # Always post-process (modifies value)
    "defang": MutatorType.POST_PROCESSABLE,  # Always post-process (modifies value)
    "b64encode": MutatorType.POST_PROCESSABLE,  # Always post-process (modifies value)
    "b64decode": MutatorType.POST_PROCESSABLE,  # Always post-process (modifies value)
    "urldecode": MutatorType.POST_PROCESSABLE,  # Always post-process (modifies value)
    "is_private": MutatorType.POST_PROCESSABLE,  # Always post-process (returns bool)
    "is_global": MutatorType.POST_PROCESSABLE,  # Always post-process (returns bool)
    "any": MutatorType.POST_PROCESSABLE,  # Always post-process (array evaluation)
    "all": MutatorType.POST_PROCESSABLE,  # Always post-process (array evaluation)
    "none": MutatorType.POST_PROCESSABLE,  # Always post-process (array evaluation)
    "avg": MutatorType.POST_PROCESSABLE,  # Always post-process (array computation)
    "average": MutatorType.POST_PROCESSABLE,  # Always post-process (array computation)
    "sum": MutatorType.POST_PROCESSABLE,  # Always post-process (array computation)
    "min": MutatorType.POST_PROCESSABLE,  # Always post-process (array computation)
    "max": MutatorType.POST_PROCESSABLE,  # Always post-process (array computation)
    "count": MutatorType.POST_PROCESSABLE,  # Always post-process (array computation)
    "unique": MutatorType.POST_PROCESSABLE,  # Always post-process (array computation)
    "first": MutatorType.POST_PROCESSABLE,  # Always post-process (array access)
    "last": MutatorType.POST_PROCESSABLE,  # Always post-process (array access)
}


@dataclass
class PostProcessingRequirement:
    """Represents a mutator that needs to be applied after OpenSearch query execution."""

    field_name: str  # Original field name from query
    mapped_field_name: str  # Field name used in OpenSearch query
    mutators: List[Dict[str, Any]]  # List of mutator specifications
    applies_to: Literal[
        "field", "value", "geo_expr", "nslookup_expr", "logical_expression"
    ]  # Whether this applies to field, value mutators, geo, nslookup, or logical expressions
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata for special processing


@dataclass
class MutatorAnalysisResult:
    """Result of analyzing mutators in a TQL query."""

    optimized_ast: Dict[str, Any]  # AST with pre-processable mutators removed
    post_processing_requirements: List[PostProcessingRequirement]  # Post-processing needed
    health_status: Literal["green", "yellow", "red"]  # Health status
    health_reasons: List[Dict[str, str]]  # Health issues found
    optimizations_applied: List[str]  # List of optimizations applied
    query_dsl: Optional[Dict[str, Any]] = None  # OpenSearch query DSL (added by core TQL class)
    save_enrichment_requested: bool = False  # Whether any mutator requested enrichment saving


class MutatorAnalyzer:
    """Analyzes TQL queries to determine mutator processing requirements."""

    context: Optional[str] = None  # Temporary storage for execution context

    def __init__(self, field_mappings: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None):
        """Initialize the analyzer.

        Args:
            field_mappings: Field mappings for intelligent analysis
        """
        self.field_mappings = field_mappings or {}
        self.intelligent_mappings = {}

        # Parse field mappings into FieldMapping objects
        for field_name, mapping in self.field_mappings.items():
            if isinstance(mapping, dict):
                # Check if this is an OpenSearch-style mapping
                if "type" in mapping and not any(k for k in mapping.keys() if k not in ["type", "fields", "analyzer"]):
                    # OpenSearch-style mapping for a single field
                    field_mapping = FieldMapping(mapping)
                    field_mapping.set_base_field_name(field_name)
                    self.intelligent_mappings[field_name] = field_mapping
                else:
                    # Traditional intelligent mapping with multiple field variants
                    field_mapping = FieldMapping(mapping)
                    if not field_mapping.base_field_name:
                        field_mapping.base_field_name = field_name
                    self.intelligent_mappings[field_name] = field_mapping
            elif isinstance(mapping, str):
                # Check if this looks like a type specification
                if mapping in [
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
                    # Type specification, create intelligent mapping
                    self.intelligent_mappings[field_name] = FieldMapping({field_name: mapping})

    def analyze_ast(self, ast: Dict[str, Any], context: str = "opensearch") -> MutatorAnalysisResult:  # noqa: C901
        """Analyze an AST to determine mutator processing requirements.

        Args:
            ast: The parsed TQL query AST
            context: Execution context ("opensearch" or "in_memory")

        Returns:
            Analysis result with optimized AST and post-processing requirements
        """
        # Deep copy AST to avoid modifying original
        optimized_ast = copy.deepcopy(ast)
        post_processing_requirements: List[PostProcessingRequirement] = []
        health_reasons: List[Dict[str, str]] = []
        optimizations_applied: List[str] = []

        # Track if enrichment saving is requested
        save_enrichment_requested = False

        # Store context temporarily for use in _analyze_node
        self.context = context

        # Check if this is a stats query
        is_stats_query = ast.get("type") in ["stats_expr", "query_with_stats"]

        # Analyze the AST recursively
        self._analyze_node(optimized_ast, post_processing_requirements, health_reasons, optimizations_applied)

        # Clean up context
        self.context = None

        # Clean up nodes marked for removal
        cleaned_ast = self._clean_ast(optimized_ast)

        # If the entire AST was removed (e.g., just "field | any eq value"), return match_all
        if cleaned_ast is None:
            optimized_ast = {"type": "match_all"}
        else:
            optimized_ast = cleaned_ast

        # Check if any mutator requested enrichment saving
        for req in post_processing_requirements:
            for mutator in req.mutators:
                if mutator.get("params"):
                    for param in mutator["params"]:
                        if isinstance(param, list) and len(param) == 2 and param[0] == "save" and param[1]:
                            save_enrichment_requested = True
                            break
            # Also check geo_params in metadata
            if req.metadata and "geo_params" in req.metadata:
                geo_params = req.metadata["geo_params"]
                if geo_params.get("save"):
                    save_enrichment_requested = True
            # Also check nslookup_params in metadata
            if req.metadata and "nslookup_params" in req.metadata:
                nslookup_params = req.metadata["nslookup_params"]
                if nslookup_params.get("save"):
                    save_enrichment_requested = True

        # Determine overall health status based on context
        health_status: Literal["green", "yellow", "red"] = "green"

        # Special handling for stats queries with post-processing in OpenSearch context
        if is_stats_query and context == "opensearch" and post_processing_requirements:
            # Stats queries that require post-processing have extremely poor performance
            health_status = "red"
            health_reasons.append(
                {
                    "status": "red",
                    "query_part": "stats with post-processing",
                    "reason": "Stats query requires fetching all documents for post-processing mutators. "
                    "This will have extremely poor performance on large datasets. "
                    "Consider pre-processing data or using OpenSearch-compatible operations.",
                }
            )

        # For in_memory context, we need to evaluate health considering ALL mutators
        # (both those in post-processing and those remaining in the AST)
        elif context == "in_memory":
            # Pass the optimized AST to health evaluation for in_memory context
            health_eval = self._evaluate_health_for_context(post_processing_requirements, context, optimized_ast)
            health_status = health_eval["health_status"]  # type: ignore[assignment]
            health_reasons.extend(health_eval["health_reasons"])
        elif post_processing_requirements:
            # Evaluate health based on context
            health_eval = self._evaluate_health_for_context(post_processing_requirements, context)
            health_status = health_eval["health_status"]  # type: ignore[assignment]
            health_reasons.extend(health_eval["health_reasons"])

        # Check for red health conditions (errors)
        for reason in health_reasons:
            if reason["status"] == "red":
                health_status = "red"
                break

        return MutatorAnalysisResult(
            optimized_ast=optimized_ast,
            post_processing_requirements=post_processing_requirements,
            health_status=health_status,
            health_reasons=health_reasons,
            optimizations_applied=optimizations_applied,
            save_enrichment_requested=save_enrichment_requested,
        )

    def _clean_ast(self, node: Any) -> Any:  # noqa: C901
        """Remove nodes marked for removal from the AST.

        Args:
            node: AST node to clean

        Returns:
            Cleaned AST node or None if node should be removed
        """
        if not isinstance(node, dict):
            return node

        # Check if this node should be removed
        if node.get("_remove_from_query"):
            return None

        # Clean child nodes
        if node.get("type") == "logical_op":
            operator = node.get("operator", "").lower()
            left = self._clean_ast(node.get("left"))
            right = self._clean_ast(node.get("right"))

            # Special handling for OR with removed nodes
            if operator == "or" and (left is None or right is None):
                # If either side of OR has array operators (was removed),
                # we need to return match_all and handle everything in post-processing
                if left is None or right is None:
                    return {"type": "match_all"}

            # Regular handling for AND
            if left is None and right is None:
                return None
            elif left is None:
                return right
            elif right is None:
                return left
            else:
                node["left"] = left
                node["right"] = right
                return node
        elif node.get("type") == "unary_op":
            operand = self._clean_ast(node.get("operand"))
            if operand is None:
                return None
            node["operand"] = operand
            return node

        # For other node types, check if it should be converted to match_all
        if node.get("_convert_to_match_all"):
            return {"type": "match_all"}

        return node

    def _has_array_operators(self, node: Any) -> bool:
        """Check if an AST node contains array operators (any, all, none).

        Args:
            node: AST node to check

        Returns:
            True if node contains array operators
        """
        if not isinstance(node, dict):
            return False

        node_type = node.get("type")

        if node_type == "comparison":
            # Check field mutators for array operators
            field_mutators = node.get("field_mutators", [])
            for mutator in field_mutators:
                if mutator.get("name", "").lower() in ["any", "all", "none"]:
                    return True
            return False
        elif node_type == "logical_op":
            # Check both sides
            return self._has_array_operators(node.get("left", {})) or self._has_array_operators(node.get("right", {}))
        elif node_type == "unary_op":
            # Check operand
            return self._has_array_operators(node.get("operand", {}))

        return False

    def _has_transform_mutators_with_filtering(self, node: Any) -> bool:
        """Check if an AST node contains transform mutators with filtering operations.

        Args:
            node: AST node to check

        Returns:
            True if node contains transform mutators with filtering operations
        """
        if not isinstance(node, dict):
            return False

        node_type = node.get("type")

        if node_type == "comparison":
            # Check if this is a filtering operation
            operator = node.get("operator", "")
            is_filtering = operator in [
                "eq",
                "=",
                "ne",
                "!=",
                "gt",
                ">",
                "gte",
                ">=",
                "lt",
                "<",
                "lte",
                "<=",
                "contains",
                "not_contains",
                "startswith",
                "endswith",
                "not_startswith",
                "not_endswith",
                "in",
                "not_in",
            ]

            if not is_filtering:
                return False

            # Check field mutators for transform mutators or type-changing mutators that need post-processing
            field_mutators = node.get("field_mutators", [])
            for mutator in field_mutators:
                mutator_name = mutator.get("name", "").lower()
                # Transform mutators that modify the value OR type-changing mutators
                if mutator_name in [
                    "lowercase",
                    "uppercase",
                    "trim",
                    "replace",
                    "refang",
                    "defang",
                    "b64encode",
                    "b64decode",
                    "urldecode",
                    # Type-changing mutators that need post-processing
                    "length",
                    "is_private",
                    "is_global",
                    "split",
                ]:
                    return True
            return False
        elif node_type == "logical_op":
            # Check both sides
            return self._has_transform_mutators_with_filtering(
                node.get("left", {})
            ) or self._has_transform_mutators_with_filtering(node.get("right", {}))
        elif node_type == "unary_op":
            # Check operand
            return self._has_transform_mutators_with_filtering(node.get("operand", {}))

        return False

    def _analyze_node(  # noqa: C901
        self,
        node: Dict[str, Any],
        post_processing_reqs: List[PostProcessingRequirement],
        health_reasons: List[Dict[str, str]],
        optimizations: List[str],
    ) -> None:
        """Recursively analyze an AST node for mutator processing.

        Args:
            node: Current AST node
            post_processing_reqs: List to append post-processing requirements
            health_reasons: List to append health issues
            optimizations: List to append optimization descriptions
        """
        if not isinstance(node, dict):
            return

        node_type = node.get("type")

        if node_type == "comparison":
            self._analyze_comparison_node(node, post_processing_reqs, health_reasons, optimizations)
        elif node_type == "collection_op":
            self._analyze_collection_node(node, post_processing_reqs, health_reasons, optimizations)
        elif node_type == "logical_op":
            operator = node.get("operator", "").lower()

            # Check if this is an OR with array operators OR transform mutators with filtering
            # BEFORE analyzing children (because analyzing children might modify the nodes)
            needs_logical_expression = False
            metadata_type = None

            if operator == "or":
                if self._has_array_operators(node):
                    needs_logical_expression = True
                    metadata_type = "or_with_array_operators"
                elif self._has_transform_mutators_with_filtering(node):
                    needs_logical_expression = True
                    metadata_type = "or_with_transform_mutators"

            if needs_logical_expression:
                # We need to evaluate the entire OR in post-processing
                # But we still want the base query to run (without array operators)

                # Deep copy the original expression before it gets modified
                original_expression = copy.deepcopy(node)

                # Add a special requirement for the entire logical expression
                post_processing_reqs.append(
                    PostProcessingRequirement(
                        field_name="_logical_expression",
                        mapped_field_name="_logical_expression",
                        mutators=[],
                        applies_to="logical_expression",
                        metadata={"expression": original_expression, "type": metadata_type},
                    )
                )

            # Always analyze both sides
            self._analyze_node(node.get("left", {}), post_processing_reqs, health_reasons, optimizations)
            self._analyze_node(node.get("right", {}), post_processing_reqs, health_reasons, optimizations)
        elif node_type == "unary_op":
            operator = node.get("operator", "").lower()

            # Check if this is a NOT with transform mutators that need filtering
            if operator == "not" and self._has_transform_mutators_with_filtering(node.get("operand", {})):
                # We need to evaluate the entire NOT in post-processing
                # Deep copy the original expression before it gets modified
                original_expression = copy.deepcopy(node)

                # Add a special requirement for the entire logical expression
                post_processing_reqs.append(
                    PostProcessingRequirement(
                        field_name="_logical_expression",
                        mapped_field_name="_logical_expression",
                        mutators=[],
                        applies_to="logical_expression",
                        metadata={"expression": original_expression, "type": "not_with_transform_mutators"},
                    )
                )

            # Analyze the operand
            self._analyze_node(node.get("operand", {}), post_processing_reqs, health_reasons, optimizations)
        elif node_type == "geo_expr":
            field_name = node.get("field")
            conditions = node.get("conditions")
            geo_params = node.get("geo_params", {})

            if field_name:
                # For OpenSearch context, geo expressions require post-processing
                if self.context == "opensearch":
                    # Create a post-processing requirement for the geo expression
                    # Build the geoip_lookup mutator
                    mutator_params = []
                    for param_name, param_value in geo_params.items():
                        mutator_params.append([param_name, param_value])

                    geo_mutator: Dict[str, Any] = {"name": "geoip_lookup"}
                    if mutator_params:
                        geo_mutator["params"] = mutator_params

                    # Create the requirement
                    req = PostProcessingRequirement(
                        field_name=field_name,
                        mapped_field_name=field_name,  # Will be mapped during processing
                        mutators=[geo_mutator],
                        applies_to="geo_expr",
                        metadata={"conditions": conditions, "geo_params": geo_params},
                    )
                    post_processing_reqs.append(req)

                    if conditions:
                        optimizations.append(
                            f"Geo expression on field '{field_name}' with conditions requires post-processing"
                        )
                    else:
                        optimizations.append(
                            f"Geo expression on field '{field_name}' for enrichment requires post-processing"
                        )
                else:
                    # For in-memory evaluation, handled during evaluation phase
                    if conditions:
                        optimizations.append(
                            f"Geo expression on field '{field_name}' with conditions handled during evaluation"
                        )
                    else:
                        optimizations.append(
                            f"Geo expression on field '{field_name}' for enrichment handled during evaluation"
                        )

            # Don't analyze conditions recursively - they're part of the geo expression
        elif node_type == "nslookup_expr":
            field_name = node.get("field")
            conditions = node.get("conditions")
            nslookup_params = node.get("nslookup_params", {})

            if field_name:
                # For OpenSearch context, nslookup expressions require post-processing
                if self.context == "opensearch":
                    # Create a post-processing requirement for the nslookup expression
                    # Build the nslookup mutator
                    mutator_params = []
                    for param_name, param_value in nslookup_params.items():
                        mutator_params.append([param_name, param_value])

                    nslookup_mutator: Dict[str, Any] = {"name": "nslookup"}
                    if mutator_params:
                        nslookup_mutator["params"] = mutator_params

                    # Create the requirement
                    req = PostProcessingRequirement(
                        field_name=field_name,
                        mapped_field_name=field_name,  # Will be mapped during processing
                        mutators=[nslookup_mutator],
                        applies_to="nslookup_expr",
                        metadata={"conditions": conditions, "nslookup_params": nslookup_params},
                    )
                    post_processing_reqs.append(req)

                    if conditions:
                        optimizations.append(
                            f"NSLookup expression on field '{field_name}' with conditions requires post-processing"
                        )
                    else:
                        optimizations.append(
                            f"NSLookup expression on field '{field_name}' for enrichment requires post-processing"
                        )
                else:
                    # For in-memory evaluation, handled during evaluation phase
                    if conditions:
                        optimizations.append(
                            f"NSLookup expression on field '{field_name}' with conditions handled during evaluation"
                        )
                    else:
                        optimizations.append(
                            f"NSLookup expression on field '{field_name}' for enrichment handled during evaluation"
                        )

            # Don't analyze conditions recursively - they're part of the nslookup expression
        elif node_type == "query_with_stats":
            # Handle query_with_stats node by analyzing the filter part
            filter_node = node.get("filter")
            if filter_node:
                self._analyze_node(filter_node, post_processing_reqs, health_reasons, optimizations)

            # Analyze the stats part if it contains mutators (though this is rare)
            stats_node = node.get("stats")
            if stats_node:
                self._analyze_node(stats_node, post_processing_reqs, health_reasons, optimizations)

        elif node_type == "stats_expr":
            # Handle pure stats expressions - they typically don't have mutators
            # but check aggregations and group_by fields for any field transformations
            aggregations = node.get("aggregations", [])
            for agg in aggregations:
                # In case aggregations have field mutators in the future
                if isinstance(agg, dict) and agg.get("field_mutators"):
                    # Analyze field mutators within aggregations if they exist
                    field_mutators = agg.get("field_mutators", [])
                    if field_mutators:
                        field_name = agg.get("field", "*")
                        # Add post-processing requirement for mutators in aggregations
                        post_processing_reqs.append(
                            PostProcessingRequirement(
                                field_name=field_name,
                                mapped_field_name=field_name,
                                mutators=field_mutators,
                                applies_to="field",
                            )
                        )

    def _analyze_comparison_node(  # noqa: C901
        self,
        node: Dict[str, Any],
        post_processing_reqs: List[PostProcessingRequirement],
        health_reasons: List[Dict[str, str]],
        optimizations: List[str],
    ) -> None:
        """Analyze a comparison node for mutator processing.

        Args:
            node: Comparison AST node
            post_processing_reqs: List to append post-processing requirements
            health_reasons: List to append health issues
            optimizations: List to append optimization descriptions
        """
        field_name = node.get("field")
        operator = node.get("operator")
        field_mutators = node.get("field_mutators", [])

        if not field_name or not operator:
            return

        # Analyze field mutators
        if field_mutators:
            # Special case: if the last mutator is any/all/none and we have a comparison operator,
            # treat it as an array comparison operator, not a regular mutator
            last_mutator = field_mutators[-1] if field_mutators else None
            if (
                last_mutator
                and last_mutator.get("name", "").lower() in ["any", "all", "none"]
                and operator
                in [
                    "eq",
                    "=",
                    "ne",
                    "!=",
                    "gt",
                    ">",
                    "lt",
                    "<",
                    "gte",
                    ">=",
                    "lte",
                    "<=",
                    "contains",
                    "not_contains",
                    "startswith",
                    "endswith",
                    "not_startswith",
                    "not_endswith",
                ]
            ):

                # Extract the array operator
                array_operator = last_mutator["name"].lower()

                # Process any mutators before the array operator
                remaining_mutators = field_mutators[:-1]
                if remaining_mutators:
                    result = self._analyze_field_mutators(field_name, remaining_mutators, operator)

                    # Update node with optimized mutators
                    if result.optimized_mutators != remaining_mutators:
                        if result.optimized_mutators:
                            node["field_mutators"] = result.optimized_mutators
                        else:
                            # Remove field_mutators if all were optimized away
                            node.pop("field_mutators", None)
                        optimizations.extend(result.optimizations)

                    # Add post-processing requirements for the remaining mutators
                    if result.post_processing_mutators:
                        post_processing_reqs.append(
                            PostProcessingRequirement(
                                field_name=field_name,
                                mapped_field_name=result.selected_field or field_name,
                                mutators=result.post_processing_mutators,
                                applies_to="field",
                            )
                        )
                else:
                    # No other mutators, remove field_mutators from node
                    node.pop("field_mutators", None)

                # Add post-processing requirement for the array comparison
                post_processing_reqs.append(
                    PostProcessingRequirement(
                        field_name=field_name,
                        mapped_field_name=field_name,
                        mutators=[],  # No mutators, just operator-based filtering
                        applies_to="field",
                        metadata={
                            "operator": array_operator,
                            "comparison_operator": operator,
                            "value": node.get("value"),
                        },
                    )
                )

                # Array operators should not affect the OpenSearch query at all
                # They are purely post-processing filters
                # Store the original node info in the post-processing requirement
                if post_processing_reqs and post_processing_reqs[-1].metadata is not None:
                    post_processing_reqs[-1].metadata["original_node"] = {
                        "type": "comparison",
                        "field": field_name,
                        "operator": operator,
                        "value": node.get("value"),
                        "field_mutators": [{"name": array_operator}],
                    }

                # Array operators should be completely removed from the OpenSearch query
                # Mark this node for removal
                node["_remove_from_query"] = True

                # Don't mark the node for post-processing - let the query be generated normally
                # The array operator is applied as a post-processing filter on top of the results

                optimizations.append(
                    f"Array operator '{array_operator}' with '{operator}' will be applied in post-processing"
                )

                # Skip the regular mutator processing that follows
                return

            else:
                # Regular mutator processing
                result = self._analyze_field_mutators(field_name, field_mutators, operator)

                # For in-memory context, keep mutators in AST for evaluation
                if self.context == "in_memory":
                    # Don't remove mutators from AST for in-memory queries
                    # They need to be applied during evaluation
                    pass
                else:
                    # Update node with optimized mutators for OpenSearch context
                    if result.optimized_mutators != field_mutators:
                        if result.optimized_mutators:
                            node["field_mutators"] = result.optimized_mutators
                        else:
                            # Remove field_mutators if all were optimized away
                            node.pop("field_mutators", None)

                        optimizations.extend(result.optimizations)

                # Add post-processing requirements
                if result.post_processing_mutators:
                    # For in-memory context, we need special handling
                    if self.context == "in_memory":
                        # Check if any mutators are transform mutators that need to be applied to results
                        transform_mutators = []
                        for mutator in result.post_processing_mutators:
                            mutator_name = mutator.get("name", "").lower()
                            # Transform mutators that modify the result
                            if mutator_name in [
                                "split",
                                "lowercase",
                                "uppercase",
                                "trim",
                                "replace",
                                "refang",
                                "defang",
                            ]:
                                transform_mutators.append(mutator)

                        # If we have transform mutators, add them as post-processing for result transformation
                        if transform_mutators:
                            post_processing_reqs.append(
                                PostProcessingRequirement(
                                    field_name=field_name,
                                    mapped_field_name=field_name,
                                    mutators=transform_mutators,
                                    applies_to="field",
                                    metadata={"transform_only": True},  # Mark as transform-only
                                )
                            )
                    else:
                        # Always include operator and value in metadata for post-processing filtering
                        metadata = {"operator": operator, "value": node.get("value")}
                        # Include original comparison info if it exists
                        if node.get("_original_comparison"):
                            metadata["_original_comparison"] = node["_original_comparison"]

                        post_processing_reqs.append(
                            PostProcessingRequirement(
                                field_name=field_name,
                                mapped_field_name=result.selected_field or field_name,
                                mutators=result.post_processing_mutators,
                                applies_to="field",
                                metadata=metadata,
                            )
                        )

                    # Check if we have transform mutators with filtering operators
                    # These need special handling in query conversion
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

                    has_transform_with_filter = False
                    for mutator in result.post_processing_mutators:
                        if mutator.get("name", "").lower() in TRANSFORM_MUTATORS:
                            has_transform_with_filter = True
                            break

                    if has_transform_with_filter and operator in [
                        "eq",
                        "=",
                        "ne",
                        "!=",
                        "contains",
                        "not_contains",
                        "startswith",
                        "endswith",
                        "not_startswith",
                        "not_endswith",
                        ">",
                        ">=",
                        "<",
                        "<=",
                        "gt",
                        "gte",
                        "lt",
                        "lte",
                        "between",
                        "not_between",
                    ]:
                        # Mark the node so query converter knows to use exists query
                        node["has_transform_mutators_with_filter"] = True

                # Check if any mutators change the field type
                has_type_changing_mutator = any(
                    mutator.get("name", "").lower()
                    in ["length", "avg", "average", "sum", "max", "min", "any", "all", "is_private", "is_global"]
                    for mutator in result.post_processing_mutators
                )

                # For field mutators on certain operations, we need to make the query less restrictive
                # This allows post-processing to correctly filter results
                if operator in [
                    "eq",
                    "=",
                    "ne",
                    "!=",
                    "contains",
                    "not_contains",
                    "startswith",
                    "endswith",
                    "not_startswith",
                    "not_endswith",
                ]:
                    # Mark the node to indicate it needs special handling in OpenSearch
                    node["post_process_value"] = True
                    # Keep the original value for reference
                    node["original_value"] = node.get("value")
                    # Also mark if we have type-changing mutators
                    if has_type_changing_mutator:
                        node["has_type_changing_mutators"] = True

                        # For in-memory queries with type-changing mutators, DON'T convert to exists check
                        # The mutators should be applied during evaluation
                        if self.context == "in_memory":
                            # Keep the original comparison intact for in-memory evaluation
                            pass
                elif has_type_changing_mutator:
                    # For type-changing mutators with numeric operators, mark for special handling
                    node["has_type_changing_mutators"] = True

            # Add health reasons
            health_reasons.extend(result.health_reasons)

            # Update field name if optimized
            if result.selected_field and result.selected_field != field_name:
                node["field"] = result.selected_field

        # Note: ALL and NOT_ALL operators are handled during evaluation, not post-processing

        # Value mutators are handled during evaluation, not post-processing
        # The evaluator's _evaluate_comparison method applies value mutators before comparison
        # So we don't need to treat them as post-processing requirements

    def _analyze_collection_node(
        self,
        node: Dict[str, Any],
        post_processing_reqs: List[PostProcessingRequirement],
        health_reasons: List[Dict[str, str]],
        optimizations: List[str],
    ) -> None:
        """Analyze a collection operation node for mutator processing.

        Args:
            node: Collection operation AST node
            post_processing_reqs: List to append post-processing requirements
            health_reasons: List to append health issues
            optimizations: List to append optimization descriptions
        """
        field_name = node.get("field")
        field_mutators = node.get("field_mutators", [])

        if not field_name:
            return

        # For collection operations, handle mutators similar to comparison nodes
        # but be more conservative about optimizations

        if field_mutators:
            # For collection ops, we're more conservative - most field mutators go to post-processing
            post_processing_field_mutators = []

            for mutator in field_mutators:
                mutator_name = mutator.get("name", "").lower()
                classification = MUTATOR_CLASSIFICATIONS.get(mutator_name, MutatorType.POST_PROCESSABLE)

                # For collection operations, be conservative and post-process most mutators
                if classification != MutatorType.PRE_PROCESSABLE:
                    post_processing_field_mutators.append(mutator)

            if post_processing_field_mutators:
                post_processing_reqs.append(
                    PostProcessingRequirement(
                        field_name=field_name,
                        mapped_field_name=field_name,
                        mutators=post_processing_field_mutators,
                        applies_to="field",
                    )
                )

                # Remove field mutators from AST
                node.pop("field_mutators", None)
                optimizations.append(
                    f"Moved {len(post_processing_field_mutators)} field mutator(s) to "
                    f"post-processing for collection operation"
                )

        # Value mutators are handled during evaluation for collection operations too
        # The evaluator applies them before comparison in _evaluate_collection_comparison

    def _evaluate_health_for_context(  # noqa: C901
        self,
        post_processing_requirements: List[PostProcessingRequirement],
        context: str,
        ast: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Evaluate health status based on context and mutator performance characteristics.

        Args:
            post_processing_requirements: List of post-processing requirements
            context: Execution context ("opensearch" or "in_memory")

        Returns:
            Dictionary with health_status and health_reasons
        """
        fast_count = 0
        moderate_count = 0
        slow_count = 0
        slow_mutators = []
        all_mutators = []

        # Helper function to process mutators
        def process_mutators(mutator_list):
            nonlocal fast_count, moderate_count, slow_count
            for mutator_spec in mutator_list:
                mutator_name = mutator_spec.get("name", "")
                all_mutators.append(mutator_name)

                try:
                    # Create mutator instance to get its performance characteristics
                    mutator = create_mutator(mutator_name, mutator_spec.get("params"))
                    perf_class = mutator.get_performance_class(context)

                    if perf_class == PerformanceClass.FAST:
                        fast_count += 1
                    elif perf_class == PerformanceClass.MODERATE:
                        moderate_count += 1
                    elif perf_class == PerformanceClass.SLOW:
                        slow_count += 1
                        slow_mutators.append(mutator_name)
                except Exception:
                    # If we can't create the mutator, assume moderate performance
                    moderate_count += 1

        # Collect all mutators from post-processing requirements
        for req in post_processing_requirements:
            process_mutators(req.mutators)

        # For in_memory context with AST, also collect mutators from the AST
        if context == "in_memory" and ast:

            def collect_ast_mutators(node):
                if isinstance(node, dict):
                    # Check for field mutators
                    if "field_mutators" in node:
                        process_mutators(node["field_mutators"])
                    # Check for value mutators
                    if "value_mutators" in node:
                        process_mutators(node["value_mutators"])
                    # Recurse into child nodes
                    for key, value in node.items():
                        if key in ["left", "right", "operand"]:
                            collect_ast_mutators(value)

            collect_ast_mutators(ast)

        # Determine health status based on context
        health_status = "green"
        health_reasons = []

        if context == "in_memory":
            # In-memory context: only slow mutators significantly impact health
            if slow_count > 0:
                health_status = "yellow"
                if slow_count > 2:
                    health_status = "red"
                health_reasons.append(
                    {
                        "status": health_status,
                        "query_part": f"mutators: {', '.join(slow_mutators)}",
                        "reason": f"{slow_count} slow mutator(s) ({', '.join(slow_mutators)}) may impact performance",
                    }
                )
            elif moderate_count > 5:
                # Many moderate mutators can also impact performance
                health_status = "yellow"
                health_reasons.append(
                    {
                        "status": "yellow",
                        "query_part": "multiple mutators",
                        "reason": f"{moderate_count} moderate-performance mutators may impact "
                        f"performance when combined",
                    }
                )
            # Fast mutators don't impact health in memory context

        elif context == "opensearch":
            # OpenSearch context: post-processing always impacts performance
            if slow_count > 0 or moderate_count > 0 or fast_count > 0:
                health_status = "yellow"
                if slow_count > 0:
                    health_status = "red" if slow_count > 1 else "yellow"

                reason_parts = []
                if fast_count > 0:
                    reason_parts.append(f"{fast_count} mutator(s)")
                if moderate_count > 0:
                    reason_parts.append(f"{moderate_count} moderate mutator(s)")
                if slow_count > 0:
                    reason_parts.append(f"{slow_count} slow mutator(s) [{', '.join(slow_mutators)}]")

                health_reasons.append(
                    {
                        "status": health_status,
                        "query_part": "post-processing required",
                        "reason": (
                            f"Post-processing required for {' + '.join(reason_parts)}, "
                            "which impacts performance with large result sets"
                        ),
                    }
                )

        return {"health_status": health_status, "health_reasons": health_reasons}

    def _analyze_field_mutators(
        self, field_name: str, mutators: List[Dict[str, Any]], operator: str
    ) -> "FieldMutatorAnalysisResult":
        """Analyze field mutators for a specific field."""
        analyzer = FieldMutatorAnalyzer(self.intelligent_mappings)
        return analyzer.analyze(field_name, mutators, operator)


@dataclass
class FieldMutatorAnalysisResult:
    """Result of analyzing field mutators for a specific field."""

    optimized_mutators: List[Dict[str, Any]]  # Mutators that remain in AST
    post_processing_mutators: List[Dict[str, Any]]  # Mutators for post-processing
    selected_field: Optional[str]  # Field name to use in OpenSearch query
    optimizations: List[str]  # Descriptions of optimizations applied
    health_reasons: List[Dict[str, str]]  # Health issues found


class FieldMutatorAnalyzer:
    """Analyzes field mutators for a specific field."""

    def __init__(self, field_mappings: Dict[str, FieldMapping]):
        """Initialize with intelligent field mappings."""
        self.field_mappings = field_mappings

    def analyze(self, field_name: str, mutators: List[Dict[str, Any]], operator: str) -> FieldMutatorAnalysisResult:
        """Analyze field mutators for optimization opportunities.

        Args:
            field_name: Name of the field
            mutators: List of mutator specifications
            operator: The operator being used in the comparison

        Returns:
            Analysis result with optimization recommendations
        """
        optimized_mutators: List[Dict[str, Any]] = []
        post_processing_mutators = []
        selected_field = None
        optimizations = []
        health_reasons = []

        # Check if we have intelligent mapping for this field
        if field_name in self.field_mappings:
            field_mapping = self.field_mappings[field_name]

            # Try to optimize mutators using field mapping
            for mutator in mutators:
                mutator_name = mutator.get("name", "").lower()

                if mutator_name == "lowercase":
                    optimization_result = self._optimize_lowercase_mutator(field_mapping, operator, mutator)
                elif mutator_name == "uppercase":
                    optimization_result = self._optimize_uppercase_mutator(field_mapping, operator, mutator)
                elif mutator_name == "trim":
                    optimization_result = self._optimize_trim_mutator(field_mapping, operator, mutator)
                else:
                    # Unknown or non-optimizable mutator - goes to post-processing
                    optimization_result = MutatorOptimizationResult(
                        can_optimize=False,
                        selected_field=None,
                        post_process_mutator=mutator,
                        optimization_description=f"Mutator '{mutator_name}' requires post-processing",
                    )

                # Apply optimization result
                if optimization_result.can_optimize:
                    if optimization_result.selected_field:
                        selected_field = optimization_result.selected_field
                    optimizations.append(optimization_result.optimization_description)
                    # Don't add to optimized_mutators if fully optimized
                else:
                    if optimization_result.post_process_mutator:
                        post_processing_mutators.append(optimization_result.post_process_mutator)
                    if optimization_result.health_issue:
                        health_reasons.append(optimization_result.health_issue)
        else:
            # No intelligent mapping - all mutators go to post-processing
            post_processing_mutators = mutators
            optimizations.append(f"No field mapping for '{field_name}' - all mutators require post-processing")

        return FieldMutatorAnalysisResult(
            optimized_mutators=optimized_mutators,
            post_processing_mutators=post_processing_mutators,
            selected_field=selected_field,
            optimizations=optimizations,
            health_reasons=health_reasons,
        )

    def _optimize_lowercase_mutator(
        self, field_mapping: FieldMapping, operator: str, mutator: Dict[str, Any]
    ) -> "MutatorOptimizationResult":
        """Try to optimize a lowercase mutator using field mappings."""
        # Per requirement: lowercase should always be post-processing
        # Even if we have a lowercase analyzer field, we don't optimize
        return MutatorOptimizationResult(
            can_optimize=False,
            selected_field=None,
            post_process_mutator=mutator,
            optimization_description="Lowercase mutator always requires post-processing",
        )

    def _optimize_uppercase_mutator(
        self, field_mapping: FieldMapping, operator: str, mutator: Dict[str, Any]
    ) -> "MutatorOptimizationResult":
        """Try to optimize an uppercase mutator using field mappings."""
        # We need to check the text_fields dict directly to ensure we have the specific analyzer
        if "uppercase" in field_mapping.text_fields:
            uppercase_field = field_mapping.text_fields["uppercase"]
            return MutatorOptimizationResult(
                can_optimize=True,
                selected_field=uppercase_field,
                post_process_mutator=None,
                optimization_description=f"Using field '{uppercase_field}' with uppercase analyzer instead of mutator",
            )
        else:
            # No uppercase analyzer - requires post-processing
            return MutatorOptimizationResult(
                can_optimize=False,
                selected_field=None,
                post_process_mutator=mutator,
                optimization_description="No uppercase analyzer available - requires post-processing",
            )

    def _optimize_trim_mutator(
        self, field_mapping: FieldMapping, operator: str, mutator: Dict[str, Any]
    ) -> "MutatorOptimizationResult":
        """Try to optimize a trim mutator using field mappings."""
        # Trim should always require post-processing to ensure consistent behavior
        # We can't reliably know if an analyzer trims whitespace
        return MutatorOptimizationResult(
            can_optimize=False,
            selected_field=None,
            post_process_mutator=mutator,
            optimization_description="Trim mutator always requires post-processing",
        )


@dataclass
class MutatorOptimizationResult:
    """Result of attempting to optimize a single mutator."""

    can_optimize: bool  # Whether mutator can be optimized away
    selected_field: Optional[str]  # Field to use in OpenSearch query
    post_process_mutator: Optional[Dict[str, Any]]  # Mutator for post-processing (if needed)
    optimization_description: str  # Description of what was done
    health_issue: Optional[Dict[str, str]] = None  # Health issue if any


# Monkey patch the analyzer into MutatorAnalyzer
# Method moved into class
