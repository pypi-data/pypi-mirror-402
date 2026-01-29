"""
Database Drivers Module.

This module provides a comprehensive driver registry and connection factory
for multiple database systems. It handles driver-specific parameter mapping,
connection string construction, and connection management.

Classes
-------
ParameterMapping
    Maps generic parameter names to driver-specific names.
DriverConfig
    Configuration for a specific database driver.
DatabaseDriver
    Enumeration of all supported database drivers with configurations.
DriverConnectionBuilder
    Builds connections using driver-specific configurations.
DatabaseConnectionFactory
    Factory for creating database connections using registered drivers.

Functions
---------
get_driver_config
    Get driver configuration by driver name.

Type Mapping Functions
----------------------
DB_TYPE_MAPPINGS
    Comprehensive mapping of database type codes to Python types.
_map_db_type_to_python
    Map database type code or name to Python type.
_extract_column_metadata_from_description
    Extract standardized column metadata from cursor description.
_infer_sqlite_column_types_from_query
    Infer SQLite column types using query parsing.
_infer_expression_type
    Infer Python type from a SQLGlot expression node.
_create_fallback_columns
    Create generic column metadata when description unavailable.

Examples
--------
>>> from drivers import DatabaseConnectionFactory
>>> params = {
...     'host': 'localhost',
...     'database': 'mydb',
...     'user': 'myuser',
...     'password': 'mypass'
... }
>>> conn = DatabaseConnectionFactory.create_connection('psycopg2', params)

Notes
-----
Supported database systems include:
- SQLite (sqlite3)
- Oracle (oracledb, cx_Oracle)
- PostgreSQL (psycopg2, psycopg3)
- SQL Server (pyodbc, pymssql)
- MySQL (mysqlclient, mysql-connector-python, PyMySQL)
- BigQuery (google-cloud-bigquery, pandas-gbq)
- Redshift (redshift_connector)
- SQLAlchemy (universal ORM)
- ConnectorX (high-performance Rust-based drivers)

The module uses a priority-based driver selection system where:
- Priority 1: ConnectorX drivers (highest performance)
- Priority 7-11: Standard Python database drivers
- Priority 2: SQLAlchemy (universal fallback)
"""

from .builder import DriverConnectionBuilder
from .factory import DatabaseConnectionFactory
from .models import DriverConfig, ParameterMapping
from .registry import DatabaseDriver, get_driver_config
from .type_mapping import (
    DB_TYPE_MAPPINGS,
    _create_fallback_columns,
    _extract_column_metadata_from_description,
    _infer_expression_type,
    _infer_sqlite_column_types_from_query,
    _map_db_type_to_python,
)

__all__ = [
    "ParameterMapping",
    "DriverConfig",
    "DatabaseDriver",
    "get_driver_config",
    "DriverConnectionBuilder",
    "DatabaseConnectionFactory",
    "DB_TYPE_MAPPINGS",
    "_map_db_type_to_python",
    "_extract_column_metadata_from_description",
    "_infer_sqlite_column_types_from_query",
    "_infer_expression_type",
    "_create_fallback_columns",
]
