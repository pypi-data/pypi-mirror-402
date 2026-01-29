"""
Transaction Configuration

This module contains configuration classes and enums for transaction management.
- ConnectionState: Enum for connection states
- TransactionState: Enum for transaction states
- IsolationLevel: Enum for SQL isolation levels
- TransactionConfig: Configuration dataclass
- TransactionMetrics: Metrics dataclass
- TransactionException: Custom exception class

Author: DataScience ToolBox
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ConnectionState(Enum):
    """
    Enumeration of possible connection states.

    Attributes
    ----------
    DISCONNECTED : str
        Connection is not established
    CONNECTED : str
        Connection is active and ready
    ERROR : str
        Connection encountered an error
    CONNECTING : str
        Connection attempt in progress
    """

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ERROR = "error"
    CONNECTING = "connecting"


class TransactionState(Enum):
    """
    Transaction state enumeration.

    Attributes
    ----------
    IDLE : str
        Transaction has not been started
    PENDING : str
        Alias for IDLE - transaction not yet started
    ACTIVE : str
        Transaction is currently in progress
    COMMITTED : str
        Transaction completed successfully
    ROLLED_BACK : str
        Transaction was rolled back
    FAILED : str
        Transaction encountered an error
    RETRYING : str
        Transaction is being retried after error
    """

    IDLE = "idle"
    PENDING = "idle"  # Alias for IDLE - transaction not yet started
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    RETRYING = "retrying"


class IsolationLevel(Enum):
    """
    SQL transaction isolation levels.

    Defines the standard SQL isolation levels that control how transaction
    integrity is visible to other transactions and the level of locking.

    Attributes
    ----------
    READ_UNCOMMITTED : str
        Lowest isolation level, allows dirty reads
    READ_COMMITTED : str
        Prevents dirty reads, default for most databases
    REPEATABLE_READ : str
        Prevents non-repeatable reads
    SERIALIZABLE : str
        Highest isolation level, prevents phantom reads
    SNAPSHOT : str
        SQL Server-specific isolation level using row versioning
    READ_COMMITTED_SNAPSHOT : str
        SQL Server-specific isolation using snapshot for read committed

    Notes
    -----
    Not all isolation levels are supported by all database systems.
    The library automatically maps to the closest supported level.
    """

    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"
    SNAPSHOT = "SNAPSHOT"  # SQL Server specific
    READ_COMMITTED_SNAPSHOT = "READ_COMMITTED_SNAPSHOT"  # SQL Server specific


@dataclass
class TransactionConfig:
    """
    Configuration for transaction execution.

    Parameters
    ----------
    max_retries : int, default=3
        Maximum number of retry attempts for failed transactions
    base_retry_delay : float, default=0.1
        Base delay in seconds before retrying (exponential backoff basis)
    max_retry_delay : float, default=30.0
        Maximum retry delay in seconds (caps exponential backoff)
    jitter_factor : float, default=0.1
        Random jitter factor (0.0 to 1.0) to prevent thundering herd
    isolation_level : IsolationLevel, optional
        SQL transaction isolation level to use
    timeout : float, optional
        Transaction timeout in seconds (None for no timeout)
    enable_deadlock_detection : bool, default=True
        Whether to detect and retry deadlocks automatically
    enable_connection_pooling : bool, default=True
        Whether to use connection pooling when available
    batch_size : int, optional
        Default batch size for bulk operations (None for auto-detect)
    enable_performance_monitoring : bool, default=True
        Whether to collect and log performance metrics

    Examples
    --------
    Default configuration:
        >>> config = TransactionConfig()

    High-reliability configuration:
        >>> config = TransactionConfig(
        ...     max_retries=10,
        ...     isolation_level=IsolationLevel.SERIALIZABLE,
        ...     timeout=300.0
        ... )

    Fast-fail configuration:
        >>> config = TransactionConfig(
        ...     max_retries=0,
        ...     enable_deadlock_detection=False
        ... )
    """

    max_retries: int = 3
    base_retry_delay: float = 0.1  # Base delay in seconds
    max_retry_delay: float = 30.0  # Maximum retry delay
    jitter_factor: float = 0.1  # Random jitter factor (0.0 to 1.0)
    isolation_level: Optional[IsolationLevel] = None
    timeout: Optional[float] = None  # Transaction timeout in seconds
    enable_deadlock_detection: bool = True
    enable_connection_pooling: bool = True
    batch_size: Optional[int] = None  # For batch operations
    enable_performance_monitoring: bool = True


@dataclass
class TransactionMetrics:
    """
    Transaction performance metrics.

    Attributes
    ----------
    start_time : float
        Transaction start time (Unix timestamp)
    end_time : float, optional
        Transaction end time (Unix timestamp)
    duration : float, optional
        Total transaction duration in seconds
    retry_count : int, default=0
        Number of retry attempts made
    error_count : int, default=0
        Number of errors encountered
    queries_executed : int, default=0
        Total number of queries executed
    rows_affected : int, default=0
        Total number of rows affected by queries
    connection_reused : bool, default=False
        Whether an existing connection was reused
    isolation_level_used : str, optional
        Isolation level that was actually used
    driver_used : str, optional
        Database driver that was used

    Examples
    --------
    Accessing metrics after transaction:
        >>> with RobustTransaction(conn) as tx:
        ...     tx.execute("INSERT INTO users VALUES (?, ?)", (1, 'Alice'))
        >>> metrics = tx.get_metrics()
        >>> print(f"Duration: {metrics.duration:.3f}s")
        >>> print(f"Rows affected: {metrics.rows_affected}")
    """

    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    retry_count: int = 0
    error_count: int = 0
    queries_executed: int = 0
    rows_affected: int = 0
    connection_reused: bool = False
    isolation_level_used: Optional[str] = None
    driver_used: Optional[str] = None


class TransactionException(Exception):
    """
    Base exception for transaction-related errors.

    This exception wraps database errors and provides additional context
    about the error category and the original exception that was raised.

    Parameters
    ----------
    message : str
        Human-readable error message
    original_error : Exception, optional
        The original exception that was raised
    error_category : str, optional
        Category of the error (e.g., 'connection', 'deadlock', 'timeout')

    Attributes
    ----------
    original_error : Exception or None
        The original exception that caused this error
    error_category : str or None
        Classification of the error type

    Examples
    --------
    Catching transaction errors:
        >>> try:
        ...     with RobustTransaction(conn) as tx:
        ...         tx.execute("INVALID SQL")
        ... except TransactionException as e:
        ...     print(f"Error category: {e.error_category}")
        ...     print(f"Original error: {e.original_error}")
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None, error_category: Optional[str] = None):
        super().__init__(message)
        self.original_error = original_error
        self.error_category = error_category
