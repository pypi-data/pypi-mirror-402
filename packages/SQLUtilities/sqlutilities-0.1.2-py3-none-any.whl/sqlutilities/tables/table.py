"""
SQL Table Management

This module provides the SQL_TABLE class for comprehensive table operations.
- SQL_TABLE: Main class for table creation, modification, and management

Author: DataScience ToolBox
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

# Use try/except to handle both absolute and relative imports
try:
    from connections.database_connection import DatabaseConnection
    from core.enums import DatabaseObjectType, SQLDialect
    from core.types import COLUMNDTYPE
    from errors.registry import SQLErrorRegistry
    from tables.definitions import (
        ColumnDefinition,
        ConstraintDefinition,
        IndexDefinition,
        TableComponentType,
        TableDefinition,
    )
    from validation.identifiers import SQL_DIALECT_REGISTRY
except ImportError:
    from .definitions import (
        ColumnDefinition,
        ConstraintDefinition,
        IndexDefinition,
        TableDefinition,
        TableComponentType,
    )
    from ..connections.database_connection import DatabaseConnection
    from ..core.enums import SQLDialect, DatabaseObjectType
    from ..core.types import COLUMNDTYPE
    from ..validation.identifiers import SQL_DIALECT_REGISTRY
    from ..errors.registry import SQLErrorRegistry

from CoreUtilities import LogLevel, get_logger

# Configure logging
logger = get_logger("sql_table", level=LogLevel.INFO, include_performance=True, include_emoji=True)


class SQL_TABLE:
    """
    Comprehensive SQL table management class that supports operations on tables
    and their components (columns, constraints, indexes) across multiple SQL dialects.

    Features:
    - Create, drop, and recreate tables
    - Manage individual table components (columns, constraints, indexes)
    - Cross-dialect SQL generation
    - Robust transaction support via DatabaseConnection (automatic retry and rollback)
    - Existence checking and validation
    - Schema introspection and documentation

    The class uses the robust DatabaseConnection which automatically wraps all
    operations in reliable transactions with retry logic and proper error handling.

    Example:
        # Initialize with robust connection
        conn = DatabaseConnection(SQLDialect.POSTGRESQL, ...)
        table = SQL_TABLE(conn, "users", schema="public")

        # Define table structure
        table.add_column("id", COLUMNDTYPE.INTEGER, is_identity=True)
        table.add_column("email", COLUMNDTYPE.VARCHAR, length=255, nullable=False)
        table.add_primary_key_constraint("pk_users", ["id"])
        table.add_unique_constraint("uk_email", ["email"])

        # Create the table (automatically wrapped in robust transaction)
        table.create_table()

        # Manage components
        table.add_index("idx_email", ["email"])
        table.drop_constraint("uk_email")
        table.recreate_table()
    """

    def __init__(
        self,
        connection: DatabaseConnection,
        table_name: str,
        schema: Optional[str] = None,
        database: Optional[str] = None,
        correction_method: Literal["encapsulate", "normalize"] = "encapsulate",
    ):
        """
        Initialize SQL_TABLE instance.

        Args:
            connection: DatabaseConnection instance
            table_name: Name of the table
            schema: Schema name (optional)
            auto_quote_identifiers: Whether to automatically quote identifiers
        """
        self.connection = connection
        self.original_table_name = table_name
        self.original_database = database

        # Set dialect first since it's needed for validation
        self.dialect = connection.dialect

        self.database = (
            SQL_DIALECT_REGISTRY.validate_identifier(
                dialect=self.dialect,
                identifier=database,
                context=DatabaseObjectType.DATABASE,
                correction_method=correction_method,
            )["final"]
            if database
            else None
        )
        self.table_name = SQL_DIALECT_REGISTRY.validate_identifier(
            dialect=self.dialect,
            identifier=table_name,
            context=DatabaseObjectType.TABLE,
            correction_method=correction_method,
        )["final"]
        self.original_schema = schema
        self.schema = (
            SQL_DIALECT_REGISTRY.validate_identifier(
                dialect=self.dialect,
                identifier=schema,
                context=DatabaseObjectType.SCHEMA,
                correction_method=correction_method,
            )["final"]
            if schema
            else None
        )
        self.correction_method = correction_method
        self.definition = TableDefinition(name=table_name, schema=schema)
        self.error_registry = SQLErrorRegistry()

        logger.debug(f"Initialized SQL_TABLE for {self.full_table_name} on {self.dialect.value}", emoji="🏗️")

    @property
    def full_table_name(self) -> str:
        """Get the fully qualified table name."""
        # For BigQuery, we need project.dataset.table format
        if self.dialect == SQLDialect.BIGQUERY:
            # Check both project_id and project parameter names
            project_id = self.connection._connection_params.get("project_id") or self.connection._connection_params.get(
                "project"
            )
            dataset_id = self.connection._connection_params.get("dataset_id") or self.connection._connection_params.get(
                "dataset"
            )
            if self.schema:
                # Remove existing backticks to avoid double-quoting
                clean_schema = self.schema.strip("`")
                clean_table = self.table_name.strip("`")
                return f"`{project_id}.{clean_schema}.{clean_table}`"
            elif dataset_id:
                # Use dataset_id from connection params
                clean_table = self.table_name.strip("`")
                return f"`{project_id}.{dataset_id}.{clean_table}`"
            else:
                # Default to 'default' dataset if no schema provided
                clean_table = self.table_name.strip("`")
                return f"`{project_id}.default.{clean_table}`"

        # For other databases, use standard schema.table format
        if self.schema:
            return f"{self.schema}.{self.table_name}"

        return f"{self.table_name}"

    @property
    def supports_if_exists(self) -> bool:
        """Check if the dialect supports IF EXISTS clause."""
        return self.dialect.supports_if_exists(DatabaseObjectType.TABLE)

    # ========== TABLE EXISTENCE AND INTROSPECTION ==========

    def exists(self, **kwargs) -> bool:
        """
        Check if the table exists in the database.

        Args:
            **kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection

        Returns:
            True if table exists, False otherwise
        """

        query = self._generate_existence_query()

        try:
            result = self.connection.execute_query(query, **kwargs)
            exists = bool(result and len(result) > 0 and result[0][0] > 0)
            logger.debug(f"Table {self.full_table_name} {'exists' if exists else 'does not exist'}", emoji="🔍")
            return exists
        except Exception as e:
            logger.error(f"Failed to check table existence: {e}", emoji="❌")
            raise

    def _generate_existence_query(self) -> str:
        """Generate dialect-specific table existence query."""
        if self.dialect == SQLDialect.ORACLE:
            # Oracle stores quoted identifiers exactly as written, unquoted identifiers as uppercase
            # Since we use quoted identifiers, we need to check for the exact case
            # The table_name property contains the quoted version, so extract the unquoted version

            if self.table_name.startswith(self.dialect.quote_character) and self.table_name.endswith(
                self.dialect.quote_character
            ):
                # Table is quoted, use exact case from original_table_name
                actual_table_name = self.table_name[1:-1]
            else:
                # Table is unquoted, Oracle stores it uppercase
                actual_table_name = self.table_name.upper()

            if self.schema:
                if self.schema.startswith(self.dialect.quote_character) and self.schema.endswith(
                    self.dialect.quote_character
                ):
                    actual_schema_name = self.schema[1:-1]
                else:
                    actual_schema_name = self.schema.upper() if self.schema else None
            else:
                actual_schema_name = None

            if self.schema:
                query = f"""
                SELECT COUNT(*) 
                FROM all_tables 
                WHERE owner = '{actual_schema_name}' 
                AND table_name = '{actual_table_name}'
                """
            else:
                query = f"""
                SELECT COUNT(*) 
                FROM user_tables 
                WHERE table_name = '{actual_table_name}'
                """
            return query

        elif self.dialect == SQLDialect.POSTGRESQL:
            schema_condition = f"schemaname = '{self.schema}'" if self.schema else "schemaname = 'public'"
            return f"""
            SELECT COUNT(*) 
            FROM pg_tables 
            WHERE {schema_condition} 
            AND tablename = '{self.table_name}'
            """

        elif self.dialect == SQLDialect.MYSQL:
            database_condition = f"table_schema = '{self.schema}'" if self.schema else "table_schema = DATABASE()"
            return f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE {database_condition} 
            AND table_name = '{self.table_name}'
            """

        elif self.dialect == SQLDialect.SQLSERVER:
            schema_condition = f"TABLE_SCHEMA = '{self.schema}'" if self.schema else "TABLE_SCHEMA = 'dbo'"
            return f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE {schema_condition} 
            AND TABLE_NAME = '{self.table_name}'
            """

        elif self.dialect == SQLDialect.SQLITE:
            return f"""
            SELECT COUNT(*) 
            FROM sqlite_master 
            WHERE type='table' AND name='{self.table_name}'
            """

        elif self.dialect == SQLDialect.BIGQUERY:
            # BigQuery table existence check - emulator doesn't support INFORMATION_SCHEMA
            # Use BigQuery client API for reliable table existence checking
            try:
                from google.cloud.exceptions import NotFound

                # Get project_id and dataset_id
                project_id = None
                dataset_id = None
                client = None

                if hasattr(self.connection, "_connection_params"):
                    project_id = self.connection._connection_params.get("project_id")
                    dataset_id = self.connection._connection_params.get("dataset_id")
                    # Also check for alternate parameter names
                    if not project_id:
                        project_id = self.connection._connection_params.get("project")
                    if not dataset_id:
                        dataset_id = self.connection._connection_params.get("dataset")

                if hasattr(self.connection, "_connection") and self.connection._connection:
                    client = self.connection._connection
                    if hasattr(client, "project") and not project_id:
                        project_id = client.project

                # Use original schema as dataset_id if available
                if not dataset_id and self.original_schema:
                    dataset_id = self.original_schema

                if dataset_id and project_id and client:
                    # Use BigQuery client API to check table existence
                    table_ref = client.dataset(dataset_id, project=project_id).table(self.original_table_name)
                    try:
                        client.get_table(table_ref)
                        # If we get here, table exists
                        return "SELECT 1 as table_exists"
                    except NotFound:
                        # Table doesn't exist
                        return "SELECT 0 as table_exists"
                else:
                    # Fallback: assume table doesn't exist
                    return "SELECT 0 as table_exists"

            except Exception:
                # If anything fails, use a simple fallback that assumes table doesn't exist
                return "SELECT 0 as table_exists"

        elif self.dialect == SQLDialect.REDSHIFT:
            schema_condition = f"schemaname = '{self.schema}'" if self.schema else "schemaname = 'public'"
            return f"""
            SELECT COUNT(*) 
            FROM pg_tables 
            WHERE {schema_condition} 
            AND tablename = '{self.table_name}'
            """

        else:
            # Generic ANSI SQL approach
            return f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = '{self.table_name}'
            """

    def get_table_info(self, **kwargs) -> Dict[str, Any]:
        """
        Get comprehensive information about the table.

        Args:
            **kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection

        Returns:
            Dictionary containing table metadata
        """

        if not self.exists(**kwargs):
            logger.warning(f"Table {self.full_table_name} does not exist", emoji="⚠️")
            return {}

        info = {
            "table_name": self.table_name,
            "schema": self.schema,
            "full_name": self.full_table_name,
            "dialect": self.dialect.value,
            "exists": True,
            "columns": self.get_columns(**kwargs),
            "constraints": self.get_constraints(**kwargs),
            "indexes": self.get_indexes(**kwargs),
            "row_count": self.get_row_count(**kwargs),
            "size_info": self.get_size_info(),
        }

        logger.debug(f"Retrieved table info for {self.full_table_name}", emoji="📊")
        return info

    def get_columns(self, **kwargs) -> List[Dict[str, Any]]:
        """Get column information for the table.

        Args:
            **kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection
        """

        query = self._generate_columns_query()

        try:
            result = self.connection.execute_query(query, **kwargs)
            columns = []

            for row in result:
                column_info = self._parse_column_row(row)
                columns.append(column_info)

            logger.debug(f"Retrieved {len(columns)} columns for {self.full_table_name}", emoji="🏛️")
            return columns

        except Exception as e:
            logger.error(f"Failed to get columns: {e}", emoji="❌")
            raise

    def _generate_columns_query(self) -> str:
        """Generate dialect-specific query to get column information."""
        if self.dialect == SQLDialect.ORACLE:
            # Strip quotes from table name for Oracle metadata queries
            # Oracle stores table names in ALL_TAB_COLUMNS without quotes but preserves case
            # from quoted identifiers (e.g., CREATE TABLE "myTable" stores as 'myTable', not 'MYTABLE')
            table_name_raw = self.table_name.strip('"')

            if self.schema:
                schema_raw = self.schema.strip('"')
                # Don't use UPPER() - compare with actual stored case
                where_clause = f"WHERE owner = '{schema_raw}' AND table_name = '{table_name_raw}'"
            else:
                # When schema not specified, use current user's tables
                # Don't use UPPER() - compare with actual stored case
                where_clause = f"WHERE owner = USER AND table_name = '{table_name_raw}'"

            return f"""
            SELECT
                column_name,
                data_type,
                data_length,
                data_precision,
                data_scale,
                nullable,
                data_default,
                column_id
            FROM all_tab_columns
            {where_clause}
            ORDER BY column_id
            """

        elif self.dialect == SQLDialect.POSTGRESQL:
            schema_condition = f"table_schema = '{self.schema}'" if self.schema else "table_schema = 'public'"
            return f"""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns 
            WHERE {schema_condition} 
            AND table_name = '{self.table_name}'
            ORDER BY ordinal_position
            """

        elif self.dialect == SQLDialect.MYSQL:
            database_condition = f"table_schema = '{self.schema}'" if self.schema else "table_schema = DATABASE()"
            return f"""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns 
            WHERE {database_condition} 
            AND table_name = '{self.table_name}'
            ORDER BY ordinal_position
            """

        elif self.dialect == SQLDialect.SQLSERVER:
            schema_condition = f"TABLE_SCHEMA = '{self.schema}'" if self.schema else "TABLE_SCHEMA = 'dbo'"
            return f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                ORDINAL_POSITION
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE {schema_condition} 
            AND TABLE_NAME = '{self.table_name}'
            ORDER BY ORDINAL_POSITION
            """

        elif self.dialect == SQLDialect.SQLITE:
            return f"PRAGMA table_info({self.table_name})"

        elif self.dialect == SQLDialect.BIGQUERY:
            # BigQuery requires fully qualified INFORMATION_SCHEMA with project.dataset
            project_id = self.connection._connection_params.get("project_id") or self.connection._connection_params.get(
                "project"
            )
            dataset_id = self.connection._connection_params.get("dataset_id") or self.connection._connection_params.get(
                "dataset"
            )
            # Extract just the table name without project.dataset prefix
            table_name_only = self.original_table_name
            return f"""
            SELECT
                column_name,
                data_type,
                NULL as character_maximum_length,
                NULL as numeric_precision,
                NULL as numeric_scale,
                is_nullable,
                NULL as column_default,
                ordinal_position
            FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = '{table_name_only}'
            ORDER BY ordinal_position
            """

        else:
            # Generic approach
            return f"""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default,
                ordinal_position
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE table_name = '{self.table_name}'
            ORDER BY ordinal_position
            """

    def _parse_column_row(self, row: Tuple) -> Dict[str, Any]:
        """Parse a column row based on dialect."""
        if self.dialect == SQLDialect.SQLITE:
            # SQLite PRAGMA returns: cid, name, type, notnull, dflt_value, pk
            return {
                "name": row[1],
                "data_type": row[2],
                "nullable": not bool(row[3]),
                "default_value": row[4],
                "is_primary_key": bool(row[5]),
                "position": row[0],
            }
        else:
            # Standard INFORMATION_SCHEMA format
            return {
                "name": row[0],
                "data_type": row[1],
                "max_length": row[2],
                "precision": row[3],
                "scale": row[4],
                "nullable": row[5] == "YES",
                "default_value": row[6],
                "position": row[7],
            }

    def get_constraints(self, **_kwargs) -> List[Dict[str, Any]]:
        """Get constraint information for the table.

        Args:
            **_kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection
        """
        # Implementation would vary by dialect
        logger.debug(f"Getting constraints for {self.full_table_name}", emoji="🔒")
        # Placeholder - would implement dialect-specific constraint queries
        return []

    def get_indexes(self, **_kwargs) -> List[Dict[str, Any]]:
        """Get index information for the table.

        Args:
            **_kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection
        """
        # Implementation would vary by dialect
        logger.debug(f"Getting indexes for {self.full_table_name}", emoji="📇")
        # Placeholder - would implement dialect-specific index queries
        return []

    def get_row_count(self, **kwargs) -> int:
        """Get the number of rows in the table.

        Args:
            **kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection
        """

        try:
            query = f"SELECT COUNT(*) FROM {self.full_table_name}"
            result = self.connection.execute_query(query, **kwargs)
            count = result[0][0] if result else 0
            logger.debug(f"Table {self.full_table_name} has {count:,} rows", emoji="📊")
            return count
        except Exception as e:
            logger.error(f"Failed to get row count: {e}", emoji="❌")
            return -1

    def get_size_info(self, _retries: int = 3) -> Dict[str, Any]:
        """Get size information for the table.

        Args:
            retries: Number of retry attempts for database queries
        """
        # Implementation would vary by dialect
        logger.debug(f"Getting size info for {self.full_table_name}", emoji="📏")
        return {"size_bytes": -1, "size_mb": -1}

    def populate_definition_from_existing(self) -> bool:
        """
        Populate the table definition with column information from an existing table.

        This method retrieves the actual table structure from the database and
        populates the SQL_TABLE definition with ColumnDefinition objects that
        match the existing table schema. This is useful when skipping SQL spec
        generation for append operations while still needing column metadata
        for data preparation.

        Returns:
            bool: True if successful, False if table doesn't exist or operation failed

        Raises:
            RuntimeError: If table doesn't exist or column information cannot be retrieved
        """
        if not self.exists():
            raise RuntimeError(f"Table {self.full_table_name} does not exist")

        try:
            logger.debug("Retrieving existing table column definitions", emoji="🔍")
            existing_columns = self.get_columns()

            if not existing_columns:
                raise RuntimeError(f"No column information found for table {self.full_table_name}")

            # Clear any existing definitions and populate with actual table structure
            self.definition.columns.clear()

            for col_info in existing_columns:
                # Map SQL data type back to COLUMNDTYPE
                data_type_str = col_info.get("data_type", "VARCHAR")
                mapped_type = self._map_string_to_columndtype(data_type_str)
                if mapped_type is None:
                    mapped_type = COLUMNDTYPE.VARCHAR
                    logger.warning(
                        f"Unknown data type '{data_type_str}' for column '{col_info['name']}', defaulting to VARCHAR",
                        emoji="⚠️",
                    )

                # Create column definition from existing table info
                column_def = ColumnDefinition(
                    name=col_info["name"],
                    data_type=mapped_type,
                    dialect=self.dialect,
                    length=col_info.get("max_length"),
                    precision=col_info.get("precision"),
                    scale=col_info.get("scale"),
                    nullable=col_info.get("nullable", True),
                    default_value=col_info.get("default_value"),
                    ordinal_position=col_info.get("ordinal_position"),
                )
                self.definition.columns.append(column_def)

            logger.debug(f"Populated table definition with {len(existing_columns)} existing columns", emoji="✅")
            return True

        except Exception as e:
            logger.error(f"Failed to populate definition from existing table: {e}", emoji="❌")
            raise RuntimeError(f"Failed to populate table definition: {str(e)}")

    # ========== TABLE OPERATIONS ==========

    def create_table(
        self,
        if_exists: Literal["fail", "replace", "append"] = "append",
        dry_run: bool = False,
        defer_constraints: bool = False,
        defer_indexes: bool = False,
        **kwargs,
    ) -> Union[bool, str, Tuple[bool, List[str]]]:
        """
        Create the table based on the current definition.

        Args:
            if_exists: How to behave if the table already exists:
                - 'fail': Raise a ValueError if table exists
                - 'replace': Drop the table before creating (recreate)
                - 'append': Create only if table doesn't exist (IF NOT EXISTS)
            dry_run: If True, return the SQL statements instead of executing them
            defer_constraints: If True, defer non-primary key constraints creation
            defer_indexes: If True, defer index creation
            **kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection

        Returns:
            If dry_run=True: String containing the SQL statements
            If dry_run=False and no deferrals: True if successful
            If dry_run=False and deferrals: Tuple of (success, deferred_sql_list)
        """

        if not self.definition.columns:
            raise ValueError("No columns defined for table creation")

        # Validate if_exists parameter
        valid_if_exists = ["fail", "replace", "append"]
        if if_exists not in valid_if_exists:
            raise ValueError(f"if_exists must be one of {valid_if_exists}, got '{if_exists}'")

        # Check existence for fail mode (only when not dry_run)
        if if_exists == "fail" and not dry_run and self.exists(**kwargs):
            raise ValueError(f"Table {self.full_table_name} already exists and if_exists='fail'")

        # Generate all SQL statements
        sql_statements, deferred_statements = self._generate_all_creation_sql(
            if_exists, defer_constraints, defer_indexes
        )

        if dry_run:
            if deferred_statements:
                all_sql = "\n\n".join(sql_statements + ["-- DEFERRED STATEMENTS:"] + deferred_statements)
            else:
                all_sql = "\n\n".join(sql_statements)
            logger.debug(f"Generated SQL for table {self.full_table_name} (mode: {if_exists})", emoji="📄")
            return all_sql

        # Execute the statements using robust connection (which handles transactions automatically)
        try:
            if if_exists == "replace" and self.exists(**kwargs):
                self.drop_table(if_exists=True, **kwargs)

            logger.debug(f"Creating table {self.full_table_name} (mode: {if_exists})", emoji="🏗️")

            # Execute immediate statements using the robust connection
            for sql in sql_statements:
                # Remove comments and execute clean SQL
                clean_sql = sql.split("\n", 1)[-1].rstrip(";")
                self.connection.execute_query(clean_sql, **kwargs)

            logger.debug(f"Successfully created table {self.full_table_name}", emoji="✅")

            # Return based on whether we have deferred statements
            if deferred_statements:
                logger.debug(f"Deferred {len(deferred_statements)} constraint/index statements", emoji="⏳")
                return True, deferred_statements
            else:
                return True

        except Exception as e:
            logger.error(f"Failed to create table {self.full_table_name}: {e}", emoji="❌")
            raise

    def drop_table(self, if_exists: bool = True, **kwargs) -> bool:
        """
        Drop the table.

        Args:
            if_exists: Whether to check if table exists before dropping
            **kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection

        Returns:
            True if successful, False otherwise
        """

        try:
            # If if_exists is True, check if table exists before attempting to drop
            if if_exists and not self.exists(**kwargs):
                logger.debug(f"Table {self.full_table_name} does not exist, skipping drop", emoji="ℹ️")
                return True

            drop_sql = self._generate_drop_table_sql(if_exists)

            logger.debug(f"Dropping table {self.full_table_name}", emoji="🗑️")
            self.connection.execute_query(drop_sql, **kwargs)

            logger.debug(f"Successfully dropped table {self.full_table_name}", emoji="✅")
            return True

        except Exception as e:
            logger.error(f"Failed to drop table {self.full_table_name}: {e}", emoji="❌")
            raise

    def recreate_table(self, dry_run: bool = False, **kwargs) -> Union[bool, str]:
        """
        Drop and recreate the table.

        Args:
            dry_run: If True, return the SQL statements instead of executing them
            **kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection

        Returns:
            If dry_run=True: String containing the SQL statements
            If dry_run=False: True if successful, False otherwise
        """

        logger.debug(f"Recreating table {self.full_table_name}", emoji="🔄")

        if dry_run:
            # Generate DROP + CREATE statements
            drop_sql = self._generate_drop_table_sql(True)
            create_statements, deferred_statements = self._generate_all_creation_sql(
                "fail"
            )  # Don't use IF NOT EXISTS for recreate

            all_statements = [f"-- Drop existing table\n{drop_sql};"] + create_statements
            if deferred_statements:
                all_statements.extend(["-- DEFERRED STATEMENTS:"] + deferred_statements)
            full_sql = "\n\n".join(all_statements)
            logger.debug(f"Generated recreate SQL for table {self.full_table_name}", emoji="📄")
            return full_sql

        # Execute recreate using robust connection (which handles transactions automatically)
        try:
            if self.exists(**kwargs):
                self.drop_table(if_exists=True, **kwargs)
            self.create_table(if_exists="fail", **kwargs)

            logger.debug(f"Successfully recreated table {self.full_table_name}", emoji="✅")
            return True

        except Exception as e:
            logger.error(f"Failed to recreate table {self.full_table_name}: {e}", emoji="❌")
            raise

    def _validate_identifier(
        self, identifier: str, context: DatabaseObjectType, force_encapsulate: bool = False
    ) -> str:
        """
        Validate and quote an SQL identifier (e.g., table name, column name).

        Args:
            identifier: The identifier to validate
            context: The context in which the identifier is used (e.g., table, column)

        Returns:
            The validated and quoted identifier
        """
        # Use the SQL dialect registry to validate and quote the identifier
        return SQL_DIALECT_REGISTRY.validate_identifier(
            dialect=self.dialect,
            identifier=identifier,
            context=context,
            correction_method="encapsulate" if force_encapsulate else self.correction_method,
        )[
            "final"
        ]  # type: ignore

    def _quote_identifier(self, identifier: str, context: DatabaseObjectType) -> str:
        """
        Quote an SQL identifier based on the dialect.

        Args:
            identifier: The identifier to quote
            context: The context in which the identifier is used (e.g., table, column)

        Returns:
            The quoted identifier
        """
        return self._validate_identifier(identifier=identifier, context=context, force_encapsulate=True)

    # ========== COLUMN OPERATIONS ==========

    def add_column(
        self,
        name: str,
        data_type: Union[COLUMNDTYPE, str],
        length: Optional[int] = None,
        precision: Optional[int] = None,
        scale: Optional[int] = None,
        nullable: bool = True,
        default_value: Optional[str] = None,
        default_expression: Optional[str] = None,
        is_identity: bool = False,
        identity_seed: Optional[int] = None,
        identity_increment: Optional[int] = None,
        character_set: Optional[str] = None,
        collation: Optional[str] = None,
        check_constraint: Optional[str] = None,
        check_constraint_name: Optional[str] = None,
        is_computed: bool = False,
        computed_expression: Optional[str] = None,
        is_stored: bool = False,
        comment: Optional[str] = None,
        description: Optional[str] = None,
        after_column: Optional[str] = None,
        **extra_attributes,
    ) -> None:
        """
        Add a column definition to the table.

        Args:
            name: Column name
            data_type: Data type (COLUMNDTYPE enum or string)
            length: Length for VARCHAR, CHAR, etc.
            precision: Precision for DECIMAL, NUMERIC, etc.
            scale: Scale for DECIMAL, NUMERIC, etc.
            nullable: Whether column allows NULL values
            default_value: Static default value
            default_expression: Dynamic default expression (e.g., CURRENT_TIMESTAMP)
            is_identity: Whether column is an identity/auto-increment column
            identity_seed: Starting value for identity column
            identity_increment: Increment value for identity column
            character_set: Character set for string columns
            collation: Collation for string columns
            check_constraint: Check constraint expression for this column
            check_constraint_name: Name for the check constraint
            is_computed: Whether this is a computed/generated column
            computed_expression: Expression for computed column
            is_stored: Whether computed column is stored (vs virtual)
            comment: Short comment for the column
            description: Extended description for documentation
            after_column: For MySQL, position this column after the specified column
            **extra_attributes: Additional dialect-specific attributes

        Note:
            Primary key, foreign key, and unique constraints should be added
            separately using add_primary_key_constraint(), add_foreign_key_constraint(),
            and add_unique_constraint() methods for proper constraint management.
        """
        # Convert string data_type to COLUMNDTYPE if necessary
        if isinstance(data_type, str):
            # Try to find matching COLUMNDTYPE enum value
            try:
                data_type = COLUMNDTYPE[data_type.upper()]
            except KeyError:
                # If not found, use VARCHAR as default
                data_type = COLUMNDTYPE.VARCHAR
                logger.warning(f"Unknown data type '{data_type}', defaulting to VARCHAR", emoji="⚠️")

        column = ColumnDefinition(
            name=name,
            data_type=data_type,
            dialect=self.dialect,
            length=length,
            precision=precision,
            scale=scale,
            nullable=nullable,
            default_value=default_value,
            default_expression=default_expression,
            is_identity=is_identity,
            identity_seed=identity_seed,
            identity_increment=identity_increment,
            character_set=character_set,
            collation=collation,
            check_constraint=check_constraint,
            check_constraint_name=check_constraint_name,
            is_computed=is_computed,
            computed_expression=computed_expression,
            is_stored=is_stored,
            comment=comment,
            description=description,
            after_column=after_column,
            extra_attributes=extra_attributes,
        )

        self.definition.columns.append(column)
        logger.debug(f"Added column definition: {name} ({data_type})", emoji="➕")

    def drop_column(self, column_name: str, **kwargs) -> bool:
        """
        Drop a column from the table.

        Args:
            column_name: Name of the column to drop
            **kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection

        Returns:
            True if successful, False otherwise
        """

        try:
            alter_sql = f"ALTER TABLE {self.full_table_name} DROP COLUMN {self._validate_identifier(identifier=column_name, context=DatabaseObjectType.COLUMN)}"

            logger.debug(f"Dropping column {column_name} from {self.full_table_name}", emoji="➖")
            self.connection.execute_query(alter_sql, **kwargs)

            logger.debug(f"Successfully dropped column {column_name}", emoji="✅")
            return True

        except Exception as e:
            logger.error(f"Failed to drop column {column_name}: {e}", emoji="❌")
            raise

    # ========== CONSTRAINT OPERATIONS ==========

    def add_primary_key_constraint(self, name: str, columns: List[str]) -> None:
        """Add a primary key constraint definition."""
        constraint = ConstraintDefinition(name=name, constraint_type=TableComponentType.PRIMARY_KEY, columns=columns)
        self.definition.constraints.append(constraint)
        logger.debug(f"Added primary key constraint: {name} on {columns}", emoji="🔑")

    def add_foreign_key_constraint(
        self,
        name: str,
        columns: List[str],
        reference_table: str,
        reference_columns: List[str],
        on_delete: Optional[str] = None,
        on_update: Optional[str] = None,
    ) -> None:
        """Add a foreign key constraint definition."""
        constraint = ConstraintDefinition(
            name=name,
            constraint_type=TableComponentType.FOREIGN_KEY,
            columns=columns,
            reference_table=reference_table,
            reference_columns=reference_columns,
            on_delete=on_delete,
            on_update=on_update,
        )
        self.definition.constraints.append(constraint)
        logger.debug(
            f"Added foreign key constraint: {name} ({columns} -> {reference_table}.{reference_columns})", emoji="🔗"
        )

    def add_unique_constraint(self, name: str, columns: List[str]) -> None:
        """Add a unique constraint definition."""
        constraint = ConstraintDefinition(
            name=name, constraint_type=TableComponentType.UNIQUE_CONSTRAINT, columns=columns
        )
        self.definition.constraints.append(constraint)
        logger.debug(f"Added unique constraint: {name} on {columns}", emoji="🦄")

    def drop_constraint(self, constraint_name: str, **kwargs) -> bool:
        """
        Drop a constraint from the table.

        Args:
            constraint_name: Name of the constraint to drop
            **kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection

        Returns:
            True if successful, False otherwise
        """

        try:
            constraint_name_quoted = self._validate_identifier(
                identifier=constraint_name, context=DatabaseObjectType.CONSTRAINT
            )
            alter_sql = f"ALTER TABLE {self.full_table_name} DROP CONSTRAINT {constraint_name_quoted}"

            logger.debug(f"Dropping constraint {constraint_name} from {self.full_table_name}", emoji="🔓")
            self.connection.execute_query(alter_sql, **kwargs)

            logger.debug(f"Successfully dropped constraint {constraint_name}", emoji="✅")
            return True

        except Exception as e:
            logger.error(f"Failed to drop constraint {constraint_name}: {e}", emoji="❌")
            raise

    # ========== INDEX OPERATIONS ==========

    def add_index(
        self,
        name: str,
        columns: List[str],
        is_unique: bool = False,
        is_clustered: bool = False,
        where_clause: Optional[str] = None,
        include_columns: Optional[List[str]] = None,
    ) -> None:
        """Add an index definition."""
        index = IndexDefinition(
            name=name,
            columns=columns,
            is_unique=is_unique,
            is_clustered=is_clustered,
            where_clause=where_clause,
            include_columns=include_columns,
        )
        self.definition.indexes.append(index)
        logger.debug(f"Added index definition: {name} on {columns}", emoji="📇")

    def drop_index(self, index_name: str, **kwargs) -> bool:
        """
        Drop an index from the table.

        Args:
            index_name: Name of the index to drop
            **kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection

        Returns:
            True if successful, False otherwise
        """

        try:
            idx_name = self._validate_identifier(identifier=index_name, context=DatabaseObjectType.INDEX)
            if self.dialect == SQLDialect.SQLSERVER:
                drop_sql = f"DROP INDEX {idx_name} ON {self.full_table_name}"
            else:
                drop_sql = f"DROP INDEX {idx_name}"

            logger.debug(f"Dropping index {index_name} from {self.full_table_name}", emoji="🗑️")
            self.connection.execute_query(drop_sql, **kwargs)

            logger.debug(f"Successfully dropped index {index_name}", emoji="✅")
            return True

        except Exception as e:
            logger.error(f"Failed to drop index {index_name}: {e}", emoji="❌")
            raise

    # ========== SQL GENERATION METHODS ==========

    def _generate_all_creation_sql(
        self,
        if_exists: Literal["fail", "replace", "append"],
        defer_constraints: bool = False,
        defer_indexes: bool = False,
    ) -> Tuple[List[str], List[str]]:
        """Generate all SQL statements needed for table creation.

        Args:
            if_exists: Action to take if table exists ('fail', 'replace', 'append')
            defer_constraints: If True, return constraint SQL separately for deferred execution
            defer_indexes: If True, return index SQL separately for deferred execution

        Returns:
            Tuple of (immediate_statements, deferred_statements)
        """
        immediate_statements = []
        deferred_statements = []

        # No need to add DROP statement here since it's handled in the runtime logic
        # The create_table method already handles dropping when if_exists='replace'

        # Generate CREATE TABLE statement
        create_sql = self._generate_create_table_sql(if_exists)
        immediate_statements.append(f"-- Create table\n{create_sql};")

        # Generate constraint statements (skip single-column primary keys as they're handled inline)
        for constraint in self.definition.constraints:
            # Skip single-column primary keys since they're handled inline in CREATE TABLE
            if constraint.constraint_type == TableComponentType.PRIMARY_KEY and len(constraint.columns) == 1:
                continue

            constraint_sql = self._generate_constraint_sql(constraint)
            constraint_statement = f"-- Add constraint: {constraint.name}\n{constraint_sql};"

            if defer_constraints:
                deferred_statements.append(constraint_statement)
            else:
                immediate_statements.append(constraint_statement)

        # Generate index statements
        for index in self.definition.indexes:
            index_sql = self._generate_index_sql(index)
            index_statement = f"-- Create index: {index.name}\n{index_sql};"

            if defer_indexes:
                deferred_statements.append(index_statement)
            else:
                immediate_statements.append(index_statement)

        return immediate_statements, deferred_statements

    def _generate_create_table_sql(self, if_exists: Literal["fail", "replace", "append"] = "fail") -> str:
        """Generate CREATE TABLE SQL statement."""
        # Base CREATE TABLE
        create_clause = "CREATE TABLE"
        if if_exists in ["append"] and self.dialect.supports_if_not_exists(DatabaseObjectType.TABLE):
            create_clause += " IF NOT EXISTS"

        create_sql = f"{create_clause} {self.full_table_name} (\n"

        # Add columns
        column_definitions = []
        for column in self.definition.columns:
            col_def = self._generate_column_definition(column)
            column_definitions.append(f"    {col_def}")

        # Add inline constraints (primary keys, unique, check, etc.)
        inline_constraints = []
        for constraint in self.definition.constraints:
            if constraint.constraint_type == TableComponentType.PRIMARY_KEY:
                # For single-column primary keys, we can add PRIMARY KEY directly to column definition
                # For multi-column primary keys, we need a table-level constraint
                if len(constraint.columns) == 1:
                    # Single column primary key - add to column definition
                    column_name = constraint.columns[0]
                    for i, col_def in enumerate(column_definitions):
                        if col_def.strip().startswith(
                            self._quote_identifier(column_name, context=DatabaseObjectType.COLUMN)
                        ):
                            # Add PRIMARY KEY to the column definition
                            column_definitions[i] = col_def + " PRIMARY KEY"
                            break
                else:
                    # Multi-column primary key - add as table constraint
                    pk_def = f"CONSTRAINT {self._quote_identifier(constraint.name, context=DatabaseObjectType.CONSTRAINT)} PRIMARY KEY ({', '.join([self._quote_identifier(col, context=DatabaseObjectType.COLUMN) for col in constraint.columns])})"
                    inline_constraints.append(f"    {pk_def}")

        all_definitions = column_definitions + inline_constraints
        create_sql += ",\n".join(all_definitions)
        create_sql += "\n)"

        # Add table options if needed
        if self.definition.tablespace:
            if self.dialect == SQLDialect.ORACLE:
                create_sql += f" TABLESPACE {self.definition.tablespace}"
            elif self.dialect == SQLDialect.POSTGRESQL:
                create_sql += f" TABLESPACE {self.definition.tablespace}"

        return create_sql

    def _generate_column_definition(self, column: ColumnDefinition) -> str:
        """
        Generate comprehensive column definition SQL.

        Supports all column attributes including:
        - Data types with size specifications
        - Identity/auto-increment with custom seed/increment
        - Computed/generated columns
        - Collation and character sets
        - Column-level check constraints
        - Default values and expressions
        """
        col_name = self._quote_identifier(column.name, context=DatabaseObjectType.COLUMN)

        # Handle computed columns
        if column.is_computed and column.computed_expression:
            if self.dialect == SQLDialect.SQLSERVER:
                stored_clause = " PERSISTED" if column.is_stored else ""
                return f"{col_name} AS ({column.computed_expression}){stored_clause}"
            elif self.dialect == SQLDialect.POSTGRESQL:
                stored_clause = " STORED" if column.is_stored else ""
                return f"{col_name} GENERATED ALWAYS AS ({column.computed_expression}){stored_clause}"
            elif self.dialect == SQLDialect.MYSQL:
                stored_clause = " STORED" if column.is_stored else " VIRTUAL"
                return f"{col_name} GENERATED ALWAYS AS ({column.computed_expression}){stored_clause}"
            else:
                # Generic computed column (may not be supported by all dialects)
                return f"{col_name} AS ({column.computed_expression})"

        # Data type
        if isinstance(column.data_type, COLUMNDTYPE):
            # Create size specification from column attributes
            if column.time_precision is not None and column.data_type.category in ["time", "datetime"]:
                # For temporal types, use time_precision as the size_spec
                size_spec = column.time_precision
            elif column.precision is not None and column.scale is not None:
                size_spec = (column.precision, column.scale)
            elif column.precision is not None:
                size_spec = column.precision
            elif column.length is not None:
                size_spec = column.length
            else:
                size_spec = None

            data_type = self._map_column_type_to_sql(column.data_type, size_spec)
        else:
            data_type = str(column.data_type)

        col_def = f"{col_name} {data_type}"

        # Character set and collation (for string types)
        if column.is_string_type:
            if column.character_set:
                if self.dialect == SQLDialect.MYSQL:
                    col_def += f" CHARACTER SET {column.character_set}"
                elif self.dialect == SQLDialect.SQLSERVER:
                    # SQL Server doesn't have separate CHARACTER SET syntax
                    pass

            if column.collation:
                if self.dialect in [SQLDialect.MYSQL, SQLDialect.POSTGRESQL, SQLDialect.SQLSERVER]:
                    col_def += f" COLLATE {column.collation}"

        # Identity/Auto-increment with custom parameters
        if column.is_identity:
            if self.dialect == SQLDialect.SQLSERVER:
                seed = column.identity_seed or 1
                increment = column.identity_increment or 1
                col_def += f" IDENTITY({seed},{increment})"
            elif self.dialect == SQLDialect.POSTGRESQL:
                if column.identity_seed or column.identity_increment:
                    # PostgreSQL 10+ supports IDENTITY columns
                    col_def += " GENERATED BY DEFAULT AS IDENTITY"
                else:
                    # Fall back to SERIAL for older PostgreSQL
                    col_def = f"{col_name} SERIAL"
            elif self.dialect == SQLDialect.MYSQL:
                col_def += " AUTO_INCREMENT"
            elif self.dialect == SQLDialect.ORACLE:
                col_def += " GENERATED BY DEFAULT AS IDENTITY"

        # Oracle requires DEFAULT before NOT NULL
        # Other databases can have them in either order, but we follow Oracle's requirement
        # DEFAULT first, then NOT NULL

        # Default value or expression
        if column.default_expression:
            col_def += f" DEFAULT {column.default_expression}"
        elif column.default_value:
            # Quote string literals appropriately
            if column.is_string_type and not column.default_value.upper().startswith(("NULL", "CURRENT_", "NOW()")):
                col_def += f" DEFAULT '{column.default_value}'"
            else:
                col_def += f" DEFAULT {column.default_value}"

        # Nullable (comes after DEFAULT for Oracle compatibility)
        if not column.nullable:
            col_def += " NOT NULL"

        # Column-level check constraint
        if column.check_constraint:
            constraint_name = column.check_constraint_name or f"chk_{column.name}"
            if self.dialect in [SQLDialect.POSTGRESQL, SQLDialect.SQLSERVER, SQLDialect.ORACLE]:
                col_def += f" CONSTRAINT {self._quote_identifier(constraint_name, context=DatabaseObjectType.CONSTRAINT)} CHECK ({column.check_constraint})"
            elif self.dialect == SQLDialect.MYSQL:
                # MySQL 8.0+ supports check constraints
                col_def += f" CHECK ({column.check_constraint})"

        # Add comment if supported
        if column.comment:
            if self.dialect == SQLDialect.MYSQL:
                col_def += f" COMMENT '{column.comment}'"
            # PostgreSQL and others handle comments separately via COMMENT ON COLUMN

        return col_def

    def _map_column_type_to_sql(
        self, col_type: COLUMNDTYPE, size_spec: Union[int, Tuple[int, ...], str, None] = None
    ) -> str:
        """
        Map COLUMNDTYPE enum to SQL data type string.

        This method uses the centralized to_sql_string method from COLUMNDTYPE
        which handles all dialect-specific mappings and parameter formatting.

        Args:
            col_type: The COLUMNDTYPE enum value
            size_spec: Size specification for the type:
                - int: length for VARCHAR, CHAR, etc. or precision for temporal types
                - tuple(int): precision for DECIMAL, or (precision, scale) for DECIMAL
                - str: custom size specification like "(10,2)"
                - None: use default sizing

        Returns:
            SQL type string appropriate for the current dialect
        """
        return COLUMNDTYPE.to_sql_string(col_type, self.dialect, size_spec)

    def _generate_drop_table_sql(self, if_exists: bool = True) -> str:
        """Generate DROP TABLE SQL statement."""
        drop_clause = "DROP TABLE"
        if if_exists and self.supports_if_exists:
            drop_clause += " IF EXISTS"

        return f"{drop_clause} {self.full_table_name}"

    def _generate_constraint_sql(self, constraint: ConstraintDefinition) -> str:
        """Generate constraint creation SQL."""
        base_sql = f"ALTER TABLE {self.full_table_name} ADD CONSTRAINT {self._quote_identifier(constraint.name, context=DatabaseObjectType.CONSTRAINT)}"

        if constraint.constraint_type == TableComponentType.PRIMARY_KEY:
            columns_str = ", ".join(
                [self._quote_identifier(col, context=DatabaseObjectType.COLUMN) for col in constraint.columns]
            )
            return f"{base_sql} PRIMARY KEY ({columns_str})"

        elif constraint.constraint_type == TableComponentType.FOREIGN_KEY:
            columns_str = ", ".join(
                [self._quote_identifier(col, context=DatabaseObjectType.COLUMN) for col in constraint.columns]
            )
            ref_columns_str = ", ".join(
                [
                    self._quote_identifier(col, context=DatabaseObjectType.COLUMN)
                    for col in constraint.reference_columns or []
                ]
            )
            ref_table = self._quote_identifier(constraint.reference_table or "", context=DatabaseObjectType.TABLE)

            fk_sql = f"{base_sql} FOREIGN KEY ({columns_str}) REFERENCES {ref_table} ({ref_columns_str})"

            if constraint.on_delete:
                fk_sql += f" ON DELETE {constraint.on_delete}"
            if constraint.on_update:
                fk_sql += f" ON UPDATE {constraint.on_update}"

            return fk_sql

        elif constraint.constraint_type == TableComponentType.UNIQUE_CONSTRAINT:
            columns_str = ", ".join(
                [self._quote_identifier(col, context=DatabaseObjectType.COLUMN) for col in constraint.columns]
            )
            return f"{base_sql} UNIQUE ({columns_str})"

        elif constraint.constraint_type == TableComponentType.CHECK_CONSTRAINT:
            return f"{base_sql} CHECK ({constraint.check_expression})"

        return base_sql

    def _generate_index_sql(self, index: IndexDefinition) -> str:
        """Generate index creation SQL."""
        create_clause = "CREATE"
        if index.is_unique:
            create_clause += " UNIQUE"
        if index.is_clustered and self.dialect == SQLDialect.SQLSERVER:
            create_clause += " CLUSTERED"

        create_clause += " INDEX"

        columns_str = ", ".join(
            [self._quote_identifier(col, context=DatabaseObjectType.COLUMN) for col in index.columns]
        )

        index_sql = f"{create_clause} {self._quote_identifier(index.name, context=DatabaseObjectType.INDEX)} ON {self.full_table_name} ({columns_str})"

        # Include columns (SQL Server)
        if index.include_columns and self.dialect == SQLDialect.SQLSERVER:
            include_str = ", ".join(
                [self._quote_identifier(col, context=DatabaseObjectType.COLUMN) for col in index.include_columns]
            )
            index_sql += f" INCLUDE ({include_str})"

        # WHERE clause for partial indexes
        if index.where_clause:
            index_sql += f" WHERE {index.where_clause}"

        return index_sql

    def prepare_insert_statement(
        self,
        columns: Optional[List[str]] = None,
        include_identity: bool = False,
        insert_mode: Literal["insert", "upsert", "ignore"] = "insert",
        batch_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Prepare an INSERT statement template for the table based on the current dialect.

        This method generates the SQL template and metadata needed for data insertion,
        but does not execute any SQL. It returns the prepared statement and parameter
        information that can be used later for actual data insertion.

        Args:
            columns: List of column names to include in the INSERT. If None, uses all table columns.
            include_identity: Whether to include identity/auto-increment columns in the INSERT
            insert_mode: Type of insert operation:
                - 'insert': Standard INSERT statement
                - 'upsert': INSERT with conflict resolution (INSERT ... ON CONFLICT/DUPLICATE KEY UPDATE)
                - 'ignore': INSERT IGNORE or INSERT ... ON CONFLICT DO NOTHING
            batch_size: Number of rows to insert per batch (affects parameter placeholder generation)

        Returns:
            Dictionary containing:
            - 'sql': The prepared SQL statement template
            - 'columns': List of column names in insertion order
            - 'parameter_style': Parameter style for the dialect ('named', 'numeric', 'format', 'pyformat')
            - 'placeholders': List of parameter placeholders for one row
            - 'batch_placeholders': Parameter placeholders for batch insert (if batch_size specified)
            - 'supports_returning': Whether the dialect supports RETURNING clause
            - 'metadata': Additional dialect-specific information

        Example:
            # Prepare standard insert
            insert_info = table.prepare_insert_statement(['name', 'email'])
            # Returns: {'sql': 'INSERT INTO users (name, email) VALUES (?, ?)', ...}

            # Prepare upsert with conflict resolution
            insert_info = table.prepare_insert_statement(insert_mode='upsert')

            # Prepare batch insert
            insert_info = table.prepare_insert_statement(batch_size=100)
        """
        if not self.definition.columns:
            raise ValueError("No columns defined for table. Cannot prepare insert statement.")

        # Determine which columns to include
        target_columns = []
        if columns is None:
            # Use all columns
            for column in self.definition.columns:
                # Skip identity columns unless explicitly requested
                if column.is_identity and not include_identity:
                    continue
                # Skip computed columns as they can't be inserted
                if column.is_computed:
                    continue
                target_columns.append(column.name)
        else:
            target_columns = columns.copy()

        if not target_columns:
            raise ValueError("No insertable columns found. Check include_identity parameter.")

        # Quote column names for SQL
        quoted_columns = [self._quote_identifier(col, context=DatabaseObjectType.COLUMN) for col in target_columns]
        columns_clause = ", ".join(quoted_columns)

        # Determine parameter style for the dialect
        parameter_info = self._get_parameter_style()

        # Generate parameter placeholders for a single row
        single_row_placeholders = []
        for i, col in enumerate(target_columns):
            if parameter_info["style"] == "named":
                single_row_placeholders.append(f":{col}")
            elif parameter_info["style"] == "pyformat":
                single_row_placeholders.append(f"%({col})s")
            elif parameter_info["style"] == "numeric":
                single_row_placeholders.append(f":{i+1}")  # Oracle uses :1, :2, :3
            elif parameter_info["style"] == "format":
                single_row_placeholders.append("%s")
            else:  # qmark (default)
                single_row_placeholders.append("?")

        values_clause = ", ".join(single_row_placeholders)

        # Generate batch placeholders if batch_size is specified
        batch_placeholders = None
        if batch_size and batch_size > 1:
            batch_rows = []
            for row_num in range(batch_size):
                row_placeholders = []
                for i, col in enumerate(target_columns):
                    if parameter_info["style"] == "named":
                        row_placeholders.append(f":{col}_{row_num}")
                    elif parameter_info["style"] == "pyformat":
                        row_placeholders.append(f"%({col}_{row_num})s")
                    elif parameter_info["style"] == "numeric":
                        param_num = row_num * len(target_columns) + i + 1
                        row_placeholders.append(f":{param_num}")  # Oracle uses :1, :2, :3
                    elif parameter_info["style"] == "format":
                        row_placeholders.append("%s")
                    else:  # qmark (default)
                        row_placeholders.append("?")
                batch_rows.append(f"({', '.join(row_placeholders)})")
            batch_placeholders = ", ".join(batch_rows)

        # Build the base INSERT statement
        base_sql = f"INSERT INTO {self.full_table_name} ({columns_clause})"

        # Handle different insert modes
        if insert_mode == "insert":
            # Standard INSERT
            if batch_placeholders:
                sql = f"{base_sql} VALUES {batch_placeholders}"
            else:
                sql = f"{base_sql} VALUES ({values_clause})"

        elif insert_mode == "ignore":
            # INSERT IGNORE or equivalent
            sql = self._generate_insert_ignore_sql(base_sql, values_clause, batch_placeholders)

        elif insert_mode == "upsert":
            # INSERT with ON CONFLICT/DUPLICATE KEY UPDATE
            sql = self._generate_upsert_sql(base_sql, values_clause, batch_placeholders, target_columns)
        else:
            raise ValueError(f"Invalid insert_mode: {insert_mode}")

        # Check if dialect supports RETURNING clause
        supports_returning = self.dialect in [SQLDialect.POSTGRESQL, SQLDialect.ORACLE, SQLDialect.SQLSERVER]

        # Prepare metadata
        metadata = {
            "table_name": self.full_table_name,
            "dialect": self.dialect.value,
            "insert_mode": insert_mode,
            "total_columns": len(target_columns),
            "batch_size": batch_size or 1,
            "has_identity": any(col.is_identity for col in self.definition.columns if col.name in target_columns),
            "has_defaults": any(
                col.default_value or col.default_expression
                for col in self.definition.columns
                if col.name in target_columns
            ),
        }

        result = {
            "sql": sql,
            "columns": target_columns,
            "parameter_style": parameter_info["style"],
            "placeholders": single_row_placeholders,
            "batch_placeholders": batch_placeholders,
            "supports_returning": supports_returning,
            "metadata": metadata,
        }

        logger.debug(f"Prepared {insert_mode} statement for {len(target_columns)} columns", emoji="📝")

        return result

    def _get_parameter_style(self) -> Dict[str, str]:
        """Get the parameter style for the current dialect using centralized preferences."""
        # Use the centralized parameter style preference from the dialect
        style = self.dialect.parameter_style_preference

        # Map styles to descriptions
        style_descriptions = {
            "qmark": "Question mark style (?)",
            "format": "ANSI C printf format codes (%s)",
            "named": "Named parameters (:name)",
            "pyformat": "Python extended format codes (%(name)s)",
            "numeric": "Numeric format ($1, $2, ...)",
        }

        description = style_descriptions.get(style, f"Unknown style: {style}")

        return {"style": style, "description": f"{description} - {self.dialect.description}"}

    def _generate_insert_ignore_sql(self, base_sql: str, values_clause: str, batch_placeholders: Optional[str]) -> str:
        """Generate INSERT IGNORE or equivalent SQL for the dialect."""
        values_part = f" VALUES {batch_placeholders}" if batch_placeholders else f" VALUES ({values_clause})"

        if self.dialect == SQLDialect.MYSQL:
            return f"{base_sql.replace('INSERT', 'INSERT IGNORE')}{values_part}"
        elif self.dialect == SQLDialect.POSTGRESQL:
            return f"{base_sql}{values_part} ON CONFLICT DO NOTHING"
        elif self.dialect == SQLDialect.SQLITE:
            return f"{base_sql.replace('INSERT', 'INSERT OR IGNORE')}{values_part}"
        elif self.dialect == SQLDialect.SQLSERVER:
            # SQL Server doesn't have direct INSERT IGNORE, use MERGE or IF NOT EXISTS
            return f"{base_sql}{values_part} -- Note: SQL Server requires MERGE for ignore behavior"
        else:
            # For other dialects, fall back to standard INSERT with a note
            return f"{base_sql}{values_part} -- Note: {self.dialect.value} may not support ignore behavior"

    def _generate_upsert_sql(
        self, base_sql: str, values_clause: str, batch_placeholders: Optional[str], target_columns: List[str]
    ) -> str:
        """Generate INSERT with upsert (ON CONFLICT/DUPLICATE KEY UPDATE) SQL."""
        values_part = f" VALUES {batch_placeholders}" if batch_placeholders else f" VALUES ({values_clause})"

        # Determine conflict columns (default to primary key columns)
        pk_constraints = [c for c in self.definition.constraints if c.constraint_type == TableComponentType.PRIMARY_KEY]
        if pk_constraints:
            conflict_columns = pk_constraints[0].columns
        else:
            raise ValueError("No primary key found for upsert operation")

        # Determine update columns (default to all non-key columns)
        update_columns = [col for col in target_columns if col not in conflict_columns]

        if not update_columns:
            raise ValueError("No update columns available for upsert (all columns are part of the primary key)")

        if self.dialect == SQLDialect.POSTGRESQL:
            conflict_cols = ", ".join(
                [self._quote_identifier(col, context=DatabaseObjectType.COLUMN) for col in conflict_columns]
            )
            update_sets = []
            for col in update_columns:
                quoted_col = self._quote_identifier(col, context=DatabaseObjectType.COLUMN)
                update_sets.append(f"{quoted_col} = EXCLUDED.{quoted_col}")
            update_clause = ", ".join(update_sets)
            return f"{base_sql}{values_part} ON CONFLICT ({conflict_cols}) DO UPDATE SET {update_clause}"

        elif self.dialect == SQLDialect.MYSQL:
            update_sets = []
            for col in update_columns:
                quoted_col = self._quote_identifier(col, context=DatabaseObjectType.COLUMN)
                update_sets.append(f"{quoted_col} = VALUES({quoted_col})")
            update_clause = ", ".join(update_sets)
            return f"{base_sql}{values_part} ON DUPLICATE KEY UPDATE {update_clause}"

        elif self.dialect == SQLDialect.SQLITE:
            conflict_cols = ", ".join(
                [self._quote_identifier(col, context=DatabaseObjectType.COLUMN) for col in conflict_columns]
            )
            update_sets = []
            for col in update_columns:
                quoted_col = self._quote_identifier(col, context=DatabaseObjectType.COLUMN)
                update_sets.append(f"{quoted_col} = excluded.{quoted_col}")
            update_clause = ", ".join(update_sets)
            return f"{base_sql}{values_part} ON CONFLICT ({conflict_cols}) DO UPDATE SET {update_clause}"

        elif self.dialect == SQLDialect.SQLSERVER:
            # SQL Server uses MERGE statement for upsert
            return f"{base_sql}{values_part} -- Note: SQL Server requires MERGE statement for full upsert behavior"

        else:
            # For other dialects, provide a basic structure with notes
            return f"{base_sql}{values_part} -- Note: {self.dialect.value} upsert syntax may differ"

    # ========== UTILITY METHODS ==========

    def backup_table(self, backup_table_name: Optional[str] = None, **kwargs) -> str:
        """
        Create a backup copy of the table.

        Args:
            backup_table_name: Name for backup table (auto-generated if not provided)
            **kwargs: Transaction configuration parameters including:
                max_retries: Maximum number of retry attempts (default: 3)
                base_retry_delay: Base delay between retries in seconds
                max_retry_delay: Maximum delay between retries in seconds
                isolation_level: Transaction isolation level
                timeout: Query timeout in seconds
                enable_deadlock_detection: Whether to enable deadlock detection

        Returns:
            Name of the backup table created
        """

        import datetime

        if not backup_table_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_table_name = f"{self.table_name}_backup_{timestamp}"

        backup_sql = f"CREATE TABLE {self._quote_identifier(backup_table_name, context=DatabaseObjectType.TABLE)} AS SELECT * FROM {self.full_table_name}"

        try:
            logger.debug(f"Creating backup table {backup_table_name}", emoji="💾")
            self.connection.execute_query(backup_sql, **kwargs)
            logger.debug(f"Successfully created backup table {backup_table_name}", emoji="✅")
            return backup_table_name
        except Exception as e:
            logger.error(f"Failed to create backup table: {e}", emoji="❌")
            raise

    def analyze_table(self) -> Dict[str, Any]:
        """
        Analyze the table and return statistics.

        Returns:
            Dictionary containing table analysis results
        """
        if not self.exists():
            return {"error": "Table does not exist"}

        analysis = {
            "table_info": self.get_table_info(),
            "row_count": self.get_row_count(),
            "size_info": self.get_size_info(),
            "column_count": len(self.get_columns()),
            "constraint_count": len(self.get_constraints()),
            "index_count": len(self.get_indexes()),
        }

        logger.debug(f"Completed analysis of {self.full_table_name}", emoji="📈")
        return analysis

    def generate_documentation(self) -> str:
        """
        Generate comprehensive documentation for the table.

        Returns:
            Formatted documentation string
        """
        if not self.exists():
            return f"# Table Documentation: {self.full_table_name}\n\n**Table does not exist**"

        info = self.get_table_info()

        doc = f"""# Table Documentation: {self.full_table_name}

## Basic Information
- **Table Name**: {self.table_name}
- **Schema**: {self.schema or 'default'}
- **Database Dialect**: {self.dialect.value}
- **Row Count**: {info.get('row_count', 'Unknown'):,}

## Columns
"""

        for column in info.get("columns", []):
            doc += f"- **{column.get('name')}**: {column.get('data_type')}"
            if not column.get("nullable", True):
                doc += " (NOT NULL)"
            if column.get("default_value"):
                doc += f" DEFAULT {column.get('default_value')}"
            doc += "\n"

        doc += f"""
## Constraints
Total: {len(info.get('constraints', []))}

## Indexes  
Total: {len(info.get('indexes', []))}

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        logger.debug(f"Generated documentation for {self.full_table_name}", emoji="📖")
        return doc

    def create_table_from_dataframe(
        self,
        df,  # pandas DataFrame
        default_table_name: Optional[str] = None,
        default_schema_name: Optional[str] = None,
        if_exists: Literal["fail", "replace", "append"] = "append",
        dry_run: bool = False,
    ) -> Union[bool, str, Tuple[bool, List[str]]]:
        """
        Create a table from a pandas DataFrame containing table definition.

        Required columns:
        - FieldName: Name of the database column
        - Datatype: Data type for the column

        Optional columns:
        - SchemaName: Schema for the table (overrides default_schema_name)
        - TableName: Table name (overrides default_table_name)
        - isRequired: Boolean indicating if column is NOT NULL (default False)
        - userGuidance: Comment or description for the column
        - isPrimaryKey: Boolean indicating if column is part of primary key (default False)
        - isForeignKey: Boolean indicating if column is a foreign key (default False)
        - fkTableName: Name of the referenced table for foreign key
        - fkFieldName: Name of the referenced column for foreign key

        Args:
            df: pandas DataFrame with table definition
            default_table_name: Default table name if not specified in DataFrame
            default_schema_name: Default schema name if not specified in DataFrame
            if_exists: How to behave if the table already exists:
                - 'fail': Raise a ValueError if table exists
                - 'replace': Drop the table before creating (recreate)
                - 'append': Create only if table doesn't exist (IF NOT EXISTS)
            dry_run: If True, return the SQL statements instead of executing them

        Returns:
            If dry_run=True: String containing the SQL statements
            If dry_run=False: True if successful, False otherwise

        Example:
            import pandas as pd

            # Create definition DataFrame
            table_def = pd.DataFrame([
                {'FieldName': 'id', 'Datatype': 'INTEGER', 'isPrimaryKey': True, 'isRequired': True},
                {'FieldName': 'name', 'Datatype': 'VARCHAR(255)', 'isRequired': True},
                {'FieldName': 'email', 'Datatype': 'VARCHAR(255)', 'isRequired': False},
                {'FieldName': 'created_at', 'Datatype': 'TIMESTAMP', 'isRequired': True},
                {'FieldName': 'user_id', 'Datatype': 'INTEGER', 'isRequired': True, 'isForeignKey': True, 'fkTableName': 'users', 'fkFieldName': 'id'}
            ])

            # Create table with different modes
            sql_table = SQL_TABLE(connection, 'users')
            sql_table.create_table_from_dataframe(table_def, if_exists='replace')  # Drop and recreate
            sql_table.create_table_from_dataframe(table_def, if_exists='append')   # Create if not exists
            sql_table.create_table_from_dataframe(table_def, if_exists='fail')     # Fail if exists
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for create_table_from_dataframe method")

        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")

        # Validate if_exists parameter
        valid_if_exists = ["fail", "replace", "append"]
        if if_exists not in valid_if_exists:
            raise ValueError(f"if_exists must be one of {valid_if_exists}, got '{if_exists}'")

        # Validate required columns
        required_columns = ["FieldName", "Datatype"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"DataFrame is missing required columns: {missing_columns}")

        if df.empty:
            raise ValueError("DataFrame cannot be empty")

        logger.debug(f"Creating table from DataFrame with {len(df)} column definitions", emoji="📊")

        # Determine table name and schema
        table_name = default_table_name or self.table_name
        schema_name = default_schema_name or self.schema

        # Check if DataFrame contains table/schema overrides
        if "TableName" in df.columns:
            table_names = df["TableName"].dropna().unique()
            if len(table_names) > 1:
                # Multiple tables detected - process each table separately
                logger.debug(
                    f"DataFrame contains {len(table_names)} different tables. Processing each separately.", emoji="🔄"
                )
                results = []
                sql_outputs = []

                for table_name_iter in table_names:
                    # Use pandas query to filter DataFrame for this specific table
                    table_df = df.query(f"TableName == '{table_name_iter}'").copy()

                    logger.debug(f"Processing table: {table_name_iter} with {len(table_df)} columns", emoji="🏗️")

                    # Recursively call this method with the filtered DataFrame
                    try:
                        result = self.create_table_from_dataframe(
                            df=table_df,
                            default_table_name=str(table_name_iter),
                            default_schema_name=default_schema_name,
                            if_exists=if_exists,
                            dry_run=dry_run,
                        )

                        if dry_run:
                            sql_outputs.append(f"-- Table: {table_name_iter}\n{result}")
                            results.append((table_name_iter, True))  # Consider successful for dry run
                        else:
                            results.append((table_name_iter, result))
                        logger.debug(f"Successfully processed table: {table_name_iter}", emoji="✅")
                    except Exception as e:
                        logger.error(f"Failed to process table {table_name_iter}: {e}", emoji="❌")
                        if dry_run:
                            sql_outputs.append(f"-- Table: {table_name_iter} (ERROR: {e})")
                        results.append((table_name_iter, False))

                if dry_run:
                    # Return combined SQL for all tables
                    return "\n\n" + ("=" * 80) + "\n\n".join(sql_outputs)

                # Return True if all tables were created successfully
                all_success = all(result for _, result in results)
                success_count = sum(1 for _, result in results if result)

                logger.debug(
                    f"Completed processing {len(table_names)} tables. {success_count}/{len(table_names)} successful.",
                    emoji="📊",
                )
                return all_success
            elif len(table_names) == 1:
                table_name = table_names[0]

        if "SchemaName" in df.columns:
            schema_names = df["SchemaName"].dropna().unique()
            if len(schema_names) > 1:
                raise ValueError(f"DataFrame contains multiple schema names: {list(schema_names)}")
            elif len(schema_names) == 1:
                schema_name = schema_names[0]

        # Update instance properties if they changed
        if table_name != self.table_name:
            self.table_name = table_name
            self.definition.name = table_name
            logger.debug(f"Updated table name to: {table_name}", emoji="📝")

        if schema_name != self.schema:
            self.schema = schema_name
            self.definition.schema = schema_name
            logger.debug(f"Updated schema name to: {schema_name}", emoji="📝")

        # Clear existing definitions
        self.definition.columns.clear()
        self.definition.constraints.clear()

        # Process each row to create column definitions
        primary_key_columns = []
        foreign_key_constraints = []

        for index, row in df.iterrows():
            field_name = str(row["FieldName"]).strip()
            if not field_name:
                logger.warning(f"Skipping row {index} with empty FieldName", emoji="⚠️")
                continue

            datatype = str(row["Datatype"]).strip()
            if not datatype:
                logger.warning(f"Skipping column {field_name} with empty Datatype", emoji="⚠️")
                continue

            # Parse optional fields
            is_required = bool(row.get("isRequired", False)) if pd.notna(row.get("isRequired")) else False
            is_primary_key = bool(row.get("isPrimaryKey", False)) if pd.notna(row.get("isPrimaryKey")) else False
            is_identity = bool(row.get("isIdentity", False)) if pd.notna(row.get("isIdentity")) else False
            identity_seed = int(row.get("identitySeed", 1)) if pd.notna(row.get("identitySeed")) else None
            identity_increment = (
                int(row.get("identityIncrement", 1)) if pd.notna(row.get("identityIncrement")) else None
            )
            is_foreign_key = bool(row.get("isForeignKey", False)) if pd.notna(row.get("isForeignKey")) else False
            fk_table_name = str(row.get("fkTableName", "")).strip() if pd.notna(row.get("fkTableName")) else None
            fk_field_name = str(row.get("fkFieldName", "")).strip() if pd.notna(row.get("fkFieldName")) else None
            user_guidance = str(row.get("userGuidance", "")).strip() if pd.notna(row.get("userGuidance")) else None

            # Validate foreign key fields
            if is_foreign_key:
                if not fk_table_name or not fk_field_name:
                    logger.warning(
                        f"Column {field_name} marked as foreign key but missing fkTableName or fkFieldName", emoji="⚠️"
                    )
                    is_foreign_key = False
                else:
                    # Store foreign key constraint information for later processing
                    fk_constraint_name = f"fk_{table_name}_{field_name}"
                    foreign_key_constraints.append(
                        {
                            "name": fk_constraint_name,
                            "column": field_name,
                            "reference_table": fk_table_name,
                            "reference_column": fk_field_name,
                        }
                    )
                    logger.debug(f"Found foreign key: {field_name} -> {fk_table_name}.{fk_field_name}", emoji="🔗")

            # Parse datatype to extract length, precision, scale, time_precision
            length, precision, scale, time_precision = self._parse_datatype_specifications(datatype)

            # Map string datatype to COLUMNDTYPE enum if possible
            mapped_datatype = self._map_string_to_columndtype(datatype)

            # Ensure we have a valid COLUMNDTYPE
            final_datatype = mapped_datatype if mapped_datatype else COLUMNDTYPE.VARCHAR

            # Create column definition
            column = ColumnDefinition(
                name=field_name,
                data_type=final_datatype,
                dialect=self.dialect,
                length=length,
                precision=precision,
                scale=scale,
                time_precision=time_precision,
                nullable=not is_required,
                comment=user_guidance,
                is_identity=is_identity,
                identity_seed=identity_seed,
                identity_increment=identity_increment,
            )

            self.definition.columns.append(column)

            if is_primary_key:
                primary_key_columns.append(field_name)

            logger.debug(f"Added column: {field_name} ({datatype})", emoji="➕")

        # Create primary key constraint if any columns are marked as primary key
        if primary_key_columns:
            pk_name = f"pk_{table_name}"
            self.add_primary_key_constraint(pk_name, primary_key_columns)

        # Create foreign key constraints
        for fk_info in foreign_key_constraints:
            self.add_foreign_key_constraint(
                name=fk_info["name"],
                columns=[fk_info["column"]],
                reference_table=fk_info["reference_table"],
                reference_columns=[fk_info["reference_column"]],
            )

        # Create the table using the standardized create_table method
        logger.debug(
            f"Creating table {self.full_table_name} with {len(self.definition.columns)} columns (mode: {if_exists})",
            emoji="🏗️",
        )
        return self.create_table(if_exists=if_exists, dry_run=dry_run)

    def _parse_datatype_specifications(
        self, datatype: str
    ) -> Tuple[Optional[int | str], Optional[int], Optional[int], Optional[int]]:
        """
        Parse datatype string to extract length, precision, scale, and time_precision specifications.

        Examples:
        - VARCHAR(255) -> length=255
        - DECIMAL(10,2) -> precision=10, scale=2
        - NUMBER(10) -> precision=10
        - DATETIME2(6) -> time_precision=6
        - TIME(3) -> time_precision=3

        Returns:
            Tuple of (length, precision, scale, time_precision)
        """
        length = None
        precision = None
        scale = None
        time_precision = None

        # Pattern for VARCHAR(n), CHAR(n), VARCHAR2(n), NVARCHAR2(n), etc.
        length_pattern = r"(?:VARCHAR2?|CHAR|NVARCHAR2?|NCHAR|TEXT)\s*\((\d+|MAX)\)"
        length_match = re.search(length_pattern, datatype.upper())
        if length_match:
            length = (
                f"({length_match.group(1)})" if length_match.group(1).upper() == "MAX" else int(length_match.group(1))
            )

        # Pattern for DECIMAL(p,s), NUMBER(p,s), NUMERIC(p,s)
        precision_scale_pattern = r"(?:DECIMAL|NUMBER|NUMERIC)\s*\((\d+)(?:,\s*(\d+))?\)"
        precision_match = re.search(precision_scale_pattern, datatype.upper())
        if precision_match:
            precision = int(precision_match.group(1))
            if precision_match.group(2):
                scale = int(precision_match.group(2))

        # Pattern for temporal types with precision: TIME(n), DATETIME(n), DATETIME2(n), TIMESTAMP(n), etc.
        temporal_precision_pattern = r"(?:TIME|DATETIME|DATETIME2|TIMESTAMP|TIMESTAMPTZ|TIMETZ|SMALLDATETIME|DATETIMEOFFSET|TIME_WITH_TIME_ZONE|TIME_WITHOUT_TIME_ZONE|TIMESTAMP_WITH_TIME_ZONE|TIMESTAMP_WITHOUT_TIME_ZONE)\s*\((\d+)\)"
        temporal_match = re.search(temporal_precision_pattern, datatype.upper())
        if temporal_match:
            time_precision = int(temporal_match.group(1))

        return length, precision, scale, time_precision

    def _map_string_to_columndtype(self, datatype: str) -> Optional[COLUMNDTYPE]:
        """
        Map string datatype to COLUMNDTYPE enum with dialect compatibility.

        Args:
            datatype: String representation of data type

        Returns:
            COLUMNDTYPE enum value that is compatible with the current dialect, or None if no mapping found
        """
        # Normalize the datatype string
        base_type = datatype.upper().split("(")[0].strip()

        # First try direct enum name match
        try:
            mapped_type = COLUMNDTYPE[base_type]
            logger.trace(f"Direct mapped {datatype} to {mapped_type}", emoji="🔄")

            # Check if this type is compatible with our current dialect
            compatible_type, _dialect_params = COLUMNDTYPE.get_dialect_compatible_type(mapped_type, self.dialect)
            if compatible_type != mapped_type:
                logger.trace(
                    f"Dialect compatibility: {mapped_type} -> {compatible_type} for {self.dialect.value}", emoji="🔀"
                )

            return compatible_type

        except KeyError:
            pass

        return None

    def alter(self, **kwargs) -> bool:
        """
        Alter the table structure.

        This is a placeholder method for table alteration operations.

        Args:
            **kwargs: Alteration parameters

        Returns:
            bool: True if successful

        Note:
            This method should be implemented with specific alteration logic.
        """
        raise NotImplementedError("alter() method is not yet fully implemented")

    def describe(self, **kwargs) -> Dict[str, Any]:
        """
        Describe the table structure and metadata.

        This is a placeholder method for describing table structure.

        Args:
            **kwargs: Description parameters

        Returns:
            Dict[str, Any]: Table description

        Note:
            This method should be implemented with specific description logic.
        """
        raise NotImplementedError("describe() method is not yet fully implemented")

    def __repr__(self) -> str:
        """String representation of the SQL_TABLE instance."""
        return f"SQL_TABLE(table='{self.full_table_name}', dialect='{self.dialect.value}', exists={self.exists()})"
