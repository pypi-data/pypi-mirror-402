# Cloud Storage Guide

This guide covers connecting DataCheck to cloud storage providers for data validation.

## AWS S3

### Prerequisites

- AWS account with S3 access
- Configured AWS credentials (profile, environment variables, or IAM role)
- `boto3` library (included with `datacheck[cloud]`)

### Authentication Methods

#### 1. AWS Profile (Recommended for Development)

Configure profiles in `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[production]
aws_access_key_id = AKIAI44QH8DHBEXAMPLE
aws_secret_access_key = je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY
region = us-west-2
```

Use with CLI:
```bash
datacheck validate --source s3://bucket/data.csv --aws-profile production
```

Use with Python:
```python
from datacheck.connectors.s3 import S3Connector

connector = S3Connector(
    bucket="my-bucket",
    profile="production"
)
```

#### 2. Environment Variables

```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_DEFAULT_REGION=us-east-1

datacheck validate --source s3://bucket/data.csv
```

#### 3. IAM Roles (Recommended for Production)

When running on AWS infrastructure, DataCheck automatically uses the attached IAM role:

```python
# No credentials needed - uses IAM role
connector = S3Connector(bucket="my-bucket")
```

Required IAM permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket",
                "s3:HeadObject"
            ],
            "Resource": [
                "arn:aws:s3:::my-bucket",
                "arn:aws:s3:::my-bucket/*"
            ]
        }
    ]
}
```

#### 4. Explicit Credentials (Python API)

```python
connector = S3Connector(
    bucket="my-bucket",
    access_key="AKIAIOSFODNN7EXAMPLE",
    secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    region="us-east-1"
)
```

> **Warning**: Avoid hardcoding credentials. Use environment variables or AWS profiles instead.

### Basic Operations

#### List Files

```python
from datacheck.connectors.s3 import S3Connector

connector = S3Connector(
    bucket="my-data-bucket",
    prefix="raw/2024/",
    profile="dev"
)

# List all files
files = connector.list_files()
for f in files:
    print(f"Path: {f.path}")
    print(f"Size: {f.size} bytes")
    print(f"Modified: {f.last_modified}")

# List with pattern
csv_files = connector.list_files(pattern="*.csv")
parquet_files = connector.list_files(pattern="events_*.parquet")
```

#### Read Single File

```python
# Read CSV
df = connector.read_file("raw/2024/users.csv")

# Read Parquet
df = connector.read_file("raw/2024/events.parquet")

# Read JSON
df = connector.read_file("raw/2024/config.json")
```

#### Check File Existence

```python
if connector.file_exists("raw/2024/users.csv"):
    df = connector.read_file("raw/2024/users.csv")
else:
    print("File not found")
```

#### Get File Size

```python
size = connector.get_file_size("raw/2024/large_file.parquet")
print(f"File size: {size / 1024 / 1024:.2f} MB")
```

### Using CloudLoader

The `CloudLoader` class provides a higher-level interface:

```python
from datacheck.connectors.s3 import S3Connector
from datacheck.loader import CloudLoader

connector = S3Connector(bucket="my-bucket", prefix="data/")

# Load single file
loader = CloudLoader(connector, "data/users.csv")
df = loader.load()

# Load multiple files with pattern
loader = CloudLoader(connector, "data/events/", pattern="*.parquet")
df = loader.load()  # Concatenated DataFrame with _source_file column

# Get file information
info = loader.get_file_info()
print(f"Files: {info.get('file_count', 1)}")
print(f"Total size: {info.get('total_size', info.get('size'))} bytes")
```

### CLI Usage

```bash
# Validate single file
datacheck validate --source s3://bucket/data/users.csv --aws-profile dev

# Validate multiple files
datacheck validate --source s3://bucket/data/events/ --pattern "*.parquet"

# List files
datacheck list-files s3://bucket/data/ --pattern "*.csv"

# With specific region
datacheck validate --source s3://bucket/data.csv --aws-region eu-west-1
```

### Error Handling

```python
from datacheck.connectors.s3 import S3Connector
from datacheck.exceptions import ConnectionError, AuthenticationError

try:
    connector = S3Connector(bucket="my-bucket", profile="invalid")
    files = connector.list_files()
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except ConnectionError as e:
    print(f"Connection failed: {e}")
```

### Best Practices

1. **Use IAM roles in production** - Avoid storing credentials in code or config files

2. **Set appropriate prefixes** - Narrow down the search scope for better performance:
   ```python
   # Good - specific prefix
   connector = S3Connector(bucket="logs", prefix="app/2024/01/")

   # Avoid - scanning entire bucket
   connector = S3Connector(bucket="logs", prefix="")
   ```

3. **Use patterns for filtering** - More efficient than loading all files:
   ```python
   files = connector.list_files(pattern="*.parquet")
   ```

4. **Handle large files** - DataCheck supports chunked reading for large files

5. **Cache connectors** - Reuse connector instances for multiple operations

---

## Google Cloud Storage

### Prerequisites

- GCP account with Cloud Storage access
- Configured GCP credentials (service account or Application Default Credentials)
- `google-cloud-storage` library (included with `datacheck[cloud]`)

### Authentication Methods

#### 1. Service Account JSON File

```python
from datacheck.connectors.gcs import GCSConnector

