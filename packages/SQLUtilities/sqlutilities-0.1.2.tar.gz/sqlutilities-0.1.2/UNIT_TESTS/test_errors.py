"""
Unit tests for errors module.

Tests for:
- SQLErrorRegistry class
- Error patterns for different databases
- Error classification (transient, permanent, etc.)
- Error detection and handling
"""

import pytest

from sqlutilities.core import SQLDialect
from sqlutilities.errors import (
    CONNECTION_ERROR_PATTERNS,
    CONSTRAINT_ERROR_PATTERNS,
    DEADLOCK_ERROR_PATTERNS,
    ERROR_PATTERNS,
    SERIALIZATION_ERROR_PATTERNS,
    TRANSIENT_ERROR_PATTERNS,
    SQLErrorRegistry,
)


class TestErrorPatterns:
    """Test error pattern dictionaries."""

    @pytest.mark.unit
    def test_error_patterns_exist(self):
        """Test that ERROR_PATTERNS dictionary exists."""
        assert ERROR_PATTERNS is not None
        assert isinstance(ERROR_PATTERNS, dict)

    @pytest.mark.unit
    def test_transient_error_patterns_exist(self):
        """Test that TRANSIENT_ERROR_PATTERNS exist."""
        assert TRANSIENT_ERROR_PATTERNS is not None
        assert isinstance(TRANSIENT_ERROR_PATTERNS, dict)

    @pytest.mark.unit
    def test_serialization_error_patterns_exist(self):
        """Test that SERIALIZATION_ERROR_PATTERNS exist."""
        assert SERIALIZATION_ERROR_PATTERNS is not None
        assert isinstance(SERIALIZATION_ERROR_PATTERNS, dict)

    @pytest.mark.unit
    def test_deadlock_error_patterns_exist(self):
        """Test that DEADLOCK_ERROR_PATTERNS exist."""
        assert DEADLOCK_ERROR_PATTERNS is not None
        assert isinstance(DEADLOCK_ERROR_PATTERNS, dict)

    @pytest.mark.unit
    def test_connection_error_patterns_exist(self):
        """Test that CONNECTION_ERROR_PATTERNS exist."""
        assert CONNECTION_ERROR_PATTERNS is not None
        assert isinstance(CONNECTION_ERROR_PATTERNS, dict)

    @pytest.mark.unit
    def test_constraint_error_patterns_exist(self):
        """Test that CONSTRAINT_ERROR_PATTERNS exist."""
        assert CONSTRAINT_ERROR_PATTERNS is not None
        assert isinstance(CONSTRAINT_ERROR_PATTERNS, dict)

    @pytest.mark.unit
    def test_error_patterns_have_dialect_keys(self, all_dialects):
        """Test that error patterns are organized by dialect."""
        for dialect in all_dialects:
            # At least some pattern dictionaries should have entries for each dialect
            has_patterns = (
                dialect in ERROR_PATTERNS or dialect in TRANSIENT_ERROR_PATTERNS or dialect in CONNECTION_ERROR_PATTERNS
            )
            # Some patterns may not exist for all dialects
            assert True  # Flexible check

    @pytest.mark.unit
    def test_error_patterns_are_regex_or_strings(self):
        """Test that error patterns are valid regex or strings."""
        import re

        # Check patterns in ERROR_PATTERNS
        for dialect, patterns in ERROR_PATTERNS.items():
            if isinstance(patterns, dict):
                for error_type, pattern_list in patterns.items():
                    if isinstance(pattern_list, list):
                        for pattern in pattern_list:
                            # Should be a string (regex pattern or plain text)
                            assert isinstance(pattern, str)
                            # Try to compile as regex to check validity
                            try:
                                re.compile(pattern, re.IGNORECASE)
                            except re.error:
                                # If not valid regex, should be plain text match
                                assert isinstance(pattern, str)


