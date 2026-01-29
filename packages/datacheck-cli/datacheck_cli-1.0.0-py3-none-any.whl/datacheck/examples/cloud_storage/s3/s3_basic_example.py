#!/usr/bin/env python3
"""Basic S3 connector usage examples.

This script demonstrates common operations with the S3 connector.
Make sure you have configured AWS credentials before running.

Usage:
    python s3_basic_example.py

Prerequisites:
    - AWS credentials configured (~/.aws/credentials or environment variables)
    - datacheck[cloud] installed
"""

from datacheck.connectors.s3 import S3Connector
from datacheck.loader import CloudLoader
from datacheck.exceptions import ConnectionError, AuthenticationError


def example_list_files():
    """Example: List files in an S3 bucket."""
    print("=" * 60)
    print("Example: List Files")
    print("=" * 60)

    # Create connector with AWS profile
    connector = S3Connector(
        bucket="my-data-bucket",
        prefix="raw/2024/",
        profile="dev",  # Uses profile from ~/.aws/credentials
    )

    # List all files
    print("\nAll files:")
    files = connector.list_files()
    for f in files:
        print(f"  {f.path} ({f.size:,} bytes)")

    # List only CSV files
    print("\nCSV files only:")
    csv_files = connector.list_files(pattern="*.csv")
    for f in csv_files:
        print(f"  {f.path}")

    # List with complex pattern
    print("\nParquet files from January:")
    jan_files = connector.list_files(pattern="*_202401*.parquet")
    for f in jan_files:
        print(f"  {f.path}")


def example_read_file():
    """Example: Read a single file from S3."""
    print("\n" + "=" * 60)
    print("Example: Read Single File")
    print("=" * 60)

    connector = S3Connector(
        bucket="my-data-bucket",
        region="us-east-1",
    )

    # Read CSV file
    print("\nReading CSV file...")
    df = connector.read_file("data/users.csv")
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")
    print(df.head())

    # Read Parquet file
    print("\nReading Parquet file...")
    df = connector.read_file("data/events.parquet")
    print(f"Loaded {len(df)} rows")


def example_cloud_loader():
    """Example: Using CloudLoader for advanced loading."""
    print("\n" + "=" * 60)
    print("Example: CloudLoader")
    print("=" * 60)

    connector = S3Connector(
        bucket="my-data-bucket",
        prefix="data/events/",
    )

    # Load single file
    print("\nLoading single file...")
    loader = CloudLoader(connector, "data/events/2024-01-01.parquet")
    df = loader.load()
    print(f"Loaded {len(df)} rows")

    # Get file info
    info = loader.get_file_info()
    print(f"File info: {info}")

    # Load multiple files with pattern
    print("\nLoading multiple files with pattern...")
    loader = CloudLoader(
        connector,
        "data/events/",
        pattern="2024-01-*.parquet"
    )
    df = loader.load()
    print(f"Loaded {len(df)} rows from multiple files")
    print(f"Source files: {df['_source_file'].unique().tolist()}")


def example_file_operations():
    """Example: File existence and size checks."""
    print("\n" + "=" * 60)
    print("Example: File Operations")
    print("=" * 60)

    connector = S3Connector(
        bucket="my-data-bucket",
    )

    # Check if file exists
    file_path = "data/users.csv"
    if connector.file_exists(file_path):
        print(f"\n{file_path} exists!")

        # Get file size
        size = connector.get_file_size(file_path)
        print(f"Size: {size:,} bytes ({size / 1024:.2f} KB)")
    else:
        print(f"\n{file_path} does not exist")


def example_error_handling():
    """Example: Handling errors gracefully."""
    print("\n" + "=" * 60)
    print("Example: Error Handling")
    print("=" * 60)

    try:
        # Try to connect with invalid credentials
        connector = S3Connector(
            bucket="nonexistent-bucket-12345",
            access_key="invalid",
            secret_key="invalid",
        )
        connector.list_files()
    except AuthenticationError as e:
        print(f"\nAuthentication error: {e}")
    except ConnectionError as e:
        print(f"\nConnection error: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")


def example_with_environment_variables():
    """Example: Using environment variables for credentials."""
    print("\n" + "=" * 60)
    print("Example: Environment Variables")
    print("=" * 60)

    import os

    # Show how to set environment variables
    print("""
To use environment variables, set:
    export AWS_ACCESS_KEY_ID=your_access_key
    export AWS_SECRET_ACCESS_KEY=your_secret_key
    export AWS_DEFAULT_REGION=us-east-1

Then create connector without explicit credentials:
    connector = S3Connector(bucket="my-bucket")
    """)

    # Check if credentials are set
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        print("AWS credentials found in environment!")
        S3Connector(bucket="my-bucket")
        # Use connector...
    else:
        print("No AWS credentials in environment.")


if __name__ == "__main__":
    print("DataCheck S3 Connector Examples")
    print("================================\n")

    # Uncomment the examples you want to run:

    # example_list_files()
    # example_read_file()
    # example_cloud_loader()
    # example_file_operations()
    # example_error_handling()
    # example_with_environment_variables()

    print("\nUncomment the examples in the script to run them.")
    print("Make sure AWS credentials are configured first.")
