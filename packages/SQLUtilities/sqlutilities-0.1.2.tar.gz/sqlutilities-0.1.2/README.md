# SQLUtils-Python

A comprehensive, production-ready Python library for unified database operations across multiple SQL database systems. SQLUtils provides a consistent, type-safe interface for working with MySQL, PostgreSQL, Oracle, SQL Server, SQLite, Redshift, and BigQuery.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

### 🔌 Multi-Database Support

- **7 Database Systems**: MySQL, PostgreSQL, Oracle, SQL Server, SQLite, Amazon Redshift, Google BigQuery
- **Automatic Driver Detection**: Intelligently selects the best available driver for each database
- **Unified API**: Write once, run anywhere with consistent interface across all databases
- **Dialect-Aware**: Automatically handles SQL dialect differences and type mappings

### 🔄 Robust Transaction Management

- **Automatic Retry Logic**: Configurable retry with exponential backoff and jitter
- **Error Classification**: Intelligent categorization of database errors (transient, permanent, deadlock, etc.)
- **ACID Compliance**: Full transaction support with configurable isolation levels
- **Performance Monitoring**: Built-in metrics for transaction duration, retry counts, and error tracking

### 🏗️ Advanced Table Management

- **Schema-Aware Operations**: Create, modify, and query table structures with full metadata support
- **Cross-Dialect SQL Generation**: Generate database-specific DDL automatically
- **Column Type Mapping**: Comprehensive type system with 50+ column types mapped across dialects
- **Constraint Support**: Primary keys, foreign keys, unique constraints, check constraints, and indexes

### ✅ Enterprise-Grade Reliability

- **Connection Pooling**: Efficient connection management and reuse
- **Error Recovery**: Automatic retry for transient failures
- **Comprehensive Logging**: Detailed logging with emoji-enhanced output
- **Type Safety**: Full type hints and validation throughout

### 🛡️ Security & Validation

- **SQL Injection Protection**: Parameterized queries with dialect-specific parameter styles
- **Identifier Validation**: Reserved word checking and SQL injection prevention
- **Secure Credential Handling**: Environment variable support for sensitive data
- **SSL/TLS Support**: Encrypted connections for supported databases

## Supported Databases

| Database            | Versions | Drivers                                                  | Status             |
| ------------------- | -------- | -------------------------------------------------------- | ------------------ |
| **PostgreSQL**      | 9.6+     | psycopg2, psycopg3, pg8000, connectorx                   | ✅ Fully Supported |
| **MySQL**           | 5.7+     | mysql-connector-python, pymysql, mysqlclient, connectorx | ✅ Fully Supported |
| **Oracle**          | 12c+     | oracledb, cx_Oracle                                      | ✅ Fully Supported |
| **SQL Server**      | 2016+    | pyodbc, pymssql                                          | ✅ Fully Supported |
| **SQLite**          | 3.8+     | sqlite3 (built-in)                                       | ✅ Fully Supported |
| **Amazon Redshift** | All      | psycopg2, redshift_connector                             | ✅ Fully Supported |
| **Google BigQuery** | All      | google-cloud-bigquery                                    | ✅ Fully Supported |

## Installation

### Quick Start

```bash
# Install core package
pip install -r requirements.txt

# Install database drivers (pure Python - no system dependencies)
pip install pymysql psycopg2-binary pymssql oracledb
```

### Database Drivers

SQLUtils supports multiple drivers for each database. Choose based on your needs:

| Database       | Pure Python Drivers                     | High-Performance Drivers (require system libs) |
| -------------- | --------------------------------------- | ---------------------------------------------- |
| **MySQL**      | `pymysql`, `mysql-connector-python`     | `mysqlclient`                                  |
| **PostgreSQL** | `psycopg2-binary`                       | `psycopg2`                                     |
| **Oracle**     | `oracledb` (thin mode)                  | `cx_Oracle`, `oracledb` (thick mode)           |
| **SQL Server** | `pymssql`                               | `pyodbc`                                       |
| **SQLite**     | Built-in (`sqlite3`)                    | -                                              |
| **Redshift**   | `psycopg2-binary`, `redshift-connector` | -                                              |
| **BigQuery**   | `google-cloud-bigquery`                 | -                                              |

**📖 For detailed installation instructions including system prerequisites, see [docs/INSTALLATION.md](docs/INSTALLATION.md)**

### Example: PostgreSQL + MySQL

```bash
pip install -r requirements.txt
pip install psycopg2-binary pymysql
```

