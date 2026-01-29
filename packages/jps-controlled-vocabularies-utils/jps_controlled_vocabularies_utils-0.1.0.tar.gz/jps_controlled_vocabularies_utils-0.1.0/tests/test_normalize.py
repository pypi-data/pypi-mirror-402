"""
Unit tests for the normalize utility functions.
"""

import pytest

from jps_controlled_vocabularies_utils.utils.normalize import normalize_key


class TestNormalizeKey:
    """Tests for the normalize_key function."""

    def test_simple_name(self) -> None:
        """Test normalization of a simple name."""
        assert normalize_key("Ready") == "ready"

    def test_name_with_spaces(self) -> None:
        """Test normalization of name with spaces."""
        assert normalize_key("Almost Ready") == "almost_ready"

    def test_name_with_multiple_spaces(self) -> None:
        """Test normalization with multiple consecutive spaces."""
        assert normalize_key("Multiple   Spaces") == "multiple_spaces"

    def test_name_with_leading_trailing_spaces(self) -> None:
        """Test normalization with leading/trailing whitespace."""
        assert normalize_key("  Trimmed  ") == "trimmed"

    def test_name_with_special_characters(self) -> None:
        """Test normalization removes special characters."""
        assert normalize_key("Ready-to-Go!") == "readytogo"
        assert normalize_key("Test@123#456") == "test123456"

    def test_name_with_underscores(self) -> None:
        """Test that underscores are preserved."""
        assert normalize_key("already_normalized") == "already_normalized"

    def test_name_with_mixed_case(self) -> None:
        """Test case conversion."""
        assert normalize_key("MixedCaseString") == "mixedcasestring"

    def test_empty_string(self) -> None:
        """Test normalization of empty string."""
        assert normalize_key("") == ""

    def test_whitespace_only(self) -> None:
        """Test normalization of whitespace-only string."""
        assert normalize_key("   ") == ""

    def test_complex_example(self) -> None:
        """Test complex normalization scenario."""
        assert normalize_key("  Almost   Ready-ish! ") == "almost_readyish"

    def test_numbers_preserved(self) -> None:
        """Test that numbers are preserved."""
        assert normalize_key("Status 123") == "status_123"

    def test_unicode_characters_removed(self) -> None:
        """Test that unicode characters are removed."""
        assert normalize_key("café") == "caf"
        assert normalize_key("naïve") == "nave"
