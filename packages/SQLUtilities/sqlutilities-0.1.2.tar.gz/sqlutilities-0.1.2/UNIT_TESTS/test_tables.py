"""
Unit tests for tables module.

Tests for:
- SQL_TABLE class
- ColumnDefinition
- TableDefinition
- ConstraintDefinition
- IndexDefinition
- Table operations (CREATE, DROP, ALTER)
"""

import pytest

from sqlutilities.core import COLUMNDTYPE, SQLDialect
from sqlutilities.tables import (
    SQL_TABLE,
    ColumnDefinition,
    ConstraintDefinition,
    IndexDefinition,
    TableComponentType,
    TableDefinition,
    TableOperation,
)


class TestColumnDefinition:
    """Test cases for ColumnDefinition class."""

    @pytest.mark.unit
    def test_column_definition_exists(self):
        """Test that ColumnDefinition class exists."""
        assert ColumnDefinition is not None

    @pytest.mark.unit
    def test_column_definition_is_dataclass(self):
        """Test that ColumnDefinition is a dataclass."""
        assert hasattr(ColumnDefinition, "__dataclass_fields__"), "ColumnDefinition should be a dataclass"

    @pytest.mark.unit
    def test_column_definition_required_fields(self):
        """Test that ColumnDefinition has required fields."""
        required_fields = ["name", "data_type", "dialect"]

        for field in required_fields:
            assert field in ColumnDefinition.__dataclass_fields__, f"ColumnDefinition missing required field '{field}'"

    @pytest.mark.unit
    def test_column_definition_creation(self):
        """Test creating a simple column definition."""
        column = ColumnDefinition(name="id", data_type=COLUMNDTYPE.INTEGER, dialect=SQLDialect.MYSQL)

        assert column.name == "id"
        assert column.data_type == COLUMNDTYPE.INTEGER
        assert column.dialect == SQLDialect.MYSQL

    @pytest.mark.unit
    def test_column_definition_with_length(self):
        """Test creating column definition with length."""
        column = ColumnDefinition(
            name="username", data_type=COLUMNDTYPE.VARCHAR, dialect=SQLDialect.POSTGRES, length=255
        )

        assert column.length == 255

    @pytest.mark.unit
    def test_column_definition_with_precision_scale(self):
        """Test creating column definition with precision and scale."""
        column = ColumnDefinition(
            name="price", data_type=COLUMNDTYPE.DECIMAL, dialect=SQLDialect.MYSQL, precision=10, scale=2
        )

        assert column.precision == 10
        assert column.scale == 2

    @pytest.mark.unit
    def test_column_definition_nullable(self):
        """Test column definition nullable flag."""
        nullable_column = ColumnDefinition(
            name="optional_field", data_type=COLUMNDTYPE.VARCHAR, dialect=SQLDialect.MYSQL, nullable=True
        )

        not_null_column = ColumnDefinition(
            name="required_field", data_type=COLUMNDTYPE.VARCHAR, dialect=SQLDialect.MYSQL, nullable=False
        )

        assert nullable_column.nullable is True
        assert not_null_column.nullable is False

    @pytest.mark.unit
    def test_column_definition_default_value(self):
        """Test column definition with default value."""
        column = ColumnDefinition(
            name="status", data_type=COLUMNDTYPE.VARCHAR, dialect=SQLDialect.POSTGRES, default_value="'active'"
        )

        assert column.default_value == "'active'"

    @pytest.mark.unit
    def test_column_definition_identity(self):
        """Test column definition with identity/auto-increment."""
        column = ColumnDefinition(
            name="id",
            data_type=COLUMNDTYPE.INTEGER,
            dialect=SQLDialect.SQLSERVER,
            is_identity=True,
            identity_seed=1,
            identity_increment=1,
        )

        assert column.is_identity is True
        assert column.identity_seed == 1
        assert column.identity_increment == 1

    @pytest.mark.unit
    def test_column_definition_validation(self):
        """Test column definition validation."""
        # Empty name should raise error
        with pytest.raises(ValueError):
            ColumnDefinition(name="", data_type=COLUMNDTYPE.INTEGER, dialect=SQLDialect.MYSQL)

    @pytest.mark.unit
    def test_column_definition_full_data_type_property(self):
        """Test full_data_type property."""
        column = ColumnDefinition(
            name="description", data_type=COLUMNDTYPE.VARCHAR, dialect=SQLDialect.MYSQL, length=500
        )

        full_type = column.full_data_type
        assert full_type is not None
        assert isinstance(full_type, str)


