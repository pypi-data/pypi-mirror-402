"""
Validation module for SQL identifiers and names.

This module provides comprehensive validation and normalization of SQL identifiers
(table names, column names, schema names, etc.) across all supported SQL dialects.

The module handles:
- Reserved word checking and handling
- Identifier length validation
- Character validation (allowed characters, special characters)
- Case sensitivity and normalization
- Quoting/encapsulation rules
- Dialect-specific identifier rules
- Automatic correction and normalization

Classes
-------
SQL_DIALECT_REGISTRY
    Static registry for SQL dialect-specific identifier validation rules

Examples
--------
Validate an identifier:
    >>> from sqlutils.validation import SQL_DIALECT_REGISTRY
    >>> from sqlutils.core import SQLDialect, DatabaseObjectType
    >>> result = SQL_DIALECT_REGISTRY.validate_identifier(
    ...     dialect=SQLDialect.POSTGRESQL,
    ...     identifier='user_table',
    ...     context=DatabaseObjectType.TABLE,
    ...     correction_method='normalize'
    ... )
    >>> print(result['final'])  # Normalized identifier
    >>> print(result['is_reserved'])  # False
    >>> print(result['correction_applied'])  # 'none' or correction type

Check for reserved words:
    >>> is_reserved = SQL_DIALECT_REGISTRY.is_reserved_word(
    ...     dialect=SQLDialect.MYSQL,
    ...     context=DatabaseObjectType.COLUMN,
    ...     identifier='select'
    ... )
    >>> print(is_reserved)  # True

Encapsulate reserved word:
    >>> result = SQL_DIALECT_REGISTRY.validate_identifier(
    ...     dialect=SQLDialect.POSTGRESQL,
    ...     identifier='order',
    ...     context=DatabaseObjectType.TABLE,
    ...     correction_method='encapsulate'
    ... )
    >>> print(result['final'])  # "order" (with quotes)

Get available drivers:
    >>> drivers = SQL_DIALECT_REGISTRY.get_best_available_driver(SQLDialect.POSTGRESQL)
    >>> print(drivers['name'])  # 'psycopg2' or 'psycopg3'

Notes
-----
The validation module automatically applies dialect-specific rules including:
- Identifier length limits (e.g., Oracle 30 chars, PostgreSQL 63 chars)
- Reserved word lists (dialect and context-specific)
- Case sensitivity rules (Oracle uppercase, PostgreSQL lowercase)
- Character restrictions (alphanumeric, underscores, etc.)
- Quoting requirements for special characters or reserved words
"""

from .identifiers import SQL_DIALECT_REGISTRY

__all__ = [
    "SQL_DIALECT_REGISTRY",
]
