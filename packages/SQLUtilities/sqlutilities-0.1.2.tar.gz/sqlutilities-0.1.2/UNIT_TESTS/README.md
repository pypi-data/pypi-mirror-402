# SQLUtils Unit Tests

Comprehensive test suite for the SQLUtils-Python library, supporting multiple database dialects and test scenarios.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Database Dialects](#database-dialects)
- [Coverage Reports](#coverage-reports)
- [Writing Tests](#writing-tests)
- [Troubleshooting](#troubleshooting)

## Overview

This test suite provides comprehensive coverage for all SQLUtils modules:

- **Core Module**: SQLDialect, DatabaseObjectType, COLUMNDTYPE enums and types
- **Drivers Module**: Database driver registry, factory, and connection building
- **Validation Module**: SQL identifier validation and normalization
- **Connections Module**: Database connection management
- **Transactions Module**: Transaction handling with retry logic
- **Errors Module**: SQL error detection and classification
- **Tables Module**: Table and column definitions, DDL operations

## Test Structure

```
UNIT_TESTS/
├── conftest.py                      # Pytest configuration and fixtures
├── test_core_enums.py              # Tests for core.enums module
├── test_core_types.py              # Tests for core.types module
├── test_drivers.py                  # Tests for drivers module
├── test_validation_identifiers.py   # Tests for validation module
├── test_connections.py              # Tests for connections module
├── test_transactions.py             # Tests for transactions module
├── test_errors.py                   # Tests for errors module
├── test_tables.py                   # Tests for tables module
├── run_tests.py                     # Test runner script
└── README.md                        # This file
```

## Prerequisites

### Required Dependencies

```bash
pip install pytest pytest-cov python-dotenv
```

### Optional Dependencies (for dialect-specific tests)

```bash
# MySQL
pip install pymysql mysql-connector-python

# PostgreSQL
pip install psycopg2-binary psycopg

# Oracle
pip install oracledb cx_Oracle

# SQL Server
pip install pyodbc pymssql

# BigQuery
pip install google-cloud-bigquery

# SQLite (built-in, no installation needed)
```

### Docker Containers (for integration tests)

The integration tests require database containers to be running. Start all containers:

```bash
cd tst/docker
bash db_test.sh start
```

Check container status:

```bash
bash db_test.sh status
```

Stop all containers:

```bash
bash db_test.sh stop
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd SQLUtils-Python
```

2. Install test dependencies:
```bash
pip install pytest pytest-cov python-dotenv
```

3. Install database drivers (optional, based on what you want to test):
```bash
pip install pymysql psycopg2-binary
```

## Running Tests

### Using the Test Runner Script (Recommended)

The `run_tests.py` script provides a convenient interface:

```bash
# Run all tests
python UNIT_TESTS/run_tests.py

# Run tests for specific dialect
python UNIT_TESTS/run_tests.py --dialect mysql
python UNIT_TESTS/run_tests.py --dialect postgres

# Run only unit tests (no integration tests)
python UNIT_TESTS/run_tests.py --unit-only

# Run only integration tests
python UNIT_TESTS/run_tests.py --integration

# Run tests for specific module
python UNIT_TESTS/run_tests.py --module connections
python UNIT_TESTS/run_tests.py --module core_types

# Run with verbose output
python UNIT_TESTS/run_tests.py -v

# Run with coverage report
python UNIT_TESTS/run_tests.py --coverage

# Check container status before running
python UNIT_TESTS/run_tests.py --check-containers

# Combine options
python UNIT_TESTS/run_tests.py --dialect postgres --integration -v
```

### Using pytest Directly

```bash
# Run all tests
pytest UNIT_TESTS/

# Run with verbose output
pytest UNIT_TESTS/ -v

# Run tests for specific dialect
pytest UNIT_TESTS/ --dialect=mysql

# Run only unit tests
pytest UNIT_TESTS/ -m unit

# Run only integration tests
pytest UNIT_TESTS/ -m integration

# Skip integration tests
pytest UNIT_TESTS/ --skip-integration

# Run specific test file
pytest UNIT_TESTS/test_core_enums.py

# Run specific test
pytest UNIT_TESTS/test_core_enums.py::TestSQLDialect::test_all_dialects_exist

# Run with coverage
pytest UNIT_TESTS/ --cov=src --cov-report=html
```

## Test Categories

### Unit Tests

Pure unit tests without external dependencies. Fast and run without database connections.

```bash
# Run only unit tests
python UNIT_TESTS/run_tests.py --unit-only

# Or with pytest
pytest UNIT_TESTS/ -m unit
```

### Integration Tests

Tests that require actual database connections. These tests:
- Connect to real databases (via Docker containers)
- Execute actual SQL statements
- Test end-to-end functionality

```bash
# Run only integration tests
python UNIT_TESTS/run_tests.py --integration

# Or with pytest
pytest UNIT_TESTS/ -m integration
```

**Note**: Integration tests require database containers to be running. Start them with:
```bash
cd tst/docker && bash db_test.sh start
```

## Database Dialects

### Supported Dialects

- **MySQL** (Port 3306)
- **PostgreSQL** (Port 54333)
- **Oracle XE** (Port 15210)
- **SQL Server** (Port 14333)
- **BigQuery Emulator** (Port 9050)
- **Redshift Emulator** (Port 5444)
- **SQLite** (In-memory, no container needed)

### Running Dialect-Specific Tests

```bash
# Test specific dialect
python UNIT_TESTS/run_tests.py --dialect mysql
python UNIT_TESTS/run_tests.py --dialect postgres
python UNIT_TESTS/run_tests.py --dialect oracle
python UNIT_TESTS/run_tests.py --dialect sqlserver
python UNIT_TESTS/run_tests.py --dialect bigquery
python UNIT_TESTS/run_tests.py --dialect redshift
python UNIT_TESTS/run_tests.py --dialect sqlite

# Test all dialects
python UNIT_TESTS/run_tests.py --dialect all
```

### Dialect Markers

Tests can be marked for specific dialects:

```python
@pytest.mark.mysql
def test_mysql_specific_feature():
    pass

@pytest.mark.postgres
def test_postgres_specific_feature():
    pass
```

## Coverage Reports

### Generate Coverage Report

```bash
# Run with coverage
python UNIT_TESTS/run_tests.py --coverage

# Or with pytest
pytest UNIT_TESTS/ --cov=src --cov-report=html --cov-report=term
```

### View HTML Coverage Report

After running with coverage, open the HTML report:

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage by Module

```bash
# Coverage for specific module
pytest UNIT_TESTS/test_connections.py --cov=src/connections --cov-report=term
```

## Writing Tests

### Test Structure

```python
import pytest
from module import ClassName

class TestClassName:
    """Test cases for ClassName."""

    @pytest.mark.unit
    def test_something(self):
        """Test description."""
        # Arrange
        obj = ClassName()

        # Act
        result = obj.method()

        # Assert
        assert result == expected_value
```

### Using Fixtures

```python
@pytest.mark.integration
@pytest.mark.mysql
def test_with_mysql(mysql_config):
    """Test using MySQL configuration fixture."""
    assert mysql_config["host"] == "localhost"
    assert mysql_config["port"] == 3306
```

### Parametrized Tests

```python
@pytest.mark.unit
@pytest.mark.parametrize("input,expected", [
    ("test", "TEST"),
    ("hello", "HELLO"),
])
def test_uppercase(input, expected):
    """Test uppercase conversion."""
    assert input.upper() == expected
```

### Integration Test Example

```python
@pytest.mark.integration
@pytest.mark.sqlite
def test_create_table(temp_sqlite_db):
    """Test creating a table in SQLite."""
    from connections import DatabaseConnection
    from tables import SQL_TABLE, ColumnDefinition
    from core import COLUMNDTYPE, SQLDialect

    # Connect to database
    conn = DatabaseConnection(
        database=temp_sqlite_db,
        dialect=SQLDialect.SQLITE
    )

    # Define table
    table = SQL_TABLE(
        name="test_table",
        columns=[
            ColumnDefinition(
                name="id",
                data_type=COLUMNDTYPE.INTEGER,
                dialect=SQLDialect.SQLITE
            )
        ]
    )

    # Create table
    table.create(conn)

    # Verify
    assert table.exists(conn)
```

## Troubleshooting

### Tests Fail with "Container not running"

**Solution**: Start the database containers:

```bash
cd tst/docker
bash db_test.sh start
```

### Import Errors

**Solution**: Ensure you're in the project root and the src directory is in the Python path:

```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
```

Or run tests using the test runner which handles this automatically:

```bash
python UNIT_TESTS/run_tests.py
```

### Driver Not Available

**Solution**: Install the required database driver:

```bash
# For MySQL
pip install pymysql

# For PostgreSQL
pip install psycopg2-binary

# For Oracle
pip install oracledb
```

Or skip integration tests:

```bash
python UNIT_TESTS/run_tests.py --unit-only
```

### Connection Refused

**Solution**: Check if containers are running and ports are correct:

```bash
cd tst/docker
bash db_test.sh status
```

Verify port mappings in `tst/docker/.env` match your test configuration.

### Permission Errors on Test Runner

**Solution**: Make the test runner executable:

```bash
chmod +x UNIT_TESTS/run_tests.py
```

## Test Configuration

### Environment Variables

Test configuration is loaded from `tst/docker/.env`:

```bash
# MySQL
MYSQL_HOST_PORT=3306
MYSQL_DATABASE=mydatabase
MYSQL_USER=myuser
MYSQL_PASSWORD=mypassword

# PostgreSQL
POSTGRES_HOST_PORT=54333
POSTGRES_DB=testdb
POSTGRES_USER=testuser
POSTGRES_PASSWORD=YourStrong!Passw0rd

# ... and more
```

### Pytest Configuration

Create `pytest.ini` in the project root for custom configuration:

```ini
[pytest]
testpaths = UNIT_TESTS
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Pure unit tests without external dependencies
    integration: Integration tests requiring database connections
    mysql: MySQL-specific tests
    postgres: PostgreSQL-specific tests
    oracle: Oracle-specific tests
    sqlserver: SQL Server-specific tests
    bigquery: BigQuery-specific tests
    redshift: Redshift-specific tests
    sqlite: SQLite-specific tests
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.3
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: testdb
        ports:
          - 3306:3306

      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: python UNIT_TESTS/run_tests.py --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Best Practices

1. **Write tests first** (TDD approach when possible)
2. **Keep tests independent** - each test should be able to run alone
3. **Use descriptive test names** - test name should describe what is being tested
4. **Mark tests appropriately** - use `@pytest.mark.unit` or `@pytest.mark.integration`
5. **Use fixtures** for common setup code
6. **Clean up after tests** - especially for integration tests
7. **Don't test implementation details** - test behavior, not internals
8. **Parametrize when possible** - avoid duplicate test code

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing test examples in the test files
- Review pytest documentation: https://docs.pytest.org/

---

**Happy Testing!** 🧪✨
