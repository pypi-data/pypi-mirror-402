"""
Driver Models and Configuration Classes.

This module contains shared data models used by the driver system. It was
extracted from the registry module to avoid circular dependencies between
the registry and builder modules.

Classes
-------
ParameterMapping
    Maps generic parameter names to driver-specific parameter names.
DriverConfig
    Complete configuration for a specific database driver.

Notes
-----
These dataclasses provide type-safe configuration for the driver system:

ParameterMapping defines how to translate a single parameter:
- param_name: Generic name (e.g., 'database')
- driver_param: Driver-specific name (e.g., 'dbname' for psycopg3)
- required: Whether this parameter must be provided
- default_value: Default value if not provided
- validator: Optional custom validation function

DriverConfig defines a complete driver configuration:
- name: Driver identifier
- dialect: SQL dialect this driver supports
- module_name: Python module to import
- import_names: List of names to import
- connection_builder: Factory method name
- parameter_mappings: Dict of ParameterMapping objects
- supported_kwargs: Additional supported options
- connection_string_format: Format for connection strings (e.g., 'odbc_string')
- requires_dsn: Whether driver requires DSN construction
- supports_windows_auth: Whether driver supports Windows authentication
- priority: Driver selection priority (higher = preferred)
- optimal_chunk_size: Recommended batch size for bulk operations

Author
------
DataScience ToolBox
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

# Import SQLDialect from core.enums - this is safe as core has no dependencies on drivers
# Use absolute import to work with pytest test discovery
try:
    from core.enums import SQLDialect
except ImportError:
    from ..core.enums import SQLDialect


@dataclass
class ParameterMapping:
    """
    Maps generic parameter names to driver-specific parameter names.

    This class defines how a single connection parameter should be mapped
    from a generic name to a driver-specific name, along with requirements
    and default values.

    Attributes
    ----------
    param_name : str
        Generic parameter name used across all drivers (e.g., 'database', 'user', 'host').
    driver_param : str
        Driver-specific parameter name (e.g., 'dbname' for psycopg3, 'db' for MySQLdb).
    required : bool, optional
        Whether this parameter is required for the driver, by default False.
    default_value : Any, optional
        Default value to use if parameter not provided, by default None.
    validator : Optional[Callable], optional
        Optional custom validation function for the parameter value, by default None.

    Examples
    --------
    >>> # Map 'database' to 'dbname' for psycopg3, required
    >>> mapping = ParameterMapping(
    ...     param_name='database',
    ...     driver_param='dbname',
    ...     required=True
    ... )
    >>> # Map 'port' with a default value
    >>> mapping = ParameterMapping(
    ...     param_name='port',
    ...     driver_param='port',
    ...     default_value=5432
    ... )
    """

    param_name: str  # Generic parameter name (e.g., 'database')
    driver_param: str  # Driver-specific parameter name (e.g., 'dbname' for psycopg)
    required: bool = False  # Whether this parameter is required
    default_value: Any = None  # Default value if not provided
    validator: Optional[Callable] = None  # Optional validation function


@dataclass
class DriverConfig:
    """
    Configuration for a specific database driver.

    This dataclass contains all configuration metadata needed to use a database
    driver, including parameter mappings, supported options, and driver capabilities.

    Attributes
    ----------
    name : str
        Driver identifier (e.g., 'psycopg2', 'pyodbc', 'oracledb').
    dialect : Optional[SQLDialect]
        SQL dialect this driver supports. None for universal drivers like SQLAlchemy.
    module_name : str
        Python module name to import (e.g., 'psycopg2', 'pyodbc').
    import_names : List[str]
        List of names to import from the module.
    connection_builder : str
        Name of the factory method that builds connections for this driver.
    parameter_mappings : Dict[str, ParameterMapping]
        Dictionary mapping generic parameter names to driver-specific mappings.
    supported_kwargs : List[str]
        Additional keyword arguments this driver supports beyond mapped parameters.
    connection_string_format : Optional[str], optional
        Connection string format (e.g., 'odbc_string' for pyodbc), by default None.
    requires_dsn : bool, optional
        Whether driver requires DSN construction (e.g., cx_Oracle), by default False.
    supports_windows_auth : bool, optional
        Whether driver supports Windows/Integrated Authentication, by default False.
    priority : int, optional
        Driver selection priority where higher numbers are preferred, by default 1.
        Priority 1: ConnectorX (highest performance)
        Priority 2-6: Specialized/fallback drivers
        Priority 7-11: Standard Python drivers
    optimal_chunk_size : int, optional
        Recommended batch size for bulk operations, by default 1000.

    Examples
    --------
    >>> config = DriverConfig(
    ...     name='psycopg2',
    ...     dialect=SQLDialect.POSTGRES,
    ...     module_name='psycopg2',
    ...     import_names=['psycopg2'],
    ...     connection_builder='build_psycopg2_connection',
    ...     parameter_mappings={
    ...         'database': ParameterMapping('database', 'database', required=True)
    ...     },
    ...     supported_kwargs=['sslmode', 'connect_timeout'],
    ...     priority=9,
    ...     optimal_chunk_size=1000
    ... )
    """

    name: str
    dialect: Optional[SQLDialect]  # Use Optional for SQLAlchemy universal driver
    module_name: str
    import_names: List[str]
    connection_builder: str  # Method name to build connection
    parameter_mappings: Dict[str, ParameterMapping]
    supported_kwargs: List[str]  # Additional kwargs this driver supports
    connection_string_format: Optional[str] = None  # For ODBC-style connections
    requires_dsn: bool = False
    supports_windows_auth: bool = False
    priority: int = 1  # Higher number = higher priority for driver selection
    optimal_chunk_size: int = 1000  # Optimal chunk size for bulk operations
