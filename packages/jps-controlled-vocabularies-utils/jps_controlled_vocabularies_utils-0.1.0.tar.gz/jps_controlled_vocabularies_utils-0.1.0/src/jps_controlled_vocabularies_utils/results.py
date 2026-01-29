"""
Result models for validation operations.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(BaseModel):
    """Represents a single validation issue.

    Attributes:
        code: Machine-readable error code.
        severity: Severity level (error, warning, info).
        message: Human-readable description of the issue.
        location: Optional location information (file path, vocabulary_id, term key).
        hint: Optional suggestion for fixing the issue.
    """

    code: str
    severity: Severity
    message: str
    location: dict[str, Any] = Field(default_factory=dict)
    hint: str | None = None


class ValidationReport(BaseModel):
    """Result of registry integrity validation.

    Attributes:
        is_valid: Whether the registry passed all validation checks.
        issues: List of validation issues found.
        vocabularies_checked: Number of vocabularies validated.
        terms_checked: Total number of terms validated.
    """

    is_valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    vocabularies_checked: int = 0
    terms_checked: int = 0


class ValueValidationResult(BaseModel):
    """Result of validating a candidate value against a term's rules.

    Attributes:
        is_valid: Whether the value passed validation.
        normalized_value: Optional normalized version of the value.
        reasons: List of human-readable reasons for validation failure.
        allowed_values: The allowed values list (if applicable).
        pattern: The regex pattern (if applicable).
        term_key: Key of the term that was validated against.
        term_name: Display name of the term.
    """

    is_valid: bool
    normalized_value: str | None = None
    reasons: list[str] = Field(default_factory=list)
    allowed_values: list[str] | None = None
    pattern: str | None = None
    term_key: str | None = None
    term_name: str | None = None
