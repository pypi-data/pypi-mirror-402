"""
Database Connection Management

This module provides the DatabaseConnection class for managing database connections.
- DatabaseConnection: Pure connection management (no transaction logic)

Author: DataScience ToolBox
"""

import copy as copy_module
import os
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

# Use try/except to handle both absolute and relative imports
try:
    from core.enums import SQLDialect
    from drivers.factory import DatabaseConnectionFactory
    from transactions.config import ConnectionState
    from transactions.transaction import _TEST_QUERIES, RobustTransaction
    from validation.identifiers import SQL_DIALECT_REGISTRY
except ImportError:
    from ..core.enums import SQLDialect
    from ..transactions.config import ConnectionState
    from ..transactions.transaction import RobustTransaction, _TEST_QUERIES
    from ..drivers.factory import DatabaseConnectionFactory
    from ..validation.identifiers import SQL_DIALECT_REGISTRY

from CoreUtilities import LogLevel, get_logger

# Configure logging
logger = get_logger("database_connection", level=LogLevel.INFO, include_performance=True, include_emoji=True)


class DatabaseConnection:
    """
    Pure database connection management class with automatic driver selection.

    This class provides robust database connection management with automatic
    driver selection, connection pooling, and state tracking. It handles the
    low-level connection lifecycle and delegates transaction and query execution
    to the RobustTransaction class.

    Responsibilities:
    - Connection establishment and teardown
    - Driver selection and fallback
    - Connection state management
    - Raw connection object provision

    Does NOT handle:
    - Query execution (delegated to RobustTransaction)
    - Cursor management (handled internally by RobustTransaction)
    - Transaction management (delegated to RobustTransaction)
    - Retry logic (handled by RobustTransaction)

    Parameters
    ----------
    dialect : SQLDialect or str
        The SQL dialect to use (e.g., SQLDialect.POSTGRESQL, 'mysql', etc.)
    pull_from_env : bool, default=True
        Whether to pull connection parameters from environment variables
    host : str, optional
        Database server hostname or IP address
    port : int, optional
        Database server port number
    database : str, optional
        Database name to connect to
    username : str, optional
        Username for authentication
    password : str, optional
        Password for authentication
    service_name : str, optional
        Oracle-specific service name
    project_id : str, optional
        BigQuery-specific project ID
    dataset_id : str, optional
        BigQuery-specific dataset ID
    driver_options : dict, optional
        Driver-specific options passed to the driver
    connection_options : dict, optional
        Connection-specific options for the connection string
    auto_connect : bool, default=True
        Whether to automatically connect upon initialization
    fast_executemany : bool, default=True
        Enable SQL Server pyodbc fast_executemany optimization
    **kwargs
        Additional connection parameters

    Attributes
    ----------
    dialect : SQLDialect
        The resolved SQL dialect being used
    state : ConnectionState
        Current connection state (DISCONNECTED, CONNECTING, CONNECTED, ERROR)
    current_driver : dict or None
        Information about the currently active driver
    available_drivers : dict
        All available drivers for the current dialect
    is_connected : bool
        Whether the connection is active and ready
    connection_info : dict
        Sanitized connection information (passwords redacted)

    Examples
    --------
    Basic connection with auto-detect:
        >>> conn = DatabaseConnection(SQLDialect.POSTGRESQL)
        >>> conn.execute_query("SELECT version()")

    Connection with explicit parameters:
        >>> conn = DatabaseConnection(
        ...     dialect='mysql',
        ...     host='localhost',
        ...     database='testdb',
        ...     username='root',
        ...     password='pass',
        ...     auto_connect=True
        ... )

    Using as context manager:
        >>> with DatabaseConnection(SQLDialect.SQLITE, database=':memory:') as conn:
        ...     conn.execute_query("CREATE TABLE test (id INTEGER)")
        ...     conn.execute_query("INSERT INTO test VALUES (1)")

    Manual driver selection:
        >>> conn = DatabaseConnection(SQLDialect.POSTGRESQL, auto_connect=False)
        >>> conn.connect(driver_name='psycopg3')

    Notes
    -----
    - Environment variables are automatically loaded if pull_from_env=True
    - Connection parameters follow the pattern: {DIALECT}_{PARAMETER}
    - Example: POSTGRESQL_HOST, MYSQL_PORT, ORACLE_SERVICE_NAME
    - Redshift connections automatically use PostgreSQL drivers
    - The class automatically selects the best available driver
    """

    def __init__(
        self,
        dialect: Union[SQLDialect, str],
        pull_from_env: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        service_name: Optional[str] = None,  # Oracle specific
        project_id: Optional[str] = None,  # BigQuery specific
        dataset_id: Optional[str] = None,  # BigQuery specific
        driver_options: Optional[Dict[str, Any]] = None,
        connection_options: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
        fast_executemany: bool = True,  # SQL Server pyodbc optimization
        # Secure credential sources (automatically retrieve on connect)
        aws_secret_name: Optional[str] = None,
        aws_secret_region: str = "us-east-1",
        aws_rds_iam: bool = False,
        aws_rds_region: str = "us-east-1",
        gcp_secret_project: Optional[str] = None,
        gcp_secret_name: Optional[str] = None,
        azure_vault_url: Optional[str] = None,
        azure_secret_name: Optional[str] = None,
        vault_path: Optional[str] = None,
        vault_mount: str = "secret",
        vault_dynamic_role: Optional[str] = None,
        keyring_service: Optional[str] = None,
        keyring_username: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the database connection with dialect-specific parameters.

        Parameters
        ----------
        dialect : SQLDialect or str
            SQL dialect enum or string name
        pull_from_env : bool, default=True
            Load connection parameters from environment variables
        host : str, optional
            Database server hostname
        port : int, optional
            Database server port
        database : str, optional
            Database/schema name
        username : str, optional
            Authentication username
        password : str, optional
            Authentication password
        service_name : str, optional
            Oracle service name (Oracle only)
        project_id : str, optional
            GCP project ID (BigQuery only)
        dataset_id : str, optional
            BigQuery dataset ID (BigQuery only)
        driver_options : dict, optional
            Driver-specific options
        connection_options : dict, optional
            Connection string options
        auto_connect : bool, default=True
            Connect automatically on initialization
        fast_executemany : bool, default=True
            Enable pyodbc fast_executemany (SQL Server only)
        **kwargs
            Additional connection parameters

        Raises
        ------
        ValueError
            If dialect is not recognized or supported
        RuntimeError
            If auto_connect fails and connection cannot be established
        """

        # =========================================================================
        # STEP 1: Automatically retrieve credentials from secure sources
        # =========================================================================
        secret_credentials = self._retrieve_credentials_from_secrets(
            aws_secret_name=aws_secret_name,
            aws_secret_region=aws_secret_region,
            aws_rds_iam=aws_rds_iam,
            aws_rds_region=aws_rds_region,
            gcp_secret_project=gcp_secret_project,
            gcp_secret_name=gcp_secret_name,
            azure_vault_url=azure_vault_url,
            azure_secret_name=azure_secret_name,
            vault_path=vault_path,
            vault_mount=vault_mount,
            vault_dynamic_role=vault_dynamic_role,
            keyring_service=keyring_service,
            keyring_username=keyring_username,
            host=host,  # Needed for RDS IAM
            port=port,  # Needed for RDS IAM
            username=username,  # Needed for RDS IAM
        )

        # Merge secret credentials with explicit parameters
        # Explicit parameters take precedence over secrets
        if secret_credentials:
            for key, value in secret_credentials.items():
                if locals().get(key) is None:
                    locals()[key] = value

        # =========================================================================
        # STEP 2: Process dialect and parameters
        # =========================================================================
        # Convert string dialect to enum if needed
        if isinstance(dialect, str):
            try:
                self._dialect = SQLDialect(dialect.lower())
            except ValueError:
                # Try to find by name_value
                for d in SQLDialect:
                    if d.name_value.lower() == dialect.lower():
                        self._dialect = d
                        break
                else:
                    raise ValueError(f"Unsupported dialect: {dialect}")
        else:
            self._dialect = dialect

        # Use resolved alias for consistency
        self._dialect = self._dialect.resolved_alias

        # Store all connection parameters including additional kwargs
        # Use merged credentials from secrets
        merged_creds = secret_credentials if secret_credentials else {}
        self._connection_params = {
            k: v
            for k, v in {
                "host": host or merged_creds.get("host"),
                "port": port or merged_creds.get("port"),
                "database": database or merged_creds.get("database"),
                "username": username or merged_creds.get("username") or merged_creds.get("user"),
                "password": password or merged_creds.get("password"),
                "service_name": service_name or merged_creds.get("service_name"),
                "project_id": project_id or merged_creds.get("project_id"),
                "dataset_id": dataset_id or merged_creds.get("dataset_id"),
                **kwargs,
            }.items()
            if v is not None
        }

        if pull_from_env:
            # Load environment variables if requested
            env_config = self.get_env_db_config()
            # Merge environment config with provided parameters
            self._connection_params = {
                **env_config,
                **{k: (env_config.get(k) if v is None else v) for k, v in self._connection_params.items()},
            }

        # Note: Redshift uses PostgreSQL drivers internally, but the dialect should remain REDSHIFT
        # The driver selection logic will automatically use psycopg2 drivers for Redshift connections
        # DO NOT change self._dialect here - it should remain as REDSHIFT throughout the connection lifecycle

        # Store options and special flags
        self._driver_options = driver_options or {}
        self._connection_options = connection_options or {}
        self._fast_executemany = fast_executemany

        # Connection state
        self._connection = None
        self._state = ConnectionState.DISCONNECTED
        self._current_driver = None
        self._available_drivers = None

        # Get available drivers for this dialect
        self._refresh_available_drivers()

        logger.trace(f"Initialized DatabaseConnection for {self._dialect.description}", emoji="🔧")

        # Auto-connect if requested
        if auto_connect:
            success = self.connect()
            if not success:
                logger.warning(f"Auto-connect failed for {self._dialect.description}", emoji="⚠️")

    @staticmethod
    def _retrieve_credentials_from_secrets(**kwargs) -> Optional[Dict[str, Any]]:
        """
        Automatically retrieve database credentials from secure sources.

        This method is called internally during initialization to pull credentials
        from various secret management systems. Only ONE secret source should be
        specified at a time.

        Priority order (first one found is used):
        1. AWS RDS IAM Authentication (no password needed)
        2. HashiCorp Vault Dynamic Credentials
        3. AWS Secrets Manager
        4. Google Secret Manager
        5. Azure Key Vault
        6. HashiCorp Vault Static Secrets
        7. OS Keyring

        Returns:
            Dictionary with connection parameters (host, port, database, username, password)
            or None if no secret source was specified
        """
        # Extract parameters
        aws_secret_name = kwargs.get("aws_secret_name")
        aws_secret_region = kwargs.get("aws_secret_region", "us-east-1")
        aws_rds_iam = kwargs.get("aws_rds_iam", False)
        aws_rds_region = kwargs.get("aws_rds_region", "us-east-1")
        gcp_secret_project = kwargs.get("gcp_secret_project")
        gcp_secret_name = kwargs.get("gcp_secret_name")
        azure_vault_url = kwargs.get("azure_vault_url")
        azure_secret_name = kwargs.get("azure_secret_name")
        vault_path = kwargs.get("vault_path")
        vault_mount = kwargs.get("vault_mount", "secret")
        vault_dynamic_role = kwargs.get("vault_dynamic_role")
        keyring_service = kwargs.get("keyring_service")
        keyring_username = kwargs.get("keyring_username")

        # For RDS IAM
        host = kwargs.get("host")
        port = kwargs.get("port")
        username = kwargs.get("username")

        # Count how many secret sources are specified
        secret_sources_count = sum(
            [
                bool(aws_secret_name),
                bool(aws_rds_iam),
                bool(gcp_secret_project and gcp_secret_name),
                bool(azure_vault_url and azure_secret_name),
                bool(vault_path),
                bool(vault_dynamic_role),
                bool(keyring_service and keyring_username),
            ]
        )

        if secret_sources_count > 1:
            logger.warning("Multiple secret sources specified. Using first one found in priority order.", emoji="⚠️")

        if secret_sources_count == 0:
            return None  # No secrets configured, use regular auth

        try:
            # Priority 1: AWS RDS IAM Authentication (no password!)
            if aws_rds_iam:
                if not all([host, port, username]):
                    raise ValueError("aws_rds_iam requires host, port, and username to be specified")

                logger.info("Retrieving AWS RDS IAM authentication token", emoji="🔐")
                from ..credentials.aws_secrets import get_rds_iam_token

                # Type assertions for type checker (validation already done above)
                assert host is not None and port is not None and username is not None

                token = get_rds_iam_token(host=host, port=port, username=username, region=aws_rds_region)
                logger.info("Retrieved RDS IAM token (valid 15 minutes)", emoji="✅")
                return {"password": token}  # Only override password with token

            # Priority 2: HashiCorp Vault Dynamic Credentials
            if vault_dynamic_role:
                logger.info(f"Generating dynamic credentials from Vault role: {vault_dynamic_role}", emoji="🔐")
                from ..credentials.vault_secrets import get_vault_dynamic_credentials

                creds = get_vault_dynamic_credentials(vault_dynamic_role)
                logger.info(f"Generated dynamic credentials (valid {creds.get('lease_duration', 0)}s)", emoji="✅")
                return {"username": creds["username"], "password": creds["password"]}

            # Priority 3: AWS Secrets Manager
            if aws_secret_name:
                logger.info(f"Retrieving credentials from AWS Secrets Manager: {aws_secret_name}", emoji="🔐")
                from ..credentials.aws_secrets import get_aws_secret

                creds = get_aws_secret(aws_secret_name, aws_secret_region)
                logger.info("Retrieved AWS secret successfully", emoji="✅")
                return creds

            # Priority 4: Google Secret Manager
            if gcp_secret_project and gcp_secret_name:
                logger.info(f"Retrieving credentials from GCP Secret Manager: {gcp_secret_name}", emoji="🔐")
                from ..credentials.gcp_secrets import get_gcp_secret

                creds = get_gcp_secret(gcp_secret_project, gcp_secret_name)
                logger.info("Retrieved GCP secret successfully", emoji="✅")
                return creds

            # Priority 5: Azure Key Vault
            if azure_vault_url and azure_secret_name:
                logger.info(f"Retrieving credentials from Azure Key Vault: {azure_secret_name}", emoji="🔐")
                from ..credentials.azure_secrets import get_azure_secret

                creds = get_azure_secret(azure_vault_url, azure_secret_name)
                logger.info("Retrieved Azure secret successfully", emoji="✅")
                return creds

            # Priority 6: HashiCorp Vault Static Secrets
            if vault_path:
                logger.info(f"Retrieving credentials from HashiCorp Vault: {vault_path}", emoji="🔐")
                from ..credentials.vault_secrets import get_vault_secret

                creds = get_vault_secret(vault_path, vault_mount)
                logger.info("Retrieved Vault secret successfully", emoji="✅")
                return creds

            # Priority 7: OS Keyring
            if keyring_service and keyring_username:
                logger.info(f"Retrieving credentials from OS Keyring: {keyring_service}", emoji="🔐")
                from ..credentials.keyring_store import get_credentials

                creds = get_credentials(keyring_service, keyring_username)
                logger.info("Retrieved keyring credentials successfully", emoji="✅")
                return creds

        except ImportError as e:
            logger.error(
                f"Failed to import credential module: {e}. "
                "Install the required package (e.g., pip install boto3, google-cloud-secret-manager, etc.)",
                emoji="❌",
            )
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve credentials from secret source: {e}", emoji="❌")
            raise

        return None

    @property
    def dialect(self) -> SQLDialect:
        """Get the current SQL dialect."""
        return self._dialect

    @property
    def state(self) -> ConnectionState:
        """Get the current connection state."""
        return self._state

    @property
    def current_driver(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently used driver."""
        return self._current_driver

    @property
    def available_drivers(self) -> Dict[str, Dict[str, Any]]:
        """Get all available drivers for the current dialect."""
        return self._available_drivers or {}

    @property
    def is_connected(self) -> bool:
        """Check if the database connection is active and ready to use."""
        return self._state == ConnectionState.CONNECTED and self._connection is not None

    @property
    def connection_info(self) -> Dict[str, Any]:
        """Get sanitized connection information (without password).

        Always includes standard connection fields (host, database) even if None,
        to ensure consistent interface across all database dialects.
        """
        info = self._connection_params.copy()
        if "password" in info and info["password"]:
            info["password"] = "***"

        # Ensure standard fields are always present for consistent interface
        # SQLite uses 'database' as file path, BigQuery uses project_id/dataset_id
        if "host" not in info:
            info["host"] = None
        if "database" not in info:
            info["database"] = info.get("dataset_id") or info.get("project_id")

        info.update(
            {
                "dialect": self._dialect.name_value,
                "state": self._state.value,
                "current_driver": self._current_driver["name"] if self._current_driver else None,
            }
        )
        return info

    @property
    def connectorx_uri(self) -> str:
        """
        Generate ConnectorX-compatible connection URI for the current connection parameters.

        Uses the existing DatabaseConnectionFactory logic to build the connection string.

        Returns:
            Connection string that can be used directly with ConnectorX read_sql()

        Raises:
            ValueError: If dialect is not supported by ConnectorX
            RuntimeError: If required connection parameters are missing

        Examples:
            >>> conn = DatabaseConnection('postgresql')
            >>> uri = conn.connectorx_uri
            >>> import connectorx as cx
            >>> df = cx.read_sql("SELECT * FROM table", uri)
        """
        try:
            # Create a copy of this connection and connect using ConnectorX driver
            connectorx_conn = self.copy(auto_connect=False)

            # Connect using the hardcoded ConnectorX driver name
            if not connectorx_conn.connect(driver_name="connectorx_{}".format(self._dialect.name_value.lower())):
                raise RuntimeError(f"Failed to connect using ConnectorX driver for {self._dialect.name_value}")

            # Get the connection string from the ConnectorX connection
            conn_str = connectorx_conn.get_raw_connection()

            # Clean up the temporary connection
            connectorx_conn.disconnect()

            # Ensure we got a valid connection string
            if not isinstance(conn_str, str):
                raise RuntimeError(f"Expected connection string, got {type(conn_str)}")

            return conn_str

        except Exception as e:
            logger.error(f"Failed to generate ConnectorX URI: {e}", emoji="❌")
            raise

    def _refresh_available_drivers(self) -> None:
        """Refresh the list of available drivers for the current dialect."""
        try:
            self._available_drivers = SQL_DIALECT_REGISTRY._get_dialect_drivers(self._dialect)
            logger.trace(f"Found {len(self._available_drivers)} drivers for {self._dialect.description}", emoji="🔍")
        except Exception as e:
            logger.error(f"Failed to refresh available drivers: {e}", emoji="❌")
            self._available_drivers = {}

    def get_best_available_driver(self) -> Optional[Dict[str, Any]]:
        """Get the best available driver for the current dialect."""
        try:
            driver_info = SQL_DIALECT_REGISTRY.get_best_available_driver(self._dialect)
            if not driver_info:
                logger.warning(f"No available drivers found for {self._dialect.description}", emoji="⚠️")
            return driver_info if driver_info else None
        except Exception as e:
            logger.error(f"Failed to get best available driver: {e}", emoji="❌")
            return None

    def _create_connection_with_driver(self, driver_info: Dict[str, Any]) -> Any:
        """Create a database connection using the specified driver."""
        driver_name = driver_info["name"]

        try:
            # Prepare connection parameters including kwargs and special flags
            all_params = self._connection_params.copy()
            all_params["fast_executemany"] = self._fast_executemany

            conn = DatabaseConnectionFactory.create_connection(
                driver_name=driver_name, connection_params=all_params, connection_options=self._connection_options
            )

            return conn

        except Exception as e:
            logger.error(f"Failed to create connection with {driver_name}: {e}", emoji="❌")
            raise

    def connect(self, driver_name: Optional[str] = None) -> bool:
        """Establish database connection using the specified or best available driver."""
        self._state = ConnectionState.CONNECTING

        try:
            # If specific driver requested, try to use it
            if driver_name:
                driver_info = None
                available_drivers = self._available_drivers or {}
                for priority, info in available_drivers.items():
                    if info["name"] == driver_name and info["available"]:
                        driver_info = info.copy()
                        driver_info["priority"] = priority
                        break

                if not driver_info:
                    raise ValueError(f"Driver '{driver_name}' not available for {self._dialect.description}")
            else:
                # Get best available driver
                driver_info = self.get_best_available_driver()
                if not driver_info:
                    raise RuntimeError(f"No available drivers found for {self._dialect.description}")

            # Attempt connection
            self._connection = self._create_connection_with_driver(driver_info)
            self._current_driver = driver_info
            self._state = ConnectionState.CONNECTED

            return True

        except Exception as e:
            self._state = ConnectionState.ERROR
            self._connection = None
            self._current_driver = None
            logger.error(f"Connection failed: {e}", emoji="💥")
            return False

    def disconnect(self) -> bool:
        """Close the database connection."""
        try:
            if self._connection and self._state == ConnectionState.CONNECTED:
                if isinstance(self._connection, dict):
                    # Handle special connection types
                    conn_type = self._connection.get("type")
                    if conn_type == "pandas_gbq":
                        # pandas-gbq doesn't need explicit closing
                        pass
                    elif conn_type == "sqlalchemy":
                        # Close SQLAlchemy engine
                        engine = self._connection.get("engine")
                        if engine and hasattr(engine, "dispose"):
                            engine.dispose()
                elif hasattr(self._connection, "close"):
                    self._connection.close()

                logger.trace(f"Disconnected from {self._dialect.description}", emoji="🔌")

            self._connection = None
            self._current_driver = None
            self._state = ConnectionState.DISCONNECTED
            return True

        except Exception as e:
            logger.error(f"Error during disconnection: {e}", emoji="❌")
            self._state = ConnectionState.ERROR
            return False

    def reconnect(self, driver_name: Optional[str] = None) -> bool:
        """Reconnect using the same or different driver."""
        logger.trace(f"Attempting to reconnect to {self._dialect.description}", emoji="🔄")
        self.disconnect()
        return self.connect(driver_name)

    def get_raw_connection(self):
        """Get the raw database connection object for RobustTransaction."""
        if not self.is_connected:
            raise RuntimeError("Connection not established")
        return self._connection

    def _ensure_connected_for_operation(self, operation_name: str):
        """Helper to ensure connection is established for an operation."""
        if not self.is_connected:
            raise RuntimeError(f"Not connected to {self._dialect.description} database for {operation_name}")

    def get_env_db_config(self):
        """Return a dict of DB config values for the given prefix."""
        prefix = self._dialect.name.upper()
        env_keys = [k for k in os.environ if k.startswith(prefix + "_")]
        return {k[len(prefix) + 1 :].lower(): os.environ[k] for k in env_keys}

    def copy(self, auto_connect: bool = False) -> "DatabaseConnection":
        """Create a deep copy of this DatabaseConnection with the same configuration."""
        # Create deep copy of connection parameters
        connection_params_copy = copy_module.deepcopy(self._connection_params)
        driver_options_copy = copy_module.deepcopy(self._driver_options)
        connection_options_copy = copy_module.deepcopy(self._connection_options)

        # Create new instance with same configuration
        new_connection = DatabaseConnection(
            dialect=self._dialect,
            pull_from_env=False,  # Don't pull from env again, use copied params
            driver_options=driver_options_copy,
            connection_options=connection_options_copy,
            auto_connect=auto_connect,
            fast_executemany=self._fast_executemany,
            **connection_params_copy,
        )

        return new_connection

    # ALL EXECUTION METHODS DELEGATE TO ROBUSTTRANSACTION

    def execute_query(self, query: str, parameters: Optional[Union[Tuple, Dict[str, Any]]] = None, **kwargs) -> Any:
        """Execute a SQL query using RobustTransaction."""
        self._ensure_connected_for_operation("execute_query")

        with RobustTransaction(self, **kwargs) as tx:
            return tx.execute(query, parameters)

    def execute_query_with_metadata(
        self, query: str, parameters: Optional[Union[Tuple, Dict[str, Any]]] = None, **kwargs
    ) -> Any:
        """Execute a SQL query and return results with metadata using RobustTransaction."""
        self._ensure_connected_for_operation("execute_query_with_metadata")

        with RobustTransaction(self, **kwargs) as tx:
            return tx.execute(query, parameters, include_metadata=True)

    def bulk_insert(
        self,
        sql: str,
        data: List[Union[Tuple, List, Dict[str, Any]]],
        chunk_size: Optional[int] = None,
        on_conflict: Optional[str] = None,
        **kwargs,
    ) -> int:
        """Perform optimized bulk insert using RobustTransaction."""
        self._ensure_connected_for_operation("bulk_insert")

        with RobustTransaction(self, **kwargs) as tx:
            return tx.bulk_insert(sql, data, chunk_size, on_conflict)

    def execute_many(
        self,
        query: str,
        parameters_list: List[Union[Tuple, Dict[str, Any]]],
        chunk_size: Optional[int] = None,
        **kwargs,
    ) -> int:
        """Execute a query multiple times with different parameters using RobustTransaction."""
        self._ensure_connected_for_operation("execute_many")

        with RobustTransaction(self, **kwargs) as tx:
            return tx.execute_many(query, parameters_list, chunk_size)

    def execute_batch(self, query: str, parameters_list: List[Union[Tuple, Dict[str, Any]]], **kwargs) -> List[Any]:
        """Execute a batch of queries using RobustTransaction."""
        self._ensure_connected_for_operation("execute_batch")

        with RobustTransaction(self, **kwargs) as tx:
            return tx.execute_batch(query, parameters_list)

    @contextmanager
    def transaction(self, **kwargs):
        """Context manager for database transactions using RobustTransaction."""
        self._ensure_connected_for_operation("transaction")

        with RobustTransaction(self, **kwargs) as tx:
            yield tx

    def test_connection(self) -> Dict[str, Any]:
        """Test the database connection and return diagnostic information."""
        result = {
            "connected": False,
            "driver": None,
            "dialect": self._dialect.name_value,
            "test_query_success": False,
            "error": None,
        }

        try:
            if self._state != ConnectionState.CONNECTED:
                if not self.connect():
                    result["error"] = "Failed to establish connection"
                    return result

            result["connected"] = True
            result["driver"] = self._current_driver["name"] if self._current_driver else None

            # Use the test query for this dialect
            test_query = _TEST_QUERIES.get(self._dialect, "SELECT 1")
            self.execute_query(test_query)
            result["test_query_success"] = True

        except Exception as e:
            result["error"] = str(e)

        return result

    def to_sqlalchemy(self, **engine_kwargs) -> Any:
        """
        Create a SQLAlchemy engine from the current connection parameters.

        This method uses the existing DatabaseConnectionFactory to create a SQLAlchemy engine
        regardless of the current connection type, making it compatible with pandas.to_sql()
        and other SQLAlchemy-based operations.

        Args:
            **engine_kwargs: Additional arguments passed to sqlalchemy.create_engine()

        Returns:
            SQLAlchemy engine object

        Raises:
            ImportError: If SQLAlchemy is not available
            ValueError: If connection parameters are insufficient for SQLAlchemy

        Examples:
            >>> conn = DatabaseConnection('postgresql')
            >>> engine = conn.to_sqlalchemy()
            >>> df.to_sql('table_name', con=engine, if_exists='replace')
        """
        try:
            # Map dialect to SQLAlchemy drivername
            drivername_mapping = {
                SQLDialect.POSTGRES: "postgresql+psycopg2",
                SQLDialect.MYSQL: "mysql+pymysql",
                SQLDialect.SQLITE: "sqlite",
                SQLDialect.SQLSERVER: "mssql+pyodbc",
                SQLDialect.ORACLE: "oracle+oracledb",
                SQLDialect.BIGQUERY: "bigquery",
                SQLDialect.REDSHIFT: "redshift+psycopg2",
            }

            if self._dialect not in drivername_mapping:
                raise ValueError(f"Dialect {self._dialect} is not supported for SQLAlchemy connections")

            # Create enhanced connection params with drivername
            enhanced_params = self._connection_params.copy()
            enhanced_params["drivername"] = drivername_mapping[self._dialect]

            # Use the existing factory to create SQLAlchemy connection
            connection_result = DatabaseConnectionFactory.create_connection(
                driver_name="SQLAlchemy", connection_params=enhanced_params, connection_options=engine_kwargs
            )

            # Extract the engine from the connection result
            if isinstance(connection_result, dict) and connection_result.get("type") == "sqlalchemy":
                engine = connection_result["engine"]
                logger.debug(f"Created SQLAlchemy engine for {self._dialect.description}", emoji="🔧")
                return engine
            else:
                raise RuntimeError("Failed to create SQLAlchemy engine through factory")

        except ImportError:
            raise ImportError("SQLAlchemy is required for to_sqlalchemy(). Install with: pip install sqlalchemy")
        except Exception as e:
            logger.error(f"SQLAlchemy engine creation failed: {e}", emoji="❌")
            raise

    def to_jdbc(self) -> Dict[str, Any]:
        """
        Generate JDBC connection URL and properties for PySpark integration.

        This method creates JDBC connection information that can be used with
        PySpark's DataFrame.read.jdbc() and DataFrame.write.jdbc() methods.

        Returns:
            Dictionary containing:
            - 'url': JDBC connection URL
            - 'properties': Connection properties dictionary
            - 'driver': JDBC driver class name

        Raises:
            ValueError: If dialect is not supported for JDBC connections

        Examples:
            >>> conn = DatabaseConnection('postgresql')
            >>> jdbc_config = conn.to_jdbc()
            >>> spark_df = spark.read.jdbc(
            ...     url=jdbc_config['url'],
            ...     table='my_table',
            ...     properties=jdbc_config['properties']
            ... )
        """
        params = self._connection_params
        host = params.get("host")
        database = params.get("database")
        port = params.get("port")
        username = params.get("username")
        password = params.get("password")

        # Build JDBC URL and driver based on dialect
        if self._dialect == SQLDialect.POSTGRES:
            port = port or 5432
            jdbc_url = f"jdbc:postgresql://{host}:{port}/{database}"
            properties = {
                "fetchsize": "10000",
                "batchsize": "10000",
                "reWriteBatchedInserts": "true",
                "driver": "org.postgresql.Driver",
            }

        elif self._dialect == SQLDialect.MYSQL:
            port = port or 3306
            jdbc_url = f"jdbc:mysql://{host}:{port}/{database}"
            properties = {
                "fetchSize": "10000",
                "rewriteBatchedStatements": "true",
                "useServerPrepStmts": "false",
                "useSSL": "false",
                "allowPublicKeyRetrieval": "true",
                "driver": "com.mysql.cj.jdbc.Driver",
            }

        elif self._dialect == SQLDialect.SQLSERVER:
            port = port or 1433
            jdbc_url = f"jdbc:sqlserver://{host}:{port};databaseName={database}"
            properties = {
                "fetchsize": "10000",
                "batchsize": "10000",
                "encrypt": "false",
                "trustServerCertificate": "true",
                "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
            }

        elif self._dialect == SQLDialect.ORACLE:
            port = port or 1521
            service_name = params.get("service_name", database)
            jdbc_url = f"jdbc:oracle:thin:@{host}:{port}:{service_name}"

            properties = {"fetchsize": "5000", "batchsize": "5000", "driver": "oracle.jdbc.OracleDriver"}

        elif self._dialect == SQLDialect.SQLITE:
            jdbc_url = f"jdbc:sqlite:{database}"
            properties = {"driver": "org.sqlite.JDBC"}

        elif self._dialect == SQLDialect.REDSHIFT:
            port = port or 5439
            jdbc_url = f"jdbc:redshift://{host}:{port}/{database}"
            properties = {"driver": "com.amazon.redshift.jdbc.Driver"}

        else:
            raise ValueError(f"JDBC not supported for dialect: {self._dialect.name_value}")

        # Add authentication to properties
        if username:
            properties["user"] = username
        if password:
            properties["password"] = password

        result = {"url": jdbc_url, "properties": properties}

        logger.debug(f"Generated JDBC configuration for {self._dialect.description}", emoji="🔌")
        return result

    def read_sql_connector_x(
        self,
        query: str,
        return_type: Literal["arrow", "arrow_stream", "pandas", "modin", "dask", "polars"] = "pandas",
        partition_on: Optional[str] = None,
        partition_range: Optional[Tuple[int, int]] = None,
        partition_num: Optional[int] = None,
        index_col: Optional[str] = None,
        protocol: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Execute a SQL query using ConnectorX for high-performance data loading.

        This method uses ConnectorX's read_sql function with the automatically
        generated connection URI from this connection's parameters.

        Args:
            query: SQL query to execute
            return_type: Output DataFrame type. Must be one of: 'pandas', 'arrow', 'polars'
            partition_on: Column name for partitioning large datasets
            partition_range: Tuple of (min_value, max_value) for partitioning range (integers only)
            partition_num: Number of partitions to create for parallel processing
            index_col: Column to use as DataFrame index (pandas only)
            protocol: Communication protocol. Must be one of: 'binary', 'csv', 'cursor', 'simple', 'text'
                     None uses ConnectorX default (typically 'binary' for best performance)
            **kwargs: Additional arguments passed to connectorx.read_sql()

        Returns:
            DataFrame (pandas, polars, or arrow depending on return_type)

        Raises:
            ImportError: If ConnectorX is not available
            ValueError: If dialect is not supported by ConnectorX or invalid parameter values
            RuntimeError: If connection parameters are insufficient

        Examples:
            >>> conn = DatabaseConnection('postgresql')
            >>> df = conn.read_sql_connector_x("SELECT * FROM large_table")
            >>>
            >>> # Use with partitioning for large datasets
            >>> df = conn.read_sql_connector_x(
            ...     query="SELECT * FROM large_table WHERE id BETWEEN ? AND ?",
            ...     partition_on="id",
            ...     partition_range=(1, 1000000),
            ...     partition_num=4,
            ...     return_type="pandas"
            ... )
            >>>
            >>> # Return as Polars DataFrame with specific protocol
            >>> df = conn.read_sql_connector_x(
            ...     query="SELECT * FROM table",
            ...     return_type="polars",
            ...     protocol="binary"
            ... )
            >>>
            >>> # Return as Arrow Table
            >>> table = conn.read_sql_connector_x(
            ...     query="SELECT * FROM table",
            ...     return_type="arrow"
            ... )
        """
        try:
            import connectorx as cx
        except ImportError:
            raise ImportError("ConnectorX is required for read_sql_connector_x(). Install with: pip install connectorx")

        # Validate return_type parameter
        valid_return_types = {"arrow", "arrow_stream", "pandas", "modin", "dask", "polars"}
        if return_type not in valid_return_types:
            raise ValueError(f"return_type must be one of {valid_return_types}, got: {return_type}")

        # Validate protocol parameter if provided
        if protocol is not None:
            valid_protocols = {"binary", "csv", "cursor", "simple", "text"}
            if protocol not in valid_protocols:
                raise ValueError(f"protocol must be one of {valid_protocols}, got: {protocol}")

        # Validate partitioning parameters
        if partition_on is not None:
            if partition_range is None or partition_num is None:
                raise ValueError(
                    "When partition_on is specified, both partition_range and partition_num must be provided"
                )

            if len(partition_range) != 2:
                raise ValueError("partition_range must be a tuple of (min_value, max_value)")

            if partition_num <= 0:
                raise ValueError("partition_num must be a positive integer")

        try:
            # Get the ConnectorX-compatible connection URI
            conn_uri = self.connectorx_uri

            # Execute query using ConnectorX with explicit parameters
            logger.debug(
                f"Executing ConnectorX query for {self._dialect.description} with return_type={return_type}", emoji="🚀"
            )

            start_time = time.time()

            # Build parameters dict, filtering out None values
            cx_params = {}
            if return_type is not None:
                cx_params["return_type"] = return_type
            if partition_on is not None:
                cx_params["partition_on"] = partition_on
                cx_params["partition_range"] = partition_range
                cx_params["partition_num"] = partition_num
            if index_col is not None:
                cx_params["index_col"] = index_col
            if protocol is not None:
                cx_params["protocol"] = protocol

            # Merge with any additional kwargs
            cx_params.update(kwargs)

            # Call ConnectorX with filtered parameters
            result = cx.read_sql(conn_uri, query, **cx_params)

            execution_time = time.time() - start_time

            # Log performance information with different checks for different return types
            if hasattr(result, "shape"):
                # pandas DataFrame or similar
                rows, cols = result.shape
                logger.debug(
                    f"ConnectorX query completed: {rows:,} rows × {cols} cols in {execution_time:.3f}s", emoji="⚡"
                )
            elif return_type == "arrow" and hasattr(result, "num_rows") and hasattr(result, "num_columns"):
                # Arrow Table
                rows, cols = result.num_rows, result.num_columns
                logger.debug(
                    f"ConnectorX query completed: {rows:,} rows × {cols} cols in {execution_time:.3f}s", emoji="⚡"
                )
            elif return_type == "polars" and hasattr(result, "height") and hasattr(result, "width"):
                # Polars DataFrame
                rows, cols = result.height, result.width
                logger.debug(
                    f"ConnectorX query completed: {rows:,} rows × {cols} cols in {execution_time:.3f}s", emoji="⚡"
                )
            else:
                logger.debug(f"ConnectorX query completed in {execution_time:.3f}s", emoji="⚡")

            return result

        except Exception as e:
            logger.error(f"ConnectorX query failed: {e}", emoji="❌")
            raise

    def __enter__(self):
        """Context manager entry."""
        if not self.is_connected:
            if not self.connect():
                raise RuntimeError(f"Failed to establish connection to {self._dialect.description}")
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        """Context manager exit."""
        self.disconnect()

    def __repr__(self) -> str:
        """String representation of the connection."""
        driver_name = self._current_driver["name"] if self._current_driver else "None"
        return (
            f"DatabaseConnection(dialect={self._dialect.name_value}, "
            f"state={self._state.value}, driver={driver_name})"
        )
