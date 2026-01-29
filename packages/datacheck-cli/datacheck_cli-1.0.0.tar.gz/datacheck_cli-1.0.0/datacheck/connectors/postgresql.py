"""PostgreSQL database connector."""


import pandas as pd
import re
import logging
from typing import Any

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from datacheck.connectors.base import DatabaseConnector
from datacheck.exceptions import DataLoadError

logger = logging.getLogger(__name__)


class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL database connector.

    Connects to PostgreSQL databases using psycopg2 and loads data into pandas DataFrames.

    Example:
        >>> connector = PostgreSQLConnector("postgresql://user:pass@localhost:5432/mydb")
        >>> with connector:
        ...     df = connector.load_table("users", where="active = true")
    """

    def __init__(self, connection_string: str) -> None:
        """Initialize PostgreSQL connector.

        Args:
            connection_string: PostgreSQL connection string

        Raises:
            DataLoadError: If psycopg2 is not installed
        """
        if not PSYCOPG2_AVAILABLE:
            raise DataLoadError(
                "psycopg2 is not installed. Install it with: pip install psycopg2-binary"
            )

        super().__init__(connection_string)
        self.connection: object = None

    def connect(self) -> None:
        """Establish connection to PostgreSQL database.

        Raises:
            DataLoadError: If connection fails
        """
        try:
            self.connection = psycopg2.connect(self.connection_string)
            self._is_connected = True
        except psycopg2.Error as e:
            raise DataLoadError(f"Failed to connect to PostgreSQL: {e}") from e
        except Exception as e:
            raise DataLoadError(f"Unexpected error connecting to PostgreSQL: {e}") from e

    def disconnect(self) -> None:
        """Close PostgreSQL connection with proper cleanup and error handling."""
        if self.connection:
            try:
                self.connection.close()  # type: ignore[attr-defined]
                logger.info("PostgreSQL connection closed successfully")
            except Exception as e:
                logger.warning(f"Error closing PostgreSQL connection: {e}")
            finally:
                self._is_connected = False
                self.connection = None

    def load_table(
        self,
        table_name: str,
        where: str | None = None,
        limit: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Load data from PostgreSQL table.

        Args:
            table_name: Name of the table to load
            where: Optional WHERE clause (without 'WHERE' keyword).
                   DEPRECATED: Use filters parameter instead for safety.
                   If used, will validate for dangerous patterns.
            limit: Optional row limit
            filters: Dictionary of column-value pairs for safe filtering.
                     Example: {"status": "active", "age": 25}
                     This is the recommended way to filter data.

        Returns:
            DataFrame containing table data

        Raises:
            DataLoadError: If not connected, table loading fails, or SQL injection detected

        Security Note:
            The `where` parameter is vulnerable to SQL injection and should be avoided.
            Use the `filters` parameter instead, which uses parameterized queries.
        """
        if not self.is_connected:
            raise DataLoadError("Not connected to database. Call connect() first.")

        # Validate table name (alphanumeric, underscore, dots for schema)
        if not re.match(r'^[a-zA-Z0-9_.]+$', table_name):
            raise DataLoadError(
                f"Invalid table name '{table_name}'. "
                "Table names must contain only alphanumeric characters, underscores, and dots."
            )

        try:
            # Build query with parameterization
            params = []
            query_parts = [f'SELECT * FROM "{table_name}"']

            # Handle both where and filters (filters takes precedence)
            conditions = []

            if filters:
                # Build WHERE clause with parameters (SAFE)
                for column, value in filters.items():
                    # Validate column name
                    if not re.match(r'^[a-zA-Z0-9_]+$', column):
                        raise DataLoadError(
                            f"Invalid column name '{column}'. "
                            "Column names must be alphanumeric with underscores only."
                        )
                    conditions.append(f'"{column}" = %s')
                    params.append(value)

            elif where:
                # Legacy where clause - validate for dangerous patterns
                self._validate_where_clause(where)
                # Note: This is still vulnerable but at least catches obvious attacks
                conditions.append(where)

            if conditions:
                query_parts.append(" WHERE " + " AND ".join(conditions))

            if limit:
                if not isinstance(limit, int) or limit <= 0:
                    raise DataLoadError(f"Invalid limit: {limit}. Must be a positive integer.")
                query_parts.append(f" LIMIT {int(limit)}")

            query_string = "".join(query_parts)

            # Execute query with parameters if available
            if params:
                return pd.read_sql_query(query_string, self.connection, params=params)  # type: ignore[call-overload,no-any-return]
            else:
                return pd.read_sql_query(query_string, self.connection)  # type: ignore[call-overload,no-any-return]

        except DataLoadError:
            # Re-raise DataLoadErrors (e.g., from validation) without wrapping
            raise
        except psycopg2.Error as e:
            raise DataLoadError(f"Failed to load table '{table_name}': {e}") from e
        except Exception as e:
            raise DataLoadError(f"Unexpected error loading table '{table_name}': {e}") from e

    def _validate_where_clause(self, where: str) -> None:
        """Validate WHERE clause for dangerous SQL injection patterns.

        Args:
            where: WHERE clause to validate

        Raises:
            DataLoadError: If dangerous pattern detected
        """
        dangerous_patterns = [
            (r';\s*(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER|EXEC|EXECUTE)\s', 'SQL command injection'),
            (r'--', 'SQL comment injection'),
            (r'/\*.*\*/', 'SQL comment block'),
            (r'xp_cmdshell', 'Command execution attempt'),
            (r'UNION\s+SELECT', 'UNION injection'),
            (r'INTO\s+(OUTFILE|DUMPFILE)', 'File writing attempt'),
        ]

        for pattern, description in dangerous_patterns:
            if re.search(pattern, where, re.IGNORECASE):
                raise DataLoadError(
                    f"Potentially dangerous SQL pattern detected in WHERE clause: {description}. "
                    "Use the 'filters' parameter instead for safe filtering."
                )

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query on PostgreSQL database.

        Args:
            query: SQL query to execute

        Returns:
            DataFrame containing query results

        Raises:
            DataLoadError: If not connected or query execution fails
        """
        if not self.is_connected:
            raise DataLoadError("Not connected to database. Call connect() first.")

        try:
            return pd.read_sql_query(query, self.connection)  # type: ignore[call-overload,no-any-return]
        except psycopg2.Error as e:
            raise DataLoadError(f"Failed to execute query: {e}") from e
        except Exception as e:
            raise DataLoadError(f"Unexpected error executing query: {e}") from e
