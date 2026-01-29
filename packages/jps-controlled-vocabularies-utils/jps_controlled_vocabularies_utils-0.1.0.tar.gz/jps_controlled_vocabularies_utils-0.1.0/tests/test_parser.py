"""
Unit tests for the Parser class.
"""

from pathlib import Path

import pytest

from jps_controlled_vocabularies_utils.exceptions import NotFoundError, ParseError, SchemaError
from jps_controlled_vocabularies_utils.parser import KeyStrategy, Parser, ParserConfig


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def parser() -> Parser:
    """Create a default parser instance."""
    return Parser()


@pytest.fixture
def strict_parser() -> Parser:
    """Create a strict parser instance."""
    config = ParserConfig(strict=True)
    return Parser(config)


@pytest.fixture
def non_strict_parser() -> Parser:
    """Create a non-strict parser instance."""
    config = ParserConfig(strict=False)
    return Parser(config)


class TestParserLoadPath:
    """Tests for Parser.load_path() method."""

    def test_load_single_file(self, parser: Parser, fixtures_dir: Path) -> None:
        """Test loading a single vocabulary file."""
        file_path = fixtures_dir / "workflow_terminology.yml"
        registry = parser.load_path(file_path)

        assert len(registry.vocabularies) == 1
        assert "workflow.system_terminology" in registry.vocabularies

        vocab = registry.get_vocabulary("workflow.system_terminology")
        assert vocab.title == "Workflow and System Terminology"
        assert len(vocab.terms) == 5

    def test_load_file_with_key_derivation(self, parser: Parser, fixtures_dir: Path) -> None:
        """Test loading file where keys are derived from names."""
        file_path = fixtures_dir / "medical_diagnoses.yml"
        registry = parser.load_path(file_path)

        vocab = registry.get_vocabulary("medical.diagnoses")
        # Keys should be auto-derived
        term_keys = [term.key for term in vocab.terms]
        assert "hypertension" in term_keys
        assert "type_2_diabetes" in term_keys
        assert "asthma" in term_keys

    def test_load_nonexistent_file(self, parser: Parser) -> None:
        """Test loading a nonexistent file raises ParseError."""
        with pytest.raises(ParseError) as exc_info:
            parser.load_path("/nonexistent/file.yml")
        assert "not exist" in str(exc_info.value).lower()

    def test_load_directory(self, parser: Parser, fixtures_dir: Path) -> None:
        """Test loading all files from a directory."""
        # Use non-strict parser since fixtures contain invalid files
        config = ParserConfig(strict=False)
        non_strict_parser = Parser(config)
        registry = non_strict_parser.load_path(fixtures_dir)
        # Should load valid vocabularies (may skip invalid ones)
        assert len(registry.vocabularies) >= 2


class TestParserLoadDirectory:
    """Tests for Parser.load_directory() method."""

    def test_load_multiple_files(self, non_strict_parser: Parser, fixtures_dir: Path) -> None:
        """Test loading multiple vocabulary files."""
        registry = non_strict_parser.load_directory(fixtures_dir)

        # Should have loaded at least workflow and medical vocabularies
        vocab_ids = registry.list_vocabulary_ids()
        assert "workflow.system_terminology" in vocab_ids
        assert "medical.diagnoses" in vocab_ids

    def test_duplicate_vocabulary_id_strict(self, strict_parser: Parser, fixtures_dir: Path) -> None:
        """Test that duplicate vocabulary_id raises error in strict mode."""
        with pytest.raises(SchemaError) as exc_info:
            strict_parser.load_directory(fixtures_dir)
        assert "duplicate" in str(exc_info.value).lower()

    def test_duplicate_vocabulary_id_non_strict(
        self, non_strict_parser: Parser, fixtures_dir: Path
    ) -> None:
        """Test that duplicate vocabulary_id is collected as error in non-strict mode."""
        registry = non_strict_parser.load_directory(fixtures_dir)
        # Should have collected errors but continued
        assert len(non_strict_parser.errors) > 0


class TestParserLoadString:
    """Tests for Parser.load_string() method."""

    def test_load_valid_yaml_string(self, parser: Parser) -> None:
        """Test loading vocabulary from YAML string."""
        yaml_content = """
schema_version: "1.0"
vocabulary_id: "test.vocab"
title: "Test Vocabulary"
description: "A test vocabulary"
terms:
  - name: "Test Term"
    description: "A test term"
"""
        registry = parser.load_string(yaml_content, "test_source")
        assert len(registry.vocabularies) == 1
        assert "test.vocab" in registry.vocabularies

        vocab = registry.get_vocabulary("test.vocab")
        assert vocab.title == "Test Vocabulary"
        assert len(vocab.terms) == 1
        assert vocab.terms[0].name == "Test Term"

    def test_load_invalid_yaml_string(self, parser: Parser) -> None:
        """Test loading invalid YAML raises ParseError."""
        yaml_content = """
invalid: yaml: content:
  - with: [unclosed bracket
"""
        with pytest.raises(ParseError):
            parser.load_string(yaml_content)

    def test_load_empty_yaml_string(self, parser: Parser) -> None:
        """Test loading empty YAML raises ParseError."""
        with pytest.raises(ParseError):
            parser.load_string("")


