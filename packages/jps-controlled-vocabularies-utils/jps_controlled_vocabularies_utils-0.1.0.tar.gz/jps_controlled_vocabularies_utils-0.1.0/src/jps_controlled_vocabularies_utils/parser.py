"""
Parser for loading controlled vocabularies from YAML sources.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from jps_controlled_vocabularies_utils.exceptions import ParseError, SchemaError
from jps_controlled_vocabularies_utils.io.yaml_loader import YamlLoader
from jps_controlled_vocabularies_utils.record import Record
from jps_controlled_vocabularies_utils.registry import Registry
from jps_controlled_vocabularies_utils.utils.normalize import normalize_key
from jps_controlled_vocabularies_utils.vocabulary import Vocabulary

logger = logging.getLogger(__name__)


class KeyStrategy(str, Enum):
    """Strategy for handling term keys."""

    EXPLICIT_ONLY = "explicit_only"
    DERIVE_IF_MISSING = "derive_if_missing"


class ParserConfig:
    """Configuration for Parser behavior.

    Attributes:
        strict: Fail fast on first error (default True).
        allow_unknown_fields: Allow extra YAML fields (default True).
        key_strategy: How to handle missing term keys (default derive_if_missing).
        case_sensitive_search: Case sensitivity for term searches (default False).
        glob_patterns: File patterns for directory loading (default ['*.yml', '*.yaml']).
    """

    def __init__(
        self,
        strict: bool = True,
        allow_unknown_fields: bool = True,
        key_strategy: KeyStrategy = KeyStrategy.DERIVE_IF_MISSING,
        case_sensitive_search: bool = False,
        glob_patterns: list[str] | None = None,
    ) -> None:
        """Initialize parser configuration.

        Args:
            strict: Whether to fail fast on first error.
            allow_unknown_fields: Whether to allow extra YAML fields.
            key_strategy: Strategy for handling missing term keys.
            case_sensitive_search: Whether searches should be case-sensitive.
            glob_patterns: File patterns for directory loading.
        """
        self.strict = strict
        self.allow_unknown_fields = allow_unknown_fields
        self.key_strategy = key_strategy
        self.case_sensitive_search = case_sensitive_search
        self.glob_patterns = glob_patterns or ["*.yml", "*.yaml"]


class Parser:
    """Parser for loading controlled vocabularies from YAML sources.

    The Parser handles loading vocabularies from files, directories, and
    in-memory strings, with configurable behavior for key derivation and
    error handling.

    Example:
        >>> parser = Parser()
        >>> registry = parser.load_path("vocabularies/workflow.yml")
        >>> vocab = registry.get_vocabulary("workflow.system_terminology")
        >>> print(vocab.title)
    """

    def __init__(self, config: ParserConfig | None = None) -> None:
        """Initialize the parser with optional configuration.

        Args:
            config: Parser configuration (uses defaults if None).
        """
        self.config = config or ParserConfig()
        self.loader = YamlLoader()
        self.errors: list[dict[str, Any]] = []

    def load_path(self, path: str | Path) -> Registry:
        """Load vocabularies from a file or directory.

        Args:
            path: Path to a YAML file or directory containing YAML files.

        Returns:
            Registry containing loaded vocabularies.

        Raises:
            ParseError: If parsing fails in strict mode.
            SchemaError: If vocabulary schema is invalid in strict mode.
        """
        path_obj = Path(path)

        if path_obj.is_file():
            return self._load_single_file(path_obj)
        elif path_obj.is_dir():
            return self.load_directory(path_obj)
        else:
            raise ParseError(
                f"Path does not exist: {path}",
                context={"path": str(path)},
            )

    def load_directory(self, path: str | Path) -> Registry:
        """Load vocabularies from all YAML files in a directory (recursive).

        Args:
            path: Path to directory containing YAML files.

        Returns:
            Registry containing loaded vocabularies from all files.

        Raises:
            ParseError: If parsing fails in strict mode.
            SchemaError: If vocabulary schema is invalid in strict mode.
        """
        path_obj = Path(path)
        self.errors.clear()

        files = self.loader.discover_files(path_obj, self.config.glob_patterns)

        if not files:
            logger.warning(f"No YAML files found in {path_obj}")
            return Registry()

        registry = Registry()

        for file_path in files:
            try:
                file_registry = self._load_single_file(file_path)
                # Merge vocabularies into main registry
                for vocab_id, vocab in file_registry.vocabularies.items():
                    if vocab_id in registry.vocabularies:
                        error_msg = f"Duplicate vocabulary_id '{vocab_id}' found in {file_path}"
                        if self.config.strict:
                            raise SchemaError(
                                error_msg,
                                context={"vocabulary_id": vocab_id, "path": str(file_path)},
                            )
                        else:
                            self.errors.append(
                                {
                                    "type": "duplicate_vocabulary_id",
                                    "vocabulary_id": vocab_id,
                                    "path": str(file_path),
                                    "message": error_msg,
                                }
                            )
                            continue
                    registry.vocabularies[vocab_id] = vocab

            except (ParseError, SchemaError) as e:
                if self.config.strict:
                    raise
                else:
                    self.errors.append(
                        {
                            "type": "parse_error",
                            "path": str(file_path),
                            "message": str(e),
                            "context": getattr(e, "context", {}),
                        }
                    )
                    logger.error(f"Failed to load {file_path}: {e}")

        logger.info(
            f"Loaded {len(registry.vocabularies)} vocabularies from {len(files)} files"
        )
        return registry

    def load_string(self, yaml_text: str, source_name: str = "<memory>") -> Registry:
        """Load vocabularies from a YAML string.

        Args:
            yaml_text: YAML content as a string.
            source_name: Logical name for the source (for error messages).

        Returns:
            Registry containing loaded vocabularies.

        Raises:
            ParseError: If parsing fails in strict mode.
            SchemaError: If vocabulary schema is invalid in strict mode.
        """
        self.errors.clear()

        data, source_info = self.loader.load_string(yaml_text, source_name)
        vocabulary = self._parse_vocabulary(data, source_info.path)

        registry = Registry()
        registry.vocabularies[vocabulary.vocabulary_id] = vocabulary

        return registry

    def _load_single_file(self, file_path: Path) -> Registry:
        """Load a single vocabulary file.

        Args:
            file_path: Path to the YAML file.

        Returns:
            Registry containing the loaded vocabulary.

        Raises:
            ParseError: If parsing fails.
            SchemaError: If vocabulary schema is invalid.
        """
        data, source_info = self.loader.load_file(file_path)
        vocabulary = self._parse_vocabulary(data, source_info.path)

        registry = Registry()
        registry.vocabularies[vocabulary.vocabulary_id] = vocabulary

        return registry

    def _parse_vocabulary(self, data: dict[str, Any], source_path: str) -> Vocabulary:
        """Parse vocabulary data into a Vocabulary model.

        Args:
            data: Parsed YAML data dictionary.
            source_path: Path to the source file (for error messages).

        Returns:
            Vocabulary object.

        Raises:
            SchemaError: If vocabulary schema is invalid.
        """
        # Validate required fields
        if "schema_version" not in data:
            raise SchemaError(
                "Missing required field 'schema_version'",
                context={"path": source_path},
            )

        if "vocabulary_id" not in data:
            raise SchemaError(
                "Missing required field 'vocabulary_id'",
                context={"path": source_path},
            )

        # Validate schema version (MVP supports "1.0")
        schema_version = data["schema_version"]
        supported_versions = ["1.0"]
        if schema_version not in supported_versions:
            raise SchemaError(
                f"Unsupported schema_version '{schema_version}'. Supported: {supported_versions}",
                context={"path": source_path, "schema_version": schema_version},
            )

        # Parse terms
        terms_data = data.get("terms", [])
        if not isinstance(terms_data, list):
            raise SchemaError(
                f"Field 'terms' must be a list, got {type(terms_data).__name__}",
                context={"path": source_path},
            )

        terms = self._parse_terms(terms_data, source_path)

        # Build vocabulary
        try:
            vocab = Vocabulary(
                schema_version=data["schema_version"],
                vocabulary_id=data["vocabulary_id"],
                title=data.get("title"),
                description=data.get("description"),
                terms=terms,
                source_path=source_path,
                metadata=data.get("metadata", {}),
            )
            return vocab

        except PydanticValidationError as e:
            raise SchemaError(
                f"Vocabulary validation failed: {e}",
                context={"path": source_path, "errors": e.errors()},
            ) from e

    def _parse_terms(self, terms_data: list[dict[str, Any]], source_path: str) -> list[Record]:
        """Parse term records from YAML data.

        Args:
            terms_data: List of term dictionaries.
            source_path: Path to the source file (for error messages).

        Returns:
            List of Record objects.

        Raises:
            SchemaError: If term parsing fails.
        """
        terms: list[Record] = []
        seen_keys: set[str] = set()

        for idx, term_data in enumerate(terms_data):
            if not isinstance(term_data, dict):
                raise SchemaError(
                    f"Term at index {idx} must be a dictionary",
                    context={"path": source_path, "index": idx},
                )

            # Validate required fields
            if "name" not in term_data:
                raise SchemaError(
                    f"Term at index {idx} missing required field 'name'",
                    context={"path": source_path, "index": idx},
                )

            if "description" not in term_data:
                raise SchemaError(
                    f"Term at index {idx} missing required field 'description'",
                    context={"path": source_path, "index": idx},
                )

            # Handle key derivation
            key = term_data.get("key")
            if key is None:
                if self.config.key_strategy == KeyStrategy.DERIVE_IF_MISSING:
                    key = normalize_key(term_data["name"])
                    term_data["key"] = key
                else:
                    raise SchemaError(
                        f"Term at index {idx} missing required field 'key' (strategy: {self.config.key_strategy})",
                        context={"path": source_path, "index": idx, "name": term_data["name"]},
                    )

            # Check for duplicate keys
            if key in seen_keys:
                error_msg = f"Duplicate term key '{key}' at index {idx}"
                if self.config.strict:
                    raise SchemaError(
                        error_msg,
                        context={"path": source_path, "index": idx, "key": key},
                    )
                else:
                    self.errors.append(
                        {
                            "type": "duplicate_term_key",
                            "path": source_path,
                            "index": idx,
                            "key": key,
                            "message": error_msg,
                        }
                    )
                    continue  # Skip this term in non-strict mode
            seen_keys.add(key)

            # Parse record
            try:
                record = Record(**term_data)
                terms.append(record)
            except PydanticValidationError as e:
                raise SchemaError(
                    f"Term validation failed at index {idx}: {e}",
                    context={"path": source_path, "index": idx, "errors": e.errors()},
                ) from e

        return terms
