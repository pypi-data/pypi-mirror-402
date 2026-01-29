"""
Database Connection Factory.

This module provides a comprehensive factory pattern implementation for creating
database connections across multiple database systems and drivers. It handles
driver-specific connection logic, parameter mapping, and connection string
construction for various database backends.

Classes
-------
DatabaseConnectionFactory
    Factory class for creating database connections using registered drivers.

Functions
---------
get_available_odbc_drivers
    Get list of available ODBC drivers on the system.
get_sql_server_drivers
    Get list of available SQL Server ODBC drivers.
handle_datetimeoffset
    Convert SQL Server DATETIMEOFFSET values to Python datetime objects.

Notes
-----
The factory supports multiple database systems including:
- SQLite (sqlite3)
- Oracle (oracledb, cx_Oracle)
- PostgreSQL (psycopg2, psycopg3)
- SQL Server (pyodbc, pymssql)
- MySQL (mysqlclient, mysql-connector-python, PyMySQL)
- BigQuery (google-cloud-bigquery, pandas-gbq)
- Redshift (redshift_connector)
- SQLAlchemy (universal)
- ConnectorX (high-performance Rust-based driver)

Author
------
DataScience ToolBox
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# Use try/except to handle both absolute and relative imports
try:
    from core.enums import DatabaseObjectType, SQLDialect
    from drivers.builder import DriverConnectionBuilder
    from drivers.registry import get_driver_config
    from validation.identifiers import SQL_DIALECT_REGISTRY
except ImportError:
    from ..core.enums import DatabaseObjectType, SQLDialect
    from ..validation.identifiers import SQL_DIALECT_REGISTRY
    from .builder import DriverConnectionBuilder
    from .registry import get_driver_config

logger = logging.getLogger(__name__)


class DatabaseConnectionFactory:
    """
    Factory for creating database connections using the driver registry.

    This class implements the factory pattern to create database connections
    across multiple database systems. It uses the driver registry to look up
    driver configurations and routes connection requests to the appropriate
    driver-specific connection builder methods.

    Methods
    -------
    create_connection(driver_name, connection_params, connection_options)
        Create a database connection using the specified driver.
    build_sqlite_connection(builder, connection_params, connection_options)
        Build SQLite connection using sqlite3.
    build_oracle_connection(builder, connection_params, connection_options)
        Build Oracle connection using oracledb.
    build_connectorx_connection(builder, connection_params, connection_options)
        Build ConnectorX connection string for high-performance data loading.
    build_cx_oracle_connection(builder, connection_params, connection_options)
        Build Oracle connection using cx_Oracle.
    build_psycopg2_connection(builder, connection_params, connection_options)
        Build PostgreSQL connection using psycopg2.
    build_psycopg3_connection(builder, connection_params, connection_options)
        Build PostgreSQL connection using psycopg3.
    build_pyodbc_sqlserver_connection(builder, connection_params, connection_options)
        Build SQL Server connection using pyodbc.
    build_pymssql_connection(builder, connection_params, connection_options)
        Build SQL Server connection using pymssql.
    build_mysqlclient_connection(builder, connection_params, connection_options)
        Build MySQL connection using mysqlclient.
    build_mysql_connector_connection(builder, connection_params, connection_options)
        Build MySQL connection using mysql-connector-python.
    build_pymysql_connection(builder, connection_params, connection_options)
        Build MySQL connection using PyMySQL.
    build_bigquery_connection(builder, connection_params, connection_options)
        Build BigQuery connection using google-cloud-bigquery.
    build_pandas_gbq_connection(builder, connection_params, connection_options)
        Build BigQuery configuration for pandas-gbq.
    build_redshift_connector_connection(builder, connection_params, connection_options)
        Build Redshift connection using redshift_connector.
    build_sqlalchemy_connection(builder, connection_params, connection_options)
        Build SQLAlchemy engine and session factory.

    Notes
    -----
    All connection builder methods follow the same signature pattern:
    - builder: DriverConnectionBuilder instance
    - connection_params: Generic connection parameters
    - connection_options: Additional driver-specific options
    """

    @staticmethod
    def create_connection(
        driver_name: str, connection_params: Dict[str, Any], connection_options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create a database connection using the specified driver.

        This method orchestrates the connection creation process by:
        1. Looking up the driver configuration from the registry
        2. Creating a connection builder for the driver
        3. Validating connection parameters
        4. Routing to the appropriate driver-specific connection builder

        Parameters
        ----------
        driver_name : str
            Name of the driver to use (e.g., 'pyodbc', 'psycopg2').
        connection_params : Dict[str, Any]
            Generic connection parameters that will be mapped to driver-specific
            parameters. Common parameters include: host, port, database, user, password.
        connection_options : Optional[Dict[str, Any]], optional
            Additional driver-specific connection options, by default None.

        Returns
        -------
        Any
            Database connection object. The exact type depends on the driver:
            - pyodbc: pyodbc.Connection
            - psycopg2: psycopg2.extensions.connection
            - sqlite3: sqlite3.Connection
            - etc.

        Raises
        ------
        ValueError
            If the driver is not supported or parameter validation fails.
        RuntimeError
            If the driver is not available or connection fails.

        Examples
        --------
        >>> params = {
        ...     'host': 'localhost',
        ...     'database': 'mydb',
        ...     'user': 'myuser',
        ...     'password': 'mypass'
        ... }
        >>> conn = DatabaseConnectionFactory.create_connection('psycopg2', params)
        """
        # Look up the driver configuration from the registry.
        config = get_driver_config(driver_name)
        if not config:
            raise ValueError(f"Unsupported driver: {driver_name}")

        # Create a connection builder for this driver configuration.
        builder = DriverConnectionBuilder(config)
        connection_options = connection_options or {}

        # Validate that all required parameters are present and valid.
        # This prevents obscure errors later in the connection process.
        errors = builder.validate_parameters(connection_params)
        if errors:
            raise ValueError(f"Parameter validation failed: {'; '.join(errors)}")

        # Route to the appropriate connection builder method based on the driver configuration.
        # Each database driver has its own builder method that handles driver-specific logic.
        method_name = config.connection_builder
        method = getattr(DatabaseConnectionFactory, method_name, None)
        if not method:
            raise RuntimeError(f"Connection builder method '{method_name}' not implemented")

        return method(builder, connection_params, connection_options)

    @staticmethod
    def build_sqlite_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """
        Build SQLite connection using sqlite3.

        Parameters
        ----------
        builder : DriverConnectionBuilder
            Connection builder with SQLite driver configuration.
        connection_params : Dict[str, Any]
            Connection parameters including 'database' (file path or ':memory:').
        connection_options : Dict[str, Any]
            Additional sqlite3.connect() options (timeout, isolation_level, etc.).

        Returns
        -------
        sqlite3.Connection
            SQLite database connection object.

        Raises
        ------
        RuntimeError
            If sqlite3 module is not available.
        Exception
            If connection fails for any other reason.
        """
        try:
            import sqlite3

            # Build driver-specific parameters from generic connection parameters.
            params = builder.build_connection_params(connection_params, connection_options)

            # SQLite uses 'database' parameter as the path to the database file.
            # Special value ':memory:' creates an in-memory database.
            db_path = params.get("database", ":memory:")

            # Remove 'database' from params since sqlite3.connect() takes it as a positional argument.
            # The remaining params (timeout, isolation_level, etc.) are passed as keyword arguments.
            params.pop("database", None)

            conn = sqlite3.connect(db_path, **params)
            logger.debug(f"Connected to SQLite database: {db_path}", extra={"emoji": "🗃️"})
            return conn

        except ImportError:
            raise RuntimeError("sqlite3 module not available")
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_oracle_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """
        Build Oracle connection using oracledb (python-oracledb).

        Parameters
        ----------
        builder : DriverConnectionBuilder
            Connection builder with oracledb driver configuration.
        connection_params : Dict[str, Any]
            Connection parameters including user, password, host, port, service_name/sid.
        connection_options : Dict[str, Any]
            Additional oracledb.connect() options.

        Returns
        -------
        oracledb.Connection
            Oracle database connection object.

        Raises
        ------
        RuntimeError
            If oracledb driver is not available.
        Exception
            If connection fails for any other reason.
        """
        try:
            import oracledb

            # Build parameters
            params = builder.build_connection_params(connection_params, connection_options)

            conn = oracledb.connect(**params)
            logger.debug("Connected to Oracle database using oracledb", extra={"emoji": "🏛️"})
            return conn

        except ImportError:
            raise RuntimeError("oracledb driver not available")
        except Exception as e:
            logger.error(f"Oracle connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_connectorx_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build ConnectorX connection."""
        try:
            import connectorx as cx

            # Build parameters
            params = builder.build_connection_params(connection_params, connection_options)

            # ConnectorX uses connection strings, so we need to build the appropriate URL
            dialect = builder.config.dialect

            if dialect == SQLDialect.POSTGRES:
                # PostgreSQL connection string format
                host = params.get("host", "localhost")
                port = params.get("port", 5432)
                user = params.get("user", "")
                password = params.get("password", "")
                database = params.get("database", "")
                sslmode = params.get("sslmode", "prefer")

                conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}"

            elif dialect == SQLDialect.MYSQL:
                # MySQL connection string format
                host = params.get("host", "localhost")
                port = params.get("port", 3306)
                user = params.get("user", "")
                password = params.get("password", "")
                database = params.get("database", "")
                charset = params.get("charset", "utf8mb4")

                conn_str = f"mysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"

            elif dialect == SQLDialect.SQLSERVER:
                # SQL Server connection string format for ConnectorX
                # Reference: https://sfu-db.github.io/connector-x/databases/mssql.html
                server = params.get("server", "localhost")
                port = params.get("port", 1433)
                user = params.get("user", "")
                password = params.get("password", "")
                database = params.get("database", "")

                # Connection parameters - use the mapped parameter names
                trusted_connection = params.get("trusted_connection", False)
                encrypt = params.get("encrypt", False)
                trust_server_certificate = params.get("trustservercertificate", False)  # This is the mapped name
                trust_server_certificate_ca = params.get("trust_server_certificate_ca", None)

                # Convert string values to boolean for ConnectorX
                if isinstance(trusted_connection, str):
                    trusted_connection = trusted_connection.lower() in ("true", "yes", "1")
                if isinstance(encrypt, str):
                    encrypt = encrypt.lower() in ("true", "yes", "1")
                if isinstance(trust_server_certificate, str):
                    trust_server_certificate = trust_server_certificate.lower() in ("true", "yes", "1")

                # URL-encode password if it contains special characters
                if password:
                    from urllib.parse import quote_plus

                    password = quote_plus(password)

                # Build base connection string
                if trusted_connection:
                    conn_str = f"mssql://{server}:{port}/{database}"
                else:
                    conn_str = f"mssql://{user}:{password}@{server}:{port}/{database}"

                # Build query parameters
                query_params = []
                if trusted_connection:
                    query_params.append("trusted_connection=true")
                if encrypt:
                    query_params.append("encrypt=true")
                if trust_server_certificate:
                    query_params.append("trust_server_certificate=true")
                if trust_server_certificate_ca:
                    query_params.append(f"trust_server_certificate_ca={trust_server_certificate_ca}")

                # Add query parameters to connection string
                if query_params:
                    conn_str += "?" + "&".join(query_params)

            elif dialect == SQLDialect.ORACLE:
                # Oracle connection string format
                host = params.get("host", "localhost")
                port = params.get("port", 1521)
                user = params.get("user", "")
                password = params.get("password", "")
                service_name = params.get("service_name", "")
                sid = params.get("sid", "")

                if service_name:
                    conn_str = f"oracle://{user}:{password}@{host}:{port}/{service_name}"
                else:
                    conn_str = f"oracle://{user}:{password}@{host}:{port}/{sid}"

            elif dialect == SQLDialect.BIGQUERY:
                # BigQuery connection string format
                project = params.get("project", "")
                dataset = params.get("dataset", "")

                if dataset:
                    conn_str = f"bigquery://{project}/{dataset}"
                else:
                    conn_str = f"bigquery://{project}"

            elif dialect == SQLDialect.SQLITE:
                # SQLite connection string format
                database = params.get("database", ":memory:")
                conn_str = f"sqlite://{database}"
            else:
                raise ValueError(f"ConnectorX does not support dialect: {dialect}")

            # Note: ConnectorX is primarily for reading data, not establishing persistent connections
            # We return the connection string that can be used with cx.read_sql()
            logger.debug(
                f"ConnectorX connection string prepared for {dialect.name if dialect else 'unknown'}",
                extra={"emoji": "🚀"},
            )
            return conn_str

        except ImportError:
            raise RuntimeError("connectorx module not available")
        except Exception as e:
            logger.error(f"ConnectorX connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_cx_oracle_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build Oracle connection using cx_Oracle."""
        try:
            import cx_Oracle

            # Build parameters
            params = builder.build_connection_params(connection_params, connection_options)

            # cx_Oracle requires DSN creation
            dsn = cx_Oracle.makedsn(
                host=params.pop("host"),
                port=params.pop("port", 1521),
                service_name=params.pop("service_name", None) or params.pop("sid", None),
            )

            params["dsn"] = dsn
            conn = cx_Oracle.connect(**params)
            logger.debug("Connected to Oracle database using cx_Oracle", extra={"emoji": "🏛️"})
            return conn

        except ImportError:
            raise RuntimeError("cx_Oracle driver not available")
        except Exception as e:
            logger.error(f"cx_Oracle connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_psycopg2_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build PostgreSQL connection using psycopg2."""
        try:
            import psycopg2
            from psycopg2.extras import register_uuid

            # Register UUID adapter for automatic UUID handling
            register_uuid()

            # Build parameters
            params = builder.build_connection_params(connection_params, connection_options)

            conn = psycopg2.connect(**params)
            logger.debug("Connected to PostgreSQL using psycopg2", extra={"emoji": "🐘"})
            return conn

        except ImportError:
            raise RuntimeError("psycopg2 driver not available")
        except Exception as e:
            logger.error(f"psycopg2 connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_psycopg3_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build PostgreSQL connection using psycopg3."""
        try:
            import psycopg

            # Build parameters
            params = builder.build_connection_params(connection_params, connection_options)

            conn = psycopg.connect(**params)
            logger.debug("Connected to PostgreSQL using psycopg3", extra={"emoji": "🐘"})
            return conn

        except ImportError:
            raise RuntimeError("psycopg3 driver not available")
        except Exception as e:
            logger.error(f"psycopg3 connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_pyodbc_sqlserver_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build SQL Server connection using pyodbc."""
        try:
            import os
            from pathlib import Path

            import pyodbc

            # Set ODBC environment variables if not already set (macOS Homebrew support)
            if not os.getenv("ODBCSYSINI"):
                homebrew_etc = Path("/opt/homebrew/etc")
                if homebrew_etc.exists():
                    os.environ["ODBCSYSINI"] = str(homebrew_etc)
                    os.environ["ODBCINI"] = str(homebrew_etc / "odbc.ini")

            # Get available ODBC drivers
            available_drivers = [driver for driver in pyodbc.drivers() if "SQL Server" in driver]
            if not available_drivers:
                raise RuntimeError("No SQL Server ODBC drivers found")

            # Use the first available driver (usually the most recent)
            detected_driver = available_drivers[0]
            logger.debug(f"Using ODBC driver: {detected_driver}", extra={"emoji": "🔍"})

            # Build ODBC connection string
            conn_str = builder.build_odbc_connection_string(connection_params, detected_driver)

            # Log connection string without sensitive data
            safe_conn_str = conn_str
            if connection_params.get("password"):
                safe_conn_str = conn_str.replace(connection_params["password"], "***")
            logger.debug(f"ODBC connection string: {safe_conn_str}", extra={"emoji": "🔗"})

            # Create connection
            conn = pyodbc.connect(conn_str, **connection_options)

            # Add converter for DATETIMEOFFSET to handle SQL Server DATETIMEOFFSET values
            conn.add_output_converter(SQL_SS_TIMESTAMPOFFSET, handle_datetimeoffset)
            logger.debug(f"Added DATETIMEOFFSET converter for SQL type {SQL_SS_TIMESTAMPOFFSET}", extra={"emoji": "🔄"})

            # Enable fast_executemany if requested
            if connection_params.get("fast_executemany", True) and hasattr(conn, "fast_executemany"):
                conn.fast_executemany = True  # type: ignore
                logger.debug("Enabled fast_executemany for SQL Server", extra={"emoji": "⚡"})

            logger.debug("Connected to SQL Server using pyodbc", extra={"emoji": "🗄️"})
            return conn

        except ImportError:
            raise RuntimeError("pyodbc driver not available")
        except Exception as e:
            logger.error(f"pyodbc SQL Server connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_pymssql_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build SQL Server connection using pymssql."""
        try:
            import pymssql

            # Build parameters
            params = builder.build_connection_params(connection_params, connection_options)

            conn = pymssql.connect(**params)
            logger.debug("Connected to SQL Server using pymssql", extra={"emoji": "🗄️"})
            return conn

        except ImportError:
            raise RuntimeError("pymssql driver not available")
        except Exception as e:
            logger.error(f"pymssql connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_mysqlclient_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build MySQL connection using mysqlclient (MySQLdb)."""
        try:
            import MySQLdb

            # Build parameters
            params = builder.build_connection_params(connection_params, connection_options)

            conn = MySQLdb.connect(**params)
            logger.debug("Connected to MySQL using mysqlclient (MySQLdb)", extra={"emoji": "🐬"})
            return conn

        except ImportError:
            raise RuntimeError("mysqlclient (MySQLdb) driver not available")
        except Exception as e:
            logger.error(f"mysqlclient connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_mysql_connector_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build MySQL connection using mysql-connector-python."""
        try:
            import mysql.connector

            # Build parameters
            params = builder.build_connection_params(connection_params, connection_options)

            conn = mysql.connector.connect(**params)
            logger.debug("Connected to MySQL using mysql-connector-python", extra={"emoji": "🐬"})
            return conn

        except ImportError:
            raise RuntimeError("mysql-connector-python driver not available")
        except Exception as e:
            logger.error(f"MySQL connector connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_pymysql_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build MySQL connection using PyMySQL."""
        try:
            import pymysql

            # Build parameters
            params = builder.build_connection_params(connection_params, connection_options)

            conn = pymysql.connect(**params)
            logger.debug("Connected to MySQL using PyMySQL", extra={"emoji": "🐬"})
            return conn

        except ImportError:
            raise RuntimeError("PyMySQL driver not available")
        except Exception as e:
            logger.error(f"PyMySQL connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_bigquery_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build BigQuery connection using google-cloud-bigquery."""
        try:
            from google.cloud import bigquery

            # Check if this is emulator mode
            emulator_mode = (
                connection_params.get("emulator") == "true"
                or connection_params.get("emulator") is True
                or connection_params.get("auth") == "emulator"
            )

            if emulator_mode:
                from google.api_core.client_options import ClientOptions
                from google.auth.credentials import AnonymousCredentials

                # Get API endpoint and project from params
                api_endpoint = connection_params.get("api_endpoint", "http://localhost:9050")
                project_id = connection_params.get("project", "test")

                # Create client options for emulator endpoint
                client_options = ClientOptions(api_endpoint=api_endpoint)

                # Create client with project, anonymous credentials, and client options
                conn = bigquery.Client(
                    project=project_id, credentials=AnonymousCredentials(), client_options=client_options
                )
                logger.debug(
                    f"Connected to BigQuery emulator at {api_endpoint} (project: {project_id})", extra={"emoji": "🧪"}
                )
            else:
                # Build parameters for standard BigQuery connection
                params = builder.build_connection_params(connection_params, connection_options)

                # Remove parameters that aren't valid for Client constructor
                dataset_id = params.pop("dataset_id", None)
                params.pop("emulator", None)
                params.pop("api_endpoint", None)
                params.pop("emulator_host", None)
                params.pop("auth", None)

                # Handle credentials_path - load credentials from file if provided
                credentials_path = connection_params.get("credentials_path")
                if credentials_path:
                    from google.oauth2 import service_account

                    credentials = service_account.Credentials.from_service_account_file(credentials_path)
                    params["credentials"] = credentials
                    logger.debug(f"Loaded BigQuery credentials from {credentials_path}", extra={"emoji": "🔐"})
                    # Remove credentials_path from params if it somehow got through
                    params.pop("credentials_path", None)

                conn = bigquery.Client(**params)
                logger.debug("Connected to Google BigQuery", extra={"emoji": "☁️"})

                # Store dataset_id for later use if provided
                if dataset_id:
                    setattr(conn, "_default_dataset_id", dataset_id)

            return conn

        except ImportError:
            raise RuntimeError("google-cloud-bigquery driver not available")
        except Exception as e:
            logger.error(f"BigQuery connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_pandas_gbq_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build BigQuery connection using pandas-gbq."""
        try:
            import pandas_gbq

            # Build parameters
            params = builder.build_connection_params(connection_params, connection_options)

            # pandas-gbq doesn't have a persistent connection object
            # Return configuration for later use
            conn = {"type": "pandas_gbq", "project_id": params.get("project_id"), "options": params}
            logger.debug("Configured BigQuery using pandas-gbq", extra={"emoji": "☁️"})
            return conn

        except ImportError:
            raise RuntimeError("pandas-gbq driver not available")
        except Exception as e:
            logger.error(f"pandas-gbq connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_redshift_connector_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build Redshift connection using redshift_connector."""
        try:
            import redshift_connector

            # Build parameters
            params = builder.build_connection_params(connection_params, connection_options)

            conn = redshift_connector.connect(**params)
            logger.debug("Connected to Redshift using redshift_connector", extra={"emoji": "🔴"})
            return conn

        except ImportError:
            raise RuntimeError("redshift_connector driver not available")
        except Exception as e:
            logger.error(f"redshift_connector connection failed: {e}", extra={"emoji": "❌"})
            raise

    @staticmethod
    def build_sqlalchemy_connection(
        builder: DriverConnectionBuilder, connection_params: Dict[str, Any], connection_options: Dict[str, Any]
    ) -> Any:
        """Build SQLAlchemy connection."""
        try:
            from sqlalchemy import URL, create_engine, text
            from sqlalchemy.orm import sessionmaker

            # Build SQLAlchemy URL using an ALLOWLIST approach for query parameters
            # Only explicitly allowed connection parameters are passed as query strings
            # This is much safer than maintaining an exhaustive exclusion list
            # Common query parameters that are valid for most database drivers
            # These are passed in the URL query string (after the ? in the connection URL)
            allowed_query_params = {
                # SSL/TLS parameters
                "ssl",
                "sslmode",
                "ssl_ca",
                "ssl_cert",
                "ssl_key",
                "sslrootcert",
                "sslcert",
                "sslkey",
                "ssl_verify_cert",
                "ssl_check_hostname",
                # Connection behavior
                "charset",
                "encoding",
                "collation",
                "timezone",
                "connect_timeout",
                "timeout",
                "pool_size",
                "max_overflow",
                "pool_recycle",
                "pool_timeout",
                # SQL Server specific
                "driver",
                "odbc_driver",
                "autocommit",
                "ansi",
                "trust_server_certificate",
                "TrustServerCertificate",  # ODBC Driver 18 format (camelCase)
                "encrypt",
                "tds_version",
                "mars_conn",
                # PostgreSQL specific
                "application_name",
                "options",
                "keepalives",
                "keepalives_idle",
                "fallback_application_name",
                # MySQL specific
                "unix_socket",
                "read_timeout",
                "write_timeout",
                "local_infile",
                "use_unicode",
                "sql_mode",
                "init_command",
                # General
                "isolation_level",
                "echo",
                "pool_pre_ping",
            }

            # Special handling for Oracle service_name
            # Oracle can connect via SID (database param) or service_name (query param)
            # If service_name is provided, always use it instead of database/SID
            database_param = connection_params.get("database")
            if connection_params.get("service_name"):
                # Oracle with service_name - don't pass database parameter at all
                # The service_name will be added to query parameters below
                database_param = None
                # Add service_name to allowed query params for this connection
                allowed_query_params = allowed_query_params | {"service_name"}

            url = connection_params.get(
                "sqlalchemy_url",
                URL.create(
                    drivername=connection_params["drivername"],
                    username=connection_params.get("username") or connection_params.get("user"),
                    password=connection_params.get("password"),
                    host=connection_params.get("host"),
                    port=connection_params.get("port"),
                    database=database_param,
                    # Only include parameters that are in the allowed list
                    query={
                        k: str(v) for k, v in connection_params.items() if k in allowed_query_params and v is not None
                    },
                ),
            )

            # Create engine with options
            engine_options = connection_options.copy()
            if "pool_pre_ping" not in engine_options:
                engine_options["pool_pre_ping"] = True
            if "echo" not in engine_options:
                engine_options["echo"] = False

            engine = create_engine(url, **engine_options)

            # Test the connection with dialect-appropriate query
            # Oracle requires FROM DUAL for SELECT statements
            test_query = "SELECT 1 FROM DUAL" if "oracle" in connection_params["drivername"] else "SELECT 1"
            with engine.connect() as test_conn:
                test_conn.execute(text(test_query))

            # Create session factory
            Session = sessionmaker(bind=engine)

            conn = {"type": "sqlalchemy", "engine": engine, "session_factory": Session, "url": str(url)}

            logger.debug("Connected using SQLAlchemy", extra={"emoji": "⚙️"})
            return conn

        except ImportError:
            raise RuntimeError("SQLAlchemy not available")
        except Exception as e:
            logger.error(f"SQLAlchemy connection failed: {e}", extra={"emoji": "❌"})
            raise


def get_available_odbc_drivers() -> List[str]:
    """
    Get list of available ODBC drivers on the system.

    This function queries the system's ODBC driver manager to retrieve
    all installed ODBC drivers. Useful for debugging connection issues
    and determining which drivers are available.

    Returns
    -------
    List[str]
        List of ODBC driver names available on the system. Returns empty
        list if pyodbc is not available or if driver detection fails.

    Examples
    --------
    >>> drivers = get_available_odbc_drivers()
    >>> print(drivers)
    ['ODBC Driver 18 for SQL Server', 'SQLite3 ODBC Driver', ...]
    """
    try:
        import pyodbc

        return pyodbc.drivers()
    except ImportError:
        logger.warning("pyodbc not available - cannot detect ODBC drivers", extra={"emoji": "⚠️"})
        return []
    except Exception as e:
        logger.error(f"Failed to get ODBC drivers: {e}", extra={"emoji": "❌"})
        return []


def get_sql_server_drivers() -> List[str]:
    """
    Get list of available SQL Server ODBC drivers.

    Filters the system's ODBC drivers to return only those that support
    SQL Server connections. These drivers typically have "SQL Server" in
    their name.

    Returns
    -------
    List[str]
        List of SQL Server ODBC driver names. Returns empty list if no
        SQL Server drivers are found.

    Examples
    --------
    >>> drivers = get_sql_server_drivers()
    >>> print(drivers)
    ['ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server']
    """
    all_drivers = get_available_odbc_drivers()
    return [driver for driver in all_drivers if "SQL Server" in driver]


# The SQL type code for DATETIMEOFFSET in SQL Server.
# This constant is used to register a custom converter with pyodbc.
SQL_SS_TIMESTAMPOFFSET = -155


def handle_datetimeoffset(dto_value):
    """
    Convert SQL Server DATETIMEOFFSET values to Python datetime objects.

    This function is registered as a custom converter with pyodbc to handle
    SQL Server DATETIMEOFFSET values, which include timezone information.
    It's called automatically by pyodbc for every DATETIMEOFFSET column value.

    Parameters
    ----------
    dto_value : bytes or str or None
        The raw DATETIMEOFFSET value from SQL Server. Can be:
        - None: NULL value
        - bytes: UTF-16LE encoded string representation
        - str: String representation (less common)

    Returns
    -------
    datetime or str or None
        - None if input is None
        - datetime object if successfully parsed
        - Original value if parsing fails (for debugging)

    Notes
    -----
    SQL Server's DATETIMEOFFSET type stores both the datetime and timezone
    offset. The value is typically transmitted as a UTF-16LE encoded string
    that can be parsed by Python's datetime.fromisoformat().
    """
    if dto_value is None:
        return None
    try:
        if isinstance(dto_value, bytes):
            # Decode the UTF-16LE encoded bytes to a string.
            # SQL Server transmits DATETIMEOFFSET as UTF-16LE encoded ISO format strings.
            decoded_str = dto_value.decode("utf-16le")

            # Parse the ISO format string to a Python datetime object.
            # Python's fromisoformat() can handle the timezone offset notation.
            return datetime.fromisoformat(decoded_str)

        # Fallback: if already a string, return it for inspection.
        # This case is less common with modern pyodbc versions.
        return dto_value.decode("utf-16le") if isinstance(dto_value, bytes) else dto_value

    except (ValueError, TypeError) as e:
        # If parsing fails, return the raw value to help with debugging.
        # This allows inspection of unexpected formats.
        print(f"Error parsing DATETIMEOFFSET: {e}")
        return dto_value
