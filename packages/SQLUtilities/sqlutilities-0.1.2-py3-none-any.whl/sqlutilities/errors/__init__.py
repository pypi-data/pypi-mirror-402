"""
Error handling module for SQL error patterns and registry.

This module provides comprehensive error handling for SQL operations across
all supported database dialects. It includes error pattern matching, error
classification, and intelligent retry policy determination.

The module includes:
- Error pattern definitions for all major database systems
- Error category classification (connection, deadlock, constraint, etc.)
- Retry policy determination (retryable, non-retryable, conditional)
- Dialect and driver-specific error pattern matching
- Comprehensive error registry with pattern lookup

Classes
-------
ErrorCategory
    High-level categorization of SQL errors
RetryPolicy
    Retry policy enumeration for different error types
ErrorPattern
    Dataclass representing an error pattern with matching criteria
SQLErrorRegistry
    Main registry for error classification and handling

Examples
--------
Classify an error:
    >>> from sqlutils.errors import SQLErrorRegistry
    >>> from sqlutils.core import SQLDialect
    >>> registry = SQLErrorRegistry()
    >>> error = Exception("ORA-00060: deadlock detected")
    >>> pattern = registry.classify_error(SQLDialect.ORACLE, 'oracledb', error)
    >>> print(pattern.category)  # ErrorCategory.CONCURRENCY
    >>> print(pattern.retry_policy)  # RetryPolicy.RETRYABLE

Check if error is retryable:
    >>> is_retryable = registry.is_retryable(SQLDialect.POSTGRESQL, 'psycopg2', error)
    >>> if is_retryable:
    ...     delay = registry.get_retry_delay(SQLDialect.POSTGRESQL, 'psycopg2', error)
    ...     time.sleep(delay)

Get suggested action:
    >>> action = registry.get_suggested_action(SQLDialect.MYSQL, 'mysql.connector', error)
    >>> print(action)

Notes
-----
The error registry is automatically initialized with patterns for all supported
databases. Custom patterns can be added through the registry interface.
Error patterns include database error codes, regex patterns, and message keywords.
"""

from .patterns import ErrorCategory, RetryPolicy
from .registry import SQLErrorRegistry

# For backwards compatibility with tests - these will be empty dicts for now
ERROR_PATTERNS = {}
TRANSIENT_ERROR_PATTERNS = {}
SERIALIZATION_ERROR_PATTERNS = {}
DEADLOCK_ERROR_PATTERNS = {}
CONNECTION_ERROR_PATTERNS = {}
CONSTRAINT_ERROR_PATTERNS = {}

__all__ = [
    "ErrorCategory",
    "RetryPolicy",
    "ERROR_PATTERNS",
    "TRANSIENT_ERROR_PATTERNS",
    "SERIALIZATION_ERROR_PATTERNS",
    "DEADLOCK_ERROR_PATTERNS",
    "CONNECTION_ERROR_PATTERNS",
    "CONSTRAINT_ERROR_PATTERNS",
    "SQLErrorRegistry",
]
