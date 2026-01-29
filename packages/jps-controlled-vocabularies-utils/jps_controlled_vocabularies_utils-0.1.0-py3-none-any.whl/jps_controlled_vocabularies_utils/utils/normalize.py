"""
Key normalization utilities.
"""

import re


def normalize_key(name: str) -> str:
    """Normalize a term name into a stable key identifier.

    Normalization rules:
    1. Convert to lowercase
    2. Trim leading and trailing whitespace
    3. Replace spaces and consecutive whitespace with underscore
    4. Remove non-alphanumeric/underscore characters

    Args:
        name: The term name to normalize.

    Returns:
        Normalized key string suitable for programmatic use.

    Examples:
        >>> normalize_key("Almost Ready")
        'almost_ready'
        >>> normalize_key("Ready-to-Go!")
        'readytogo'
        >>> normalize_key("  Multiple   Spaces  ")
        'multiple_spaces'
    """
    # Convert to lowercase and trim
    key = name.lower().strip()

    # Replace multiple spaces with single space first
    key = re.sub(r"\s+", " ", key)

    # Replace spaces with underscores
    key = key.replace(" ", "_")

    # Remove non-alphanumeric/underscore characters
    key = re.sub(r"[^a-z0-9_]", "", key)

    # Remove consecutive underscores
    key = re.sub(r"_+", "_", key)

    # Remove leading/trailing underscores
    key = key.strip("_")

    return key
