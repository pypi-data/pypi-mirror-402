"""
Table management module for table definitions and operations.

This module provides comprehensive table management capabilities including
schema definition, DDL generation, and table operations across all supported
SQL dialects.

The module includes:
- Table component type definitions (columns, constraints, indexes)
- Table operation management (create, drop, alter, recreate)
- Column definitions with full attribute support
- Constraint definitions (primary key, foreign key, unique, check)
- Index definitions (unique, clustered, partial)
- Cross-dialect DDL generation

Classes
-------
TableComponentType
    Enumeration of table component types
TableOperation
    Enumeration of table operations
ColumnDefinition
    Comprehensive column definition dataclass
ConstraintDefinition
    Table constraint definition dataclass
IndexDefinition
    Index definition dataclass
TableDefinition
    Complete table definition dataclass
SQL_TABLE
    Main class for table management and operations

Examples
--------
Define and create a table:
    >>> from sqlutils.tables import SQL_TABLE, ColumnDefinition, COLUMNDTYPE
    >>> from sqlutils.connections import DatabaseConnection
    >>> conn = DatabaseConnection('postgresql')
    >>> table = SQL_TABLE(conn, 'users', schema='public')
    >>> table.add_column('id', COLUMNDTYPE.INTEGER, is_identity=True)
    >>> table.add_column('email', COLUMNDTYPE.VARCHAR, length=255, nullable=False)
    >>> table.add_primary_key_constraint('pk_users', ['id'])
    >>> table.add_unique_constraint('uk_email', ['email'])
    >>> table.create_table()

Create table from DataFrame definition:
    >>> import pandas as pd
    >>> df = pd.DataFrame([
    ...     {'FieldName': 'id', 'Datatype': 'INTEGER', 'isPrimaryKey': True},
    ...     {'FieldName': 'name', 'Datatype': 'VARCHAR(100)', 'isRequired': True}
    ... ])
    >>> table = SQL_TABLE(conn, 'users')
    >>> table.create_table_from_dataframe(df)

Generate SQL without executing:
    >>> sql = table.create_table(dry_run=True)
    >>> print(sql)

Notes
-----
All table operations are dialect-aware and generate appropriate SQL for the
target database system. The library handles identifier quoting, type mapping,
and dialect-specific syntax automatically.
"""

from .definitions import (
    ColumnDefinition,
    ConstraintDefinition,
    IndexDefinition,
    TableComponentType,
    TableDefinition,
    TableOperation,
)
from .table import SQL_TABLE

__all__ = [
    "TableComponentType",
    "TableOperation",
    "ColumnDefinition",
    "ConstraintDefinition",
    "IndexDefinition",
    "TableDefinition",
    "SQL_TABLE",
]
