"""
Driver Connection Builder.

This module provides the connection builder class that handles parameter mapping,
validation, and connection string construction for database drivers. It serves as
the bridge between generic connection parameters and driver-specific requirements.

Classes
-------
DriverConnectionBuilder
    Builds database connections using driver-specific configurations.

Notes
-----
The builder handles several key responsibilities:
1. Parameter mapping: Converts generic parameters (host, database, user) to
   driver-specific names (e.g., 'database' -> 'dbname' for psycopg3).
2. Parameter validation: Ensures required parameters are present and supported.
3. Type conversion: Converts string booleans and integers to proper types.
4. ODBC string construction: Builds ODBC connection strings for pyodbc.
5. Windows authentication detection: Determines when to use Windows auth.

Author
------
DataScience ToolBox
"""

from typing import Any, Dict, List, Optional

# Use try/except to handle both absolute and relative imports
try:
    from core.enums import SQLDialect
except ImportError:
    from ..core.enums import SQLDialect

try:
    from drivers.models import DriverConfig
except ImportError:
    from .models import DriverConfig

from CoreUtilities import LogLevel, get_logger

# Configure logging
logger = get_logger("driver_builder", level=LogLevel.WARNING, include_performance=True, include_emoji=True)


class DriverConnectionBuilder:
    """
    Builds database connections using driver-specific configurations.

    This class handles the translation between generic connection parameters
    and driver-specific parameter names, formats, and requirements. It provides
    parameter validation, type conversion, and connection string construction.

    Attributes
    ----------
    config : DriverConfig
        The driver configuration containing parameter mappings, supported options,
        and other driver-specific metadata.

    Methods
    -------
    build_connection_params(connection_params, additional_options)
        Build driver-specific connection parameters from generic parameters.
    should_use_windows_auth(connection_params)
        Determine if Windows Authentication should be used.
    build_odbc_connection_string(connection_params, detected_driver)
        Build ODBC connection string for drivers that require it.
    validate_parameters(connection_params)
        Validate connection parameters for this driver.
    build(connection_params, connection_options)
        Public wrapper around build_connection_params.

    Examples
    --------
    >>> config = get_driver_config('psycopg2')
    >>> builder = DriverConnectionBuilder(config)
    >>> params = builder.build_connection_params({
    ...     'host': 'localhost',
    ...     'database': 'mydb',
    ...     'user': 'myuser',
    ...     'password': 'mypass'
    ... })
    """

    def __init__(self, driver_config: DriverConfig):
        """
        Initialize the connection builder with a driver configuration.

        Parameters
        ----------
        driver_config : DriverConfig
            Configuration for the database driver.
        """
        self.config = driver_config

    def _convert_parameter_value(self, param_name: str, value: Any) -> Any:
        """
        Convert parameter values to appropriate types based on parameter name.

        Many database drivers expect boolean and integer values as actual Python
        types rather than strings. This method automatically converts string
        representations to the appropriate types based on known parameter names.

        Parameters
        ----------
        param_name : str
            Parameter name in lowercase (e.g., 'ssl', 'port', 'timeout').
        value : Any
            Parameter value to convert. If already the correct type, returns as-is.

        Returns
        -------
        Any
            Converted parameter value with the appropriate type.

        Notes
        -----
        Boolean parameters recognized: ssl, ssl_insecure, iam, auto_create,
        force_lowercase, allow_db_user_override, database_metadata_current_db_only,
        iam_disable_cache, tcp_keepalive.

        Integer parameters recognized: port, timeout, max_prepared_statements,
        idp_response_timeout, listen_port, client_protocol_version.
        """
        # Boolean parameters that should be converted from strings to booleans.
        # These are common flags used across various database drivers.
        boolean_params = {
            "ssl",
            "ssl_insecure",
            "iam",
            "auto_create",
            "force_lowercase",
            "allow_db_user_override",
            "database_metadata_current_db_only",
            "iam_disable_cache",
            "tcp_keepalive",
        }

        # Integer parameters that should be converted from strings to integers.
        # These are typically numeric settings like ports and timeouts.
        integer_params = {
            "port",
            "timeout",
            "max_prepared_statements",
            "idp_response_timeout",
            "listen_port",
            "client_protocol_version",
        }

        if param_name in boolean_params and isinstance(value, str):
            # Convert string boolean values to actual booleans.
            # Supports common representations: true/false, yes/no, 1/0, on/off.
            value_lower = value.lower()
            if value_lower in ("true", "1", "yes", "on"):
                return True
            elif value_lower in ("false", "0", "no", "off"):
                return False
            else:
                # If it's not a recognizable boolean string, return as-is to preserve the value.
                return value

        elif param_name in integer_params and isinstance(value, str):
            # Convert string integer values to actual integers.
            try:
                return int(value)
            except ValueError:
                # If it's not a valid integer string, return as-is to preserve the value.
                return value

        return value

    def build_connection_params(
        self, connection_params: Dict[str, Any], additional_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build driver-specific connection parameters from generic parameters.

        This method performs the core parameter mapping functionality by:
        1. Mapping generic parameter names to driver-specific names
        2. Applying default values where configured
        3. Converting parameter types (string booleans to bool, etc.)
        4. Including supported additional kwargs
        5. Validating required parameters

        Parameters
        ----------
        connection_params : Dict[str, Any]
            Generic connection parameters using standard names like 'host',
            'database', 'user', 'password', 'port'.
        additional_options : Optional[Dict[str, Any]], optional
            Additional driver-specific options to include, by default None.

        Returns
        -------
        Dict[str, Any]
            Driver-specific connection parameters ready to pass to the driver's
            connect() function. Parameter names and types are driver-specific.

        Raises
        ------
        ValueError
            If a required parameter is missing and has no default value.

        Examples
        --------
        >>> # For psycopg3, 'database' maps to 'dbname'
        >>> params = builder.build_connection_params({'database': 'mydb'})
        >>> print(params)
        {'dbname': 'mydb'}
        """
        driver_params = {}
        additional_options = additional_options or {}

        # Map generic parameters to driver-specific parameter names.
        # For example, 'database' might map to 'dbname' for psycopg3 or 'db' for MySQLdb.
        for generic_name, mapping in self.config.parameter_mappings.items():
            value = connection_params.get(generic_name)

            if value is not None:
                # Convert parameter value to appropriate type (e.g., string "true" to boolean True).
                converted_value = self._convert_parameter_value(mapping.driver_param.lower(), value)
                driver_params[mapping.driver_param] = converted_value
            elif mapping.default_value is not None:
                # Use the configured default value if parameter not provided.
                converted_value = self._convert_parameter_value(mapping.driver_param.lower(), mapping.default_value)
                driver_params[mapping.driver_param] = converted_value
            elif mapping.required:
                # Check if any alias provides this parameter (e.g., project_id -> project)
                # Look for other parameter mappings that output to the same driver_param
                alias_value = None
                for other_name, other_mapping in self.config.parameter_mappings.items():
                    if (
                        other_name != generic_name
                        and other_mapping.driver_param == mapping.driver_param
                        and connection_params.get(other_name) is not None
                    ):
                        alias_value = connection_params.get(other_name)
                        break

                if alias_value is not None:
                    # Use the alias value
                    converted_value = self._convert_parameter_value(mapping.driver_param.lower(), alias_value)
                    driver_params[mapping.driver_param] = converted_value
                else:
                    # Raise error if required parameter is missing and has no default or alias.
                    raise ValueError(f"Required parameter '{generic_name}' not provided for {self.config.name}")

        # Add supported kwargs that aren't in the parameter mappings.
        # These are additional options specific to the driver (e.g., 'sslmode', 'charset').
        for key, value in connection_params.items():
            if (
                key.lower() in [k.lower() for k in self.config.supported_kwargs]
                and key not in self.config.parameter_mappings
                and value is not None
            ):
                # Convert string booleans and integers to proper types.
                converted_value = self._convert_parameter_value(key.lower(), value)
                driver_params[key.lower()] = converted_value

        # Add additional options provided separately.
        # These override any conflicting parameters from connection_params.
        for key, value in additional_options.items():
            if key.lower() in [k.lower() for k in self.config.supported_kwargs]:
                driver_params[key.lower()] = value

        return driver_params

    def should_use_windows_auth(self, connection_params: Dict[str, Any]) -> bool:
        """
        Determine if Windows Authentication should be used.

        This method checks various indicators to determine if Windows/Integrated
        Authentication should be used instead of username/password authentication.
        Only applicable for drivers that support Windows authentication (primarily
        SQL Server drivers).

        Parameters
        ----------
        connection_params : Dict[str, Any]
            Connection parameters to check for Windows auth indicators.

        Returns
        -------
        bool
            True if Windows Authentication should be used, False otherwise.

        Notes
        -----
        Windows auth is detected through:
        1. Explicit flags: trusted_connection, integrated_security
        2. Authentication type: authentication='windows' or 'ActiveDirectoryIntegrated'
        3. Implicit: no username/password provided and driver supports Windows auth
        """
        # Only proceed if the driver supports Windows authentication.
        if not self.config.supports_windows_auth:
            return False

        # Check explicit Windows authentication flags.
        trusted_conn = connection_params.get("trusted_connection", "").lower()
        integrated_sec = connection_params.get("integrated_security", "").lower()
        authentication = connection_params.get("authentication", "").lower()

        # Return True if any explicit Windows auth flag is set.
        if (
            integrated_sec in ["yes", "true", "1"]
            or trusted_conn in ["yes", "true", "1"]
            or authentication in ["windows", "activedirectoryintegrated"]
        ):
            return True

        # Implicit Windows auth: if no credentials provided and driver supports it.
        # This is a convenience feature for Windows environments.
        if (
            not connection_params.get("username")
            and not connection_params.get("password")
            and self.config.supports_windows_auth
        ):
            return True

        return False

    def build_odbc_connection_string(
        self, connection_params: Dict[str, Any], detected_driver: Optional[str] = None
    ) -> str:
        """
        Build ODBC connection string for drivers that require it.

        Constructs a semicolon-delimited ODBC connection string with proper
        formatting for parameter names and values. Handles special cases like:
        - Windows authentication (Trusted_Connection)
        - SQL Server port notation (server,port)
        - ODBC-specific parameter names (TrustServerCertificate, etc.)

        Parameters
        ----------
        connection_params : Dict[str, Any]
            Generic connection parameters to convert to ODBC format.
        detected_driver : Optional[str], optional
            Auto-detected ODBC driver name to use in the connection string.
            If provided, overrides any driver specified in connection_params.

        Returns
        -------
        str
            Formatted ODBC connection string (e.g., "DRIVER={...};SERVER=...;DATABASE=...").

        Raises
        ------
        ValueError
            If driver does not use ODBC connection string format.

        Examples
        --------
        >>> conn_str = builder.build_odbc_connection_string(
        ...     {'host': 'localhost', 'database': 'mydb'},
        ...     'ODBC Driver 18 for SQL Server'
        ... )
        >>> print(conn_str)
        'DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=mydb'
        """
        if not self.config.connection_string_format == "odbc_string":
            raise ValueError(f"Driver {self.config.name} does not use ODBC connection strings")

        conn_parts = []
        processed_params = set()

        # Add detected driver if provided (prefer auto-detected over environment driver)
        if detected_driver:
            conn_parts.append(f"DRIVER={{{detected_driver}}}")
            processed_params.add("driver")
        elif "driver" in connection_params:
            driver_name = connection_params["driver"]
            if not driver_name.startswith("{"):
                driver_name = f"{{{driver_name}}}"
            conn_parts.append(f"DRIVER={driver_name}")
            processed_params.add("driver")

        # Handle Windows Authentication first to avoid conflicts
        use_windows_auth = self.should_use_windows_auth(connection_params)
        if use_windows_auth:
            conn_parts.append("Trusted_Connection=yes")
            processed_params.update(["trusted_connection", "username", "password"])

        # Map standard parameters (skip already processed ones)
        for generic_name, mapping in self.config.parameter_mappings.items():
            if generic_name in processed_params:
                continue

            value = connection_params.get(generic_name)
            if value is not None:
                # Special handling for trusted_connection to avoid conflicts
                if generic_name == "trusted_connection" and use_windows_auth:
                    continue
                conn_parts.append(f"{mapping.driver_param}={value}")
                processed_params.add(generic_name)

        # Add supported additional parameters
        odbc_param_mappings = {
            "timeout": "Connection Timeout",
            "command_timeout": "Command Timeout",
            "connection_timeout": "Connection Timeout",
            "trustservercertificate": "TrustServerCertificate",
            "trust_server_certificate": "TrustServerCertificate",  # Handle underscore version
            "encrypt": "Encrypt",
            "multisubnetfailover": "MultiSubnetFailover",
            "applicationintent": "ApplicationIntent",
            "failoverpartner": "Failover_Partner",
            "attachdbfilename": "AttachDbFilename",
            "workstation_id": "Workstation ID",
            "app_name": "APP",
            "language": "Language",
            "packet_size": "Packet Size",
            "mars_connection": "MARS_Connection",
        }

        # Special handling for SQL Server port - needs to be part of server name
        server_name = connection_params.get("server", connection_params.get("host", "localhost"))
        port = connection_params.get("port")
        if port and server_name and "," not in server_name:
            # Update server in the connection parts
            for i, part in enumerate(conn_parts):
                if part.startswith("SERVER="):
                    conn_parts[i] = f"SERVER={server_name},{port}"
                    processed_params.add("port")
                    break

        for key, value in connection_params.items():
            if key in processed_params or value is None:
                continue

            # Check if this parameter should be mapped to ODBC format
            odbc_key = odbc_param_mappings.get(key.lower())
            if odbc_key:
                conn_parts.append(f"{odbc_key}={value}")
            elif key.lower() in [k.lower() for k in self.config.supported_kwargs] and key.lower() not in [
                m.param_name.lower() for m in self.config.parameter_mappings.values()
            ]:
                # Pass through unknown but supported parameters
                conn_parts.append(f"{key}={value}")

        connection_string = ";".join(conn_parts)
        logger.debug(f"ODBC connection string generated for {self.config.name}")

        return connection_string

    def validate_parameters(self, connection_params: Dict[str, Any]) -> List[str]:
        """
        Validate connection parameters for this driver.

        Checks that all required parameters are present and logs warnings for
        unrecognized parameters. Does not raise exceptions but returns a list
        of validation error messages.

        Parameters
        ----------
        connection_params : Dict[str, Any]
            Connection parameters to validate against the driver configuration.

        Returns
        -------
        List[str]
            List of validation error messages. Empty list if all validations pass.
            Errors indicate missing required parameters.

        Notes
        -----
        Unrecognized parameters generate debug log messages but not errors,
        allowing forward compatibility with new driver features.

        Examples
        --------
        >>> errors = builder.validate_parameters({'host': 'localhost'})
        >>> if errors:
        ...     print("Validation failed:", errors)
        """
        errors = []

        # Check required parameters to ensure all mandatory configuration is present.
        # For parameters that have aliases (multiple input names mapping to same output),
        # check if ANY of the aliases are provided
        for generic_name, mapping in self.config.parameter_mappings.items():
            if mapping.required and connection_params.get(generic_name) is None:
                # Only report error if there's no default value to fall back on.
                if mapping.default_value is None:
                    # Check if any other parameter mapping produces the same output (alias)
                    has_alias = any(
                        connection_params.get(other_name) is not None
                        and other_mapping.driver_param == mapping.driver_param
                        for other_name, other_mapping in self.config.parameter_mappings.items()
                        if other_name != generic_name
                    )
                    if not has_alias:
                        errors.append(f"Required parameter '{generic_name}' missing for {self.config.name}")

        # Check for unsupported parameters to help catch typos and configuration issues.
        # Build list of all parameters this driver recognizes.
        all_supported = list(self.config.parameter_mappings.keys()) + [k.lower() for k in self.config.supported_kwargs]

        # Log warnings for unrecognized parameters but don't treat as errors.
        # This allows forward compatibility with new driver features.
        for param in connection_params:
            if param.lower() not in [p.lower() for p in all_supported]:
                logger.debug(f"Parameter '{param}' not recognized for {self.config.name} driver")

        return errors

    def build(
        self, connection_params: Dict[str, Any], connection_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build connection parameters for the driver.

        This is a public wrapper around build_connection_params() that provides
        a simpler, more intuitive API for external callers.

        Parameters
        ----------
        connection_params : Dict[str, Any]
            Generic connection parameters using standard names.
        connection_options : Optional[Dict[str, Any]], optional
            Additional driver-specific connection options, by default None.

        Returns
        -------
        Dict[str, Any]
            Driver-specific connection parameters ready to pass to the driver's
            connect() function.

        Examples
        --------
        >>> params = builder.build({'host': 'localhost', 'database': 'mydb'})
        """
        return self.build_connection_params(connection_params, connection_options or {})