## Quick Start

### Basic Connection

```python
from sqlutilities import DatabaseConnection, SQLDialect

# Simple connection
with DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    host="localhost",
    port=5432,
    database="mydb",
    user="myuser",
    password="mypassword"
) as conn:
    # Execute a query
    results = conn.execute_query("SELECT * FROM users WHERE active = %s", (True,))
    for row in results:
        print(row)
```

### Using Environment Variables

```python
import os
from sqlutilities import DatabaseConnection, SQLDialect

# Load credentials from environment
with DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
) as conn:
    results = conn.execute_query("SELECT COUNT(*) FROM products")
    print(f"Total products: {results[0][0]}")
```

### Transaction Management

```python
from sqlutilities import DatabaseConnection, SQLDialect, TransactionConfig, IsolationLevel
from sqlutilities.transactions import RobustTransaction

# Configure transaction with retry logic
config = TransactionConfig(
    max_retries=5,
    base_retry_delay=1.0,
    isolation_level=IsolationLevel.READ_COMMITTED
)

with DatabaseConnection(dialect=SQLDialect.SQLSERVER, **db_config) as conn:
    with RobustTransaction(conn, config=config) as tx:
        # All operations in this block are transactional
        tx.execute("INSERT INTO orders (customer_id, total) VALUES (?, ?)", (123, 99.99))
        tx.execute("UPDATE inventory SET quantity = quantity - 1 WHERE product_id = ?", (456,))
        # Automatically committed on success, rolled back on error
```

### Table Management

```python
from sqlutilities import DatabaseConnection, SQLDialect, SQL_TABLE, COLUMNDTYPE

with DatabaseConnection(dialect=SQLDialect.ORACLE, **db_config) as conn:
    # Create a table
    table = SQL_TABLE(conn, "employees")

    # Define columns
    table.add_column("id", COLUMNDTYPE.INTEGER, nullable=False, is_identity=True)
    table.add_column("name", COLUMNDTYPE.VARCHAR, length=100, nullable=False)
    table.add_column("email", COLUMNDTYPE.VARCHAR, length=255)
    table.add_column("salary", COLUMNDTYPE.DECIMAL, precision=10, scale=2)
    table.add_column("hire_date", COLUMNDTYPE.DATE, nullable=False)
    table.add_column("is_active", COLUMNDTYPE.BOOLEAN, default_value="1")

    # Add constraints
    table.add_primary_key_constraint("pk_employees", ["id"])
    table.add_unique_constraint("uk_employee_email", ["email"])

    # Create the table
    table.create_table(if_exists='replace')

    # Check if table exists
    if table.exists():
        print(f"Table {table.table_name} created successfully!")

    # Get column information
    columns = table.get_columns()
    for col in columns:
        print(f"Column: {col['name']}, Type: {col['data_type']}")
```

### Cross-Dialect Type Mapping

```python
from sqlutilities import COLUMNDTYPE, SQLDialect

# Automatically maps to database-specific types
decimal_col = COLUMNDTYPE.DECIMAL

# PostgreSQL: DECIMAL(10,2)
pg_type = COLUMNDTYPE.to_sql_string(decimal_col, SQLDialect.POSTGRES, (10, 2))

# Oracle: NUMBER(10,2)
oracle_type = COLUMNDTYPE.to_sql_string(decimal_col, SQLDialect.ORACLE, (10, 2))

# MySQL: DECIMAL(10,2)
mysql_type = COLUMNDTYPE.to_sql_string(decimal_col, SQLDialect.MYSQL, (10, 2))

print(f"PostgreSQL: {pg_type}")
print(f"Oracle: {oracle_type}")
print(f"MySQL: {mysql_type}")
```

### High-Performance Data Loading

Load SQL query results directly into dataframes with multiple backend support:

```python
from sqlutilities import DatabaseConnection, SQLDialect, read_sql

with DatabaseConnection(dialect=SQLDialect.POSTGRES, **db_config) as conn:
    # Polars (default - highest performance)
    df_polars = read_sql("SELECT * FROM large_table WHERE date > '2024-01-01'", conn)

    # Pandas (most compatible)
    df_pandas = read_sql(
        "SELECT * FROM users WHERE age > %s",
        conn,
        parameters=(18,),
        output_format='pandas'
    )

    # Dask (distributed computing for huge datasets)
    df_dask = read_sql(
        "SELECT * FROM massive_table",
        conn,
        output_format='dask',
        dask_partitions=8,
        dask_index_column='id'
    )

    # PyArrow (columnar format)
    table_arrow = read_sql(
        "SELECT * FROM data",
        conn,
        output_format='pyarrow'
    )
```

