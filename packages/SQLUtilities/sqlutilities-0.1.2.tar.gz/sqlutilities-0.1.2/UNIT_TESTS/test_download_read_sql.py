"""
Unit tests for download.read_sql module.

This module tests the high-performance data loading functionality including:
- read_sql() function with multiple dataframe backends
- execute_query_with_metadata() function
- Type inference and column metadata extraction
- ConnectorX integration with fallback handling
- Multi-dialect support across all databases
"""

import pytest

from sqlutilities.connections import DatabaseConnection
from sqlutilities.core import SQLDialect
from sqlutilities.download import execute_query_with_metadata, read_sql

# Check which optional dependencies are available
PANDAS_AVAILABLE = False
POLARS_AVAILABLE = False
DASK_AVAILABLE = False
PYARROW_AVAILABLE = False

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    pd = None  # type: ignore

try:
    import polars as pl

    POLARS_AVAILABLE = True
except ImportError:
    pl = None  # type: ignore

try:
    import dask.dataframe as dd

    DASK_AVAILABLE = True
except ImportError:
    dd = None  # type: ignore

try:
    import pyarrow as pa

    PYARROW_AVAILABLE = True
except ImportError:
    pa = None  # type: ignore


class TestReadSQLBasicFunctionality:
    """Basic functionality tests for read_sql across all databases."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
            # (SQLDialect.REDSHIFT, "redshift_config"),  # Commented out: requires sqlalchemy-redshift package
        ],
    )
    @pytest.mark.skipif(not PANDAS_AVAILABLE, reason="Pandas not installed")
    def test_basic_pandas_query(self, dialect, config_name, request):
        """Test basic query returning Pandas DataFrame across all databases."""
        config = request.getfixturevalue(config_name)

        # Create connection
        conn = DatabaseConnection(dialect=dialect, **config)
        conn.connect()

        try:
            # Create a simple test table
            table_name = f"test_read_sql_pandas_{dialect.name_value}"

            # Handle dialect-specific SQL
            if dialect == SQLDialect.SQLITE:
                # Drop table first to ensure clean state
                conn.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                create_sql = f"""
                    CREATE TABLE {table_name} (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        value REAL
                    )
                """
                insert_sql = f"INSERT INTO {table_name} (id, name, value) VALUES (?, ?, ?)"
                select_query = f"SELECT * FROM {table_name}"
            elif dialect == SQLDialect.ORACLE:
                # Oracle syntax
                create_sql = f"""
                    BEGIN
                        EXECUTE IMMEDIATE 'DROP TABLE "{table_name}"';
                    EXCEPTION
                        WHEN OTHERS THEN NULL;
                    END;
                """
                conn.execute_query(create_sql)
                create_sql = f"""
                    CREATE TABLE "{table_name}" (
                        "id" NUMBER PRIMARY KEY,
                        "name" VARCHAR2(100) NOT NULL,
                        "value" NUMBER
                    )
                """
                insert_sql = f'INSERT INTO "{table_name}" ("id", "name", "value") VALUES (:1, :2, :3)'
                select_query = f'SELECT "id", "name", "value" FROM "{table_name}"'
            elif dialect == SQLDialect.SQLSERVER:
                create_sql = f"""
                    IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name};
                    CREATE TABLE {table_name} (
                        id INT PRIMARY KEY,
                        name NVARCHAR(100) NOT NULL,
                        value FLOAT
                    )
                """
                insert_sql = f"INSERT INTO {table_name} (id, name, value) VALUES (?, ?, ?)"
                select_query = f"SELECT * FROM {table_name}"
            else:  # MySQL, PostgreSQL, Redshift
                create_sql = f"""
                    DROP TABLE IF EXISTS {table_name};
                    CREATE TABLE {table_name} (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        value FLOAT
                    )
                """
                insert_sql = (
                    f"INSERT INTO {table_name} (id, name, value) VALUES (%s, %s, %s)"
                    if dialect != SQLDialect.SQLITE
                    else f"INSERT INTO {table_name} (id, name, value) VALUES (?, ?, ?)"
                )
                select_query = f"SELECT * FROM {table_name}"

            # Create table
            conn.execute_query(create_sql)

            # Insert test data
            test_data = [(1, "Alice", 100.5), (2, "Bob", 200.75), (3, "Charlie", 300.25)]
            for row in test_data:
                conn.execute_query(insert_sql, row)

            # Test read_sql with Pandas
            df = read_sql(select_query, conn, output_format="pandas")

            # Verify results
            assert df is not None
            assert len(df) == 3
            assert "id" in df.columns or "ID" in df.columns  # Case may vary by database
            assert "name" in df.columns or "NAME" in df.columns or "name" in str(df.columns).lower()

            # Cleanup
            if dialect == SQLDialect.ORACLE:
                conn.execute_query(f'DROP TABLE "{table_name}"')
            else:
                conn.execute_query(f"DROP TABLE {table_name}")

        finally:
            conn.disconnect()

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
            # (SQLDialect.REDSHIFT, "redshift_config"),  # Commented out: requires sqlalchemy-redshift package
        ],
    )
    @pytest.mark.skipif(not POLARS_AVAILABLE, reason="Polars not installed")
    def test_basic_polars_query(self, dialect, config_name, request):
        """Test basic query returning Polars DataFrame across all databases."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)
        conn.connect()

        try:
            table_name = f"test_read_sql_polars_{dialect.name_value}"

            # Handle dialect-specific SQL
            if dialect == SQLDialect.SQLITE:
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY, name TEXT)"
                insert_sql = f"INSERT INTO {table_name} (id, name) VALUES (?, ?)"
                select_query = f"SELECT * FROM {table_name} WHERE id <= 2"
            elif dialect == SQLDialect.ORACLE:
                conn.execute_query(
                    f"BEGIN EXECUTE IMMEDIATE 'DROP TABLE \"{table_name}\"'; EXCEPTION WHEN OTHERS THEN NULL; END;"
                )
                create_sql = f'CREATE TABLE "{table_name}" ("id" NUMBER PRIMARY KEY, "name" VARCHAR2(100))'
                insert_sql = f'INSERT INTO "{table_name}" ("id", "name") VALUES (:1, :2)'
                select_query = f'SELECT "id", "name" FROM "{table_name}" WHERE "id" <= 2'
            elif dialect == SQLDialect.SQLSERVER:
                create_sql = f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name}; CREATE TABLE {table_name} (id INT PRIMARY KEY, name NVARCHAR(100))"
                insert_sql = f"INSERT INTO {table_name} (id, name) VALUES (?, ?)"
                select_query = f"SELECT * FROM {table_name} WHERE id <= 2"
            else:
                create_sql = f"DROP TABLE IF EXISTS {table_name}; CREATE TABLE {table_name} (id INTEGER PRIMARY KEY, name VARCHAR(100))"
                insert_sql = (
                    f"INSERT INTO {table_name} (id, name) VALUES (%s, %s)"
                    if dialect != SQLDialect.SQLITE
                    else f"INSERT INTO {table_name} (id, name) VALUES (?, ?)"
                )
                select_query = f"SELECT * FROM {table_name} WHERE id <= 2"

            conn.execute_query(create_sql)

            test_data = [(1, "Test1"), (2, "Test2"), (3, "Test3")]
            for row in test_data:
                conn.execute_query(insert_sql, row)

            # Test read_sql with Polars (default format)
            df = read_sql(select_query, conn, output_format="polars")

            assert df is not None
            assert len(df) == 2

            # Cleanup
            if dialect == SQLDialect.ORACLE:
                conn.execute_query(f'DROP TABLE "{table_name}"')
            else:
                conn.execute_query(f"DROP TABLE {table_name}")

        finally:
            conn.disconnect()


