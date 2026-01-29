#!/usr/bin/env python3
"""Batch validation example for S3 data.

This script demonstrates how to validate multiple files from S3
in a batch processing workflow.

Usage:
    python s3_batch_validation.py
"""

import sys
from datetime import datetime
from typing import Any

from datacheck.connectors.s3 import S3Connector
from datacheck.connectors.cloud_base import CloudFile


def validate_batch(
    connector: S3Connector,
    files: list[CloudFile],
) -> dict[str, Any]:
    """Validate a batch of files and return summary.

    Args:
        connector: S3 connector instance
        files: List of files to validate

    Returns:
        Validation summary dictionary
    """
    results = {
        "total_files": len(files),
        "successful": 0,
        "failed": 0,
        "total_rows": 0,
        "errors": [],
    }

    for file in files:
        try:
            print(f"  Validating: {file.path}...")
            df = connector.read_file(file.path)

            # Basic validation checks
            row_count = len(df)
            col_count = len(df.columns)

            # Check for empty files
            if row_count == 0:
                results["errors"].append({
                    "file": file.path,
                    "error": "Empty file"
                })
                results["failed"] += 1
                continue

            # Check for expected columns (customize as needed)
            # required_columns = ["id", "timestamp", "value"]
            # missing = set(required_columns) - set(df.columns)
            # if missing:
            #     results["errors"].append({
            #         "file": file.path,
            #         "error": f"Missing columns: {missing}"
            #     })
            #     results["failed"] += 1
            #     continue

            results["successful"] += 1
            results["total_rows"] += row_count
            print(f"    OK: {row_count} rows, {col_count} columns")

        except Exception as e:
            results["errors"].append({
                "file": file.path,
                "error": str(e)
            })
            results["failed"] += 1
            print(f"    FAILED: {e}")

    return results


def main():
    """Main batch validation workflow."""
    print("=" * 60)
    print("S3 Batch Validation Example")
    print("=" * 60)

    # Configuration
    BUCKET = "my-data-bucket"
    PREFIX = "raw/events/"
    PATTERN = "*.parquet"
    AWS_PROFILE = "dev"

    print("\nConfiguration:")
    print(f"  Bucket: {BUCKET}")
    print(f"  Prefix: {PREFIX}")
    print(f"  Pattern: {PATTERN}")
    print(f"  Profile: {AWS_PROFILE}")

    # Create connector
    print("\nConnecting to S3...")
    connector = S3Connector(
        bucket=BUCKET,
        prefix=PREFIX,
        profile=AWS_PROFILE,
    )

    # List files to validate
    print("\nDiscovering files...")
    files = connector.list_files(pattern=PATTERN)
    print(f"Found {len(files)} files to validate")

    if not files:
        print("No files found. Exiting.")
        return

    # Show file summary
    total_size = sum(f.size for f in files)
    print(f"Total size: {total_size / 1024 / 1024:.2f} MB")

    # Run validation
    print("\nStarting validation...")
    start_time = datetime.now()
    results = validate_batch(connector, files)
    duration = (datetime.now() - start_time).total_seconds()

    # Print results
    print("\n" + "=" * 60)
    print("Validation Results")
    print("=" * 60)
    print(f"Total files:    {results['total_files']}")
    print(f"Successful:     {results['successful']}")
    print(f"Failed:         {results['failed']}")
    print(f"Total rows:     {results['total_rows']:,}")
    print(f"Duration:       {duration:.2f} seconds")

    if results["errors"]:
        print("\nErrors:")
        for err in results["errors"]:
            print(f"  {err['file']}: {err['error']}")

    # Exit with error code if any failures
    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    # Uncomment to run:
    # main()
    print("Uncomment main() in the script to run the batch validation.")
    print("Make sure to update BUCKET, PREFIX, and AWS_PROFILE first.")
