"""Azure Blob Storage connector for DataCheck."""
import io
import re
from collections.abc import Iterator

import pandas as pd

from datacheck.connectors.cloud_base import CloudConnector, CloudFile
from datacheck.exceptions import AuthenticationError, ConnectionError


class AzureConnector(CloudConnector):
    """Azure Blob Storage connector."""

    def __init__(
        self,
        container: str,
        prefix: str = "",
        account_name: str | None = None,
        account_key: str | None = None,
        connection_string: str | None = None,
        sas_token: str | None = None,
    ) -> None:
        """Initialize Azure Blob connector.

        Args:
            container: Azure container name
            prefix: Path prefix (folder)
            account_name: Azure storage account name
            account_key: Azure storage account key
            connection_string: Azure connection string (alternative auth)
            sas_token: Shared Access Signature token (alternative auth)
        """
        self.container = container
        self.account_name = account_name
        self.account_key = account_key
        self.connection_string = connection_string
        self.sas_token = sas_token

        # Use container as bucket for base class
        super().__init__(container, prefix, region=account_name or "")

        # Initialize Azure client
        self._client = self._create_client()

    def _validate_config(self) -> None:
        """Validate Azure configuration."""
        if not self.container:
            raise ValueError("Azure container name is required")

        # Validate container name format
        if not self._is_valid_container_name(self.container):
            raise ValueError(f"Invalid Azure container name: {self.container}")

        # Check authentication options
        if not any([
            self.connection_string,
            (self.account_name and self.account_key),
            (self.account_name and self.sas_token),
        ]):
            raise ValueError(
                "Azure authentication required: provide connection_string, "
                "or account_name with account_key or sas_token"
            )

    def _is_valid_container_name(self, name: str) -> bool:
        """Validate Azure container name format.

        Args:
            name: Container name to validate

        Returns:
            True if valid, False otherwise
        """
        # Azure container naming rules
        # Must be 3-63 characters, lowercase letters, numbers, and hyphens
        # Must start with letter or number
        pattern = r"^[a-z0-9][a-z0-9\-]{1,61}[a-z0-9]$"
        return bool(re.match(pattern, name))

    def _create_client(self):
        """Create Azure Blob service client.

        Returns:
            azure.storage.blob.BlobServiceClient

        Raises:
            AuthenticationError: If credentials not found
            ConnectionError: If client creation fails
        """
        try:
            from azure.storage.blob import BlobServiceClient
            from azure.core.exceptions import ClientAuthenticationError
        except ImportError:
            raise ImportError(
                "azure-storage-blob is required for Azure connector. "
                "Install with: pip install datacheck[cloud]"
            )

        try:
            if self.connection_string:
                # Use connection string
                return BlobServiceClient.from_connection_string(self.connection_string)
            elif self.account_name and self.account_key:
                # Use account name and key
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                return BlobServiceClient(
                    account_url=account_url,
                    credential=self.account_key,
                )
            elif self.account_name and self.sas_token:
                # Use SAS token
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                return BlobServiceClient(
                    account_url=account_url,
                    credential=self.sas_token,
                )
            else:
                raise AuthenticationError(
                    "Azure authentication required: provide connection_string, "
                    "or account_name with account_key or sas_token"
                )

        except ClientAuthenticationError as e:
            raise AuthenticationError(f"Azure authentication failed: {e}")
        except Exception as e:
            raise ConnectionError(f"Failed to create Azure client: {e}")

    def list_files(self, pattern: str = "*") -> list[CloudFile]:
        """List files in Azure container.

        Args:
            pattern: Glob pattern to match files

        Returns:
            List of CloudFile objects

        Raises:
            ConnectionError: If container doesn't exist or access denied
            AuthenticationError: If access is denied
        """
        from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError

        try:
            container_client = self._client.get_container_client(self.container)

            # List all blobs with prefix
            blobs = container_client.list_blobs(name_starts_with=self.prefix)

            # Convert to CloudFile objects
            files = []
            for blob in blobs:
                # Skip "directory" markers
                if blob.name.endswith("/"):
                    continue

                files.append(
                    CloudFile(
                        path=blob.name,
                        size=blob.size or 0,
                        last_modified=blob.last_modified.isoformat() if blob.last_modified else "",
                        etag=blob.etag,
                    )
                )

            # Filter by pattern
            if pattern != "*":
                file_paths = [f.path for f in files]
                matched_paths = self._match_pattern(file_paths, pattern)
                files = [f for f in files if f.path in matched_paths]

            return files

        except ResourceNotFoundError:
            raise ConnectionError(f"Azure container does not exist: {self.container}")
        except ClientAuthenticationError:
            raise AuthenticationError(f"Access denied to Azure container: {self.container}")
        except Exception as e:
            raise ConnectionError(f"Azure error: {e}")

    def read_csv(self, path: str, **kwargs) -> pd.DataFrame:
        """Read CSV file from Azure Blob.

        Args:
            path: Blob name (file path)
            **kwargs: Additional arguments for pd.read_csv

        Returns:
            DataFrame with file contents

        Raises:
            FileNotFoundError: If file doesn't exist
            ConnectionError: If read fails
        """
        from azure.core.exceptions import ResourceNotFoundError

        try:
            container_client = self._client.get_container_client(self.container)
            blob_client = container_client.get_blob_client(path)
            content = blob_client.download_blob().readall()
            return pd.read_csv(io.BytesIO(content), **kwargs)

        except ResourceNotFoundError:
            raise FileNotFoundError(f"File not found in Azure: {path}")
        except Exception as e:
            raise ConnectionError(f"Failed to read CSV from Azure: {e}")

    def read_parquet(self, path: str, **kwargs) -> pd.DataFrame:
        """Read Parquet file from Azure Blob.

        Args:
            path: Blob name (file path)
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

        from azure.core.exceptions import ResourceNotFoundError

        try:
            container_client = self._client.get_container_client(self.container)
            blob_client = container_client.get_blob_client(path)
            content = blob_client.download_blob().readall()
            return pd.read_parquet(io.BytesIO(content), **kwargs)

        except ResourceNotFoundError:
            raise FileNotFoundError(f"File not found in Azure: {path}")
        except Exception as e:
            raise ConnectionError(f"Failed to read Parquet from Azure: {e}")

    def read_json(self, path: str, **kwargs) -> pd.DataFrame:
        """Read JSON file from Azure Blob.

        Args:
            path: Blob name (file path)
            **kwargs: Additional arguments for pd.read_json

        Returns:
            DataFrame with file contents

        Raises:
            FileNotFoundError: If file doesn't exist
            ConnectionError: If read fails
        """
        from azure.core.exceptions import ResourceNotFoundError

        try:
            container_client = self._client.get_container_client(self.container)
            blob_client = container_client.get_blob_client(path)
            content = blob_client.download_blob().readall()
            return pd.read_json(io.BytesIO(content), **kwargs)

        except ResourceNotFoundError:
            raise FileNotFoundError(f"File not found in Azure: {path}")
        except Exception as e:
            raise ConnectionError(f"Failed to read JSON from Azure: {e}")

    def file_exists(self, path: str) -> bool:
        """Check if file exists in Azure Blob.

        Args:
            path: Blob name (file path)

        Returns:
            True if file exists, False otherwise
        """
        try:
            container_client = self._client.get_container_client(self.container)
            blob_client = container_client.get_blob_client(path)
            return blob_client.exists()
        except Exception:
            return False

    def get_file_size(self, path: str) -> int:
        """Get file size in bytes.

        Args:
            path: Blob name (file path)

        Returns:
            File size in bytes

        Raises:
            FileNotFoundError: If file doesn't exist
            ConnectionError: If operation fails
        """
        from azure.core.exceptions import ResourceNotFoundError

        try:
            container_client = self._client.get_container_client(self.container)
            blob_client = container_client.get_blob_client(path)
            properties = blob_client.get_blob_properties()
            return properties.size or 0

        except ResourceNotFoundError:
            raise FileNotFoundError(f"File not found in Azure: {path}")
        except Exception as e:
            raise ConnectionError(f"Failed to get file size: {e}")

    def read_chunked(
        self, path: str, chunk_size: int = 10000, **kwargs
    ) -> Iterator[pd.DataFrame]:
        """Read large file in chunks.

        Args:
            path: Blob name (file path)
            chunk_size: Number of rows per chunk
            **kwargs: Additional arguments for reader

        Yields:
            DataFrame chunks

        Raises:
            ValueError: If file format doesn't support chunked reading
        """
        # Determine file type
        ext = path.lower().split(".")[-1]

        container_client = self._client.get_container_client(self.container)
        blob_client = container_client.get_blob_client(path)
        content = blob_client.download_blob().readall()

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
