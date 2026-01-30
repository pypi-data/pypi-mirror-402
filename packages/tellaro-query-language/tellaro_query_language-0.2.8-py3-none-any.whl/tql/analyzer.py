"""
Analyzer information and mutator optimization for TQL.

This module provides support for OpenSearch analyzer information in field mappings
and intelligent optimization of mutator chains based on analyzer capabilities.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union


class AnalyzerInfo:
    """Represents OpenSearch analyzer configuration."""

    def __init__(self, analyzer_config: Union[str, Dict[str, Any]]):
        """Initialize analyzer info from configuration.

        Args:
            analyzer_config: Either a string analyzer name (e.g., "standard", "english")
                           or a dictionary containing analyzer configuration:
                {
                    "tokenizer": {
                        "type": "pattern|standard|keyword|whitespace",
                        "pattern": "regex_pattern"  # For pattern tokenizer
                    },
                    "filters": ["lowercase", "uppercase", "stop", "trim", ...]
                }
        """
        if isinstance(analyzer_config, str):
            # Handle built-in analyzer names
            self.tokenizer, self.filters = self._get_builtin_analyzer_config(analyzer_config)
        else:
            # Handle full analyzer configuration dictionary
            self.tokenizer = analyzer_config.get("tokenizer", {})
            self.filters = analyzer_config.get("filters", [])

        # Normalize filter representations
        self.normalized_filters = set()
        for filter_def in self.filters:
            if isinstance(filter_def, str):
                self.normalized_filters.add(filter_def)
            elif isinstance(filter_def, dict):
                filter_type = filter_def.get("type", "")
                self.normalized_filters.add(filter_type)

    def _get_builtin_analyzer_config(self, analyzer_name: str) -> Tuple[Dict[str, Any], List[str]]:
        """Get configuration for built-in OpenSearch/Elasticsearch analyzers.

        Args:
            analyzer_name: Name of the built-in analyzer

        Returns:
            Tuple of (tokenizer_config, filters_list)
        """
        # Define common built-in analyzer configurations
        builtin_configs = {
            "standard": ({"type": "standard"}, ["lowercase"]),
            "english": ({"type": "standard"}, ["lowercase", "stop", "stemmer"]),
            "keyword": ({"type": "keyword"}, []),
            "whitespace": ({"type": "whitespace"}, []),
            "simple": ({"type": "lowercase"}, []),
            "stop": ({"type": "lowercase"}, ["stop"]),
            "pattern": ({"type": "pattern", "pattern": "\\W+"}, ["lowercase"]),
            # Add more analyzers as needed
            "autocomplete": ({"type": "edge_ngram"}, ["lowercase"]),
            "search_time_analyzer": ({"type": "standard"}, ["lowercase", "stop"]),
            "ngram": ({"type": "ngram"}, ["lowercase"]),
            "edge_ngram": ({"type": "edge_ngram"}, ["lowercase"]),
            "shingle": ({"type": "standard"}, ["lowercase", "shingle"]),
            "french": ({"type": "standard"}, ["lowercase", "stop", "french_stemmer"]),
        }

        if analyzer_name in builtin_configs:
            tokenizer_config, filters = builtin_configs[analyzer_name]
            return tokenizer_config, filters
        # Default fallback for unknown analyzers
        return {"type": "standard"}, ["lowercase"]

    def can_handle_split(self, delimiter: str) -> bool:
        """Check if the tokenizer can handle splitting on the given delimiter.

        Args:
            delimiter: The delimiter to check (e.g., ' ', ',', etc.)

        Returns:
            True if the tokenizer handles this split operation
        """
        tokenizer_type = self.tokenizer.get("type", "")

        if tokenizer_type == "whitespace" and delimiter.strip() == "":
            return True
        elif tokenizer_type == "standard" and delimiter in [" ", "\t", "\n"]:
            return True
        elif tokenizer_type == "pattern":
            pattern = self.tokenizer.get("pattern", "")
            if pattern:
                try:
                    # Check if the pattern would split on this delimiter
                    test_text = f"word{delimiter}another"
                    parts = re.split(pattern, test_text)
                    return len(parts) > 1 and parts[0] == "word" and parts[-1] == "another"
                except re.error:
                    return False

        return False

    def has_filter(self, filter_name: str) -> bool:
        """Check if the analyzer has a specific filter.

        Args:
            filter_name: Name of the filter to check

        Returns:
            True if the filter is present
        """
        return filter_name in self.normalized_filters

    def get_optimization_score(self, mutators: List[Dict[str, Any]]) -> int:
        """Calculate how many mutators this analyzer can optimize away.

        Args:
            mutators: List of mutator configurations

        Returns:
            Number of mutators that can be optimized away
        """
        score = 0

        for mutator in mutators:
            mutator_name = mutator.get("name", "").lower()

            # Check text transformation filters
            if mutator_name == "lowercase" and self.has_filter("lowercase"):
                score += 1
            elif mutator_name == "uppercase" and self.has_filter("uppercase"):
                score += 1
            elif mutator_name == "trim" and self.has_filter("trim"):
                score += 1

            # Check split operations
            elif mutator_name == "split":
                params = mutator.get("params", [])
                if params and len(params) > 0:
                    # First parameter should be the delimiter
                    delimiter_param = params[0]
                    if isinstance(delimiter_param, list) and len(delimiter_param) == 2:
                        param_key, delimiter = delimiter_param  # [key, value] format
                        if param_key == "delimiter" and self.can_handle_split(delimiter):
                            score += 1

        return score


class MutatorOptimizer:
    """Optimizes mutator chains based on field analyzer information."""

    @staticmethod
    def find_best_field_variant(
        field_name: str, mutators: List[Dict[str, Any]], field_mapping: Dict[str, Any]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Find the best field variant and optimized mutator chain.

        Args:
            field_name: The base field name
            mutators: List of mutator configurations
            field_mapping: Enhanced field mapping with analyzer info

        Returns:
            Tuple of (best_field_name, remaining_mutators)
        """
        if field_name not in field_mapping:
            # No mapping info, return original
            return field_name, mutators

        mapping_info = field_mapping[field_name]
        if not isinstance(mapping_info, dict):
            # Simple mapping, no optimization possible
            return field_name, mutators

        best_field = field_name
        best_score = 0
        best_remaining_mutators = mutators

        # Check each field variant in the mapping
        for variant_name, variant_config in mapping_info.items():
            if variant_name == "analyzer":
                continue  # Skip meta fields

            if isinstance(variant_config, dict) and "analyzer" in variant_config:
                analyzer_info = AnalyzerInfo(variant_config["analyzer"])
                score = analyzer_info.get_optimization_score(mutators)

                if score > best_score:
                    best_field = variant_name
                    best_score = score
                    best_remaining_mutators = MutatorOptimizer._remove_optimized_mutators(mutators, analyzer_info)

        return best_field, best_remaining_mutators

    @staticmethod
    def _remove_optimized_mutators(mutators: List[Dict[str, Any]], analyzer_info: AnalyzerInfo) -> List[Dict[str, Any]]:
        """Remove mutators that are handled by the analyzer.

        Args:
            mutators: Original mutator list
            analyzer_info: Analyzer configuration

        Returns:
            List of remaining mutators
        """
        remaining = []

        for mutator in mutators:
            mutator_name = mutator.get("name", "").lower()
            should_keep = True

            # Check if this mutator is handled by the analyzer
            if mutator_name == "lowercase" and analyzer_info.has_filter("lowercase"):
                should_keep = False
            elif mutator_name == "uppercase" and analyzer_info.has_filter("uppercase"):
                should_keep = False
            elif mutator_name == "trim" and analyzer_info.has_filter("trim"):
                should_keep = False
            elif mutator_name == "split":
                # Check if split operation is handled by tokenizer
                params = mutator.get("params", [])
                if params and len(params) > 0:
                    delimiter_param = params[0]
                    if isinstance(delimiter_param, list) and len(delimiter_param) == 2:
                        param_key, delimiter = delimiter_param
                        if param_key == "delimiter" and analyzer_info.can_handle_split(delimiter):
                            should_keep = False

            if should_keep:
                remaining.append(mutator)

        return remaining

    @staticmethod
    def optimize_query_ast(ast: Dict[str, Any], field_mappings: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
        """Optimize a TQL query AST by optimizing mutator chains.

        Args:
            ast: The TQL query AST
            field_mappings: Enhanced field mappings with analyzer info

        Returns:
            Optimized AST
        """
        if not isinstance(ast, dict):
            return ast

        ast_type = ast.get("type")

        if ast_type == "comparison":
            # Optimize field mutators in comparison operations
            field_mutators = ast.get("field_mutators", [])
            if field_mutators and ast.get("field") in field_mappings:
                optimized_field, remaining_mutators = MutatorOptimizer.find_best_field_variant(
                    ast["field"], field_mutators, field_mappings
                )

                # Update the AST with optimized field and mutators
                optimized_ast = ast.copy()
                optimized_ast["field"] = optimized_field
                if remaining_mutators:
                    optimized_ast["field_mutators"] = remaining_mutators
                else:
                    optimized_ast.pop("field_mutators", None)

                return optimized_ast

        elif ast_type == "logical_op":
            # Recursively optimize logical operations
            return {
                **ast,
                "left": MutatorOptimizer.optimize_query_ast(ast["left"], field_mappings),
                "right": MutatorOptimizer.optimize_query_ast(ast["right"], field_mappings),
            }

        elif ast_type == "unary_op":
            # Recursively optimize unary operations
            return {**ast, "operand": MutatorOptimizer.optimize_query_ast(ast["operand"], field_mappings)}

        elif ast_type == "geo_expr":
            # Recursively optimize geo expressions
            return {**ast, "conditions": MutatorOptimizer.optimize_query_ast(ast["conditions"], field_mappings)}

        elif ast_type == "collection_op":
            # Collection operations can also have field mutators
            field_mutators = ast.get("field_mutators", [])
            if field_mutators and ast.get("field") in field_mappings:
                optimized_field, remaining_mutators = MutatorOptimizer.find_best_field_variant(
                    ast["field"], field_mutators, field_mappings
                )

                optimized_ast = ast.copy()
                optimized_ast["field"] = optimized_field
                if remaining_mutators:
                    optimized_ast["field_mutators"] = remaining_mutators
                else:
                    optimized_ast.pop("field_mutators", None)

                return optimized_ast

        return ast


class EnhancedFieldMapping:
    """Enhanced field mapping that supports analyzer information."""

    def __init__(self, mapping_info: Dict[str, Any]):
        """Initialize enhanced field mapping.

        Args:
            mapping_info: Dictionary containing field mapping information.
                         Supports enhanced format with analyzer info:
                         {
                             "name": {
                                 "name": "keyword",
                                 "name.text": {
                                     "type": "text",
                                     "analyzer": {
                                         "tokenizer": {"type": "whitespace"},
                                         "filters": ["lowercase"]
                                     }
                                 }
                             }
                         }
        """
        self.raw_mapping = mapping_info
        self.field_variants: Dict[str, Dict[str, Any]] = {}  # field_name -> {variant_name -> variant_info}
        self.analyzer_info: Dict[str, AnalyzerInfo] = {}  # field_name -> AnalyzerInfo

        self._parse_mapping(mapping_info)

    def _parse_mapping(self, mapping_info: Dict[str, Any]):
        """Parse the mapping information and extract analyzer details."""
        for field_name, field_config in mapping_info.items():
            if isinstance(field_config, dict):
                self.field_variants[field_name] = {}

                for variant_name, variant_config in field_config.items():
                    if variant_name == "analyzer":
                        continue  # Skip analyzer meta-info

                    self.field_variants[field_name][variant_name] = variant_config

                    # Extract analyzer information if present
                    if isinstance(variant_config, dict) and "analyzer" in variant_config:
                        analyzer_key = f"{field_name}.{variant_name}"
                        self.analyzer_info[analyzer_key] = AnalyzerInfo(variant_config["analyzer"])
            else:
                # Simple mapping format - create basic field variant
                self.field_variants[field_name] = {field_name: field_config}

    def get_field_variants(self, field_name: str) -> Dict[str, Any]:
        """Get all variants for a field.

        Args:
            field_name: The field name

        Returns:
            Dictionary of variant_name -> variant_config
        """
        return self.field_variants.get(field_name, {field_name: "keyword"})

    def get_analyzer_info(self, field_path: str) -> Optional[AnalyzerInfo]:
        """Get analyzer information for a field path.

        Args:
            field_path: Full field path (e.g., "name.text")

        Returns:
            AnalyzerInfo if available, None otherwise
        """
        return self.analyzer_info.get(field_path)

    def is_enhanced_mapping(self) -> bool:
        """Check if this mapping contains analyzer information.

        Returns:
            True if any field has analyzer info
        """
        return len(self.analyzer_info) > 0
