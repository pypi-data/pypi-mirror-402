# Contributing to SQLUtils-Python

Thank you for your interest in contributing to SQLUtils-Python! This document provides guidelines and requirements for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)
- [Commit Message Guidelines](#commit-message-guidelines)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Prioritize code quality and maintainability

## Getting Started

1. **Fork the repository**
   ```bash
   # On GitHub, click "Fork" button
   git clone https://github.com/YOUR_USERNAME/SQLUtils-Python.git
   cd SQLUtils-Python
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # OR
   git checkout -b bugfix/issue-number-description
   ```

3. **Set up your development environment** (see [Development Setup](#development-setup))

## Development Setup

### 1. Install Core Dependencies

```bash
# Install core requirements
pip install -r requirements.txt

# Install test dependencies
pip install -r UNIT_TESTS/requirements-test.txt
```

### 2. Install Database Drivers (Optional)

Install drivers for databases you want to test:

```bash
# Install all commonly used drivers
pip install psycopg2-binary pymysql pyodbc oracledb
```

See [INSTALLATION.md](INSTALLATION.md) for detailed driver installation instructions.

### 3. Set Up Test Databases

The test suite uses Docker containers for integration testing:

```bash
# Start all test databases
cd tst/docker
bash db_test.sh start

# Check status
bash db_test.sh status

# Stop databases when done
bash db_test.sh stop
```

### 4. Configure Environment (Optional)

Create a `.env` file for custom database connection settings:

```bash
# Optional: Custom test database configurations
DB_MYSQL_HOST=localhost
DB_MYSQL_PORT=3306
DB_POSTGRES_HOST=localhost
DB_POSTGRES_PORT=5432
# ... etc
```

## Code Style Guidelines

SQLUtils-Python follows strict code style guidelines to ensure consistency and readability.

### Python Style Guide

We follow **PEP 8** with the following specifics:

#### Formatting

- **Line Length**: Maximum 120 characters
- **Indentation**: 4 spaces (no tabs)
- **Blank Lines**:
  - 2 blank lines between top-level functions/classes
  - 1 blank line between class methods
- **Quotes**: Use double quotes `"` for strings (unless single quotes avoid escaping)

#### Naming Conventions

```python
# Classes: PascalCase
class DatabaseConnection:
    pass

# Functions and methods: snake_case
def execute_query(sql: str) -> List[Tuple]:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 5
DEFAULT_TIMEOUT = 30

# Private methods/attributes: leading underscore
def _internal_method(self):
    pass

# Enums: PascalCase class, UPPER_SNAKE_CASE values
class SQLDialect(Enum):
    POSTGRES = "postgres"
    MYSQL = "mysql"
```

#### Type Hints

**Always use type hints** for function parameters and return values:

```python
from typing import Optional, List, Dict, Tuple, Any

def execute_query(
    self,
    query: str,
    parameters: Optional[Tuple] = None,
    fetch_results: bool = True
) -> List[Tuple[Any, ...]]:
    """Execute a query and return results."""
    pass
```

#### Imports

Organize imports in the following order:

```python
# 1. Standard library imports
import os
import sys
from typing import Optional, List

# 2. Third-party imports
from CoreUtilities import get_logger

# 3. Local imports
from core.enums import SQLDialect
from core.types import COLUMNDTYPE
```

Use `isort` to automatically organize imports:
```bash
isort src/
```

### Documentation Style (NumPy Docstrings)

**All public modules, classes, methods, and functions must have NumPy-style docstrings.**

#### Module Docstring

```python
"""
Database connection management module.

This module provides the DatabaseConnection class for managing connections
to multiple SQL database systems with automatic driver selection and
connection pooling.

Classes
-------
DatabaseConnection
    Main class for database connections with multi-dialect support.

Examples
--------
>>> from connections import DatabaseConnection
>>> from core.enums import SQLDialect
>>> conn = DatabaseConnection(
...     dialect=SQLDialect.POSTGRES,
...     host="localhost",
...     database="mydb"
... )
"""
```

#### Class Docstring

```python
class DatabaseConnection:
    """
    Unified database connection interface supporting multiple SQL dialects.

    This class provides a consistent API for connecting to and interacting with
    various SQL database systems including PostgreSQL, MySQL, Oracle, SQL Server,
    SQLite, Redshift, and BigQuery.

    Parameters
    ----------
    dialect : SQLDialect
        The SQL dialect/database type to connect to.
    host : str, optional
        Database server hostname or IP address.
    port : int, optional
        Database server port number.
    database : str, optional
        Database name to connect to.
    user : str, optional
        Username for authentication.
    password : str, optional
        Password for authentication.

    Attributes
    ----------
    dialect : SQLDialect
        The SQL dialect being used.
    connection : Any
        The underlying database connection object.
    is_connected : bool
        Whether the connection is currently active.

    Raises
    ------
    ValueError
        If required connection parameters are missing.
    ConnectionError
        If connection to the database fails.

    Examples
    --------
    >>> with DatabaseConnection(
    ...     dialect=SQLDialect.POSTGRES,
    ...     host="localhost",
    ...     database="mydb",
    ...     user="user",
    ...     password="pass"
    ... ) as conn:
    ...     results = conn.execute_query("SELECT * FROM users")
    ...     for row in results:
    ...         print(row)

    See Also
    --------
    Transaction : For transaction management with retry logic.
    SQL_TABLE : For table creation and management.
    """
```

#### Method/Function Docstring

```python
def execute_query(
    self,
    query: str,
    parameters: Optional[Tuple] = None,
    fetch_results: bool = True
) -> List[Tuple[Any, ...]]:
    """
    Execute a SQL query and optionally fetch results.

    Parameters
    ----------
    query : str
        The SQL query to execute.
    parameters : tuple, optional
        Parameters for parameterized queries. Default is None.
    fetch_results : bool, optional
        Whether to fetch and return results. Default is True.

    Returns
    -------
    List[Tuple[Any, ...]]
        List of result rows as tuples. Empty list if fetch_results is False.

    Raises
    ------
    QueryExecutionError
        If query execution fails.
    ValueError
        If query is empty or invalid.

    Examples
    --------
    >>> results = conn.execute_query(
    ...     "SELECT * FROM users WHERE id = %s",
    ...     (123,)
    ... )
    >>> print(results[0])
    (123, 'John Doe', 'john@example.com')

    Notes
    -----
    This method automatically handles parameterization based on the database
    dialect. Always use parameterized queries to prevent SQL injection.
    """
```

### Inline Comments

Use inline comments to explain **WHY**, not **WHAT**:

```python
# Good: Explains reasoning
# Oracle requires DEFAULT before NOT NULL (syntax requirement)
if column.default_value:
    col_def += f" DEFAULT {column.default_value}"
if not column.nullable:
    col_def += " NOT NULL"

# Bad: States the obvious
# Add default value
if column.default_value:
    col_def += f" DEFAULT {column.default_value}"
```

### Code Quality Tools

We use the following tools to enforce code quality:

```bash
# Format code with Black (line length 120)
black --line-length 120 src/

# Sort imports
isort src/

# Lint with flake8
flake8 src/ --max-line-length=120

# Type check with mypy
mypy src/

# Run all checks
black --line-length 120 src/ && isort src/ && flake8 src/ --max-line-length=120 && mypy src/
```

## Testing Requirements

### Test Coverage

- **Minimum coverage**: 80% overall
- **Critical modules**: 90%+ coverage (connections, transactions, tables)
- All new features **must** include tests
- All bug fixes **must** include regression tests

### Running Tests

```bash
# Run all tests
python UNIT_TESTS/run_tests.py

# Run specific test file
pytest UNIT_TESTS/test_connections.py -v

# Run specific test method
pytest UNIT_TESTS/test_connections.py::test_basic_connection -v

# Run tests for specific database
pytest UNIT_TESTS/ -k mysql -v
pytest UNIT_TESTS/ -k postgres -v
pytest UNIT_TESTS/ -k oracle -v

# Run only unit tests (no database required)
pytest UNIT_TESTS/ -m unit -v

# Skip integration tests
pytest UNIT_TESTS/ --skip-integration -v

# Run with coverage
pytest UNIT_TESTS/ --cov=src --cov-report=html
```

### Writing Tests

#### Test Structure

Use pytest and follow this structure:

```python
import pytest
from connections import DatabaseConnection
from core.enums import SQLDialect

class TestDatabaseConnection:
    """Tests for DatabaseConnection class."""

    def test_basic_connection(self):
        """Test basic database connection."""
        # Arrange
        config = {
            'dialect': SQLDialect.POSTGRES,
            'host': 'localhost',
            'database': 'test_db'
        }

        # Act
        with DatabaseConnection(**config) as conn:
            result = conn.execute_query("SELECT 1")

        # Assert
        assert result is not None
        assert len(result) == 1

    @pytest.mark.parametrize("dialect", [
        SQLDialect.MYSQL,
        SQLDialect.POSTGRES,
        SQLDialect.SQLSERVER
    ])
    def test_multi_dialect_support(self, dialect):
        """Test that multiple dialects are supported."""
        # Test implementation
        pass
```

#### Test Categories

Use pytest marks to categorize tests:

```python
@pytest.mark.unit
def test_type_validation():
    """Unit test for type validation."""
    pass

@pytest.mark.integration
def test_database_connection():
    """Integration test requiring database."""
    pass

@pytest.mark.slow
def test_large_dataset():
    """Slow test for large datasets."""
    pass
```

#### Test Fixtures

Use fixtures for common setup:

```python
@pytest.fixture
def db_connection():
    """Fixture providing a database connection."""
    conn = DatabaseConnection(
        dialect=SQLDialect.POSTGRES,
        host="localhost",
        database="test_db"
    )
    conn.connect()
    yield conn
    conn.disconnect()

def test_with_fixture(db_connection):
    """Test using connection fixture."""
    result = db_connection.execute_query("SELECT 1")
    assert result is not None
```

#### Mocking

Use mocks for external dependencies:

```python
from unittest.mock import Mock, patch

def test_connection_failure():
    """Test handling of connection failures."""
    with patch('psycopg2.connect') as mock_connect:
        mock_connect.side_effect = ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            conn = DatabaseConnection(dialect=SQLDialect.POSTGRES)
            conn.connect()
```

### Test Naming

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<what_is_being_tested>`

Use descriptive names:

```python
# Good
def test_execute_query_with_parameters_prevents_sql_injection():
    pass

def test_transaction_retries_on_deadlock():
    pass

# Bad
def test_query():
    pass

def test_transaction():
    pass
```

## Documentation Standards

### README Updates

If your contribution:
- Adds new features → Update README with examples
- Changes API → Update relevant README sections
- Adds new database support → Update supported databases table

### Docstring Requirements

Every public API element must have:
- Summary line (one sentence)
- Parameters section (if applicable)
- Returns section (if applicable)
- Raises section (if applicable)
- Examples section (recommended)
- Notes section (if needed)

### Code Comments

- Use inline comments sparingly
- Explain **WHY**, not **WHAT**
- Document complex algorithms or business logic
- Flag TODOs, FIXMEs, or HACKs clearly

```python
# TODO: Add support for custom retry strategies
# FIXME: Oracle BLOB handling needs optimization
# HACK: Workaround for MySQL 5.7 datetime precision issue
```

## Pull Request Process

### Before Submitting

1. **Run all tests**
   ```bash
   python UNIT_TESTS/run_tests.py
   ```

2. **Run code quality checks**
   ```bash
   black --line-length 120 src/ && isort src/ && flake8 src/ --max-line-length=120
   ```

3. **Update documentation**
   - Add/update docstrings
   - Update README if needed
   - Add examples for new features

4. **Write/update tests**
   - Ensure 80%+ coverage for new code
   - Add integration tests for database features
   - Add unit tests for utility functions

### Submitting Pull Request

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create pull request** on GitHub with:
   - Clear, descriptive title
   - Detailed description of changes
   - Reference to related issues
   - Screenshots/examples if applicable

3. **PR Description Template**
   ```markdown
   ## Description
   Brief description of what this PR does.

   ## Type of Change
   - [ ] Bug fix (non-breaking change fixing an issue)
   - [ ] New feature (non-breaking change adding functionality)
   - [ ] Breaking change (fix or feature causing existing functionality to change)
   - [ ] Documentation update

   ## Testing
   - [ ] All existing tests pass
   - [ ] New tests added for new functionality
   - [ ] Integration tests pass for all supported databases
   - [ ] Code coverage maintained/improved

   ## Checklist
   - [ ] Code follows project style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings generated
   - [ ] Tests added that prove fix/feature works

   ## Related Issues
   Fixes #(issue number)
   ```

### Review Process

- Maintainers will review your PR
- Address feedback and requested changes
- Once approved, PR will be merged

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
# Good commit messages
git commit -m "feat(connections): add support for connection pooling"
git commit -m "fix(oracle): correct column order in get_columns() query"
git commit -m "docs(readme): add installation instructions for macOS"
git commit -m "test(transactions): add retry logic integration tests"

# Bad commit messages
git commit -m "fixed bug"
git commit -m "updates"
git commit -m "WIP"
```

### Detailed Example

```
feat(tables): add support for check constraints

Add support for CHECK constraints in table definitions across all
supported dialects. Includes automatic translation of constraint
syntax for dialect-specific requirements.

- Add add_check_constraint() method to SQL_TABLE
- Implement dialect-specific CHECK syntax generation
- Add integration tests for all 7 database systems
- Update documentation with examples

Fixes #123
```

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Join discussions on GitHub Discussions
- Be patient and respectful

---

**Thank you for contributing to SQLUtils-Python!** 🎉
