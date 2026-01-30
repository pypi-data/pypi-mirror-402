"""AST building utilities for TQL parser."""

from typing import Any, Dict, List, Tuple, Union


class ASTBuilder:
    """Builds Abstract Syntax Tree from parsed TQL expressions."""

    def extract_field_info(self, field_spec: Any) -> Tuple[str, Union[str, None], List[Dict[str, Any]]]:  # noqa: C901
        """Extract field name, optional type hint, and mutators from field specification.

        Args:
            field_spec: Field specification that may include type hint and mutators

        Returns:
            Tuple of (field_name, type_hint or None, list of mutators)
        """
        if isinstance(field_spec, list):
            field_name = field_spec[0]
            type_hint = None
            mutators = []

            # Process remaining elements
            i = 1
            while i < len(field_spec):
                item = field_spec[i]
                if isinstance(item, str) and item.lower() in [
                    "number",
                    "int",
                    "float",
                    "decimal",
                    "date",
                    "array",
                    "bool",
                    "boolean",
                    "geo",
                    "object",
                    "string",
                ]:
                    # This is a type hint
                    type_hint = item.lower()
                elif isinstance(item, list):
                    # This is a mutator [name, params] or [name]
                    if len(item) >= 1:
                        mutator_dict = {"name": item[0]}
                        if len(item) > 1 and isinstance(item[1], list):
                            # Has parameters
                            params = []
                            for param in item[1]:
                                if isinstance(param, list) and len(param) == 2:
                                    # Named parameter: [name, value]
                                    params.append(param)
                                elif isinstance(param, str):
                                    # Positional parameter - handle based on mutator type
                                    mutator_name = item[0].lower()
                                    if mutator_name == "split":
                                        params.append(["delimiter", param])
                                    elif mutator_name == "replace":
                                        # For replace, first positional is 'find', second is 'replace'
                                        if not params or all(p[0] != "find" for p in params):
                                            params.append(["find", param])
                                        elif all(p[0] != "replace" for p in params):
                                            params.append(["replace", param])
                                        else:
                                            # Too many positional params
                                            params.append(["_positional", param])
                                    else:
                                        # For other mutators, use first positional as unnamed param
                                        params.append(["_positional", param])
                            if params:
                                mutator_dict["params"] = params
                        mutators.append(mutator_dict)
                i += 1

            return field_name, type_hint, mutators
        else:
            # Just field name as string
            return field_spec, None, []

    def extract_value_info(self, value_spec: Any) -> Tuple[Any, List[Dict[str, Any]]]:  # noqa: C901
        """Extract value and optional mutators from value specification.

        Args:
            value_spec: Value specification that may include mutators

        Returns:
            Tuple of (value, list of mutators)
        """
        if isinstance(value_spec, list):
            # Check if this is a list literal (all elements are simple values)
            # vs a value with mutators (first element is value, rest are mutator specs)
            if len(value_spec) == 0:
                return value_spec, []

            # If it's a single-element list containing a list, unwrap it
            if len(value_spec) == 1 and isinstance(value_spec[0], list):
                return value_spec[0], []

            # If it's a single-element list containing a simple value, unwrap it
            if len(value_spec) == 1 and not isinstance(value_spec[0], list):
                return value_spec[0], []

            # Special case: if first element is a list and rest are mutators,
            # this is a list literal with mutators
            if isinstance(value_spec[0], list) and all(
                isinstance(value_spec[0][i], str) for i in range(len(value_spec[0]))
            ):
                # First element is a list of strings
                has_mutators = False
                for i in range(1, len(value_spec)):
                    item = value_spec[i]
                    if isinstance(item, list) and len(item) >= 1 and isinstance(item[0], str):
                        # This looks like a mutator spec
                        has_mutators = True
                        break

                if has_mutators:
                    # This is a list literal with mutators
                    value = value_spec[0]
                    mutators = []
                    # Process remaining elements as mutators
                    i = 1
                    while i < len(value_spec):
                        item = value_spec[i]
                        if isinstance(item, list):
                            # This is a mutator [name, params] or [name]
                            if len(item) >= 1:
                                mutator_dict = {"name": item[0]}
                                if len(item) > 1 and isinstance(item[1], list):
                                    # Has parameters
                                    params = []
                                    for param in item[1]:
                                        if isinstance(param, list) and len(param) == 2:
                                            # Named parameter: [name, value]
                                            params.append(param)
                                        elif isinstance(param, str):
                                            # Positional parameter - handle based on mutator type
                                            mutator_name = item[0].lower()
                                            if mutator_name == "split":
                                                params.append(["delimiter", param])
                                            elif mutator_name == "replace":
                                                # For replace, first positional is 'find', second is 'replace'
                                                if not params or all(p[0] != "find" for p in params):
                                                    params.append(["find", param])
                                                elif all(p[0] != "replace" for p in params):
                                                    params.append(["replace", param])
                                                else:
                                                    # Too many positional params
                                                    params.append(["_positional", param])
                                            else:
                                                # For other mutators, use first positional as unnamed param
                                                params.append(["_positional", param])
                                    if params:
                                        mutator_dict["params"] = params
                                mutators.append(mutator_dict)
                        i += 1
                    return value, mutators

            # Check if any element after the first looks like a mutator
            has_mutators = False
            for i in range(1, len(value_spec)):
                item = value_spec[i]
                if isinstance(item, list) and len(item) >= 1 and isinstance(item[0], str):
                    # This looks like a mutator spec
                    has_mutators = True
                    break

            if not has_mutators:
                # This is a list literal, return it as-is
                return value_spec, []

            # This is a value with mutators
            value = value_spec[0]
            mutators = []

            # Process remaining elements as mutators
            i = 1
            while i < len(value_spec):
                item = value_spec[i]
                if isinstance(item, list):
                    # This is a mutator [name, params] or [name]
                    if len(item) >= 1:
                        mutator_dict = {"name": item[0]}
                        if len(item) > 1 and isinstance(item[1], list):
                            # Has parameters
                            params = []
                            for param in item[1]:
                                if isinstance(param, list) and len(param) == 2:
                                    params.append(param)
                            if params:
                                mutator_dict["params"] = params
                        mutators.append(mutator_dict)
                i += 1

            return value, mutators
        else:
            # Just the value itself, no mutators
            return value_spec, []
