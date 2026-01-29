"""
Database Driver Registry.

This module contains the comprehensive registry of all supported database drivers
and their configurations. It provides a central location for managing driver
metadata, parameter mappings, and driver selection logic.

Classes
-------
DatabaseDriver
    Enumeration of all supported database drivers with their configurations.

Functions
---------
get_driver_config
    Get driver configuration by driver name.
get_connection_builder
    Get connection builder for a specific driver.
get_drivers_for_dialect
    Get all drivers that support a specific SQL dialect.

Notes
-----
The registry uses a priority-based system to select drivers:
- Priority 1: ConnectorX drivers (highest performance)
- Priority 7-11: Standard Python database drivers
- Priority 2: SQLAlchemy (universal fallback)

Each driver configuration includes:
- Parameter mappings (generic to driver-specific)
- Supported connection options
- Priority level for driver selection
- Optimal chunk size for bulk operations

Author
------
DataScience ToolBox
"""

from __future__ import annotations  # Enable string annotations for forward references

from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional

# Use try/except to handle both absolute and relative imports
try:
    from core.enums import SQLDialect
except ImportError:
    from ..core.enums import SQLDialect

try:
    from drivers.models import DriverConfig, ParameterMapping
except ImportError:
    from .models import DriverConfig, ParameterMapping

# Avoid circular import with builder
if TYPE_CHECKING:
    from .builder import DriverConnectionBuilder

from CoreUtilities import LogLevel, get_logger

# Configure logging
logger = get_logger("driver_registry", level=LogLevel.WARNING, include_performance=True, include_emoji=True)


