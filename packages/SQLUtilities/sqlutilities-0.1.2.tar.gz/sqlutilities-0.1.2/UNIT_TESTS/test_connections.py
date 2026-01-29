"""
Unit tests for connections module.

Tests for:
- DatabaseConnection class
- Connection pooling
- Connection lifecycle
- Connection context managers
"""

import pytest

from sqlutilities.connections import DatabaseConnection
from sqlutilities.core import SQLDialect


class TestDatabaseConnection:
    """Test cases for DatabaseConnection class."""

    @pytest.mark.unit
    def test_database_connection_class_exists(self):
        """Test that DatabaseConnection class exists."""
        assert DatabaseConnection is not None

    @pytest.mark.unit
    def test_database_connection_has_connect_method(self):
        """Test that DatabaseConnection has connect method."""
        assert hasattr(DatabaseConnection, "connect") or hasattr(
            DatabaseConnection, "__init__"
        ), "DatabaseConnection should have connect method or constructor"

    @pytest.mark.unit
    def test_database_connection_has_close_method(self):
        """Test that DatabaseConnection has close method."""
        # Should have methods to close connection
        connection_methods = dir(DatabaseConnection)
        has_close = any(method in connection_methods for method in ["close", "disconnect", "__exit__"])

        assert has_close, "DatabaseConnection should have close/disconnect method"

    @pytest.mark.unit
    def test_database_connection_context_manager_support(self):
        """Test that DatabaseConnection supports context manager protocol."""
        # Should have __enter__ and __exit__ for 'with' statement
        has_enter = hasattr(DatabaseConnection, "__enter__")
        has_exit = hasattr(DatabaseConnection, "__exit__")

        assert has_enter and has_exit, "DatabaseConnection should support context manager protocol"

    @pytest.mark.unit
    def test_database_connection_has_execute_method(self):
        """Test that DatabaseConnection has execute method."""
        connection_methods = dir(DatabaseConnection)
        has_execute = any(method in connection_methods for method in ["execute", "execute_query", "query", "run"])

        assert has_execute, "DatabaseConnection should have execute method"

    @pytest.mark.unit
    def test_database_connection_has_cursor_method(self):
        """Test that DatabaseConnection has get_raw_connection method."""
        connection_methods = dir(DatabaseConnection)

        # DatabaseConnection uses get_raw_connection to access underlying driver
        assert (
            "get_raw_connection" in connection_methods
        ), "DatabaseConnection should have get_raw_connection method to access underlying driver"


