"""
SQLUtils - A comprehensive Python library for SQL database operations.

This package provides utilities for database connections, transactions,
table management, and error handling across multiple SQL dialects including
PostgreSQL, MySQL, SQL Server, Oracle, SQLite, BigQuery, and Redshift.

The library follows a modular architecture with clear separation of concerns:
- Core types and enums for dialect-agnostic database operations
- Driver management with automatic fallback capabilities
- Robust connection handling with retry logic
- Transaction management with ACID guarantees
- Comprehensive error handling and classification
- Table schema management and DDL generation
- Identifier validation and normalization
- High-performance data loading with multiple dataframe backends

Examples
--------
Basic database connection and query:
    >>> from sqlutils import DatabaseConnection, SQLDialect
    >>> conn = DatabaseConnection(SQLDialect.POSTGRESQL)
    >>> result = conn.execute_query("SELECT * FROM users")

Transaction management:
    >>> with conn.transaction() as tx:
    ...     tx.execute("INSERT INTO users VALUES (?)", (1, 'Alice'))
    ...     tx.execute("UPDATE accounts SET balance = balance - 100")

Table management:
    >>> from sqlutils import SQL_TABLE, ColumnDefinition, COLUMNDTYPE
    >>> table = SQL_TABLE(conn, "users")
    >>> table.add_column("id", COLUMNDTYPE.INTEGER, is_identity=True)
    >>> table.create_table()

High-performance data loading:
    >>> from sqlutils import read_sql
    >>> # Load data as Polars dataframe (default, highest performance)
    >>> df = read_sql("SELECT * FROM users", conn)
    >>> # Or use Pandas
    >>> df_pandas = read_sql("SELECT * FROM users", conn, output_format='pandas')

Notes
-----
This package requires appropriate database drivers to be installed separately
for each dialect you plan to use. The library will automatically detect and
use the best available driver for your environment.
"""

# Database connections
from .connections import DatabaseConnection

# Core types and enums
from .core import (
    COLUMNDTYPE,
    Column_Type,
    DatabaseObjectType,
    SQLDialect,
    TemporalPrecision,
)

# Data loading
from .download import (
    execute_query_with_metadata,
    read_sql,
)

# Driver management
from .drivers import (
    DatabaseConnectionFactory,
    DatabaseDriver,
    get_driver_config,
)

# Error handling
from .errors import SQLErrorRegistry

# Table management
from .tables import (
    SQL_TABLE,
    ColumnDefinition,
    TableDefinition,
)

# Transaction management
from .transactions import (
    IsolationLevel,
    RobustTransaction,
    TransactionConfig,
)

# Validation
from .validation import SQL_DIALECT_REGISTRY

# Version is set by setuptools-scm from git tags
try:
    from ._version import version as __version__
except ImportError:
    # Package not installed or _version.py not generated yet
    __version__ = "0.0.1.dev0"

__all__ = [
    # Core
    "DatabaseObjectType",
    "SQLDialect",
    "COLUMNDTYPE",
    "Column_Type",
    "TemporalPrecision",
    # Drivers
    "DatabaseDriver",
    "DatabaseConnectionFactory",
    "get_driver_config",
    # Connections
    "DatabaseConnection",
    # Transactions
    "RobustTransaction",
    "TransactionConfig",
    "IsolationLevel",
    # Errors
    "SQLErrorRegistry",
    # Tables
    "SQL_TABLE",
    "ColumnDefinition",
    "TableDefinition",
    # Validation
    "SQL_DIALECT_REGISTRY",
    # Data loading
    "read_sql",
    "execute_query_with_metadata",
]
