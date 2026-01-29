"""
Database connections module.

This module provides the DatabaseConnection class for managing database connections
with automatic driver selection, connection pooling, and retry logic.

The module handles:
- Connection establishment and teardown
- Driver selection and fallback mechanisms
- Connection state management
- Raw connection object provision for transactions
- Integration with various database drivers

Classes
-------
DatabaseConnection
    Main class for managing database connections with automatic failover

Examples
--------
Basic connection:
    >>> from sqlutils.connections import DatabaseConnection
    >>> from sqlutils.core import SQLDialect
    >>> conn = DatabaseConnection(SQLDialect.POSTGRESQL)

Connection with explicit parameters:
    >>> conn = DatabaseConnection(
    ...     dialect=SQLDialect.MYSQL,
    ...     host='localhost',
    ...     port=3306,
    ...     database='mydb',
    ...     username='user',
    ...     password='pass'
    ... )

Using connection as context manager:
    >>> with DatabaseConnection(SQLDialect.SQLITE, database='test.db') as conn:
    ...     result = conn.execute_query("SELECT * FROM users")
"""

from .database_connection import DatabaseConnection

__all__ = [
    "DatabaseConnection",
]
