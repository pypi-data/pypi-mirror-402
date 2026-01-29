"""Google Cloud Storage connector for DataCheck."""
import io
import re
from collections.abc import Iterator

import pandas as pd

from datacheck.connectors.cloud_base import CloudConnector, CloudFile
from datacheck.exceptions import AuthenticationError, ConnectionError


class GCSConnector(CloudConnector):
    """Google Cloud Storage connector."""

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        project: str | None = None,
        credentials_path: str | None = None,
    ) -> None:
        """Initialize GCS connector.

        Args:
            bucket: GCS bucket name
            prefix: Path prefix (folder)
            project: GCP project ID
            credentials_path: Path to service account JSON file (optional)
        """
        self.project = project
        self.credentials_path = credentials_path

        super().__init__(bucket, prefix, region=project or "")

        # Initialize GCS client
        self._client = self._create_client()

    def _validate_config(self) -> None:
        """Validate GCS configuration."""
        if not self.bucket:
            raise ValueError("GCS bucket name is required")

        # Validate bucket name format
        if not self._is_valid_bucket_name(self.bucket):
            raise ValueError(f"Invalid GCS bucket name: {self.bucket}")

    def _is_valid_bucket_name(self, name: str) -> bool:
        """Validate GCS bucket name format.

        Args:
            name: Bucket name to validate

        Returns:
            True if valid, False otherwise
        """
        # GCS bucket naming rules
        # Must be 3-63 characters, lowercase, numbers, hyphens, underscores
        # Must start and end with letter or number
        pattern = r"^[a-z0-9][a-z0-9\-_\.]{1,61}[a-z0-9]$"
        return bool(re.match(pattern, name))

    def _create_client(self):
        """Create GCS client.

        Returns:
            google.cloud.storage.Client

        Raises:
            AuthenticationError: If credentials not found
            ConnectionError: If client creation fails
        """
        try:
            from google.cloud import storage
            from google.auth.exceptions import DefaultCredentialsError
        except ImportError:
            raise ImportError(
                "google-cloud-storage is required for GCS connector. "
                "Install with: pip install datacheck[cloud]"
            )

        try:
            if self.credentials_path:
                # Use explicit credentials file
                return storage.Client.from_service_account_json(
                    self.credentials_path,
                    project=self.project,
                )
            else:
                # Use Application Default Credentials
                return storage.Client(project=self.project)

        except DefaultCredentialsError:
            raise AuthenticationError(
                "GCP credentials not found. Set GOOGLE_APPLICATION_CREDENTIALS "
                "environment variable, or pass credentials_path parameter."
            )
        except Exception as e:
            raise ConnectionError(f"Failed to create GCS client: {e}")

    def list_files(self, pattern: str = "*") -> list[CloudFile]:
        """List files in GCS bucket.

        Args:
            pattern: Glob pattern to match files

        Returns:
            List of CloudFile objects

        Raises:
            ConnectionError: If bucket doesn't exist or access denied
            AuthenticationError: If access is denied
        """
        from google.api_core.exceptions import NotFound, Forbidden

        try:
            bucket = self._client.bucket(self.bucket)

            # List all blobs with prefix
            blobs = bucket.list_blobs(prefix=self.prefix)

            # Convert to CloudFile objects
            files = []
            for blob in blobs:
                # Skip "directory" markers (blobs ending with /)
                if blob.name.endswith("/"):
                    continue

                files.append(
                    CloudFile(
                        path=blob.name,
                        size=blob.size or 0,
                        last_modified=blob.updated.isoformat() if blob.updated else "",
                        etag=blob.etag,
                    )
                )

            # Filter by pattern
            if pattern != "*":
                file_paths = [f.path for f in files]
                matched_paths = self._match_pattern(file_paths, pattern)
                files = [f for f in files if f.path in matched_paths]

            return files

        except NotFound:
            raise ConnectionError(f"GCS bucket does not exist: {self.bucket}")
        except Forbidden:
            raise AuthenticationError(f"Access denied to GCS bucket: {self.bucket}")
        except Exception as e:
            raise ConnectionError(f"GCS error: {e}")

    def read_csv(self, path: str, **kwargs) -> pd.DataFrame:
        """Read CSV file from GCS.

        Args:
            path: GCS blob name (file path)
            **kwargs: Additional arguments for pd.read_csv

        Returns:
            DataFrame with file contents

        Raises:
            FileNotFoundError: If file doesn't exist
            ConnectionError: If read fails
        """
        from google.api_core.exceptions import NotFound

        try:
            bucket = self._client.bucket(self.bucket)
            blob = bucket.blob(path)
            content = blob.download_as_bytes()
            return pd.read_csv(io.BytesIO(content), **kwargs)

        except NotFound:
            raise FileNotFoundError(f"File not found in GCS: {path}")
        except Exception as e:
            raise ConnectionError(f"Failed to read CSV from GCS: {e}")

    def read_parquet(self, path: str, **kwargs) -> pd.DataFrame:
        """Read Parquet file from GCS.

        Args:
            path: GCS blob name (file path)
            **kwargs: Additional arguments for reading

        Returns:
            DataFrame with file contents

        Raises:
            FileNotFoundError: If file doesn't exist
            ConnectionError: If read fails
        """
        try:
            import pyarrow.parquet  # noqa: F401 - check availability
        except ImportError:
            raise ImportError(
                "pyarrow is required for reading Parquet files. "
                "Install with: pip install datacheck[cloud]"
            )

        from google.api_core.exceptions import NotFound

        try:
            bucket = self._client.bucket(self.bucket)
            blob = bucket.blob(path)
            content = blob.download_as_bytes()
            return pd.read_parquet(io.BytesIO(content), **kwargs)

        except NotFound:
            raise FileNotFoundError(f"File not found in GCS: {path}")
        except Exception as e:
            raise ConnectionError(f"Failed to read Parquet from GCS: {e}")

    def read_json(self, path: str, **kwargs) -> pd.DataFrame:
        """Read JSON file from GCS.

        Args:
            path: GCS blob name (file path)
            **kwargs: Additional arguments for pd.read_json

        Returns:
            DataFrame with file contents

        Raises:
            FileNotFoundError: If file doesn't exist
            ConnectionError: If read fails
        """
        from google.api_core.exceptions import NotFound

        try:
            bucket = self._client.bucket(self.bucket)
            blob = bucket.blob(path)
            content = blob.download_as_bytes()
            return pd.read_json(io.BytesIO(content), **kwargs)

        except NotFound:
            raise FileNotFoundError(f"File not found in GCS: {path}")
        except Exception as e:
            raise ConnectionError(f"Failed to read JSON from GCS: {e}")

    def file_exists(self, path: str) -> bool:
        """Check if file exists in GCS.

        Args:
            path: GCS blob name (file path)

        Returns:
            True if file exists, False otherwise
        """
        try:
            bucket = self._client.bucket(self.bucket)
            blob = bucket.blob(path)
            return blob.exists()
        except Exception:
            return False

    def get_file_size(self, path: str) -> int:
        """Get file size in bytes.

        Args:
            path: GCS blob name (file path)

        Returns:
            File size in bytes

        Raises:
            FileNotFoundError: If file doesn't exist
            ConnectionError: If operation fails
        """
        from google.api_core.exceptions import NotFound

        try:
            bucket = self._client.bucket(self.bucket)
            blob = bucket.blob(path)
            blob.reload()  # Fetch metadata
            return blob.size or 0

        except NotFound:
            raise FileNotFoundError(f"File not found in GCS: {path}")
        except Exception as e:
            raise ConnectionError(f"Failed to get file size: {e}")

    def read_chunked(
        self, path: str, chunk_size: int = 10000, **kwargs
    ) -> Iterator[pd.DataFrame]:
        """Read large file in chunks.

        Args:
            path: GCS blob name (file path)
            chunk_size: Number of rows per chunk
            **kwargs: Additional arguments for reader

        Yields:
            DataFrame chunks

        Raises:
            ValueError: If file format doesn't support chunked reading
        """
        # Determine file type
        ext = path.lower().split(".")[-1]

        bucket = self._client.bucket(self.bucket)
        blob = bucket.blob(path)
        content = blob.download_as_bytes()

        if ext == "csv":
            # Stream CSV in chunks
            yield from pd.read_csv(
                io.BytesIO(content), chunksize=chunk_size, **kwargs
            )

        elif ext in ["parquet", "pq"]:
            try:
                import pyarrow.parquet as pq
            except ImportError:
                raise ImportError(
                    "pyarrow is required for reading Parquet files. "
                    "Install with: pip install datacheck[cloud]"
                )

            # Read Parquet in batches
            parquet_file = pq.ParquetFile(io.BytesIO(content))

            for batch in parquet_file.iter_batches(batch_size=chunk_size):
                yield batch.to_pandas()

        else:
            raise ValueError(f"Chunked reading not supported for {ext} files")
