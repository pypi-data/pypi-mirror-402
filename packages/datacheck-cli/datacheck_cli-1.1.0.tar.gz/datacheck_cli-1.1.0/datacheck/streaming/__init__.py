"""Streaming and large file support for DataCheck.

WARNING: Streaming validation is EXPERIMENTAL and not fully compatible with CLI rules.
The streaming module uses a different rule system (datacheck.validation.rules) than
the main CLI (datacheck.rules). Results may differ between streaming and standard validation.

To use streaming validation, you must explicitly opt-in by passing `experimental=True`:

    from datacheck.streaming import StreamingValidator
    validator = StreamingValidator(rules=my_rules, experimental=True)

"""
import warnings

from datacheck.streaming.chunked_reader import (
    ChunkedReader,
    ChunkedCSVReader,
    ChunkedParquetReader,
    ChunkInfo,
)
from datacheck.streaming.streaming_validator import (
    StreamingValidator,
    StreamingValidationResult,
    ValidationProgress,
)
from datacheck.streaming.progress import ProgressTracker, ProgressCallback

# Emit warning on import
warnings.warn(
    "Streaming validation is experimental and not fully compatible with CLI rules. "
    "See module docstring for details.",
    UserWarning,
    stacklevel=2,
)

__all__ = [
    # Chunked readers
    "ChunkedReader",
    "ChunkedCSVReader",
    "ChunkedParquetReader",
    "ChunkInfo",
    # Streaming validation
    "StreamingValidator",
    "StreamingValidationResult",
    "ValidationProgress",
    # Progress tracking
    "ProgressTracker",
    "ProgressCallback",
]