connector = GCSConnector(
    bucket="my-bucket",
    project="my-project",
    credentials_path="/path/to/service-account.json"
)
```

CLI usage:
```bash
datacheck validate --source gs://bucket/data.csv --gcp-credentials /path/to/creds.json
```

#### 2. Application Default Credentials (ADC)

Set the environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

Or use `gcloud auth application-default login` for local development:
```bash
gcloud auth application-default login
```

Then create connector without explicit credentials:
```python
connector = GCSConnector(bucket="my-bucket", project="my-project")
```

### Basic Operations

```python
from datacheck.connectors.gcs import GCSConnector

connector = GCSConnector(
    bucket="my-data-bucket",
    prefix="raw/2024/",
    project="my-project",
)

# List all files
files = connector.list_files()
for f in files:
    print(f"Path: {f.path}, Size: {f.size} bytes")

# List with pattern
csv_files = connector.list_files(pattern="*.csv")

# Read file
df = connector.read_file("raw/2024/users.csv")

# Check file existence
if connector.file_exists("raw/2024/users.csv"):
    print("File exists!")
```

### CLI Usage

```bash
# List files
datacheck list-files gs://bucket/data/ --gcp-project my-project

# Validate file
datacheck validate --source gs://bucket/data.csv --gcp-project my-project

# With credentials file
datacheck validate --source gs://bucket/data.csv --gcp-credentials /path/to/creds.json
```

### Required IAM Permissions

```
storage.buckets.get
storage.objects.get
storage.objects.list
```

---

## Azure Blob Storage

### Prerequisites

- Azure account with Storage access
- Storage account credentials (connection string, account key, or SAS token)
- `azure-storage-blob` library (included with `datacheck[cloud]`)

### Authentication Methods

#### 1. Connection String (Recommended)

```python
from datacheck.connectors.azure import AzureConnector

connector = AzureConnector(
    container="my-container",
    connection_string="DefaultEndpointsProtocol=https;AccountName=..."
)
```

CLI usage:
```bash
datacheck validate --source az://container/data.csv --azure-connection-string "..."
```

#### 2. Account Name and Key

```python
connector = AzureConnector(
    container="my-container",
    account_name="mystorageaccount",
    account_key="your-account-key"
)
```

CLI usage:
```bash
datacheck validate --source az://container/data.csv --azure-account myaccount --azure-key mykey
```

#### 3. SAS Token

```python
connector = AzureConnector(
    container="my-container",
    account_name="mystorageaccount",
    sas_token="?sv=2020-08-04&ss=b&..."
)
```

### Basic Operations

```python
from datacheck.connectors.azure import AzureConnector

connector = AzureConnector(
    container="my-container",
    prefix="raw/2024/",
    connection_string="DefaultEndpointsProtocol=https;..."
)

# List all files
files = connector.list_files()
for f in files:
    print(f"Path: {f.path}, Size: {f.size} bytes")

# List with pattern
parquet_files = connector.list_files(pattern="*.parquet")

# Read file
df = connector.read_file("raw/2024/users.csv")

# Check file existence
if connector.file_exists("raw/2024/users.csv"):
    print("File exists!")
```

### CLI Usage

```bash
# List files
datacheck list-files az://container/data/ --azure-account myaccount --azure-key mykey

# Validate file with connection string
datacheck validate --source az://container/data.csv --azure-connection-string "..."

# Validate with account key
datacheck validate --source az://container/data.csv --azure-account myaccount --azure-key mykey
```

### URL Schemes

Azure Blob Storage supports multiple URL schemes:
- `az://container/path` (recommended)
- `azure://container/path`
- `wasb://container/path`
- `wasbs://container/path`

---

## Troubleshooting

### Common Issues

#### "NoCredentialsError: Unable to locate credentials"

**Cause**: AWS credentials not configured

**Solution**:
1. Check `~/.aws/credentials` exists and is properly formatted
2. Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables
3. Ensure IAM role is attached (for AWS infrastructure)

#### "AccessDenied: Access Denied"

**Cause**: Insufficient IAM permissions

**Solution**:
1. Verify IAM policy includes required S3 actions
2. Check bucket policy allows access
3. Ensure correct bucket name and region

#### "NoSuchBucket: The specified bucket does not exist"

**Cause**: Incorrect bucket name or region

**Solution**:
1. Verify bucket name is correct
2. Ensure region matches bucket's actual region
3. Check for typos in bucket name

#### Slow Performance with Many Files

**Cause**: Listing too many objects

**Solution**:
1. Use more specific prefix
2. Use pattern matching to filter files
3. Consider partitioning data by date/category

### GCS Issues

#### "DefaultCredentialsError: Could not automatically determine credentials"

**Cause**: GCP credentials not configured

**Solution**:
1. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
2. Run `gcloud auth application-default login` for local development
3. Pass `credentials_path` parameter to GCSConnector

#### "Forbidden: 403 ... does not have storage.objects.list access"

**Cause**: Insufficient IAM permissions

**Solution**:
1. Grant `Storage Object Viewer` role to the service account
2. Verify the service account has access to the bucket
3. Check bucket-level IAM policies

### Azure Issues

#### "AuthenticationError: Azure authentication required"

**Cause**: No valid Azure credentials provided

**Solution**:
1. Provide `connection_string` parameter
2. Or provide `account_name` with `account_key`
3. Or provide `account_name` with `sas_token`

#### "ResourceNotFoundError: The specified container does not exist"

**Cause**: Container name is incorrect or doesn't exist

**Solution**:
1. Verify container name is correct (case-sensitive)
2. Ensure the container exists in the storage account
3. Check that the storage account name is correct
