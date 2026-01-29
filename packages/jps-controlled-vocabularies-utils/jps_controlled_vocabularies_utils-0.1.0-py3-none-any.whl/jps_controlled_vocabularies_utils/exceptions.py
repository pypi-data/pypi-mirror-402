"""
Custom exceptions for controlled vocabularies package.
"""

from typing import Any


class ControlledVocabularyError(Exception):
    """Base exception for controlled vocabulary operations."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message describing what went wrong.
            context: Optional dictionary with additional context (path, line, field).
        """
        super().__init__(message)
        self.context = context or {}


class ParseError(ControlledVocabularyError):
    """Exception raised when YAML parsing fails."""

    pass


class SchemaError(ControlledVocabularyError):
    """Exception raised when vocabulary schema validation fails."""

    pass


class ValidationError(ControlledVocabularyError):
    """Exception raised when vocabulary or value validation fails."""

    pass


class NotFoundError(ControlledVocabularyError):
    """Exception raised when a vocabulary or term is not found."""

    pass