**Key Features:**

- **ConnectorX acceleration**: Rust-based high-performance loading (automatic)
- **Automatic fallback**: Native driver support if ConnectorX unavailable
- **Multiple backends**: Pandas, Polars, Dask, PyArrow
- **Type inference**: Automatic column type detection across all databases
- **SQLite support**: Special handling for SQLite's dynamic type system

## Documentation

### Core Modules

- **[Connections](sqlutilities/connections/)** - Database connection management with automatic driver selection
- **[Transactions](sqlutilities/transactions/)** - ACID-compliant transactions with retry logic and error handling
- **[Tables](sqlutilities/tables/)** - Table creation, modification, and metadata management
- **[Core Types](sqlutilities/core/)** - SQL data type system with cross-dialect mapping
- **[Drivers](sqlutilities/drivers/)** - Driver registry, connection factory, and type mapping
- **[Download](sqlutilities/download/)** - High-performance data loading with multiple dataframe backends
- **[Validation](sqlutilities/validation/)** - SQL identifier validation and sanitization
- **[Errors](sqlutilities/errors/)** - Error classification and pattern matching

### Key Concepts

#### Database Dialects

SQLUtils supports 7 SQL dialects with automatic handling of differences:

```python
from sqlutilities import SQLDialect

# Available dialects
SQLDialect.MYSQL
SQLDialect.POSTGRES
SQLDialect.ORACLE
SQLDialect.SQLSERVER
SQLDialect.SQLITE
SQLDialect.REDSHIFT
SQLDialect.BIGQUERY
```

#### Column Data Types

Comprehensive type system with 50+ types:

```python
from sqlutilities import COLUMNDTYPE

# Numeric types
COLUMNDTYPE.INTEGER, COLUMNDTYPE.BIGINT, COLUMNDTYPE.DECIMAL
COLUMNDTYPE.FLOAT, COLUMNDTYPE.DOUBLE, COLUMNDTYPE.NUMERIC

# String types
COLUMNDTYPE.VARCHAR, COLUMNDTYPE.CHAR, COLUMNDTYPE.TEXT

# Date/Time types
COLUMNDTYPE.DATE, COLUMNDTYPE.TIME, COLUMNDTYPE.TIMESTAMP
COLUMNDTYPE.DATETIME, COLUMNDTYPE.DATETIME2

# Binary types
COLUMNDTYPE.BLOB, COLUMNDTYPE.BINARY, COLUMNDTYPE.VARBINARY

# Special types
COLUMNDTYPE.JSON, COLUMNDTYPE.UUID, COLUMNDTYPE.BOOLEAN
```

#### Error Handling

Intelligent error classification and automatic retry:

```python
from sqlutilities import TransactionConfig, IsolationLevel

# Configure retry behavior
config = TransactionConfig(
    max_retries=5,                    # Maximum retry attempts
    base_retry_delay=1.0,             # Initial retry delay (seconds)
    max_retry_delay=30.0,             # Maximum retry delay
    exponential_backoff=True,         # Use exponential backoff
    jitter_factor=0.1,                # Add randomness to prevent thundering herd
    isolation_level=IsolationLevel.SERIALIZABLE
)
```

## Architecture

```
SQLUtils-Python/
├── sqlutilities/
│   ├── __init__.py           # Package exports and public API
│   ├── connections/          # Database connection management
│   │   └── database_connection.py
│   ├── transactions/         # Transaction handling & retry logic
│   │   ├── transaction.py
│   │   └── config.py
│   ├── tables/               # Table operations & DDL
│   │   ├── table.py
│   │   └── definitions.py
│   ├── download/             # High-performance data loading
│   │   └── read_sql.py
│   ├── core/                 # Core enums & types
│   │   ├── enums.py
│   │   └── types.py
│   ├── drivers/              # Driver registry & factory
│   │   ├── factory.py
│   │   ├── registry.py
│   │   ├── builder.py
│   │   └── type_mapping.py
│   ├── validation/           # Input validation
│   │   └── identifiers.py
│   ├── errors/               # Error classification
│   │   ├── patterns.py
│   │   └── registry.py
│   └── credentials/          # Secure credential management
│       ├── aws_secrets.py
│       ├── gcp_secrets.py
│       ├── azure_secrets.py
│       ├── vault_secrets.py
│       └── keyring_store.py
└── UNIT_TESTS/               # Comprehensive test suite
    ├── test_connections.py
    ├── test_tables.py
    └── conftest.py
```