class TestReadSQLWithParameters:
    """Tests for parameterized queries."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    @pytest.mark.skipif(not PANDAS_AVAILABLE, reason="Pandas not installed")
    def test_parameterized_query(self, dialect, config_name, request):
        """Test queries with parameters."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)
        conn.connect()

        try:
            table_name = f"test_params_{dialect.name_value}"

            # Create table and insert data
            if dialect == SQLDialect.SQLITE:
                conn.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                conn.execute_query(f"CREATE TABLE {table_name} (id INTEGER, value INTEGER)")
                conn.execute_query(f"INSERT INTO {table_name} VALUES (1, 10), (2, 20), (3, 30)")
                query = f"SELECT * FROM {table_name} WHERE value > ?"
                params = (15,)
            elif dialect == SQLDialect.ORACLE:
                conn.execute_query(
                    f"BEGIN EXECUTE IMMEDIATE 'DROP TABLE \"{table_name}\"'; EXCEPTION WHEN OTHERS THEN NULL; END;"
                )
                conn.execute_query(f'CREATE TABLE "{table_name}" ("id" NUMBER, "value" NUMBER)')
                conn.execute_query(f'INSERT INTO "{table_name}" VALUES (1, 10)')
                conn.execute_query(f'INSERT INTO "{table_name}" VALUES (2, 20)')
                conn.execute_query(f'INSERT INTO "{table_name}" VALUES (3, 30)')
                query = f'SELECT "id", "value" FROM "{table_name}" WHERE "value" > :1'
                params = (15,)
            elif dialect == SQLDialect.SQLSERVER:
                conn.execute_query(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name}")
                conn.execute_query(f"CREATE TABLE {table_name} (id INT, value INT)")
                conn.execute_query(f"INSERT INTO {table_name} VALUES (1, 10), (2, 20), (3, 30)")
                query = f"SELECT * FROM {table_name} WHERE value > ?"
                params = (15,)
            else:  # MySQL, PostgreSQL
                conn.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                conn.execute_query(f"CREATE TABLE {table_name} (id INTEGER, value INTEGER)")
                conn.execute_query(f"INSERT INTO {table_name} VALUES (1, 10), (2, 20), (3, 30)")
                query = f"SELECT * FROM {table_name} WHERE value > %s"
                params = (15,)

            # Execute parameterized query
            df = read_sql(query, conn, parameters=params, output_format="pandas")

            assert df is not None
            assert len(df) == 2  # Should return rows with value 20 and 30

            # Cleanup
            if dialect == SQLDialect.ORACLE:
                conn.execute_query(f'DROP TABLE "{table_name}"')
            else:
                conn.execute_query(f"DROP TABLE {table_name}")

        finally:
            conn.disconnect()


