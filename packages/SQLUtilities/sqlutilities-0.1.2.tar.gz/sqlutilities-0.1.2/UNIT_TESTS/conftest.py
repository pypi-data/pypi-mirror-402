"""
Pytest configuration and shared fixtures for SQLUtils unit tests.

This module provides:
- Database connection fixtures for all supported dialects
- Test configuration from .env file
- Shared test utilities and helpers
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

import pytest
from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent.parent

# Add project root to Python path so imports work
sys.path.insert(0, str(project_root))

# Import core dependencies that tests need
try:
    from sqlutilities.core.enums import SQLDialect
except ImportError as e:
    print(f"Warning: Could not import SQLDialect: {e}")
    SQLDialect = None

try:
    from sqlutilities.drivers.factory import DatabaseConnectionFactory
except ImportError as e:
    print(f"Warning: Could not import DatabaseConnectionFactory: {e}")
    DatabaseConnectionFactory = None


# Load environment variables from tst/docker/.env
env_path = project_root / "tst" / "docker" / ".env"
if env_path.exists():
    load_dotenv(env_path)


# Cache for available databases (checked once per session)
_available_databases_cache = None


def get_available_databases() -> Set[str]:
    """
    Check which databases are actually running and available.

    Runs 'bash tst/docker/db_test.sh status' and parses the output to determine
    which database containers are running and connected.

    Returns:
        Set of database names that are available (e.g., 'mysql', 'postgres', etc.)
    """
    global _available_databases_cache

    # Return cached result if available
    if _available_databases_cache is not None:
        return _available_databases_cache

    available = set()

    try:
        # Run the database status check script
        result = subprocess.run(
            ["bash", "db_test.sh", "status"],
            cwd=project_root / "tst" / "docker",
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Parse the output to find databases that are RUNNING & CONNECTED
        for line in result.stdout.split("\n"):
            if "RUNNING & CONNECTED" in line:
                # Extract database name from lines like: "✓ my-mysql-db - RUNNING & CONNECTED"
                if "mysql" in line.lower():
                    available.add("mysql")
                elif "postgres-test" in line.lower():
                    available.add("postgres")
                elif "oracle" in line.lower():
                    available.add("oracle")
                elif "sqlserver" in line.lower():
                    available.add("sqlserver")
                elif "redshift" in line.lower():
                    available.add("redshift")

        # SQLite is always available (built-in)
        available.add("sqlite")

        # BigQuery is available if credentials file exists
        bigquery_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if bigquery_creds and os.path.exists(bigquery_creds):
            available.add("bigquery")

    except Exception as e:
        print(f"Warning: Could not check database availability: {e}")
        # If we can't check, assume SQLite only
        available = {"sqlite"}

    # Cache the result
    _available_databases_cache = available

    return available


@pytest.fixture(scope="session")
def available_databases():
    """Fixture that provides the set of available databases."""
    return get_available_databases()


def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--dialect",
        action="store",
        default="all",
        help="Database dialect to test: mysql, postgres, oracle, sqlserver, bigquery, redshift, sqlite, or all",
    )
    parser.addoption(
        "--skip-integration",
        action="store_true",
        default=False,
        help="Skip integration tests that require actual database connections",
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "mysql: tests specific to MySQL dialect")
    config.addinivalue_line("markers", "postgres: tests specific to PostgreSQL dialect")
    config.addinivalue_line("markers", "oracle: tests specific to Oracle dialect")
    config.addinivalue_line("markers", "sqlserver: tests specific to SQL Server dialect")
    config.addinivalue_line("markers", "bigquery: tests specific to BigQuery dialect")
    config.addinivalue_line("markers", "redshift: tests specific to Redshift dialect")
    config.addinivalue_line("markers", "sqlite: tests specific to SQLite dialect")
    config.addinivalue_line("markers", "integration: tests that require database connections")
    config.addinivalue_line("markers", "unit: pure unit tests without external dependencies")


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command-line options and database availability."""
    dialect = config.getoption("--dialect").lower()
    skip_integration = config.getoption("--skip-integration")

    # Get available databases (cached per session)
    available_dbs = get_available_databases()

    # Print database availability at start of test session
    if items:  # Only print if there are items to test
        print(f"\n🔍 Available databases: {', '.join(sorted(available_dbs))}")

    # Skip integration tests if requested
    if skip_integration:
        skip_marker = pytest.mark.skip(reason="--skip-integration flag provided")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_marker)

    # Skip tests for unavailable databases (only for integration tests)
    for item in items:
        if "integration" in item.keywords:
            # Check if this test is parametrized with a dialect
            # Extract dialect from test name (e.g., test_name[mysql-mysql_config])
            test_name = item.nodeid
            for db_name in ["mysql", "postgres", "oracle", "sqlserver", "bigquery", "redshift", "sqlite"]:
                if f"[{db_name}-" in test_name.lower() or f"-{db_name}_config]" in test_name.lower():
                    if db_name not in available_dbs:
                        skip_marker = pytest.mark.skip(
                            reason=f"Database '{db_name}' is not available (not running or not connected)"
                        )
                        item.add_marker(skip_marker)
                        break

    # Skip tests for dialects not selected
    if dialect != "all":
        for item in items:
            # Check if test has any dialect marker
            test_dialects = []
            for marker_name in ["mysql", "postgres", "oracle", "sqlserver", "bigquery", "redshift", "sqlite"]:
                if marker_name in item.keywords:
                    test_dialects.append(marker_name)

            # If test has dialect markers and none match the selected dialect, skip it
            if test_dialects and dialect not in test_dialects:
                skip_marker = pytest.mark.skip(
                    reason=f"Test is for {', '.join(test_dialects)}, but --dialect={dialect} was specified"
                )
                item.add_marker(skip_marker)


