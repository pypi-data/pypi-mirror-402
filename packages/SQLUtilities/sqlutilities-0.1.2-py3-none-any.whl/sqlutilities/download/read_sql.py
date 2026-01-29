"""
SQL query execution and data loading module.

This module provides high-performance SQL query execution with support for
multiple dataframe backends (Pandas, Polars, Dask, PyArrow). It leverages
ConnectorX for optimal performance when available and provides automatic
fallback to native drivers.

The module handles:
- Multi-backend dataframe creation (Pandas, Polars, Dask, PyArrow)
- Column type inference and metadata extraction
- ConnectorX acceleration with automatic fallback
- SQLite-specific type inference using query parsing
- Optional dependency management with graceful degradation

Functions
---------
execute_query_with_metadata
    Execute a SQL query and return column metadata with data.
read_sql
    Execute a SQL query and return results in various dataframe formats.

Examples
--------
>>> from connections import DatabaseConnection
>>> from download.read_sql import read_sql
>>>
>>> conn = DatabaseConnection(dialect="postgres", host="localhost", database="mydb")
>>> df = read_sql("SELECT * FROM users", conn, output_format='polars')
>>> print(df.head())

See Also
--------
DatabaseConnection : Main connection interface
execute_query_with_metadata : Lower-level query execution with metadata

Notes
-----
This module requires pandas as a core dependency. Polars, Dask, and PyArrow
are optional and will gracefully degrade if not installed.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional, Self, Tuple, Union

import pandas as pd

from ..connections.database_connection import DatabaseConnection
from ..core.enums import SQLDialect
from ..drivers.type_mapping import (
    _create_fallback_columns,
    _extract_column_metadata_from_description,
    _infer_sqlite_column_types_from_query,
)

# Optional dependency: Dask for distributed dataframe operations
try:
    import dask.dataframe as dd  # type: ignore
except ImportError:
    # Create stub class that raises informative errors
    class dd:
        @staticmethod
        def from_pandas(*args, **kwargs):
            raise ImportError("Dask is not installed. Please install dask to use this feature.")

        DataFrame = None

        @staticmethod
        def read_sql_table(*args, **kwargs):
            raise ImportError("Dask is not installed. Please install dask to use this feature.")


# Optional dependency: Polars for high-performance dataframe operations
try:
    import polars as pl  # type: ignore
except ImportError:
    # Create stub class that raises informative errors
    class pl:
        @staticmethod
        def DataFrame(*args, **kwargs):
            raise ImportError("Polars is not installed. Please install polars to use this feature.")

        @staticmethod
        def read_database_uri(*args, **kwargs):
            raise ImportError("Polars is not installed. Please install polars to use this feature.")

        @staticmethod
        def read_database(*args, **kwargs):
            raise ImportError("Polars is not installed. Please install polars to use this feature.")

        @staticmethod
        def from_pandas(*args, **kwargs):
            raise ImportError("Polars is not installed. Please install polars to use this feature.")


# Optional dependency: PyArrow for columnar data format
try:
    import pyarrow as pa  # type: ignore
except ImportError:
    # Create stub class that raises informative errors
    class pa:
        class Table:
            @staticmethod
            def from_pandas(*args, **kwargs):
                raise ImportError("PyArrow is not installed. Please install pyarrow to use this feature.")


logger = logging.getLogger(__name__)


def execute_query_with_metadata(
    query: str, connection: DatabaseConnection, parameters: Optional[Union[Tuple, Dict[str, Any]]] = None
) -> Tuple[Dict[str, Any], List[List[Any]]]:
    """
    Execute a SQL query and return column metadata and data as separate structures.

    This function executes a SQL query and returns both the column metadata
    (including names and types) and the raw data as separate lists. For SQLite,
    it uses query parsing to infer types since SQLite's type system is dynamic.

    Parameters
    ----------
    query : str
        SQL query string to execute.
    connection : DatabaseConnection
        Active database connection instance.
    parameters : tuple or dict, optional
        Query parameters. Use tuple for positional parameters (e.g., ?)
        or dict for named parameters (e.g., :name or %(name)s).
        Default is None.

    Returns
    -------
    tuple
        A tuple containing two elements:
        - columns : Dict[str, Any]
            Dictionary mapping column names to their metadata (type info).
        - data : List[List[Any]]
            List of rows, where each row is a list of column values.

    Raises
    ------
    ConnectionError
        If database connection cannot be established.
    QueryExecutionError
        If query execution fails.

    Examples
    --------
    >>> from connections import DatabaseConnection
    >>> conn = DatabaseConnection(dialect="sqlite", database="test.db")
    >>> columns, data = execute_query_with_metadata(
    ...     "SELECT id, name, age FROM users WHERE age > ?",
    ...     conn,
    ...     parameters=(18,)
    ... )
    >>> print("Columns:", columns)
    {'id': {'type': 'INTEGER'}, 'name': {'type': 'TEXT'}, 'age': {'type': 'INTEGER'}}
    >>> print("First row:", data[0])
    [1, 'John Doe', 25]

    Notes
    -----
    For SQLite databases, this function uses query parsing to infer column types
    since SQLite's dynamic type system doesn't always provide reliable type
    information through cursor.description.
    """
    # Ensure connection is active before executing query
    if not connection.is_connected:
        logger.debug("Connection not active, attempting to connect...")
        connection.connect()

    # Log query execution (truncate long queries for readability)
    logger.debug(f"Executing query: {query[:100]}{'...' if len(query) > 100 else ''}")

    # Execute query through connection's metadata-aware method
    result = connection.execute_query_with_metadata(query, parameters)

    # Get dialect to determine type mapping strategy
    dialect = connection.dialect

    # Initialize return structures
    columns = {}
    data = []

    if result:
        # Result format: (data_rows, description) tuple from _execute_raw
        if isinstance(result, tuple) and len(result) == 2:
            data_rows, description = result

            # Extract column metadata from cursor description
            # Try result.description first (some drivers attach it to result object)
            if hasattr(result, "description"):
                columns = _extract_column_metadata_from_description(result.description, dialect)  # type: ignore

            # Use tuple description if available (standard format)
            if description:
                columns = _extract_column_metadata_from_description(description, dialect)
            else:
                # Fallback: generate generic column names (col_0, col_1, etc.)
                columns = _create_fallback_columns(data_rows)

            # Materialize cursor results if needed (convert to list)
            if hasattr(data_rows, "fetchall"):
                data_rows = data_rows.fetchall()

            # Convert rows to list of lists for consistent interface
            data = [list(row) for row in data_rows] if data_rows else []

    logger.debug(f"Query executed successfully: {len(columns)} columns, {len(data)} rows")

    # SQLite requires special type inference via query parsing (not from cursor.description)
    # Other databases return reliable type info from cursor.description
    return (_infer_sqlite_column_types_from_query(query, connection) if dialect == SQLDialect.SQLITE else columns), data


def read_sql(
    query: str,
    connection: DatabaseConnection,
    parameters: Optional[Union[Tuple, Dict[str, Any]]] = None,
    dask_partitions: int = 4,
    dask_index_column: Optional[str] = None,
    output_format: Literal["pandas", "polars", "dask", "pyarrow"] = "polars",
    native_fallback: bool = True,
    **kwargs,
) -> pd.DataFrame | dd.DataFrame | pl.DataFrame | pa.Table:  # type: ignore
    """
    Execute a SQL query and return results in the specified dataframe format.

    This function provides a unified interface for executing SQL queries and
    returning results in various dataframe formats. It uses ConnectorX for
    high-performance data loading when available, with automatic fallback to
    native drivers (Pandas, Polars, etc.) if ConnectorX fails.

    The function attempts the following loading strategies in order:
    1. ConnectorX (fastest, Rust-based)
    2. Native driver (format-specific fallback)
    3. Pandas → format conversion (last resort)

    Parameters
    ----------
    query : str
        SQL query string to execute.
    connection : DatabaseConnection
        Active database connection instance.
    parameters : tuple or dict, optional
        Query parameters. Use tuple for positional parameters or dict for
        named parameters. Default is None.
    dask_partitions : int, optional
        Number of partitions for Dask dataframes. Only used when
        output_format='dask'. Default is 4.
    dask_index_column : str, optional
        Column to use as index for Dask dataframes. Required when
        output_format='dask'. Default is None.
    output_format : {'pandas', 'polars', 'dask', 'pyarrow'}, optional
        Desired output format for the dataframe. Default is 'polars'.
    native_fallback : bool, optional
        Whether to fall back to native drivers if ConnectorX fails.
        If False, raises exception on ConnectorX failure. Default is True.
    **kwargs
        Additional keyword arguments passed to the underlying read function
        (e.g., parse_dates, dtype, chunksize for pandas).

    Returns
    -------
    pd.DataFrame or dd.DataFrame or pl.DataFrame or pa.Table
        Query results in the requested dataframe format.

    Raises
    ------
    AssertionError
        If output_format is not one of the supported formats.
    AssertionError
        If dask_index_column is not provided when output_format='dask'.
    ImportError
        If the requested output format library is not installed.
    ConnectionError
        If database connection fails.
    QueryExecutionError
        If query execution fails in all attempted methods.

    Examples
    --------
    >>> from connections import DatabaseConnection
    >>> from download.read_sql import read_sql
    >>>
    >>> # PostgreSQL with Polars (default, highest performance)
    >>> conn = DatabaseConnection(dialect="postgres", host="localhost", database="mydb")
    >>> df = read_sql("SELECT * FROM users WHERE age > 18", conn)
    >>> print(type(df))
    <class 'polars.dataframe.frame.DataFrame'>
    >>>
    >>> # MySQL with Pandas and parameters
    >>> conn = DatabaseConnection(dialect="mysql", host="localhost", database="mydb")
    >>> df = read_sql(
    ...     "SELECT id, name, salary FROM employees WHERE salary > %s",
    ...     conn,
    ...     parameters=(50000,),
    ...     output_format='pandas'
    ... )
    >>> print(df.head())
    >>>
    >>> # Dask for large datasets with partitioning
    >>> df = read_sql(
    ...     "SELECT * FROM large_table",
    ...     conn,
    ...     output_format='dask',
    ...     dask_partitions=8,
    ...     dask_index_column='id'
    ... )
    >>> print(df.compute().head())

    Notes
    -----
    - ConnectorX provides the best performance but may not support all SQL
      dialects or features. The function automatically falls back to native
      drivers when needed.
    - For Dask output, an index column must be specified for proper partitioning.
    - Polars and PyArrow are optimized for columnar operations and provide
      better performance than Pandas for large datasets.
    - When using parameters, ensure the parameter style matches your database
      dialect (?, %s, :name, etc.).

    See Also
    --------
    execute_query_with_metadata : Lower-level query execution with metadata.
    DatabaseConnection.read_sql_connector_x : ConnectorX-based loading.
    """
    # Validate output format early to fail fast
    assert output_format in [
        "pandas",
        "polars",
        "dask",
        "pyarrow",
    ], "output_format must be one of 'pandas', 'polars', 'dask', or 'pyarrow'"

    # Primary strategy: Use ConnectorX for maximum performance (Rust-based)
    try:
        # ConnectorX uses 'arrow' instead of 'pyarrow' for PyArrow tables
        cx_return_type = "arrow" if output_format == "pyarrow" else output_format
        return connection.read_sql_connector_x(query=query, return_type=cx_return_type, **kwargs)  # type: ignore [The literal accepts a larger set of values for this function then this wrapper function permits.]
    except (Exception, BaseException) as e:
        logger.error(f"Error reading SQL with ConnectorX: {e}")

        # Fallback strategy: Use native drivers if ConnectorX fails
        if native_fallback:
            logger.debug("Falling back to native driver implementation")

            # Pandas fallback: Use SQLAlchemy connection
            if output_format == "pandas":
                try:
                    return pd.read_sql(query, connection.to_sqlalchemy(), params=parameters, **kwargs)
                except (Exception, BaseException) as e2:
                    logger.error(f"Error reading SQL with Pandas fallback: {e2}")
                    raise e2

            # Dask fallback: Requires index column for partitioning
            elif output_format == "dask":
                assert isinstance(dask_index_column, str), "dask_index_column must be a string when using Dask"
                try:
                    return dd.read_sql_table(
                        query,
                        connection.to_sqlalchemy(),
                        index_col=dask_index_column,
                        npartitions=dask_partitions,
                        params=parameters,
                        **kwargs,
                    )
                except (Exception, BaseException) as e2:
                    logger.error(f"Error reading SQL with Dask fallback: {e2}")
                    raise e2

            # Polars fallback: Try ConnectorX URI first, then SQLAlchemy
            elif output_format == "polars":
                try:
                    # Attempt Polars native ConnectorX support
                    return pl.read_database_uri(query, uri=connection.connectorx_uri, engine="connectorx", **kwargs)
                except (Exception, BaseException) as e2:
                    logger.error(f"Error reading SQL with Polars ConnectorX fallback: {e2}")
                    try:
                        # Final fallback: Polars SQLAlchemy support
                        logger.debug("Trying Polars SQLAlchemy fallback")
                        return pl.read_database(query, connection=connection.to_sqlalchemy(), **kwargs)
                    except (Exception, BaseException) as e3:
                        logger.error(f"Error reading SQL with Polars SQLAlchemy fallback: {e3}")
                        raise e3

            # PyArrow fallback: Load via Pandas then convert
            elif output_format == "pyarrow":
                try:
                    # Load data via Pandas first (widely compatible)
                    df = pd.read_sql(query, connection.to_sqlalchemy(), params=parameters, **kwargs)
                    # Convert to PyArrow Table format
                    return pa.Table.from_pandas(df)
                except (Exception, BaseException) as e2:
                    logger.error(f"Error reading SQL with PyArrow fallback: {e2}")
                    raise e2
        else:
            # Native fallback disabled, propagate ConnectorX error
            raise e