class TestConstraintDefinition:
    """Test cases for ConstraintDefinition class."""

    @pytest.mark.unit
    def test_constraint_definition_exists(self):
        """Test that ConstraintDefinition class exists."""
        assert ConstraintDefinition is not None

    @pytest.mark.unit
    def test_constraint_definition_is_dataclass(self):
        """Test that ConstraintDefinition is a dataclass."""
        assert hasattr(ConstraintDefinition, "__dataclass_fields__"), "ConstraintDefinition should be a dataclass"

    @pytest.mark.unit
    def test_constraint_definition_required_fields(self):
        """Test that ConstraintDefinition has required fields."""
        required_fields = ["name", "constraint_type", "columns"]

        for field in required_fields:
            assert (
                field in ConstraintDefinition.__dataclass_fields__
            ), f"ConstraintDefinition missing required field '{field}'"

    @pytest.mark.unit
    def test_primary_key_constraint(self):
        """Test creating primary key constraint."""
        pk = ConstraintDefinition(name="pk_users", constraint_type=TableComponentType.PRIMARY_KEY, columns=["id"])

        assert pk.name == "pk_users"
        assert pk.constraint_type == TableComponentType.PRIMARY_KEY
        assert pk.columns == ["id"]

    @pytest.mark.unit
    def test_foreign_key_constraint(self):
        """Test creating foreign key constraint."""
        fk = ConstraintDefinition(
            name="fk_orders_users",
            constraint_type=TableComponentType.FOREIGN_KEY,
            columns=["user_id"],
            reference_table="users",
            reference_columns=["id"],
        )

        assert fk.reference_table == "users"
        assert fk.reference_columns == ["id"]

    @pytest.mark.unit
    def test_unique_constraint(self):
        """Test creating unique constraint."""
        unique = ConstraintDefinition(
            name="uk_email", constraint_type=TableComponentType.UNIQUE_CONSTRAINT, columns=["email"]
        )

        assert unique.constraint_type == TableComponentType.UNIQUE_CONSTRAINT

    @pytest.mark.unit
    def test_check_constraint(self):
        """Test creating check constraint."""
        check = ConstraintDefinition(
            name="chk_age",
            constraint_type=TableComponentType.CHECK_CONSTRAINT,
            columns=["age"],
            check_expression="age >= 18",
        )

        assert check.check_expression == "age >= 18"


class TestIndexDefinition:
    """Test cases for IndexDefinition class."""

    @pytest.mark.unit
    def test_index_definition_exists(self):
        """Test that IndexDefinition class exists."""
        assert IndexDefinition is not None

    @pytest.mark.unit
    def test_index_definition_is_dataclass(self):
        """Test that IndexDefinition is a dataclass."""
        assert hasattr(IndexDefinition, "__dataclass_fields__"), "IndexDefinition should be a dataclass"

    @pytest.mark.unit
    def test_index_definition_required_fields(self):
        """Test that IndexDefinition has required fields."""
        required_fields = ["name", "columns"]

        for field in required_fields:
            assert field in IndexDefinition.__dataclass_fields__, f"IndexDefinition missing required field '{field}'"

    @pytest.mark.unit
    def test_simple_index_creation(self):
        """Test creating a simple index."""
        index = IndexDefinition(name="idx_email", columns=["email"])

        assert index.name == "idx_email"
        assert index.columns == ["email"]

    @pytest.mark.unit
    def test_unique_index_creation(self):
        """Test creating a unique index."""
        index = IndexDefinition(name="idx_username", columns=["username"], is_unique=True)

        assert index.is_unique is True

    @pytest.mark.unit
    def test_composite_index_creation(self):
        """Test creating a composite index."""
        index = IndexDefinition(name="idx_name", columns=["first_name", "last_name"])

        assert len(index.columns) == 2

    @pytest.mark.unit
    def test_clustered_index(self):
        """Test creating a clustered index."""
        index = IndexDefinition(name="idx_id", columns=["id"], is_clustered=True)

        assert index.is_clustered is True

    @pytest.mark.unit
    def test_partial_index(self):
        """Test creating a partial index."""
        index = IndexDefinition(
            name="idx_active_users", columns=["created_at"], is_partial=True, where_clause="status = 'active'"
        )

        assert index.is_partial is True
        assert index.where_clause == "status = 'active'"


