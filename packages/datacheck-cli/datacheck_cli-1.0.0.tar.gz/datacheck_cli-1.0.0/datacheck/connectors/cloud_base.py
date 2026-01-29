"""Base class for cloud storage connectors."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class CloudFile:
    """Represents a file in cloud storage."""

    path: str
    size: int
    last_modified: str
    etag: str | None = None


class CloudConnector(ABC):
    """Abstract base class for cloud storage connectors."""

    def __init__(
        self, bucket: str, prefix: str = "", region: str | None = None
    ) -> None:
        """Initialize cloud connector.

        Args:
            bucket: Bucket/container name
            prefix: Path prefix to filter files
            region: Cloud region (provider-specific)
        """
        self.bucket = bucket
        self.prefix = prefix
        self.region = region
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate configuration."""
        pass

    @abstractmethod
    def list_files(self, pattern: str = "*") -> list[CloudFile]:
        """List files matching pattern.

        Args:
            pattern: Glob pattern to match files

        Returns:
            List of CloudFile objects
        """
        pass

    @abstractmethod
    def read_csv(self, path: str, **kwargs) -> pd.DataFrame:
        """Read CSV file from cloud storage.

        Args:
            path: File path in cloud storage
            **kwargs: Additional arguments for pd.read_csv

        Returns:
            DataFrame with file contents
        """
        pass

    @abstractmethod
    def read_parquet(self, path: str, **kwargs) -> pd.DataFrame:
        """Read Parquet file from cloud storage.

        Args:
            path: File path in cloud storage
            **kwargs: Additional arguments for reading

        Returns:
            DataFrame with file contents
        """
        pass

    @abstractmethod
    def read_json(self, path: str, **kwargs) -> pd.DataFrame:
        """Read JSON file from cloud storage.

        Args:
            path: File path in cloud storage
            **kwargs: Additional arguments for pd.read_json

        Returns:
            DataFrame with file contents
        """
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: File path in cloud storage

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def get_file_size(self, path: str) -> int:
        """Get file size in bytes.

        Args:
            path: File path in cloud storage

        Returns:
            File size in bytes
        """
        pass

    def read_file(self, path: str, **kwargs) -> pd.DataFrame:
        """Read file based on extension.

        Args:
            path: File path
            **kwargs: Additional arguments for reader

        Returns:
            DataFrame with file contents

        Raises:
            ValueError: If file format is not supported
        """
        ext = path.lower().split(".")[-1]

        if ext == "csv":
            return self.read_csv(path, **kwargs)
        elif ext in ["parquet", "pq"]:
            return self.read_parquet(path, **kwargs)
        elif ext == "json":
            return self.read_json(path, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _match_pattern(self, files: list[str], pattern: str) -> list[str]:
        """Filter files by glob pattern.

        Args:
            files: List of file paths
            pattern: Glob pattern

        Returns:
            Filtered list of paths
        """
        import fnmatch

        return [f for f in files if fnmatch.fnmatch(f, pattern)]
