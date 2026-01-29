"""
Unit tests for the Registry class.
"""

import pytest

from jps_controlled_vocabularies_utils.exceptions import NotFoundError
from jps_controlled_vocabularies_utils.parser import Parser
from jps_controlled_vocabularies_utils.registry import Registry


@pytest.fixture
def sample_registry() -> Registry:
    """Create a sample registry with test data."""
    yaml_content = """
schema_version: "1.0"
vocabulary_id: "test.vocab"
title: "Test Vocabulary"
description: "A test vocabulary for unit tests"
terms:
  - key: term1
    name: "First Term"
    description: "The first test term"
    synonyms: ["term one", "first"]
    tags: ["test"]
  - key: term2
    name: "Second Term"
    description: "The second test term"
    tags: ["test"]
  - key: search_term
    name: "Searchable Term"
    description: "A term for search testing"
    synonyms: ["findable"]
"""
    parser = Parser()
    return parser.load_string(yaml_content)


class TestRegistryBasics:
    """Tests for basic Registry operations."""

    def test_empty_registry(self) -> None:
        """Test creating an empty registry."""
        registry = Registry()
        assert len(registry.vocabularies) == 0
        assert registry.list_vocabulary_ids() == []

    def test_list_vocabulary_ids(self, sample_registry: Registry) -> None:
        """Test listing vocabulary IDs."""
        vocab_ids = sample_registry.list_vocabulary_ids()
        assert len(vocab_ids) == 1
        assert "test.vocab" in vocab_ids


class TestRegistryGetVocabulary:
    """Tests for Registry.get_vocabulary() method."""

    def test_get_existing_vocabulary(self, sample_registry: Registry) -> None:
        """Test retrieving an existing vocabulary."""
        vocab = sample_registry.get_vocabulary("test.vocab")
        assert vocab.vocabulary_id == "test.vocab"
        assert vocab.title == "Test Vocabulary"

    def test_get_nonexistent_vocabulary(self, sample_registry: Registry) -> None:
        """Test retrieving nonexistent vocabulary raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc_info:
            sample_registry.get_vocabulary("nonexistent.vocab")
        assert "not found" in str(exc_info.value).lower()
        assert "nonexistent.vocab" in str(exc_info.value)


class TestRegistryListTerms:
    """Tests for Registry.list_terms() method."""

    def test_list_terms(self, sample_registry: Registry) -> None:
        """Test listing all terms in a vocabulary."""
        terms = sample_registry.list_terms("test.vocab")
        assert len(terms) == 3
        term_names = [term.name for term in terms]
        assert "First Term" in term_names
        assert "Second Term" in term_names

    def test_list_terms_nonexistent_vocabulary(self, sample_registry: Registry) -> None:
        """Test listing terms for nonexistent vocabulary raises NotFoundError."""
        with pytest.raises(NotFoundError):
            sample_registry.list_terms("nonexistent.vocab")


class TestRegistryGetTerm:
    """Tests for Registry.get_term() method."""

    def test_get_existing_term(self, sample_registry: Registry) -> None:
        """Test retrieving an existing term by key."""
        term = sample_registry.get_term("test.vocab", "term1")
        assert term.key == "term1"
        assert term.name == "First Term"

    def test_get_nonexistent_term(self, sample_registry: Registry) -> None:
        """Test retrieving nonexistent term raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc_info:
            sample_registry.get_term("test.vocab", "nonexistent_key")
        assert "not found" in str(exc_info.value).lower()
        assert "nonexistent_key" in str(exc_info.value)

    def test_get_term_from_nonexistent_vocabulary(self, sample_registry: Registry) -> None:
        """Test retrieving term from nonexistent vocabulary raises NotFoundError."""
        with pytest.raises(NotFoundError):
            sample_registry.get_term("nonexistent.vocab", "term1")


class TestRegistrySearchTerms:
    """Tests for Registry.search_terms() method."""

    def test_search_exact_match(self, sample_registry: Registry) -> None:
        """Test exact match search."""
        results = sample_registry.search_terms(
            "test.vocab", "First Term", search_mode="exact"
        )
        assert len(results) == 1
        assert results[0].name == "First Term"

    def test_search_prefix_match(self, sample_registry: Registry) -> None:
        """Test prefix match search."""
        results = sample_registry.search_terms("test.vocab", "First", search_mode="prefix")
        assert len(results) == 1
        assert results[0].name == "First Term"

    def test_search_contains_match(self, sample_registry: Registry) -> None:
        """Test contains match search."""
        results = sample_registry.search_terms("test.vocab", "Term", search_mode="contains")
        # Should match all three terms as they all contain "Term"
        assert len(results) == 3

    def test_search_case_insensitive(self, sample_registry: Registry) -> None:
        """Test case-insensitive search (default)."""
        results = sample_registry.search_terms(
            "test.vocab", "first term", case_sensitive=False
        )
        assert len(results) == 1
        assert results[0].name == "First Term"

    def test_search_case_sensitive(self, sample_registry: Registry) -> None:
        """Test case-sensitive search."""
        results = sample_registry.search_terms(
            "test.vocab", "first term", case_sensitive=True
        )
        # Should not match "First Term" due to case difference
        assert len(results) == 0

    def test_search_by_key(self, sample_registry: Registry) -> None:
        """Test search matches term keys."""
        results = sample_registry.search_terms("test.vocab", "term1", search_mode="exact")
        assert len(results) == 1
        assert results[0].key == "term1"

    def test_search_by_synonym(self, sample_registry: Registry) -> None:
        """Test search matches synonyms."""
        results = sample_registry.search_terms(
            "test.vocab", "term one", search_mode="exact"
        )
        assert len(results) == 1
        assert results[0].name == "First Term"

    def test_search_no_results(self, sample_registry: Registry) -> None:
        """Test search with no matching results."""
        results = sample_registry.search_terms(
            "test.vocab", "nonexistent", search_mode="exact"
        )
        assert len(results) == 0

    def test_search_nonexistent_vocabulary(self, sample_registry: Registry) -> None:
        """Test search in nonexistent vocabulary raises NotFoundError."""
        with pytest.raises(NotFoundError):
            sample_registry.search_terms("nonexistent.vocab", "term")