class TestTableDefinition:
    """Test cases for TableDefinition class."""

    @pytest.mark.unit
    def test_table_definition_exists(self):
        """Test that TableDefinition class exists."""
        assert TableDefinition is not None

    @pytest.mark.unit
    def test_table_definition_is_dataclass(self):
        """Test that TableDefinition is a dataclass."""
        assert hasattr(TableDefinition, "__dataclass_fields__"), "TableDefinition should be a dataclass"

    @pytest.mark.unit
    def test_table_definition_required_fields(self):
        """Test that TableDefinition has required field."""
        assert "name" in TableDefinition.__dataclass_fields__, "TableDefinition missing required field 'name'"

    @pytest.mark.unit
    def test_simple_table_definition(self):
        """Test creating a simple table definition."""
        table = TableDefinition(name="users")

        assert table.name == "users"
        assert isinstance(table.columns, list)

    @pytest.mark.unit
    def test_table_definition_with_schema(self):
        """Test table definition with schema."""
        table = TableDefinition(name="users", schema="public")

        assert table.schema == "public"

    @pytest.mark.unit
    def test_table_definition_with_columns(self):
        """Test table definition with columns."""
        columns = [
            ColumnDefinition(name="id", data_type=COLUMNDTYPE.INTEGER, dialect=SQLDialect.POSTGRES),
            ColumnDefinition(name="username", data_type=COLUMNDTYPE.VARCHAR, dialect=SQLDialect.POSTGRES, length=50),
        ]

        table = TableDefinition(name="users", columns=columns)

        assert len(table.columns) == 2

    @pytest.mark.unit
    def test_table_definition_with_constraints(self):
        """Test table definition with constraints."""
        constraints = [
            ConstraintDefinition(name="pk_users", constraint_type=TableComponentType.PRIMARY_KEY, columns=["id"])
        ]

        table = TableDefinition(name="users", constraints=constraints)

        assert len(table.constraints) == 1

    @pytest.mark.unit
    def test_table_definition_with_indexes(self):
        """Test table definition with indexes."""
        indexes = [IndexDefinition(name="idx_email", columns=["email"])]

        table = TableDefinition(name="users", indexes=indexes)

        assert len(table.indexes) == 1

    @pytest.mark.unit
    def test_complete_table_definition(self):
        """Test creating a complete table definition."""
        table = TableDefinition(
            name="users",
            schema="public",
            columns=[
                ColumnDefinition(name="id", data_type=COLUMNDTYPE.INTEGER, dialect=SQLDialect.POSTGRES, nullable=False),
                ColumnDefinition(
                    name="email", data_type=COLUMNDTYPE.VARCHAR, dialect=SQLDialect.POSTGRES, length=255, nullable=False
                ),
            ],
            constraints=[
                ConstraintDefinition(name="pk_users", constraint_type=TableComponentType.PRIMARY_KEY, columns=["id"])
            ],
            indexes=[IndexDefinition(name="idx_email", columns=["email"], is_unique=True)],
            comment="User accounts table",
        )

        assert table.name == "users"
        assert len(table.columns) == 2
        assert len(table.constraints) == 1
        assert len(table.indexes) == 1
        assert table.comment == "User accounts table"


class TestTableComponentType:
    """Test cases for TableComponentType enum."""

    @pytest.mark.unit
    def test_table_component_type_exists(self):
        """Test that TableComponentType enum exists."""
        assert TableComponentType is not None

    @pytest.mark.unit
    def test_table_component_types_defined(self):
        """Test that common component types are defined."""
        expected_types = ["COLUMN", "PRIMARY_KEY", "FOREIGN_KEY", "UNIQUE_CONSTRAINT", "CHECK_CONSTRAINT", "INDEX"]

        for comp_type in expected_types:
            assert hasattr(TableComponentType, comp_type), f"TableComponentType.{comp_type} not found"


