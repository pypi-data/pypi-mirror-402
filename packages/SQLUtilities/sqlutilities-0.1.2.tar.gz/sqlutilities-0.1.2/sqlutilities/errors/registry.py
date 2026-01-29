"""
SQL Error Registry

This module contains the comprehensive registry of SQL errors.
- DialectErrorRegistry: Dataclass for dialect-specific error patterns
- SQLErrorRegistry: Main registry class for error classification and handling

Author: DataScience ToolBox
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Use try/except to handle both absolute and relative imports
try:
    from core.enums import SQLDialect
    from errors.patterns import ErrorCategory, ErrorPattern, RetryPolicy
except ImportError:
    from ..core.enums import SQLDialect
    from .patterns import ErrorPattern, ErrorCategory, RetryPolicy

from CoreUtilities import LogLevel, get_logger

# Configure logging
logger = get_logger("sql_error_registry", level=LogLevel.INFO, include_performance=True, include_emoji=True)


@dataclass
class DialectErrorRegistry:
    """Error registry for a specific SQL dialect."""

    dialect: SQLDialect
    driver_patterns: Dict[str, List[ErrorPattern]]  # driver_name -> patterns
    common_patterns: List[ErrorPattern]  # Common patterns for all drivers


class SQLErrorRegistry:
    """
    Comprehensive registry of SQL errors across all supported dialects and drivers.
    """

    def __init__(self):
        self._registries: Dict[SQLDialect, DialectErrorRegistry] = {}
        self._initialize_registries()

    def _initialize_registries(self):
        """Initialize error registries for all supported dialects."""

        # Oracle Database
        self._registries[SQLDialect.ORACLE] = DialectErrorRegistry(
            dialect=SQLDialect.ORACLE,
            driver_patterns={
                "oracledb": self._get_oracledb_patterns(),
                "cx_Oracle": self._get_cx_oracle_patterns(),
            },
            common_patterns=self._get_oracle_common_patterns(),
        )

        # PostgreSQL
        self._registries[SQLDialect.POSTGRES] = DialectErrorRegistry(
            dialect=SQLDialect.POSTGRES,
            driver_patterns={
                "psycopg2": self._get_psycopg2_patterns(),
                "psycopg": self._get_psycopg3_patterns(),
            },
            common_patterns=self._get_postgres_common_patterns(),
        )

        # SQL Server
        self._registries[SQLDialect.SQLSERVER] = DialectErrorRegistry(
            dialect=SQLDialect.SQLSERVER,
            driver_patterns={
                "pyodbc": self._get_pyodbc_sqlserver_patterns(),
                "pymssql": self._get_pymssql_patterns(),
            },
            common_patterns=self._get_sqlserver_common_patterns(),
        )

        # MySQL
        self._registries[SQLDialect.MYSQL] = DialectErrorRegistry(
            dialect=SQLDialect.MYSQL,
            driver_patterns={
                "mysql.connector": self._get_mysql_connector_patterns(),
                "pymysql": self._get_pymysql_patterns(),
            },
            common_patterns=self._get_mysql_common_patterns(),
        )

        # SQLite
        self._registries[SQLDialect.SQLITE] = DialectErrorRegistry(
            dialect=SQLDialect.SQLITE,
            driver_patterns={
                "sqlite3": self._get_sqlite3_patterns(),
            },
            common_patterns=self._get_sqlite_common_patterns(),
        )

        # BigQuery
        self._registries[SQLDialect.BIGQUERY] = DialectErrorRegistry(
            dialect=SQLDialect.BIGQUERY,
            driver_patterns={
                "google.cloud.bigquery": self._get_bigquery_client_patterns(),
                "pandas_gbq": self._get_pandas_gbq_patterns(),
            },
            common_patterns=self._get_bigquery_common_patterns(),
        )

        # Redshift
        self._registries[SQLDialect.REDSHIFT] = DialectErrorRegistry(
            dialect=SQLDialect.REDSHIFT,
            driver_patterns={
                "redshift_connector": self._get_redshift_connector_patterns(),
            },
            common_patterns=self._get_redshift_common_patterns(),
        )

    # Oracle Error Patterns
    def _get_oracle_common_patterns(self) -> List[ErrorPattern]:
        """Common Oracle error patterns across all drivers."""
        return [
            # Connection Errors
            ErrorPattern(
                error_code="ORA-12541",
                pattern=re.compile(r"ORA-12541.*TNS.*no listener", re.IGNORECASE),
                message_keywords=["TNS", "no listener", "ORA-12541"],
                category=ErrorCategory.CONNECTION,
                retry_policy=RetryPolicy.RETRYABLE_WITH_DELAY,
                description="TNS listener is not running or not accessible",
                suggested_action="Check if Oracle listener is running and network connectivity",
                retry_delay_seconds=5.0,
                max_retries=3,
            ),
            ErrorPattern(
                error_code="ORA-12514",
                pattern=re.compile(r"ORA-12514.*TNS.*could not resolve", re.IGNORECASE),
                message_keywords=["TNS", "could not resolve", "ORA-12514"],
                category=ErrorCategory.CONNECTION,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="TNS could not resolve the connect descriptor",
                suggested_action="Check service name or SID in connection string",
            ),
            # Authentication Errors
            ErrorPattern(
                error_code="ORA-01017",
                pattern=re.compile(r"ORA-01017.*invalid username/password", re.IGNORECASE),
                message_keywords=["invalid username", "password", "ORA-01017"],
                category=ErrorCategory.AUTHENTICATION,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Invalid username or password",
                suggested_action="Verify credentials and account status",
            ),
            # Deadlocks and Concurrency
            ErrorPattern(
                error_code="ORA-00060",
                pattern=re.compile(r"ORA-00060.*deadlock detected", re.IGNORECASE),
                message_keywords=["deadlock", "ORA-00060"],
                category=ErrorCategory.CONCURRENCY,
                retry_policy=RetryPolicy.RETRYABLE,
                description="Deadlock detected while waiting for resource",
                suggested_action="Retry transaction with exponential backoff",
                retry_delay_seconds=1.0,
                max_retries=3,
            ),
            # Resource Errors
            ErrorPattern(
                error_code="ORA-00020",
                pattern=re.compile(r"ORA-00020.*maximum number of processes", re.IGNORECASE),
                message_keywords=["maximum number of processes", "ORA-00020"],
                category=ErrorCategory.RESOURCE,
                retry_policy=RetryPolicy.RETRYABLE_WITH_DELAY,
                description="Maximum number of processes exceeded",
                suggested_action="Wait for processes to complete or increase process limit",
                retry_delay_seconds=10.0,
                max_retries=5,
            ),
            # Constraint Violations
            ErrorPattern(
                error_code="ORA-00001",
                pattern=re.compile(r"ORA-00001.*unique constraint.*violated", re.IGNORECASE),
                message_keywords=["unique constraint", "violated", "ORA-00001"],
                category=ErrorCategory.CONSTRAINT,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Unique constraint violation",
                suggested_action="Check for duplicate values or modify data",
            ),
            # Storage Errors
            ErrorPattern(
                error_code="ORA-01653",
                pattern=re.compile(r"ORA-01653.*unable to extend table", re.IGNORECASE),
                message_keywords=["unable to extend", "tablespace", "ORA-01653"],
                category=ErrorCategory.STORAGE,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Unable to extend table due to insufficient tablespace",
                suggested_action="Add more space to tablespace or cleanup old data",
                severity="CRITICAL",
            ),
        ]

    def _get_oracledb_patterns(self) -> List[ErrorPattern]:
        """Oracle-specific error patterns for oracledb driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"DPY-\d+", re.IGNORECASE),
                message_keywords=["DPY-"],
                category=ErrorCategory.DRIVER,
                retry_policy=RetryPolicy.CONDITIONAL,
                description="Oracle python-oracledb driver error",
                suggested_action="Check driver documentation for specific DPY error code",
            ),
        ]

    def _get_cx_oracle_patterns(self) -> List[ErrorPattern]:
        """Oracle-specific error patterns for cx_Oracle driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"cx_Oracle\.DatabaseError", re.IGNORECASE),
                message_keywords=["DatabaseError"],
                category=ErrorCategory.DRIVER,
                retry_policy=RetryPolicy.CONDITIONAL,
                description="cx_Oracle database error",
                suggested_action="Check underlying Oracle error code",
            ),
        ]

    # PostgreSQL Error Patterns
    def _get_postgres_common_patterns(self) -> List[ErrorPattern]:
        """Common PostgreSQL error patterns across all drivers."""
        return [
            # Connection Errors
            ErrorPattern(
                error_code="08006",
                pattern=re.compile(r"connection.*failed|could not connect", re.IGNORECASE),
                message_keywords=["connection failed", "could not connect"],
                category=ErrorCategory.CONNECTION,
                retry_policy=RetryPolicy.RETRYABLE_WITH_DELAY,
                description="Connection failure",
                suggested_action="Check network connectivity and server status",
                retry_delay_seconds=2.0,
                max_retries=3,
            ),
            # Authentication Errors
            ErrorPattern(
                error_code="28P01",
                pattern=re.compile(r"password authentication failed", re.IGNORECASE),
                message_keywords=["password authentication failed"],
                category=ErrorCategory.AUTHENTICATION,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Password authentication failed",
                suggested_action="Check username and password",
            ),
            # Deadlocks
            ErrorPattern(
                error_code="40P01",
                pattern=re.compile(r"deadlock detected", re.IGNORECASE),
                message_keywords=["deadlock detected"],
                category=ErrorCategory.CONCURRENCY,
                retry_policy=RetryPolicy.RETRYABLE,
                description="Deadlock detected",
                suggested_action="Retry transaction",
                retry_delay_seconds=0.5,
                max_retries=3,
            ),
            # Constraint Violations
            ErrorPattern(
                error_code="23505",
                pattern=re.compile(r"duplicate key.*violates unique constraint", re.IGNORECASE),
                message_keywords=["duplicate key", "unique constraint"],
                category=ErrorCategory.CONSTRAINT,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Duplicate key violates unique constraint",
                suggested_action="Check for duplicate values",
            ),
            # Storage/Resource
            ErrorPattern(
                error_code="53100",
                pattern=re.compile(r"disk full|no space left", re.IGNORECASE),
                message_keywords=["disk full", "no space left"],
                category=ErrorCategory.STORAGE,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Disk full or no space left on device",
                suggested_action="Free up disk space",
                severity="CRITICAL",
            ),
        ]

    def _get_psycopg2_patterns(self) -> List[ErrorPattern]:
        """PostgreSQL-specific error patterns for psycopg2 driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"psycopg2\.OperationalError", re.IGNORECASE),
                message_keywords=["OperationalError"],
                category=ErrorCategory.CONNECTION,
                retry_policy=RetryPolicy.RETRYABLE_WITH_DELAY,
                description="Psycopg2 operational error",
                suggested_action="Check connection and retry",
                retry_delay_seconds=1.0,
            ),
        ]

    def _get_psycopg3_patterns(self) -> List[ErrorPattern]:
        """PostgreSQL-specific error patterns for psycopg3 driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"psycopg\.OperationalError", re.IGNORECASE),
                message_keywords=["OperationalError"],
                category=ErrorCategory.CONNECTION,
                retry_policy=RetryPolicy.RETRYABLE_WITH_DELAY,
                description="Psycopg3 operational error",
                suggested_action="Check connection and retry",
                retry_delay_seconds=1.0,
            ),
        ]

    # SQL Server Error Patterns
    def _get_sqlserver_common_patterns(self) -> List[ErrorPattern]:
        """Common SQL Server error patterns across all drivers."""
        return [
            # Connection Errors
            ErrorPattern(
                error_code=2,
                pattern=re.compile(r"Named Pipes Provider.*could not open", re.IGNORECASE),
                message_keywords=["Named Pipes", "could not open"],
                category=ErrorCategory.CONNECTION,
                retry_policy=RetryPolicy.RETRYABLE_WITH_DELAY,
                description="Named Pipes connection error",
                suggested_action="Check SQL Server service and network connectivity",
                retry_delay_seconds=5.0,
            ),
            # Authentication
            ErrorPattern(
                error_code=18456,
                pattern=re.compile(r"Login failed", re.IGNORECASE),
                message_keywords=["Login failed"],
                category=ErrorCategory.AUTHENTICATION,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Login failed for user",
                suggested_action="Check credentials and user permissions",
            ),
            # Deadlocks
            ErrorPattern(
                error_code=1205,
                pattern=re.compile(r"deadlock victim", re.IGNORECASE),
                message_keywords=["deadlock victim"],
                category=ErrorCategory.CONCURRENCY,
                retry_policy=RetryPolicy.RETRYABLE,
                description="Transaction was deadlock victim",
                suggested_action="Retry transaction",
                retry_delay_seconds=1.0,
                max_retries=3,
            ),
            # Constraint Violations
            ErrorPattern(
                error_code=2627,
                pattern=re.compile(r"duplicate key.*unique.*constraint", re.IGNORECASE),
                message_keywords=["duplicate key", "unique constraint"],
                category=ErrorCategory.CONSTRAINT,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Violation of unique key constraint",
                suggested_action="Check for duplicate values",
            ),
            # Storage
            ErrorPattern(
                error_code=1105,
                pattern=re.compile(r"disk.*full|insufficient space", re.IGNORECASE),
                message_keywords=["disk full", "insufficient space"],
                category=ErrorCategory.STORAGE,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Could not allocate space due to insufficient disk space",
                suggested_action="Free up disk space or add more storage",
                severity="CRITICAL",
            ),
        ]

    def _get_pyodbc_sqlserver_patterns(self) -> List[ErrorPattern]:
        """SQL Server-specific error patterns for pyodbc driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"pyodbc\.Error", re.IGNORECASE),
                message_keywords=["pyodbc.Error"],
                category=ErrorCategory.DRIVER,
                retry_policy=RetryPolicy.CONDITIONAL,
                description="PyODBC driver error",
                suggested_action="Check underlying SQL Server error",
            ),
        ]

    def _get_pymssql_patterns(self) -> List[ErrorPattern]:
        """SQL Server-specific error patterns for pymssql driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"pymssql\.Error", re.IGNORECASE),
                message_keywords=["pymssql.Error"],
                category=ErrorCategory.DRIVER,
                retry_policy=RetryPolicy.CONDITIONAL,
                description="PyMSSQL driver error",
                suggested_action="Check underlying SQL Server error",
            ),
        ]

    # MySQL Error Patterns
    def _get_mysql_common_patterns(self) -> List[ErrorPattern]:
        """Common MySQL error patterns across all drivers."""
        return [
            # Connection Errors
            ErrorPattern(
                error_code=2003,
                pattern=re.compile(r"Can't connect to MySQL server", re.IGNORECASE),
                message_keywords=["Can't connect", "MySQL server"],
                category=ErrorCategory.CONNECTION,
                retry_policy=RetryPolicy.RETRYABLE_WITH_DELAY,
                description="Cannot connect to MySQL server",
                suggested_action="Check server status and network connectivity",
                retry_delay_seconds=2.0,
                max_retries=3,
            ),
            # Authentication
            ErrorPattern(
                error_code=1045,
                pattern=re.compile(r"Access denied.*using password", re.IGNORECASE),
                message_keywords=["Access denied", "using password"],
                category=ErrorCategory.AUTHENTICATION,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Access denied for user",
                suggested_action="Check username and password",
            ),
            # Deadlocks
            ErrorPattern(
                error_code=1213,
                pattern=re.compile(r"Deadlock found", re.IGNORECASE),
                message_keywords=["Deadlock found"],
                category=ErrorCategory.CONCURRENCY,
                retry_policy=RetryPolicy.RETRYABLE,
                description="Deadlock found when trying to get lock",
                suggested_action="Retry transaction",
                retry_delay_seconds=0.5,
                max_retries=3,
            ),
            # Constraint Violations
            ErrorPattern(
                error_code=1062,
                pattern=re.compile(r"Duplicate entry.*for key", re.IGNORECASE),
                message_keywords=["Duplicate entry", "for key"],
                category=ErrorCategory.CONSTRAINT,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Duplicate entry for key",
                suggested_action="Check for duplicate values",
            ),
            # Storage
            ErrorPattern(
                error_code=1114,
                pattern=re.compile(r"table.*is full", re.IGNORECASE),
                message_keywords=["table", "is full"],
                category=ErrorCategory.STORAGE,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Table is full",
                suggested_action="Increase table space or cleanup old data",
                severity="CRITICAL",
            ),
        ]

    def _get_mysql_connector_patterns(self) -> List[ErrorPattern]:
        """MySQL-specific error patterns for mysql-connector-python driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"mysql\.connector\.Error", re.IGNORECASE),
                message_keywords=["mysql.connector.Error"],
                category=ErrorCategory.DRIVER,
                retry_policy=RetryPolicy.CONDITIONAL,
                description="MySQL Connector/Python error",
                suggested_action="Check underlying MySQL error",
            ),
        ]

    def _get_pymysql_patterns(self) -> List[ErrorPattern]:
        """MySQL-specific error patterns for PyMySQL driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"pymysql\.Error", re.IGNORECASE),
                message_keywords=["pymysql.Error"],
                category=ErrorCategory.DRIVER,
                retry_policy=RetryPolicy.CONDITIONAL,
                description="PyMySQL driver error",
                suggested_action="Check underlying MySQL error",
            ),
        ]

    # SQLite Error Patterns
    def _get_sqlite_common_patterns(self) -> List[ErrorPattern]:
        """Common SQLite error patterns."""
        return [
            # Database Locked
            ErrorPattern(
                error_code="SQLITE_BUSY",
                pattern=re.compile(r"database is locked", re.IGNORECASE),
                message_keywords=["database is locked"],
                category=ErrorCategory.CONCURRENCY,
                retry_policy=RetryPolicy.RETRYABLE,
                description="Database is locked",
                suggested_action="Retry after brief delay",
                retry_delay_seconds=0.1,
                max_retries=10,
            ),
            # Constraint Violations
            ErrorPattern(
                error_code="SQLITE_CONSTRAINT",
                pattern=re.compile(r"UNIQUE constraint failed", re.IGNORECASE),
                message_keywords=["UNIQUE constraint failed"],
                category=ErrorCategory.CONSTRAINT,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="UNIQUE constraint failed",
                suggested_action="Check for duplicate values",
            ),
            # Storage
            ErrorPattern(
                error_code="SQLITE_FULL",
                pattern=re.compile(r"database.*disk.*full", re.IGNORECASE),
                message_keywords=["database", "disk", "full"],
                category=ErrorCategory.STORAGE,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Database or disk is full",
                suggested_action="Free up disk space",
                severity="CRITICAL",
            ),
        ]

    def _get_sqlite3_patterns(self) -> List[ErrorPattern]:
        """SQLite-specific error patterns for sqlite3 driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"sqlite3\.Error", re.IGNORECASE),
                message_keywords=["sqlite3.Error"],
                category=ErrorCategory.DRIVER,
                retry_policy=RetryPolicy.CONDITIONAL,
                description="SQLite3 driver error",
                suggested_action="Check underlying SQLite error",
            ),
        ]

    # BigQuery Error Patterns
    def _get_bigquery_common_patterns(self) -> List[ErrorPattern]:
        """Common BigQuery error patterns across all drivers."""
        return [
            # Authentication
            ErrorPattern(
                error_code=401,
                pattern=re.compile(r"Request had invalid authentication", re.IGNORECASE),
                message_keywords=["invalid authentication"],
                category=ErrorCategory.AUTHENTICATION,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Invalid authentication credentials",
                suggested_action="Check service account key or OAuth credentials",
            ),
            # Rate Limiting
            ErrorPattern(
                error_code=429,
                pattern=re.compile(r"Quota exceeded|Rate limit exceeded", re.IGNORECASE),
                message_keywords=["Quota exceeded", "Rate limit exceeded"],
                category=ErrorCategory.RESOURCE,
                retry_policy=RetryPolicy.RETRYABLE_WITH_DELAY,
                description="Quota or rate limit exceeded",
                suggested_action="Implement exponential backoff retry",
                retry_delay_seconds=60.0,
                max_retries=3,
            ),
            # Schema/Resource Errors
            ErrorPattern(
                error_code=404,
                pattern=re.compile(r"Table.*not found|Dataset.*not found", re.IGNORECASE),
                message_keywords=["not found", "Table", "Dataset"],
                category=ErrorCategory.SCHEMA,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Table or dataset not found",
                suggested_action="Check table/dataset name and project permissions",
            ),
        ]

    def _get_bigquery_client_patterns(self) -> List[ErrorPattern]:
        """BigQuery-specific error patterns for google-cloud-bigquery driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"google\.cloud\.exceptions", re.IGNORECASE),
                message_keywords=["google.cloud.exceptions"],
                category=ErrorCategory.DRIVER,
                retry_policy=RetryPolicy.CONDITIONAL,
                description="Google Cloud BigQuery client error",
                suggested_action="Check specific Google Cloud exception",
            ),
        ]

    def _get_pandas_gbq_patterns(self) -> List[ErrorPattern]:
        """BigQuery-specific error patterns for pandas-gbq driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"pandas_gbq\.gbq\.GenericGBQException", re.IGNORECASE),
                message_keywords=["GenericGBQException"],
                category=ErrorCategory.DRIVER,
                retry_policy=RetryPolicy.CONDITIONAL,
                description="Pandas GBQ generic exception",
                suggested_action="Check underlying BigQuery error",
            ),
        ]

    # Redshift Error Patterns
    def _get_redshift_common_patterns(self) -> List[ErrorPattern]:
        """Common Redshift error patterns."""
        return [
            # Connection Errors
            ErrorPattern(
                error_code="08006",
                pattern=re.compile(r"connection.*failed|could not connect.*redshift", re.IGNORECASE),
                message_keywords=["connection failed", "could not connect", "redshift"],
                category=ErrorCategory.CONNECTION,
                retry_policy=RetryPolicy.RETRYABLE_WITH_DELAY,
                description="Redshift connection failure",
                suggested_action="Check cluster status and network connectivity",
                retry_delay_seconds=5.0,
                max_retries=3,
            ),
            # Resource Limits
            ErrorPattern(
                error_code="25006",
                pattern=re.compile(r"disk full|insufficient disk space", re.IGNORECASE),
                message_keywords=["disk full", "insufficient disk space"],
                category=ErrorCategory.STORAGE,
                retry_policy=RetryPolicy.NON_RETRYABLE,
                description="Insufficient disk space on cluster",
                suggested_action="Add more nodes or cleanup old data",
                severity="CRITICAL",
            ),
            # Serialization Errors (similar to deadlocks)
            ErrorPattern(
                error_code="40001",
                pattern=re.compile(r"serialization failure", re.IGNORECASE),
                message_keywords=["serialization failure"],
                category=ErrorCategory.CONCURRENCY,
                retry_policy=RetryPolicy.RETRYABLE,
                description="Serialization failure in concurrent transactions",
                suggested_action="Retry transaction",
                retry_delay_seconds=1.0,
                max_retries=3,
            ),
        ]

    def _get_redshift_connector_patterns(self) -> List[ErrorPattern]:
        """Redshift-specific error patterns for redshift_connector driver."""
        return [
            ErrorPattern(
                error_code=None,
                pattern=re.compile(r"redshift_connector\.Error", re.IGNORECASE),
                message_keywords=["redshift_connector.Error"],
                category=ErrorCategory.DRIVER,
                retry_policy=RetryPolicy.CONDITIONAL,
                description="Redshift connector error",
                suggested_action="Check underlying Redshift error",
            ),
        ]

    # Public Methods
    def classify_error(
        self, dialect: SQLDialect, driver_name: str, error: Exception, error_message: Optional[str] = None
    ) -> Optional[ErrorPattern]:
        """
        Classify an error and return the matching error pattern.

        Args:
            dialect: SQL dialect
            driver_name: Name of the database driver
            error: Exception object
            error_message: Optional error message (uses str(error) if not provided)

        Returns:
            ErrorPattern if match found, None otherwise
        """
        if error_message is None:
            error_message = str(error)

        # Get registry for dialect
        registry = self._registries.get(dialect.resolved_alias)
        if not registry:
            logger.warning(f"No error registry found for dialect: {dialect}", emoji="⚠️")
            return None

        # Check driver-specific patterns first
        driver_patterns = registry.driver_patterns.get(driver_name, [])
        for pattern in driver_patterns:
            if self._matches_pattern(pattern, error, error_message):
                logger.debug(f"Matched driver-specific pattern: {pattern.description}", emoji="🎯")
                return pattern

        # Check common patterns for the dialect
        for pattern in registry.common_patterns:
            if self._matches_pattern(pattern, error, error_message):
                logger.debug(f"Matched common pattern: {pattern.description}", emoji="🎯")
                return pattern

        logger.debug(f"No pattern matched for error: {error_message[:100]}...", emoji="❓")
        return None

    def _matches_pattern(self, pattern: ErrorPattern, error: Exception, error_message: str) -> bool:
        """Check if an error matches the given pattern."""

        # Check error code if available
        if pattern.error_code is not None:
            error_code = getattr(error, "code", None) or getattr(error, "errno", None)
            if error_code is not None:
                if str(error_code) == str(pattern.error_code):
                    return True

        # Check regex pattern
        if pattern.pattern is not None:
            if pattern.pattern.search(error_message):
                return True

        # Check message keywords
        if pattern.message_keywords:
            message_lower = error_message.lower()
            for keyword in pattern.message_keywords:
                if keyword.lower() in message_lower:
                    return True

        return False

    def is_retryable(
        self, dialect: SQLDialect, driver_name: str, error: Exception, error_message: Optional[str] = None
    ) -> bool:
        """
        Determine if an error is retryable.

        Args:
            dialect: SQL dialect
            driver_name: Name of the database driver
            error: Exception object
            error_message: Optional error message

        Returns:
            True if error is retryable, False otherwise
        """
        pattern = self.classify_error(dialect, driver_name, error, error_message)
        if pattern:
            return pattern.retry_policy in [
                RetryPolicy.RETRYABLE,
                RetryPolicy.RETRYABLE_IMMEDIATE,
                RetryPolicy.RETRYABLE_WITH_DELAY,
            ]

        # Default to non-retryable for unclassified errors
        return False

    def is_transient(
        self, dialect: SQLDialect, driver_name: str, error: Exception, error_message: Optional[str] = None
    ) -> bool:
        """
        Check if an error is transient (temporary and retriable).

        This is an alias for is_retryable() - transient errors are those
        that are temporary and can be retried.

        Args:
            dialect: SQL dialect
            driver_name: Name of the database driver
            error: Exception object
            error_message: Optional error message

        Returns:
            True if error is transient, False otherwise
        """
        return self.is_retryable(dialect, driver_name, error, error_message)

    def get_retry_delay(
        self, dialect: SQLDialect, driver_name: str, error: Exception, error_message: Optional[str] = None
    ) -> Optional[float]:
        """
        Get the recommended retry delay for an error.

        Args:
            dialect: SQL dialect
            driver_name: Name of the database driver
            error: Exception object
            error_message: Optional error message

        Returns:
            Retry delay in seconds, or None if not retryable
        """
        pattern = self.classify_error(dialect, driver_name, error, error_message)
        if pattern and self.is_retryable(dialect, driver_name, error, error_message):
            return pattern.retry_delay_seconds
        return None

    def get_max_retries(
        self, dialect: SQLDialect, driver_name: str, error: Exception, error_message: Optional[str] = None
    ) -> Optional[int]:
        """
        Get the maximum number of retries for an error.

        Args:
            dialect: SQL dialect
            driver_name: Name of the database driver
            error: Exception object
            error_message: Optional error message

        Returns:
            Maximum number of retries, or None if unlimited
        """
        pattern = self.classify_error(dialect, driver_name, error, error_message)
        if pattern:
            return pattern.max_retries
        return None

    def get_suggested_action(
        self, dialect: SQLDialect, driver_name: str, error: Exception, error_message: Optional[str] = None
    ) -> str:
        """
        Get the suggested action for handling an error.

        Args:
            dialect: SQL dialect
            driver_name: Name of the database driver
            error: Exception object
            error_message: Optional error message

        Returns:
            Suggested action string
        """
        pattern = self.classify_error(dialect, driver_name, error, error_message)
        if pattern:
            return pattern.suggested_action
        return "Review error details and check database documentation"

    def get_supported_dialects(self) -> List[SQLDialect]:
        """Get list of supported SQL dialects."""
        return list(self._registries.keys())

    def get_supported_drivers(self, dialect: SQLDialect) -> List[str]:
        """Get list of supported drivers for a dialect."""
        registry = self._registries.get(dialect.resolved_alias)
        if registry:
            return list(registry.driver_patterns.keys())
        return []

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered error patterns."""
        stats = {
            "total_dialects": len(self._registries),
            "total_drivers": 0,
            "patterns_by_category": defaultdict(int),
            "patterns_by_retry_policy": defaultdict(int),
            "total_patterns": 0,
        }

        for registry in self._registries.values():
            stats["total_drivers"] += len(registry.driver_patterns)

            # Count common patterns
            for pattern in registry.common_patterns:
                stats["patterns_by_category"][pattern.category.code] += 1
                stats["patterns_by_retry_policy"][pattern.retry_policy.code] += 1
                stats["total_patterns"] += 1

            # Count driver-specific patterns
            for driver_patterns in registry.driver_patterns.values():
                for pattern in driver_patterns:
                    stats["patterns_by_category"][pattern.category.code] += 1
                    stats["patterns_by_retry_policy"][pattern.retry_policy.code] += 1
                    stats["total_patterns"] += 1

        return dict(stats)


# Global registry instance
_error_registry = None


def get_error_registry() -> SQLErrorRegistry:
    """Get the global error registry instance."""
    global _error_registry
    if _error_registry is None:
        _error_registry = SQLErrorRegistry()
        logger.info("Initialized SQL Error Registry", emoji="🎯")
    return _error_registry


def classify_sql_error(
    dialect: SQLDialect, driver_name: str, error: Exception, error_message: Optional[str] = None
) -> Optional[ErrorPattern]:
    """
    Convenience function to classify a SQL error.

    Args:
        dialect: SQL dialect
        driver_name: Name of the database driver
        error: Exception object
        error_message: Optional error message

    Returns:
        ErrorPattern if match found, None otherwise
    """
    registry = get_error_registry()
    return registry.classify_error(dialect, driver_name, error, error_message)


def is_sql_error_retryable(
    dialect: SQLDialect, driver_name: str, error: Exception, error_message: Optional[str] = None
) -> bool:
    """
    Convenience function to check if a SQL error is retryable.

    Args:
        dialect: SQL dialect
        driver_name: Name of the database driver
        error: Exception object
        error_message: Optional error message

    Returns:
        True if error is retryable, False otherwise
    """
    registry = get_error_registry()
    return registry.is_retryable(dialect, driver_name, error, error_message)