class DatabaseDriver(Enum):
    """
    Registry of all supported database drivers with their configurations.

    This enumeration contains every supported database driver along with its
    complete configuration including parameter mappings, supported options,
    priority level, and optimal chunk sizes for bulk operations.

    Attributes
    ----------
    Each enum member has a DriverConfig value containing:
    - name: Driver identifier
    - dialect: SQL dialect (SQLDialect enum)
    - module_name: Python module name to import
    - import_names: List of names to import from module
    - connection_builder: Factory method name for building connections
    - parameter_mappings: Generic to driver-specific parameter mappings
    - supported_kwargs: Additional supported connection options
    - priority: Driver selection priority (higher = preferred)
    - optimal_chunk_size: Recommended batch size for bulk operations

    Notes
    -----
    Drivers are organized by database system:
    - ConnectorX: High-performance Rust-based drivers
    - SQLite: sqlite3
    - Oracle: oracledb, cx_Oracle
    - PostgreSQL: psycopg2, psycopg3
    - SQL Server: pyodbc, pymssql
    - MySQL: mysqlclient, mysql-connector-python, PyMySQL
    - BigQuery: google-cloud-bigquery, pandas-gbq
    - Redshift: redshift_connector
    - SQLAlchemy: Universal ORM driver
    """

    # ConnectorX Drivers (High-performance Rust-based drivers)
    CONNECTORX_POSTGRES = DriverConfig(
        name="connectorx_postgres",
        dialect=SQLDialect.POSTGRES,
        module_name="connectorx",
        import_names=["connectorx"],
        connection_builder="build_connectorx_connection",
        parameter_mappings={
            "user": ParameterMapping("user", "user", required=True),
            "password": ParameterMapping("password", "password", required=True),
            "host": ParameterMapping("host", "host", required=True),
            "port": ParameterMapping("port", "port", default_value=5432),
            "database": ParameterMapping("database", "database", required=True),
        },
        supported_kwargs=["sslmode", "connect_timeout"],
        priority=1,  # Highest priority for ConnectorX
        optimal_chunk_size=5000,  # High-performance chunks
    )

    CONNECTORX_MYSQL = DriverConfig(
        name="connectorx_mysql",
        dialect=SQLDialect.MYSQL,
        module_name="connectorx",
        import_names=["connectorx"],
        connection_builder="build_connectorx_connection",
        parameter_mappings={
            "host": ParameterMapping("host", "host", required=True),
            "port": ParameterMapping("port", "port", default_value=3306),
            "database": ParameterMapping("database", "database"),
            "user": ParameterMapping("user", "user", required=True),
            "password": ParameterMapping("password", "password", required=True),
        },
        supported_kwargs=["charset", "ssl_mode"],
        priority=1,  # Highest priority for ConnectorX
        optimal_chunk_size=5000,  # High-performance chunks
    )

    CONNECTORX_SQLSERVER = DriverConfig(
        name="connectorx_sqlserver",
        dialect=SQLDialect.SQLSERVER,
        module_name="connectorx",
        import_names=["connectorx"],
        connection_builder="build_connectorx_connection",
        parameter_mappings={
            "host": ParameterMapping("host", "server", required=True),
            "database": ParameterMapping("database", "database"),
            "user": ParameterMapping("user", "user"),
            "password": ParameterMapping("password", "password"),
            "port": ParameterMapping("port", "port", default_value=1433),
            "trusted_connection": ParameterMapping("trusted_connection", "trusted_connection"),
            "encrypt": ParameterMapping("encrypt", "encrypt"),
            "trustservercertificate": ParameterMapping("TrustServerCertificate", "trustservercertificate"),
            "trust_server_certificate_ca": ParameterMapping(
                "trust_server_certificate_ca", "trust_server_certificate_ca"
            ),
        },
        supports_windows_auth=True,
        supported_kwargs=["encrypt", "trust_server_certificate", "trust_server_certificate_ca"],
        priority=1,  # Highest priority for ConnectorX
        optimal_chunk_size=5000,  # High-performance chunks
    )

    CONNECTORX_ORACLE = DriverConfig(
        name="connectorx_oracle",
        dialect=SQLDialect.ORACLE,
        module_name="connectorx",
        import_names=["connectorx"],
        connection_builder="build_connectorx_connection",
        parameter_mappings={
            "user": ParameterMapping("user", "user", required=True),
            "password": ParameterMapping("password", "password", required=True),
            "host": ParameterMapping("host", "host", required=True),
            "port": ParameterMapping("port", "port", default_value=1521),
            "service_name": ParameterMapping("service_name", "service_name"),
            "database": ParameterMapping("database", "sid"),
        },
        supported_kwargs=["service_name"],
        priority=1,  # Highest priority for ConnectorX
        optimal_chunk_size=5000,  # High-performance chunks
    )

    CONNECTORX_SQLITE = DriverConfig(
        name="connectorx_sqlite",
        dialect=SQLDialect.SQLITE,
        module_name="connectorx",
        import_names=["connectorx"],
        connection_builder="build_connectorx_connection",
        parameter_mappings={
            "database": ParameterMapping("database", "database", required=True, default_value=":memory:")
        },
        supported_kwargs=[],
        priority=1,  # Highest priority for ConnectorX
        optimal_chunk_size=3000,  # Good chunks for SQLite via ConnectorX
    )

    CONNECTORX_BIGQUERY = DriverConfig(
        name="connectorx_bigquery",
        dialect=SQLDialect.BIGQUERY,
        module_name="connectorx",
        import_names=["connectorx"],
        connection_builder="build_connectorx_connection",
        parameter_mappings={
            "project": ParameterMapping("project", "project", required=True),
            "credentials": ParameterMapping("credentials", "credentials", required=False),
            "location": ParameterMapping("location", "location", required=False),
        },
        supported_kwargs=["credentials", "location"],
        priority=1,  # Highest priority for ConnectorX
        optimal_chunk_size=10000,  # Large chunks for BigQuery performance
    )

    # SQLite Drivers
    SQLITE3 = DriverConfig(
        name="sqlite3",
        dialect=SQLDialect.SQLITE,
        module_name="sqlite3",
        import_names=["sqlite3"],
        connection_builder="build_sqlite_connection",
        parameter_mappings={
            "database": ParameterMapping("database", "database", required=True, default_value=":memory:")
        },
        supported_kwargs=[
            "timeout",
            "detect_types",
            "isolation_level",
            "check_same_thread",
            "factory",
            "cached_statements",
            "uri",
        ],
        priority=8,  # Demoted from 9 (was demoted from 10)
        optimal_chunk_size=500,  # Smaller chunks for SQLite to avoid memory issues
    )

    # Oracle Drivers
    ORACLEDB = DriverConfig(
        name="oracledb",
        dialect=SQLDialect.ORACLE,
        module_name="oracledb",
        import_names=["oracledb"],
        connection_builder="build_oracle_connection",
        parameter_mappings={
            "user": ParameterMapping("user", "user", required=True),
            "password": ParameterMapping("password", "password", required=True),
            "host": ParameterMapping("host", "host", required=True),
            "port": ParameterMapping("port", "port", default_value=1521),
            "service_name": ParameterMapping("service_name", "service_name"),
            "database": ParameterMapping("database", "sid"),  # Alternative to service_name
        },
        supported_kwargs=[
            "dsn",
            "mode",
            "encoding",
            "nencoding",
            "threaded",
            "events",
            "purity",
            "newpassword",
            "wallet_location",
            "wallet_password",
            "disable_oob",
            "stmtcachesize",
            "edition",
            "tag",
            "matchanytag",
            "config_dir",
            "appcontext",
            "shardingkey",
            "supershardingkey",
        ],
        priority=9,  # Demoted from 10
        optimal_chunk_size=5000,  # Larger chunks for Oracle array bind efficiency
    )

    CX_ORACLE = DriverConfig(
        name="cx_Oracle",
        dialect=SQLDialect.ORACLE,
        module_name="cx_Oracle",
        import_names=["cx_Oracle"],
        connection_builder="build_cx_oracle_connection",
        parameter_mappings={
            "user": ParameterMapping("user", "user", required=True),
            "password": ParameterMapping("password", "password", required=True),
            "host": ParameterMapping("host", "host", required=True),
            "port": ParameterMapping("port", "port", default_value=1521),
            "service_name": ParameterMapping("service_name", "service_name"),
            "database": ParameterMapping("database", "sid"),
        },
        requires_dsn=True,
        supported_kwargs=[
            "mode",
            "encoding",
            "nencoding",
            "threaded",
            "events",
            "purity",
            "newpassword",
            "tag",
            "matchanytag",
            "edition",
            "appcontext",
            "shardingkey",
            "supershardingkey",
        ],
        priority=4,  # Demoted from 5
        optimal_chunk_size=5000,  # Larger chunks for Oracle array bind efficiency
    )

    # PostgreSQL Drivers
    PSYCOPG2 = DriverConfig(
        name="psycopg2",
        dialect=SQLDialect.POSTGRES,
        module_name="psycopg2",
        import_names=["psycopg2"],
        connection_builder="build_psycopg2_connection",
        parameter_mappings={
            "user": ParameterMapping("user", "user", required=True),
            "password": ParameterMapping("password", "password", required=True),
            "host": ParameterMapping("host", "host", required=True),
            "port": ParameterMapping("port", "port", default_value=5432),
            "database": ParameterMapping("database", "database", required=True),
        },
        supported_kwargs=[
            "sslmode",
            "connect_timeout",
            "application_name",
            "client_encoding",
            "options",
            "sslcert",
            "sslkey",
            "sslrootcert",
            "sslcrl",
            "requiressl",
            "krbsrvname",
            "gsslib",
            "service",
        ],
        priority=9,  # Demoted from 10
        optimal_chunk_size=1000,  # Good balance for PostgreSQL COPY and execute_values
    )

    PSYCOPG3 = DriverConfig(
        name="psycopg",
        dialect=SQLDialect.POSTGRES,
        module_name="psycopg",
        import_names=["psycopg"],
        connection_builder="build_psycopg3_connection",
        parameter_mappings={
            "user": ParameterMapping("user", "user", required=True),
            "password": ParameterMapping("password", "password", required=True),
            "host": ParameterMapping("host", "host", required=True),
            "port": ParameterMapping("port", "port", default_value=5432),
            "database": ParameterMapping("database", "dbname", required=True),  # Note: dbname vs database
        },
        supported_kwargs=[
            "sslmode",
            "connect_timeout",
            "application_name",
            "client_encoding",
            "options",
            "sslcert",
            "sslkey",
            "sslrootcert",
            "sslcrl",
            "requiressl",
            "krbsrvname",
            "gsslib",
            "service",
            "target_session_attrs",
        ],
        priority=7,  # Demoted from 8
        optimal_chunk_size=1000,  # Good balance for PostgreSQL COPY and execute_values
    )

    # SQL Server Drivers
    PYODBC_SQLSERVER = DriverConfig(
        name="pyodbc",
        dialect=SQLDialect.SQLSERVER,
        module_name="pyodbc",
        import_names=["pyodbc"],
        connection_builder="build_pyodbc_sqlserver_connection",
        parameter_mappings={
            "host": ParameterMapping("host", "SERVER", required=True),
            "database": ParameterMapping("database", "DATABASE"),
            "user": ParameterMapping("user", "UID"),
            "username": ParameterMapping("username", "UID"),  # Alias for user
            "password": ParameterMapping("password", "PWD"),
            "port": ParameterMapping("port", "PORT"),
            "trust_server_certificate": ParameterMapping("trust_server_certificate", "TrustServerCertificate"),
            "trusted_connection": ParameterMapping("trusted_connection", "Trusted_Connection"),
            "driver": ParameterMapping("driver", "DRIVER"),
        },
        connection_string_format="odbc_string",
        supports_windows_auth=True,
        supported_kwargs=[
            "driver",
            "timeout",
            "connection_timeout",
            "command_timeout",
            "trustservercertificate",
            "encrypt",
            "multisubnetfailover",
            "applicationintent",
            "failoverpartner",
            "attachdbfilename",
            "authentication",
            "integrated_security",
            "trusted_connection",
            "workstation_id",
            "app_name",
            "language",
            "mars_connection",
            "packet_size",
            "autocommit",
            "ansi",
            "quoted_id",
        ],
        priority=9,  # Demoted from 10
        optimal_chunk_size=1000,  # Good for pyodbc fast_executemany
    )

    PYMSSQL = DriverConfig(
        name="pymssql",
        dialect=SQLDialect.SQLSERVER,
        module_name="pymssql",
        import_names=["pymssql"],
        connection_builder="build_pymssql_connection",
        parameter_mappings={
            "host": ParameterMapping("host", "server", required=True),
            "port": ParameterMapping("port", "port", default_value=1433),
            "database": ParameterMapping("database", "database"),
            "user": ParameterMapping("user", "user"),
            "password": ParameterMapping("password", "password"),
        },
        supported_kwargs=[
            "timeout",
            "login_timeout",
            "charset",
            "as_dict",
            "appname",
            "port",
            "tds_version",
            "autocommit",
        ],
        priority=4,  # Demoted from 5
        optimal_chunk_size=500,  # Smaller chunks for pymssql
    )

    # MySQL Drivers
    MYSQLCLIENT = DriverConfig(
        name="mysqlclient",
        dialect=SQLDialect.MYSQL,
        module_name="MySQLdb",
        import_names=["MySQLdb"],
        connection_builder="build_mysqlclient_connection",
        parameter_mappings={
            "host": ParameterMapping("host", "host", required=True),
            "port": ParameterMapping("port", "port", default_value=3306),
            "database": ParameterMapping("database", "db"),
            "user": ParameterMapping("user", "user", required=True),
            "password": ParameterMapping("password", "passwd", required=True),
        },
        supported_kwargs=[
            "charset",
            "connect_timeout",
            "read_timeout",
            "write_timeout",
            "autocommit",
            "local_infile",
            "ssl",
            "ssl_ca",
            "ssl_cert",
            "ssl_key",
            "ssl_verify_cert",
            "ssl_cipher",
            "ssl_capath",
            "init_command",
            "sql_mode",
            "compress",
            "named_pipe",
            "use_unicode",
            "client_flag",
            "cursorclass",
        ],
        priority=11,  # Demoted from 12 (highest priority for MySQL)
        optimal_chunk_size=1000,  # Good for multi-row INSERT
    )

    MYSQL_CONNECTOR = DriverConfig(
        name="mysql-connector-python",
        dialect=SQLDialect.MYSQL,
        module_name="mysql.connector",
        import_names=["mysql.connector"],
        connection_builder="build_mysql_connector_connection",
        parameter_mappings={
            "host": ParameterMapping("host", "host", required=True),
            "port": ParameterMapping("port", "port", default_value=3306),
            "database": ParameterMapping("database", "database"),
            "user": ParameterMapping("user", "user", required=True),
            "password": ParameterMapping("password", "password", required=True),
        },
        supported_kwargs=[
            "ssl_disabled",
            "ssl_ca",
            "ssl_cert",
            "ssl_key",
            "ssl_verify_cert",
            "ssl_verify_identity",
            "ssl_cipher_suites",
            "connect_timeout",
            "autocommit",
            "charset",
            "collation",
            "use_pure",
            "auth_plugin",
            "sql_mode",
            "time_zone",
            "init_command",
            "client_flags",
            "compress",
            "converter_class",
            "failover",
            "option_files",
            "option_groups",
            "allow_local_infile",
            "use_unicode",
        ],
        priority=9,  # Demoted from 10
        optimal_chunk_size=1000,  # Good for multi-row INSERT
    )

    PYMYSQL = DriverConfig(
        name="PyMySQL",
        dialect=SQLDialect.MYSQL,
        module_name="pymysql",
        import_names=["pymysql"],
        connection_builder="build_pymysql_connection",
        parameter_mappings={
            "host": ParameterMapping("host", "host", default_value="localhost"),
            "port": ParameterMapping("port", "port", default_value=3306),
            "database": ParameterMapping("database", "database"),
            "user": ParameterMapping("user", "user"),
            "password": ParameterMapping("password", "password"),
        },
        supported_kwargs=[
            "charset",
            "connect_timeout",
            "read_timeout",
            "write_timeout",
            "autocommit",
            "local_infile",
            "ssl",
            "ssl_ca",
            "ssl_cert",
            "ssl_key",
            "ssl_verify_cert",
            "ssl_verify_identity",
            "ssl_check_hostname",
            "init_command",
            "cursor",
            "defer_connect",
            "sql_mode",
            "client_flag",
            "program_name",
            "server_public_key",
        ],
        priority=7,  # Demoted from 8
        optimal_chunk_size=1000,  # Good for multi-row INSERT
    )

    # BigQuery Drivers
    BIGQUERY_CLIENT = DriverConfig(
        name="google-cloud-bigquery",
        dialect=SQLDialect.BIGQUERY,
        module_name="google.cloud.bigquery",
        import_names=["google.cloud", "bigquery"],
        connection_builder="build_bigquery_connection",
        parameter_mappings={
            "project": ParameterMapping(
                "project", "project", required=True
            ),  # Map BIGQUERY_PROJECT or project to project
            "project_id": ParameterMapping("project_id", "project", required=False),  # Also accept project_id as alias
            "dataset": ParameterMapping("dataset", "dataset_id", required=False),  # Map BIGQUERY_DATASET to dataset_id
            "api_endpoint": ParameterMapping("api_endpoint", "api_endpoint", required=False),
            "emulator_host": ParameterMapping("emulator_host", "emulator_host", required=False),
            "emulator": ParameterMapping("emulator", "emulator", required=False),
            "auth": ParameterMapping("auth", "auth", required=False),
            "credentials": ParameterMapping("credentials", "credentials", required=False),
            "location": ParameterMapping("location", "location", required=False),
        },
        supported_kwargs=[
            "credentials",
            "credentials_path",
            "location",
            "default_query_job_config",
            "client_info",
            "client_options",
            "dataset_id",
            "api_endpoint",
            "emulator_host",
            "emulator",
            "auth",  # Add emulator params
        ],
        priority=8,  # Demoted from 9 (was demoted from 10)
        optimal_chunk_size=10000,  # Larger chunks for better BigQuery throughput
    )

    PANDAS_GBQ = DriverConfig(
        name="pandas-gbq",
        dialect=SQLDialect.BIGQUERY,
        module_name="pandas_gbq",
        import_names=["pandas_gbq"],
        connection_builder="build_pandas_gbq_connection",
        parameter_mappings={"project_id": ParameterMapping("project_id", "project_id", required=True)},
        supported_kwargs=["auth_method", "service_account_path", "location", "configuration", "credentials"],
        priority=7,  # Demoted from 8
        optimal_chunk_size=10000,  # Larger chunks for better BigQuery throughput
    )

    # Redshift Drivers
    REDSHIFT_PSYCOPG2 = DriverConfig(
        name="psycopg2",
        dialect=SQLDialect.REDSHIFT,
        module_name="psycopg2",
        import_names=["psycopg2"],
        connection_builder="build_psycopg2_connection",
        parameter_mappings={
            "user": ParameterMapping("user", "user", required=True),
            "password": ParameterMapping("password", "password", required=True),
            "host": ParameterMapping("host", "host", required=True),
            "port": ParameterMapping("port", "port", default_value=5439),
            "database": ParameterMapping("database", "database", required=True),
            "ssl": ParameterMapping("ssl", "sslmode", required=False),  # Map ssl boolean to sslmode
            "sslmode": ParameterMapping("sslmode", "sslmode", required=False),
        },
        supported_kwargs=[
            "sslmode",
            "connect_timeout",
            "application_name",
            "client_encoding",
            "options",
            "sslcert",
            "sslkey",
            "sslrootcert",
            "sslcrl",
            "requiressl",
            "krbsrvname",
            "gsslib",
            "service",
        ],
        priority=10,  # Higher priority number = selected first (for local PostgreSQL emulators)
        optimal_chunk_size=2000,  # Larger chunks for Redshift
    )

    REDSHIFT_CONNECTOR = DriverConfig(
        name="redshift_connector",
        dialect=SQLDialect.REDSHIFT,
        module_name="redshift_connector",
        import_names=["redshift_connector"],
        connection_builder="build_redshift_connector_connection",
        parameter_mappings={
            "host": ParameterMapping("host", "host", required=True),
            "port": ParameterMapping("port", "port", default_value=5439),
            "database": ParameterMapping("database", "database", required=True),
            "user": ParameterMapping("user", "user", required=True),
            "password": ParameterMapping("password", "password", required=True),
            "ssl": ParameterMapping("ssl", "ssl", required=False),
            "sslmode": ParameterMapping("sslmode", "sslmode", required=False),
        },
        supported_kwargs=[
            "ssl",
            "sslmode",
            "timeout",
            "max_prepared_statements",
            "tcp_keepalive",
            "application_name",
            "preferred_role",
            "principal_arn",
            "credentials_provider",
            "region",
            "cluster_identifier",
            "auto_create",
            "db_groups",
        ],
        priority=9,  # Lower priority - use for actual AWS Redshift only
        optimal_chunk_size=2000,  # Larger chunks for Redshift
    )

    # SQLAlchemy (Universal) - Can work with any dialect
    SQLALCHEMY = DriverConfig(
        name="SQLAlchemy",
        dialect=None,  # Special case - works with any dialect
        module_name="sqlalchemy",
        import_names=["sqlalchemy"],
        connection_builder="build_sqlalchemy_connection",
        parameter_mappings={},  # SQLAlchemy handles this via URL building
        supported_kwargs=[
            "pool_size",
            "max_overflow",
            "pool_timeout",
            "pool_recycle",
            "pool_pre_ping",
            "echo",
            "echo_pool",
            "logging_name",
            "connect_args",
            "poolclass",
            "pool_events",
        ],
        priority=2,  # Demoted from 3 - lower priority as fallback option
    )


