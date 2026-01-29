"""
Unit tests for the Validator class.
"""

from pathlib import Path

import pytest

from jps_controlled_vocabularies_utils.exceptions import NotFoundError
from jps_controlled_vocabularies_utils.parser import Parser, ParserConfig
from jps_controlled_vocabularies_utils.registry import Registry
from jps_controlled_vocabularies_utils.results import Severity
from jps_controlled_vocabularies_utils.validator import Validator


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def validator() -> Validator:
    """Create a validator instance."""
    return Validator()


@pytest.fixture
def valid_registry(fixtures_dir: Path) -> Registry:
    """Load a valid registry for testing."""
    parser = Parser()
    return parser.load_path(fixtures_dir / "workflow_terminology.yml")


@pytest.fixture
def invalid_registry(fixtures_dir: Path) -> Registry:
    """Load an invalid registry for testing validation errors."""
    # Use non-strict parser to load invalid vocab without raising during parse
    config = ParserConfig(strict=False)
    parser = Parser(config)
    return parser.load_path(fixtures_dir / "invalid_vocab.yml")


class TestValidateRegistryBasics:
    """Tests for basic registry validation."""

    def test_validate_valid_registry(
        self, validator: Validator, valid_registry: Registry
    ) -> None:
        """Test validation of a valid registry."""
        report = validator.validate_registry(valid_registry)
        # May have warnings but should be valid
        assert report.vocabularies_checked == 1
        assert report.terms_checked == 5

    def test_validate_empty_registry(self, validator: Validator) -> None:
        """Test validation of empty registry."""
        registry = Registry()
        report = validator.validate_registry(registry)
        assert report.is_valid
        assert report.vocabularies_checked == 0
        assert report.terms_checked == 0


class TestValidateRegistrySchemaVersion:
    """Tests for schema version validation."""

    def test_valid_schema_version(self, validator: Validator, valid_registry: Registry) -> None:
        """Test that valid schema version passes."""
        report = validator.validate_registry(valid_registry)
        # No schema version errors
        schema_errors = [i for i in report.issues if "SCHEMA_VERSION" in i.code]
        assert len(schema_errors) == 0

    def test_missing_schema_version(self, validator: Validator) -> None:
        """Test validation catches missing schema version."""
        yaml_content = """
vocabulary_id: "test.vocab"
terms:
  - name: "Term"
    description: "Description"
"""
        parser = Parser()
        # This should fail during parsing, not validation
        with pytest.raises(Exception):
            parser.load_string(yaml_content)


class TestValidateRegistryTerms:
    """Tests for term validation."""

    def test_duplicate_term_keys(
        self, validator: Validator, invalid_registry: Registry
    ) -> None:
        """Test that duplicate term keys were skipped during non-strict parsing."""
        # In non-strict mode, duplicates are skipped, so validator won't find them
        # Check that the parser errors were collected
        config = ParserConfig(strict=False)
        parser = Parser(config)
        registry = parser.load_path(Path(__file__).parent / "fixtures" / "invalid_vocab.yml")
        
        # Parser should have collected errors
        assert len(parser.errors) > 0
        
        # Validator should still pass on the loaded (de-duplicated) registry
        # since duplicates were removed during parsing
        report = validator.validate_registry(registry)
        # The registry itself is valid (duplicates removed), but check for invalid replaced_by
        invalid_ref_errors = [i for i in report.issues if i.code == "INVALID_REPLACED_BY"]
        assert len(invalid_ref_errors) > 0

    def test_invalid_replaced_by_reference(
        self, validator: Validator, invalid_registry: Registry
    ) -> None:
        """Test validation catches invalid replaced_by references."""
        report = validator.validate_registry(invalid_registry)
        assert not report.is_valid
        replacement_errors = [i for i in report.issues if i.code == "INVALID_REPLACED_BY"]
        assert len(replacement_errors) > 0


class TestValidateRegistryIssues:
    """Tests for validation issue reporting."""

    def test_issue_structure(self, validator: Validator, invalid_registry: Registry) -> None:
        """Test that validation issues have proper structure."""
        report = validator.validate_registry(invalid_registry)

        for issue in report.issues:
            assert hasattr(issue, "code")
            assert hasattr(issue, "severity")
            assert hasattr(issue, "message")
            assert hasattr(issue, "location")
            assert issue.severity in [Severity.ERROR, Severity.WARNING, Severity.INFO]

    def test_error_severity_makes_invalid(
        self, validator: Validator, invalid_registry: Registry
    ) -> None:
        """Test that ERROR severity makes registry invalid."""
        report = validator.validate_registry(invalid_registry)
        has_errors = any(i.severity == Severity.ERROR for i in report.issues)
        assert has_errors
        assert not report.is_valid


