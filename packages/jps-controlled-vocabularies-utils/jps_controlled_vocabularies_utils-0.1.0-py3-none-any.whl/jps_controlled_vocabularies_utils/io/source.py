"""
Source information tracking for vocabulary files.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SourceInfo:
    """Metadata about a vocabulary source file.

    Attributes:
        path: Path to the source file (absolute or relative).
        name: Human-readable name (typically filename).
        modified_time: Last modification timestamp (optional).
    """

    path: str
    name: str
    modified_time: datetime | None = None

    @classmethod
    def from_path(cls, file_path: Path) -> "SourceInfo":
        """Create SourceInfo from a file path.

        Args:
            file_path: Path to the source file.

        Returns:
            SourceInfo instance with metadata from the file.
        """
        modified_time = None
        if file_path.exists():
            mtime = file_path.stat().st_mtime
            modified_time = datetime.fromtimestamp(mtime)

        return cls(
            path=str(file_path.absolute()),
            name=file_path.name,
            modified_time=modified_time,
        )

    @classmethod
    def from_string(cls, name: str = "<memory>") -> "SourceInfo":
        """Create SourceInfo for in-memory YAML strings.

        Args:
            name: Logical name for the source (default: '<memory>').

        Returns:
            SourceInfo instance for in-memory source.
        """
        return cls(path=name, name=name, modified_time=None)
