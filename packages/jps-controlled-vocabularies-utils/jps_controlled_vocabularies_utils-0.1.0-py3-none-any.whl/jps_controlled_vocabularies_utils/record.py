"""
Pydantic models for controlled vocabulary terms (records).
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class Record(BaseModel):
    """Represents an individual controlled vocabulary term.

    Each record must have at minimum a name and description. Additional
    fields provide metadata, validation rules, and relationship information.

    Attributes:
        name: Display name of the term (required).
        description: Explanation of the term's meaning and usage (required).
        key: Stable identifier for programmatic reference (optional; derived from name if absent).
        synonyms: Alternative names for this term.
        tags: Classification labels for organizing and filtering terms.
        deprecated: Whether this term is deprecated and should not be used.
        replaced_by: Key of the term that replaces this deprecated term.
        pattern: Regex pattern that values must match.
        allowed_values: List of exact values that are valid for this term.
        examples: Example values demonstrating proper usage.
        metadata: Additional user-defined attributes.
    """

    name: str
    description: str
    key: str | None = None
    synonyms: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    deprecated: bool = False
    replaced_by: str | None = None
    pattern: str | None = None
    allowed_values: list[str] | None = None
    examples: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name", "description")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Ensure name and description are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field must be non-empty")
        return v

    model_config = {
        "extra": "allow",  # Allow unknown fields for forward compatibility
    }
