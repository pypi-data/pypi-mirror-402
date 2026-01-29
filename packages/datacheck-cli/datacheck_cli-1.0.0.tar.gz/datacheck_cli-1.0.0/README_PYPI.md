# DataCheck

**Fast, CLI-first data validation for modern data teams**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Quick Start

```bash
pip install datacheck-cli
datacheck validate data.csv --config validation.yaml
```

## Features

- **Multiple formats**: CSV, Parquet, PostgreSQL, MySQL, SQL Server, cloud storage (S3, GCS, Azure)
- **Simple YAML config**: Define rules in readable YAML
- **CI/CD ready**: Proper exit codes for automation
- **Enterprise features**: Parallel execution, sampling, Slack notifications, custom plugins

## Validation Rules

| Rule | Purpose |
|------|---------|
| `not_null` | No missing values |
| `min` / `max` | Numeric range |
| `unique` | No duplicates |
| `regex` | Pattern matching |
| `allowed_values` | Whitelist |

## Example Config

```yaml
checks:
  - name: user_validation
    column: user_id
    rules:
      not_null: true
      unique: true
      min: 1

  - name: email_check
    column: email
    rules:
      regex: "^[\\w.-]+@[\\w.-]+\\.\\w+$"
```

## Installation Options

```bash
pip install datacheck-cli              # Core
pip install datacheck-cli[postgresql]  # + PostgreSQL
pip install datacheck-cli[cloud]       # + S3, GCS, Azure
pip install datacheck-cli[all]         # Everything
```

## Links

- [GitHub](https://github.com/squrtech/datacheck)
- [Issues](https://github.com/squrtech/datacheck/issues)

## License

Apache License 2.0 - Copyright 2026 Squrtech
