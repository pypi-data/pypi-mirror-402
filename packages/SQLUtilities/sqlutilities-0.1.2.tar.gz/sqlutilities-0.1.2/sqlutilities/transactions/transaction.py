"""
Robust Transaction Management

This module provides the RobustTransaction class for transaction execution.
- RobustTransaction: Transaction manager with retry logic and error handling

Author: DataScience ToolBox
"""

from __future__ import annotations  # Enable string annotations for forward references

import csv
import io
import random
import time
from contextlib import contextmanager
from threading import Lock
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import sqlglot

# Use try/except to handle both absolute and relative imports
try:
    from core.enums import DatabaseObjectType, SQLDialect
    from core.types import COLUMNDTYPE
    from errors.registry import ErrorCategory, RetryPolicy, SQLErrorRegistry
    from transactions.config import TransactionConfig, TransactionException, TransactionMetrics, TransactionState
    from validation.identifiers import SQL_DIALECT_REGISTRY
except ImportError:
    from ..core.enums import DatabaseObjectType, SQLDialect
    from ..core.types import COLUMNDTYPE
    from ..errors.registry import ErrorCategory, RetryPolicy, SQLErrorRegistry
    from ..validation.identifiers import SQL_DIALECT_REGISTRY
    from .config import TransactionConfig, TransactionException, TransactionMetrics, TransactionState

# Avoid circular import with DatabaseConnection
if TYPE_CHECKING:
    try:
        from connections.database_connection import DatabaseConnection
    except ImportError:
        from ..connections.database_connection import DatabaseConnection

from CoreUtilities import LogLevel, get_logger

# Configure logging
logger = get_logger("robust_transaction", level=LogLevel.INFO, include_performance=True, include_emoji=True)


# Constants for test queries
_TEST_QUERIES = {
    SQLDialect.POSTGRESQL: "SELECT 1",
    SQLDialect.MYSQL: "SELECT 1",
    SQLDialect.SQLITE: "SELECT 1",
    SQLDialect.SQLSERVER: "SELECT 1",
    SQLDialect.ORACLE: "SELECT 1 FROM DUAL",
    SQLDialect.BIGQUERY: "SELECT 1",
    SQLDialect.REDSHIFT: "SELECT 1",
}

# Constants for transaction commands
_TRANSACTION_COMMANDS = {
    "begin": {
        SQLDialect.MYSQL: "START TRANSACTION",
        SQLDialect.SQLITE: "BEGIN TRANSACTION",
        SQLDialect.SQLSERVER: "BEGIN TRANSACTION",
        # Default for PostgreSQL, Redshift, etc.
        "default": "BEGIN",
    }
}


