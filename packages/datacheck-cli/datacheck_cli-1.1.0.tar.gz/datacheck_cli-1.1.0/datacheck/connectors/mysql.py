"""MySQL database connector."""


import pandas as pd
import re
import logging
from typing import Any

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

from datacheck.connectors.base import DatabaseConnector
from datacheck.exceptions import DataLoadError

logger = logging.getLogger(__name__)


class MySQLConnector(DatabaseConnector):
    """MySQL database connector.

    Connects to MySQL databases using mysql-connector-python and loads data
    into pandas DataFrames.

    Example:
        >>> connector = MySQLConnector("mysql://user:pass@localhost:3306/mydb")
        >>> with connector:
        ...     df = connector.load_table("users")
    """

    def __init__(self, connection_string: str) -> None:
        """Initialize MySQL connector.

        Args:
            connection_string: MySQL connection string

        Raises:
            DataLoadError: If mysql-connector-python is not installed
        """
        if not MYSQL_AVAILABLE:
            raise DataLoadError(
                "mysql-connector-python is not installed. "
                "Install it with: pip install mysql-connector-python"
            )

        super().__init__(connection_string)
        self.connection: object = None
        self._parse_connection_string()

    def _parse_connection_string(self) -> None:
        """Parse MySQL connection string into components."""
        # Simple parsing of mysql://user:pass@host:port/database
        try:
            from sqlalchemy.engine.url import make_url
            url = make_url(self.connection_string)

            self.config = {
                "host": url.host or "localhost",
                "port": url.port or 3306,
                "user": url.username,
                "password": url.password,
                "database": url.database,
            }
        except Exception as e:
            raise DataLoadError(f"Invalid MySQL connection string: {e}") from e

    def connect(self) -> None:
        """Establish connection to MySQL database.

        Raises:
            DataLoadError: If connection fails
        """
        try:
            self.connection = mysql.connector.connect(**self.config)
            self._is_connected = True
        except MySQLError as e:
            raise DataLoadError(f"Failed to connect to MySQL: {e}") from e
        except Exception as e:
            raise DataLoadError(f"Unexpected error connecting to MySQL: {e}") from e

    def disconnect(self) -> None:
        """Close MySQL connection with proper cleanup and error handling."""
        if self.connection:
            try:
                if self.connection.is_connected():  # type: ignore[attr-defined]
                    self.connection.close()  # type: ignore[attr-defined]
                    logger.info("MySQL connection closed successfully")
            except Exception as e:
                logger.warning(f"Error closing MySQL connection: {e}")
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
        """Load data from MySQL table.

        Args:
            table_name: Name of the table to load
            where: Optional WHERE clause (without 'WHERE' keyword).
                   DEPRECATED: Use filters parameter instead for safety.
            limit: Optional row limit
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
            query_parts = [f"SELECT * FROM `{table_name}`"]

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
                    conditions.append(f"`{column}` = %s")
                    params.append(value)

            elif where:
                # Legacy where clause - validate for dangerous patterns
                self._validate_where_clause(where)
                conditions.append(where)

            if conditions:
                query_parts.append(" WHERE " + " AND ".join(conditions))

            if limit:
                if not isinstance(limit, int) or limit <= 0:
                    raise DataLoadError(f"Invalid limit: {limit}. Must be a positive integer.")
                query_parts.append(f" LIMIT {int(limit)}")

            query_string = " ".join(query_parts)

            # Execute query with parameters if available
            if params:
                return pd.read_sql_query(query_string, self.connection, params=params)  # type: ignore[call-overload,no-any-return]
            else:
                return pd.read_sql_query(query_string, self.connection)  # type: ignore[call-overload,no-any-return]

        except DataLoadError:
            # Re-raise DataLoadErrors (e.g., from validation) without wrapping
            raise
        except MySQLError as e:
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
        """Execute SQL query on MySQL database.

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
        except MySQLError as e:
            raise DataLoadError(f"Failed to execute query: {e}") from e
        except Exception as e:
            raise DataLoadError(f"Unexpected error executing query: {e}") from e