## Testing

### Running Tests

SQLUtils includes a comprehensive test suite with 460+ tests covering all supported databases.

```bash
# Run all tests
python UNIT_TESTS/run_tests.py

# Run tests for specific database
pytest UNIT_TESTS/ -k mysql
pytest UNIT_TESTS/ -k postgres
pytest UNIT_TESTS/ -k oracle

# Run only unit tests (no database required)
pytest UNIT_TESTS/ -m unit

# Run only integration tests
pytest UNIT_TESTS/ -m integration

# Skip integration tests
pytest UNIT_TESTS/ --skip-integration
```

### Test Database Setup

The test suite uses Docker containers for database testing:

```bash
# Start all test databases
cd tst/docker
bash db_test.sh start

# Check database status
bash db_test.sh status

# Stop all databases
bash db_test.sh stop
```

### Test Coverage

- **464 passing tests** across all modules
- **Integration tests** for all 7 database systems
- **Unit tests** for core functionality
- **Automatic skipping** of unavailable databases

## Configuration

### Connection Parameters

Common parameters across all databases:

```python
{
    "host": "localhost",           # Database server hostname
    "port": 5432,                  # Port number
    "database": "mydb",            # Database name
    "user": "myuser",              # Username
    "password": "mypassword",      # Password
    "schema": "public"             # Schema (PostgreSQL, SQL Server, Oracle)
}
```

### Database-Specific Parameters

#### Oracle

```python
{
    "service_name": "XEPDB1",      # Oracle service name
    "sid": "XE"                     # Oracle SID (alternative to service_name)
}
```

#### SQL Server

```python
{
    "trust_server_certificate": "yes",  # Trust self-signed certificates
    "trusted_connection": "yes"          # Use Windows authentication
}
```

#### BigQuery

```python
{
    "project_id": "my-project",    # GCP project ID
    "dataset": "my_dataset",       # BigQuery dataset
    "credentials_path": "/path/to/key.json"  # Service account key
}
```

#### SQLite

```python
{
    "database": ":memory:"         # In-memory database
    # or
    "database": "/path/to/db.sqlite"  # File-based database
}
```

## Advanced Features

### Dry-Run SQL Generation

Generate SQL without executing:

```python
table = SQL_TABLE(conn, "test_table")
table.add_column("id", COLUMNDTYPE.INTEGER, nullable=False)
table.add_column("name", COLUMNDTYPE.VARCHAR, length=100)

# Generate CREATE TABLE SQL without executing
sql = table.create_table(dry_run=True)
print(sql)
# Output: CREATE TABLE "test_table" (
#     "id" INTEGER NOT NULL,
#     "name" VARCHAR(100)
# )
```

### Transaction Metrics

Monitor transaction performance:

```python
with Transaction(conn) as tx:
    tx.execute("INSERT INTO logs VALUES (?)", (message,))

    # Access metrics
    metrics = tx.metrics
    print(f"Duration: {metrics.duration_seconds}s")
    print(f"Retries: {metrics.retry_count}")
    print(f"Status: {metrics.final_status}")
```

### Connection Pooling

Reuse connections efficiently:

```python
conn = DatabaseConnection(dialect=SQLDialect.POSTGRES, **config)

# Execute multiple queries on same connection
result1 = conn.execute_query("SELECT * FROM table1")
result2 = conn.execute_query("SELECT * FROM table2")

conn.disconnect()
```

## Performance

SQLUtils is designed for performance:

- **Lazy Loading**: Drivers loaded only when needed
- **Connection Reuse**: Efficient connection pooling
- **Prepared Statements**: Parameterized queries for better performance
- **Batch Operations**: Support for bulk inserts and updates
- **Optimized Type Mapping**: Minimal overhead for type conversions

## Best Practices

### 1. Use Context Managers

```python
from sqlutilities import DatabaseConnection, SQLDialect

# ✅ Good - Automatic cleanup
with DatabaseConnection(dialect=SQLDialect.MYSQL, **config) as conn:
    results = conn.execute_query("SELECT * FROM users")

# ❌ Avoid - Manual cleanup required
conn = DatabaseConnection(dialect=SQLDialect.MYSQL, **config)
results = conn.execute_query("SELECT * FROM users")
conn.disconnect()
```

