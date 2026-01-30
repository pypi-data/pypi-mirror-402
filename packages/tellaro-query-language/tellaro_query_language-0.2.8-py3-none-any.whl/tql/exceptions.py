"""TQL exception classes.

This module defines custom exceptions used throughout the TQL library.
"""

from typing import Any, Dict, List, Optional


class TQLError(Exception):
    """Base exception class for all TQL errors."""

    def __init__(  # noqa: B042
        self,
        message: str,
        position: Optional[int] = None,
        query: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize TQL error with enhanced context.

        Args:
            message: Primary error message
            position: Character position where error occurred
            query: Original query string
            suggestions: List of suggestions or examples
            context: Additional context information
        """
        super().__init__(message)
        self.position = position
        self.query = query
        self.suggestions = suggestions or []
        self.context = context or {}

    def __str__(self) -> str:
        """Format error message with position and suggestions."""
        lines = []

        # Main error message with position
        if self.position is not None:
            lines.append(f"{self.__class__.__name__} at position {self.position}: {super().__str__()}")

            # Show query with position indicator
            if self.query:
                lines.append(f"Query: {self.query}")
                # Add position indicator
                if 0 <= self.position <= len(self.query):
                    lines.append(" " * (7 + self.position) + "^")
        else:
            lines.append(f"{self.__class__.__name__}: {super().__str__()}")

        # Add suggestions
        if self.suggestions:
            if len(self.suggestions) == 1:
                lines.append(f"Did you mean: {self.suggestions[0]}?")
            else:
                lines.append("Suggestions:")
                for suggestion in self.suggestions:
                    lines.append(f"  - {suggestion}")

        return "\n".join(lines)


class TQLSyntaxError(TQLError):
    """Raised when TQL query has syntax errors."""


class TQLParseError(TQLError):
    """Raised when there's an error parsing a TQL query."""


class TQLTypeError(TQLError):
    """Raised when an operator is incompatible with a field's data type."""

    def __init__(  # noqa: B042
        self, field: str, field_type: str, operator: str, valid_operators: Optional[List[str]] = None, **kwargs
    ):
        """Initialize type error with field and operator context."""
        message = f"Cannot apply operator '{operator}' to field '{field}' of type '{field_type}'. "

        if operator in [">", ">=", "<", "<="] and field_type in ["keyword", "text"]:
            message += (
                "Numeric comparison operators (>, >=, <, <=) require numeric field types "
                "(integer, long, float, double). "
            )
            if valid_operators:
                message += f"Consider using: {', '.join(valid_operators)} for {field_type} fields."
        elif valid_operators:
            message += f"Valid operators for {field_type} fields: {', '.join(valid_operators)}"

        super().__init__(message, **kwargs)
        self.field = field
        self.field_type = field_type
        self.operator = operator
        self.valid_operators = valid_operators


class TQLFieldError(TQLError):
    """Raised when referencing invalid or non-existent fields."""

    def __init__(self, field: str, available_fields: Optional[List[str]] = None, **kwargs):  # noqa: B042
        """Initialize field error with available fields context."""
        message = f"Unknown field '{field}'."

        if available_fields:
            message += f"\nAvailable fields: {', '.join(sorted(available_fields))}"

            # Simple suggestion based on string similarity
            suggestions = []
            field_lower = field.lower()
            for available in available_fields:
                if field_lower in available.lower() or available.lower() in field_lower:
                    suggestions.append(f"{available}")

            if suggestions and "suggestions" not in kwargs:
                kwargs["suggestions"] = suggestions[:3]  # Limit to top 3 suggestions

        super().__init__(message, **kwargs)
        self.field = field
        self.available_fields = available_fields


class TQLValueError(TQLError):
    """Raised when provided values don't match expected formats."""


class TQLOperatorError(TQLError):
    """Raised when operators are used incorrectly."""


class TQLExecutionError(TQLError):
    """Raised when there's an error executing a TQL query."""


class TQLValidationError(TQLError):
    """Raised when a TQL query fails validation."""


class TQLUnsupportedOperationError(TQLError):
    """Raised when attempting to use unsupported operations with a backend."""


class TQLConfigError(TQLError):
    """Raised when there's a configuration error."""


class TQLMutatorError(TQLError):
    """Raised when there's an error applying a mutator."""

    def __init__(  # noqa: B042
        self, mutator_name: str, field_name: str, value_type: str, message: Optional[str] = None, **kwargs
    ):
        """Initialize mutator error with context."""
        if not message:
            message = (
                f"Cannot apply mutator '{mutator_name}' to field '{field_name}' with value of type '{value_type}'."
            )

        super().__init__(message, **kwargs)
        self.mutator_name = mutator_name
        self.field_name = field_name
        self.value_type = value_type
