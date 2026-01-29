"""Database management for DataCheck API.

Provides SQLite storage for validation results and metrics.
"""

import sqlite3
from pathlib import Path
from typing import Any
from contextlib import contextmanager
from datetime import datetime
import json
import threading


class Database:
    """SQLite database manager for validation results."""

    def __init__(self, db_path: str = "datacheck.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._initialized = False
        # Instance-level thread-local storage for connections
        self._local = threading.local()

    def initialize(self) -> None:
        """Create database tables if they don't exist."""
        conn = self._get_connection()

        # Validations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                source TEXT,
                status TEXT NOT NULL,
                pass_rate REAL,
                quality_score REAL,
                total_rows INTEGER,
                total_columns INTEGER,
                rules_run INTEGER,
                rules_passed INTEGER,
                rules_failed INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                duration_seconds REAL,
                config_hash TEXT,
                metadata TEXT
            )
        """)

        # Validation rules table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS validation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                validation_id INTEGER NOT NULL,
                rule_name TEXT NOT NULL,
                rule_type TEXT,
                column_name TEXT,
                status TEXT NOT NULL,
                passed_rows INTEGER DEFAULT 0,
                failed_rows INTEGER DEFAULT 0,
                error_message TEXT,
                details TEXT,
                FOREIGN KEY (validation_id) REFERENCES validations(id)
            )
        """)

        # Alerts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                validation_id INTEGER,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                source TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                acknowledged INTEGER DEFAULT 0,
                acknowledged_at DATETIME,
                metadata TEXT,
                FOREIGN KEY (validation_id) REFERENCES validations(id)
            )
        """)

        # Metrics table for time-series data
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                source TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)

        # Create indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_validations_timestamp
            ON validations(timestamp)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_validations_status
            ON validations(status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rules_validation
            ON validation_rules(validation_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
            ON alerts(timestamp)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp
            ON metrics(metric_name, timestamp)
        """)

        conn.commit()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection for this instance."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    @contextmanager
    def get_cursor(self):
        """Get database cursor with automatic commit/rollback."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def query(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query.

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            Cursor with results
        """
        conn = self._get_connection()
        return conn.execute(sql, params)

    def insert_validation(self, data: dict[str, Any]) -> int:
        """Insert validation record.

        Args:
            data: Validation data

        Returns:
            Inserted row ID
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO validations
                (filename, source, status, pass_rate, quality_score,
                 total_rows, total_columns, rules_run, rules_passed,
                 rules_failed, duration_seconds, config_hash, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('filename', ''),
                data.get('source', ''),
                data.get('status', 'unknown'),
                data.get('pass_rate'),
                data.get('quality_score'),
                data.get('total_rows'),
                data.get('total_columns'),
                data.get('rules_run'),
                data.get('rules_passed'),
                data.get('rules_failed'),
                data.get('duration_seconds'),
                data.get('config_hash'),
                json.dumps(data.get('metadata', {})),
            ))
            return cursor.lastrowid

    def insert_rule_result(self, data: dict[str, Any]) -> int:
        """Insert rule result.

        Args:
            data: Rule result data

        Returns:
            Inserted row ID
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO validation_rules
                (validation_id, rule_name, rule_type, column_name,
                 status, passed_rows, failed_rows, error_message, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('validation_id'),
                data.get('rule_name', ''),
                data.get('rule_type', ''),
                data.get('column_name', ''),
                data.get('status', 'unknown'),
                data.get('passed_rows', 0),
                data.get('failed_rows', 0),
                data.get('error_message'),
                json.dumps(data.get('details', {})),
            ))
            return cursor.lastrowid

    def insert_alert(self, data: dict[str, Any]) -> int:
        """Insert alert record.

        Args:
            data: Alert data

        Returns:
            Inserted row ID
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO alerts
                (validation_id, severity, title, message, source, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data.get('validation_id'),
                data.get('severity', 'info'),
                data.get('title', ''),
                data.get('message', ''),
                data.get('source', ''),
                json.dumps(data.get('metadata', {})),
            ))
            return cursor.lastrowid

    def insert_metric(self, name: str, value: float, source: str = None) -> int:
        """Insert metric record.

        Args:
            name: Metric name
            value: Metric value
            source: Metric source

        Returns:
            Inserted row ID
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO metrics (metric_name, metric_value, source)
                VALUES (?, ?, ?)
            """, (name, value, source))
            return cursor.lastrowid

    def get_validation(self, validation_id: int) -> dict[str, Any] | None:
        """Get validation by ID.

        Args:
            validation_id: Validation ID

        Returns:
            Validation record or None
        """
        cursor = self.query(
            "SELECT * FROM validations WHERE id = ?",
            (validation_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_validation_rules(self, validation_id: int) -> list[dict[str, Any]]:
        """Get rules for a validation.

        Args:
            validation_id: Validation ID

        Returns:
            List of rule results
        """
        cursor = self.query(
            "SELECT * FROM validation_rules WHERE validation_id = ?",
            (validation_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_recent_validations(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent validations.

        Args:
            limit: Maximum number to return

        Returns:
            List of validation records
        """
        cursor = self.query("""
            SELECT * FROM validations
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_validation_summary(
        self,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Get validation summary statistics.

        Args:
            since: Only include validations after this time

        Returns:
            Summary statistics
        """
        if since:
            cursor = self.query("""
                SELECT
                    COUNT(*) as total_checks,
                    AVG(CASE WHEN status = 'passed' THEN 100.0 ELSE 0.0 END) as pass_rate,
                    AVG(quality_score) as avg_quality,
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(total_rows) as total_rows_checked
                FROM validations
                WHERE timestamp > ?
            """, (since,))
        else:
            cursor = self.query("""
                SELECT
                    COUNT(*) as total_checks,
                    AVG(CASE WHEN status = 'passed' THEN 100.0 ELSE 0.0 END) as pass_rate,
                    AVG(quality_score) as avg_quality,
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(total_rows) as total_rows_checked
                FROM validations
            """)

        row = cursor.fetchone()
        return dict(row) if row else {}

    def get_trends(
        self,
        since: datetime | None = None,
        group_by: str = "hour",
    ) -> list[dict[str, Any]]:
        """Get validation trends over time.

        Args:
            since: Start time for trends
            group_by: Grouping ('hour', 'day', 'week')

        Returns:
            List of trend data points
        """
        if group_by == "hour":
            time_format = "%Y-%m-%d %H:00:00"
        elif group_by == "day":
            time_format = "%Y-%m-%d"
        else:
            time_format = "%Y-%W"

        if since:
            cursor = self.query(f"""
                SELECT
                    strftime('{time_format}', timestamp) as period,
                    AVG(CASE WHEN status = 'passed' THEN 100.0 ELSE 0.0 END) as pass_rate,
                    COUNT(*) as count,
                    AVG(quality_score) as avg_quality
                FROM validations
                WHERE timestamp > ?
                GROUP BY period
                ORDER BY period
            """, (since,))
        else:
            cursor = self.query(f"""
                SELECT
                    strftime('{time_format}', timestamp) as period,
                    AVG(CASE WHEN status = 'passed' THEN 100.0 ELSE 0.0 END) as pass_rate,
                    COUNT(*) as count,
                    AVG(quality_score) as avg_quality
                FROM validations
                GROUP BY period
                ORDER BY period
            """)

        return [dict(row) for row in cursor.fetchall()]

    def get_top_issues(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most common validation failures.

        Args:
            limit: Maximum number to return

        Returns:
            List of top issues
        """
        cursor = self.query("""
            SELECT
                rule_name,
                rule_type,
                column_name,
                COUNT(*) as failure_count,
                AVG(failed_rows) as avg_failed_rows
            FROM validation_rules
            WHERE status = 'failed'
            GROUP BY rule_name, column_name
            ORDER BY failure_count DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def get_alerts(
        self,
        since: datetime | None = None,
        unacknowledged_only: bool = False,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get alerts.

        Args:
            since: Only include alerts after this time
            unacknowledged_only: Only return unacknowledged alerts
            limit: Maximum number to return

        Returns:
            List of alerts
        """
        conditions = []
        params = []

        if since:
            conditions.append("timestamp > ?")
            params.append(since)

        if unacknowledged_only:
            conditions.append("acknowledged = 0")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        cursor = self.query(f"""
            SELECT * FROM alerts
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """, tuple(params))

        return [dict(row) for row in cursor.fetchall()]

    def acknowledge_alert(self, alert_id: int) -> bool:
        """Acknowledge an alert.

        Args:
            alert_id: Alert ID

        Returns:
            True if acknowledged
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE alerts
                SET acknowledged = 1, acknowledged_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (alert_id,))
            return cursor.rowcount > 0

    def close(self) -> None:
        """Close database connection for current thread."""
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
