"""
Transaction management module.

This module provides comprehensive transaction management with automatic retry logic,
error classification, and performance monitoring across all supported SQL dialects.

The module includes:
- Transaction configuration and isolation level management
- Performance metrics collection and reporting
- Robust transaction execution with automatic retry
- Error classification and intelligent retry policies
- Deadlock detection and resolution
- Batch and bulk operation optimizations

Classes
-------
TransactionConfig
    Configuration for transaction execution including retry policies
TransactionMetrics
    Performance metrics for transaction execution
IsolationLevel
    SQL transaction isolation levels
TransactionState
    Transaction state enumeration
RobustTransaction
    Main transaction manager with retry logic and error handling

Examples
--------
Basic transaction usage:
    >>> from sqlutils.transactions import RobustTransaction
    >>> from sqlutils.connections import DatabaseConnection
    >>> conn = DatabaseConnection('postgresql')
    >>> with RobustTransaction(conn) as tx:
    ...     tx.execute("INSERT INTO users VALUES (?, ?)", (1, 'Alice'))
    ...     tx.execute("UPDATE accounts SET balance = balance - 100")

Custom transaction configuration:
    >>> from sqlutils.transactions import TransactionConfig, IsolationLevel
    >>> config = TransactionConfig(
    ...     max_retries=5,
    ...     isolation_level=IsolationLevel.SERIALIZABLE,
    ...     enable_deadlock_detection=True
    ... )
    >>> with RobustTransaction(conn, config=config) as tx:
    ...     tx.execute("SELECT * FROM accounts FOR UPDATE")

Bulk insert with automatic batching:
    >>> data = [(i, f'user{i}') for i in range(10000)]
    >>> with RobustTransaction(conn) as tx:
    ...     tx.bulk_insert("INSERT INTO users VALUES (?, ?)", data, chunk_size=1000)

Notes
-----
All transactions are ACID-compliant and support automatic rollback on errors.
The RobustTransaction class automatically retries transient errors like deadlocks.
"""

from .config import IsolationLevel, TransactionConfig, TransactionMetrics, TransactionState
from .transaction import RobustTransaction

__all__ = [
    "TransactionConfig",
    "TransactionMetrics",
    "IsolationLevel",
    "TransactionState",
    "RobustTransaction",
]
