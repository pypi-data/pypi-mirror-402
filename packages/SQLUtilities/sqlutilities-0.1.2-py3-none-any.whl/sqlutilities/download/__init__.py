"""
SQL Data Loading Module.

This module provides high-performance SQL query execution with support for
multiple dataframe backends (Pandas, Polars, Dask, PyArrow). It leverages
ConnectorX for optimal performance when available and provides automatic
fallback to native drivers.

The module handles:
- Multi-backend dataframe creation (Pandas, Polars, Dask, PyArrow)
- Column type inference and metadata extraction
- ConnectorX acceleration with automatic fallback
- SQLite-specific type inference using query parsing

Functions
---------
read_sql
    Execute a SQL query and return results in various dataframe formats.
execute_query_with_metadata
    Execute a SQL query and return column metadata with data.

Examples
--------
Basic usage with Polars (default):
    >>> from download import read_sql
    >>> from connections import DatabaseConnection
    >>> conn = DatabaseConnection(dialect="postgres", host="localhost", database="mydb")
    >>> df = read_sql("SELECT * FROM users", conn)
    >>> print(df.head())

Using Pandas with parameters:
    >>> df = read_sql(
    ...     "SELECT * FROM employees WHERE salary > %s",
    ...     conn,
    ...     parameters=(50000,),
    ...     output_format='pandas'
    ... )

Using Dask for large datasets:
    >>> df = read_sql(
    ...     "SELECT * FROM large_table",
    ...     conn,
    ...     output_format='dask',
    ...     dask_partitions=8,
    ...     dask_index_column='id'
    ... )

Notes
-----
This module requires pandas as a core dependency. Polars, Dask, and PyArrow
are optional and will gracefully degrade if not installed.

ConnectorX provides the best performance but may not support all SQL dialects
or features. The module automatically falls back to native drivers when needed.
"""

from .read_sql import execute_query_with_metadata, read_sql

__all__ = [
    "read_sql",
    "execute_query_with_metadata",
]