class TestTableOperation:
    """Test cases for TableOperation enum."""

    @pytest.mark.unit
    def test_table_operation_exists(self):
        """Test that TableOperation enum exists."""
        assert TableOperation is not None

    @pytest.mark.unit
    def test_table_operations_defined(self):
        """Test that common operations are defined."""
        expected_operations = ["CREATE", "DROP", "ALTER", "DESCRIBE"]

        for operation in expected_operations:
            assert hasattr(TableOperation, operation), f"TableOperation.{operation} not found"


class TestSQLTable:
    """Test cases for SQL_TABLE class."""

    @pytest.mark.unit
    def test_sql_table_class_exists(self):
        """Test that SQL_TABLE class exists."""
        assert SQL_TABLE is not None

    @pytest.mark.unit
    def test_sql_table_has_create_method(self):
        """Test that SQL_TABLE has create method."""
        table_methods = dir(SQL_TABLE)

        has_create = any(method in table_methods for method in ["create", "create_table"])

        assert has_create, "SQL_TABLE should have create method"

    @pytest.mark.unit
    def test_sql_table_has_drop_method(self):
        """Test that SQL_TABLE has drop method."""
        table_methods = dir(SQL_TABLE)

        has_drop = any(method in table_methods for method in ["drop", "drop_table"])

        assert has_drop, "SQL_TABLE should have drop method"

    @pytest.mark.unit
    def test_sql_table_has_alter_method(self):
        """Test that SQL_TABLE has alter method."""
        table_methods = dir(SQL_TABLE)

        has_alter = any(method in table_methods for method in ["alter", "alter_table"])

        assert has_alter, "SQL_TABLE should have alter method"

    @pytest.mark.unit
    def test_sql_table_has_exists_method(self):
        """Test that SQL_TABLE has exists check method."""
        table_methods = dir(SQL_TABLE)

        has_exists = any(method in table_methods for method in ["exists", "table_exists", "check_exists"])

        assert has_exists, "SQL_TABLE should have exists check method"

    @pytest.mark.unit
    def test_sql_table_has_describe_method(self):
        """Test that SQL_TABLE has describe method."""
        table_methods = dir(SQL_TABLE)

        has_describe = any(method in table_methods for method in ["describe", "describe_table", "get_structure"])

        assert has_describe, "SQL_TABLE should have describe method"


