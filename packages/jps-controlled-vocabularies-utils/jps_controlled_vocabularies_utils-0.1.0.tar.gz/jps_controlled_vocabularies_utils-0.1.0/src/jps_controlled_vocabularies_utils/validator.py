"""
Validator for controlled vocabularies and values.
"""

import logging
import re
from typing import Any

from jps_controlled_vocabularies_utils.exceptions import NotFoundError, ValidationError
from jps_controlled_vocabularies_utils.registry import Registry
from jps_controlled_vocabularies_utils.results import (
    Severity,
    ValidationIssue,
    ValidationReport,
    ValueValidationResult,
)

logger = logging.getLogger(__name__)


class Validator:
    """Validator for controlled vocabularies and values.

    The Validator performs two types of validation:
    1. Registry integrity: Validates vocabulary schema, uniqueness, and references.
    2. Value validation: Validates candidate values against term rules.

    Example:
        >>> validator = Validator()
        >>> report = validator.validate_registry(registry)
        >>> if not report.is_valid:
        ...     for issue in report.issues:
        ...         print(f"{issue.severity}: {issue.message}")
    """

    def __init__(self) -> None:
        """Initialize the validator."""
        self.supported_schema_versions = ["1.0"]

    def validate_registry(self, registry: Registry) -> ValidationReport:
        """Validate the integrity of a vocabulary registry.

        Performs the following checks:
        - Schema version is present and supported
        - Vocabulary IDs are unique (already enforced by Registry dict)
        - Terms have required fields
        - Term keys are unique within each vocabulary
        - Deprecated terms with replaced_by reference valid keys
        - Basic structural constraints

        Args:
            registry: The Registry to validate.

        Returns:
            ValidationReport with validation results and any issues found.
        """
        issues: list[ValidationIssue] = []
        vocab_count = 0
        term_count = 0

        for vocab_id, vocab in registry.vocabularies.items():
            vocab_count += 1

            # Validate schema version
            if not vocab.schema_version:
                issues.append(
                    ValidationIssue(
                        code="MISSING_SCHEMA_VERSION",
                        severity=Severity.ERROR,
                        message="Missing schema_version",
                        location={"vocabulary_id": vocab_id},
                        hint="Add schema_version field (e.g., '1.0')",
                    )
                )
            elif vocab.schema_version not in self.supported_schema_versions:
                issues.append(
                    ValidationIssue(
                        code="UNSUPPORTED_SCHEMA_VERSION",
                        severity=Severity.ERROR,
                        message=f"Unsupported schema_version: {vocab.schema_version}",
                        location={"vocabulary_id": vocab_id},
                        hint=f"Supported versions: {self.supported_schema_versions}",
                    )
                )

            # Validate vocabulary_id
            if not vocab.vocabulary_id:
                issues.append(
                    ValidationIssue(
                        code="MISSING_VOCABULARY_ID",
                        severity=Severity.ERROR,
                        message="Missing vocabulary_id",
                        location={"source_path": vocab.source_path or "unknown"},
                    )
                )

            # Validate terms exist (optional check - can allow empty vocabularies)
            if not vocab.terms:
                issues.append(
                    ValidationIssue(
                        code="EMPTY_VOCABULARY",
                        severity=Severity.WARNING,
                        message=f"Vocabulary '{vocab_id}' has no terms",
                        location={"vocabulary_id": vocab_id},
                    )
                )

            # Validate individual terms
            seen_keys: set[str] = set()
            term_keys: dict[str, str] = {}  # key -> term name mapping

            for idx, term in enumerate(vocab.terms):
                term_count += 1

                # Validate required fields
                if not term.name:
                    issues.append(
                        ValidationIssue(
                            code="MISSING_TERM_NAME",
                            severity=Severity.ERROR,
                            message=f"Term at index {idx} has empty name",
                            location={"vocabulary_id": vocab_id, "term_index": idx},
                        )
                    )

                if not term.description:
                    issues.append(
                        ValidationIssue(
                            code="MISSING_TERM_DESCRIPTION",
                            severity=Severity.ERROR,
                            message=f"Term '{term.name}' at index {idx} has empty description",
                            location={"vocabulary_id": vocab_id, "term_index": idx, "term_name": term.name},
                        )
                    )

                # Validate key uniqueness
                if term.key:
                    if term.key in seen_keys:
                        issues.append(
                            ValidationIssue(
                                code="DUPLICATE_TERM_KEY",
                                severity=Severity.ERROR,
                                message=f"Duplicate term key '{term.key}'",
                                location={
                                    "vocabulary_id": vocab_id,
                                    "term_key": term.key,
                                    "term_name": term.name,
                                },
                                hint=f"Previously defined for term '{term_keys.get(term.key)}'",
                            )
                        )
                    else:
                        seen_keys.add(term.key)
                        term_keys[term.key] = term.name

                # Validate replaced_by reference
                if term.deprecated and term.replaced_by:
                    # Will validate after all terms are processed
                    pass

            # Validate replaced_by references point to valid keys
            for term in vocab.terms:
                if term.deprecated and term.replaced_by:
                    if term.replaced_by not in term_keys:
                        issues.append(
                            ValidationIssue(
                                code="INVALID_REPLACED_BY",
                                severity=Severity.ERROR,
                                message=f"Term '{term.name}' references non-existent replacement key '{term.replaced_by}'",
                                location={
                                    "vocabulary_id": vocab_id,
                                    "term_key": term.key,
                                    "term_name": term.name,
                                    "replaced_by": term.replaced_by,
                                },
                                hint=f"Available keys: {', '.join(sorted(term_keys.keys()))}",
                            )
                        )

                # Validate regex pattern if present
                if term.pattern:
                    try:
                        re.compile(term.pattern)
                    except re.error as e:
                        issues.append(
                            ValidationIssue(
                                code="INVALID_REGEX_PATTERN",
                                severity=Severity.ERROR,
                                message=f"Term '{term.name}' has invalid regex pattern: {e}",
                                location={
                                    "vocabulary_id": vocab_id,
                                    "term_key": term.key,
                                    "term_name": term.name,
                                    "pattern": term.pattern,
                                },
                            )
                        )

        is_valid = all(issue.severity != Severity.ERROR for issue in issues)

        return ValidationReport(
            is_valid=is_valid,
            issues=issues,
            vocabularies_checked=vocab_count,
            terms_checked=term_count,
        )

    def validate_value(
        self,
        registry: Registry,
        vocabulary_id: str,
        term_key: str,
        value: str,
        allow_both: bool = True,
    ) -> ValueValidationResult:
        """Validate a candidate value against a term's validation rules.

        Validation rules checked (when present):
        - allowed_values: Value must be in the list (exact match)
        - pattern: Value must match the regex pattern

        Args:
            registry: The Registry containing vocabularies.
            vocabulary_id: ID of the vocabulary containing the term.
            term_key: Key of the term to validate against.
            value: The candidate value to validate.
            allow_both: If True, value must satisfy both allowed_values AND pattern.
                       If False, satisfying either is sufficient (OR semantics).

        Returns:
            ValueValidationResult with validation outcome and detailed reasons.

        Raises:
            NotFoundError: If the vocabulary or term is not found.
        """
        try:
            vocab = registry.get_vocabulary(vocabulary_id)
            term = registry.get_term(vocabulary_id, term_key)
        except NotFoundError as e:
            logger.error(f"Validation failed: {e}")
            raise

        reasons: list[str] = []
        passed_allowed = True
        passed_pattern = True

        # Check allowed_values
        if term.allowed_values is not None:
            if value not in term.allowed_values:
                passed_allowed = False
                reasons.append(
                    f"Value '{value}' is not in the allowed values list: {term.allowed_values}"
                )

        # Check pattern
        if term.pattern is not None:
            try:
                pattern = re.compile(term.pattern)
                if not pattern.match(value):
                    passed_pattern = False
                    reasons.append(f"Value '{value}' does not match required pattern: {term.pattern}")
            except re.error as e:
                reasons.append(f"Invalid regex pattern in term: {e}")
                passed_pattern = False

        # Determine validity based on allow_both setting
        if allow_both:
            # Must pass all applicable rules
            is_valid = passed_allowed and passed_pattern
        else:
            # Must pass at least one rule (if any rules exist)
            has_rules = term.allowed_values is not None or term.pattern is not None
            if not has_rules:
                is_valid = True  # No rules means always valid
            else:
                is_valid = passed_allowed or passed_pattern

        # Check if term is deprecated
        if term.deprecated:
            warning = f"Warning: Term '{term.name}' is deprecated."
            if term.replaced_by:
                warning += f" Use '{term.replaced_by}' instead."
            reasons.append(warning)

        return ValueValidationResult(
            is_valid=is_valid,
            normalized_value=value.strip() if is_valid else None,
            reasons=reasons,
            allowed_values=term.allowed_values,
            pattern=term.pattern,
            term_key=term.key,
            term_name=term.name,
        )

    def get_validation_hints(
        self,
        registry: Registry,
        vocabulary_id: str,
        term_key: str,
    ) -> dict[str, Any]:
        """Get validation hints for a term (allowed values, pattern, etc.).

        Args:
            registry: The Registry containing vocabularies.
            vocabulary_id: ID of the vocabulary containing the term.
            term_key: Key of the term to get hints for.

        Returns:
            Dictionary with validation hints.

        Raises:
            NotFoundError: If the vocabulary or term is not found.
        """
        term = registry.get_term(vocabulary_id, term_key)

        return {
            "term_key": term.key,
            "term_name": term.name,
            "description": term.description,
            "allowed_values": term.allowed_values,
            "pattern": term.pattern,
            "examples": term.examples,
            "deprecated": term.deprecated,
            "replaced_by": term.replaced_by,
        }