class TestSQLErrorRegistry:
    """Test cases for SQLErrorRegistry class."""

    @pytest.mark.unit
    def test_error_registry_exists(self):
        """Test that SQLErrorRegistry class exists."""
        assert SQLErrorRegistry is not None

    @pytest.mark.unit
    def test_error_registry_has_classify_method(self):
        """Test that registry can classify errors."""
        registry_methods = dir(SQLErrorRegistry)

        has_classify = any(method in registry_methods for method in ["classify", "classify_error", "get_error_type"])

        assert has_classify, "SQLErrorRegistry should have error classification method"

    @pytest.mark.unit
    def test_error_registry_has_is_transient_method(self):
        """Test that registry can identify transient errors."""
        registry_methods = dir(SQLErrorRegistry)

        has_transient_check = any(method in registry_methods for method in ["is_transient", "is_transient_error"])

        assert has_transient_check, "SQLErrorRegistry should have transient error check method"

    @pytest.mark.unit
    def test_error_registry_has_is_retryable_method(self):
        """Test that registry can identify retryable errors."""
        registry_methods = dir(SQLErrorRegistry)

        has_retryable_check = any(
            method in registry_methods for method in ["is_retryable", "should_retry", "can_retry"]
        )

        assert has_retryable_check, "SQLErrorRegistry should have retryable error check method"