class TestValidateValue:
    """Tests for value validation against term rules."""

    def test_validate_allowed_value_valid(
        self, validator: Validator, valid_registry: Registry
    ) -> None:
        """Test validating a value in allowed_values list."""
        result = validator.validate_value(
            valid_registry,
            "workflow.system_terminology",
            "readiness_status.ready",
            "Ready",
        )
        assert result.is_valid
        assert result.term_key == "readiness_status.ready"
        assert result.term_name == "Ready"

    def test_validate_allowed_value_invalid(
        self, validator: Validator, valid_registry: Registry
    ) -> None:
        """Test validating a value not in allowed_values list."""
        result = validator.validate_value(
            valid_registry,
            "workflow.system_terminology",
            "readiness_status.ready",
            "Invalid Value",
        )
        assert not result.is_valid
        assert len(result.reasons) > 0
        assert "not in the allowed values" in result.reasons[0]

    def test_validate_pattern_valid(
        self, validator: Validator, valid_registry: Registry
    ) -> None:
        """Test validating a value matching regex pattern."""
        result = validator.validate_value(
            valid_registry,
            "workflow.system_terminology",
            "system.environment",
            "production",
        )
        assert result.is_valid

    def test_validate_pattern_invalid(
        self, validator: Validator, valid_registry: Registry
    ) -> None:
        """Test validating a value not matching regex pattern."""
        result = validator.validate_value(
            valid_registry,
            "workflow.system_terminology",
            "system.environment",
            "invalid_env",
        )
        assert not result.is_valid
        assert any("pattern" in reason.lower() for reason in result.reasons)

    def test_validate_deprecated_term(
        self, validator: Validator, valid_registry: Registry
    ) -> None:
        """Test validation includes deprecation warning."""
        result = validator.validate_value(
            valid_registry,
            "workflow.system_terminology",
            "deprecated_term",
            "Old Status",
        )
        # Should be valid but with deprecation warning
        deprecation_warnings = [r for r in result.reasons if "deprecated" in r.lower()]
        assert len(deprecation_warnings) > 0
        assert "readiness_status.ready" in deprecation_warnings[0]

    def test_validate_nonexistent_vocabulary(
        self, validator: Validator, valid_registry: Registry
    ) -> None:
        """Test validation with nonexistent vocabulary raises NotFoundError."""
        with pytest.raises(NotFoundError):
            validator.validate_value(
                valid_registry, "nonexistent.vocab", "term_key", "value"
            )

    def test_validate_nonexistent_term(
        self, validator: Validator, valid_registry: Registry
    ) -> None:
        """Test validation with nonexistent term raises NotFoundError."""
        with pytest.raises(NotFoundError):
            validator.validate_value(
                valid_registry,
                "workflow.system_terminology",
                "nonexistent_key",
                "value",
            )

    def test_validate_no_rules(self, validator: Validator) -> None:
        """Test validation passes when term has no validation rules."""
        yaml_content = """
schema_version: "1.0"
vocabulary_id: "test.vocab"
terms:
  - key: no_rules
    name: "No Rules Term"
    description: "Term without validation rules"
"""
        parser = Parser()
        registry = parser.load_string(yaml_content)

        result = validator.validate_value(registry, "test.vocab", "no_rules", "any value")
        assert result.is_valid


class TestGetValidationHints:
    """Tests for get_validation_hints method."""

    def test_get_hints(self, validator: Validator, valid_registry: Registry) -> None:
        """Test retrieving validation hints for a term."""
        hints = validator.get_validation_hints(
            valid_registry,
            "workflow.system_terminology",
            "readiness_status.ready",
        )

        assert hints["term_key"] == "readiness_status.ready"
        assert hints["term_name"] == "Ready"
        assert hints["description"] is not None
        assert hints["allowed_values"] is not None
        assert isinstance(hints["examples"], list)

    def test_get_hints_nonexistent_term(
        self, validator: Validator, valid_registry: Registry
    ) -> None:
        """Test getting hints for nonexistent term raises NotFoundError."""
        with pytest.raises(NotFoundError):
            validator.get_validation_hints(
                valid_registry, "workflow.system_terminology", "nonexistent"
            )