@pytest.mark.integration
class TestTableSQLGeneration:
    """Test SQL generation for table operations using dry_run mode."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            # (SQLDialect.REDSHIFT, "redshift_config")  # Commented out: requires sqlalchemy-redshift package
        ],
    )
    def test_create_table_sql_structure(self, dialect, config_name, request):
        """Test that CREATE TABLE SQL has correct structure for ALL dialects."""
        from sqlutilities.connections import DatabaseConnection

        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Create SQL_TABLE instance
            sql_table = SQL_TABLE(connection=conn, table_name="test_table")

            # Add columns to definition
            sql_table.add_column(name="id", data_type=COLUMNDTYPE.INTEGER, nullable=False)
            sql_table.add_column(name="name", data_type=COLUMNDTYPE.VARCHAR, length=100)

            # Add primary key constraint (BigQuery doesn't support PRIMARY KEY enforcement)
            if dialect != SQLDialect.BIGQUERY:
                sql_table.add_primary_key_constraint("pk_test", ["id"])

            # Generate CREATE TABLE SQL using dry_run
            sql = sql_table.create_table(if_exists="fail", dry_run=True)

            # Verify SQL structure
            assert sql is not None, f"Should generate SQL for {dialect.name}"
            assert isinstance(sql, str), f"SQL should be a string for {dialect.name}"
            assert "CREATE TABLE" in sql.upper(), f"Should contain CREATE TABLE for {dialect.name}"
            assert "id" in sql.lower(), f"Should contain column name 'id' for {dialect.name}"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.SQLITE, "sqlite_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            # (SQLDialect.REDSHIFT, "redshift_config")  # Commented out: requires sqlalchemy-redshift package
        ],
    )
    def test_drop_table_sql_structure(self, dialect, config_name, request):
        """Test that DROP TABLE SQL has correct structure for ALL dialects."""
        from sqlutilities.connections import DatabaseConnection

        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Create SQL_TABLE instance
            sql_table = SQL_TABLE(connection=conn, table_name="test_table")

            # Generate DROP TABLE SQL using private method
            sql = sql_table._generate_drop_table_sql(if_exists=True)

            assert sql is not None, f"Should generate SQL for {dialect.name}"
            assert isinstance(sql, str), f"SQL should be a string for {dialect.name}"
            assert "DROP TABLE" in sql.upper(), f"Should contain DROP TABLE for {dialect.name}"


@pytest.mark.integration
class TestTableIntegration:
    """Integration tests for actual table operations."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            # (SQLDialect.REDSHIFT, "redshift_config")  # Commented out: requires sqlalchemy-redshift package,
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_create_simple_table(self, dialect, config_name, request):
        """Test creating a comprehensive table with all supported column types for each dialect."""
        from sqlutilities.connections import DatabaseConnection

        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Create SQL_TABLE instance with table name
            sql_table = SQL_TABLE(connection=conn, table_name="test_comprehensive_table")

            try:
                # Drop table if exists first
                sql_table.drop_table(if_exists=True)

                # Add primary key column (INTEGER with auto-increment for most dialects)
                sql_table.add_column(name="id", data_type=COLUMNDTYPE.INTEGER, nullable=False, is_identity=True)

                # Numeric types
                sql_table.add_column(name="bigint_col", data_type=COLUMNDTYPE.BIGINT, nullable=True)
                sql_table.add_column(
                    name="decimal_col", data_type=COLUMNDTYPE.DECIMAL, precision=10, scale=2, nullable=True
                )
                sql_table.add_column(name="float_col", data_type=COLUMNDTYPE.FLOAT, nullable=True)
                sql_table.add_column(name="double_col", data_type=COLUMNDTYPE.DOUBLE, nullable=True)

                # String types
                sql_table.add_column(name="varchar_col", data_type=COLUMNDTYPE.VARCHAR, length=255, nullable=True)
                sql_table.add_column(name="char_col", data_type=COLUMNDTYPE.CHAR, length=10, nullable=True)
                sql_table.add_column(name="text_col", data_type=COLUMNDTYPE.TEXT, nullable=True)

                # Date/Time types
                sql_table.add_column(name="date_col", data_type=COLUMNDTYPE.DATE, nullable=True)
                sql_table.add_column(name="timestamp_col", data_type=COLUMNDTYPE.TIMESTAMP, nullable=True)

                # Boolean type
                sql_table.add_column(name="boolean_col", data_type=COLUMNDTYPE.BOOLEAN, nullable=True)

                # Binary type (if supported)
                if dialect not in [SQLDialect.BIGQUERY]:  # BigQuery has different binary handling
                    sql_table.add_column(name="blob_col", data_type=COLUMNDTYPE.BLOB, nullable=True)

                # JSON type for dialects that support it
                if dialect in [SQLDialect.POSTGRES, SQLDialect.MYSQL, SQLDialect.SQLSERVER]:
                    sql_table.add_column(name="json_col", data_type=COLUMNDTYPE.JSON, nullable=True)

                # Add primary key constraint (BigQuery doesn't support PRIMARY KEY enforcement)
                if dialect != SQLDialect.BIGQUERY:
                    sql_table.add_primary_key_constraint("pk_test_comprehensive", ["id"])

                # Create the table
                created = sql_table.create_table(if_exists="fail")
                assert created, f"Failed to create comprehensive table for {dialect.name}"

                # Verify table exists
                exists = sql_table.exists()
                assert exists, f"Table should exist after creation for {dialect.name}"

                # Verify columns were created by getting table info
                columns = sql_table.get_columns()
                assert len(columns) > 0, f"Should have columns for {dialect.name}"

                # Verify we have at least the essential columns
                column_names = [col["name"].lower() for col in columns]
                assert "id" in column_names, f"Should have 'id' column for {dialect.name}"
                assert any("varchar" in name for name in column_names), f"Should have varchar column for {dialect.name}"
                assert any(
                    "decimal" in name or "numeric" in name for name in column_names
                ), f"Should have decimal/numeric column for {dialect.name}"

                print(f"✅ {dialect.name}: Created table with {len(columns)} columns")

            finally:
                # Clean up
                try:
                    sql_table.drop_table(if_exists=True)
                except Exception as e:
                    print(f"Warning: Failed to drop test_comprehensive_table for {dialect.name}: {e}")

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            # (SQLDialect.REDSHIFT, "redshift_config")  # Commented out: requires sqlalchemy-redshift package,
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_drop_table_with_if_exists(self, dialect, config_name, request):
        """Test DROP TABLE IF EXISTS functionality for ALL dialects."""
        from sqlutilities.connections import DatabaseConnection

        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Create SQL_TABLE instance
            sql_table = SQL_TABLE(connection=conn, table_name="test_drop_if_exists")

            try:
                # Test 1: Drop non-existent table with if_exists=True (should not error)
                dropped = sql_table.drop_table(if_exists=True)
                assert (
                    dropped
                ), f"drop_table(if_exists=True) should succeed even if table doesn't exist for {dialect.name}"

                # Test 2: Create table, then drop it with if_exists=True
                sql_table.add_column(name="id", data_type=COLUMNDTYPE.INTEGER)
                sql_table.create_table(if_exists="fail")

                assert sql_table.exists(), f"Table should exist after creation for {dialect.name}"

                dropped = sql_table.drop_table(if_exists=True)
                assert dropped, f"Should drop existing table for {dialect.name}"
                assert not sql_table.exists(), f"Table should not exist after drop for {dialect.name}"

                # Test 3: Drop again with if_exists=True (should not error)
                dropped = sql_table.drop_table(if_exists=True)
                assert dropped, f"Should handle dropping non-existent table with if_exists=True for {dialect.name}"

                print(f"✅ {dialect.name}: DROP TABLE IF EXISTS works correctly")

            finally:
                # Ensure cleanup
                try:
                    sql_table.drop_table(if_exists=True)
                except Exception:
                    pass

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            # (SQLDialect.BIGQUERY, "bigquery_config"),  # Commented out: BigQuery free tier doesn't support INSERT (DML)
            # (SQLDialect.REDSHIFT, "redshift_config"),  # Commented out: requires sqlalchemy-redshift package
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_create_table_with_data_insertion(self, dialect, config_name, request):
        """Test creating a table and inserting data to verify column types work."""
        from datetime import datetime

        from sqlutilities.connections import DatabaseConnection

        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Create SQL_TABLE instance
            sql_table = SQL_TABLE(connection=conn, table_name="test_data_insertion")

            try:
                # Drop table if exists
                sql_table.drop_table(if_exists=True)

                # Add columns with various types and features
                sql_table.add_column(name="id", data_type=COLUMNDTYPE.INTEGER, nullable=False, is_identity=True)
                sql_table.add_column(name="name", data_type=COLUMNDTYPE.VARCHAR, length=100, nullable=False)
                sql_table.add_column(
                    name="amount",
                    data_type=COLUMNDTYPE.DECIMAL,
                    precision=10,
                    scale=2,
                    nullable=True,
                    default_value="0.00",
                )
                sql_table.add_column(
                    name="is_active",
                    data_type=COLUMNDTYPE.BOOLEAN,
                    nullable=False,
                    default_value=(
                        "1"
                        if dialect in [SQLDialect.MYSQL, SQLDialect.SQLITE, SQLDialect.SQLSERVER, SQLDialect.ORACLE]
                        else "TRUE"
                    ),
                )
                sql_table.add_column(name="created_at", data_type=COLUMNDTYPE.TIMESTAMP, nullable=True)

                # Add primary key (BigQuery doesn't support PRIMARY KEY enforcement)
                if dialect != SQLDialect.BIGQUERY:
                    sql_table.add_primary_key_constraint("pk_test_data", ["id"])

                # Create the table
                created = sql_table.create_table(if_exists="fail")
                assert created, f"Failed to create table for {dialect.name}"

                # Insert test data
                if dialect == SQLDialect.ORACLE:
                    # Oracle requires quoted column names when table was created with quotes
                    insert_sql = """
                    INSERT INTO {table} ("name", "amount", "is_active", "created_at")
                    VALUES (:1, :2, :3, :4)
                    """.format(
                        table=sql_table.full_table_name
                    )
                    params = ("Test Item", 99.99, 1, datetime.now())
                elif dialect == SQLDialect.BIGQUERY:
                    # BigQuery uses named parameters with @param syntax
                    # Note: datetime must be ISO format string for BigQuery JSON serialization
                    insert_sql = """
                    INSERT INTO {table} (name, amount, is_active, created_at)
                    VALUES (@name, @amount, @is_active, @created_at)
                    """.format(
                        table=sql_table.full_table_name
                    )
                    params = {
                        "name": "Test Item",
                        "amount": 99.99,
                        "is_active": True,
                        "created_at": datetime.now().isoformat(),
                    }
                elif dialect in [SQLDialect.SQLSERVER, SQLDialect.SQLITE]:
                    insert_sql = """
                    INSERT INTO {table} (name, amount, is_active, created_at)
                    VALUES (?, ?, ?, ?)
                    """.format(
                        table=sql_table.full_table_name
                    )
                    params = ("Test Item", 99.99, 1, datetime.now())
                else:  # MySQL, Postgres, Redshift
                    insert_sql = """
                    INSERT INTO {table} (name, amount, is_active, created_at)
                    VALUES (%s, %s, %s, %s)
                    """.format(
                        table=sql_table.full_table_name
                    )
                    params = ("Test Item", 99.99, True, datetime.now())

                conn.execute_query(insert_sql, params)

                # Verify data was inserted
                if dialect == SQLDialect.ORACLE:
                    # Oracle requires quoted column names when table was created with quotes
                    select_sql = f'SELECT "name", "amount", "is_active" FROM {sql_table.full_table_name}'
                else:
                    select_sql = f"SELECT name, amount, is_active FROM {sql_table.full_table_name}"
                rows = conn.execute_query(select_sql)

                assert len(rows) > 0, f"Should have inserted data for {dialect.name}"
                assert rows[0][0] == "Test Item", f"Should retrieve correct name for {dialect.name}"

                print(f"✅ {dialect.name}: Successfully inserted and retrieved data")

            finally:
                # Clean up
                try:
                    sql_table.drop_table(if_exists=True)
                except Exception as e:
                    print(f"Warning: Failed to drop test_data_insertion for {dialect.name}: {e}")

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dialect,config_name",
        [
            (SQLDialect.MYSQL, "mysql_config"),
            (SQLDialect.POSTGRES, "postgres_config"),
            (SQLDialect.ORACLE, "oracle_config"),
            (SQLDialect.SQLSERVER, "sqlserver_config"),
            (SQLDialect.BIGQUERY, "bigquery_config"),
            # (SQLDialect.REDSHIFT, "redshift_config")  # Commented out: requires sqlalchemy-redshift package,
            (SQLDialect.SQLITE, "sqlite_config"),
        ],
    )
    def test_table_exists_check(self, dialect, config_name, request):
        """Test the exists() method returns correct results for ALL dialects."""
        from sqlutilities.connections import DatabaseConnection

        config = request.getfixturevalue(config_name)

        with DatabaseConnection(dialect=dialect, **config) as conn:
            # Test 1: Check for a table that definitely doesn't exist
            nonexistent_table = SQL_TABLE(connection=conn, table_name="nonexistent_table_xyz_12345")
            exists = nonexistent_table.exists()
            assert not exists, f"Non-existent table should return False for {dialect.name}"

            # Test 2: Check for a table we create
            sql_table = SQL_TABLE(connection=conn, table_name="test_exists_verification")

            try:
                # Ensure clean state
                sql_table.drop_table(if_exists=True)

                # Verify it doesn't exist before creation
                assert not sql_table.exists(), f"Table should not exist before creation for {dialect.name}"

                # Create table
                sql_table.add_column(name="id", data_type=COLUMNDTYPE.INTEGER)
                sql_table.create_table(if_exists="fail")

                # Verify it exists after creation
                assert sql_table.exists(), f"Table should exist after creation for {dialect.name}"

                # Drop it
                sql_table.drop_table(if_exists=False)

                # Verify it doesn't exist after drop
                assert not sql_table.exists(), f"Table should not exist after drop for {dialect.name}"

                print(f"✅ {dialect.name}: exists() method works correctly")

            finally:
                try:
                    sql_table.drop_table(if_exists=True)
                except Exception:
                    pass