### 2. Use Parameterized Queries

```python
# ✅ Good - SQL injection safe
user_id = 123
results = conn.execute_query("SELECT * FROM users WHERE id = %s", (user_id,))

# ❌ Avoid - SQL injection vulnerable
results = conn.execute_query(f"SELECT * FROM users WHERE id = {user_id}")
```

### 3. Use Transactions for Multiple Operations

```python
from sqlutilities.transactions import RobustTransaction

# ✅ Good - Atomic operations
with RobustTransaction(conn) as tx:
    tx.execute("INSERT INTO orders (...) VALUES (...)")
    tx.execute("UPDATE inventory SET quantity = quantity - 1")

# ❌ Avoid - Not atomic
conn.execute_query("INSERT INTO orders (...) VALUES (...)")
conn.execute_query("UPDATE inventory SET quantity = quantity - 1")
```

### 4. Handle Errors Appropriately

```python
from sqlutilities.transactions import RobustTransaction
from sqlutilities.transactions.config import TransactionException

try:
    with RobustTransaction(conn) as tx:
        tx.execute("INSERT INTO table (...) VALUES (...)")
except TransactionException as e:
    logger.error(f"Transaction failed: {e}")
    if e.is_retryable:
        # Retry logic here
        pass
```

## Troubleshooting

### Common Issues

**Driver Not Found**

```python
# Error: No driver found for dialect 'mysql'
# Solution: Install a MySQL driver
pip install mysql-connector-python
```

**SSL Certificate Error (SQL Server)**

```python
# Error: SSL certificate verification failed
# Solution: Trust server certificate
conn = DatabaseConnection(
    dialect=SQLDialect.SQLSERVER,
    trust_server_certificate="yes",
    **other_params
)
```

**Oracle Service Name vs SID**

```python
# Use service_name for pluggable databases
conn = DatabaseConnection(
    dialect=SQLDialect.ORACLE,
    service_name="XEPDB1",  # For PDB
    **other_params
)

# Use sid for older Oracle versions
conn = DatabaseConnection(
    dialect=SQLDialect.ORACLE,
    sid="XE",  # For older versions
    **other_params
)
```

## Contributing

Contributions are welcome! We follow strict code quality and testing standards to ensure reliability.

**📖 For detailed contributing guidelines, code style requirements, and testing standards, see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)**

### Quick Start for Contributors

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/SQLUtils-Python.git
cd SQLUtils-Python

# Install dependencies
pip install -r requirements.txt
pip install -r UNIT_TESTS/requirements-test.txt

# Start test databases
cd tst/docker
bash db_test.sh start

# Run tests
cd ../..
python UNIT_TESTS/run_tests.py
```

### Code Quality Standards

- **Style**: PEP 8, Black formatting (120 char line length)
- **Documentation**: NumPy-style docstrings required
- **Testing**: 80%+ coverage, all tests must pass
- **Type Hints**: Required for all public functions

## Known Limitations

### Amazon Redshift

- **SQLAlchemy Integration**: Some features require the `sqlalchemy-redshift` package which is not included by default. Install with: `pip install sqlalchemy-redshift`
- Redshift integration tests are currently disabled pending package installation

### Google BigQuery

- **DML Operations**: INSERT, UPDATE, DELETE statements require billing to be enabled on your Google Cloud project (free tier restrictions)
- **PRIMARY KEY**: BigQuery does not enforce PRIMARY KEY constraints; they are informational only

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## AI Authorship Disclaimer

This package was developed with the assistance of LLM-based coding tools (Claude Code by Anthropic). AI tools were used for the following activities:

- **Code authorship** - Implementation of utilities, functions, and classes
- **Test development** - Creation of comprehensive unit tests
- **Documentation** - Generation of NumPy-style docstrings and README content
- **Code review** - Identification of bugs, edge cases, and improvements

Users should evaluate the code for their specific use cases and report any issues through the GitHub issue tracker.

---

## Acknowledgments

- Built with support for enterprise-grade database operations
- Inspired by the need for unified database interfaces
- Special thanks to all contributors and testers

## Support

- **Documentation**: See module docstrings for detailed API documentation
- **Issues**: Report bugs on [GitHub Issues](https://github.com/ruppert20/SQLUtils-Python/issues)
- **Discussions**: Join discussions on [GitHub Discussions](https://github.com/ruppert20/SQLUtils-Python/discussions)

---

**Made with ❤️ for the Python database community**