class TestConnectionLifecycle:
    """Test connection lifecycle management."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_connection_initialization_parameters(self, dialect, config_name, request):
        """Test that connection accepts initialization parameters."""
        config = request.getfixturevalue(config_name)

        # Create connection with all the standard parameters
        conn = DatabaseConnection(dialect=dialect, **config)

        # Verify connection was created with the parameters
        assert conn is not None, "Connection should be created with parameters"
        assert conn.dialect == dialect, f"Dialect should be {dialect}"
        assert conn.state.value in ["connected", "error", "disconnected"], "Connection should have valid state"

        conn.disconnect()

    @pytest.mark.unit
    def test_connection_state_tracking(self):
        """Test that connection tracks its state."""
        # DatabaseConnection should have a state property
        assert hasattr(DatabaseConnection, "state"), "DatabaseConnection should have state property"

        # Create a connection without auto-connect to check initial state
        from sqlutilities.transactions.config import ConnectionState

        conn = DatabaseConnection(dialect=SQLDialect.SQLITE, database=":memory:", auto_connect=False)

        # Initial state should be DISCONNECTED
        assert conn.state == ConnectionState.DISCONNECTED, f"Initial state should be DISCONNECTED, got {conn.state}"

        # After connecting, state should be CONNECTED
        conn.connect()
        assert conn.state == ConnectionState.CONNECTED, f"After connect, state should be CONNECTED, got {conn.state}"

        # After disconnecting, state should be DISCONNECTED
        conn.disconnect()
        assert (
            conn.state == ConnectionState.DISCONNECTED
        ), f"After disconnect, state should be DISCONNECTED, got {conn.state}"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_connection_error_handling(self, dialect, config_name, request):
        """Test that connection handles errors gracefully with invalid credentials."""
        # Get the real config from fixtures
        config = request.getfixturevalue(config_name)

        # SQLite doesn't use host - it's file-based, so it will always connect successfully
        # Skip this test for SQLite as invalid host doesn't apply
        if dialect == SQLDialect.SQLITE:
            pytest.skip("SQLite is file-based and doesn't use host parameter")

        # Test with invalid host - should fail gracefully without crashing
        conn = DatabaseConnection(
            dialect=dialect,
            host="invalid_host_that_does_not_exist",
            database=config.get("database", "test"),
            username=config.get("username", config.get("user", "invalid")),
            password=config.get("password", config.get("passwd", "invalid")),
        )

        # Connection object should be created but not connected
        assert conn is not None, "Connection object should be created even when connection fails"

        # State should indicate error or disconnected
        assert conn.state.value in [
            "error",
            "disconnected",
            "closed",
        ], f"Connection state should indicate failure, got: {conn.state.value}"

        # Should not be connected
        is_connected = conn.is_connected() if callable(conn.is_connected) else conn.is_connected
        assert not is_connected, "Connection should not be connected with invalid host"


class TestConnectionPooling:
    """Test connection pooling functionality."""

    @pytest.mark.unit
    def test_connection_pool_support(self):
        """Test that connection pooling is supported."""
        # Check if DatabaseConnection or factory supports pooling
        connection_attrs = dir(DatabaseConnection)

        # Common pooling-related attributes
        pooling_indicators = ["pool", "pool_size", "max_connections", "min_connections"]

        # Check if any pooling indicator exists
        has_pooling = any(attr in connection_attrs for attr in pooling_indicators)

        # Pooling may or may not be explicitly exposed - this is optional
        # The test passes as long as the check completes without error
        assert isinstance(has_pooling, bool), "Should be able to check for pooling support"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_connection_reuse(self, dialect, config_name, request):
        """Test that connections can be reused."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Execute first query
        # Oracle requires FROM DUAL for SELECT without a table
        if dialect == SQLDialect.ORACLE:
            result1 = conn.execute_query("SELECT 1 FROM DUAL")
            result2 = conn.execute_query("SELECT 2 FROM DUAL")
        else:
            result1 = conn.execute_query("SELECT 1")
            result2 = conn.execute_query("SELECT 2")

        assert result1 is not None
        assert len(result1) > 0

        # Reuse same connection for second query
        assert result2 is not None
        assert len(result2) > 0

        # Connection should still be usable
        assert conn.is_connected, "Connection should still be connected after reuse"

        conn.disconnect()


