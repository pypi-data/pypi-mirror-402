"""Error analysis utilities for TQL parser."""

from typing import List, Tuple


class ErrorAnalyzer:
    """Analyzes parse errors to provide helpful feedback."""

    @staticmethod
    def analyze_parse_error(query: str, position: int, error_str: str) -> Tuple[str, List[str]]:  # noqa: C901
        """Analyze parse error to provide helpful feedback.

        Args:
            query: The original query string
            position: Character position where error occurred
            error_str: The original error string from pyparsing

        Returns:
            Tuple of (error message, list of suggestions)
        """
        suggestions = []

        # Check for invalid operators first (before position-specific checks)
        if "==" in query:
            pos = query.find("==")
            return f"Invalid operator '==' at position {pos}. Use '=' for equality", [query.replace("==", "=")]

        # Check if query ends with an operator (special case)
        if query.rstrip().endswith(("=", "!=", ">", "<", ">=", "<=", "contains", "startswith", "endswith")):
            # Find the operator
            for op in [">=", "<=", "!=", "contains", "startswith", "endswith", "=", ">", "<"]:
                if query.rstrip().endswith(op):
                    return f"Expected value after operator '{op}'", [f'Examples: field {op} "value"']

        # Get context around error position
        if position >= 0 and position < len(query):
            # Look at what's around the error position
            # start = max(0, position - 10)  # Not used
            # end = min(len(query), position + 10)  # Not used
            # context = query[start:end]  # Not currently used

            # Check for common issues
            before = query[:position].strip()
            after = query[position:].strip()

            # Missing operator after field
            if (
                before
                and after
                and not any(op in before[-10:] for op in ["=", "!=", ">", "<", ">=", "<=", "in", "contains", "exists"])
            ):
                # Likely missing operator
                last_word = before.split()[-1] if before.split() else ""
                suggestions = [
                    f'{last_word} = "{after.split()[0]}"' if after else f"{last_word} exists",
                ]
                if after:
                    suggestions.append(f'{last_word} contains "{after.split()[0]}"')
                return f"Expected operator after field '{last_word}'", suggestions

            # Unclosed quote
            if query.count('"') % 2 != 0:
                last_quote_pos = query.rfind('"', 0, position)
                if last_quote_pos >= 0:
                    return f"Unterminated string literal starting at position {last_quote_pos}", []

            if query.count("'") % 2 != 0:
                last_quote_pos = query.rfind("'", 0, position)
                if last_quote_pos >= 0:
                    return f"Unterminated string literal starting at position {last_quote_pos}", []

            # Missing value after operator
            tokens = before.split()
            if tokens and tokens[-1] in ["=", "!=", ">", "<", ">=", "<=", "contains", "startswith", "endswith"]:
                return f"Expected value after operator '{tokens[-1]}'", [
                    f'Examples: {tokens[-2] if len(tokens) > 1 else "field"} {tokens[-1]} "value"'
                ]

        # Default message if we can't determine specific issue
        all_operators = [
            "=",
            "!=",
            ">",
            "<",
            ">=",
            "<=",
            "contains",
            "startswith",
            "endswith",
            "in",
            "not in",
            "between",
            "not between",
            "cidr",
            "not cidr",
            "exists",
            "not exists",
            "regexp",
            "not regexp",
        ]
        return "Invalid syntax", [f"Valid operators: {', '.join(all_operators)}"]
