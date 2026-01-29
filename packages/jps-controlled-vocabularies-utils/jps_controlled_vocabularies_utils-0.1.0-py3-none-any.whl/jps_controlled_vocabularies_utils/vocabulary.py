"""
Vocabulary model representing a complete controlled vocabulary with its terms.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from jps_controlled_vocabularies_utils.record import Record


class Vocabulary(BaseModel):
    """Represents a complete controlled vocabulary with metadata and terms.

    A vocabulary is a named collection of related terms, identified by a unique
    vocabulary_id and conforming to a specific schema version.

    Attributes:
        schema_version: Version of the YAML schema used (required).
        vocabulary_id: Unique identifier for this vocabulary (required).
        title: Human-readable title for the vocabulary (optional).
        description: Explanation of the vocabulary's purpose and scope (optional).
        terms: List of term records in this vocabulary.
        source_path: Path to the source file (populated by parser).
        metadata: Additional user-defined attributes.
    """

    schema_version: str
    vocabulary_id: str
    title: str | None = None
    description: str | None = None
    terms: list[Record] = Field(default_factory=list)
    source_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("schema_version", "vocabulary_id")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Ensure required string fields are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field must be non-empty")
        return v

    model_config = {
        "extra": "allow",  # Allow unknown fields for forward compatibility
    }