class RobustTransaction:
    """
    High-performance, dialect-agnostic transaction manager with intelligent retry logic.

    Responsibilities:
    - ALL query execution and cursor management
    - Transaction management (begin, commit, rollback)
    - Error classification and retry logic
    - Bulk operations and optimizations
    - Performance monitoring
    """

    def __init__(
        self,
        connection: DatabaseConnection,
        config: Optional[TransactionConfig] = None,
        error_registry: Optional[SQLErrorRegistry] = None,
        **kwargs,
    ):
        """Initialize robust transaction manager."""

        # Create config from kwargs if not provided directly
        if config is None and kwargs:
            self.config = TransactionConfig(**kwargs)
        else:
            self.config = config or TransactionConfig()

        self.error_registry = error_registry or SQLErrorRegistry()
        self.connection = connection

        # Transaction state
        self.state = TransactionState.IDLE
        self.metrics = TransactionMetrics(start_time=time.time())
        self._transaction_lock = Lock()
        self._savepoints: List[str] = []

        # Cache for formatted column strings to avoid repeated validation
        self._formatted_columns_cache: Dict[tuple, str] = {}

    @property
    def dialect(self) -> SQLDialect:
        """Get the SQL dialect."""
        return self.connection.dialect

    @property
    def is_active(self) -> bool:
        """Check if transaction is currently active."""
        return self.state == TransactionState.ACTIVE

    def _get_transaction_command(self, command_type: str) -> Optional[str]:
        """Get the appropriate transaction command for the current dialect."""
        if command_type == "begin":
            if self.dialect in [SQLDialect.BIGQUERY, SQLDialect.ORACLE]:
                # These dialects don't use explicit transaction commands
                return None

            return _TRANSACTION_COMMANDS["begin"].get(self.dialect, _TRANSACTION_COMMANDS["begin"]["default"])

        elif command_type in ["commit", "rollback"]:
            if self.dialect == SQLDialect.BIGQUERY:
                return None
            return command_type.upper()

        return None

    def _get_placeholder_string(self, num_columns: int) -> str:
        """Get the appropriate placeholder string for the current dialect."""
        if self.dialect == SQLDialect.ORACLE:
            return ", ".join([f":{i+1}" for i in range(num_columns)])
        elif self.dialect in [SQLDialect.SQLSERVER, SQLDialect.SQLITE]:
            return ", ".join(["?"] * num_columns)
        else:  # PostgreSQL, MySQL, Redshift, etc.
            return ", ".join(["%s"] * num_columns)

    def _format_columns_string(self, columns: List[str]) -> str:
        """Format column names for SQL queries using the validate_identifier function with caching."""
        # Use tuple as cache key since it's hashable
        cache_key = tuple(columns)

        # Return cached result if available
        if cache_key in self._formatted_columns_cache:
            return self._formatted_columns_cache[cache_key]

        # Compute formatted columns
        formatted_columns = []
        for col in columns:
            # Use validate_identifier with 'encapsulate' method to get proper quoting
            validation_result = SQL_DIALECT_REGISTRY.validate_identifier(
                dialect=self.dialect, identifier=col, context=DatabaseObjectType.COLUMN, correction_method="encapsulate"
            )
            formatted_columns.append(validation_result["final"])

        # Cache and return result
        result = ", ".join(formatted_columns)
        self._formatted_columns_cache[cache_key] = result
        return result

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        base_delay = self.config.base_retry_delay * (2**attempt)
        capped_delay = min(base_delay, self.config.max_retry_delay)
        jitter = random.uniform(0, self.config.jitter_factor * capped_delay)
        return capped_delay + jitter

    def _classify_error(self, error: Exception) -> Tuple[ErrorCategory, RetryPolicy]:
        """Classify error and determine retry strategy."""
        error_pattern = self.error_registry.classify_error(
            self.connection.dialect,
            self.connection.current_driver["name"] if self.connection.current_driver else "unknown",
            error,
        )

        if error_pattern:
            return error_pattern.category, error_pattern.retry_policy
        else:
            return ErrorCategory.UNKNOWN, RetryPolicy.NON_RETRYABLE

    def _should_retry_error(self, error: Exception, attempt: int) -> bool:
        """Determine if an error should trigger a retry."""
        if attempt >= self.config.max_retries:
            return False

        error_category, retry_policy = self._classify_error(error)

        if retry_policy == RetryPolicy.NON_RETRYABLE:
            logger.trace(f"Error classified as non-retryable: {error_category.value}", emoji="🚫")
            return False

        if retry_policy == RetryPolicy.RETRYABLE_IMMEDIATE:
            logger.trace(f"Error classified for immediate retry: {error_category.value}", emoji="🔄")
            return True

        if retry_policy == RetryPolicy.RETRYABLE:
            logger.trace(f"Error classified for exponential backoff: {error_category.value}", emoji="⏰")
            return True

        if (
            retry_policy == RetryPolicy.RETRYABLE_WITH_DELAY
            and error_category == ErrorCategory.CONCURRENCY
            and self.config.enable_deadlock_detection
        ):
            logger.warning(f"Deadlock detected, will retry: {error_category.value}", emoji="🔄")
            return True

        return False

    def _begin_transaction(self) -> None:
        """Begin a new transaction."""
        if self.state != TransactionState.IDLE:
            raise TransactionException(f"Cannot begin transaction in state: {self.state.value}")

        try:
            # Get raw connection to check autocommit status
            raw_conn = self.connection.get_raw_connection()

            # For SQL Server with pyodbc, use implicit transactions (no explicit BEGIN needed)
            if (
                self.dialect == SQLDialect.SQLSERVER
                and self.connection.current_driver
                and self.connection.current_driver["name"] == "pyodbc"
                and raw_conn is not None
                and hasattr(raw_conn, "autocommit")
            ):

                raw_conn.autocommit = False  # type: ignore

                # For SQL Server pyodbc, don't send explicit BEGIN - let pyodbc handle implicit transaction
                logger.debug(f"SQL Server pyodbc: Using implicit transaction (no explicit BEGIN)", emoji="�")

            else:
                logger.debug(f"Not SQL Server pyodbc, using explicit transaction commands", emoji="🔍")

                # For other dialects, use explicit transaction commands
                command = self._get_transaction_command("begin")
                logger.debug(f"Transaction begin command: {command}", emoji="📝")
                if command:
                    self._execute_raw(command)

            self.state = TransactionState.ACTIVE
            self.metrics.driver_used = (
                self.connection.current_driver["name"] if self.connection.current_driver else None
            )
            logger.debug(f"Transaction started for {self.dialect.description}", emoji="▶️")

        except Exception as e:
            self.state = TransactionState.FAILED
            logger.error(f"Failed to begin transaction: {e}", emoji="❌")
            raise TransactionException(f"Failed to begin transaction: {e}", e)

    def _commit_transaction(self) -> None:
        """Commit the current transaction."""
        if self.state != TransactionState.ACTIVE:
            raise TransactionException(f"Cannot commit transaction in state: {self.state.value}")

        try:
            # For SQL Server with pyodbc, use direct connection.commit() (like your example)
            if (
                self.dialect == SQLDialect.SQLSERVER
                and self.connection.current_driver
                and self.connection.current_driver["name"] == "pyodbc"
            ):

                raw_conn = self.connection.get_raw_connection()
                if raw_conn is not None and hasattr(raw_conn, "commit"):
                    raw_conn.commit()
                else:
                    raise RuntimeError("No raw connection available for commit")

            else:
                # For other dialects, use explicit COMMIT command
                command = self._get_transaction_command("commit")
                if command:
                    self._execute_raw(command)

            self.state = TransactionState.COMMITTED
            self._savepoints.clear()

            logger.trace(f"Transaction committed for {self.dialect.description}", emoji="✅")

        except Exception as e:
            self.state = TransactionState.FAILED
            logger.error(f"Failed to commit transaction: {e}", emoji="❌")
            # Try to rollback on commit failure
            try:
                self._rollback_transaction()
            except Exception as rollback_error:
                logger.error(f"Failed to rollback after commit failure: {rollback_error}", emoji="💥")
            raise TransactionException(f"Failed to commit transaction: {e}", e)

    def _rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        if self.state not in [TransactionState.ACTIVE, TransactionState.FAILED]:
            logger.warning(f"Cannot rollback transaction in state: {self.state.value}", emoji="⚠️")
            return

        try:
            # For SQL Server with pyodbc, use direct connection.rollback()
            if (
                self.dialect == SQLDialect.SQLSERVER
                and self.connection.current_driver
                and self.connection.current_driver["name"] == "pyodbc"
            ):

                raw_conn = self.connection.get_raw_connection()
                if raw_conn is not None and hasattr(raw_conn, "rollback"):
                    raw_conn.rollback()

            else:
                # For other dialects, use explicit ROLLBACK command
                command = self._get_transaction_command("rollback")
                if command:
                    self._execute_raw(command)

            self.state = TransactionState.ROLLED_BACK
            self._savepoints.clear()

            logger.trace(f"Transaction rolled back for {self.dialect.description}", emoji="↩️")

        except Exception as e:
            logger.error(f"Failed to rollback transaction: {e}", emoji="❌")

    def _execute_raw(
        self, query: str, parameters: Optional[Union[Tuple, Dict[str, Any]]] = None, include_metadata: bool = False
    ) -> Any:
        """Execute a query with proper cursor management."""

        raw_conn = self.connection.get_raw_connection()

        if isinstance(raw_conn, dict):
            conn_type = raw_conn.get("type")

            if conn_type == "pandas_gbq":
                # Handle pandas-gbq special case
                try:
                    import pandas_gbq  # type: ignore

                    return pandas_gbq.read_gbq(query, project_id=raw_conn["project_id"], **raw_conn.get("options", {}))
                except ImportError:
                    raise RuntimeError("pandas_gbq not available")

            elif conn_type == "sqlalchemy":
                # Handle SQLAlchemy connections using session pattern
                try:
                    from sqlalchemy import text
                    from sqlalchemy.orm import sessionmaker

                    engine = raw_conn["engine"]
                    Session = sessionmaker(bind=engine)
                    session = Session()

                    try:
                        if parameters:
                            result = session.execute(text(query), parameters)
                        else:
                            result = session.execute(text(query))

                        # Handle different query types
                        if query.strip().upper().startswith("SELECT"):
                            rows = result.fetchall()
                            if include_metadata:
                                # Create description from SQLAlchemy result metadata
                                description = []
                                if hasattr(result, "keys"):
                                    for key in result.keys():
                                        description.append((str(key), "unknown", None, None, None, None, None))
                                return (rows, description)
                            else:
                                return rows
                        else:
                            # For non-SELECT queries, commit and return rowcount
                            session.commit()
                            # SQLAlchemy 2.0+ uses result.rowcount
                            rowcount = getattr(result, "rowcount", 0)
                            return rowcount

                    except Exception as e:
                        session.rollback()
                        raise
                    finally:
                        session.close()

                except ImportError:
                    raise RuntimeError("SQLAlchemy not available")
                except Exception as e:
                    logger.error(f"SQLAlchemy query execution failed: {e}", emoji="💥")
                    raise

            else:
                raise RuntimeError(f"Unknown connection type: {conn_type}")

        else:
            # Check if this is a BigQuery client
            if (
                self.connection.current_driver
                and self.connection.current_driver["name"] in ["google-cloud-bigquery"]
                and raw_conn is not None
            ):
                # Handle BigQuery client
                try:
                    from google.cloud import bigquery
                    from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter

                    job_config = None

                    # Handle parameters for BigQuery (uses @param_name syntax with dict params)
                    if parameters and isinstance(parameters, dict):
                        query_params = []
                        for name, value in parameters.items():
                            # Infer BigQuery type from Python type
                            if isinstance(value, bool):
                                bq_type = "BOOL"
                            elif isinstance(value, int):
                                bq_type = "INT64"
                            elif isinstance(value, float):
                                bq_type = "FLOAT64"
                            elif isinstance(value, str):
                                bq_type = "STRING"
                            elif isinstance(value, bytes):
                                bq_type = "BYTES"
                            else:
                                bq_type = "STRING"  # Default to string
                            query_params.append(ScalarQueryParameter(name, bq_type, value))

                        job_config = QueryJobConfig()
                        job_config.query_parameters = query_params

                    query_job = raw_conn.query(query, job_config=job_config)  # type: ignore
                    results = query_job.result()

                    rows = [tuple(row.values()) for row in results]

                    if include_metadata:
                        # Create description-like tuple for BigQuery schema
                        schema = results.schema
                        description = [(field.name, field.field_type, None, None, None, None, None) for field in schema]
                        return (rows, description)
                    else:
                        return rows
                except ImportError:
                    raise RuntimeError("google-cloud-bigquery driver not available")
                except Exception as e:
                    logger.error(f"BigQuery query execution failed: {e}", emoji="💥")
                    raise

            # Standard database cursor approach with proper cleanup
            if raw_conn is None:
                raise RuntimeError("Connection is None")

            cursor = raw_conn.cursor()  # type: ignore
            try:
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)

                # Try to fetch results if it's a SELECT query or SQLite PRAGMA query
                query_upper = query.strip().upper()
                if (
                    query_upper.startswith("SELECT")
                    or query_upper.startswith("PRAGMA")
                    or query_upper.startswith("DESCRIBE")
                    or query_upper.startswith("SHOW")
                ):
                    results = cursor.fetchall()
                    if include_metadata:
                        # Return a tuple containing (data, description) for metadata preservation
                        return (results, cursor.description)
                    else:
                        return results
                else:
                    results = cursor.rowcount
                    return results

            finally:
                # For MySQL, consume any unread results before closing cursor
                try:
                    if hasattr(cursor, "fetchall") and hasattr(cursor, "_connection"):
                        # Check if this is a MySQL connector cursor
                        conn_module = cursor._connection.__class__.__module__
                        if "mysql.connector" in conn_module:
                            # Consume any remaining results
                            while cursor.nextset():
                                pass
                except Exception:
                    # Ignore errors during cleanup
                    pass

                # Always close the cursor to prevent resource leaks
                cursor.close()

    @contextmanager
    def _cursor_context(self):
        """Context manager for cursor operations with automatic cleanup."""
        raw_conn = self.connection.get_raw_connection()

        # Handle SQLAlchemy and other special cases differently
        if isinstance(raw_conn, dict):
            raise RuntimeError("Cursor context not supported for special connection types")

        if raw_conn is None:
            raise RuntimeError("Connection is None")

        cursor = raw_conn.cursor()  # type: ignore
        try:
            yield cursor
        finally:
            cursor.close()

    def execute(
        self, query: str, parameters: Optional[Union[Tuple, Dict[str, Any]]] = None, include_metadata: bool = False
    ) -> Any:
        """
        Execute a single SQL query within the transaction.

        Args:
            query: SQL query to execute
            parameters: Optional parameters for the query
            include_metadata: If True, return tuple of (results, metadata) for SELECT queries

        Returns:
            Query results, or tuple of (results, metadata) if include_metadata=True
        """
        if self.state != TransactionState.ACTIVE:
            raise TransactionException(f"Transaction not active (state: {self.state.value})")

        for attempt in range(self.config.max_retries + 1):
            try:
                start_time = time.time()

                result = self._execute_raw(query, parameters, include_metadata=include_metadata)

                # Update metrics
                execution_time = time.time() - start_time
                self.metrics.queries_executed += 1

                # Handle metrics counting for both metadata and non-metadata results
                if include_metadata and isinstance(result, tuple) and len(result) == 2:
                    # For metadata results, count the data rows
                    data_rows = result[0]
                    self.metrics.rows_affected += len(data_rows) if data_rows else 0
                elif hasattr(result, "__len__"):
                    self.metrics.rows_affected += len(result) if result else 0
                elif isinstance(result, int):
                    self.metrics.rows_affected += result

                log_msg = f"Query executed{'with metadata ' if include_metadata else ''}in {execution_time:.3f}s"
                logger.debug(log_msg, emoji="⚡")
                return result

            except Exception as e:
                self.metrics.error_count += 1

                if self._should_retry_error(e, attempt):
                    retry_delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        f"Query failed (attempt {attempt + 1}), retrying in {retry_delay:.2f}s: {e}", emoji="🔄"
                    )

                    time.sleep(retry_delay)
                    self.metrics.retry_count += 1
                    continue
                else:
                    error_category, _ = self._classify_error(e)
                    logger.error(f"Query failed permanently: {e}", emoji="💥")
                    raise TransactionException(f"Query execution failed: {e}", e, error_category)

        raise TransactionException("Maximum retries exceeded")

    def execute_batch(self, query: str, parameters_list: List[Union[Tuple, Dict[str, Any]]]) -> List[Any]:
        """Execute a batch of queries with the same statement but different parameters."""
        if self.state != TransactionState.ACTIVE:
            raise TransactionException(f"Transaction not active (state: {self.state.value})")

        if not parameters_list:
            return []

        results = []
        batch_size = self.config.batch_size or len(parameters_list)

        try:
            # Process in batches
            for i in range(0, len(parameters_list), batch_size):
                batch = parameters_list[i : i + batch_size]
                batch_results = []

                for params in batch:
                    result = self.execute(query, params)
                    batch_results.append(result)

                results.extend(batch_results)
                logger.debug(f"Processed batch {i // batch_size + 1}, {len(batch)} queries", emoji="📦")

            logger.debug(f"Batch execution completed: {len(parameters_list)} queries", emoji="✅")
            return results

        except Exception as e:
            raise TransactionException(f"Batch execution failed: {e}", e)

    def bulk_insert(
        self,
        sql: str,
        data: List[Union[Tuple, List, Dict[str, Any]]],
        chunk_size: Optional[int] = None,
        on_conflict: Optional[str] = None,
    ) -> int:
        """Perform optimized bulk insert using each driver's most efficient method."""
        if self.state != TransactionState.ACTIVE:
            raise TransactionException(f"Transaction not active (state: {self.state.value})")

        if not data:
            return 0

        try:
            # PostgreSQL has true bulk optimizations (COPY, execute_values)
            driver_name = self.connection.current_driver["name"] if self.connection.current_driver else "unknown"
            if self.dialect == SQLDialect.POSTGRES and driver_name in ["psycopg2", "psycopg3"]:
                chunk_size = chunk_size or self._get_optimal_chunk_size()
                columns, table = self._parse_insert_columns_and_table(sql)
                # Normalize data only if needed
                normalized_data = self._normalize_bulk_data_optimized(data, columns)

                logger.trace(f"Starting PostgreSQL bulk insert: {len(normalized_data)} rows into {table}", emoji="📦")

                # Try COPY first for maximum performance
                try:
                    csv_buffer = io.StringIO()
                    csv.writer(csv_buffer).writerows(normalized_data)
                    csv_buffer.seek(0)

                    with self._cursor_context() as cursor:
                        columns_str = self._format_columns_string(columns)
                        copy_sql = f"COPY {table} ({columns_str}) FROM STDIN WITH CSV"
                        cursor.copy_expert(copy_sql, csv_buffer)
                        total_inserted = len(normalized_data)

                except Exception as copy_error:
                    logger.warning(f"COPY failed, falling back to execute_many: {copy_error}", emoji="⚠️")
                    # Fallback to standard execute_many method
                    total_inserted = self.execute_many(sql, normalized_data, chunk_size)  # type: ignore
            else:
                # For all other dialects, bulk insert is just execute_many with an INSERT statement
                logger.trace(f"Delegating to execute_many for bulk insert: {len(data)} rows", emoji="🔄")
                # Delegate to execute_many - exact same path as batch method
                total_inserted = self.execute_many(sql, data, chunk_size)  # type: ignore

            logger.trace(f"Bulk insert completed: {total_inserted} rows inserted", emoji="✅")
            return total_inserted

        except Exception as e:
            logger.error(f"Bulk insert failed: {e}", emoji="❌")
            raise TransactionException(f"Bulk insert failed: {e}", e)

    def execute_many(
        self, query: str, parameters_list: List[Union[Tuple, Dict[str, Any]]], chunk_size: Optional[int] = None
    ) -> int:
        """Execute a query multiple times with different parameters using driver-optimized methods."""
        if self.state != TransactionState.ACTIVE:
            raise TransactionException(f"Transaction not active (state: {self.state.value})")

        if not parameters_list:
            return 0

        chunk_size = chunk_size or self._get_optimal_chunk_size()

        try:
            driver_name = self.connection.current_driver["name"] if self.connection.current_driver else "unknown"
            total_affected: int = 0

            # PostgreSQL with psycopg2/3 optimization
            if self.dialect == SQLDialect.POSTGRES and driver_name in ["psycopg2", "psycopg3"]:
                execute_batch = None
                try:
                    from psycopg2.extras import execute_batch
                except ImportError:
                    try:
                        from psycopg.extras import execute_batch  # type: ignore
                    except ImportError:
                        pass  # execute_batch remains None

                if execute_batch is not None:
                    with self._cursor_context() as cursor:
                        for i in range(0, len(parameters_list), chunk_size):
                            chunk = parameters_list[i : i + chunk_size]
                            execute_batch(cursor, query, chunk, page_size=len(chunk))
                            total_affected += cursor.rowcount if cursor.rowcount > 0 else len(chunk)

            if total_affected == 0:
                # Use generic chunked executemany for all other cases
                with self._cursor_context() as cursor:
                    for i in range(0, len(parameters_list), chunk_size):
                        chunk = parameters_list[i : i + chunk_size]
                        cursor.executemany(query, chunk)
                        total_affected += cursor.rowcount if cursor.rowcount > 0 else len(chunk)

            self.metrics.queries_executed += len(parameters_list)
            self.metrics.rows_affected += total_affected
            return total_affected

        except Exception as e:
            logger.error(f"Execute_many failed: {e}", emoji="❌")
            raise TransactionException(f"Execute_many failed: {e}", e)

    def _get_optimal_chunk_size(self) -> int:
        """Get the optimal chunk size for the current driver."""
        if self.connection.current_driver:
            driver_name = self.connection.current_driver["name"]

            # Find the driver config in the registry
            from ..drivers.registry import DatabaseDriver

            for driver_enum in DatabaseDriver:
                driver_config = driver_enum.value
                if driver_config.name == driver_name:
                    return driver_config.optimal_chunk_size

        # Fallback to default if driver not found
        return 1000

    @classmethod
    def _parse_insert_columns_and_table(cls, sql: str) -> Tuple[List[str], str]:
        """Parse the column names from an INSERT SQL statement."""
        # Replace parameter placeholders with dummy values before parsing
        # sqlglot interprets %s as modulo operator, so we need to replace them
        # Common placeholders: %s (psycopg2/pymysql), ? (sqlite/pyodbc), :name (cx_Oracle)
        import re
        # Replace %s placeholders with NULL for parsing
        sanitized_sql = re.sub(r'%s', 'NULL', sql)
        # Replace ? placeholders with NULL for parsing
        sanitized_sql = re.sub(r'\?', 'NULL', sanitized_sql)
        # Replace :name placeholders with NULL for parsing
        sanitized_sql = re.sub(r':\w+', 'NULL', sanitized_sql)

        # Parse the sanitized SQL into an expression tree
        parsed = sqlglot.parse_one(sanitized_sql)

        # Extract the column names
        # For an INSERT, parsed.this is the Schema, which contains:
        # - this: the Table object
        # - expressions: the column Identifiers
        if isinstance(parsed, sqlglot.exp.Insert):  # type: ignore
            schema = parsed.this
            columns = [col.name for col in schema.expressions]
            table_name = schema.this.sql()
            return columns, table_name
        else:
            raise ValueError("SQL must be an INSERT statement to extract columns")

    def _normalize_bulk_data_optimized(
        self, data: List[Union[Tuple, List, Dict[str, Any]]], columns: List[str]
    ) -> List[Tuple]:
        """Optimize bulk data normalization by checking data format first."""
        if not data:
            return []

        # Fast path: Check if all data is already tuples (most common case)
        first_row = data[0]
        if isinstance(first_row, tuple):
            # Quick check if all rows are tuples - much faster than normalizing
            all_tuples = all(isinstance(row, tuple) for row in data[: min(10, len(data))])
            if all_tuples:
                logger.trace(f"Data already in tuple format, skipping normalization for {len(data)} rows", emoji="⚡")
                return data  # type: ignore

        # Fallback to full normalization if needed
        logger.trace(f"Normalizing {len(data)} rows of mixed format data", emoji="🔄")
        normalized = []

        for row in data:
            if isinstance(row, dict):
                # Convert dict to tuple in column order
                tuple_row = tuple(row.get(col) for col in columns)
                normalized.append(tuple_row)
            elif isinstance(row, (list, tuple)):
                # Convert to tuple
                normalized.append(tuple(row))
            else:
                raise ValueError(f"Unsupported data format: {type(row)}")

        return normalized

    def commit(self) -> None:
        """
        Commit the current transaction.

        This is a public wrapper around _commit_transaction().
        """
        self._commit_transaction()

    def rollback(self) -> None:
        """
        Rollback the current transaction.

        This is a public wrapper around _rollback_transaction().
        """
        self._rollback_transaction()

    def get_metrics(self) -> TransactionMetrics:
        """Get transaction performance metrics."""
        if self.metrics.end_time is None and self.state in [TransactionState.COMMITTED, TransactionState.ROLLED_BACK]:
            self.metrics.end_time = time.time()
            self.metrics.duration = self.metrics.end_time - self.metrics.start_time

        return self.metrics

    def __enter__(self):
        """Context manager entry."""
        with self._transaction_lock:
            try:
                # Ensure connection is established
                if not self.connection.is_connected:
                    if not self.connection.connect():
                        raise TransactionException("Failed to establish database connection")

                self._begin_transaction()
                return self

            except Exception as e:
                self.state = TransactionState.FAILED
                logger.error(f"Failed to enter transaction context: {e}", emoji="❌")
                raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        with self._transaction_lock:
            commit_successful = False
            try:
                if exc_type is None:
                    # No exception occurred, commit transaction
                    if self.state == TransactionState.ACTIVE:
                        self._commit_transaction()
                        commit_successful = True
                    else:
                        logger.warning(
                            f"Transaction not ACTIVE (state: {self.state.value}), skipping commit", emoji="⚠️"
                        )
                else:
                    # Exception occurred, rollback transaction
                    if self.state == TransactionState.ACTIVE:
                        self._rollback_transaction()
                        logger.warning(f"Transaction rolled back due to exception: {exc_val}", emoji="↩️")

                # Update final metrics
                self.metrics.end_time = time.time()
                self.metrics.duration = self.metrics.end_time - self.metrics.start_time

                if self.config.enable_performance_monitoring:
                    logger.debug(
                        f"Transaction completed - Duration: {self.metrics.duration:.3f}s, "
                        f"Queries: {self.metrics.queries_executed}, "
                        f"Retries: {self.metrics.retry_count}, "
                        f"Errors: {self.metrics.error_count}",
                        emoji="📊",
                    )

            except Exception as cleanup_error:
                logger.error(f"Error during transaction cleanup: {cleanup_error}", emoji="❌")
                # If commit failed, ensure we don't suppress the original exception
                if not commit_successful and exc_type is None:
                    # Commit failed but there was no original exception - re-raise the commit error
                    raise cleanup_error

            logger.debug(f"Exited transaction context for {self.dialect.description}", emoji="🚪")

    def __repr__(self) -> str:
        """String representation of the transaction."""
        return (
            f"RobustTransaction(dialect={self.dialect.name_value}, "
            f"state={self.state.value}, "
            f"retries={self.config.max_retries})"
        )
