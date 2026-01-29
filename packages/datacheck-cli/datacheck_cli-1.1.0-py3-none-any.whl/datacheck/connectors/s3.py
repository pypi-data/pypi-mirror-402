"""AWS S3 connector for DataCheck."""
import io
import re
from collections.abc import Iterator

import pandas as pd

from datacheck.connectors.cloud_base import CloudConnector, CloudFile
from datacheck.exceptions import AuthenticationError, ConnectionError


class S3Connector(CloudConnector):
    """AWS S3 connector."""

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        region: str = "us-east-1",
        profile: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        """Initialize S3 connector.

        Args:
            bucket: S3 bucket name
            prefix: Path prefix (folder)
            region: AWS region
            profile: AWS profile name (from ~/.aws/credentials)
            access_key: AWS access key ID (optional)
            secret_key: AWS secret access key (optional)
        """
        self.profile = profile
        self.access_key = access_key
        self.secret_key = secret_key

        super().__init__(bucket, prefix, region)

        # Initialize S3 client
        self._client = self._create_client()
        self._resource = self._create_resource()

    def _validate_config(self) -> None:
        """Validate S3 configuration."""
        if not self.bucket:
            raise ValueError("S3 bucket name is required")

        # Validate bucket name format
        if not self._is_valid_bucket_name(self.bucket):
            raise ValueError(f"Invalid S3 bucket name: {self.bucket}")

    def _is_valid_bucket_name(self, name: str) -> bool:
        """Validate S3 bucket name format.

        Args:
            name: Bucket name to validate

        Returns:
            True if valid, False otherwise
        """
        # S3 bucket naming rules
        pattern = r"^[a-z0-9][a-z0-9\-]{1,61}[a-z0-9]$"
        return bool(re.match(pattern, name))

    def _create_client(self):
        """Create boto3 S3 client.

        Returns:
            boto3 S3 client

        Raises:
            AuthenticationError: If credentials not found
            ConnectionError: If client creation fails
        """
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 connector. "
                "Install with: pip install datacheck[cloud]"
            )

        try:
            if self.access_key and self.secret_key:
                # Use explicit credentials
                return boto3.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                )
            elif self.profile:
                # Use profile from ~/.aws/credentials
                session = boto3.Session(profile_name=self.profile)
                return session.client("s3", region_name=self.region)
            else:
                # Use default credentials (IAM role, env vars, etc.)
                return boto3.client("s3", region_name=self.region)

        except NoCredentialsError:
            raise AuthenticationError(
                "AWS credentials not found. Set AWS_ACCESS_KEY_ID and "
                "AWS_SECRET_ACCESS_KEY environment variables, or configure "
                "~/.aws/credentials file."
            )
        except Exception as e:
            raise ConnectionError(f"Failed to create S3 client: {e}")

    def _create_resource(self):
        """Create boto3 S3 resource.

        Returns:
            boto3 S3 resource
        """
        import boto3

        if self.access_key and self.secret_key:
            return boto3.resource(
                "s3",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )
        elif self.profile:
            session = boto3.Session(profile_name=self.profile)
            return session.resource("s3", region_name=self.region)
        else:
            return boto3.resource("s3", region_name=self.region)

    def list_files(self, pattern: str = "*") -> list[CloudFile]:
        """List files in S3 bucket.

        Args:
            pattern: Glob pattern to match files

        Returns:
            List of CloudFile objects

        Raises:
            ConnectionError: If bucket doesn't exist or access denied
            AuthenticationError: If access is denied
        """
        from botocore.exceptions import ClientError

        try:
            bucket = self._resource.Bucket(self.bucket)

            # List all objects with prefix
            objects = bucket.objects.filter(Prefix=self.prefix)

            # Convert to CloudFile objects
            files = [
                CloudFile(
                    path=obj.key,
                    size=obj.size,
                    last_modified=obj.last_modified.isoformat(),
                    etag=obj.e_tag,
                )
                for obj in objects
            ]

            # Filter by pattern
            if pattern != "*":
                file_paths = [f.path for f in files]
                matched_paths = self._match_pattern(file_paths, pattern)
                files = [f for f in files if f.path in matched_paths]

            return files

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchBucket":
                raise ConnectionError(f"S3 bucket does not exist: {self.bucket}")
            elif error_code == "403":
                raise AuthenticationError(f"Access denied to S3 bucket: {self.bucket}")
            else:
                raise ConnectionError(f"S3 error: {e}")

    def read_csv(self, path: str, **kwargs) -> pd.DataFrame:
        """Read CSV file from S3.

        Args:
            path: S3 key (file path)
            **kwargs: Additional arguments for pd.read_csv

        Returns:
            DataFrame with file contents

        Raises:
            FileNotFoundError: If file doesn't exist
            ConnectionError: If read fails
        """
        from botocore.exceptions import ClientError

        try:
            obj = self._client.get_object(Bucket=self.bucket, Key=path)
            return pd.read_csv(io.BytesIO(obj["Body"].read()), **kwargs)

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found in S3: {path}")
            raise ConnectionError(f"Failed to read CSV from S3: {e}")

    def read_parquet(self, path: str, **kwargs) -> pd.DataFrame:
        """Read Parquet file from S3.

        Args:
            path: S3 key (file path)
            **kwargs: Additional arguments for reading

        Returns:
            DataFrame with file contents

        Raises:
            ConnectionError: If read fails
        """
        try:
            import pyarrow.parquet  # noqa: F401 - check availability
        except ImportError:
            raise ImportError(
                "pyarrow is required for reading Parquet files. "
                "Install with: pip install datacheck[cloud]"
            )

        try:
            # Read file content first, then parse with PyArrow
            from botocore.exceptions import ClientError

            try:
                obj = self._client.get_object(Bucket=self.bucket, Key=path)
                content = obj["Body"].read()
                return pd.read_parquet(io.BytesIO(content), **kwargs)
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey":
                    raise FileNotFoundError(f"File not found in S3: {path}")
                raise ConnectionError(f"Failed to read Parquet from S3: {e}")

        except Exception as e:
            raise ConnectionError(f"Failed to read Parquet from S3: {e}")

    def read_json(self, path: str, **kwargs) -> pd.DataFrame:
        """Read JSON file from S3.

        Args:
            path: S3 key (file path)
            **kwargs: Additional arguments for pd.read_json

        Returns:
            DataFrame with file contents

        Raises:
            FileNotFoundError: If file doesn't exist
            ConnectionError: If read fails
        """
        from botocore.exceptions import ClientError

        try:
            obj = self._client.get_object(Bucket=self.bucket, Key=path)
            return pd.read_json(io.BytesIO(obj["Body"].read()), **kwargs)

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found in S3: {path}")
            raise ConnectionError(f"Failed to read JSON from S3: {e}")

    def file_exists(self, path: str) -> bool:
        """Check if file exists in S3.

        Args:
            path: S3 key (file path)

        Returns:
            True if file exists, False otherwise
        """
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self.bucket, Key=path)
            return True
        except ClientError:
            return False

    def get_file_size(self, path: str) -> int:
        """Get file size in bytes.

        Args:
            path: S3 key (file path)

        Returns:
            File size in bytes

        Raises:
            ConnectionError: If operation fails
        """
        from botocore.exceptions import ClientError

        try:
            response = self._client.head_object(Bucket=self.bucket, Key=path)
            return response["ContentLength"]
        except ClientError as e:
            raise ConnectionError(f"Failed to get file size: {e}")

    def read_chunked(
        self, path: str, chunk_size: int = 10000, **kwargs
    ) -> Iterator[pd.DataFrame]:
        """Read large file in chunks.

        Args:
            path: S3 key (file path)
            chunk_size: Number of rows per chunk
            **kwargs: Additional arguments for reader

        Yields:
            DataFrame chunks

        Raises:
            ValueError: If file format doesn't support chunked reading
        """
        # Determine file type
        ext = path.lower().split(".")[-1]

        if ext == "csv":
            # Stream CSV in chunks
            obj = self._client.get_object(Bucket=self.bucket, Key=path)

            yield from pd.read_csv(
                io.BytesIO(obj["Body"].read()), chunksize=chunk_size, **kwargs
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
            obj = self._client.get_object(Bucket=self.bucket, Key=path)
            content = obj["Body"].read()

            parquet_file = pq.ParquetFile(io.BytesIO(content))

            for batch in parquet_file.iter_batches(batch_size=chunk_size):
                yield batch.to_pandas()

        else:
            raise ValueError(f"Chunked reading not supported for {ext} files")