def get_driver_config(driver_name: str) -> Optional[DriverConfig]:
    """
    Get driver configuration by driver name.

    Performs case-insensitive lookup of driver configuration from the
    DatabaseDriver registry. This is the primary way to access driver
    metadata when creating connections.

    Parameters
    ----------
    driver_name : str
        Name of the driver to look up (case-insensitive).
        Examples: 'pyodbc', 'psycopg2', 'oracledb', 'connectorx_postgres'.

    Returns
    -------
    Optional[DriverConfig]
        DriverConfig object containing the driver's configuration, or None
        if the driver name is not found in the registry.

    Examples
    --------
    >>> config = get_driver_config('psycopg2')
    >>> print(config.dialect)
    SQLDialect.POSTGRES
    >>> print(config.priority)
    9
    """
    for driver in DatabaseDriver:
        if driver.value.name.lower() == driver_name.lower():
            return driver.value
    return None


def get_connection_builder(driver_name: str) -> Optional["DriverConnectionBuilder"]:
    """
    Get connection builder for a specific driver.

    Creates a DriverConnectionBuilder instance configured for the specified
    driver. The builder handles parameter mapping and validation for the driver.

    Parameters
    ----------
    driver_name : str
        Name of the driver to create a builder for (case-insensitive).

    Returns
    -------
    Optional[DriverConnectionBuilder]
        Configured connection builder for the driver, or None if the
        driver name is not found in the registry.

    Examples
    --------
    >>> builder = get_connection_builder('pyodbc')
    >>> params = builder.build_connection_params({'host': 'localhost', ...})
    """
    # Import here to avoid circular dependency.
    from .builder import DriverConnectionBuilder

    config = get_driver_config(driver_name)
    if config:
        return DriverConnectionBuilder(config)
    return None