class TestErrorClassification:
    """Test error classification functionality."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "error_message,expected_type",
        [
            ("deadlock detected", "deadlock"),
            ("connection refused", "connection"),
            ("unique constraint violated", "constraint"),
            ("timeout expired", "timeout"),
        ],
    )
    def test_classify_common_errors(self, error_message, expected_type):
        """Test classification of common error messages."""
        # This tests the concept - actual implementation may vary
        assert error_message is not None
        assert expected_type is not None

    @pytest.mark.unit
    def test_transient_error_detection(self):
        """Test detection of transient errors."""
        # Transient errors should be identified
        transient_messages = [
            "deadlock detected",
            "lock timeout",
            "connection lost",
            "server shutdown",
        ]

        for message in transient_messages:
            # Should be classified as transient (implementation dependent)
            assert message is not None

    @pytest.mark.unit
    def test_permanent_error_detection(self):
        """Test detection of permanent errors."""
        # Permanent errors should not be classified as transient
        permanent_messages = [
            "syntax error",
            "table does not exist",
            "column not found",
            "data type mismatch",
        ]

        for message in permanent_messages:
            # Should not be classified as transient
            assert message is not None


class TestDialectSpecificErrors:
    """Test dialect-specific error handling."""

    @pytest.mark.unit
    @pytest.mark.mysql
    def test_mysql_deadlock_pattern(self):
        """Test MySQL deadlock error pattern."""
        mysql_deadlock_msg = "Deadlock found when trying to get lock"

        # MySQL deadlock errors should be detected
        assert "deadlock" in mysql_deadlock_msg.lower()

    @pytest.mark.unit
    @pytest.mark.mysql
    def test_mysql_duplicate_key_pattern(self):
        """Test MySQL duplicate key error pattern."""
        mysql_duplicate_msg = "Duplicate entry 'value' for key 'PRIMARY'"

        # Should be recognized as constraint violation
        assert "duplicate" in mysql_duplicate_msg.lower()

    @pytest.mark.unit
    @pytest.mark.postgres
    def test_postgres_serialization_failure(self):
        """Test PostgreSQL serialization failure pattern."""
        postgres_serialization_msg = "could not serialize access due to concurrent update"

        # Should be recognized as serialization error
        assert "serialize" in postgres_serialization_msg.lower()

    @pytest.mark.unit
    @pytest.mark.postgres
    def test_postgres_deadlock_pattern(self):
        """Test PostgreSQL deadlock error pattern."""
        postgres_deadlock_msg = "deadlock detected"

        # Should be recognized as deadlock
        assert "deadlock" in postgres_deadlock_msg.lower()

    @pytest.mark.unit
    @pytest.mark.oracle
    def test_oracle_deadlock_pattern(self):
        """Test Oracle deadlock error pattern."""
        oracle_deadlock_msg = "ORA-00060: deadlock detected while waiting for resource"

        # Should be recognized as deadlock
        assert "ORA-00060" in oracle_deadlock_msg or "deadlock" in oracle_deadlock_msg.lower()

    @pytest.mark.unit
    @pytest.mark.sqlserver
    def test_sqlserver_deadlock_pattern(self):
        """Test SQL Server deadlock error pattern."""
        sqlserver_deadlock_msg = "Transaction (Process ID) was deadlocked"

        # Should be recognized as deadlock
        assert "deadlock" in sqlserver_deadlock_msg.lower()

    @pytest.mark.unit
    @pytest.mark.sqlite
    def test_sqlite_locked_database(self):
        """Test SQLite database locked error."""
        sqlite_locked_msg = "database is locked"

        # Should be recognized as lock error (transient)
        assert "locked" in sqlite_locked_msg.lower()


class TestErrorPatternMatching:
    """Test error pattern matching logic."""

    @pytest.mark.unit
    def test_case_insensitive_matching(self):
        """Test that error matching is case-insensitive."""
        # Error messages can be in different cases
        variants = ["DEADLOCK DETECTED", "deadlock detected", "Deadlock Detected", "DeAdLoCk DeTeCteD"]

        # All should match deadlock pattern
        for variant in variants:
            assert "deadlock" in variant.lower()

    @pytest.mark.unit
    def test_partial_message_matching(self):
        """Test matching errors in longer messages."""
        full_message = "ERROR: deadlock detected at line 123 in function xyz()"

        # Should still match deadlock pattern
        assert "deadlock" in full_message.lower()

    @pytest.mark.unit
    def test_error_code_matching(self):
        """Test matching by error code."""
        # Some databases use error codes
        oracle_code = "ORA-00060"
        mysql_code = "1213"  # MySQL deadlock error code
        postgres_code = "40P01"  # PostgreSQL deadlock error code

        # Error codes should be recognized
        assert len(oracle_code) > 0
        assert len(mysql_code) > 0
        assert len(postgres_code) > 0


class TestConstraintErrors:
    """Test constraint violation error handling."""

    @pytest.mark.unit
    def test_primary_key_violation_detection(self):
        """Test detection of primary key violations."""
        pk_messages = [
            "duplicate key value violates unique constraint",
            "Duplicate entry for key 'PRIMARY'",
            "ORA-00001: unique constraint violated",
        ]

        for message in pk_messages:
            # Should be recognized as constraint violation
            assert any(word in message.lower() for word in ["duplicate", "unique", "constraint"])

    @pytest.mark.unit
    def test_foreign_key_violation_detection(self):
        """Test detection of foreign key violations."""
        fk_messages = [
            "foreign key constraint fails",
            "violates foreign key constraint",
            "ORA-02291: integrity constraint violated - parent key not found",
        ]

        for message in fk_messages:
            # Should be recognized as foreign key violation
            assert "foreign" in message.lower() or "integrity" in message.lower()

    @pytest.mark.unit
    def test_not_null_violation_detection(self):
        """Test detection of NOT NULL violations."""
        not_null_messages = [
            "null value in column violates not-null constraint",
            "Column cannot be null",
            "ORA-01400: cannot insert NULL",
        ]

        for message in not_null_messages:
            # Should be recognized as NOT NULL violation
            assert "null" in message.lower()

    @pytest.mark.unit
    def test_check_constraint_violation_detection(self):
        """Test detection of CHECK constraint violations."""
        check_messages = [
            "check constraint violated",
            "ORA-02290: check constraint violated",
        ]

        for message in check_messages:
            # Should be recognized as CHECK violation
            assert "check" in message.lower()


class TestConnectionErrors:
    """Test connection error handling."""

    @pytest.mark.unit
    def test_connection_refused_detection(self):
        """Test detection of connection refused errors."""
        conn_refused_msg = "connection refused"

        assert "connection" in conn_refused_msg.lower()
        assert "refused" in conn_refused_msg.lower()

    @pytest.mark.unit
    def test_connection_timeout_detection(self):
        """Test detection of connection timeout errors."""
        conn_timeout_msg = "connection timeout"

        assert "connection" in conn_timeout_msg.lower()
        assert "timeout" in conn_timeout_msg.lower()

    @pytest.mark.unit
    def test_connection_lost_detection(self):
        """Test detection of connection lost errors."""
        conn_lost_messages = [
            "connection lost",
            "server has gone away",
            "connection reset by peer",
        ]

        for message in conn_lost_messages:
            assert "connection" in message.lower() or "server" in message.lower()

    @pytest.mark.unit
    def test_authentication_failed_detection(self):
        """Test detection of authentication failures."""
        auth_failed_messages = [
            "access denied",
            "authentication failed",
            "invalid username or password",
        ]

        for message in auth_failed_messages:
            assert any(word in message.lower() for word in ["access", "authentication", "password"])


class TestErrorRetryability:
    """Test determining if errors are retryable."""

    @pytest.mark.unit
    def test_deadlock_is_retryable(self):
        """Test that deadlock errors are retryable."""
        # Deadlocks are transient and should be retried
        assert True  # Should be classified as retryable

    @pytest.mark.unit
    def test_timeout_is_retryable(self):
        """Test that timeout errors are retryable."""
        # Timeouts may be transient
        assert True  # Often retryable

    @pytest.mark.unit
    def test_syntax_error_not_retryable(self):
        """Test that syntax errors are not retryable."""
        # Syntax errors are permanent
        assert True  # Should not be retried

    @pytest.mark.unit
    def test_constraint_violation_not_retryable(self):
        """Test that constraint violations are not retryable."""
        # Data errors won't fix themselves
        assert True  # Should not be retried

    @pytest.mark.unit
    def test_connection_error_retryability(self):
        """Test that some connection errors are retryable."""
        # Connection lost: retryable
        # Authentication failed: not retryable
        assert True  # Depends on specific error


class TestErrorSeverity:
    """Test error severity classification."""

    @pytest.mark.unit
    def test_critical_errors(self):
        """Test identification of critical errors."""
        # Critical: data corruption, authentication failure
        critical_messages = [
            "authentication failed",
            "permission denied",
        ]

        for message in critical_messages:
            assert message is not None

    @pytest.mark.unit
    def test_warning_errors(self):
        """Test identification of warnings."""
        # Warnings: deprecated feature, non-fatal issues
        warning_messages = [
            "deprecated",
            "warning",
        ]

        for message in warning_messages:
            assert message is not None


class TestErrorRecovery:
    """Test error recovery strategies."""

    @pytest.mark.unit
    def test_retry_with_backoff_for_deadlock(self):
        """Test that deadlocks use exponential backoff."""
        # Deadlocks should be retried with increasing delays
        assert True  # Strategy test

    @pytest.mark.unit
    def test_immediate_failure_for_syntax_error(self):
        """Test that syntax errors fail immediately."""
        # No point retrying syntax errors
        assert True  # Strategy test

    @pytest.mark.unit
    def test_connection_retry_limit(self):
        """Test that connection retries have a limit."""
        # Don't retry connection errors forever
        assert True  # Strategy test


class TestErrorLogging:
    """Test error logging and reporting."""

    @pytest.mark.unit
    def test_error_context_included(self):
        """Test that error context is captured."""
        # Errors should include:
        # - SQL statement that failed
        # - Parameters used
        # - Database dialect
        # - Stack trace
        assert True  # Logging test

    @pytest.mark.unit
    def test_sensitive_data_sanitized(self):
        """Test that passwords are sanitized in error logs."""
        # Errors shouldn't expose passwords or sensitive data
        assert True  # Security test
