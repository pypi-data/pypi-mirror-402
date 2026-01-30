"""Parser module for Tellaro Query Language (TQL).

This module provides the main TQLParser class that orchestrates parsing
using the modular parser components.
"""

from typing import Any, Dict, List

from pyparsing import ParseException, ParserElement

from .exceptions import TQLOperatorError, TQLParseError, TQLSyntaxError, TQLValueError
from .parser_components.ast_builder import ASTBuilder
from .parser_components.error_analyzer import ErrorAnalyzer
from .parser_components.field_extractor import FieldExtractor
from .parser_components.grammar import TQLGrammar

ParserElement.enablePackrat()


class TQLParser:
    """TQL query parser.

    Parses TQL query strings into an Abstract Syntax Tree (AST) that can be
    evaluated against data or converted to backend-specific query formats.
    """

    # Maximum query depth to prevent stack overflow and DoS attacks
    MAX_QUERY_DEPTH = 50

    def __init__(self):
        """Initialize the parser with TQL grammar."""
        self.grammar = TQLGrammar()
        self.ast_builder = ASTBuilder()
        self.error_analyzer = ErrorAnalyzer()
        self.field_extractor = FieldExtractor()

    def parse(self, query: str) -> Dict[str, Any]:
        """Parse a TQL query string into an AST.

        Args:
            query: The TQL query string to parse

        Returns:
            Dictionary representing the parsed query AST

        Raises:
            TQLParseError: If the query has invalid syntax
        """
        # Handle empty or whitespace-only queries
        if not query or not query.strip():
            # Return a special AST that matches all records
            return {"type": "match_all"}

        try:
            # Parse the query
            parsed_result = self.grammar.tql_expr.parseString(query, parseAll=True)

            # Convert to our AST format
            # Start depth counting at 0 from parse() entry point
            return self._build_ast(parsed_result.asList()[0], depth=0)

        except ParseException as e:
            # Extract position and context from pyparsing exception
            position = e.col - 1 if hasattr(e, "col") else e.loc

            # Check for unclosed quotes first
            if query.count('"') % 2 != 0:
                last_quote_pos = query.rfind('"')
                raise TQLSyntaxError(
                    f"Unterminated string literal starting at position {last_quote_pos}",
                    position=last_quote_pos,
                    query=query,
                    suggestions=[],
                )

            if query.count("'") % 2 != 0:
                last_quote_pos = query.rfind("'")
                raise TQLSyntaxError(
                    f"Unterminated string literal starting at position {last_quote_pos}",
                    position=last_quote_pos,
                    query=query,
                    suggestions=[],
                )

            # Analyze the error to provide better feedback
            error_msg, suggestions = self.error_analyzer.analyze_parse_error(query, position, str(e))

            raise TQLSyntaxError(error_msg, position=position, query=query, suggestions=suggestions)
        except TQLOperatorError as e:
            # Re-raise operator errors with query context
            e.query = query
            raise e
        except ValueError as e:
            # Handle value errors from our own validation
            raise TQLValueError(str(e), query=query)
        except Exception as e:
            # Generic parse error for unexpected exceptions
            raise TQLParseError(f"Invalid TQL syntax: {str(e)}", query=query)

    def extract_fields(self, query: str) -> List[str]:
        """Extract all unique field references from a TQL query.

        This method parses the query and traverses the AST to find all field names
        referenced in the query. Field mappings are not applied.

        Args:
            query: The TQL query string

        Returns:
            Sorted list of unique field names referenced in the query

        Raises:
            TQLParseError: If the query has invalid syntax
        """
        # Parse the query into an AST
        ast = self.parse(query)

        # Extract fields using the field extractor
        return self.field_extractor.extract_fields(ast)

    def _build_ast(self, parsed: Any, depth: int = 0) -> Dict[str, Any]:  # noqa: C901
        """Build AST from parsed pyparsing result.

        Args:
            parsed: The parsed result from pyparsing
            depth: Current recursion depth (for DoS prevention)

        Returns:
            Dictionary representing the AST node

        Raises:
            TQLSyntaxError: If query depth exceeds maximum allowed depth
        """
        # Check depth limit to prevent stack overflow and DoS attacks
        if depth > self.MAX_QUERY_DEPTH:
            raise TQLSyntaxError(
                f"Query depth exceeds maximum allowed depth of {self.MAX_QUERY_DEPTH}. "
                "Please simplify your query to reduce nesting.",
                position=0,
                query="",
                suggestions=["Reduce query nesting depth", "Split into multiple simpler queries"],
            )

        if isinstance(parsed, list):
            if len(parsed) == 1:
                # Single item, check if it's a field with is_private/is_global mutator
                item = parsed[0]
                if isinstance(item, list):
                    # Check if this is a stats expression (starts with 'stats')
                    if len(item) >= 2 and isinstance(item[0], str) and item[0].lower() == "stats":
                        # This is a stats expression without filter
                        return self._build_stats_ast(item)
                    # Could be a typed_field
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(item)
                    if field_mutators:
                        # Check if the last mutator is is_private or is_global
                        last_mutator = field_mutators[-1] if field_mutators else None
                        if last_mutator and last_mutator.get("name", "").lower() in ["is_private", "is_global"]:
                            # This is field | is_private or field | is_global without operator
                            # Default to eq true
                            result = {
                                "type": "comparison",
                                "field": field_name,
                                "type_hint": type_hint,
                                "operator": "eq",
                                "value": "true",
                            }
                            if field_mutators:
                                result["field_mutators"] = field_mutators
                            return result
                        else:
                            # This is field | mutator without operator (e.g., field | lowercase)
                            # Treat as field exists with mutator for output transformation
                            result = {
                                "type": "comparison",
                                "field": field_name,
                                "type_hint": type_hint,
                                "operator": "exists",
                                "field_mutators": field_mutators,
                            }
                            return result
                # Single item, unwrap it
                return self._build_ast(parsed[0], depth + 1)
            elif len(parsed) >= 2 and isinstance(parsed[0], str) and parsed[0].lower() == "stats":
                # This is a stats expression without filter (applies to all records)
                return self._build_stats_ast(parsed)
            elif len(parsed) == 2:
                # Could be unary logical operator (NOT), unary comparison (field exists), stats expression, or empty geo expression
                first, second = parsed

                # Check for stats expression: | stats ...
                if isinstance(first, str) and first == "|" and isinstance(second, list) and len(second) > 0:
                    # Check if this is a stats expression
                    if isinstance(second[0], str) and second[0].lower() == "stats":
                        # This is | stats expression
                        return self._build_stats_ast(second)

                # Check for empty geo expression: field | geo
                if isinstance(second, str) and second.lower() in ["geo", "geoip_lookup"]:
                    # This is an empty geo expression: field | geo()
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(first)

                    result = {
                        "type": "geo_expr",
                        "field": field_name,
                        "type_hint": type_hint,
                        "field_mutators": field_mutators,
                        "conditions": None,  # No conditions for enrichment-only
                    }

                    return result

                # Check for empty nslookup expression: field | nslookup
                elif isinstance(second, str) and second.lower() == "nslookup":
                    # This is an empty nslookup expression: field | nslookup()
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(first)

                    result = {
                        "type": "nslookup_expr",
                        "field": field_name,
                        "type_hint": type_hint,
                        "field_mutators": field_mutators,
                        "conditions": None,  # No conditions for enrichment-only
                    }

                    return result

                # Check for NOT operator first (before field | mutator check)
                elif isinstance(first, str) and (first.lower() == "not" or first == "!"):
                    # Unary logical operator (NOT or !)
                    return {"type": "unary_op", "operator": "not", "operand": self._build_ast(second, depth + 1)}

                # Check for field | mutator without operator
                # This happens when we have a field with mutator(s) as the last element
                elif isinstance(first, str) and isinstance(second, list):
                    # This could be field | mutator structure
                    # Check if second is a mutator structure (either ['mutator'] or ['mutator', [...params...]])
                    if len(second) >= 1 and isinstance(second[0], str):
                        mutator_name = second[0]
                        # Build a typed_field from these components
                        typed_field = [first, second]
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(typed_field)

                        if mutator_name.lower() in ["is_private", "is_global"]:
                            # This is field | is_private or field | is_global without operator
                            # Default to eq true
                            result = {
                                "type": "comparison",
                                "field": field_name,
                                "type_hint": type_hint,
                                "operator": "eq",
                                "value": "true",
                            }
                        else:
                            # This is field | mutator without operator (e.g., field | lowercase)
                            # Treat as field exists with mutator for output transformation
                            result = {
                                "type": "comparison",
                                "field": field_name,
                                "type_hint": type_hint,
                                "operator": "exists",
                            }

                        if field_mutators:
                            result["field_mutators"] = field_mutators
                        return result
                elif isinstance(second, str) and (second.lower() == "exists" or second.lower() == "!exists"):
                    # Unary comparison operation (field exists or !exists)
                    field_name, type_hint, mutators = self.ast_builder.extract_field_info(first)
                    operator = "not_exists" if second.lower() == "!exists" else "exists"
                    result = {
                        "type": "comparison",
                        "field": field_name,
                        "type_hint": type_hint,
                        "operator": operator,
                        "value": None,  # No value for unary operators
                    }
                    if mutators:
                        result["field_mutators"] = mutators
                    return result
                elif isinstance(first, list) and isinstance(second, list):
                    # This could be filter + stats
                    # Check if second element starts with 'stats'
                    if len(second) >= 2 and isinstance(second[0], str) and second[0].lower() == "stats":
                        # This is filter | stats
                        return {
                            "type": "query_with_stats",
                            "filter": self._build_ast(first, depth + 1),
                            "stats": self._build_stats_ast(second),
                        }
                else:
                    # Fallback to treating as unary logical operator
                    return {
                        "type": "unary_op",
                        "operator": first.lower(),
                        "operand": self._build_ast(second, depth + 1),
                    }
            elif len(parsed) >= 3:
                # Check if this is a field with multiple mutators
                if isinstance(parsed[0], str) and all(
                    isinstance(item, list) and len(item) >= 1 and isinstance(item[0], str) for item in parsed[1:]
                ):
                    # This looks like field | mutator1 | mutator2 | ...
                    last_mutator_list = parsed[-1]
                    if len(last_mutator_list) >= 1 and isinstance(last_mutator_list[0], str):
                        # This is a field with mutators
                        # Build the typed_field structure
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(parsed)

                        # Check if last mutator is is_private/is_global
                        last_mutator_name = last_mutator_list[0].lower()
                        if last_mutator_name in ["is_private", "is_global"]:
                            # Default to eq true for these special mutators
                            result = {
                                "type": "comparison",
                                "field": field_name,
                                "type_hint": type_hint,
                                "operator": "eq",
                                "value": "true",
                            }
                        else:
                            # For other mutators, treat as field exists
                            result = {
                                "type": "comparison",
                                "field": field_name,
                                "type_hint": type_hint,
                                "operator": "exists",
                            }

                        if field_mutators:
                            result["field_mutators"] = field_mutators
                        return result

            if len(parsed) == 4:
                # Check for field_in_values marker: field in [values] __field_in_values__
                if isinstance(parsed[3], str) and parsed[3] == "__field_in_values__":
                    # This is field in [values] syntax
                    field_part, op, values_list, marker = parsed
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(field_part)
                    # Extract values from the list
                    values = []
                    for item in values_list:
                        if isinstance(item, list) and len(item) >= 1:
                            values.append(item[0] if len(item) == 1 else item)
                        else:
                            values.append(item)
                    result = {
                        "type": "comparison",
                        "field": field_name,
                        "type_hint": type_hint,
                        "operator": "in",
                        "value": values,
                    }
                    if field_mutators:
                        result["field_mutators"] = field_mutators
                    return result

                # Check for ANY/ALL operators: ANY field op value
                first, field, operator, value = parsed

                if isinstance(first, str) and first.lower() in ["any", "all"]:
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(field)
                    value_extracted, value_mutators = self.ast_builder.extract_value_info(value)
                    result = {
                        "type": "collection_op",
                        "operator": first.lower(),
                        "field": field_name,
                        "type_hint": type_hint,
                        "comparison_operator": operator.lower(),
                        "value": value_extracted,
                    }
                    if field_mutators:
                        result["field_mutators"] = field_mutators
                    if value_mutators:
                        result["value_mutators"] = value_mutators
                    return result
                else:
                    # Handle other 4-element cases like "field is not value", "field not in value", or geo expressions
                    first, second, third, fourth = parsed

                    # Check for negated operators like "field not none value"
                    if (
                        isinstance(second, str)
                        and (second.lower() == "not" or second == "!")
                        and isinstance(third, str)
                    ):
                        # This is a negated operator
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(first)
                        # Handle 'not none' -> 'any' (double negative)
                        if third.lower() == "none":
                            normalized_operator = "any"
                        else:
                            normalized_operator = f"not_{third.lower()}"

                        # Extract value properly - unwrap if it's a double-wrapped list
                        # This happens for "field not in [values]" where the list is wrapped twice
                        value = fourth
                        if (
                            third.lower() == "in"
                            and isinstance(fourth, list)
                            and len(fourth) == 1
                            and isinstance(fourth[0], list)
                        ):
                            # Unwrap the double-wrapped list for "not in" with values
                            value = fourth[0]

                        result = {
                            "type": "comparison",
                            "field": field_name,
                            "type_hint": type_hint,
                            "operator": normalized_operator,
                            "value": value,
                        }
                        if field_mutators:
                            result["field_mutators"] = field_mutators
                        return result

                    # Check for geo() expression with parameters: field geo params...
                    if isinstance(second, str) and second.lower() in ["geo", "geoip_lookup"]:
                        # This is a geo expression: field | geo(params...)
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(first)

                        # All remaining elements are parameters (could be conditions or actual params)
                        conditions = None
                        geo_params = {}

                        # Process all parameters starting from third element
                        param_elements = parsed[2:]  # Everything after field and 'geo'

                        for element in param_elements:
                            if isinstance(element, list):
                                if len(element) == 2:
                                    # Check if this is a parameter or a condition
                                    if isinstance(element[0], str):
                                        # This is a proper parameter: ['param_name', 'value']
                                        param_name, param_value = element
                                        # Convert string boolean values to actual booleans
                                        if isinstance(param_value, str):
                                            if param_value.lower() == "true":
                                                param_value = True
                                            elif param_value.lower() == "false":
                                                param_value = False
                                        geo_params[param_name] = param_value
                                    else:
                                        # This is a condition like [['country_iso_code'], '=', ['US']]
                                        conditions = element
                                elif len(element) == 3 and element[1] == "=":
                                    # This is a parameter parsed as comparison: [['param'], '=', ['value']]
                                    if (
                                        isinstance(element[0], list)
                                        and len(element[0]) == 1
                                        and isinstance(element[0][0], str)
                                        and element[0][0] in ["force", "cache", "cache_ttl", "db_path", "save", "field"]
                                    ):
                                        param_name = element[0][0]
                                        param_value = (
                                            element[2]
                                            if not isinstance(element[2], list)
                                            else element[2][0] if element[2] else None
                                        )
                                        # Convert string boolean values to actual booleans
                                        if isinstance(param_value, str):
                                            if param_value.lower() == "true":
                                                param_value = True
                                            elif param_value.lower() == "false":
                                                param_value = False
                                        geo_params[param_name] = param_value
                                    else:
                                        # This is actual conditions, not a parameter
                                        conditions = element
                                else:
                                    # This might be conditions
                                    conditions = element

                        result = {
                            "type": "geo_expr",
                            "field": field_name,
                            "type_hint": type_hint,
                            "field_mutators": field_mutators,
                            "conditions": self._build_ast(conditions, depth + 1) if conditions else None,
                        }

                        # Add geo parameters if any
                        if geo_params:
                            result["geo_params"] = geo_params

                        return result

                    # Check for nslookup() expression with parameters: field nslookup params...
                    elif isinstance(second, str) and second.lower() == "nslookup":
                        # This is a nslookup expression: field | nslookup(params...)
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(first)

                        # All remaining elements are parameters (could be conditions or actual params)
                        conditions = None
                        nslookup_params = {}

                        # Process all parameters starting from third element
                        param_elements = parsed[2:]  # Everything after field and 'nslookup'

                        for element in param_elements:
                            if isinstance(element, list):
                                if len(element) == 2:
                                    # Check if this is a parameter or a condition
                                    if isinstance(element[0], str):
                                        # This is a proper parameter: ['param_name', 'value']
                                        param_name, param_value = element
                                        # Convert string boolean values to actual booleans
                                        if isinstance(param_value, str):
                                            if param_value.lower() == "true":
                                                param_value = True
                                            elif param_value.lower() == "false":
                                                param_value = False
                                        nslookup_params[param_name] = param_value
                                    else:
                                        # This is a condition like [['resolved_ip'], 'exists']
                                        conditions = element
                                elif len(element) == 3 and element[1] == "=":
                                    # This is a parameter parsed as comparison: [['param'], '=', ['value']]
                                    if (
                                        isinstance(element[0], list)
                                        and len(element[0]) == 1
                                        and isinstance(element[0][0], str)
                                        and element[0][0]
                                        in ["force", "servers", "append_field", "save", "types", "field"]
                                    ):
                                        param_name = element[0][0]
                                        param_value = (
                                            element[2]
                                            if not isinstance(element[2], list)
                                            else element[2][0] if element[2] else None
                                        )
                                        # Handle types parameter which should be a list
                                        if param_name == "types" and isinstance(element[2], list):
                                            param_value = element[2]
                                            # Unwrap if double-wrapped
                                            if len(param_value) == 1 and isinstance(param_value[0], list):
                                                param_value = param_value[0]
                                        # Convert string boolean values to actual booleans
                                        elif isinstance(param_value, str):
                                            if param_value.lower() == "true":
                                                param_value = True
                                            elif param_value.lower() == "false":
                                                param_value = False
                                        nslookup_params[param_name] = param_value
                                    else:
                                        # This is actual conditions, not a parameter
                                        conditions = element
                                else:
                                    # This might be conditions
                                    conditions = element

                        result = {
                            "type": "nslookup_expr",
                            "field": field_name,
                            "type_hint": type_hint,
                            "field_mutators": field_mutators,
                            "conditions": self._build_ast(conditions, depth + 1) if conditions else None,
                        }

                        # Add nslookup parameters if any
                        if nslookup_params:
                            result["nslookup_params"] = nslookup_params

                        return result

                    # Handle "field is not value" or "field ! is value"
                    if (
                        isinstance(second, str)
                        and second.lower() == "is"
                        and isinstance(third, str)
                        and third.lower() == "not"
                    ):
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(first)
                        result = {
                            "type": "comparison",
                            "field": field_name,
                            "type_hint": type_hint,
                            "operator": "is_not",
                            "value": fourth,
                        }
                        if field_mutators:
                            result["field_mutators"] = field_mutators
                        return result
                    elif isinstance(second, str) and second == "!" and isinstance(third, str) and third.lower() == "is":
                        # Handle "field ! is value"
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(first)
                        result = {
                            "type": "comparison",
                            "field": field_name,
                            "type_hint": type_hint,
                            "operator": "is_not",
                            "value": fourth,
                        }
                        if field_mutators:
                            result["field_mutators"] = field_mutators
                        return result

                    # Handle "field not operator value" (e.g., "field not in value") or "field ! operator value"
                    if isinstance(second, str) and (second.lower() == "not" or second == "!"):
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(first)
                        value, value_mutators = self.ast_builder.extract_value_info(fourth)
                        result = {
                            "type": "comparison",
                            "field": field_name,
                            "type_hint": type_hint,
                            "operator": f"not_{third.lower()}",
                            "value": value,
                        }
                        if field_mutators:
                            result["field_mutators"] = field_mutators
                        if value_mutators:
                            result["value_mutators"] = value_mutators
                        return result
            elif len(parsed) == 5:
                # Check for field_not_in_values marker: field not in [values] __field_not_in_values__
                if isinstance(parsed[4], str) and parsed[4] == "__field_not_in_values__":
                    # This is field not in [values] syntax
                    field_part, not_kw, in_kw, values_list, marker = parsed
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(field_part)
                    # Extract values from the list
                    values = []
                    for item in values_list:
                        if isinstance(item, list) and len(item) >= 1:
                            values.append(item[0] if len(item) == 1 else item)
                        else:
                            values.append(item)
                    result = {
                        "type": "comparison",
                        "field": field_name,
                        "type_hint": type_hint,
                        "operator": "not_in",
                        "value": values,
                    }
                    if field_mutators:
                        result["field_mutators"] = field_mutators
                    return result

                # Check for natural between syntax: field between value1 and value2
                # Only process as between if the second element is "between"
                if (
                    isinstance(parsed[1], str)
                    and parsed[1].lower() == "between"
                    and isinstance(parsed[3], str)
                    and parsed[3].lower() == "and"
                ):
                    field, between_op, value1, and_op, value2 = parsed
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(field)
                    result = {
                        "type": "comparison",
                        "field": field_name,
                        "type_hint": type_hint,
                        "operator": "between",
                        "value": [value1, value2],
                    }
                    if field_mutators:
                        result["field_mutators"] = field_mutators
                    return result
                else:
                    # Check if this is a geo expression with multiple parameters
                    if isinstance(parsed[1], str) and parsed[1].lower() in ["geo", "geoip_lookup"]:
                        # This is a geo expression with multiple parameters
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(parsed[0])

                        # All remaining elements are parameters (could be conditions or actual params)
                        conditions = None
                        geo_params = {}

                        # Process all parameters starting from third element
                        param_elements = parsed[2:]  # Everything after field and 'geo'

                        for element in param_elements:
                            if isinstance(element, list):
                                if len(element) == 2:
                                    # Check if this is a parameter or a condition
                                    if isinstance(element[0], str):
                                        # This is a proper parameter: ['param_name', 'value']
                                        param_name, param_value = element
                                        # Convert string boolean values to actual booleans
                                        if isinstance(param_value, str):
                                            if param_value.lower() == "true":
                                                param_value = True
                                            elif param_value.lower() == "false":
                                                param_value = False
                                        geo_params[param_name] = param_value
                                    else:
                                        # This is a condition like [['country_iso_code'], '=', ['US']]
                                        conditions = element
                                elif len(element) == 3 and element[1] == "=":
                                    # This is a parameter parsed as comparison: [['param'], '=', ['value']]
                                    if (
                                        isinstance(element[0], list)
                                        and len(element[0]) == 1
                                        and isinstance(element[0][0], str)
                                        and element[0][0] in ["force", "cache", "cache_ttl", "db_path", "save", "field"]
                                    ):
                                        param_name = element[0][0]
                                        param_value = (
                                            element[2]
                                            if not isinstance(element[2], list)
                                            else element[2][0] if element[2] else None
                                        )
                                        # Convert string boolean values to actual booleans
                                        if isinstance(param_value, str):
                                            if param_value.lower() == "true":
                                                param_value = True
                                            elif param_value.lower() == "false":
                                                param_value = False
                                        geo_params[param_name] = param_value
                                    else:
                                        # This is actual conditions, not a parameter
                                        conditions = element
                                else:
                                    # This might be conditions
                                    conditions = element

                        result = {
                            "type": "geo_expr",
                            "field": field_name,
                            "type_hint": type_hint,
                            "field_mutators": field_mutators,
                            "conditions": self._build_ast(conditions, depth + 1) if conditions else None,
                        }

                        # Add geo parameters if any
                        if geo_params:
                            result["geo_params"] = geo_params

                        return result
                    # Check if this is a nslookup expression with multiple parameters
                    elif isinstance(parsed[1], str) and parsed[1].lower() == "nslookup":
                        # This is a nslookup expression with multiple parameters
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(parsed[0])

                        # All remaining elements are parameters (could be conditions or actual params)
                        conditions = None
                        nslookup_params = {}

                        # Process all parameters starting from third element
                        param_elements = parsed[2:]  # Everything after field and 'nslookup'

                        for element in param_elements:
                            if isinstance(element, list):
                                if len(element) == 2:
                                    # Check if this is a parameter or a condition
                                    if isinstance(element[0], str):
                                        # This is a proper parameter: ['param_name', 'value']
                                        param_name, param_value = element
                                        # Convert string boolean values to actual booleans
                                        if isinstance(param_value, str):
                                            if param_value.lower() == "true":
                                                param_value = True
                                            elif param_value.lower() == "false":
                                                param_value = False
                                        nslookup_params[param_name] = param_value
                                    else:
                                        # This is a condition like [['resolved_ip'], 'exists']
                                        conditions = element
                                elif len(element) == 3 and element[1] == "=":
                                    # This is a parameter parsed as comparison: [['param'], '=', ['value']]
                                    if (
                                        isinstance(element[0], list)
                                        and len(element[0]) == 1
                                        and isinstance(element[0][0], str)
                                        and element[0][0]
                                        in ["force", "servers", "append_field", "save", "types", "field"]
                                    ):
                                        param_name = element[0][0]
                                        param_value = (
                                            element[2]
                                            if not isinstance(element[2], list)
                                            else element[2][0] if element[2] else None
                                        )
                                        # Handle types parameter which should be a list
                                        if param_name == "types" and isinstance(element[2], list):
                                            param_value = element[2]
                                            # Unwrap if double-wrapped
                                            if len(param_value) == 1 and isinstance(param_value[0], list):
                                                param_value = param_value[0]
                                        # Convert string boolean values to actual booleans
                                        elif isinstance(param_value, str):
                                            if param_value.lower() == "true":
                                                param_value = True
                                            elif param_value.lower() == "false":
                                                param_value = False
                                        nslookup_params[param_name] = param_value
                                    else:
                                        # This is actual conditions, not a parameter
                                        conditions = element
                                else:
                                    # This might be conditions
                                    conditions = element

                        result = {
                            "type": "nslookup_expr",
                            "field": field_name,
                            "type_hint": type_hint,
                            "field_mutators": field_mutators,
                            "conditions": self._build_ast(conditions, depth + 1) if conditions else None,
                        }

                        # Add nslookup parameters if any
                        if nslookup_params:
                            result["nslookup_params"] = nslookup_params

                        return result
                    else:
                        # This is a chained operation, not a between operation
                        return self._build_chained_ast(parsed, depth + 1)

            elif len(parsed) == 6:
                # Check for "field not between value1 and value2" or "field ! between value1 and value2"
                # Only process as not_between if it matches the pattern
                if (
                    len(parsed) >= 6
                    and isinstance(parsed[1], str)
                    and (parsed[1].lower() == "not" or parsed[1] == "!")
                    and isinstance(parsed[2], str)
                    and parsed[2].lower() == "between"
                    and isinstance(parsed[4], str)
                    and parsed[4].lower() == "and"
                ):
                    field, not_word, between_op, value1, and_op, value2 = parsed
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(field)
                    result = {
                        "type": "comparison",
                        "field": field_name,
                        "type_hint": type_hint,
                        "operator": "not_between",
                        "value": [value1, value2],
                    }
                    if field_mutators:
                        result["field_mutators"] = field_mutators
                    return result
                else:
                    # Check if this is a geo expression with multiple parameters
                    if isinstance(parsed[1], str) and parsed[1].lower() in ["geo", "geoip_lookup"]:
                        # This is a geo expression with multiple parameters (6+ elements)
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(parsed[0])

                        # All remaining elements are parameters (could be conditions or actual params)
                        conditions = None
                        geo_params = {}

                        # Process all parameters starting from third element
                        param_elements = parsed[2:]  # Everything after field and 'geo'

                        for element in param_elements:
                            if isinstance(element, list):
                                if len(element) == 2:
                                    # Check if this is a parameter or a condition
                                    if isinstance(element[0], str):
                                        # This is a proper parameter: ['param_name', 'value']
                                        param_name, param_value = element
                                        # Convert string boolean values to actual booleans
                                        if isinstance(param_value, str):
                                            if param_value.lower() == "true":
                                                param_value = True
                                            elif param_value.lower() == "false":
                                                param_value = False
                                        geo_params[param_name] = param_value
                                    else:
                                        # This is a condition like [['country_iso_code'], '=', ['US']]
                                        conditions = element
                                elif len(element) == 3 and element[1] == "=":
                                    # This is a parameter parsed as comparison: [['param'], '=', ['value']]
                                    if (
                                        isinstance(element[0], list)
                                        and len(element[0]) == 1
                                        and isinstance(element[0][0], str)
                                        and element[0][0] in ["force", "cache", "cache_ttl", "db_path", "save", "field"]
                                    ):
                                        param_name = element[0][0]
                                        param_value = (
                                            element[2]
                                            if not isinstance(element[2], list)
                                            else element[2][0] if element[2] else None
                                        )
                                        # Convert string boolean values to actual booleans
                                        if isinstance(param_value, str):
                                            if param_value.lower() == "true":
                                                param_value = True
                                            elif param_value.lower() == "false":
                                                param_value = False
                                        geo_params[param_name] = param_value
                                    else:
                                        # This is actual conditions, not a parameter
                                        conditions = element
                                else:
                                    # This might be conditions
                                    conditions = element

                        result = {
                            "type": "geo_expr",
                            "field": field_name,
                            "type_hint": type_hint,
                            "field_mutators": field_mutators,
                            "conditions": self._build_ast(conditions, depth + 1) if conditions else None,
                        }

                        # Add geo parameters if any
                        if geo_params:
                            result["geo_params"] = geo_params

                        return result
                    else:
                        # This is a chained operation, not a not_between operation
                        return self._build_chained_ast(parsed, depth + 1)

            elif len(parsed) == 3:
                # Binary operation or comparison (including negated unary operators like "field not exists")
                left, operator, right = parsed

                # Check for geo() expression first
                if isinstance(operator, str) and operator.lower() in ["geo", "geoip_lookup"]:
                    # This is a geo expression: field | geo(conditions OR params)
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(left)

                    conditions = None
                    geo_params = {}

                    # Check if this is actually a parameter masquerading as a condition
                    # Look for comparison operations where the field is a known parameter name
                    if (
                        isinstance(right, list)
                        and len(right) == 3
                        and isinstance(right[1], str)
                        and right[1] == "="
                        and isinstance(right[0], list)
                        and len(right[0]) == 1
                        and isinstance(right[0][0], str)
                        and right[0][0] in ["force", "cache", "cache_ttl", "db_path", "save"]
                    ):
                        # This is a parameter parsed as a comparison: force = true
                        param_name = right[0][0]
                        param_value = right[2] if not isinstance(right[2], list) else right[2][0] if right[2] else None
                        # Convert string boolean values to actual booleans
                        if isinstance(param_value, str):
                            if param_value.lower() == "true":
                                param_value = True
                            elif param_value.lower() == "false":
                                param_value = False
                        geo_params[param_name] = param_value
                    else:
                        # This is actual conditions: geo(country_iso_code eq 'US')
                        conditions = right

                    result = {
                        "type": "geo_expr",
                        "field": field_name,
                        "type_hint": type_hint,
                        "field_mutators": field_mutators,
                        "conditions": self._build_ast(conditions, depth + 1) if conditions else None,
                    }

                    # Add geo parameters if any
                    if geo_params:
                        result["geo_params"] = geo_params

                    return result

                # Check for nslookup() expression
                elif isinstance(operator, str) and operator.lower() == "nslookup":
                    # This is a nslookup expression: field | nslookup(conditions OR params)
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(left)

                    conditions = None
                    nslookup_params = {}

                    # Check if this is actually a parameter masquerading as a condition
                    # Look for comparison operations where the field is a known parameter name
                    if (
                        isinstance(right, list)
                        and len(right) == 3
                        and isinstance(right[1], str)
                        and right[1] == "="
                        and isinstance(right[0], list)
                        and len(right[0]) == 1
                        and isinstance(right[0][0], str)
                        and right[0][0] in ["force", "servers", "append_field", "save", "types"]
                    ):
                        # This is a parameter parsed as a comparison: force = true
                        param_name = right[0][0]
                        param_value = right[2] if not isinstance(right[2], list) else right[2][0] if right[2] else None
                        # Handle types parameter which should be a list
                        if param_name == "types" and isinstance(right[2], list):
                            param_value = right[2]
                            # Unwrap if double-wrapped
                            if len(param_value) == 1 and isinstance(param_value[0], list):
                                param_value = param_value[0]
                        # Convert string boolean values to actual booleans
                        elif isinstance(param_value, str):
                            if param_value.lower() == "true":
                                param_value = True
                            elif param_value.lower() == "false":
                                param_value = False
                        nslookup_params[param_name] = param_value
                    else:
                        # This is actual conditions: nslookup(data contains 'example.com')
                        conditions = right

                    result = {
                        "type": "nslookup_expr",
                        "field": field_name,
                        "type_hint": type_hint,
                        "field_mutators": field_mutators,
                        "conditions": self._build_ast(conditions, depth + 1) if conditions else None,
                    }

                    # Add nslookup parameters if any
                    if nslookup_params:
                        result["nslookup_params"] = nslookup_params

                    return result

                if operator.lower() in ["and", "or"]:
                    # Logical operation
                    return {
                        "type": "logical_op",
                        "operator": operator.lower(),
                        "left": self._build_ast(left, depth + 1),
                        "right": self._build_ast(right, depth + 1),
                    }
                elif (
                    isinstance(operator, str)
                    and (operator.lower() == "not" or operator == "!")
                    and isinstance(right, str)
                    and right.lower() == "exists"
                ):
                    # Handle "field not exists" or "field ! exists" (negated unary operator)
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(left)
                    result = {
                        "type": "comparison",
                        "field": field_name,
                        "type_hint": type_hint,
                        "operator": "not_exists",
                        "value": None,
                    }
                    if field_mutators:
                        result["field_mutators"] = field_mutators
                    return result
                elif (
                    isinstance(operator, str)
                    and operator.lower() == "is"
                    and isinstance(right, str)
                    and right.lower() == "not"
                ):
                    # This will be handled in the 4-element case for "field is not value"
                    # Return unknown for now - should not normally reach here
                    return {"type": "unknown", "value": parsed}
                elif isinstance(operator, str) and operator == "!" and isinstance(right, str) and right.lower() == "is":
                    # Handle "field ! is value" - need to look ahead
                    # This is incomplete and will be handled in the 4-element case
                    # Return unknown for now - should not normally reach here
                    return {"type": "unknown", "value": parsed}
                else:
                    # Comparison operation
                    # Handle 'in' operator - can be "value in field(s)" or "field in [values]"
                    if isinstance(operator, str) and operator.lower() == "in":
                        # Check for old syntax: [field1, field2] in value
                        # The parser wraps list literals, so check for wrapped lists too
                        check_list = left
                        if isinstance(left, list) and len(left) == 1 and isinstance(left[0], list):
                            # Unwrap if it's [[field1, field2]]
                            check_list = left[0]

                        if isinstance(check_list, list) and len(check_list) > 1:
                            # Check if this is a list of identifiers (field names)
                            is_field_list = True
                            field_names = []
                            for item in check_list:
                                if isinstance(item, str):
                                    field_names.append(item)
                                else:
                                    is_field_list = False
                                    break

                            if is_field_list:
                                # Extract value for suggestion
                                value_str = right
                                if isinstance(right, list) and len(right) > 0:
                                    value_str = right[0]

                                raise TQLSyntaxError(
                                    "Field list on left side of 'in' operator is no longer supported",
                                    suggestions=[
                                        f'"{value_str}" in [{", ".join(field_names)}]',
                                        f"'{value_str}' in [{', '.join(field_names)}]",
                                    ],
                                    position=0,
                                )

                        # Check if right is a list of fields (value in [fields] syntax)
                        # Note: field in [values] is now handled by field_in_values grammar rule
                        # with __field_in_values__ marker, so this is only for value in [fields]
                        if isinstance(right, list) and len(right) > 0:
                            # Check if all elements are fields (typed_fields wrapped in lists)
                            # value in [field1, field2] produces right = [['field1'], ['field2']]
                            # field in ["val1", "val2"] produces right = ['val1', 'val2']
                            # (but field in [values] is now handled by __field_in_values__ marker)
                            is_field_list = all(
                                isinstance(item, list) and len(item) >= 1 and isinstance(item[0], str) for item in right
                            )

                            if is_field_list:
                                # This is "value in [field1, field2, ...]" format
                                value_extracted, value_mutators = self.ast_builder.extract_value_info(left)
                                # Create an OR expression for all fields
                                field_comparisons = []
                                for field in right:
                                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(field)
                                    comparison = {
                                        "type": "comparison",
                                        "field": field_name,
                                        "type_hint": type_hint,
                                        "operator": "in",
                                        "value": (
                                            [value_extracted]
                                            if not isinstance(value_extracted, list)
                                            else value_extracted
                                        ),
                                    }
                                    if field_mutators:
                                        comparison["field_mutators"] = field_mutators
                                    if value_mutators:
                                        comparison["value_mutators"] = value_mutators
                                    field_comparisons.append(comparison)

                                # Build OR expression
                                result = field_comparisons[0]
                                for i in range(1, len(field_comparisons)):
                                    result = {
                                        "type": "logical_op",
                                        "operator": "or",
                                        "left": result,
                                        "right": field_comparisons[i],
                                    }
                                return result

                        # For 'in' operator with single field, left is the value, right is field
                        # Extract the value from left
                        value_extracted, value_mutators = self.ast_builder.extract_value_info(left)

                        # Treat as standard "value in field" (single field)
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(right)
                        result = {
                            "type": "comparison",
                            "field": field_name,
                            "type_hint": type_hint,
                            "operator": "in",
                            "value": [value_extracted] if not isinstance(value_extracted, list) else value_extracted,
                        }
                        if field_mutators:
                            result["field_mutators"] = field_mutators
                        if value_mutators:
                            result["value_mutators"] = value_mutators
                        return result

                    if operator.lower() == "between":
                        # Between operator with list of values
                        if isinstance(right, list) and len(right) == 2:
                            field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(left)
                            result = {
                                "type": "comparison",
                                "field": field_name,
                                "type_hint": type_hint,
                                "operator": "between",
                                "value": right,
                            }
                            if field_mutators:
                                result["field_mutators"] = field_mutators
                            return result
                        else:
                            # Extract field name for error message
                            field_display = (
                                self.ast_builder.extract_field_info(left)[0] if isinstance(left, list) else left
                            )
                            raise TQLOperatorError(
                                f"'between' operator requires exactly 2 values, got {len(right) if isinstance(right, list) else 1}",
                                suggestions=[f"{field_display} between [18, 65]"],
                            )

                    # Check for negated operators (space-separated like "not in")
                    if isinstance(operator, list) and len(operator) == 2:
                        neg_word, base_op = operator
                        if neg_word.lower() == "not" or neg_word == "!":
                            field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(left)
                            value, value_mutators = self.ast_builder.extract_value_info(right)
                            # Handle 'not none' -> 'any' (double negative)
                            if base_op.lower() == "none":
                                normalized_operator = "any"
                            else:
                                normalized_operator = f"not_{base_op.lower()}"
                            result = {
                                "type": "comparison",
                                "field": field_name,
                                "type_hint": type_hint,
                                "operator": normalized_operator,
                                "value": value,
                            }
                            if field_mutators:
                                result["field_mutators"] = field_mutators
                            if value_mutators:
                                result["value_mutators"] = value_mutators
                            return result

                    # Check for bang operators (like !contains, !in, etc.)
                    if isinstance(operator, str) and operator.startswith("!") and operator != "!=":
                        # Bang operator - convert to not_operator (but not !=)
                        base_op = operator[1:].lower()
                        field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(left)
                        value, value_mutators = self.ast_builder.extract_value_info(right)
                        # Handle '!none' -> 'any' (double negative)
                        if base_op == "none":
                            normalized_operator = "any"
                        else:
                            normalized_operator = f"not_{base_op}"
                        result = {
                            "type": "comparison",
                            "field": field_name,
                            "type_hint": type_hint,
                            "operator": normalized_operator,
                            "value": value,
                        }
                        if field_mutators:
                            result["field_mutators"] = field_mutators
                        if value_mutators:
                            result["value_mutators"] = value_mutators
                        return result

                    # Standard "field op value" format
                    field_name, type_hint, field_mutators = self.ast_builder.extract_field_info(left)
                    value, value_mutators = self.ast_builder.extract_value_info(right)
                    # Normalize operator: convert 'none' to 'not_any'
                    normalized_operator = operator.lower()
                    if normalized_operator == "none":
                        normalized_operator = "not_any"

                    # Additional check for old 'in' syntax that got parsed differently
                    # If operator is 'in' and value is a list of identifiers, this might be the old syntax
                    if normalized_operator == "in" and isinstance(value, list) and len(value) > 1:
                        # Check if all items look like field names
                        all_identifiers = all(
                            isinstance(v, str) and v.replace(".", "").replace("_", "").isalnum() for v in value
                        )
                        if all_identifiers:
                            raise TQLSyntaxError(
                                "Field list in value syntax is no longer supported. Use value in [fields] instead",
                                suggestions=[
                                    f'"{field_name}" in [{", ".join(value)}]',
                                    f"'{field_name}' in [{', '.join(value)}]",
                                ],
                                position=0,
                            )

                    result = {
                        "type": "comparison",
                        "field": field_name,
                        "type_hint": type_hint,
                        "operator": normalized_operator,
                        "value": value,
                    }
                    if field_mutators:
                        result["field_mutators"] = field_mutators
                    if value_mutators:
                        result["value_mutators"] = value_mutators
                    return result
            else:
                # Handle longer lists (chained operations)
                # This happens with infixNotation for multiple AND/OR operations
                # The structure will be flattened, so we need to reconstruct the tree
                return self._build_chained_ast(parsed, depth + 1)
        else:
            # Single value - should already be a proper AST node
            if isinstance(parsed, dict):
                return parsed
            else:
                # This shouldn't happen, but handle gracefully
                raise TQLParseError(f"Unexpected parsed value type: {type(parsed)}")

        # This should be unreachable, but helps mypy understand all paths return
        raise AssertionError("Unreachable code in _build_ast")

    def _build_chained_ast(self, parsed_list: List[Any], depth: int = 0) -> Dict[str, Any]:
        """Build AST from chained operations (e.g., A AND B AND C).

        Args:
            parsed_list: List of alternating operands and operators
            depth: Current recursion depth (for DoS prevention)

        Returns:
            Dictionary representing the AST node

        Raises:
            TQLSyntaxError: If query depth exceeds maximum allowed depth
        """
        # Check depth limit to prevent stack overflow
        if depth > self.MAX_QUERY_DEPTH:
            raise TQLSyntaxError(
                f"Query depth exceeds maximum allowed depth of {self.MAX_QUERY_DEPTH}. "
                "Please simplify your query to reduce nesting.",
                position=0,
                query="",
                suggestions=["Reduce query nesting depth", "Split into multiple simpler queries"],
            )
        if len(parsed_list) < 3:
            # Not enough elements for a chained operation
            return {"type": "unknown", "value": parsed_list}

        # Start with the first operand
        result = self._build_ast(parsed_list[0], depth + 1)

        # Process pairs of (operator, operand)
        i = 1
        while i < len(parsed_list) - 1:
            operator = parsed_list[i]
            operand = parsed_list[i + 1]

            if operator.lower() in ["and", "or"]:
                result = {
                    "type": "logical_op",
                    "operator": operator.lower(),
                    "left": result,
                    "right": self._build_ast(operand, depth + 1),
                }
            else:
                # This shouldn't happen in a well-formed chained expression
                return {"type": "unknown", "value": parsed_list}

            i += 2

        return result

    def _build_stats_ast(self, parsed: List[Any]) -> Dict[str, Any]:  # noqa: C901
        """Build AST for stats expression.

        Args:
            parsed: Parsed stats expression [stats, aggregations, [by, fields]]

        Returns:
            Dictionary representing the stats AST
        """
        result: Dict[str, Any] = {"type": "stats_expr", "aggregations": [], "group_by": []}

        # Skip the 'stats' keyword
        i = 1

        # Process aggregations until we hit 'by' or end
        while i < len(parsed):
            if isinstance(parsed[i], str) and parsed[i].lower() == "by":
                # Start of group by clause
                i += 1
                break

            # Process aggregation
            if isinstance(parsed[i], str) and parsed[i].lower() == "count":
                # Special case for count(*)
                result["aggregations"].append({"function": "count", "field": "*", "alias": None})
                i += 1
            elif isinstance(parsed[i], list):
                # Check if this is a single aggregation with alias pattern
                # Pattern: [['func', 'field'], 'as', 'alias'] or ['count', 'as', 'alias']
                if (
                    len(parsed[i]) >= 3
                    and isinstance(parsed[i][1], str)
                    and parsed[i][1].lower() == "as"
                    and (
                        isinstance(parsed[i][0], list)
                        or (isinstance(parsed[i][0], str) and parsed[i][0].lower() == "count")
                    )
                ):
                    # This is a single aggregation with alias
                    items_to_process = [parsed[i]]
                else:
                    # This is a list of aggregations
                    items_to_process = parsed[i]
                for item in items_to_process:
                    agg_dict: Dict[str, Any] = {}

                    if isinstance(item, str) and item.lower() == "count":
                        # count(*) case
                        agg_dict["function"] = "count"
                        agg_dict["field"] = "*"
                        agg_dict["alias"] = None
                    elif (
                        isinstance(item, list)
                        and len(item) >= 3
                        and isinstance(item[0], str)
                        and item[0].lower() == "count"
                        and item[1].lower() == "as"
                    ):
                        # count(*) with alias: ['count', 'as', 'alias']
                        agg_dict["function"] = "count"
                        agg_dict["field"] = "*"
                        agg_dict["alias"] = item[2]
                    elif isinstance(item, list):
                        # Regular aggregation: [func, field, ...] or [[func, field], 'as', 'alias']
                        if len(item) >= 2 and isinstance(item[0], list):
                            # Aggregation with alias: [[func, field, ...], 'as', 'alias']
                            func_spec = item[0]
                            # Normalize function aliases
                            func = func_spec[0].lower()
                            if func == "avg":
                                func = "average"
                            elif func == "med":
                                func = "median"
                            elif func == "standard_deviation":
                                func = "std"
                            elif func in ["p", "pct", "percentiles"]:
                                func = "percentile"
                            elif func in ["pct_rank", "pct_ranks", "percentile_ranks"]:
                                func = "percentile_rank"
                            agg_dict["function"] = func
                            agg_dict["field"] = func_spec[1] if len(func_spec) > 1 else "*"

                            # Check for modifiers (top/bottom) or percentile values
                            if len(func_spec) >= 3:
                                # Check if it's a percentile function with values
                                func_name = agg_dict["function"]
                                if func_name in ["percentile", "percentiles", "p", "pct"]:
                                    # Handle percentile values - they come as separate elements
                                    percentile_values = []
                                    for j in range(2, len(func_spec)):
                                        if isinstance(func_spec[j], str) and func_spec[j].replace(".", "").isdigit():
                                            percentile_values.append(float(func_spec[j]))
                                        else:
                                            break  # Stop if we hit a non-numeric value
                                    agg_dict["percentile_values"] = percentile_values
                                elif func_name in ["percentile_rank", "percentile_ranks", "pct_rank", "pct_ranks"]:
                                    # Handle percentile rank values - they come as separate elements
                                    rank_values = []
                                    for j in range(2, len(func_spec)):
                                        if (
                                            isinstance(func_spec[j], str)
                                            and func_spec[j].replace(".", "").replace("-", "").isdigit()
                                        ):
                                            rank_values.append(float(func_spec[j]))
                                        else:
                                            break  # Stop if we hit a non-numeric value
                                    agg_dict["rank_values"] = rank_values
                                elif len(func_spec) >= 4 and func_spec[2].lower() in ["top", "bottom"]:
                                    agg_dict["modifier"] = func_spec[2].lower()
                                    agg_dict["limit"] = int(func_spec[3])

                            # Check for alias
                            if len(item) >= 3 and item[1].lower() == "as":
                                agg_dict["alias"] = item[2]
                            else:
                                agg_dict["alias"] = None
                        else:
                            # Simple aggregation: [func, field]
                            # Normalize function aliases
                            func = item[0].lower() if len(item) > 0 else "count"
                            if func == "avg":
                                func = "average"
                            elif func == "med":
                                func = "median"
                            elif func == "standard_deviation":
                                func = "std"
                            elif func in ["p", "pct", "percentiles"]:
                                func = "percentile"
                            elif func in ["pct_rank", "pct_ranks", "percentile_ranks"]:
                                func = "percentile_rank"
                            agg_dict["function"] = func
                            agg_dict["field"] = item[1] if len(item) > 1 else "*"
                            agg_dict["alias"] = None

                            # Check for modifiers or percentile values
                            if len(item) >= 3:
                                func_name = agg_dict["function"]
                                if func_name in ["percentile", "percentiles", "p", "pct"]:
                                    # Handle percentile values - they come as separate elements
                                    percentile_values = []
                                    for j in range(2, len(item)):
                                        if isinstance(item[j], str) and item[j].replace(".", "").isdigit():
                                            percentile_values.append(float(item[j]))
                                        else:
                                            break  # Stop if we hit a non-numeric value
                                    agg_dict["percentile_values"] = percentile_values
                                elif func_name in ["percentile_rank", "percentile_ranks", "pct_rank", "pct_ranks"]:
                                    # Handle percentile rank values - they come as separate elements
                                    rank_values = []
                                    for j in range(2, len(item)):
                                        if (
                                            isinstance(item[j], str)
                                            and item[j].replace(".", "").replace("-", "").isdigit()
                                        ):
                                            rank_values.append(float(item[j]))
                                        else:
                                            break  # Stop if we hit a non-numeric value
                                    agg_dict["rank_values"] = rank_values
                                elif len(item) >= 4 and item[2].lower() in ["top", "bottom"]:
                                    agg_dict["modifier"] = item[2].lower()
                                    agg_dict["limit"] = int(item[3])

                    if "function" in agg_dict:
                        result["aggregations"].append(agg_dict)

                i += 1
            else:
                i += 1

        # Process group by fields and visualization hint
        while i < len(parsed):
            if isinstance(parsed[i], str):
                if parsed[i] == "=>":
                    # Visualization hint found
                    i += 1
                    if i < len(parsed) and isinstance(parsed[i], str):
                        result["viz_hint"] = parsed[i].lower()
                    break
                elif parsed[i] not in ["by", ","]:
                    # This is a simple field name without bucket size - normalize to dict format
                    result["group_by"].append({"field": parsed[i], "bucket_size": None})
            elif isinstance(parsed[i], list):
                # This is a group by field with optional bucket size
                if len(parsed[i]) >= 1:
                    # Check for "top N" specification
                    if len(parsed[i]) >= 3 and parsed[i][1].lower() == "top":
                        field_spec = {"field": parsed[i][0], "bucket_size": int(parsed[i][2])}
                        result["group_by"].append(field_spec)
                    else:
                        # No bucket size specified - normalize to dict format
                        result["group_by"].append({"field": parsed[i][0], "bucket_size": None})
            i += 1

        return result


# Legacy function for backward compatibility
def parse_query(query: str):
    """Parse a TQL query string and return the parsed result.

    This function is kept for backward compatibility with existing code.
    New code should use TQLParser class directly.

    Args:
        query: The TQL query string.

    Returns:
        The pyparsing ParseResults.
    """
    parser = TQLParser()
    # For legacy compatibility, we return the raw pyparsing result
    parsed_result = parser.grammar.tql_expr.parseString(query, parseAll=True)
    return parsed_result