def get_drivers_for_dialect(dialect: SQLDialect) -> List[DriverConfig]:
    """
    Get all drivers that support a specific SQL dialect.

    Returns a priority-sorted list of all drivers that support the given
    SQL dialect. This is useful for driver auto-selection when multiple
    drivers are available for a database system.

    Parameters
    ----------
    dialect : SQLDialect
        SQL dialect enum value (e.g., SQLDialect.POSTGRES, SQLDialect.MYSQL).

    Returns
    -------
    List[DriverConfig]
        List of DriverConfig objects supporting the dialect, sorted by
        priority (highest priority first). Returns empty list if no
        drivers support the dialect.

    Examples
    --------
    >>> drivers = get_drivers_for_dialect(SQLDialect.POSTGRES)
    >>> for driver in drivers:
    ...     print(f"{driver.name}: priority {driver.priority}")
    connectorx_postgres: priority 1
    psycopg2: priority 9
    psycopg3: priority 7
    """
    # Use resolved alias for consistency to handle dialect aliases.
    # For example, TSQL resolves to SQLSERVER.
    target_dialect = dialect.resolved_alias

    # Find all drivers that support this dialect by iterating through the registry.
    matching_drivers = []
    for driver in DatabaseDriver:
        driver_config = driver.value
        if driver_config.dialect == target_dialect:
            matching_drivers.append(driver_config)

    # Sort by priority with highest priority first.
    # Higher priority drivers (e.g., ConnectorX) will be preferred during auto-selection.
    matching_drivers.sort(key=lambda x: x.priority, reverse=True)

    return matching_drivers