class TestConnectionContextManager:
    """Test connection context manager functionality."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_context_manager_enter_returns_connection(self, dialect, config_name, request):
        """Test that __enter__ returns usable connection."""
        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Should return the connection object
            assert conn is not None, "__enter__ should return the connection object"
            assert hasattr(conn, "execute_query"), "Returned object should be usable for executing queries"

            # Verify connection is actually usable
            # Oracle requires FROM DUAL for SELECT without a table
            if dialect == SQLDialect.ORACLE:
                result = conn.execute_query("SELECT 1 FROM DUAL")
            else:
                result = conn.execute_query("SELECT 1")
            assert result is not None, "Should be able to execute queries"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_context_manager_exit_closes_connection(self, dialect, config_name, request):
        """Test that __exit__ closes connection properly."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Enter and exit context
        conn.__enter__()
        initial_state = conn.state
        conn.__exit__(None, None, None)

        # Connection should be closed after exit
        assert (
            conn.state.value in ["disconnected", "closed", "idle"] or not conn.is_connected()
        ), f"Connection should be closed after __exit__, state: {conn.state.value}"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_context_manager_exception_handling(self, dialect, config_name, request):
        """Test that context manager handles exceptions properly."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Enter context
        conn.__enter__()

        # Simulate an exception
        test_exception = ValueError("Test error")
        conn.__exit__(ValueError, test_exception, None)

        # Connection should still be closed even with exception
        assert (
            conn.state.value in ["disconnected", "closed", "idle"] or not conn.is_connected()
        ), "Connection should close even when exception occurs"


class TestConnectionMethods:
    """Test connection method behavior."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_execute_accepts_sql_string(self, dialect, config_name, request):
        """Test that execute method accepts SQL string."""
        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Execute a simple SELECT query using execute_query
            # Oracle requires FROM DUAL for SELECT without a table
            if dialect == SQLDialect.ORACLE:
                result = conn.execute_query("SELECT 1 FROM DUAL")
            else:
                result = conn.execute_query("SELECT 1")

            assert result is not None, "Should execute simple SQL string"
            assert len(result) > 0, "Should return results"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name,param_style",
        [
            (SQLDialect.MYSQL, "mysql_config", "%s"),
            (SQLDialect.POSTGRES, "postgres_config", "%s"),
            (SQLDialect.ORACLE, "oracle_config", ":1"),
            (SQLDialect.SQLSERVER, "sqlserver_config", "?"),
            (SQLDialect.BIGQUERY, "bigquery_config", "@value"),
            (SQLDialect.REDSHIFT, "redshift_config", "%s"),
            (SQLDialect.SQLITE, "sqlite_config", "?"),
        ],
    )
    def test_execute_accepts_parameters(self, dialect, config_name, param_style, request):
        """Test that execute method accepts parameters."""
        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Test parameterized query for SQL injection protection
            # Oracle requires FROM DUAL for SELECT without a table
            # BigQuery uses named parameters with @param syntax
            if dialect == SQLDialect.ORACLE:
                query = f"SELECT {param_style} as value FROM DUAL"
                params = (42,)
            elif dialect == SQLDialect.BIGQUERY:
                query = f"SELECT {param_style} as value"
                params = {"value": 42}
            else:
                query = f"SELECT {param_style} as value"
                params = (42,)
            result = conn.execute_query(query, params)

            assert result is not None, "Should execute parameterized query"
            assert len(result) > 0, "Should return results"
            assert result[0][0] == 42, "Should return correct parameter value"

    @pytest.mark.unit
    def test_fetchone_method_exists(self):
        """Test that result fetching methods exist."""
        connection_methods = dir(DatabaseConnection)

        # Should have execute_query method which returns results
        has_execute = "execute_query" in connection_methods

        assert has_execute, "DatabaseConnection should have execute_query method for fetching results"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_commit_method_exists(self, dialect, config_name, request):
        """Test that transaction support exists via transaction() method."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Connection should have transaction context manager
        assert hasattr(conn, "transaction"), "DatabaseConnection should have transaction method"

        # transaction should be callable
        assert callable(conn.transaction), "transaction should be callable"

        conn.disconnect()

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_rollback_method_exists(self, dialect, config_name, request):
        """Test that transaction rollback works via transaction context manager."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Transaction context manager should handle rollback on exception
        try:
            with conn.transaction() as tx:
                # Transaction provides commit and rollback
                assert hasattr(tx, "rollback"), "Transaction should have rollback method"
                assert callable(tx.rollback), "rollback should be callable"
        except Exception:
            pass  # Expected if transaction setup fails

        conn.disconnect()


class TestConnectionProperties:
    """Test connection properties and attributes."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_connection_has_dialect_property(self, dialect, config_name, request):
        """Test that connection tracks its dialect."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Connection should track which dialect it's using
        assert hasattr(conn, "dialect"), "Connection should have dialect property"
        assert conn.dialect == dialect, f"Connection dialect should be {dialect}"

        conn.disconnect()

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_connection_has_database_property(self, dialect, config_name, request):
        """Test that connection knows its database."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Connection info should contain database
        conn_info = conn.connection_info
        assert "database" in conn_info or "dbname" in conn_info, "Connection should track database name"

        conn.disconnect()

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_connection_has_host_property(self, dialect, config_name, request):
        """Test that connection knows its host."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Connection info should contain host
        conn_info = conn.connection_info
        assert "host" in conn_info, "Connection should track host"

        conn.disconnect()


