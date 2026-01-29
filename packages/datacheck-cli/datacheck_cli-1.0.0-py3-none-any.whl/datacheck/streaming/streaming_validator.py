"""Streaming validation for large datasets."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from datacheck.streaming.chunked_reader import (
    ChunkedReader,
    create_chunked_reader,
)
from datacheck.streaming.progress import ProgressTracker, ProgressCallback
from datacheck.validation.rules import Rule, Severity


@dataclass
class ValidationProgress:
    """Progress information during streaming validation."""
    chunk_number: int
    total_rows_processed: int
    rules_checked: int
    failures_found: int
    current_pass_rate: float


@dataclass
class StreamingValidationResult:
    """Result of streaming validation."""
    timestamp: str
    source: str
    total_rows: int
    total_chunks: int
    rules_run: int
    total_checks: int
    passed_checks: int
    failed_checks: int
    errors: int
    warnings: int
    infos: int
    pass_rate: float
    elapsed_seconds: float
    rows_per_second: float
    memory_peak_mb: float
    chunk_results: list[dict[str, Any]] = field(default_factory=list)
    failed_rows_sample: list[dict[str, Any]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return True if no error-level failures."""
        return self.errors == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "timestamp": self.timestamp,
            "source": self.source,
            "summary": {
                "total_rows": self.total_rows,
                "total_chunks": self.total_chunks,
                "rules_run": self.rules_run,
                "total_checks": self.total_checks,
                "passed_checks": self.passed_checks,
                "failed_checks": self.failed_checks,
                "errors": self.errors,
                "warnings": self.warnings,
                "infos": self.infos,
                "pass_rate": round(self.pass_rate, 2),
                "passed": self.passed,
            },
            "performance": {
                "elapsed_seconds": round(self.elapsed_seconds, 2),
                "rows_per_second": round(self.rows_per_second, 2),
                "memory_peak_mb": round(self.memory_peak_mb, 2),
            },
            "failed_rows_sample": self.failed_rows_sample[:100],  # Limit sample size
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert result to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=indent)


