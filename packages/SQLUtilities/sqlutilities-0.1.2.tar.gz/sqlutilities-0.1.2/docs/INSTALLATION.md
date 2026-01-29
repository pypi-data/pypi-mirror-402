# Installation Guide

This guide provides detailed installation instructions for SQLUtils-Python and its database drivers.

## Table of Contents

- [Quick Install](#quick-install)
- [System Prerequisites](#system-prerequisites)
  - [SQL Server (pyodbc)](#sql-server-pyodbc)
  - [MySQL (mysqlclient)](#mysql-mysqlclient)
  - [Oracle (oracledb, cx_Oracle)](#oracle-oracledb-cx_oracle)
  - [PostgreSQL (psycopg2)](#postgresql-psycopg2)
- [Python Package Installation](#python-package-installation)
  - [Core Package](#core-package)
  - [Database Drivers](#database-drivers)
- [Verification](#verification)

## Quick Install

For most use cases, you can install SQLUtils-Python with pure Python drivers that don't require system libraries:

```bash
# Install core package
pip install -r requirements.txt

# Install pure Python database drivers (no system dependencies)
pip install pymysql psycopg2-binary pymssql oracledb
```

## System Prerequisites

Some database drivers require system libraries to be installed first. Only install what you need for your target database(s).

### SQL Server (pyodbc)

The `pyodbc` driver requires ODBC drivers to be installed on your system.

#### macOS (Homebrew)

```bash
# Install Microsoft ODBC Driver 18 for SQL Server
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18 mssql-tools18
```

#### Linux (Ubuntu/Debian)

```bash
# Add Microsoft repository
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

# Install ODBC driver
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 unixodbc-dev
```

#### Linux (RHEL/CentOS)

```bash
# Add Microsoft repository
sudo curl -o /etc/yum.repos.d/mssql-release.repo https://packages.microsoft.com/config/rhel/8/prod.repo

# Install ODBC driver
sudo yum remove unixODBC-utf16 unixODBC-utf16-devel
sudo ACCEPT_EULA=Y yum install -y msodbcsql18 mssql-tools18 unixODBC-devel
```

#### Official Documentation

- [Microsoft ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- [Linux Installation Guide](https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)

---

### MySQL (mysqlclient)

The `mysqlclient` driver requires MySQL client libraries. **Note:** `pymysql` is a pure Python alternative that doesn't require these libraries.

#### macOS (Homebrew)

```bash
# Install MySQL client libraries
brew install mysql-client

# Add to PATH (required for compilation)
echo 'export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Set compiler flags (may be needed)
export LDFLAGS="-L/opt/homebrew/opt/mysql-client/lib"
export CPPFLAGS="-I/opt/homebrew/opt/mysql-client/include"
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get install -y python3-dev default-libmysqlclient-dev build-essential pkg-config
```

#### Linux (RHEL/CentOS)

```bash
sudo yum install -y python3-devel mysql-devel gcc
```

#### Official Documentation

- [MySQL Client Library](https://dev.mysql.com/downloads/c-api/)
- [mysqlclient Documentation](https://github.com/PyMySQL/mysqlclient)

---

### Oracle (oracledb, cx_Oracle)

Oracle drivers may require Oracle Instant Client for "thick mode" operation. **Note:** The modern `oracledb` driver supports "thin mode" which doesn't require Instant Client.

#### macOS (Homebrew)

```bash
# For thick mode (cx_Oracle or oracledb thick mode)
# Note: Oracle Instant Client is not available via Homebrew
# Download manually from Oracle website

# Download from: https://www.oracle.com/database/technologies/instant-client/macos-intel-x86-downloads.html
# Or for Apple Silicon: https://www.oracle.com/database/technologies/instant-client/macos-arm64-downloads.html

# After downloading, extract and set environment variables:
# export LD_LIBRARY_PATH=/path/to/instantclient_19_8:$LD_LIBRARY_PATH
```

#### Linux (Ubuntu/Debian)

```bash
# Download Instant Client Basic and SDK packages
# From: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html

# For zip installation:
sudo mkdir -p /opt/oracle
cd /opt/oracle
sudo unzip instantclient-basic-linux.x64-19.8.0.0.0dbru.zip
sudo unzip instantclient-sdk-linux.x64-19.8.0.0.0dbru.zip

# Set environment variables
echo 'export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_8:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Install libaio (required)
sudo apt-get install -y libaio1
```

#### Linux (RHEL/CentOS)

```bash
# Download and install RPM packages
# From: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html

sudo yum install -y oracle-instantclient-basic-19.8.0.0.0-1.x86_64.rpm
sudo yum install -y oracle-instantclient-devel-19.8.0.0.0-1.x86_64.rpm
sudo yum install -y libaio
```

#### Official Documentation

- [Oracle Instant Client Downloads](https://www.oracle.com/database/technologies/instant-client/downloads.html)
- [python-oracledb Documentation](https://python-oracledb.readthedocs.io/)
- [cx_Oracle Installation](https://cx-oracle.readthedocs.io/en/latest/user_guide/installation.html)

**Recommended:** Use `oracledb` in thin mode to avoid Instant Client installation:

```python
import oracledb
# Thin mode is the default - no Instant Client needed
```

---

### PostgreSQL (psycopg2)

The `psycopg2` driver requires PostgreSQL client libraries. **Note:** `psycopg2-binary` is a standalone package that includes them (recommended for development).

#### macOS (Homebrew) - For psycopg2 (non-binary)

```bash
# Install PostgreSQL client libraries
brew install postgresql@14

# Add to PATH
echo 'export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Set compiler flags (may be needed)
export LDFLAGS="-L/opt/homebrew/opt/postgresql@14/lib"
export CPPFLAGS="-I/opt/homebrew/opt/postgresql@14/include"
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get install -y libpq-dev python3-dev
```

#### Linux (RHEL/CentOS)

```bash
sudo yum install -y postgresql-devel python3-devel gcc
```

#### Official Documentation

- [PostgreSQL Downloads](https://www.postgresql.org/download/)
- [psycopg2 Installation](https://www.psycopg.org/docs/install.html)

**Note:** For development/testing, use `psycopg2-binary` which includes precompiled libraries. For production, compile `psycopg2` against your system's PostgreSQL version for better performance and compatibility.

---

## Python Package Installation

### Core Package

Install the core SQLUtils-Python package and its dependencies:

```bash
pip install -r requirements.txt
```

This installs:
- `CoreUtilities` - Logging and utility functions
- `sqlglot` - SQL parser and transpiler
- `Unidecode` - Unicode text transliteration

### Database Drivers

Install only the drivers you need. Drivers are grouped by whether they require system libraries.

#### Pure Python Drivers (No System Dependencies)

These drivers work out-of-the-box without system libraries:

```bash
# MySQL
pip install pymysql==1.1.2

# PostgreSQL
pip install psycopg2-binary==2.9.11

# SQL Server
pip install pymssql==2.3.9

# Oracle (thin mode)
pip install oracledb==3.4.0

# Redshift (uses PostgreSQL driver)
pip install psycopg2-binary==2.9.11

# BigQuery
pip install google-cloud-bigquery==3.38.0
```

#### High-Performance Drivers (Require System Libraries)

These drivers require system libraries (see [System Prerequisites](#system-prerequisites)):

```bash
# MySQL (requires MySQL client libraries)
pip install mysqlclient

# PostgreSQL (requires PostgreSQL client libraries)
pip install psycopg2

# SQL Server (requires ODBC driver)
pip install pyodbc==5.3.0

# Oracle thick mode (requires Instant Client)
pip install cx_Oracle==8.3.0
```

#### Alternative Drivers

```bash
# MySQL - Official Oracle connector
pip install mysql-connector-python==9.3.0

# PostgreSQL - Modern psycopg3
pip install psycopg

# Redshift - Native connector
pip install redshift_connector==2.1.5

# Universal high-performance driver (Rust-based)
pip install connectorx

# SQLAlchemy ORM support
pip install sqlalchemy
```

### Complete Installation Examples

**Example 1: PostgreSQL + MySQL (Pure Python)**
```bash
pip install -r requirements.txt
pip install psycopg2-binary==2.9.11 pymysql==1.1.2
```

**Example 2: SQL Server + Oracle (with system libraries)**
```bash
# First install system prerequisites (see above)
# Then install Python packages:
pip install -r requirements.txt
pip install pyodbc==5.3.0 oracledb==3.4.0
```

**Example 3: All databases (mixed approach)**
```bash
pip install -r requirements.txt
pip install psycopg2-binary==2.9.11 \
            pymysql==1.1.2 \
            pyodbc==5.3.0 \
            oracledb==3.4.0 \
            google-cloud-bigquery==3.38.0 \
            redshift_connector==2.1.5
```

## Verification

Verify your installation by checking which drivers are available:

```python
from drivers.registry import DriverRegistry

# Get available drivers for each dialect
mysql_drivers = DriverRegistry.get_available_drivers('mysql')
postgres_drivers = DriverRegistry.get_available_drivers('postgres')
oracle_drivers = DriverRegistry.get_available_drivers('oracle')
sqlserver_drivers = DriverRegistry.get_available_drivers('sqlserver')

print(f"MySQL drivers: {[d.driver_name for d in mysql_drivers]}")
print(f"PostgreSQL drivers: {[d.driver_name for d in postgres_drivers]}")
print(f"Oracle drivers: {[d.driver_name for d in oracle_drivers]}")
print(f"SQL Server drivers: {[d.driver_name for d in sqlserver_drivers]}")
```

Or test a connection:

```python
from connections import DatabaseConnection
from core.enums import SQLDialect

# Test PostgreSQL connection
try:
    with DatabaseConnection(
        dialect=SQLDialect.POSTGRES,
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="postgres"
    ) as conn:
        result = conn.execute_query("SELECT version()")
        print(f"Connected! PostgreSQL version: {result[0][0]}")
except Exception as e:
    print(f"Connection failed: {e}")
```

## Troubleshooting

### "No module named 'X'" Error

Install the missing driver:
```bash
pip install <driver_name>
```

### "Can't find ODBC driver" (SQL Server)

Install the Microsoft ODBC driver following the [SQL Server prerequisites](#sql-server-pyodbc).

### "Library not loaded" (macOS)

Ensure Homebrew packages are installed and PATH is set:
```bash
brew install mysql-client postgresql@14
echo 'export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### psycopg2 vs psycopg2-binary

- Use `psycopg2-binary` for development (easier installation)
- Use `psycopg2` for production (better performance, compile against system PostgreSQL)

### Oracle Instant Client Not Found

For modern Oracle databases (12c+), use `oracledb` in thin mode (default) to avoid Instant Client:
```python
import oracledb
# No need to call init_oracle_client() - thin mode is default
```

## Next Steps

- See [README.md](../README.md) for usage examples
- See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup
- Run tests: `python UNIT_TESTS/run_tests.py`