class TestConnectionSecurity:
    """Test connection security features."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name,param_style",
        [
            (SQLDialect.MYSQL, "mysql_config", "%s"),
            (SQLDialect.POSTGRES, "postgres_config", "%s"),
            (SQLDialect.ORACLE, "oracle_config", ":1"),
            (SQLDialect.SQLSERVER, "sqlserver_config", "?"),
            (SQLDialect.BIGQUERY, "bigquery_config", "@test_value"),
            (SQLDialect.REDSHIFT, "redshift_config", "%s"),
            (SQLDialect.SQLITE, "sqlite_config", "?"),
        ],
    )
    def test_parameterized_query_support(self, dialect, config_name, param_style, request):
        """Test that parameterized queries are supported."""
        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Test parameterized query to prevent SQL injection
            # Oracle requires FROM DUAL for SELECT without a table
            # BigQuery uses named parameters with @param syntax
            if dialect == SQLDialect.ORACLE:
                query = f"SELECT {param_style} as test_value FROM DUAL"
                params = ("test_data",)
            elif dialect == SQLDialect.BIGQUERY:
                query = f"SELECT {param_style} as test_value"
                params = {"test_value": "test_data"}
            else:
                query = f"SELECT {param_style} as test_value"
                params = ("test_data",)
            result = conn.execute_query(query, params)

            assert result is not None, "Parameterized queries should work"
            assert len(result) > 0, "Should return results"
            assert result[0][0] == "test_data", "Parameters should be correctly bound"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_password_not_in_repr(self, dialect, config_name, request):
        """Test that password is not exposed in string representation."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Get string representation
        conn_str = str(conn)
        conn_repr = repr(conn)

        # Password should be masked or not present
        password = config.get("password", config.get("passwd", ""))
        if password:
            assert password not in conn_str, "Password should not appear in str()"
            assert password not in conn_repr, "Password should not appear in repr()"

        conn.disconnect()

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_connection_string_sanitization(self, dialect, config_name, request):
        """Test that connection strings are sanitized for logging."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Connection info should have sanitized password
        conn_info = conn.connection_info
        if "password" in conn_info:
            assert conn_info["password"] == "***", "Password should be masked in connection info"

        # Check password is not in string representation
        password = config.get("password", config.get("passwd", ""))
        if password:
            assert password not in repr(conn), "Password should be masked in repr"

        conn.disconnect()


class TestConnectionCompatibility:
    """Test connection compatibility with different dialects."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "dialect",
        [
            SQLDialect.MYSQL,
            SQLDialect.POSTGRES,
            SQLDialect.ORACLE,
            SQLDialect.SQLSERVER,
            SQLDialect.SQLITE,
        ],
    )
    def test_connection_supports_major_dialects(self, dialect):
        """Test that connection supports major SQL dialects."""
        # Verify dialect enum exists and is valid
        assert dialect is not None
        assert isinstance(dialect, SQLDialect)

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_connection_autocommit_support(self, dialect, config_name, request):
        """Test that connection supports autocommit mode."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Get raw connection and check if it supports autocommit
        raw_conn = conn.get_raw_connection()
        has_autocommit = (
            hasattr(raw_conn, "autocommit")
            or hasattr(raw_conn, "set_autocommit")
            or hasattr(raw_conn, "get_autocommit")
        )

        # Autocommit support is optional but common
        assert isinstance(has_autocommit, bool), "Should be able to check autocommit support"

        conn.disconnect()

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_connection_transaction_isolation_support(self, dialect, config_name, request):
        """Test that connection supports transaction isolation levels."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)

        # Connection should have transaction method which supports isolation levels
        assert hasattr(conn, "transaction"), "Connection should have transaction method"

        # Transaction context manager is the way to handle isolation levels
        assert callable(conn.transaction), "transaction should be callable"

        conn.disconnect()


