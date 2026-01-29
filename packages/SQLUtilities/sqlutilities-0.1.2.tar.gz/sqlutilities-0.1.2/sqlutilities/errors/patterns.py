"""
SQL Error Patterns

This module contains error pattern definitions for SQL errors.
- ErrorCategory: Enum for error categories
- RetryPolicy: Enum for retry policies
- ErrorPattern: Dataclass for error patterns

Author: DataScience ToolBox
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Pattern


class ErrorCategory(Enum):
    """High-level categorization of SQL errors."""

    CONNECTION = ("connection", "Connection and network related errors")
    AUTHENTICATION = ("authentication", "Authentication and authorization errors")
    SYNTAX = ("syntax", "SQL syntax and parsing errors")
    CONSTRAINT = ("constraint", "Constraint violation errors")
    TRANSACTION = ("transaction", "Transaction management errors")
    CONCURRENCY = ("concurrency", "Deadlocks and locking errors")
    RESOURCE = ("resource", "Resource exhaustion and limits")
    DATA_INTEGRITY = ("data_integrity", "Data integrity and validation errors")
    SCHEMA = ("schema", "Schema and object existence errors")
    PERMISSION = ("permission", "Permission and privilege errors")
    TIMEOUT = ("timeout", "Query and operation timeout errors")
    STORAGE = ("storage", "Storage space and I/O errors")
    CONFIGURATION = ("configuration", "Database configuration errors")
    DRIVER = ("driver", "Database driver specific errors")
    UNKNOWN = ("unknown", "Unclassified or unexpected errors")

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def description(self) -> str:
        return self.value[1]


class RetryPolicy(Enum):
    """Retry policy for different types of errors."""

    RETRYABLE = ("retryable", "Error can be retried with exponential backoff")
    RETRYABLE_IMMEDIATE = ("retryable_immediate", "Error can be retried immediately")
    RETRYABLE_WITH_DELAY = ("retryable_with_delay", "Error should be retried after a fixed delay")
    NON_RETRYABLE = ("non_retryable", "Error should not be retried")
    CONDITIONAL = ("conditional", "Error retryability depends on context")

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def description(self) -> str:
        return self.value[1]


@dataclass
class ErrorPattern:
    """
    Represents an error pattern with matching criteria and metadata.

    This dataclass defines a comprehensive error pattern that can be used to
    match, classify, and handle database errors across different dialects and
    drivers. It includes matching criteria, categorization, retry policies,
    and suggested remediation actions.

    Parameters
    ----------
    error_code : str or int, optional
        Database-specific error code (e.g., 'ORA-00060', 1205, '40P01')
    pattern : Pattern[str], optional
        Compiled regex pattern for matching error messages
    message_keywords : List[str]
        Keywords to match in error message (case-insensitive)
    category : ErrorCategory
        High-level error category classification
    retry_policy : RetryPolicy
        Policy for determining if/how to retry the operation
    description : str
        Human-readable description of the error
    suggested_action : str
        Recommended action to resolve the error
    retry_delay_seconds : float, optional
        Recommended delay before retry (in seconds)
    max_retries : int, optional
        Maximum number of recommended retry attempts
    severity : str, default='ERROR'
        Error severity level ('ERROR', 'WARNING', 'CRITICAL')

    Examples
    --------
    Define a deadlock error pattern:
        >>> import re
        >>> pattern = ErrorPattern(
        ...     error_code='40P01',
        ...     pattern=re.compile(r'deadlock detected', re.IGNORECASE),
        ...     message_keywords=['deadlock', 'detected'],
        ...     category=ErrorCategory.CONCURRENCY,
        ...     retry_policy=RetryPolicy.RETRYABLE,
        ...     description='Deadlock detected',
        ...     suggested_action='Retry transaction',
        ...     retry_delay_seconds=0.5,
        ...     max_retries=3
        ... )

    Define a connection error pattern:
        >>> pattern = ErrorPattern(
        ...     error_code='08006',
        ...     pattern=re.compile(r'connection.*failed', re.IGNORECASE),
        ...     message_keywords=['connection', 'failed'],
        ...     category=ErrorCategory.CONNECTION,
        ...     retry_policy=RetryPolicy.RETRYABLE_WITH_DELAY,
        ...     description='Connection failure',
        ...     suggested_action='Check network and server status',
        ...     retry_delay_seconds=2.0,
        ...     severity='CRITICAL'
        ... )

    Notes
    -----
    Error patterns support multiple matching strategies:
    - Direct error code matching (most specific)
    - Regex pattern matching on error message
    - Keyword matching in error message (most flexible)

    The matching is performed in order of specificity, with error code
    taking precedence over patterns, which take precedence over keywords.
    """

    error_code: Optional[str | int]  # Database-specific error code
    pattern: Optional[Pattern[str]]  # Regex pattern for error message
    message_keywords: List[str]  # Keywords to match in error message
    category: ErrorCategory
    retry_policy: RetryPolicy
    description: str
    suggested_action: str
    retry_delay_seconds: Optional[float] = None
    max_retries: Optional[int] = None
    severity: str = "ERROR"  # ERROR, WARNING, CRITICAL
