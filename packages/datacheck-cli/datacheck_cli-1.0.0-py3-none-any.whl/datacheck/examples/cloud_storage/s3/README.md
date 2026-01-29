# S3 Examples

This directory contains example scripts for working with AWS S3 in DataCheck.

## Files

| File | Description |
|------|-------------|
| `s3_basic_example.py` | Basic S3 operations: list files, read data, check existence |
| `s3_batch_validation.py` | Batch validation workflow for multiple files |
| `config_example.yaml` | Example configuration file for data validation |

## Prerequisites

1. Install DataCheck with cloud support:
   ```bash
   pip install datacheck[cloud]
   ```

2. Configure AWS credentials using one of these methods:

   **Option A: AWS Profile** (recommended)
   ```bash
   # ~/.aws/credentials
   [dev]
   aws_access_key_id = AKIA...
   aws_secret_access_key = ...
   ```

   **Option B: Environment Variables**
   ```bash
   export AWS_ACCESS_KEY_ID=AKIA...
   export AWS_SECRET_ACCESS_KEY=...
   export AWS_DEFAULT_REGION=us-east-1
   ```

## Running Examples

1. Edit the example script to update bucket names and paths
2. Uncomment the example functions you want to run
3. Run the script:
   ```bash
   python s3_basic_example.py
   ```

## CLI Examples

```bash
# List files
datacheck list-files s3://my-bucket/data/ --pattern "*.csv"

# Validate single file
datacheck validate --source s3://my-bucket/data/users.csv

# Validate multiple files
datacheck validate --source s3://my-bucket/data/ --pattern "*.parquet"

# With AWS profile
datacheck validate --source s3://my-bucket/data.csv --aws-profile production
```