class TestExecuteQueryWithMetadata:
    """Tests for execute_query_with_metadata function."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_metadata_extraction(self, dialect, config_name, request):
        """Test column metadata extraction."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)
        conn.connect()

        try:
            table_name = f"test_metadata_{dialect.name_value}"

            # Create table
            if dialect == SQLDialect.SQLITE:
                conn.execute_query(f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER, name TEXT)")
                conn.execute_query(f"INSERT INTO {table_name} VALUES (1, 'Test')")
                query = f"SELECT * FROM {table_name}"
            elif dialect == SQLDialect.ORACLE:
                conn.execute_query(
                    f"BEGIN EXECUTE IMMEDIATE 'DROP TABLE \"{table_name}\"'; EXCEPTION WHEN OTHERS THEN NULL; END;"
                )
                conn.execute_query(f'CREATE TABLE "{table_name}" ("id" NUMBER, "name" VARCHAR2(100))')
                conn.execute_query(f"INSERT INTO \"{table_name}\" VALUES (1, 'Test')")
                query = f'SELECT "id", "name" FROM "{table_name}"'
            elif dialect == SQLDialect.SQLSERVER:
                conn.execute_query(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name}")
                conn.execute_query(f"CREATE TABLE {table_name} (id INT, name NVARCHAR(100))")
                conn.execute_query(f"INSERT INTO {table_name} VALUES (1, 'Test')")
                query = f"SELECT * FROM {table_name}"
            else:
                conn.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                conn.execute_query(f"CREATE TABLE {table_name} (id INTEGER, name VARCHAR(100))")
                conn.execute_query(f"INSERT INTO {table_name} VALUES (1, 'Test')")
                query = f"SELECT * FROM {table_name}"

            # Get metadata
            columns, data = execute_query_with_metadata(query, conn)

            assert isinstance(columns, dict)
            assert len(data) == 1

            # Cleanup
            if dialect == SQLDialect.ORACLE:
                conn.execute_query(f'DROP TABLE "{table_name}"')
            else:
                conn.execute_query(f"DROP TABLE {table_name}")

        finally:
            conn.disconnect()


class TestReadSQLPyArrow:
    """Tests for PyArrow output format."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    @pytest.mark.skipif(not PYARROW_AVAILABLE or not PANDAS_AVAILABLE, reason="PyArrow or Pandas not installed")
    def test_pyarrow_output(self, dialect, config_name, request):
        """Test PyArrow Table output format."""
        config = request.getfixturevalue(config_name)

        conn = DatabaseConnection(dialect=dialect, **config)
        conn.connect()

        try:
            table_name = f"test_pyarrow_{dialect.name_value}"

            if dialect == SQLDialect.SQLITE:
                conn.execute_query(f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER)")
                conn.execute_query(f"INSERT INTO {table_name} VALUES (1)")
                query = f"SELECT * FROM {table_name}"
            else:
                conn.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                conn.execute_query(f"CREATE TABLE {table_name} (id INTEGER)")
                conn.execute_query(f"INSERT INTO {table_name} VALUES (1)")
                query = f"SELECT * FROM {table_name}"

            table = read_sql(query, conn, output_format="pyarrow")

            assert table is not None
            assert hasattr(table, "num_rows") or hasattr(table, "shape")

            # Cleanup
            conn.execute_query(f"DROP TABLE {table_name}")

        finally:
            conn.disconnect()


class TestReadSQLErrorHandling:
    """Tests for error handling."""

    @pytest.mark.unit
    def test_invalid_output_format(self):
        """Test that invalid output format raises error."""
        # This is a unit test that doesn't require a database connection
        # It will fail during validation before attempting to connect
        with pytest.raises(AssertionError, match="output_format must be one of"):
            conn = DatabaseConnection(dialect=SQLDialect.SQLITE, database=":memory:")
            read_sql("SELECT 1", conn, output_format="invalid_format")  # type: ignore


# Test summary
@pytest.mark.unit
def test_module_imports():
    """Test that all required modules can be imported."""
    from sqlutilities.download import execute_query_with_metadata, read_sql

    assert read_sql is not None
    assert execute_query_with_metadata is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