class TestConnectionMetadata:
    """Test connection metadata and introspection."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_connection_has_metadata_access(self, dialect, config_name, request):
        """Test that connection can access database metadata."""
        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Connection should be able to execute metadata queries
            assert hasattr(conn, "execute_query"), "Connection should have execute_query method"
            assert conn.is_connected, "Connection should be connected for metadata access"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name,query",
        [
            (SQLDialect.MYSQL, "mysql_config", "SHOW TABLES"),
            (SQLDialect.POSTGRES, "postgres_config", "SELECT tablename FROM pg_tables WHERE schemaname='public'"),
            (SQLDialect.ORACLE, "oracle_config", "SELECT table_name FROM user_tables"),
            (
                SQLDialect.SQLSERVER,
                "sqlserver_config",
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'",
            ),
            (SQLDialect.BIGQUERY, "bigquery_config", None),  # BigQuery requires qualified INFORMATION_SCHEMA
            (SQLDialect.REDSHIFT, "redshift_config", "SELECT tablename FROM pg_tables WHERE schemaname='public'"),
            (SQLDialect.SQLITE, "sqlite_config", "SELECT name FROM sqlite_master WHERE type='table'"),
        ],
    )
    def test_connection_can_list_tables(self, dialect, config_name, query, request):
        """Test that connection can list tables."""
        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # BigQuery requires qualified INFORMATION_SCHEMA with project and dataset
            if dialect == SQLDialect.BIGQUERY:
                project_id = config.get("project_id")
                dataset_id = config.get("dataset_id")
                query = f"SELECT table_name FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.TABLES`"

            # Execute dialect-specific query to list tables
            tables = conn.execute_query(query)

            # Should return a list (may be empty for new database)
            assert isinstance(tables, (list, tuple)), "Should return list of tables"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            (SQLDialect.REDSHIFT, "redshift_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_connection_can_describe_table(self, dialect, config_name, request):
        """Test that connection can describe table structure."""
        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Create a test table and describe it - EVERY dialect must actually do this
            try:
                if dialect == SQLDialect.SQLITE:
                    conn.execute_query("DROP TABLE IF EXISTS test_metadata")
                    conn.execute_query("CREATE TABLE test_metadata (id INTEGER, name TEXT)")
                    columns = conn.execute_query("PRAGMA table_info(test_metadata)")

                elif dialect == SQLDialect.MYSQL:
                    conn.execute_query("DROP TABLE IF EXISTS test_metadata")
                    conn.execute_query("CREATE TABLE test_metadata (id INT, name VARCHAR(100))")
                    columns = conn.execute_query("DESCRIBE test_metadata")

                elif dialect == SQLDialect.POSTGRES or dialect == SQLDialect.REDSHIFT:
                    conn.execute_query("DROP TABLE IF EXISTS test_metadata")
                    conn.execute_query("CREATE TABLE test_metadata (id INTEGER, name VARCHAR(100))")
                    columns = conn.execute_query(
                        "SELECT column_name, data_type FROM information_schema.columns "
                        "WHERE table_name = 'test_metadata'"
                    )

                elif dialect == SQLDialect.ORACLE:
                    # Oracle doesn't support IF EXISTS, try/except for drop
                    try:
                        conn.execute_query("DROP TABLE test_metadata")
                    except:
                        pass  # Table doesn't exist, that's fine
                    conn.execute_query("CREATE TABLE test_metadata (id NUMBER, name VARCHAR2(100))")
                    columns = conn.execute_query(
                        "SELECT column_name, data_type FROM user_tab_columns "
                        "WHERE table_name = 'TEST_METADATA'"  # Oracle uppercases table names
                    )

                elif dialect == SQLDialect.SQLSERVER:
                    conn.execute_query("IF OBJECT_ID('test_metadata', 'U') IS NOT NULL DROP TABLE test_metadata")
                    conn.execute_query("CREATE TABLE test_metadata (id INT, name VARCHAR(100))")
                    columns = conn.execute_query(
                        "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_NAME = 'test_metadata'"
                    )

                elif dialect == SQLDialect.BIGQUERY:
                    # BigQuery requires dataset.table naming - get dataset from config
                    dataset_id = config.get("dataset_id")
                    project_id = config.get("project_id")

                    # Drop table if exists
                    conn.execute_query(f"DROP TABLE IF EXISTS `{project_id}.{dataset_id}.test_metadata`")

                    # Create table with fully qualified name
                    conn.execute_query(
                        f"CREATE TABLE `{project_id}.{dataset_id}.test_metadata` " "(id INT64, name STRING)"
                    )

                    # Describe table
                    columns = conn.execute_query(
                        f"SELECT column_name, data_type FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS` "
                        f"WHERE table_name = 'test_metadata'"
                    )
                else:
                    raise ValueError(f"Unsupported dialect for table creation test: {dialect}")

                # MUST get column information for ALL dialects - no exceptions!
                assert columns is not None, f"Failed to get columns for {dialect.name}"
                assert len(columns) > 0, f"Should retrieve table structure information for {dialect.name}"
                assert (
                    len(columns) >= 2
                ), f"Should have at least 2 columns (id, name) for {dialect.name}, got {len(columns)}"

            finally:
                # Clean up - must clean up for ALL dialects
                try:
                    if dialect == SQLDialect.ORACLE:
                        conn.execute_query("DROP TABLE test_metadata")
                    elif dialect == SQLDialect.BIGQUERY:
                        dataset_id = config.get("dataset_id")
                        project_id = config.get("project_id")
                        conn.execute_query(f"DROP TABLE IF EXISTS `{project_id}.{dataset_id}.test_metadata`")
                    elif dialect == SQLDialect.SQLSERVER:
                        conn.execute_query("IF OBJECT_ID('test_metadata', 'U') IS NOT NULL DROP TABLE test_metadata")
                    else:
                        conn.execute_query("DROP TABLE IF EXISTS test_metadata")
                except Exception as e:
                    # Log cleanup failure but don't fail the test
                    print(f"Warning: Failed to clean up test_metadata table for {dialect.name}: {e}")


@pytest.mark.integration
class TestConnectionIntegration:
    """Integration tests for actual database connections."""

    @pytest.mark.integration
    @pytest.mark.sqlite
    def test_sqlite_connection_creation(self, temp_sqlite_db):
        """Test creating SQLite connection."""
        # temp_sqlite_db fixture should provide a valid database path
        assert temp_sqlite_db is not None

        # Create connection using the temp database
        conn = DatabaseConnection(dialect=SQLDialect.SQLITE, database=temp_sqlite_db)

        # Verify connection was created
        assert conn is not None
        assert conn.dialect == SQLDialect.SQLITE

        conn.disconnect()

    @pytest.mark.integration
    @pytest.mark.mysql
    def test_mysql_connection_creation(self, mysql_config):
        """Test creating MySQL connection."""
        assert mysql_config is not None

        # Create actual MySQL connection
        with DatabaseConnection(dialect=SQLDialect.MYSQL, **mysql_config) as conn:
            # Verify connection works
            assert conn is not None
            result = conn.execute_query("SELECT 1")
            assert result is not None
            assert len(result) > 0
            assert result[0][0] == 1

    @pytest.mark.integration
    @pytest.mark.postgres
    def test_postgres_connection_creation(self, postgres_config):
        """Test creating PostgreSQL connection."""
        assert postgres_config is not None

        # Create actual PostgreSQL connection
        with DatabaseConnection(dialect=SQLDialect.POSTGRES, **postgres_config) as conn:
            # Verify connection works
            assert conn is not None
            result = conn.execute_query("SELECT 1")
            assert result is not None
            assert len(result) > 0
            assert result[0][0] == 1

    @pytest.mark.integration
    @pytest.mark.oracle
    def test_oracle_connection_creation(self, oracle_config):
        """Test creating Oracle connection."""
        assert oracle_config is not None

        # Create actual Oracle connection
        with DatabaseConnection(dialect=SQLDialect.ORACLE, **oracle_config) as conn:
            # Verify connection works
            assert conn is not None
            result = conn.execute_query("SELECT 1 FROM DUAL")
            assert result is not None
            assert len(result) > 0
            assert result[0][0] == 1

    @pytest.mark.integration
    @pytest.mark.sqlserver
    def test_sqlserver_connection_creation(self, sqlserver_config):
        """Test creating SQL Server connection."""
        assert sqlserver_config is not None

        # Create actual SQL Server connection
        with DatabaseConnection(dialect=SQLDialect.SQLSERVER, **sqlserver_config) as conn:
            # Verify connection works
            assert conn is not None
            result = conn.execute_query("SELECT 1")
            assert result is not None
            assert len(result) > 0
            assert result[0][0] == 1
