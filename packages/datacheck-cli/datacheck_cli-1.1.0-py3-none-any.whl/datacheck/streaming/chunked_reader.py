"""Chunked data reader for processing large files."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Generator

import pandas as pd


@dataclass
class ChunkInfo:
    """Information about a data chunk."""
    chunk_number: int
    rows_in_chunk: int
    total_rows_processed: int
    is_last_chunk: bool
    memory_usage_bytes: int


class ChunkedReader(ABC):
    """Abstract base class for chunked data readers."""

    def __init__(
        self,
        path: str | Path,
        chunk_size: int = 10000,
        **kwargs,
    ):
        """Initialize chunked reader.

        Args:
            path: Path to the data file
            chunk_size: Number of rows per chunk
            **kwargs: Additional reader-specific options
        """
        self.path = Path(path)
        self.chunk_size = chunk_size
        self.options = kwargs
        self._total_rows: int | None = None
        self._columns: list | None = None

    @property
    def total_rows(self) -> int | None:
        """Get total number of rows (if known)."""
        return self._total_rows

    @property
    def columns(self) -> list | None:
        """Get column names."""
        return self._columns

    @abstractmethod
    def iter_chunks(self) -> Generator[tuple[pd.DataFrame, ChunkInfo], None, None]:
        """Iterate over data chunks.

        Yields:
            Tuple of (DataFrame chunk, ChunkInfo)
        """
        pass

    @abstractmethod
    def get_schema(self) -> dict[str, str]:
        """Get data schema (column names and types).

        Returns:
            Dictionary mapping column names to data types
        """
        pass

    def estimate_total_rows(self) -> int | None:
        """Estimate total number of rows.

        Returns:
            Estimated row count or None if cannot be determined
        """
        return self._total_rows

    def get_file_size(self) -> int:
        """Get file size in bytes."""
        return self.path.stat().st_size


class ChunkedCSVReader(ChunkedReader):
    """Chunked reader for CSV files."""

    def __init__(
        self,
        path: str | Path,
        chunk_size: int = 10000,
        delimiter: str = ",",
        encoding: str = "utf-8",
        has_header: bool = True,
        **kwargs,
    ):
        """Initialize CSV chunked reader.

        Args:
            path: Path to CSV file
            chunk_size: Number of rows per chunk
            delimiter: Field delimiter
            encoding: File encoding
            has_header: Whether file has header row
            **kwargs: Additional pandas read_csv options
        """
        super().__init__(path, chunk_size, **kwargs)
        self.delimiter = delimiter
        self.encoding = encoding
        self.has_header = has_header
        self._estimate_rows()

    def _estimate_rows(self) -> None:
        """Estimate total rows by sampling file."""
        file_size = self.get_file_size()
        if file_size == 0:
            self._total_rows = 0
            return

        # Sample first few lines to estimate average line length
        sample_size = min(file_size, 65536)  # 64KB sample
        with open(self.path, encoding=self.encoding) as f:
            sample = f.read(sample_size)
            lines = sample.count("\n")
            if lines > 0:
                avg_line_length = sample_size / lines
                self._total_rows = int(file_size / avg_line_length)
                if self.has_header:
                    self._total_rows -= 1

    def iter_chunks(self) -> Generator[tuple[pd.DataFrame, ChunkInfo], None, None]:
        """Iterate over CSV chunks.

        Yields:
            Tuple of (DataFrame chunk, ChunkInfo)
        """
        chunk_number = 0
        total_rows_processed = 0

        reader = pd.read_csv(
            self.path,
            chunksize=self.chunk_size,
            delimiter=self.delimiter,
            encoding=self.encoding,
            header=0 if self.has_header else None,
            **self.options,
        )

        for chunk in reader:
            chunk_number += 1
            rows_in_chunk = len(chunk)
            total_rows_processed += rows_in_chunk

            # Store columns from first chunk
            if self._columns is None:
                self._columns = list(chunk.columns)

            # Calculate memory usage
            memory_usage = chunk.memory_usage(deep=True).sum()

            # Check if this might be the last chunk
            is_last = rows_in_chunk < self.chunk_size

            chunk_info = ChunkInfo(
                chunk_number=chunk_number,
                rows_in_chunk=rows_in_chunk,
                total_rows_processed=total_rows_processed,
                is_last_chunk=is_last,
                memory_usage_bytes=int(memory_usage),
            )

            yield chunk, chunk_info

        # Update total rows with actual count
        self._total_rows = total_rows_processed

    def get_schema(self) -> dict[str, str]:
        """Get CSV schema by reading first chunk.

        Returns:
            Dictionary mapping column names to inferred data types
        """
        # Read just the first few rows to infer schema
        df = pd.read_csv(
            self.path,
            nrows=100,
            delimiter=self.delimiter,
            encoding=self.encoding,
            header=0 if self.has_header else None,
            **self.options,
        )
        self._columns = list(df.columns)
        return {col: str(df[col].dtype) for col in df.columns}


class ChunkedParquetReader(ChunkedReader):
    """Chunked reader for Parquet files."""

    def __init__(
        self,
        path: str | Path,
        chunk_size: int = 10000,
        columns: list | None = None,
        **kwargs,
    ):
        """Initialize Parquet chunked reader.

        Args:
            path: Path to Parquet file
            chunk_size: Number of rows per chunk
            columns: Specific columns to read (None for all)
            **kwargs: Additional options
        """
        super().__init__(path, chunk_size, **kwargs)
        self.selected_columns = columns
        self._read_metadata()

    def _read_metadata(self) -> None:
        """Read Parquet metadata to get row count and schema."""
        try:
            import pyarrow.parquet as pq

            parquet_file = pq.ParquetFile(self.path)
            self._total_rows = parquet_file.metadata.num_rows
            schema = parquet_file.schema_arrow
            self._columns = schema.names
            self._schema = {
                field.name: str(field.type) for field in schema
            }
        except ImportError:
            # Fall back to pandas if pyarrow not available
            df = pd.read_parquet(self.path, engine="auto")
            self._total_rows = len(df)
            self._columns = list(df.columns)
            self._schema = {col: str(df[col].dtype) for col in df.columns}

    def iter_chunks(self) -> Generator[tuple[pd.DataFrame, ChunkInfo], None, None]:
        """Iterate over Parquet chunks.

        Yields:
            Tuple of (DataFrame chunk, ChunkInfo)
        """
        try:
            import pyarrow.parquet as pq

            parquet_file = pq.ParquetFile(self.path)
            chunk_number = 0
            total_rows_processed = 0

            # Read in batches
            for batch in parquet_file.iter_batches(
                batch_size=self.chunk_size,
                columns=self.selected_columns,
            ):
                chunk = batch.to_pandas()
                chunk_number += 1
                rows_in_chunk = len(chunk)
                total_rows_processed += rows_in_chunk

                memory_usage = chunk.memory_usage(deep=True).sum()
                is_last = total_rows_processed >= self._total_rows

                chunk_info = ChunkInfo(
                    chunk_number=chunk_number,
                    rows_in_chunk=rows_in_chunk,
                    total_rows_processed=total_rows_processed,
                    is_last_chunk=is_last,
                    memory_usage_bytes=int(memory_usage),
                )

                yield chunk, chunk_info

        except ImportError:
            # Fall back to reading full file if pyarrow not available
            df = pd.read_parquet(
                self.path,
                columns=self.selected_columns,
                engine="auto",
            )

            chunk_number = 0
            total_rows_processed = 0

            for start in range(0, len(df), self.chunk_size):
                chunk = df.iloc[start:start + self.chunk_size]
                chunk_number += 1
                rows_in_chunk = len(chunk)
                total_rows_processed += rows_in_chunk

                memory_usage = chunk.memory_usage(deep=True).sum()
                is_last = total_rows_processed >= len(df)

                chunk_info = ChunkInfo(
                    chunk_number=chunk_number,
                    rows_in_chunk=rows_in_chunk,
                    total_rows_processed=total_rows_processed,
                    is_last_chunk=is_last,
                    memory_usage_bytes=int(memory_usage),
                )

                yield chunk, chunk_info

    def get_schema(self) -> dict[str, str]:
        """Get Parquet schema.

        Returns:
            Dictionary mapping column names to data types
        """
        return getattr(self, "_schema", {})


def create_chunked_reader(
    path: str | Path,
    chunk_size: int = 10000,
    **kwargs,
) -> ChunkedReader:
    """Create appropriate chunked reader based on file extension.

    Args:
        path: Path to data file
        chunk_size: Number of rows per chunk
        **kwargs: Additional reader options

    Returns:
        ChunkedReader instance

    Raises:
        ValueError: If file format is not supported
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in (".csv", ".tsv", ".txt"):
        delimiter = "," if suffix == ".csv" else "\t"
        return ChunkedCSVReader(
            path,
            chunk_size=chunk_size,
            delimiter=kwargs.pop("delimiter", delimiter),
            **kwargs,
        )
    elif suffix in (".parquet", ".pq"):
        return ChunkedParquetReader(
            path,
            chunk_size=chunk_size,
            **kwargs,
        )
    else:
        raise ValueError(f"Unsupported file format: {suffix}")
