"""Microsoft SQL Server database connector."""


import pandas as pd
import re
import logging
from typing import Any

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

from datacheck.connectors.base import DatabaseConnector
from datacheck.exceptions import DataLoadError

logger = logging.getLogger(__name__)


class SQLServerConnector(DatabaseConnector):
    """Microsoft SQL Server database connector.

    Connects to SQL Server databases using pyodbc and loads data into pandas DataFrames.

    Example:
        >>> connector = SQLServerConnector("mssql://user:pass@localhost/mydb")
        >>> with connector:
        ...     df = connector.load_table("users")
    """

    def __init__(self, connection_string: str) -> None:
        """Initialize SQL Server connector.

        Args:
            connection_string: SQL Server connection string

        Raises:
            DataLoadError: If pyodbc is not installed
        """
        if not PYODBC_AVAILABLE:
            raise DataLoadError(
                "pyodbc is not installed. Install it with: pip install pyodbc"
            )

        super().__init__(connection_string)
        self.connection: object = None
        self._build_odbc_connection_string()

    def _build_odbc_connection_string(self) -> None:
        """Build ODBC connection string from URL format."""
        try:
            from sqlalchemy.engine.url import make_url
            url = make_url(self.connection_string)

            driver = "{ODBC Driver 17 for SQL Server}"
            server = url.host or "localhost"
            database = url.database

            if url.username and url.password:
                self.odbc_string = (
                    f"DRIVER={driver};"
                    f"SERVER={server};"
                    f"DATABASE={database};"
                    f"UID={url.username};"
                    f"PWD={url.password}"
                )
            else:
                # Use Windows authentication
                self.odbc_string = (
                    f"DRIVER={driver};"
                    f"SERVER={server};"
                    f"DATABASE={database};"
                    f"Trusted_Connection=yes"
                )
        except Exception as e:
            raise DataLoadError(f"Invalid SQL Server connection string: {e}") from e

    def connect(self) -> None:
        """Establish connection to SQL Server database.

        Raises:
            DataLoadError: If connection fails
        """
        try:
            self.connection = pyodbc.connect(self.odbc_string)
            self._is_connected = True
        except pyodbc.Error as e:
            raise DataLoadError(f"Failed to connect to SQL Server: {e}") from e
        except Exception as e:
            raise DataLoadError(f"Unexpected error connecting to SQL Server: {e}") from e

    def disconnect(self) -> None:
        """Close SQL Server connection with proper cleanup and error handling."""
        if self.connection:
            try:
                self.connection.close()  # type: ignore[attr-defined]
                logger.info("SQL Server connection closed successfully")
            except Exception as e:
                logger.warning(f"Error closing SQL Server connection: {e}")
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
        """Load data from SQL Server table.

        Args:
            table_name: Name of the table to load
            where: Optional WHERE clause (without 'WHERE' keyword).
                   DEPRECATED: Use filters parameter instead for safety.
            limit: Optional row limit (uses TOP in SQL Server)
            filters: Dictionary of column-value pairs for safe filtering.
                     Example: {"status": "active", "age": 25}

        Returns:
            DataFrame containing table data

        Raises:
            DataLoadError: If not connected, table loading fails, or SQL injection detected
        """
        if not self.is_connected:
            raise DataLoadError("Not connected to database. Call connect() first.")

        # Validate table name
        if not re.match(r'^[a-zA-Z0-9_.]+$', table_name):
            raise DataLoadError(
                f"Invalid table name '{table_name}'. "
                "Table names must contain only alphanumeric characters, underscores, and dots."
            )

        try:
            # Build query with parameterization
            params = []

            # SQL Server uses TOP instead of LIMIT
            if limit:
                if not isinstance(limit, int) or limit <= 0:
                    raise DataLoadError(f"Invalid limit: {limit}. Must be a positive integer.")
                query_parts = [f"SELECT TOP {int(limit)} * FROM [{table_name}]"]
            else:
                query_parts = [f"SELECT * FROM [{table_name}]"]

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
                    conditions.append(f"[{column}] = ?")
                    params.append(value)

            elif where:
                # Legacy where clause - validate for dangerous patterns
                self._validate_where_clause(where)
                conditions.append(where)

            if conditions:
                query_parts.append(" WHERE " + " AND ".join(conditions))

            query_string = " ".join(query_parts)

            # Execute query with parameters if available
            if params:
                return pd.read_sql_query(query_string, self.connection, params=params)  # type: ignore[call-overload,no-any-return]
            else:
                return pd.read_sql_query(query_string, self.connection)  # type: ignore[call-overload,no-any-return]

        except DataLoadError:
            # Re-raise DataLoadErrors (e.g., from validation) without wrapping
            raise
        except pyodbc.Error as e:
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
        ]

        for pattern, description in dangerous_patterns:
            if re.search(pattern, where, re.IGNORECASE):
                raise DataLoadError(
                    f"Potentially dangerous SQL pattern detected in WHERE clause: {description}. "
                    "Use the 'filters' parameter instead for safe filtering."
                )

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query on SQL Server database.

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
        except pyodbc.Error as e:
            raise DataLoadError(f"Failed to execute query: {e}") from e
        except Exception as e:
            raise DataLoadError(f"Unexpected error executing query: {e}") from e