# Database configuration helpers
class DatabaseConfig:
    """Container for database connection configuration from .env."""

    @staticmethod
    def get_mysql_config() -> Dict[str, str]:
        """Get MySQL connection configuration."""
        port_str = os.getenv("MYSQL_HOST_PORT", "3306")
        return {
            "host": os.getenv("MYSQL_HOST"),
            "port": int(port_str) if port_str else 3306,
            "database": os.getenv("MYSQL_DATABASE"),
            "user": os.getenv("MYSQL_USER"),
            "password": os.getenv("MYSQL_PASSWORD"),
        }

    @staticmethod
    def get_postgres_config() -> Dict[str, str]:
        """Get PostgreSQL connection configuration."""
        port_str = os.getenv("POSTGRES_HOST_PORT", "5432")
        return {
            "host": os.getenv("POSTGRES_HOST"),
            "port": int(port_str) if port_str else 5432,
            "database": os.getenv("POSTGRES_DB"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD"),
        }

    @staticmethod
    def get_oracle_config() -> Dict[str, str]:
        """Get Oracle connection configuration."""
        port_str = os.getenv("ORACLE_HOST_PORT", "1521")
        return {
            "host": os.getenv("ORACLE_HOST"),
            "port": int(port_str) if port_str else 1521,
            "service_name": os.getenv("ORACLE_SERVICE_NAME"),
            "user": os.getenv("ORACLE_USER"),
            "password": os.getenv("ORACLE_PASSWORD"),
        }

    @staticmethod
    def get_sqlserver_config() -> Dict[str, str]:
        """Get SQL Server connection configuration."""
        port_str = os.getenv("SQLSERVER_HOST_PORT", "1433")
        return {
            "host": os.getenv("SQLSERVER_HOST"),
            "port": int(port_str) if port_str else 1433,
            "database": os.getenv("SQLSERVER_DB_NAME"),
            "user": os.getenv("SQLSERVER_USER"),
            "password": os.getenv("SQLSERVER_PASSWORD"),
            "driver": "ODBC Driver 18 for SQL Server",  # Required for PyODBC connections
            "TrustServerCertificate": "yes",  # Required for self-signed certificates in Docker (ODBC Driver 18 format)
        }

    @staticmethod
    def get_bigquery_config() -> Dict[str, str]:
        """Get BigQuery configuration using service account credentials."""
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

        # Parse project_id from credentials file
        project_id = None
        try:
            import json

            with open(credentials_path, "r") as f:
                creds = json.load(f)
                project_id = creds.get("project_id")
        except Exception as e:
            raise ValueError(f"Failed to parse project_id from credentials file: {e}")

        if not project_id:
            raise ValueError("project_id not found in credentials file")

        dataset = os.getenv("BIGQUERY_DATASET")
        if not dataset:
            raise ValueError("BIGQUERY_DATASET environment variable not set")

        return {
            "project_id": project_id,  # Use project_id (aliased to project in driver)
            "credentials_path": credentials_path,
            "dataset_id": dataset,  # Use dataset_id to match main library code
        }

    @staticmethod
    def get_redshift_config() -> Dict[str, str]:
        """Get Redshift emulator configuration."""
        port_str = os.getenv("REDSHIFT_PORT", "5439")
        return {
            "host": os.getenv("REDSHIFT_HOST"),
            "port": int(port_str) if port_str else 5439,
            "database": os.getenv("REDSHIFT_POSTGRES_DB"),
            "user": os.getenv("REDSHIFT_POSTGRES_USER"),
            "password": os.getenv("REDSHIFT_POSTGRES_PASSWORD"),
            "sslmode": "disable",  # Disable SSL for local PostgreSQL emulator (psycopg2 format)
        }

    @staticmethod
    def get_sqlite_config() -> Dict[str, str]:
        """Get SQLite configuration (file-based for test isolation)."""
        # Use file-based database instead of :memory: to allow connection sharing
        # between the test connection and read_sql's SQLAlchemy connection
        import tempfile

        db_path = os.path.join(tempfile.gettempdir(), "sqlutils_test.db")
        return {
            "database": db_path,
        }

    @staticmethod
    def get_dialect_config(dialect: SQLDialect) -> Optional[Dict[str, str]]:
        """Get configuration for any dialect."""
        config_map = {
            SQLDialect.MYSQL: DatabaseConfig.get_mysql_config,
            SQLDialect.POSTGRES: DatabaseConfig.get_postgres_config,
            SQLDialect.ORACLE: DatabaseConfig.get_oracle_config,
            SQLDialect.SQLSERVER: DatabaseConfig.get_sqlserver_config,
            SQLDialect.BIGQUERY: DatabaseConfig.get_bigquery_config,
            SQLDialect.REDSHIFT: DatabaseConfig.get_redshift_config,
            SQLDialect.SQLITE: DatabaseConfig.get_sqlite_config,
        }
        return config_map.get(dialect, lambda: None)()

    @staticmethod
    def get_enabled_dialects() -> List[SQLDialect]:
        """Get list of dialects that are configured in .env."""
        # For now, return all dialects that have configuration
        # In production, you might check if containers are running
        return [
            SQLDialect.MYSQL,
            SQLDialect.POSTGRES,
            SQLDialect.ORACLE,
            SQLDialect.SQLSERVER,
            SQLDialect.BIGQUERY,
            SQLDialect.REDSHIFT,
            SQLDialect.SQLITE,
        ]


# Pytest fixtures
@pytest.fixture(scope="session")
def database_configs():
    """Provide database configurations for all dialects."""
    return {
        "mysql": DatabaseConfig.get_mysql_config(),
        "postgres": DatabaseConfig.get_postgres_config(),
        "oracle": DatabaseConfig.get_oracle_config(),
        "sqlserver": DatabaseConfig.get_sqlserver_config(),
        "bigquery": DatabaseConfig.get_bigquery_config(),
        "redshift": DatabaseConfig.get_redshift_config(),
        "sqlite": DatabaseConfig.get_sqlite_config(),
    }


@pytest.fixture(scope="session")
def enabled_dialects():
    """Provide list of enabled SQL dialects."""
    return DatabaseConfig.get_enabled_dialects()


@pytest.fixture
def mysql_config():
    """MySQL connection configuration."""
    return DatabaseConfig.get_mysql_config()


@pytest.fixture
def postgres_config():
    """PostgreSQL connection configuration."""
    return DatabaseConfig.get_postgres_config()


@pytest.fixture
def oracle_config():
    """Oracle connection configuration."""
    return DatabaseConfig.get_oracle_config()


@pytest.fixture
def sqlserver_config():
    """SQL Server connection configuration."""
    return DatabaseConfig.get_sqlserver_config()


@pytest.fixture
def bigquery_config():
    """BigQuery emulator configuration."""
    return DatabaseConfig.get_bigquery_config()


@pytest.fixture
def redshift_config():
    """Redshift emulator configuration."""
    return DatabaseConfig.get_redshift_config()


@pytest.fixture
def sqlite_config():
    """SQLite configuration."""
    return DatabaseConfig.get_sqlite_config()


@pytest.fixture(scope="session")
def connection_factory():
    """Provide DatabaseConnectionFactory instance."""
    return DatabaseConnectionFactory


@pytest.fixture
def sample_table_name():
    """Provide a sample table name for testing."""
    return "test_table"


@pytest.fixture
def sample_column_names():
    """Provide sample column names for testing."""
    return ["id", "name", "email", "created_at", "updated_at"]


@pytest.fixture
def all_dialects():
    """Provide list of all SQL dialects."""
    return [
        SQLDialect.MYSQL,
        SQLDialect.POSTGRES,
        SQLDialect.ORACLE,
        SQLDialect.SQLSERVER,
        SQLDialect.BIGQUERY,
        SQLDialect.REDSHIFT,
        SQLDialect.SQLITE,
    ]


@pytest.fixture
def temp_sqlite_db(tmp_path):
    """Create a temporary SQLite database file."""
    db_path = tmp_path / "test_db.sqlite"
    return str(db_path)


# Helper functions for tests
def is_container_running(container_name: str) -> bool:
    """Check if a Docker container is running."""
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={container_name}"], capture_output=True, text=True, check=True
        )
        return bool(result.stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def skip_if_container_not_running(container_name: str):
    """Pytest skip decorator if container is not running."""
    if not is_container_running(container_name):
        return pytest.mark.skip(reason=f"Container {container_name} is not running")
    return lambda func: func


# Export helper for use in tests
__all__ = [
    "DatabaseConfig",
    "is_container_running",
    "skip_if_container_not_running",
]
