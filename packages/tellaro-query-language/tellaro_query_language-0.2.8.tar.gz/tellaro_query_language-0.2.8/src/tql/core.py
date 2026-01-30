"""Core TQL implementation.

This module provides the main TQL class that serves as the primary interface
for parsing and executing TQL queries against different backends.
"""

from typing import Any, Dict, Generator, List, Optional, Union

from .analyzer import EnhancedFieldMapping
from .core_components import FileOperations, OpenSearchOperations, StatsOperations, ValidationOperations
from .evaluator import TQLEvaluator
from .exceptions import (
    TQLExecutionError,
    TQLOperatorError,
    TQLParseError,
    TQLSyntaxError,
    TQLTypeError,
    TQLValidationError,
)
from .mutator_analyzer import MutatorAnalysisResult
from .parser import TQLParser
from .stats_evaluator import TQLStatsEvaluator


class TQL:
    """Main TQL query interface.

    This class provides the primary interface for parsing TQL queries and executing
    them against various backends including direct file operations and OpenSearch.

    Example:
        >>> tql = TQL()
        >>> query = "name eq 'John' AND age > 25"
        >>> results = tql.query(data, query)
    """

    def __init__(self, field_mappings: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None):  # noqa: C901
        """Initialize TQL instance.

        Args:
            field_mappings: Optional mapping of TQL field names to backend field names.
                          Supports multiple formats:

                          1. Simple: {"field": "keyword"}

                          2. Complex: {"field": {"field": "keyword", "field.text": "text"}}

                          3. Enhanced with analyzer info:
                          {
                              "field": {
                                  "field": "keyword",
                                  "field.text": {
                                      "type": "text",
                                      "analyzer": {
                                          "tokenizer": {"type": "whitespace"},
                                          "filters": ["lowercase"]
                                      }
                                  }
                              }
                          }
        """
        self.parser = TQLParser()
        self.evaluator = TQLEvaluator()
        self.stats_evaluator = TQLStatsEvaluator()
        self.field_mappings = field_mappings or {}

        # Create enhanced field mappings for optimization
        self.enhanced_mappings = {}
        if self.field_mappings:
            for field_name, field_config in self.field_mappings.items():
                self.enhanced_mappings[field_name] = EnhancedFieldMapping({field_name: field_config})

        # Check if any mappings have analyzer information
        self.has_analyzer_info = any(mapping.is_enhanced_mapping() for mapping in self.enhanced_mappings.values())

        # Extract simple mappings for evaluator
        # For complex mappings (dict), use the first key as the simple mapping
        self._simple_mappings = {}
        for k, v in self.field_mappings.items():
            if isinstance(v, str):
                # Check if this looks like a type specification (common OpenSearch types)
                if v in [
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
                    # This is a type specification, not a field mapping
                    # Map the field to itself
                    self._simple_mappings[k] = k
                else:
                    # This is a field name mapping
                    self._simple_mappings[k] = v
            elif isinstance(v, dict) and v:
                # Check if this is a type specification dict
                if "type" in v and len(v) == 1:
                    # This is just a type specification, map field to itself
                    self._simple_mappings[k] = k
                elif "type" in v and "fields" in v:
                    # This is an OpenSearch-style mapping, map field to itself
                    self._simple_mappings[k] = k
                else:
                    # Intelligent field mapping extraction for complex mappings
                    # Priority: 1) Key matching field name, 2) Key without dots (primary field), 3) First key

                    if k in v:
                        # Field name exists as key in mapping (e.g., {"username": {"username": "keyword", ...}})
                        self._simple_mappings[k] = k
                    else:
                        # Find primary field (keys without dots, not starting with underscore)
                        primary_fields = [
                            field_key
                            for field_key in v.keys()
                            if "." not in field_key and not field_key.startswith("_")
                        ]

                        if primary_fields:
                            # Use first primary field
                            self._simple_mappings[k] = primary_fields[0]
                        else:
                            # Fallback to first key (maintain backward compatibility)
                            self._simple_mappings[k] = next(iter(v.keys()))
            else:
                # Default to mapping field to itself
                self._simple_mappings[k] = k

        # Simple mappings will be passed to evaluator methods as needed

        # Initialize component operations
        self.opensearch_ops = OpenSearchOperations(self.parser, self.field_mappings, self.enhanced_mappings)
        self.file_ops = FileOperations()
        self.stats_ops = StatsOperations(self.parser, self._simple_mappings)
        self.validation_ops = ValidationOperations(self.parser, self.field_mappings)

    def parse(self, query: str) -> Dict[str, Any]:
        """Parse a TQL query string into an AST.

        Args:
            query: TQL query string

        Returns:
            Abstract Syntax Tree (AST) representation

        Raises:
            TQLParseError: If the query has invalid syntax
        """
        return self.parser.parse(query)

    def validate(self, query: str, validate_fields: bool = False) -> bool:
        """Validate a TQL query for syntax and optionally field names.

        Args:
            query: TQL query string
            validate_fields: Whether to validate field names against mappings

        Returns:
            True if query is valid, False if syntax errors

        Raises:
            TQLFieldError: If field validation fails
            TQLValidationError: If type validation fails
        """
        try:
            return self.validation_ops.validate(query, validate_fields)
        except TQLSyntaxError:
            # Syntax errors mean invalid query
            return False

    def _ast_to_query_string(self, ast: Dict[str, Any]) -> str:
        """Convert AST back to query string for display purposes."""
        if ast.get("type") == "comparison":
            field = ast.get("field", "")
            op = ast.get("operator", "")
            value = ast.get("value", "")
            if isinstance(value, str):
                value = f'"{value}"'
            return f"{field} {op} {value}"
        elif ast.get("type") == "logical_op":
            left = self._ast_to_query_string(ast.get("left", {}))
            right = self._ast_to_query_string(ast.get("right", {}))
            op = ast.get("operator", "").upper()
            return f"({left} {op} {right})"
        elif ast.get("type") == "unary_op":
            operand = self._ast_to_query_string(ast.get("operand", {}))
            return f"NOT {operand}"
        return str(ast)

    def query(  # noqa: C901
        self, data: Union[List[Dict], str], query: str, size: int = 10, save_enrichment: bool = False
    ) -> Dict[str, Any]:  # noqa: C901
        """Execute a TQL query against data and return results in execute_opensearch format.

        Args:
            data: List of dictionaries or path to JSON/CSV file
            query: TQL query string (can be filter query, stats query, or combined)
            size: Number of documents to return (0 for stats-only queries)
            save_enrichment: If True and mutators add enrichment fields, save back to source

        Returns:
            Dictionary containing:
            - results: List of matching records (if size > 0 and no stats)
            - stats: Stats results (if query contains stats)
            - total: Total number of matching documents
            - post_processing_applied: Whether post-processing was applied
            - health_status: Query health status
            - health_reasons: List of health issues

        Raises:
            TQLParseError: If query parsing fails
            TQLExecutionError: If query execution fails
        """
        # Parse the query
        ast = self.parse(query)

        # Check query type
        query_type = ast.get("type")

        # Load data if it's a file path
        if isinstance(data, str):
            records = self.file_ops.load_file(data)
            source_file = data
        else:
            records = data
            source_file = None

        # Initialize result structure
        result = {"total": 0, "post_processing_applied": False, "health_status": "green", "health_reasons": []}

        # Handle stats queries
        if query_type == "stats_expr":
            # This is a pure stats query like "| stats count()"
            stats_result = self.stats(data, query)
            # Get viz_hint from the parsed AST
            viz_hint = ast.get("viz_hint")
            # Convert to execute_opensearch format
            result["stats"] = self._convert_stats_result(stats_result, viz_hint)
            result["total"] = len(records)
            return result

        elif query_type == "query_with_stats":
            # This is a combined query like "status = 'active' | stats count()"
            # First filter the data
            parsed = self.parse(query)
            filter_ast = parsed["filter"]
            stats_ast = parsed["stats"]

            # Apply filter
            filtered_records = []
            for record in records:
                if self.evaluator._evaluate_node(filter_ast, record, self._simple_mappings):
                    filtered_records.append(record)

            # Apply stats to filtered data
            stats_result = self.stats_evaluator.evaluate_stats(filtered_records, stats_ast)
            # Get viz_hint from the stats AST
            viz_hint = stats_ast.get("viz_hint")
            result["stats"] = self._convert_stats_result(stats_result, viz_hint)
            result["total"] = len(filtered_records)

            # Include filtered documents if size > 0
            if size > 0:
                result["results"] = filtered_records[:size]

            return result

        # Handle regular filter queries with mutator analysis
        # Analyze the query for mutators
        from .mutator_analyzer import MutatorAnalyzer
        from .post_processor import QueryPostProcessor

        analyzer = MutatorAnalyzer(field_mappings=self.field_mappings)
        analysis_result = analyzer.analyze_ast(ast, context="in_memory")

        # Use the optimized AST for evaluation
        optimized_ast = analysis_result.optimized_ast

        # First pass: collect all matching records using optimized AST
        matched_records = []
        for record in records:
            # Check if record matches using the optimized AST (without array operators)
            if self.evaluator._evaluate_node(optimized_ast, record, self._simple_mappings):
                matched_records.append(record)

        # Apply post-processing if needed
        if analysis_result.post_processing_requirements:
            processor = QueryPostProcessor()

            # Apply mutators/enrichments
            processed_records = processor.process_results(
                matched_records, analysis_result.post_processing_requirements, track_enrichments=save_enrichment
            )

            # Apply filters (for array operators like any/all/none)
            filtered_records = processor.filter_results(processed_records, analysis_result.post_processing_requirements)

            matched_records = filtered_records
            result["post_processing_applied"] = True

            # Add post-processing stats
            result["post_processing_stats"] = {
                "documents_retrieved": len(processed_records),
                "documents_returned": len(filtered_records),
                "documents_filtered": len(processed_records) - len(filtered_records),
            }

        # Set result data
        result["total"] = len(matched_records)
        if size > 0:
            result["results"] = matched_records[:size]

        # Update health status based on analysis
        result["health_status"] = analysis_result.health_status
        result["health_reasons"] = [
            reason.get("reason", reason.get("description", "")) for reason in analysis_result.health_reasons
        ]

        # Save enrichments if requested
        if save_enrichment and result.get("post_processing_applied") and source_file:
            # For file sources, we would need to re-process all records with enrichments
            # This is a complex operation that would require applying mutators to all records
            # For now, we'll skip this functionality in the in-memory implementation
            pass

        return result

    def query_single(self, record: Dict[str, Any], query: str) -> bool:
        """Check if a single record matches a TQL query.

        Args:
            record: Dictionary to test
            query: TQL query string

        Returns:
            True if record matches the query

        Raises:
            TQLParseError: If query parsing fails
        """
        ast = self.parse(query)
        return self.evaluator._evaluate_node(ast, record, self._simple_mappings)

    def to_opensearch(self, query: str) -> Dict[str, Any]:
        """Convert TQL query to OpenSearch query format.

        Args:
            query: TQL query string

        Returns:
            OpenSearch query dictionary

        Raises:
            TQLParseError: If query parsing fails
        """
        return self.opensearch_ops.to_opensearch(query)

    def to_opensearch_dsl(self, query: str) -> Dict[str, Any]:
        """Convert TQL query to OpenSearch DSL format.

        This is an alias for to_opensearch() for backward compatibility.

        Args:
            query: TQL query string

        Returns:
            OpenSearch DSL query dictionary
        """
        return self.opensearch_ops.to_opensearch_dsl(query)

    def analyze_query(self, query: str, context: str = "in_memory") -> Dict[str, Any]:  # noqa: C901
        """Analyze a TQL query for structure, complexity, and potential issues.

        Args:
            query: TQL query string
            context: Execution context ("in_memory" or "opensearch")

        Returns:
            Dictionary containing analysis results including:
            - ast: The parsed AST
            - stats: Query statistics (fields used, operators, etc.)
            - complexity: Query complexity metrics
            - warnings: Potential issues or optimizations
            - health: Overall query health assessment
        """
        # Parse the query
        ast = self.parse(query)

        # Collect basic statistics
        stats: Dict[str, Any] = {
            "fields": set(),
            "operators": set(),
            "logical_operators": set(),
            "has_mutators": False,
            "has_type_hints": False,
            "depth": 0,
        }

        def traverse_ast(node, depth=0):
            if isinstance(node, dict):
                stats["depth"] = max(stats["depth"], depth)
                node_type = node.get("type")

                if node_type == "comparison":
                    if "field" in node:
                        stats["fields"].add(node["field"])
                    if "operator" in node:
                        stats["operators"].add(node["operator"])
                    if node.get("type_hint"):
                        stats["has_type_hints"] = True
                    if node.get("field_mutators") or node.get("value_mutators"):
                        stats["has_mutators"] = True
                elif node_type == "logical_op":
                    stats["logical_operators"].add(node.get("operator"))
                    traverse_ast(node.get("left"), depth + 1)
                    traverse_ast(node.get("right"), depth + 1)
                elif node_type == "unary_op":
                    stats["logical_operators"].add("not")
                    traverse_ast(node.get("operand"), depth + 1)
                elif node_type == "query_with_stats":
                    # Traverse into the filter part to find mutators and fields
                    filter_node = node.get("filter")
                    if filter_node:
                        traverse_ast(filter_node, depth + 1)
                    # Also traverse the stats part
                    stats_node = node.get("stats")
                    if stats_node:
                        traverse_ast(stats_node, depth + 1)
                elif node_type == "stats_expr":
                    # Check aggregations for any fields or mutators
                    aggregations = node.get("aggregations", [])
                    for agg in aggregations:
                        if isinstance(agg, dict):
                            field = agg.get("field")
                            if field and field != "*":
                                stats["fields"].add(field)
                            # Check for field mutators in aggregations
                            if agg.get("field_mutators"):
                                stats["has_mutators"] = True
                elif node_type == "geo_expr":
                    # Geo expressions always have mutators
                    field = node.get("field")
                    if field:
                        stats["fields"].add(field)
                    stats["has_mutators"] = True
                elif node_type == "nslookup_expr":
                    # NSLookup expressions always have mutators
                    field = node.get("field")
                    if field:
                        stats["fields"].add(field)
                    stats["has_mutators"] = True

        traverse_ast(ast)

        # Convert sets to lists for JSON serialization
        stats["fields"] = sorted(stats["fields"])
        stats["operators"] = sorted(stats["operators"])
        stats["logical_operators"] = sorted(stats["logical_operators"])

        # Check for warnings and performance issues
        warnings = self.validation_ops.check_performance_issues(ast, query)

        # Assess overall health
        health_score = 100
        health_reasons = []

        if stats["depth"] > 5:
            health_score -= 20
            health_reasons.append("Query is deeply nested (depth > 5)")

        if len(stats["fields"]) > 10:
            health_score -= 10
            health_reasons.append("Query uses many fields (>10)")

        for warning in warnings:
            if warning["severity"] == "error":
                health_score -= 20
            elif warning["severity"] == "warning":
                health_score -= 10

        # If there are mutators, analyze their performance impact
        mutator_health_info = None
        if stats["has_mutators"]:
            # Use MutatorAnalyzer to evaluate mutator performance
            from .mutator_analyzer import MutatorAnalyzer

            analyzer = MutatorAnalyzer(self.field_mappings)
            mutator_analysis = analyzer.analyze_ast(ast, context=context)

            # Get the context-specific health evaluation
            mutator_health_info = {
                "health_status": mutator_analysis.health_status,
                "health_reasons": mutator_analysis.health_reasons,
                "post_processing_required": len(mutator_analysis.post_processing_requirements) > 0,
            }

            # Adjust overall health based on mutator analysis
            if mutator_analysis.health_status == "red":
                health_score -= 30
                health_reasons.extend([r["reason"] for r in mutator_analysis.health_reasons if r["status"] == "red"])
            elif mutator_analysis.health_status == "yellow":
                health_score -= 15
                health_reasons.extend([r["reason"] for r in mutator_analysis.health_reasons if r["status"] == "yellow"])

        health_status = "good" if health_score >= 80 else "fair" if health_score >= 60 else "poor"

        result = {
            "query": query,
            "ast": ast,
            "stats": stats,
            "complexity": {
                "depth": stats["depth"],
                "field_count": len(stats["fields"]),
                "operator_count": len(stats["operators"]) + len(stats["logical_operators"]),
            },
            "warnings": warnings,
            "health": {"status": health_status, "score": health_score, "reasons": health_reasons},
        }

        # Add mutator health info if present
        if mutator_health_info:
            result["mutator_health"] = mutator_health_info

        return result

    def execute_opensearch(  # noqa: C901
        self,
        opensearch_client: Any = None,
        index: Optional[str] = None,
        query: Optional[str] = None,
        size: int = 500,
        from_: int = 0,
        sort: Optional[List[Dict[str, Any]]] = None,
        timestamp_field: str = "@timestamp",
        time_range: Optional[Dict[str, str]] = None,
        scan_all: bool = False,
        scroll_size: int = 1000,
        scroll_timeout: str = "5m",
        save_enrichment: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute a TQL query against OpenSearch with post-processing and enhanced features.

        This method maintains backward compatibility while delegating to the new implementation.

        Args:
            opensearch_client: OpenSearch client instance (ignored - uses internal client)
            index: Index name to search
            query: The TQL query string
            size: Number of results to return (default: 500)
            search_after: Values from previous result's sort field for pagination
            sort: Sort order specification (e.g., [{"@timestamp": "desc"}, {"_id": "asc"}])
            timestamp_field: Field name for timestamp filtering (default: "@timestamp")
            time_range: Optional time range dict with 'gte' and/or 'lte' keys
            scan_all: If True, use scroll API to retrieve all matching documents
            scroll_size: Size per scroll when scan_all=True (default: 1000)
            scroll_timeout: Scroll timeout when scan_all=True (default: "5m")
            save_enrichment: If True, save enriched documents back to OpenSearch

        Returns:
            Dictionary containing:
            - results: List of processed results
            - total: Total number of matching documents
            - sort_values: Sort values of the last document (for search_after pagination)
            - post_processing_applied: Whether post-processing was applied
            - health_status: Query health status
            - health_reasons: List of health issues
            - performance_impact: Post-processing performance impact info
            - scan_info: Information about scan operation (if scan_all=True)

        Raises:
            TQLExecutionError: If query execution fails
        """
        # Handle both old and new calling conventions
        if isinstance(opensearch_client, str) and query is None:
            # New style: execute_opensearch(query, index=index, ...)
            query = opensearch_client
            index = index
            # Check if opensearch_client is in kwargs (for test mocking)
            if "opensearch_client" in kwargs:
                opensearch_client = kwargs["opensearch_client"]
        elif query is None:
            raise ValueError("Query parameter is required")

        # Remove parameters that the new implementation doesn't understand
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["save_enrichment", "opensearch_client"]}

        # Add the supported parameters
        filtered_kwargs.update(
            {
                "timestamp_field": timestamp_field,
                "time_range": time_range,
                "scan_all": scan_all,
                "scroll_size": scroll_size,
                "scroll_timeout": scroll_timeout,
                "from_": from_,
                "sort": sort,
            }
        )

        # Add opensearch_client if it was provided (e.g., for mocking)
        if opensearch_client is not None and not isinstance(opensearch_client, str):
            filtered_kwargs["client"] = opensearch_client

        # Execute using new implementation
        results = self.opensearch_ops.execute_opensearch(query, index=index, size=size, **filtered_kwargs)

        # Convert to old format if needed
        if isinstance(results, list):
            # Legacy format - convert to dict
            # Check if post-processing was applied by analyzing the query
            post_processing_applied = False
            try:
                analysis = self.analyze_query(query, context="opensearch")
                if "mutator_health" in analysis and analysis["mutator_health"].get("post_processing_required"):
                    post_processing_applied = True
            except Exception:
                # Ignore analysis errors - this is just for health status
                pass

            # Determine health status based on post-processing
            if post_processing_applied:
                health_status = "yellow"
                health_reasons = ["Post-processing required - results may be incomplete with pagination"]
            else:
                health_status = "green"
                health_reasons = []

            return {
                "results": results,
                "total": len(results),
                "post_processing_applied": post_processing_applied,
                "health_status": health_status,
                "health_reasons": health_reasons,
                "performance_impact": {"overhead_ms": 0, "mutators_applied": 0},
                "scan_info": {"used_scan": False},
                "optimizations_applied": [],
            }
        else:
            # Already in dict format - just ensure required fields exist for backward compatibility
            if "scan_info" not in results:
                results["scan_info"] = {"used_scan": False}
            if "optimizations_applied" not in results:
                results["optimizations_applied"] = []
            return results

    def evaluate(self, query: str) -> Dict[str, Any]:  # noqa: C901
        """Evaluate a TQL query for validation, health status, and field mapping information.

        This method validates the query and returns comprehensive information including
        health status, validation results, and field mappings.

        Args:
            query: TQL query string

        Returns:
            Dictionary containing:
            - is_valid: Whether the query is syntactically valid
            - errors: List of validation errors with type, message, field, position
            - fields: Dictionary mapping field names to their mappings
            - health: Health status ('green', 'yellow', or 'red')
            - health_reasons: List of health issues with status, query_part, and reason
        """
        # Initialize result
        result: Dict[str, Any] = {"is_valid": True, "errors": [], "fields": {}, "health": "green", "health_reasons": []}

        # Handle empty query
        if not query or not query.strip():
            result["is_valid"] = False
            result["errors"].append({"type": "TQLSyntaxError", "message": "Empty query", "position": 0})
            return result

        try:
            # First try to parse the query
            ast = self.parse(query)

            # Extract field information from AST
            fields = {}
            field_names = self._extract_fields_from_ast(ast)

            # Process field mappings and check for unknown fields
            for field in field_names:
                if field in self.field_mappings:
                    # Get the mapped field name(s)
                    mapping = self.field_mappings[field]
                    if isinstance(mapping, str):
                        fields[field] = [mapping]
                    elif isinstance(mapping, dict):
                        # Handle intelligent mappings
                        mapped_fields = []
                        for key, value in mapping.items():
                            if isinstance(value, dict) and "type" in value:
                                # This is a field mapping with type info
                                mapped_fields.append(key)
                            elif isinstance(value, str):
                                # Direct mapping
                                mapped_fields.append(key)
                        fields[field] = mapped_fields if mapped_fields else [field]
                    else:
                        fields[field] = []
                else:
                    # No mapping found
                    fields[field] = []
                    if self.field_mappings:  # Only flag as error if mappings are defined
                        result["is_valid"] = False
                        # Get available fields for suggestions
                        available_fields = sorted(self.field_mappings.keys())
                        error_msg = f"Unknown field '{field}'. Available fields: {', '.join(available_fields[:5])}"
                        if len(available_fields) > 5:
                            error_msg += f" and {len(available_fields) - 5} more"

                        result["errors"].append(
                            {
                                "type": "TQLFieldError",
                                "message": error_msg,
                                "field": field,
                                "position": query.find(field),
                            }
                        )

                        # Update health status
                        result["health"] = "red"
                        result["health_reasons"].append(
                            {"status": "red", "query_part": field, "reason": f"Unknown field '{field}'"}
                        )

            result["fields"] = fields

            # Check for type compatibility if mappings are provided
            if self.field_mappings:
                try:
                    # Validate types
                    self.validation_ops._check_type_compatibility(ast)

                    # Check for performance issues
                    warnings = self.validation_ops.check_performance_issues(ast, query)

                    # Process warnings
                    for warning in warnings:
                        if warning["severity"] == "error":
                            result["health"] = "red"
                            result["health_reasons"].append(
                                {
                                    "status": "red",
                                    "query_part": warning.get("query_part", warning.get("field", query[:20] + "...")),
                                    "reason": warning["message"],
                                }
                            )
                        elif warning["severity"] == "warning":
                            if result["health"] == "green":
                                result["health"] = "yellow"
                            result["health_reasons"].append(
                                {
                                    "status": "yellow",
                                    "query_part": warning.get("query_part", warning.get("field", query[:20] + "...")),
                                    "reason": warning["message"],
                                }
                            )

                except (TQLValidationError, TQLTypeError) as e:
                    # Type validation error
                    result["is_valid"] = False
                    error_msg = str(e)
                    error_field: Optional[str] = getattr(e, "field", None)
                    error_operator: Optional[str] = getattr(e, "operator", None)

                    result["errors"].append(
                        {
                            "type": "TQLTypeError",
                            "message": error_msg,
                            "field": error_field,
                            "operator": error_operator,
                            "position": (
                                query.find(f"{error_field} {error_operator}")
                                if error_field and error_operator
                                else None
                            ),
                        }
                    )

                    # Add to health_reasons
                    query_part = (
                        f"{error_field} {error_operator} ..." if error_field and error_operator else query[:20] + "..."
                    )
                    result["health"] = "red"
                    result["health_reasons"].append({"status": "red", "query_part": query_part, "reason": error_msg})

                except TQLOperatorError as e:
                    # Operator usage error
                    result["is_valid"] = False
                    result["errors"].append(
                        {"type": "TQLOperatorError", "message": str(e), "position": getattr(e, "position", None)}
                    )

        except TQLSyntaxError as e:
            # Syntax errors
            result["is_valid"] = False
            position = getattr(e, "position", None)
            # suggestions = getattr(e, "suggestions", [])  # Reserved for future use

            # Try to extract field from syntax error
            field = None
            try:
                # Parse partial AST to get field
                partial_query = query[:position] if position else query
                if " " in partial_query:
                    field = partial_query.split()[0]
            except Exception:
                # Ignore errors when trying to extract field from partial query
                pass

            error_entry = {"type": "TQLSyntaxError", "message": str(e), "position": position}

            # Add field to errors if we could extract it
            if field:
                result["fields"][field] = []

            result["errors"].append(error_entry)
            result["health"] = "red"

            # Add to health_reasons
            result["health_reasons"].append(
                {"status": "red", "query_part": query[:20] + "..." if len(query) > 20 else query, "reason": str(e)}
            )

        except TQLParseError as e:
            # General parsing errors
            result["is_valid"] = False
            result["errors"].append(
                {"type": "TQLParseError", "message": str(e), "position": getattr(e, "position", None)}
            )
            result["health"] = "red"
            result["health_reasons"].append(
                {"status": "red", "query_part": query[:20] + "..." if len(query) > 20 else query, "reason": str(e)}
            )

        except Exception as e:
            # Unexpected errors
            result["is_valid"] = False
            result["errors"].append({"type": type(e).__name__, "message": str(e), "position": None})
            result["health"] = "red"
            result["health_reasons"].append(
                {"status": "red", "query_part": query[:20] + "..." if len(query) > 20 else query, "reason": str(e)}
            )

        return result

    def _extract_fields_from_ast(self, ast: Dict[str, Any]) -> List[str]:  # noqa: C901
        """Extract all field names from an AST recursively."""
        fields = []

        if isinstance(ast, dict):
            node_type = ast.get("type")

            if node_type == "comparison":
                field = ast.get("field")
                if field:
                    fields.append(field)

            elif node_type == "collection_op":
                field = ast.get("field")
                if field:
                    fields.append(field)

            elif node_type == "logical_op":
                # Recursively extract from both sides
                fields.extend(self._extract_fields_from_ast(ast.get("left", {})))
                fields.extend(self._extract_fields_from_ast(ast.get("right", {})))

            elif node_type == "unary_op":
                # Recursively extract from operand
                fields.extend(self._extract_fields_from_ast(ast.get("operand", {})))

            elif node_type == "mutator":
                # Extract from source
                fields.extend(self._extract_fields_from_ast(ast.get("source", {})))

            elif node_type == "query":
                # Extract from filter
                if "filter" in ast:
                    fields.extend(self._extract_fields_from_ast(ast["filter"]))

        return list(set(fields))  # Remove duplicates

    def analyze(self, query: str) -> Dict[str, Any]:
        """Analyze a TQL query and return detailed execution information.

        This method parses the query and returns information about how it would
        be executed, without actually running it against data.

        Args:
            query: TQL query string

        Returns:
            Dictionary containing:
            - ast: The parsed AST
            - opensearch: The OpenSearch query (if applicable)
            - explanation: Human-readable explanation
            - field_mappings: Applied field mappings
        """
        # Parse the query
        ast = self.parse(query)

        # Convert to OpenSearch format
        try:
            opensearch_query = self.to_opensearch(query)
        except Exception:
            opensearch_query = None

        # Generate explanation
        explanation = self._ast_to_query_string(ast)

        # Collect field mappings used
        used_mappings = {}
        fields = self.extract_fields(query)
        for field in fields:
            if field in self.field_mappings:
                used_mappings[field] = self.field_mappings[field]

        return {
            "query": query,
            "ast": ast,
            "opensearch": opensearch_query,
            "explanation": explanation,
            "field_mappings": used_mappings,
        }

    def explain(self, query: str) -> Dict[str, Any]:
        """Explain how a TQL query will be executed.

        Provides a detailed breakdown of query parsing, field mappings,
        and execution strategy.

        Args:
            query: TQL query string

        Returns:
            Detailed execution plan
        """
        result = self.analyze(query)

        # Add execution strategy
        result["execution_strategy"] = {
            "backend": "opensearch" if result["opensearch"] else "in-memory",
            "optimizations": [],
        }

        # Add any optimizations
        if self.has_analyzer_info:
            result["execution_strategy"]["optimizations"].append(
                "Using enhanced field mappings with analyzer information"
            )

        return result

    def explain_optimization(self, query: str) -> Dict[str, Any]:
        """Explain query optimizations for OpenSearch execution.

        Shows how mutators are split between Phase 1 (OpenSearch) and Phase 2 (post-processing).

        Args:
            query: TQL query string

        Returns:
            Optimization explanation including phase breakdown
        """
        # Use opensearch_ops.analyze_opensearch_query for backward compatibility
        analysis = self.opensearch_ops.analyze_opensearch_query(query)

        if isinstance(analysis, MutatorAnalysisResult):
            # Has mutators - show phase breakdown
            optimized_query = self._ast_to_query_string(analysis.optimized_ast)

            # Extract post-processing requirements
            post_processing_mutators = []
            for req in analysis.post_processing_requirements:
                post_processing_mutators.extend(req.mutators)

            return {
                "query": query,
                "has_mutators": True,
                "phase1": {
                    "description": "OpenSearch query (with optimizations applied)",
                    "query": optimized_query,
                    "optimizations": analysis.optimizations_applied,
                },
                "phase2": {
                    "description": "Post-processing filters and enrichments",
                    "requirements": analysis.post_processing_requirements,
                    "mutators": post_processing_mutators,
                },
                "health": {"status": analysis.health_status, "reasons": analysis.health_reasons},
            }
        else:
            # No mutators
            return {
                "query": query,
                "has_mutators": False,
                "opensearch_query": analysis["opensearch_query"],
                "optimizations": analysis["optimizations"],
                "notes": ["Query can be fully executed in OpenSearch without post-processing"],
            }

    def extract_fields(self, query: str) -> List[str]:
        """Extract all unique field names referenced in a TQL query.

        Args:
            query: TQL query string

        Returns:
            Sorted list of unique field names

        Raises:
            TQLParseError: If query parsing fails
        """
        return self.parser.extract_fields(query)

    def stats(self, data: Union[List[Dict], str], stats_query: str) -> Dict[str, Any]:
        """Execute a statistics query on data.

        Args:
            data: List of records or file path
            stats_query: Stats query string (e.g., "| stats count() by status")

        Returns:
            Dictionary containing aggregation results
        """
        return self.stats_ops.stats(data, stats_query)

    def query_stats(self, data: Union[List[Dict], str], query: str) -> Dict[str, Any]:
        """Execute a TQL query with stats aggregation.

        This combines filtering and statistical aggregation in one query.

        Args:
            data: List of records or file path
            query: Combined query string (e.g., "status = 'active' | stats count() by type")

        Returns:
            Dictionary containing aggregation results
        """
        return self.stats_ops.query_stats(data, query)

    def analyze_stats_query(self, query: str) -> Dict[str, Any]:
        """Analyze a stats query for performance and correctness.

        Args:
            query: Stats query string

        Returns:
            Analysis results including AST and any warnings
        """
        return self.stats_ops.analyze_stats_query(query)

    def query_file_streaming(
        self,
        file_path: str,
        query: str,
        input_format: str = "auto",
        csv_delimiter: str = ",",
        csv_headers: Optional[List[str]] = None,
        no_header: bool = False,
        field_types: Optional[Dict[str, str]] = None,
        sample_size: int = 100,
    ) -> Generator[Dict[str, Any], None, None]:
        """Execute a TQL query against a file in streaming mode.

        This method processes files line-by-line with minimal memory usage,
        yielding matching records as they are found.

        Args:
            file_path: Path to file
            query: TQL query string (filter query only, not stats)
            input_format: File format ('json', 'jsonl', 'csv', 'auto')
            csv_delimiter: CSV delimiter character
            csv_headers: Manual CSV header names
            no_header: Force CSV to be treated as having no header
            field_types: Manual field type mappings
            sample_size: Number of records to sample for type inference

        Yields:
            Matching records as dictionaries

        Raises:
            TQLParseError: If query parsing fails
            TQLExecutionError: If file processing fails
        """
        from .streaming_file_processor import StreamingFileProcessor

        # Parse the query
        ast = self.parse(query)

        # Validate query type (only filter queries supported for streaming)
        query_type = ast.get("type")
        if query_type in ["stats_expr", "query_with_stats"]:
            raise TQLExecutionError("Stats queries not supported in streaming mode. Use query_file_stats() instead.")

        # Create streaming processor
        processor = StreamingFileProcessor(
            sample_size=sample_size,
            csv_delimiter=csv_delimiter,
            field_types=field_types,
            csv_headers=csv_headers,
            no_header=no_header,
        )

        # Process file and evaluate query on each record
        for record in processor.process_file(file_path, input_format):
            if self.evaluator._evaluate_node(ast, record, self._simple_mappings):
                yield record

    def query_file_stats(
        self,
        file_path: str,
        query: str,
        input_format: str = "auto",
        csv_delimiter: str = ",",
        csv_headers: Optional[List[str]] = None,
        no_header: bool = False,
        field_types: Optional[Dict[str, str]] = None,
        sample_size: int = 100,
    ) -> Dict[str, Any]:
        """Execute a TQL stats query against a file in streaming mode.

        This method processes files line-by-line with accumulator-based stats
        calculations for memory efficiency.

        Args:
            file_path: Path to file
            query: TQL query string (can include filters and stats)
            input_format: File format ('json', 'jsonl', 'csv', 'auto')
            csv_delimiter: CSV delimiter character
            csv_headers: Manual CSV header names
            no_header: Force CSV to be treated as having no header
            field_types: Manual field type mappings
            sample_size: Number of records to sample for type inference

        Returns:
            Dictionary containing aggregation results

        Raises:
            TQLParseError: If query parsing fails
            TQLExecutionError: If file processing fails
        """
        from .streaming_file_processor import StreamingFileProcessor

        # Parse the query
        ast = self.parse(query)
        query_type = ast.get("type")

        # Create streaming processor
        processor = StreamingFileProcessor(
            sample_size=sample_size,
            csv_delimiter=csv_delimiter,
            field_types=field_types,
            csv_headers=csv_headers,
            no_header=no_header,
        )

        # Handle different query types
        if query_type == "stats_expr":
            # Pure stats query - process all records
            record_iter = processor.process_file(file_path, input_format)
            return self.stats_evaluator.evaluate_stats_streaming(record_iter, ast, self.field_mappings)

        elif query_type == "query_with_stats":
            # Filter + stats query
            filter_ast = ast["filter"]
            stats_ast = ast["stats"]

            # Create filtered iterator
            def filtered_records():
                for record in processor.process_file(file_path, input_format):
                    if self.evaluator._evaluate_node(filter_ast, record, self._simple_mappings):
                        yield record

            return self.stats_evaluator.evaluate_stats_streaming(filtered_records(), stats_ast, self.field_mappings)

        else:
            # Regular filter query - shouldn't use stats method
            raise TQLExecutionError("Use query_file_streaming() for filter queries without stats aggregations.")

    def query_folder(
        self,
        folder_path: str,
        query: str,
        pattern: str = "*",
        input_format: str = "auto",
        recursive: bool = False,
        parallel: int = 4,
        csv_delimiter: str = ",",
        csv_headers: Optional[List[str]] = None,
        no_header: bool = False,
        field_types: Optional[Dict[str, str]] = None,
        sample_size: int = 100,
    ) -> Dict[str, Any]:
        """Execute a TQL query against multiple files in a folder.

        This method processes all matching files and aggregates results,
        supporting both filter queries (with records) and stats queries.

        Args:
            folder_path: Path to folder
            query: TQL query string
            pattern: Glob pattern for file matching
            input_format: File format ('json', 'jsonl', 'csv', 'auto')
            recursive: Process subdirectories recursively
            parallel: Number of parallel workers
            csv_delimiter: CSV delimiter character
            csv_headers: Manual CSV header names
            no_header: Force CSV to be treated as having no header
            field_types: Manual field type mappings
            sample_size: Number of records to sample for type inference

        Returns:
            Dictionary containing results and/or stats aggregated across all files

        Raises:
            TQLParseError: If query parsing fails
            TQLExecutionError: If folder processing fails
        """
        from .streaming_file_processor import StreamingFileProcessor

        # Parse the query
        ast = self.parse(query)
        query_type = ast.get("type")

        # Create streaming processor
        processor = StreamingFileProcessor(
            sample_size=sample_size,
            csv_delimiter=csv_delimiter,
            field_types=field_types,
            csv_headers=csv_headers,
            no_header=no_header,
        )

        # Process folder based on query type
        if query_type == "stats_expr":
            # Pure stats query - aggregate across all files

            def all_records():
                for _file_path, record in processor.process_folder(
                    folder_path, pattern, input_format, recursive, parallel
                ):
                    yield record

            stats_result = self.stats_evaluator.evaluate_stats_streaming(all_records(), ast, self.field_mappings)
            return {"stats": stats_result, "files_processed": "multiple"}

        elif query_type == "query_with_stats":
            # Filter + stats query
            filter_ast = ast["filter"]
            stats_ast = ast["stats"]

            def filtered_records():
                for _file_path, record in processor.process_folder(
                    folder_path, pattern, input_format, recursive, parallel
                ):
                    if self.evaluator._evaluate_node(filter_ast, record, self._simple_mappings):
                        yield record

            stats_result = self.stats_evaluator.evaluate_stats_streaming(
                filtered_records(), stats_ast, self.field_mappings
            )
            return {"stats": stats_result, "files_processed": "multiple"}

        else:
            # Regular filter query - collect matching records from all files
            matched_records = []
            files_processed = 0
            files_with_matches = 0

            for file_path, record in processor.process_folder(folder_path, pattern, input_format, recursive, parallel):
                files_processed += 1
                if self.evaluator._evaluate_node(ast, record, self._simple_mappings):
                    matched_records.append({"_source_file": file_path, **record})
                    files_with_matches += 1

            return {
                "results": matched_records,
                "total": len(matched_records),
                "files_processed": files_processed,
                "files_with_matches": files_with_matches,
            }

    def _apply_mutators_to_record(self, ast: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
        """Apply any mutators in the AST to enrich the record.

        Args:
            ast: Query AST that may contain mutators
            record: Record to enrich

        Returns:
            Enriched record (may be same as input if no enrichments)
        """
        # Check if we need to apply mutators
        if not self._has_output_mutators(ast):
            return record

        # Deep copy to avoid modifying original
        import copy

        enriched_record = copy.deepcopy(record)

        # Apply mutators from AST nodes
        self._apply_node_mutators(ast, enriched_record)

        return enriched_record

    def _has_output_mutators(self, ast: Dict[str, Any]) -> bool:
        """Check if AST contains mutators that should transform output.

        Args:
            ast: Query AST

        Returns:
            True if output mutators are present
        """
        if isinstance(ast, dict):
            node_type = ast.get("type")

            # Check for field mutators with exists operator (output transformation)
            if node_type == "comparison" and ast.get("operator") == "exists" and ast.get("field_mutators"):
                return True

            # Recursively check child nodes
            if node_type == "logical_op":
                left = ast.get("left", {})
                right = ast.get("right", {})
                return self._has_output_mutators(left) or self._has_output_mutators(right)
            elif node_type == "unary_op":
                operand = ast.get("operand", {})
                return self._has_output_mutators(operand)

        return False

    def _apply_node_mutators(self, ast: Dict[str, Any], record: Dict[str, Any]) -> None:
        """Apply mutators from AST nodes to the record.

        Args:
            ast: Query AST
            record: Record to modify (in-place)
        """
        if not isinstance(ast, dict):
            return

        node_type = ast.get("type")

        # Apply mutators for exists operator (output transformation)
        if node_type == "comparison" and ast.get("operator") == "exists" and ast.get("field_mutators"):
            field_name = ast["field"]
            field_mutators = ast["field_mutators"]

            # Get field value
            field_value = self._get_nested_field(record, field_name)

            if field_value is not None:
                # Apply mutators
                from .mutators import apply_mutators

                mutated_value = apply_mutators(field_value, field_mutators, field_name, record)

                # Update record with mutated value
                self._set_nested_field(record, field_name, mutated_value)

        # Recursively process child nodes
        elif node_type == "logical_op":
            self._apply_node_mutators(ast.get("left", {}), record)
            self._apply_node_mutators(ast.get("right", {}), record)
        elif node_type == "unary_op":
            self._apply_node_mutators(ast.get("operand", {}), record)

    def _get_nested_field(self, record: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested field path.

        Args:
            record: Record dictionary
            field_path: Dot-separated field path

        Returns:
            Field value or None if not found
        """
        parts = field_path.split(".")
        current = record

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _set_nested_field(self, record: Dict[str, Any], field_path: str, value: Any) -> None:
        """Set value in nested field path.

        Args:
            record: Record dictionary to modify
            field_path: Dot-separated field path
            value: Value to set
        """
        parts = field_path.split(".")
        current = record

        # Navigate to parent of target field
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set the value
        if len(parts) > 0:
            current[parts[-1]] = value

    def _convert_stats_result(self, stats_result: Dict[str, Any], viz_hint: Optional[str] = None) -> Dict[str, Any]:
        """Convert stats result from query() format to execute_opensearch format.

        Args:
            stats_result: Result from stats() or query_stats() method
            viz_hint: Optional visualization hint from the query

        Returns:
            Stats result in execute_opensearch format
        """
        # Map the stats evaluator format to execute_opensearch format
        result = {}

        if stats_result.get("type") == "simple_aggregation":
            result = {
                "type": "stats",
                "operation": stats_result["function"],
                "field": stats_result["field"],
                "values": stats_result["value"],
            }
        elif stats_result.get("type") == "multiple_aggregations":
            # For multiple aggregations, return the results dict
            result = {"type": "stats_multiple", "results": stats_result["results"]}
        elif stats_result.get("type") == "grouped_aggregation":
            # For grouped aggregations
            result = {
                "type": "stats_grouped",
                "group_by": stats_result["group_by"],
                "results": stats_result["results"],
                "operation": stats_result.get("function", "count"),
                "field": stats_result.get("field", "*"),
            }
        else:
            # Return as-is if format is unknown
            result = stats_result

        # Add visualization hint if provided
        if viz_hint:
            result["viz_hint"] = viz_hint

        return result