class StreamingValidator:
    """Validator that processes data in streaming fashion."""

    def __init__(
        self,
        rules: list[Rule] | None = None,
        chunk_size: int = 10000,
        max_failed_rows_sample: int = 100,
        progress_callback: ProgressCallback | None = None,
    ):
        """Initialize streaming validator.

        Args:
            rules: Validation rules to apply
            chunk_size: Number of rows per chunk
            max_failed_rows_sample: Maximum failed rows to store in sample
            progress_callback: Callback for progress updates
        """
        self.rules = rules or []
        self.chunk_size = chunk_size
        self.max_failed_rows_sample = max_failed_rows_sample
        self.progress_callback = progress_callback

    def add_rule(self, rule: Rule) -> "StreamingValidator":
        """Add a validation rule.

        Args:
            rule: Rule to add

        Returns:
            Self for chaining
        """
        self.rules.append(rule)
        return self

    def add_rules(self, rules: list[Rule]) -> "StreamingValidator":
        """Add multiple validation rules.

        Args:
            rules: Rules to add

        Returns:
            Self for chaining
        """
        self.rules.extend(rules)
        return self

    def validate_file(
        self,
        path: str | Path,
        source: str | None = None,
        **reader_kwargs,
    ) -> StreamingValidationResult:
        """Validate a file in streaming fashion.

        Args:
            path: Path to data file
            source: Source identifier for reporting
            **reader_kwargs: Additional reader options

        Returns:
            StreamingValidationResult
        """
        path = Path(path)
        source = source or str(path)

        reader = create_chunked_reader(
            path,
            chunk_size=self.chunk_size,
            **reader_kwargs,
        )

        return self.validate_reader(reader, source=source)

    def validate_reader(
        self,
        reader: ChunkedReader,
        source: str = "unknown",
    ) -> StreamingValidationResult:
        """Validate data from a chunked reader.

        Args:
            reader: ChunkedReader instance
            source: Source identifier

        Returns:
            StreamingValidationResult
        """
        # Initialize tracking
        progress = ProgressTracker(
            total_rows=reader.total_rows,
            total_bytes=reader.get_file_size() if hasattr(reader, "get_file_size") else None,
        )
        if self.progress_callback:
            progress.set_callback(self.progress_callback)

        progress.start()

        # Aggregated results
        total_rows = 0
        total_chunks = 0
        total_checks = 0
        passed_checks = 0
        errors = 0
        warnings = 0
        infos = 0
        failed_rows_sample: list[dict[str, Any]] = []
        chunk_results: list[dict[str, Any]] = []
        peak_memory = 0

        try:
            for chunk_df, chunk_info in reader.iter_chunks():
                total_chunks += 1
                total_rows += chunk_info.rows_in_chunk
                peak_memory = max(peak_memory, chunk_info.memory_usage_bytes)

                # Validate this chunk
                chunk_passed = 0
                chunk_failed = 0
                chunk_errors = 0
                chunk_warnings = 0

                for rule in self.rules:
                    results = rule.validate(chunk_df)

                    for result in results:
                        total_checks += 1

                        if result.passed:
                            passed_checks += 1
                            chunk_passed += 1
                        else:
                            chunk_failed += 1

                            # Count by severity
                            if result.severity == Severity.ERROR:
                                errors += 1
                                chunk_errors += 1
                            elif result.severity == Severity.WARNING:
                                warnings += 1
                                chunk_warnings += 1
                            else:
                                infos += 1

                            # Collect failed row samples
                            if len(failed_rows_sample) < self.max_failed_rows_sample:
                                for row_idx in result.failed_rows[:10]:
                                    if len(failed_rows_sample) >= self.max_failed_rows_sample:
                                        break
                                    # Adjust row index for chunk offset
                                    global_row_idx = chunk_info.total_rows_processed - chunk_info.rows_in_chunk + row_idx
                                    failed_rows_sample.append({
                                        "row": global_row_idx,
                                        "rule": result.rule_name,
                                        "column": result.column,
                                        "message": result.message,
                                    })

                # Store chunk result summary
                chunk_results.append({
                    "chunk": total_chunks,
                    "rows": chunk_info.rows_in_chunk,
                    "passed": chunk_passed,
                    "failed": chunk_failed,
                    "errors": chunk_errors,
                    "warnings": chunk_warnings,
                })

                # Update progress
                progress.update(
                    rows=chunk_info.rows_in_chunk,
                    bytes_read=chunk_info.memory_usage_bytes,
                    chunk_complete=True,
                )

            progress.complete()

        except Exception as e:
            progress.fail(e)
            raise

        # Calculate final metrics
        elapsed = progress.elapsed_time.total_seconds()
        rows_per_sec = total_rows / elapsed if elapsed > 0 else 0
        pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 100.0

        return StreamingValidationResult(
            timestamp=datetime.now().isoformat(),
            source=source,
            total_rows=total_rows,
            total_chunks=total_chunks,
            rules_run=len(self.rules),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            errors=errors,
            warnings=warnings,
            infos=infos,
            pass_rate=pass_rate,
            elapsed_seconds=elapsed,
            rows_per_second=rows_per_sec,
            memory_peak_mb=peak_memory / (1024 * 1024),
            chunk_results=chunk_results,
            failed_rows_sample=failed_rows_sample,
        )

    def validate_dataframe_streaming(
        self,
        df: pd.DataFrame,
        source: str = "dataframe",
    ) -> StreamingValidationResult:
        """Validate a DataFrame in chunks (for testing or in-memory large DataFrames).

        Args:
            df: DataFrame to validate
            source: Source identifier

        Returns:
            StreamingValidationResult
        """
        progress = ProgressTracker(total_rows=len(df))
        if self.progress_callback:
            progress.set_callback(self.progress_callback)

        progress.start()

        total_rows = len(df)
        total_chunks = 0
        total_checks = 0
        passed_checks = 0
        errors = 0
        warnings = 0
        infos = 0
        failed_rows_sample: list[dict[str, Any]] = []
        chunk_results: list[dict[str, Any]] = []
        peak_memory = df.memory_usage(deep=True).sum()

        try:
            # Process in chunks
            for start_idx in range(0, len(df), self.chunk_size):
                end_idx = min(start_idx + self.chunk_size, len(df))
                chunk_df = df.iloc[start_idx:end_idx]
                total_chunks += 1

                chunk_passed = 0
                chunk_failed = 0
                chunk_errors = 0
                chunk_warnings = 0

                for rule in self.rules:
                    results = rule.validate(chunk_df)

                    for result in results:
                        total_checks += 1

                        if result.passed:
                            passed_checks += 1
                            chunk_passed += 1
                        else:
                            chunk_failed += 1

                            if result.severity == Severity.ERROR:
                                errors += 1
                                chunk_errors += 1
                            elif result.severity == Severity.WARNING:
                                warnings += 1
                                chunk_warnings += 1
                            else:
                                infos += 1

                            # Collect failed row samples
                            if len(failed_rows_sample) < self.max_failed_rows_sample:
                                for row_idx in result.failed_rows[:10]:
                                    if len(failed_rows_sample) >= self.max_failed_rows_sample:
                                        break
                                    global_row_idx = start_idx + row_idx
                                    failed_rows_sample.append({
                                        "row": global_row_idx,
                                        "rule": result.rule_name,
                                        "column": result.column,
                                        "message": result.message,
                                    })

                chunk_results.append({
                    "chunk": total_chunks,
                    "rows": len(chunk_df),
                    "passed": chunk_passed,
                    "failed": chunk_failed,
                    "errors": chunk_errors,
                    "warnings": chunk_warnings,
                })

                progress.update(
                    rows=len(chunk_df),
                    chunk_complete=True,
                )

            progress.complete()

        except Exception as e:
            progress.fail(e)
            raise

        elapsed = progress.elapsed_time.total_seconds()
        rows_per_sec = total_rows / elapsed if elapsed > 0 else 0
        pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 100.0

        return StreamingValidationResult(
            timestamp=datetime.now().isoformat(),
            source=source,
            total_rows=total_rows,
            total_chunks=total_chunks,
            rules_run=len(self.rules),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            errors=errors,
            warnings=warnings,
            infos=infos,
            pass_rate=pass_rate,
            elapsed_seconds=elapsed,
            rows_per_second=rows_per_sec,
            memory_peak_mb=peak_memory / (1024 * 1024),
            chunk_results=chunk_results,
            failed_rows_sample=failed_rows_sample,
        )

    @classmethod
    def from_config(
        cls,
        config: dict[str, Any],
        chunk_size: int = 10000,
        progress_callback: ProgressCallback | None = None,
    ) -> "StreamingValidator":
        """Create a streaming validator from configuration.

        Args:
            config: Configuration dictionary with rules
            chunk_size: Chunk size for processing
            progress_callback: Progress callback

        Returns:
            StreamingValidator instance
        """
        from datacheck.validation.config import parse_rules_config

        rules = parse_rules_config(config)
        return cls(
            rules=rules,
            chunk_size=chunk_size,
            progress_callback=progress_callback,
        )