class TestParserKeyStrategies:
    """Tests for different key derivation strategies."""

    def test_explicit_only_strategy_success(self, fixtures_dir: Path) -> None:
        """Test explicit_only strategy with explicit keys."""
        config = ParserConfig(key_strategy=KeyStrategy.EXPLICIT_ONLY)
        parser = Parser(config)

        file_path = fixtures_dir / "workflow_terminology.yml"
        registry = parser.load_path(file_path)

        vocab = registry.get_vocabulary("workflow.system_terminology")
        # All terms have explicit keys
        assert all(term.key is not None for term in vocab.terms)

    def test_explicit_only_strategy_failure(self, fixtures_dir: Path) -> None:
        """Test explicit_only strategy fails when keys are missing."""
        config = ParserConfig(key_strategy=KeyStrategy.EXPLICIT_ONLY, strict=True)
        parser = Parser(config)

        file_path = fixtures_dir / "medical_diagnoses.yml"
        # This file has no explicit keys, should fail
        with pytest.raises(SchemaError) as exc_info:
            parser.load_path(file_path)
        assert "missing required field 'key'" in str(exc_info.value).lower()

    def test_derive_if_missing_strategy(self, fixtures_dir: Path) -> None:
        """Test derive_if_missing strategy auto-generates keys."""
        config = ParserConfig(key_strategy=KeyStrategy.DERIVE_IF_MISSING)
        parser = Parser(config)

        file_path = fixtures_dir / "medical_diagnoses.yml"
        registry = parser.load_path(file_path)

        vocab = registry.get_vocabulary("medical.diagnoses")
        # All terms should have keys (derived or explicit)
        assert all(term.key is not None for term in vocab.terms)
        # Check specific derived key
        hypertension_term = next(t for t in vocab.terms if t.name == "Hypertension")
        assert hypertension_term.key == "hypertension"


class TestParserValidation:
    """Tests for parser validation of YAML structure."""

    def test_missing_schema_version(self, parser: Parser) -> None:
        """Test that missing schema_version raises SchemaError."""
        yaml_content = """
vocabulary_id: "test.vocab"
terms:
  - name: "Term"
    description: "Description"
"""
        with pytest.raises(SchemaError) as exc_info:
            parser.load_string(yaml_content)
        assert "schema_version" in str(exc_info.value).lower()

    def test_missing_vocabulary_id(self, parser: Parser) -> None:
        """Test that missing vocabulary_id raises SchemaError."""
        yaml_content = """
schema_version: "1.0"
terms:
  - name: "Term"
    description: "Description"
"""
        with pytest.raises(SchemaError) as exc_info:
            parser.load_string(yaml_content)
        assert "vocabulary_id" in str(exc_info.value).lower()

    def test_unsupported_schema_version(self, parser: Parser) -> None:
        """Test that unsupported schema version raises SchemaError."""
        yaml_content = """
schema_version: "99.0"
vocabulary_id: "test.vocab"
terms: []
"""
        with pytest.raises(SchemaError) as exc_info:
            parser.load_string(yaml_content)
        assert "unsupported" in str(exc_info.value).lower()

    def test_terms_not_a_list(self, parser: Parser) -> None:
        """Test that terms field must be a list."""
        yaml_content = """
schema_version: "1.0"
vocabulary_id: "test.vocab"
terms: "not a list"
"""
        with pytest.raises(SchemaError) as exc_info:
            parser.load_string(yaml_content)
        assert "list" in str(exc_info.value).lower()

    def test_term_missing_name(self, parser: Parser) -> None:
        """Test that term without name raises SchemaError."""
        yaml_content = """
schema_version: "1.0"
vocabulary_id: "test.vocab"
terms:
  - description: "No name field"
"""
        with pytest.raises(SchemaError) as exc_info:
            parser.load_string(yaml_content)
        assert "name" in str(exc_info.value).lower()

    def test_term_missing_description(self, parser: Parser) -> None:
        """Test that term without description raises SchemaError."""
        yaml_content = """
schema_version: "1.0"
vocabulary_id: "test.vocab"
terms:
  - name: "Term Name"
"""
        with pytest.raises(SchemaError) as exc_info:
            parser.load_string(yaml_content)
        assert "description" in str(exc_info.value).lower()

    def test_duplicate_term_keys(self, parser: Parser, fixtures_dir: Path) -> None:
        """Test that duplicate term keys raise SchemaError."""
        file_path = fixtures_dir / "invalid_vocab.yml"
        with pytest.raises(SchemaError) as exc_info:
            parser.load_path(file_path)
        assert "duplicate" in str(exc_info.value).lower()
