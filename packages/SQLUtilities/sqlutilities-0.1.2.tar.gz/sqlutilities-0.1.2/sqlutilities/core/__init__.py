"""
Core Module for SQL Utilities.

This module provides the fundamental building blocks for working with SQL
databases across multiple dialects. It exports core enumerations and type
definitions used throughout the SQL utilities package.

The core module consists of:
- DatabaseObjectType: Enumeration of database object types (tables, views,
  indexes, constraints, etc.) across all major SQL dialects
- SQLDialect: Enumeration of supported SQL dialects with complete identifier
  validation rules, quoting conventions, and syntax support
- COLUMNDTYPE: Comprehensive enumeration of SQL column data types with
  dialect-specific metadata and cross-dialect compatibility
- Column_Type: Named tuple representing a resolved column data type with
  all dialect-specific properties
- TemporalPrecision: Helper class for temporal type precision calculations
  and byte size determinations

These exports form the foundation for SQL identifier validation, type
conversion, and dialect-specific query generation throughout the package.

Examples
--------
>>> from core import DatabaseObjectType, SQLDialect, COLUMNDTYPE
>>> obj_type = DatabaseObjectType.TABLE
>>> dialect = SQLDialect.POSTGRES
>>> dtype = COLUMNDTYPE.VARCHAR
>>> print(f"{obj_type.description} in {dialect.description}")
Data storage structure with rows and columns in PostgreSQL
"""

# Import enumerations for database object types and SQL dialects.
from .enums import DatabaseObjectType, SQLDialect

# Import type definitions for column data types and temporal precision.
from .types import COLUMNDTYPE, Column_Type, TemporalPrecision

# Explicitly define public API to control what gets imported with "from core import *".
__all__ = [
    "DatabaseObjectType",  # Enumeration of database object types
    "SQLDialect",  # Enumeration of SQL dialects with identifier rules
    "COLUMNDTYPE",  # Enumeration of column data types
    "Column_Type",  # Named tuple for resolved column types
    "TemporalPrecision",  # Helper class for temporal precision calculations
]
