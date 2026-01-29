"""Progress tracking for streaming operations."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections.abc import Callable
import time


@dataclass
class ProgressCallback:
    """Callback configuration for progress updates."""
    on_progress: Callable[["ProgressTracker"], None] | None = None
    on_chunk_complete: Callable[["ProgressTracker", int], None] | None = None
    on_complete: Callable[["ProgressTracker"], None] | None = None
    on_error: Callable[["ProgressTracker", Exception], None] | None = None
    update_interval: float = 0.5  # Minimum seconds between progress updates


@dataclass
class ProgressTracker:
    """Track progress of streaming operations."""
    total_rows: int | None = None
    total_chunks: int | None = None
    processed_rows: int = 0
    processed_chunks: int = 0
    failed_rows: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None
    current_chunk_rows: int = 0
    bytes_processed: int = 0
    total_bytes: int | None = None
    status: str = "pending"
    error_message: str | None = None

    # Internal tracking
    _last_update_time: float = field(default=0.0, repr=False)
    _callback: ProgressCallback | None = field(default=None, repr=False)

    def start(self) -> None:
        """Mark operation as started."""
        self.start_time = datetime.now()
        self.status = "running"
        self._last_update_time = time.time()

    def complete(self) -> None:
        """Mark operation as complete."""
        self.end_time = datetime.now()
        self.status = "completed"
        if self._callback and self._callback.on_complete:
            self._callback.on_complete(self)

    def fail(self, error: Exception) -> None:
        """Mark operation as failed."""
        self.end_time = datetime.now()
        self.status = "failed"
        self.error_message = str(error)
        if self._callback and self._callback.on_error:
            self._callback.on_error(self, error)

    def update(
        self,
        rows: int = 0,
        bytes_read: int = 0,
        chunk_complete: bool = False,
    ) -> None:
        """Update progress.

        Args:
            rows: Number of rows processed in this update
            bytes_read: Bytes processed in this update
            chunk_complete: Whether a chunk was completed
        """
        self.processed_rows += rows
        self.current_chunk_rows = rows
        self.bytes_processed += bytes_read

        if chunk_complete:
            self.processed_chunks += 1
            if self._callback and self._callback.on_chunk_complete:
                self._callback.on_chunk_complete(self, self.processed_chunks)

        # Call progress callback with rate limiting
        if self._callback and self._callback.on_progress:
            current_time = time.time()
            if current_time - self._last_update_time >= self._callback.update_interval:
                self._callback.on_progress(self)
                self._last_update_time = current_time

    def set_callback(self, callback: ProgressCallback) -> None:
        """Set progress callback."""
        self._callback = callback

    @property
    def percent_complete(self) -> float:
        """Get percentage complete (0-100)."""
        if self.total_rows and self.total_rows > 0:
            return min(100.0, (self.processed_rows / self.total_rows) * 100)
        elif self.total_bytes and self.total_bytes > 0:
            return min(100.0, (self.bytes_processed / self.total_bytes) * 100)
        return 0.0

    @property
    def elapsed_time(self) -> timedelta:
        """Get elapsed time."""
        if not self.start_time:
            return timedelta(0)
        end = self.end_time or datetime.now()
        return end - self.start_time

    @property
    def rows_per_second(self) -> float:
        """Calculate rows processed per second."""
        elapsed = self.elapsed_time.total_seconds()
        if elapsed > 0:
            return self.processed_rows / elapsed
        return 0.0

    @property
    def estimated_time_remaining(self) -> timedelta | None:
        """Estimate remaining time."""
        if self.percent_complete <= 0 or self.percent_complete >= 100:
            return None

        elapsed = self.elapsed_time.total_seconds()
        if elapsed <= 0:
            return None

        # Calculate based on current rate
        rate = self.percent_complete / elapsed
        remaining_percent = 100.0 - self.percent_complete
        remaining_seconds = remaining_percent / rate

        return timedelta(seconds=remaining_seconds)

    @property
    def is_complete(self) -> bool:
        """Check if operation is complete."""
        return self.status in ("completed", "failed")

    def to_dict(self) -> dict:
        """Convert progress to dictionary."""
        return {
            "status": self.status,
            "processed_rows": self.processed_rows,
            "total_rows": self.total_rows,
            "processed_chunks": self.processed_chunks,
            "total_chunks": self.total_chunks,
            "percent_complete": round(self.percent_complete, 2),
            "rows_per_second": round(self.rows_per_second, 2),
            "elapsed_seconds": round(self.elapsed_time.total_seconds(), 2),
            "bytes_processed": self.bytes_processed,
            "failed_rows": self.failed_rows,
            "error_message": self.error_message,
        }

    def format_progress(self) -> str:
        """Format progress as human-readable string."""
        parts = []

        # Row progress
        if self.total_rows:
            parts.append(f"{self.processed_rows:,}/{self.total_rows:,} rows")
        else:
            parts.append(f"{self.processed_rows:,} rows")

        # Percentage
        parts.append(f"({self.percent_complete:.1f}%)")

        # Rate
        if self.rows_per_second > 0:
            parts.append(f"@ {self.rows_per_second:,.0f} rows/s")

        # ETA
        eta = self.estimated_time_remaining
        if eta:
            if eta.total_seconds() < 60:
                parts.append(f"ETA: {eta.total_seconds():.0f}s")
            elif eta.total_seconds() < 3600:
                parts.append(f"ETA: {eta.total_seconds() / 60:.1f}m")
            else:
                parts.append(f"ETA: {eta.total_seconds() / 3600:.1f}h")

        return " ".join(parts)


def create_console_progress_callback() -> ProgressCallback:
    """Create a progress callback that prints to console.

    Returns:
        ProgressCallback configured for console output
    """
    def on_progress(tracker: ProgressTracker) -> None:
        print(f"\r{tracker.format_progress()}", end="", flush=True)

    def on_complete(tracker: ProgressTracker) -> None:
        print(f"\n✓ Complete: {tracker.processed_rows:,} rows in {tracker.elapsed_time.total_seconds():.1f}s")

    def on_error(tracker: ProgressTracker, error: Exception) -> None:
        print(f"\n✗ Error: {error}")

    return ProgressCallback(
        on_progress=on_progress,
        on_complete=on_complete,
        on_error=on_error,
        update_interval=0.1,
    )
