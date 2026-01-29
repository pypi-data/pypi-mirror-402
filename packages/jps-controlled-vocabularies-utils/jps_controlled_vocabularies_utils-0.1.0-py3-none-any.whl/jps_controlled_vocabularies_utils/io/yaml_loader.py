"""
YAML file loading utilities.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

from jps_controlled_vocabularies_utils.exceptions import ParseError
from jps_controlled_vocabularies_utils.io.source import SourceInfo

logger = logging.getLogger(__name__)


class YamlLoader:
    """Handles loading and parsing of YAML vocabulary files.

    This loader uses safe_load to prevent code execution vulnerabilities
    and provides detailed error messages for debugging.
    """

    @staticmethod
    def load_file(file_path: Path) -> tuple[dict[str, Any], SourceInfo]:
        """Load a YAML vocabulary file.

        Args:
            file_path: Path to the YAML file.

        Returns:
            Tuple of (parsed YAML data, source info).

        Raises:
            ParseError: If the file cannot be read or parsed.
        """
        if not file_path.exists():
            raise ParseError(
                f"File not found: {file_path}",
                context={"path": str(file_path)},
            )

        if not file_path.is_file():
            raise ParseError(
                f"Path is not a file: {file_path}",
                context={"path": str(file_path)},
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                raise ParseError(
                    f"Empty or invalid YAML file: {file_path}",
                    context={"path": str(file_path)},
                )

            if not isinstance(data, dict):
                raise ParseError(
                    f"YAML file must contain a dictionary at root level: {file_path}",
                    context={"path": str(file_path), "type": type(data).__name__},
                )

            source_info = SourceInfo.from_path(file_path)
            logger.debug(f"Loaded vocabulary from {file_path}")

            return data, source_info

        except yaml.YAMLError as e:
            raise ParseError(
                f"Failed to parse YAML file: {file_path}",
                context={"path": str(file_path), "error": str(e)},
            ) from e
        except Exception as e:
            raise ParseError(
                f"Error reading file: {file_path}",
                context={"path": str(file_path), "error": str(e)},
            ) from e

    @staticmethod
    def load_string(yaml_text: str, source_name: str = "<memory>") -> tuple[dict[str, Any], SourceInfo]:
        """Load a YAML vocabulary from a string.

        Args:
            yaml_text: YAML content as a string.
            source_name: Logical name for the source.

        Returns:
            Tuple of (parsed YAML data, source info).

        Raises:
            ParseError: If the YAML cannot be parsed.
        """
        try:
            data = yaml.safe_load(yaml_text)

            if data is None:
                raise ParseError(
                    "Empty or invalid YAML string",
                    context={"source": source_name},
                )

            if not isinstance(data, dict):
                raise ParseError(
                    "YAML string must contain a dictionary at root level",
                    context={"source": source_name, "type": type(data).__name__},
                )

            source_info = SourceInfo.from_string(source_name)
            logger.debug(f"Loaded vocabulary from string: {source_name}")

            return data, source_info

        except yaml.YAMLError as e:
            raise ParseError(
                f"Failed to parse YAML string: {source_name}",
                context={"source": source_name, "error": str(e)},
            ) from e

    @staticmethod
    def discover_files(directory: Path, patterns: list[str]) -> list[Path]:
        """Discover YAML files in a directory matching glob patterns.

        Args:
            directory: Directory to search.
            patterns: List of glob patterns (e.g., ['*.yml', '*.yaml']).

        Returns:
            List of matching file paths, sorted alphabetically.

        Raises:
            ParseError: If the directory doesn't exist or isn't a directory.
        """
        if not directory.exists():
            raise ParseError(
                f"Directory not found: {directory}",
                context={"path": str(directory)},
            )

        if not directory.is_dir():
            raise ParseError(
                f"Path is not a directory: {directory}",
                context={"path": str(directory)},
            )

        files: list[Path] = []
        for pattern in patterns:
            files.extend(directory.rglob(pattern))

        # Filter to only regular files and sort
        files = [f for f in files if f.is_file()]
        files.sort()

        logger.info(f"Discovered {len(files)} YAML files in {directory}")
        return files
