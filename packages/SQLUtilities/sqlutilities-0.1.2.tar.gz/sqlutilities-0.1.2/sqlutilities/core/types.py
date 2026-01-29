"""
Core SQL Type Definitions.

This module provides a comprehensive type system for SQL column data types
across all major SQL database dialects. It enables consistent handling of
data types, cross-dialect compatibility, and proper type conversion.

The module contains three main components:

1. COLUMNDTYPE Enumeration
   A comprehensive enum of all column data types across SQL dialects including
   Oracle, PostgreSQL, SQL Server, MySQL, SQLite, BigQuery, and Redshift.
   Each data type includes detailed metadata about storage requirements,
   precision limits, supported dialects, and cross-dialect compatibility.

2. Column_Type NamedTuple
   A lightweight data structure representing a resolved column type with all
   dialect-specific properties materialized. This eliminates the need for
   runtime lookups of special_properties and provides efficient access to
   type metadata.

3. TemporalPrecision Class
   A utility class for calculating byte sizes of temporal data types (datetime,
   time, timestamp) based on precision level and dialect. Different dialects
   have varying storage requirements for temporal precision.

Type Categories
---------------
The COLUMNDTYPE enum organizes types into logical categories:
- numeric_integer: Integer types (TINYINT, SMALLINT, INTEGER, BIGINT, INT64)
- numeric_decimal: Fixed-point decimal types (DECIMAL, NUMERIC, NUMBER)
- numeric_float: Floating-point types (FLOAT, REAL, DOUBLE, BINARY_FLOAT)
- numeric_money: Currency types (MONEY, SMALLMONEY)
- text_fixed: Fixed-length text (CHAR, CHARACTER, NCHAR)
- text_variable: Variable-length text (VARCHAR, VARCHAR2, NVARCHAR)
- text_large: Large text objects (TEXT, CLOB, NTEXT)
- binary: Binary data (BINARY, VARBINARY, BLOB, BYTEA)
- time: Time types (TIME)
- date: Date types (DATE)
- datetime: Date/time types (DATETIME, DATETIME2, TIMESTAMP)
- boolean: Boolean types (BOOLEAN, BIT)
- json: JSON data types (JSON, JSONB)
- xml: XML data types (XML)
- uuid: UUID/GUID types (UUID, UNIQUEIDENTIFIER)
- spatial: Geometric/geographic types (GEOMETRY, GEOGRAPHY)

Cross-Dialect Compatibility
----------------------------
Each data type includes dialect_overrides mapping unsupported types to
equivalent types in other dialects. For example:
- Oracle's NUMBER maps to DECIMAL in other dialects
- SQL Server's DATETIME2 maps to TIMESTAMP in PostgreSQL
- BigQuery's INT64 maps to BIGINT in traditional databases

Author
------
DataScience ToolBox

Examples
--------
>>> from core.types import COLUMNDTYPE, Column_Type
>>> # Get a data type and check its properties
>>> dtype = COLUMNDTYPE.VARCHAR
>>> print(dtype.category)
text_variable
>>> print(dtype.description)
Variable-length character string
>>> # Get dialect-specific type information
>>> pg_varchar = dtype.get_types_for_dialect(SQLDialect.POSTGRES)
>>> print(pg_varchar.max_bytes)
10485760
>>> # Check cross-dialect compatibility
>>> oracle_type, params = COLUMNDTYPE.get_dialect_compatible_type(
...     COLUMNDTYPE.VARCHAR, SQLDialect.ORACLE
... )
>>> print(oracle_type.name_value)
varchar2
"""

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Literal, NamedTuple, Optional, Tuple, Union

from .enums import DatabaseObjectType, SQLDialect
from CoreUtilities.core_types import CoreDataType

# Avoid circular import - import SQL_DIALECT_REGISTRY only when type checking or at runtime when needed.
# This allows type checkers to validate types without actually importing the module.
if TYPE_CHECKING:
    from ..validation.identifiers import SQL_DIALECT_REGISTRY

# Type alias for temporal precision values.
# Supports both full names and common abbreviations for convenience.
PrecisionLevel = Literal["second", "millisecond", "microsecond", "nanosecond", "ms", "us", "ns"]


class COLUMNDTYPE(Enum):
    """
    Comprehensive enumeration of SQL column data types across major dialects.

    This enum provides a standardized way to reference and work with column
    data types across different database management systems (DBMS) including
    Oracle, PostgreSQL, SQL Server, MySQL, SQLite, BigQuery, and Redshift.

    Each enum member represents a specific SQL data type and contains a tuple
    with the type name and a comprehensive metadata dictionary. The metadata
    includes:

    Metadata Fields
    ---------------
    category : str
        Type category (e.g., 'numeric_integer', 'text_variable', 'datetime').
    description : str
        Human-readable description of the data type.
    min_bytes : int
        Minimum storage size in bytes.
    max_bytes : int
        Maximum storage size in bytes (varies by dialect).
    max_precision : Optional[int]
        Maximum precision or length allowed for this type.
    time_zone_support : bool
        Whether the type supports timezone information.
    supported_dialects : List[SQLDialect]
        List of SQL dialects that natively support this type.
    min_value : Optional[Union[int, float]]
        Minimum numeric value (for numeric types).
    max_value : Optional[Union[int, float]]
        Maximum numeric value (for numeric types).
    optimal_type : Union[type, str]
        Optimal Python type for this SQL type.
    format_hints : Dict[str, Any]
        Formatting and usage hints specific to this type.
    sql_parameters : Dict[str, Any]
        SQL parameter specification (required, optional, defaults, formats).
    special_properties : Dict[SQLDialect, Dict[str, Any]]
        Dialect-specific overrides for properties.
    dialect_overrides : Dict[SQLDialect, Tuple[str, Any]]
        Cross-dialect type mappings for unsupported types.

    Properties
    ----------
    name_value : str
        The string name of the data type.
    metadata : Dict[str, Any]
        Complete metadata dictionary.
    category : str
        The type category.
    description : str
        Human-readable description.
    min_bytes : int
        Minimum storage bytes.
    max_bytes : int
        Maximum storage bytes.
    max_precision : Optional[int]
        Maximum precision/length.
    time_zone_support : bool
        Timezone support flag.
    supported_dialects : List[SQLDialect]
        Supported SQL dialects.
    min_value : Optional[Union[int, float]]
        Minimum value for numeric types.
    max_value : Optional[Union[int, float]]
        Maximum value for numeric types.

    Methods
    -------
    get_property(property_name, dialect=None, default=None)
        Get any property with optional dialect-specific override.
    is_fixed_length(dialect=None)
        Check if the type is fixed-length.
    supports_dialect(dialect)
        Check if the type is supported by a dialect.
    get_types_for_dialect(dialect)
        Get a Column_Type with dialect-specific properties resolved.
    get_all_clean_enums_for_dialect(dialect)
        Get all supported types for a dialect as Column_Type objects.
    get_optimal_types_by_category(dialect)
        Get types organized by category for a dialect.
    get_dialect_compatible_type(datatype, target_dialect)
        Find compatible type for a target dialect.
    to_sql_string(datatype, target_dialect, size_spec=None)
        Convert type to SQL string with proper formatting.

    Examples
    --------
    >>> # Basic usage
    >>> dtype = COLUMNDTYPE.VARCHAR
    >>> print(dtype.category)
    text_variable
    >>> print(dtype.description)
    Variable-length character string

    >>> # Get dialect-specific information
    >>> dtype.get_property('max_bytes', SQLDialect.POSTGRES)
    10485760
    >>> dtype.get_property('max_bytes', SQLDialect.ORACLE)
    4000

    >>> # Check dialect support
    >>> COLUMNDTYPE.TINYINT.supports_dialect(SQLDialect.MYSQL)
    True
    >>> COLUMNDTYPE.TINYINT.supports_dialect(SQLDialect.POSTGRES)
    False

    >>> # Get resolved type for specific dialect
    >>> pg_varchar = COLUMNDTYPE.VARCHAR.get_types_for_dialect(SQLDialect.POSTGRES)
    >>> print(pg_varchar.max_bytes)
    10485760

    >>> # Cross-dialect compatibility
    >>> oracle_type, params = COLUMNDTYPE.get_dialect_compatible_type(
    ...     COLUMNDTYPE.VARCHAR, SQLDialect.ORACLE
    ... )
    >>> print(oracle_type.name_value)
    varchar2

    >>> # Generate SQL type string
    >>> sql_str = COLUMNDTYPE.to_sql_string(
    ...     COLUMNDTYPE.DECIMAL, SQLDialect.POSTGRES, (10, 2)
    ... )
    >>> print(sql_str)
    DECIMAL(10,2)
    """

    # Numeric Types - Integer
    TINYINT = (
        "tinyint",
        {
            "category": "numeric_integer",
            "description": "Very small integer (8-bit)",
            "min_bytes": 1,
            "max_bytes": 1,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.MYSQL, SQLDialect.SQLSERVER, SQLDialect.SQLITE],
            "min_value": -128,  # Default MySQL signed
            "max_value": 127,  # Default MySQL signed
            "optimal_type": int,
            "format_hints": {"range_check": True, "signed": True},
            "sql_parameters": {
                "required": [],  # No parameters required for TINYINT
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple type name, no parameters
                "alternate_formats": {},
            },
            "special_properties": {
                SQLDialect.MYSQL: {
                    "min_value": -128,  # Signed range
                    "max_value": 127,
                    "description": "Very small integer (8-bit signed) - MySQL specific",
                    "format_hints": {"signed": True, "unsigned_option": True},
                },
                SQLDialect.SQLSERVER: {
                    "min_value": 0,  # SQL Server TINYINT is unsigned only
                    "max_value": 255,
                    "description": "Very small integer (8-bit unsigned) - SQL Server specific",
                    "format_hints": {"signed": False, "unsigned_only": True},
                },
            },
            "dialect_overrides": {
                SQLDialect.ORACLE: ("NUMBER", (3, 0)),
                SQLDialect.POSTGRES: ("SMALLINT", None),
                SQLDialect.REDSHIFT: ("SMALLINT", None),
                SQLDialect.BIGQUERY: ("INT64", None),
            },
            "validated_date": "2025-07-25",
        },
    )
    SMALLINT = (
        "smallint",
        {
            "category": "numeric_integer",
            "description": "Small integer (16-bit signed)",
            "min_bytes": 2,
            "max_bytes": 2,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.POSTGRES,
                SQLDialect.SQLSERVER,
                SQLDialect.MYSQL,
                SQLDialect.SQLITE,
                SQLDialect.REDSHIFT,
            ],
            "min_value": -32768,
            "max_value": 32767,
            "optimal_type": int,
            "format_hints": {"range_check": True, "signed": True},
            "sql_parameters": {
                "required": [],  # No parameters required for SMALLINT
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple type name, no parameters
                "alternate_formats": {},
            },
            "dialect_overrides": {SQLDialect.ORACLE: ("NUMBER", (5, 0)), SQLDialect.BIGQUERY: ("INT64", None)},
            "validated_date": "2025-07-26",
        },
    )
    INTEGER = (
        "integer",
        {
            "category": "numeric_integer",
            "description": "Standard integer (32-bit signed)",
            "min_bytes": 4,
            "max_bytes": 4,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.POSTGRES,
                SQLDialect.SQLSERVER,
                SQLDialect.MYSQL,
                SQLDialect.SQLITE,
                SQLDialect.REDSHIFT,
            ],
            "min_value": -2147483648,
            "max_value": 2147483647,
            "optimal_type": int,
            "format_hints": {"range_check": True, "signed": True},
            "sql_parameters": {
                "required": [],  # No parameters required for INTEGER
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple type name, no parameters
                "alternate_formats": {},
            },
            "dialect_overrides": {SQLDialect.ORACLE: ("NUMBER", (10, 0)), SQLDialect.BIGQUERY: ("INT64", None)},
        },
    )
    INT = (
        "int",
        {
            "category": "numeric_integer",
            "description": "Standard integer (alias for INTEGER)",
            "min_bytes": 4,
            "max_bytes": 4,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.POSTGRES,
                SQLDialect.SQLSERVER,
                SQLDialect.MYSQL,
                SQLDialect.SQLITE,
                SQLDialect.REDSHIFT,
            ],
            "min_value": -2147483648,
            "max_value": 2147483647,
            "optimal_type": int,
            "format_hints": {"range_check": True, "signed": True},
            "sql_parameters": {
                "required": [],  # No parameters required for INT
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple type name, no parameters
                "alternate_formats": {},
            },
            "dialect_overrides": {SQLDialect.ORACLE: ("NUMBER", (10, 0)), SQLDialect.BIGQUERY: ("INT64", None)},
        },
    )
    BIGINT = (
        "bigint",
        {
            "category": "numeric_integer",
            "description": "Large integer (64-bit signed)",
            "min_bytes": 8,
            "max_bytes": 8,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.POSTGRES,
                SQLDialect.SQLSERVER,
                SQLDialect.MYSQL,
                SQLDialect.SQLITE,
                SQLDialect.REDSHIFT,
            ],
            "min_value": -9223372036854775808,
            "max_value": 9223372036854775807,
            "optimal_type": int,
            "format_hints": {"range_check": True, "signed": True},
            "sql_parameters": {
                "required": [],  # No parameters required for BIGINT
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple type name, no parameters
                "alternate_formats": {},
            },
            "dialect_overrides": {SQLDialect.ORACLE: ("NUMBER", (19, 0)), SQLDialect.BIGQUERY: ("INT64", None)},
        },
    )
    INT64 = (
        "int64",
        {
            "category": "numeric_integer",
            "description": "64-bit signed integer (BigQuery native type)",
            "min_bytes": 8,
            "max_bytes": 8,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.BIGQUERY],
            "min_value": -9223372036854775808,
            "max_value": 9223372036854775807,
            "optimal_type": int,
            "format_hints": {"range_check": True, "signed": True, "bigquery_native": True},
            "sql_parameters": {
                "required": [],  # No parameters required for INT64
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple type name, no parameters
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.ORACLE: ("NUMBER", (19, 0)),
                SQLDialect.POSTGRES: ("BIGINT", None),
                SQLDialect.SQLSERVER: ("BIGINT", None),
                SQLDialect.MYSQL: ("BIGINT", None),
                SQLDialect.SQLITE: ("INTEGER", None),
                SQLDialect.REDSHIFT: ("BIGINT", None),
            },
        },
    )

    # Numeric Types - Decimal/Fixed-Point
    DECIMAL = (
        "decimal",
        {
            "category": "numeric_decimal",
            "description": "Exact numeric with user-defined precision and scale",
            "min_bytes": 1,
            "max_bytes": 131,  # Oracle max
            "max_precision": 38,  # SQL standard maximum
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.ORACLE,
                SQLDialect.POSTGRES,
                SQLDialect.SQLSERVER,
                SQLDialect.MYSQL,
                SQLDialect.SQLITE,
                SQLDialect.BIGQUERY,
                SQLDialect.REDSHIFT,
            ],
            "min_value": None,  # Depends on precision/scale
            "max_value": None,  # Depends on precision/scale
            "optimal_type": "float",
            "format_hints": {"precision_required": True, "scale_required": True, "use_decimal_module": True},
            "sql_parameters": {
                "required": ["precision"],  # Precision is required
                "optional": ["scale"],  # Scale is optional
                "default_format": "{type_name}({precision},{scale})",  # DECIMAL(precision,scale)
                "defaults": {"precision": 10, "scale": 0},  # Default precision and scale
                "alternate_formats": {
                    "precision_only": "{type_name}({precision})",  # DECIMAL(precision) when scale not provided
                    "no_params": "{type_name}",  # DECIMAL when neither provided
                },
            },
            "special_properties": {
                SQLDialect.MYSQL: {
                    "max_bytes": 65,  # Max precision 65
                    "max_precision": 65,
                    "description": "Exact numeric, precision 1-65, scale 0-30 - MySQL",
                    "format_hints": {"precision_max": 65, "scale_max": 30},
                },
                SQLDialect.POSTGRES: {
                    "max_bytes": 131,  # Up to precision 1000
                    "max_precision": 1000,
                    "description": "Exact numeric, precision up to 1000 digits - PostgreSQL",
                    "format_hints": {"precision_max": 1000, "high_precision": True},
                },
                SQLDialect.SQLSERVER: {
                    "max_bytes": 17,  # Precision 1-38
                    "max_precision": 38,
                    "description": "Exact numeric, precision 1-38, scale 0-precision - SQL Server",
                    "format_hints": {"precision_max": 38, "scale_max": 38},
                },
                SQLDialect.ORACLE: {
                    "max_bytes": 22,  # NUMBER storage
                    "max_precision": 38,
                    "description": "Exact numeric, precision 1-38, scale -84 to 127 - Oracle",
                    "format_hints": {"precision_max": 38, "scale_range": (-84, 127)},
                },
                SQLDialect.SQLITE: {
                    "max_bytes": 8,  # Uses REAL internally
                    "max_precision": 15,
                    "description": "Stored as TEXT, converted to REAL - SQLite",
                    "optimal_type": float,
                    "format_hints": {"stored_as_text": True, "converted_to_real": True},
                },
                SQLDialect.BIGQUERY: {
                    "max_bytes": 16,  # BigQuery DECIMAL storage (38 digits precision)
                    "max_precision": 38,
                    "description": "Exact numeric, precision up to 38 digits - BigQuery",
                    "format_hints": {"precision_max": 38, "scale_max": 9, "bigquery_decimal": True},
                },
                SQLDialect.REDSHIFT: {
                    "max_bytes": 17,  # Same as SQL Server
                    "max_precision": 38,
                    "description": "Exact numeric, precision 1-38, scale 0-precision - Redshift",
                    "format_hints": {"precision_max": 38, "scale_max": 37},
                },
            },
            "dialect_overrides": {SQLDialect.ORACLE: ("NUMBER", None)},  # Oracle uses NUMBER instead of DECIMAL
        },
    )
    NUMERIC = (
        "numeric",
        {
            "category": "numeric_decimal",
            "description": "Exact numeric (alias for DECIMAL)",
            "min_bytes": 1,
            "max_bytes": 131,
            "max_precision": 38,
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.ORACLE,
                SQLDialect.POSTGRES,
                SQLDialect.SQLSERVER,
                SQLDialect.MYSQL,
                SQLDialect.SQLITE,
                SQLDialect.BIGQUERY,
                SQLDialect.REDSHIFT,
            ],
            "min_value": None,  # Depends on precision/scale
            "max_value": None,  # Depends on precision/scale
            "optimal_type": "float",
            "format_hints": {"precision_required": True, "scale_required": True, "use_decimal_module": True},
            "special_properties": {
                SQLDialect.MYSQL: {
                    "max_bytes": 65,  # Max precision 65
                    "max_precision": 65,
                    "description": "Exact numeric, precision 1-65, scale 0-30 - MySQL",
                    "format_hints": {"precision_max": 65, "scale_max": 30},
                },
                SQLDialect.POSTGRES: {
                    "max_bytes": 131,  # Up to precision 1000
                    "max_precision": 1000,
                    "description": "Exact numeric, precision up to 1000 digits - PostgreSQL",
                    "format_hints": {"precision_max": 1000, "high_precision": True},
                },
                SQLDialect.SQLSERVER: {
                    "max_bytes": 17,  # Precision 1-38
                    "max_precision": 38,
                    "description": "Exact numeric, precision 1-38, scale 0-precision - SQL Server",
                    "format_hints": {"precision_max": 38, "scale_max": 38},
                },
                SQLDialect.ORACLE: {
                    "max_bytes": 22,  # NUMBER storage
                    "max_precision": 38,
                    "description": "Exact numeric, precision 1-38, scale -84 to 127 - Oracle",
                    "format_hints": {"precision_max": 38, "scale_range": (-84, 127)},
                },
                SQLDialect.SQLITE: {
                    "max_bytes": 8,  # Uses REAL internally
                    "max_precision": 15,
                    "description": "Stored as TEXT, converted to REAL - SQLite",
                    "optimal_type": float,
                    "format_hints": {"stored_as_text": True, "converted_to_real": True},
                },
                SQLDialect.BIGQUERY: {
                    "max_bytes": 16,  # BigQuery NUMERIC storage (38 digits precision)
                    "max_precision": 38,
                    "description": "Exact numeric, precision up to 38 digits - BigQuery",
                    "format_hints": {"precision_max": 38, "scale_max": 9, "bigquery_numeric": True},
                },
                SQLDialect.REDSHIFT: {
                    "max_bytes": 17,  # Same as SQL Server
                    "max_precision": 38,
                    "description": "Exact numeric, precision 1-38, scale 0-precision - Redshift",
                    "format_hints": {"precision_max": 38, "scale_max": 37},
                },
            },
            "sql_parameters": {
                "required": ["precision"],
                "optional": ["scale"],
                "defaults": {"precision": 10, "scale": 0},
                "default_format": "{type_name}({precision},{scale})",
                "alternate_formats": {"precision_only": "{type_name}({precision})"},
            },
            "dialect_overrides": {},
        },
    )
    NUMBER = (
        "number",
        {
            "category": "numeric_decimal",
            "description": "Oracle numeric type with precision and scale",
            "min_bytes": 1,
            "max_bytes": 22,
            "max_precision": 38,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.ORACLE],
            "min_value": None,  # Depends on precision/scale
            "max_value": None,  # Depends on precision/scale
            "optimal_type": "float",
            "format_hints": {
                "precision_required": True,
                "scale_required": True,
                "use_decimal_module": True,
                "oracle_number": True,
            },
            "sql_parameters": {
                "required": [],  # Can be used without parameters as NUMBER
                "optional": ["precision", "scale"],  # Both precision and scale are optional
                "defaults": {"precision": 38, "scale": 0},
                "default_format": "{type_name}",  # Simple NUMBER
                "alternate_formats": {
                    "with_precision": "{type_name}({precision})",
                    "with_precision_scale": "{type_name}({precision},{scale})",
                },
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("NUMERIC", None),
                SQLDialect.MYSQL: ("DECIMAL", None),
                SQLDialect.SQLSERVER: ("DECIMAL", None),
                SQLDialect.SQLITE: ("NUMERIC", None),
                SQLDialect.BIGQUERY: ("NUMERIC", None),
                SQLDialect.REDSHIFT: ("DECIMAL", None),
            },
        },
    )
    MONEY = (
        "money",
        {
            "category": "numeric_money",
            "description": "Currency amount with fixed fractional precision",
            "min_bytes": 8,
            "max_bytes": 8,
            "max_precision": 4,  # Fixed scale of 4
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.SQLSERVER, SQLDialect.POSTGRES],
            "min_value": -922337203685477.5808,
            "max_value": 922337203685477.5807,
            "optimal_type": "float",
            "format_hints": {"fixed_scale": 4, "currency_type": True, "use_decimal_module": True},
            "dialect_overrides": {
                SQLDialect.ORACLE: ("NUMBER", (19, 4)),
                SQLDialect.MYSQL: ("DECIMAL", (19, 4)),
                SQLDialect.SQLITE: ("NUMERIC", (19, 4)),
                SQLDialect.BIGQUERY: ("NUMERIC", (19, 4)),
                SQLDialect.REDSHIFT: ("DECIMAL", (19, 4)),
            },
        },
    )
    SMALLMONEY = (
        "smallmoney",
        {
            "category": "numeric_money",
            "description": "Small currency amount (SQL Server)",
            "min_bytes": 4,
            "max_bytes": 4,
            "max_precision": 4,  # Fixed scale of 4
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.SQLSERVER],
            "min_value": -214748.3648,
            "max_value": 214748.3647,
            "optimal_type": "float",
            "format_hints": {"fixed_scale": 4, "currency_type": True, "use_decimal_module": True, "small_range": True},
            "dialect_overrides": {
                SQLDialect.ORACLE: ("NUMBER", (10, 4)),
                SQLDialect.POSTGRES: ("DECIMAL", (10, 4)),
                SQLDialect.MYSQL: ("DECIMAL", (10, 4)),
                SQLDialect.SQLITE: ("DECIMAL", (10, 4)),
                SQLDialect.BIGQUERY: ("NUMERIC", (10, 4)),
                SQLDialect.REDSHIFT: ("DECIMAL", (10, 4)),
            },
        },
    )

    # Numeric Types - Floating-Point
    FLOAT = (
        "float",
        {
            "category": "numeric_float",
            "description": "Approximate numeric floating-point",
            "min_bytes": 4,
            "max_bytes": 8,
            "max_precision": 53,  # Double precision (binary digits)
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES, SQLDialect.SQLSERVER, SQLDialect.MYSQL, SQLDialect.REDSHIFT],
            "min_value": -3.4028235e38,  # Single precision by default
            "max_value": 3.4028235e38,
            "optimal_type": float,
            "format_hints": {"precision_type": "approximate", "scientific_notation_ok": True, "inf_nan_support": True},
            "sql_parameters": {
                "required": [],  # No parameters required for FLOAT
                "optional": ["precision"],  # Precision is optional
                "defaults": {},
                "default_format": "{type_name}",  # Simple FLOAT
                "alternate_formats": {"with_precision": "{type_name}({precision})"},  # FLOAT(precision)
            },
            "dialect_overrides": {
                SQLDialect.ORACLE: ("BINARY_FLOAT", None),
                SQLDialect.POSTGRESQL: ("DOUBLE PRECISION", None),
                SQLDialect.SQLITE: ("REAL", None),
                SQLDialect.BIGQUERY: ("FLOAT64", None),
            },
            "special_properties": {
                SQLDialect.MYSQL: {
                    "min_value": -3.402823466e38,
                    "max_value": 3.402823466e38,
                    "max_precision": 53,
                    "description": "Single precision (FLOAT) or double precision (FLOAT(p)) - MySQL",
                    "format_hints": {"mysql_float_precision": True, "supports_unsigned": True},
                },
                SQLDialect.SQLSERVER: {
                    "min_value": -3.40e38,
                    "max_value": 3.40e38,
                    "max_precision": 24,  # Single precision
                    "description": "Floating point number (24-bit precision) - SQL Server",
                    "format_hints": {"single_precision_default": True},
                },
                SQLDialect.ORACLE: {
                    "min_value": -1.0e126,
                    "max_value": 1.0e126,
                    "max_precision": 126,
                    "description": "Single or double precision floating-point - Oracle",
                    "format_hints": {"extended_precision": True},
                },
            },
        },
    )
    REAL = (
        "real",
        {
            "category": "numeric_float",
            "description": "Single precision floating-point",
            "min_bytes": 4,
            "max_bytes": 4,
            "max_precision": 24,  # Single precision (binary digits)
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES, SQLDialect.SQLSERVER, SQLDialect.SQLITE],
            "min_value": -3.4028235e38,
            "max_value": 3.4028235e38,
            "optimal_type": float,
            "format_hints": {"precision_type": "approximate", "single_precision": True, "scientific_notation_ok": True},
            "special_properties": {
                SQLDialect.SQLSERVER: {
                    "min_value": -3.40e38,
                    "max_value": 3.40e38,
                    "max_precision": 24,
                    "description": "Single precision floating-point (7 digits precision) - SQL Server",
                    "format_hints": {"single_precision": True, "precision_digits": 7},
                }
            },
            "sql_parameters": {
                "required": [],  # No parameters required for REAL
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple REAL, no parameters
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.MYSQL: ("FLOAT", None),
                SQLDialect.ORACLE: ("BINARY_FLOAT", None),
                SQLDialect.BIGQUERY: ("FLOAT64", None),
                SQLDialect.REDSHIFT: ("REAL", None),
            },
        },
    )
    DOUBLE = (
        "double",
        {
            "category": "numeric_float",
            "description": "Double precision floating-point",
            "min_bytes": 8,
            "max_bytes": 8,
            "max_precision": 53,  # Double precision (binary digits)
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.MYSQL, SQLDialect.SQLITE],
            "min_value": -1.7976931348623157e308,
            "max_value": 1.7976931348623157e308,
            "optimal_type": float,
            "format_hints": {"precision_type": "approximate", "double_precision": True, "scientific_notation_ok": True},
            "special_properties": {
                SQLDialect.MYSQL: {
                    "max_precision": 53,
                    "description": "Double precision floating-point (64-bit) - MySQL",
                    "format_hints": {"double_precision": True, "precision_digits": 53},
                }
            },
            "sql_parameters": {
                "required": [],  # No parameters required for DOUBLE
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple DOUBLE, no parameters
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("DOUBLE PRECISION", None),
                SQLDialect.ORACLE: ("BINARY_DOUBLE", None),
                SQLDialect.SQLSERVER: ("FLOAT", (53,)),
                SQLDialect.BIGQUERY: ("FLOAT64", None),
                SQLDialect.REDSHIFT: ("DOUBLE PRECISION", None),
            },
        },
    )
    DOUBLE_PRECISION = (
        "DOUBLE PRECISION",
        {
            "category": "numeric_float",
            "description": "Double precision floating-point (PostgreSQL)",
            "min_bytes": 8,
            "max_bytes": 8,
            "max_precision": 53,  # Double precision (binary digits)
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES, SQLDialect.REDSHIFT],
            "min_value": -1.7976931348623157e308,
            "max_value": 1.7976931348623157e308,
            "optimal_type": float,
            "format_hints": {"precision_type": "approximate", "double_precision": True, "scientific_notation_ok": True},
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "DOUBLE PRECISION",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.ORACLE: ("BINARY_DOUBLE", None),
                SQLDialect.SQLSERVER: ("FLOAT", (53,)),
                SQLDialect.MYSQL: ("DOUBLE", None),
                SQLDialect.SQLITE: ("REAL", None),
                SQLDialect.BIGQUERY: ("FLOAT64", None),
            },
        },
    )
    FLOAT64 = (
        "float64",
        {
            "category": "numeric_float",
            "description": "64-bit floating-point (BigQuery native type)",
            "min_bytes": 8,
            "max_bytes": 8,
            "max_precision": 53,  # Double precision (binary digits)
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.BIGQUERY],
            "min_value": -1.7976931348623157e308,
            "max_value": 1.7976931348623157e308,
            "optimal_type": float,
            "format_hints": {
                "precision_type": "approximate",
                "double_precision": True,
                "scientific_notation_ok": True,
                "bigquery_native": True,
            },
            "sql_parameters": {
                "required": [],  # No parameters required for FLOAT64
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple type name, no parameters
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.ORACLE: ("BINARY_DOUBLE", None),
                SQLDialect.POSTGRES: ("DOUBLE PRECISION", None),
                SQLDialect.SQLSERVER: ("FLOAT", (53,)),
                SQLDialect.MYSQL: ("DOUBLE", None),
                SQLDialect.SQLITE: ("REAL", None),
                SQLDialect.REDSHIFT: ("DOUBLE PRECISION", None),
            },
        },
    )

    # Oracle-specific floating-point types
    BINARY_FLOAT = (
        "binary_float",
        {
            "category": "numeric_float",
            "description": "Oracle 32-bit binary floating-point (IEEE 754)",
            "min_bytes": 4,
            "max_bytes": 4,
            "max_precision": 24,  # Single precision (binary digits)
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.ORACLE],
            "min_value": -3.4028235e38,
            "max_value": 3.4028235e38,
            "optimal_type": float,
            "format_hints": {
                "precision_type": "approximate",
                "single_precision": True,
                "scientific_notation_ok": True,
                "oracle_native": True,
                "ieee_754": True,
            },
            "sql_parameters": {
                "required": [],  # No parameters required for BINARY_FLOAT
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple BINARY_FLOAT
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("REAL", None),
                SQLDialect.SQLSERVER: ("REAL", None),
                SQLDialect.MYSQL: ("FLOAT", None),
                SQLDialect.SQLITE: ("REAL", None),
                SQLDialect.BIGQUERY: ("FLOAT64", None),
                SQLDialect.REDSHIFT: ("REAL", None),
            },
        },
    )
    BINARY_DOUBLE = (
        "binary_double",
        {
            "category": "numeric_float",
            "description": "Oracle 64-bit binary floating-point (IEEE 754)",
            "min_bytes": 8,
            "max_bytes": 8,
            "max_precision": 53,  # Double precision (binary digits)
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.ORACLE],
            "min_value": -1.7976931348623157e308,
            "max_value": 1.7976931348623157e308,
            "optimal_type": float,
            "format_hints": {
                "precision_type": "approximate",
                "double_precision": True,
                "scientific_notation_ok": True,
                "oracle_native": True,
                "ieee_754": True,
            },
            "sql_parameters": {
                "required": [],  # No parameters required for BINARY_DOUBLE
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple BINARY_DOUBLE
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("DOUBLE PRECISION", None),
                SQLDialect.SQLSERVER: ("FLOAT", (53,)),
                SQLDialect.MYSQL: ("DOUBLE", None),
                SQLDialect.SQLITE: ("REAL", None),
                SQLDialect.BIGQUERY: ("FLOAT64", None),
                SQLDialect.REDSHIFT: ("DOUBLE PRECISION", None),
            },
        },
    )

    # Character/Text Types - Fixed Length
    CHAR = (
        "char",
        {
            "category": "text_fixed",
            "description": "Fixed-length character string",
            "min_bytes": 1,
            "max_bytes": 8000,  # SQL Server max
            "max_precision": 8000,
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.ORACLE,
                SQLDialect.POSTGRES,
                SQLDialect.SQLSERVER,
                SQLDialect.MYSQL,
                SQLDialect.SQLITE,
                SQLDialect.REDSHIFT,
            ],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {"encoding": "utf-8", "fixed_length": True, "padding_with_spaces": True},
            "sql_parameters": {
                "required": ["length"],
                "optional": [],
                "defaults": {"length": 1},
                "default_format": "{type_name}({length})",
                "alternate_formats": {},
            },
            "dialect_overrides": {SQLDialect.BIGQUERY: ("STRING", None)},  # BigQuery uses STRING instead of CHAR
            "special_properties": {
                SQLDialect.MYSQL: {
                    "max_bytes": 255,
                    "description": "Fixed-length string, max 255 characters - MySQL",
                    "format_hints": {"encoding": "utf8mb4", "fixed_length": True, "max_chars": 255},
                },
                SQLDialect.POSTGRES: {
                    "max_bytes": 10485760,  # 10MB theoretical
                    "description": "Fixed-length string, very large max - PostgreSQL",
                    "format_hints": {"encoding": "utf-8", "fixed_length": True, "large_max": True},
                },
                SQLDialect.SQLSERVER: {
                    "max_bytes": 8000,
                    "description": "Fixed-length string, max 8,000 characters - SQL Server",
                    "format_hints": {"encoding": "utf-16", "fixed_length": True, "max_chars": 8000},
                },
                SQLDialect.ORACLE: {
                    "max_bytes": 2000,
                    "description": "Fixed-length string, max 2,000 bytes - Oracle",
                    "format_hints": {"encoding": "utf-8", "fixed_length": True, "max_bytes": 2000},
                },
                SQLDialect.SQLITE: {
                    "max_bytes": 1000000000,  # 1GB limit
                    "description": "Treated as TEXT, max ~1GB - SQLite",
                    "format_hints": {"encoding": "utf-8", "affinity": "TEXT", "treated_as_text": True},
                },
            },
        },
    )
    CHARACTER = (
        "character",
        {
            "category": "text_fixed",
            "description": "Fixed-length character string (alias for CHAR)",
            "min_bytes": 1,
            "max_bytes": 8000,
            "max_precision": 8000,
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.ORACLE,
                SQLDialect.POSTGRES,
                SQLDialect.SQLSERVER,
                SQLDialect.MYSQL,
                SQLDialect.SQLITE,
            ],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {"encoding": "utf-8", "fixed_length": True, "padding_with_spaces": True},
            "sql_parameters": {
                "required": ["length"],
                "optional": [],
                "defaults": {"length": 1},
                "default_format": "{type_name}({length})",
                "alternate_formats": {},
            },
            "dialect_overrides": {SQLDialect.REDSHIFT: ("CHAR", None), SQLDialect.BIGQUERY: ("STRING", None)},
        },
    )
    NCHAR = (
        "nchar",
        {
            "category": "text_fixed",
            "description": "Fixed-length Unicode character string",
            "min_bytes": 2,
            "max_bytes": 8000,
            "max_precision": 8000,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.ORACLE, SQLDialect.SQLSERVER, SQLDialect.MYSQL],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {
                "encoding": "utf-16",
                "fixed_length": True,
                "unicode_support": True,
                "padding_with_spaces": True,
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("CHAR", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("CHAR", None),
            },
        },
    )

    # Character/Text Types - Variable Length
    VARCHAR = (
        "varchar",
        {
            "category": "text_variable",
            "description": "Variable-length character string",
            "min_bytes": 0,
            "max_bytes": 65535,  # MySQL max
            "max_precision": 8000,
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.POSTGRES,
                SQLDialect.SQLSERVER,
                SQLDialect.MYSQL,
                SQLDialect.SQLITE,
                SQLDialect.REDSHIFT,
            ],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {"encoding": "utf-8", "escape_chars": True, "null_handling": "empty_string_as_null"},
            "sql_parameters": {
                "required": ["length"],  # Length is required for VARCHAR
                "optional": [],
                "default_format": "{type_name}({length})",  # VARCHAR(length)
                "defaults": {"length": 255},  # Default length if not specified
                "alternate_formats": {
                    "no_length": "{type_name}",  # Some cases allow VARCHAR without length
                    "max_length": "{type_name}(MAX)",  # SQL Server VARCHAR(MAX)
                },
            },
            "dialect_overrides": {
                SQLDialect.ORACLE: ("VARCHAR2", None),
                SQLDialect.BIGQUERY: ("STRING", None),  # BigQuery uses STRING instead of VARCHAR
            },
            "special_properties": {
                SQLDialect.MYSQL: {
                    "max_bytes": 65535,
                    "description": "Variable-length string, max 65,535 bytes - MySQL",
                    "format_hints": {"encoding": "utf8mb4", "collation": "utf8mb4_unicode_ci"},
                },
                SQLDialect.POSTGRES: {
                    "max_bytes": 10485760,  # 10MB theoretical limit
                    "description": "Variable-length string, unlimited practical length - PostgreSQL",
                    "format_hints": {"encoding": "utf-8", "escape_quotes": True},
                },
                SQLDialect.SQLSERVER: {
                    "max_bytes": 2147483647,  # 2GB max for VARCHAR(MAX)
                    "description": "Variable-length string, max 8,000 characters (or 2GB with VARCHAR(MAX)) - SQL Server",
                    "format_hints": {
                        "encoding": "utf-16",
                        "use_nvarchar_for_unicode": True,
                        "supports_max": True,
                        "varchar_max_for_large_text": True,
                    },
                },
                SQLDialect.ORACLE: {
                    "max_bytes": 4000,
                    "description": "Variable-length string, max 4,000 bytes - Oracle (use VARCHAR2)",
                    "format_hints": {"encoding": "utf-8", "use_varchar2_instead": True},
                },
                SQLDialect.SQLITE: {
                    "max_bytes": 1000000000,  # 1GB limit
                    "description": "Variable-length string, max ~1GB - SQLite",
                    "format_hints": {"encoding": "utf-8", "affinity": "TEXT"},
                },
            },
        },
    )
    VARCHAR2 = (
        "varchar2",
        {
            "category": "text_variable",
            "description": "Variable-length character string (Oracle)",
            "min_bytes": 0,
            "max_bytes": 32767,
            "max_precision": 32767,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.ORACLE],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {"encoding": "utf-8", "variable_length": True, "oracle_preferred": True},
            "sql_parameters": {
                "required": ["length"],
                "optional": [],
                "defaults": {"length": 255},
                "default_format": "{type_name}({length})",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("VARCHAR", None),
                SQLDialect.MYSQL: ("VARCHAR", None),
                SQLDialect.SQLSERVER: ("VARCHAR", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", None),
            },
        },
    )
    NVARCHAR = (
        "nvarchar",
        {
            "category": "text_variable",
            "description": "Variable-length Unicode character string",
            "min_bytes": 0,
            "max_bytes": 4000,
            "max_precision": 8000,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.SQLSERVER],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {"encoding": "utf-16", "variable_length": True, "unicode_support": True},
            "special_properties": {
                SQLDialect.SQLSERVER: {
                    "max_bytes": 2147483647,  # 2GB max for NVARCHAR(MAX)
                    "description": "Variable-length Unicode string, max 4,000 characters (or 2GB with NVARCHAR(MAX)) - SQL Server",
                    "format_hints": {
                        "encoding": "utf-16",
                        "unicode_support": True,
                        "supports_max": True,
                        "nvarchar_max_for_large_text": True,
                    },
                }
            },
            "dialect_overrides": {
                SQLDialect.ORACLE: ("NVARCHAR2", None),
                SQLDialect.POSTGRES: ("VARCHAR", None),
                SQLDialect.MYSQL: ("VARCHAR", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", None),
            },
        },
    )
    NVARCHAR2 = (
        "nvarchar2",
        {
            "category": "text_variable",
            "description": "Variable-length Unicode character string (Oracle)",
            "min_bytes": 0,
            "max_bytes": 32767,
            "max_precision": 32767,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.ORACLE],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {
                "encoding": "utf-16",
                "variable_length": True,
                "unicode_support": True,
                "oracle_preferred": True,
            },
            "sql_parameters": {
                "required": ["length"],
                "optional": [],
                "defaults": {"length": 255},
                "default_format": "{type_name}({length})",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("VARCHAR", None),
                SQLDialect.MYSQL: ("VARCHAR", None),
                SQLDialect.SQLSERVER: ("NVARCHAR", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", None),
            },
        },
    )

    # Character/Text Types - Large Objects
    TEXT = (
        "text",
        {
            "category": "text_large",
            "description": "Variable-length text string (large)",
            "min_bytes": 0,
            "max_bytes": 2147483647,  # 2GB
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES, SQLDialect.MYSQL, SQLDialect.SQLITE],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {"encoding": "utf-8", "large_object": True, "streaming_recommended": True},
            "sql_parameters": {
                "required": [],  # No parameters required for TEXT
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple TEXT
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.ORACLE: ("CLOB", None),
                SQLDialect.SQLSERVER: ("VARCHAR", "MAX"),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "MAX"),
            },
            "special_properties": {
                SQLDialect.MYSQL: {
                    "max_bytes": 65535,  # 64KB for TEXT
                    "description": "Text string, max 65,535 characters - MySQL TEXT",
                    "format_hints": {"encoding": "utf8mb4", "max_size": "64KB", "mysql_text": True},
                },
                SQLDialect.POSTGRES: {
                    "max_bytes": 1073741823,  # ~1GB
                    "description": "Variable-length text, unlimited practical size - PostgreSQL",
                    "format_hints": {
                        "encoding": "utf-8",
                        "unlimited_practical_size": True,
                        "streaming_recommended": True,
                    },
                },
                SQLDialect.SQLITE: {
                    "max_bytes": 1000000000,  # 1GB limit
                    "description": "Text string, max ~1GB - SQLite",
                    "format_hints": {"encoding": "utf-8", "affinity": "TEXT", "max_size": "1GB"},
                },
            },
        },
    )
    STRING = (
        "string",
        {
            "category": "text_large",
            "description": "Variable-length text string (BigQuery native type)",
            "min_bytes": 0,
            "max_bytes": 10485760,  # 10MB max for BigQuery STRING
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.BIGQUERY],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {"encoding": "utf-8", "bigquery_native": True},
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("TEXT", None),
                SQLDialect.MYSQL: ("TEXT", None),
                SQLDialect.ORACLE: ("CLOB", None),
                SQLDialect.SQLSERVER: ("VARCHAR", "MAX"),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "MAX"),
            },
            "special_properties": {},
        },
    )
    LONGTEXT = (
        "longtext",
        {
            "category": "text_large",
            "description": "Very large text string (MySQL)",
            "min_bytes": 0,
            "max_bytes": 4294967295,  # 4GB
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.MYSQL],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {
                "encoding": "utf8mb4",
                "very_large_size": True,
                "streaming_recommended": True,
                "max_size": "4GB",
            },
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("TEXT", None),
                SQLDialect.SQLSERVER: ("VARCHAR", "MAX"),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.ORACLE: ("CLOB", None),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "MAX"),
            },
        },
    )
    MEDIUMTEXT = (
        "mediumtext",
        {
            "category": "text_large",
            "description": "Medium-sized text string (MySQL)",
            "min_bytes": 0,
            "max_bytes": 16777215,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.MYSQL],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {"encoding": "utf8mb4", "medium_size": True, "max_size": "16MB"},
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("TEXT", None),
                SQLDialect.SQLSERVER: ("VARCHAR", "MAX"),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.ORACLE: ("CLOB", None),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "MAX"),
            },
        },
    )
    TINYTEXT = (
        "tinytext",
        {
            "category": "text_large",
            "description": "Small text string (MySQL)",
            "min_bytes": 0,
            "max_bytes": 255,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.MYSQL],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {"encoding": "utf8mb4", "small_size": True, "max_size": "255 bytes"},
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("TEXT", None),
                SQLDialect.SQLSERVER: ("VARCHAR", "MAX"),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.ORACLE: ("CLOB", None),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "MAX"),
            },
        },
    )
    CLOB = (
        "clob",
        {
            "category": "text_large",
            "description": "Character Large Object",
            "min_bytes": 0,
            "max_bytes": 4294967295,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.ORACLE],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {
                "encoding": "utf-8",
                "large_object": True,
                "streaming_recommended": True,
                "oracle_lob": True,
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("TEXT", None),
                SQLDialect.SQLSERVER: ("VARCHAR", "MAX"),
                SQLDialect.MYSQL: ("LONGTEXT", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "MAX"),
            },
        },
    )
    NCLOB = (
        "nclob",
        {
            "category": "text_large",
            "description": "Unicode Character Large Object",
            "min_bytes": 0,
            "max_bytes": 4294967295,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.ORACLE],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {
                "encoding": "utf-16",
                "large_object": True,
                "unicode_support": True,
                "streaming_recommended": True,
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("TEXT", None),
                SQLDialect.SQLSERVER: ("NVARCHAR", "MAX"),
                SQLDialect.MYSQL: ("LONGTEXT", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "MAX"),
            },
        },
    )

    # Date and Time Types
    DATE = (
        "date",
        {
            "category": "date",
            "description": "Date value (year, month, day)",
            "min_bytes": 3,
            "max_bytes": 4,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.ORACLE,
                SQLDialect.POSTGRES,
                SQLDialect.SQLSERVER,
                SQLDialect.MYSQL,
                SQLDialect.BIGQUERY,
                SQLDialect.REDSHIFT,
            ],
            "min_value": "1000-01-01",  # Most restrictive (MySQL)
            "max_value": "9999-12-31",  # SQL standard maximum date
            "optimal_type": "date_string",
            "format_hints": {
                "iso_format": "YYYY-MM-DD",
                "use_date_class": True,
                "timezone_naive": True,
                "datetime_string_format": "%Y-%m-%d",
            },
            "sql_parameters": {
                "required": [],  # No parameters required for DATE
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple DATE
                "alternate_formats": {},
            },
            "dialect_overrides": {SQLDialect.SQLITE: ("TEXT", None)},  # SQLite doesn't have native DATE
            "special_properties": {
                SQLDialect.MYSQL: {
                    "min_value": "1000-01-01",
                    "max_value": "9999-12-31",
                    "format_hints": {"iso_format": "YYYY-MM-DD", "zero_dates_handling": "1000-01-01"},
                },
                SQLDialect.ORACLE: {
                    "min_value": "-4712-01-01",  # 4712 BC in ISO format
                    "max_value": "9999-12-31",
                    "optimal_type": "datetime.date",
                    "format_hints": {
                        "iso_format": "YYYY-MM-DD",
                        "century_handling": True,
                        "bc_support": True,
                        "use_native_date": True,
                    },
                },
                SQLDialect.POSTGRES: {
                    "min_value": "-4713-01-01",  # 4713 BC in ISO format
                    "max_value": "5874897-12-31",
                    "format_hints": {"extended_range": True, "bc_ad_support": True},
                },
                SQLDialect.SQLSERVER: {
                    "min_value": "0001-01-01",
                    "max_value": "9999-12-31",
                    "format_hints": {"iso_format": "YYYY-MM-DD"},
                },
                SQLDialect.SQLITE: {
                    "min_value": "0001-01-01",
                    "max_value": "9999-12-31",
                    "format_hints": {"text_storage": True, "flexible_format": True},
                },
            },
        },
    )
    TIME = (
        "time",
        {
            "category": "time",
            "description": "Time value (hour, minute, second)",
            "min_bytes": 3,
            "max_bytes": 6,
            "max_precision": 6,
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.POSTGRES,
                SQLDialect.SQLSERVER,
                SQLDialect.MYSQL,
                SQLDialect.SQLITE,
                SQLDialect.BIGQUERY,
                SQLDialect.REDSHIFT,
            ],
            "min_value": "00:00:00",
            "max_value": "23:59:59.999999",
            "optimal_type": "time_string",
            "format_hints": {
                "iso_format": "HH:MM:SS.ffffff",
                "use_time_class": True,
                "precision_microseconds": True,
                "datetime_string_format": "%H:%M:%S.%f",
            },
            "special_properties": {
                SQLDialect.MYSQL: {
                    "min_value": "-838:59:59",  # MySQL allows negative time for duration
                    "max_value": "838:59:59",
                    "format_hints": {"duration_support": True, "negative_time": True, "mysql_time_range": True},
                },
                SQLDialect.SQLSERVER: {
                    "min_value": "00:00:00.0000000",
                    "max_value": "23:59:59.9999999",
                    "format_hints": {"nanosecond_precision": True, "seven_decimal_places": True},
                },
                SQLDialect.POSTGRES: {
                    "min_value": "00:00:00",
                    "max_value": "24:00:00",
                    "format_hints": {"allows_24_hour": True, "microsecond_precision": True},
                },
                SQLDialect.SQLITE: {
                    "min_value": "00:00:00",
                    "max_value": "23:59:59.999",
                    "format_hints": {"text_storage": True, "millisecond_precision": True},
                },
            },
            "sql_parameters": {
                "required": [],  # No parameters required for TIME
                "optional": ["precision"],  # Optional precision for fractional seconds
                "defaults": {"precision": 0},
                "default_format": "{type_name}",  # Simple TIME
                "alternate_formats": {"with_precision": "{type_name}({precision})"},
            },
            "dialect_overrides": {SQLDialect.ORACLE: ("DATE", None)},
        },
    )

    DATETIME2 = (
        "datetime2",
        {
            "category": "datetime",
            "description": "Enhanced date and time value (SQL Server)",
            "min_bytes": 6,
            "max_bytes": 8,
            "max_precision": 7,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.SQLSERVER],
            "min_value": "0001-01-01 00:00:00",
            "max_value": "9999-12-31 23:59:59.9999999",
            "optimal_type": "datetime.datetime",
            "format_hints": {
                "iso_format": "YYYY-MM-DD HH:MM:SS.fffffff",
                "use_datetime_class": True,
                "high_precision": True,
                "sqlserver_enhanced": True,
                "datetime_string_format": "%Y-%m-%d %H:%M:%S.%f",
            },
            "sql_parameters": {
                "required": [],  # No parameters required for DATETIME2
                "optional": ["precision"],  # Optional precision for fractional seconds
                "defaults": {"precision": 6},
                "default_format": "{type_name}",  # Simple DATETIME2
                "alternate_formats": {"with_precision": "{type_name}({precision})"},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("TIMESTAMP", None),
                SQLDialect.MYSQL: ("DATETIME", None),
                SQLDialect.ORACLE: ("TIMESTAMP", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("DATETIME", None),
                SQLDialect.REDSHIFT: ("TIMESTAMP", None),
            },
        },
    )

    DATETIME = (
        "datetime",
        {
            "category": "datetime",
            "description": "Date and time value",
            "min_bytes": 8,
            "max_bytes": 8,
            "max_precision": 6,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.SQLSERVER, SQLDialect.MYSQL, SQLDialect.BIGQUERY],
            "min_value": "1000-01-01 00:00:00",  # MySQL minimum
            "max_value": "9999-12-31 23:59:59.999",
            "optimal_type": "datetime_string",
            "format_hints": {
                "iso_format": "YYYY-MM-DD HH:MM:SS.fff",
                "use_datetime_class": True,
                "timezone_naive": True,
                "datetime_string_format": "%Y-%m-%d %H:%M:%S.%f",
            },
            "special_properties": {
                SQLDialect.MYSQL: {
                    "min_value": "1000-01-01 00:00:00",
                    "max_value": "9999-12-31 23:59:59.999999",
                    "format_hints": {"microsecond_precision": True, "mysql_datetime": True},
                },
                SQLDialect.SQLSERVER: {
                    "min_value": "1753-01-01 00:00:00.000",
                    "max_value": "9999-12-31 23:59:59.997",
                    "optimal_type": "datetime.datetime",
                    "format_hints": {"rounded_milliseconds": True, "rounding_increment": "0.000, 0.003, 0.007"},
                },
            },
            "sql_parameters": {
                "required": [],  # No parameters required for DATETIME
                "optional": ["precision"],  # Optional precision for fractional seconds
                "defaults": {"precision": 3},
                "default_format": "{type_name}",  # Simple DATETIME
                "alternate_formats": {"with_precision": "{type_name}({precision})"},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("TIMESTAMP", None),
                SQLDialect.ORACLE: ("DATE", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.REDSHIFT: ("TIMESTAMP", None),
            },
        },
    )

    SMALLDATETIME = (
        "smalldatetime",
        {
            "category": "datetime",
            "description": "Smaller date and time value (SQL Server)",
            "min_bytes": 4,
            "max_bytes": 4,
            "max_precision": 0,  # Minute precision only
            "time_zone_support": False,
            "supported_dialects": [],  # [SQLDialect.SQLSERVER],
            "min_value": "1900-01-01 00:00:00",
            "max_value": "2079-06-06 23:59:00",  # Rounds to nearest minute
            "optimal_type": "datetime_string",
            "format_hints": {
                "iso_format": "YYYY-MM-DD HH:MM:00",
                "use_datetime_class": True,
                "minute_precision": True,
                "limited_range": True,
                "datetime_string_format": "%Y-%m-%d %H:%M:%S",
                "seconds_rounded": True,
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("TIMESTAMP", None),
                SQLDialect.MYSQL: ("DATETIME", None),
                SQLDialect.ORACLE: ("DATE", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("DATETIME", None),
                SQLDialect.REDSHIFT: ("TIMESTAMP", None),
                SQLDialect.SQLSERVER: ("DATETIME2", None),
            },
        },
    )
    TIMESTAMP = (
        "timestamp",
        {
            "category": "datetime",
            "description": "Timestamp value",
            "min_bytes": 4,
            "max_bytes": 8,
            "max_precision": 6,
            "time_zone_support": False,
            "supported_dialects": [
                SQLDialect.ORACLE,
                SQLDialect.POSTGRES,
                SQLDialect.MYSQL,
                SQLDialect.SQLITE,
                SQLDialect.BIGQUERY,
                SQLDialect.REDSHIFT,
            ],
            "min_value": "1970-01-01 00:00:01",  # Common Unix timestamp start
            "max_value": "2038-01-19 03:14:07",  # 32-bit Unix timestamp limit
            "optimal_type": "datetime_string",
            "format_hints": {
                "iso_format": "YYYY-MM-DD HH:MM:SS.ffffff",
                "use_datetime_class": True,
                "precision_microseconds": True,
                "datetime_string_format": "%Y-%m-%d %H:%M:%S.%f",
            },
            "sql_parameters": {
                "required": [],
                "optional": ["precision"],
                "defaults": {"precision": 6},
                "default_format": "{type_name}",
                "alternate_formats": {"precision_only": "{type_name}({precision})"},
            },
            "dialect_overrides": {SQLDialect.SQLSERVER: ("DATETIME2", None)},
            "special_properties": {
                SQLDialect.MYSQL: {
                    "min_value": "1970-01-01 00:00:01",
                    "max_value": "2038-01-19 03:14:07",
                    "format_hints": {"unix_timestamp": True, "utc_storage": True, "auto_update": True},
                },
                SQLDialect.POSTGRES: {
                    "min_value": "-4713-01-01 00:00:00",
                    "max_value": "294276-12-31 23:59:59.999999",
                    "format_hints": {"extended_range": True, "microsecond_precision": True},
                },
                SQLDialect.ORACLE: {
                    "min_value": "-4712-01-01 00:00:00.000000000",
                    "max_value": "9999-12-31 23:59:59.999999999",
                    "format_hints": {"nanosecond_precision": True, "oracle_timestamp": True},
                },
                SQLDialect.SQLITE: {
                    "min_value": "0001-01-01 00:00:00",
                    "max_value": "9999-12-31 23:59:59.999",
                    "format_hints": {"text_storage": True, "flexible_format": True},
                },
            },
        },
    )
    TIMESTAMPTZ = (
        "timestamptz",
        {
            "category": "datetime",
            "description": "Timestamp with time zone",
            "min_bytes": 8,
            "max_bytes": 8,
            "max_precision": 6,
            "time_zone_support": True,
            "supported_dialects": [SQLDialect.POSTGRES, SQLDialect.REDSHIFT],
            "min_value": "-4713-01-01 00:00:00+00",
            "max_value": "294276-12-31 23:59:59.999999+14",  # UTC+14 is max timezone
            "optimal_type": "datetime_string",
            "format_hints": {
                "iso_format": "YYYY-MM-DD HH:MM:SS.ffffff+TZ",
                "use_datetime_class": True,
                "timezone_aware": True,
                "utc_recommended": True,
                "datetime_string_format": "%Y-%m-%d %H:%M:%S.%f",
            },
            "sql_parameters": {
                "required": [],
                "optional": ["precision"],
                "defaults": {"precision": 6},
                "default_format": "{type_name}",
                "alternate_formats": {"precision_only": "{type_name}({precision})"},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("DATETIMEOFFSET", None),
                SQLDialect.MYSQL: ("TIMESTAMP", None),
                SQLDialect.ORACLE: ("TIMESTAMP WITH TIME ZONE", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("TIMESTAMP", None),
            },
        },
    )
    TIMESTAMP_WITH_TIME_ZONE = (
        "TIMESTAMP WITH TIME ZONE",
        {
            "category": "datetime",
            "description": "Timestamp with time zone (PostgreSQL)",
            "min_bytes": 8,
            "max_bytes": 8,
            "max_precision": 6,
            "time_zone_support": True,
            "supported_dialects": [SQLDialect.POSTGRES, SQLDialect.ORACLE],
            "min_value": "-4713-01-01 00:00:00+00",
            "max_value": "294276-12-31 23:59:59.999999+14",
            "optimal_type": "datetime_string",
            "format_hints": {
                "iso_format": "YYYY-MM-DD HH:MM:SS.ffffff+TZ",
                "use_datetime_class": True,
                "timezone_aware": True,
                "postgres_tz_format": True,
                "datetime_string_format": "%Y-%m-%d %H:%M:%S.%f",
            },
            "sql_parameters": {
                "required": [],
                "optional": ["precision"],
                "defaults": {"precision": 6},
                "default_format": "TIMESTAMP WITH TIME ZONE",
                "alternate_formats": {"precision_only": "TIMESTAMP({precision}) WITH TIME ZONE"},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("DATETIMEOFFSET", None),
                SQLDialect.MYSQL: ("TIMESTAMP", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("TIMESTAMP", None),
                SQLDialect.REDSHIFT: ("TIMESTAMPTZ", None),
            },
            "special_properties": {
                SQLDialect.ORACLE: {
                    "optimal_type": "datetime.datetime",
                    "format_hints": {"use_native_datetime": True, "oracle_timestamp_tz": True},
                }
            },
        },
    )
    TIMESTAMP_WITHOUT_TIME_ZONE = (
        "TIMESTAMP WITHOUT TIME ZONE",
        {
            "category": "datetime",
            "description": "Timestamp without time zone (PostgreSQL)",
            "min_bytes": 8,
            "max_bytes": 8,
            "max_precision": 6,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES],
            "min_value": "-4713-01-01 00:00:00",
            "max_value": "294276-12-31 23:59:59.999999",
            "optimal_type": "datetime_string",
            "format_hints": {
                "iso_format": "YYYY-MM-DD HH:MM:SS.ffffff",
                "use_datetime_class": True,
                "timezone_naive": True,
                "postgres_local_time": True,
                "datetime_string_format": "%Y-%m-%d %H:%M:%S.%f",
            },
            "sql_parameters": {
                "required": [],
                "optional": ["precision"],
                "defaults": {"precision": 6},
                "default_format": "TIMESTAMP WITHOUT TIME ZONE",
                "alternate_formats": {"precision_only": "TIMESTAMP({precision}) WITHOUT TIME ZONE"},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("DATETIME2", None),
                SQLDialect.MYSQL: ("TIMESTAMP", None),
                SQLDialect.ORACLE: ("TIMESTAMP", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("TIMESTAMP", None),
                SQLDialect.REDSHIFT: ("TIMESTAMP", None),
            },
        },
    )
    TIMETZ = (
        "timetz",
        {
            "category": "time",
            "description": "Time with time zone",
            "min_bytes": 6,
            "max_bytes": 6,
            "max_precision": 6,
            "time_zone_support": True,
            "supported_dialects": [SQLDialect.POSTGRES],
            "min_value": "00:00:00+14",  # Earliest possible time with timezone
            "max_value": "24:00:00-12",  # Latest possible time with timezone
            "optimal_type": "time_string",
            "format_hints": {
                "iso_format": "HH:MM:SS.ffffff+TZ",
                "use_time_class": True,
                "timezone_aware": True,
                "postgres_timetz": True,
                "datetime_string_format": "%H:%M:%S.%f",
            },
            "sql_parameters": {
                "required": [],
                "optional": ["precision"],
                "defaults": {"precision": 6},
                "default_format": "{type_name}",
                "alternate_formats": {"precision_only": "{type_name}({precision})"},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("TIME", None),
                SQLDialect.MYSQL: ("TIME", None),
                SQLDialect.ORACLE: ("TIMESTAMP WITH TIME ZONE", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("TIME", None),
                SQLDialect.REDSHIFT: ("TIME", None),
            },
        },
    )
    TIME_WITH_TIME_ZONE = (
        "TIME WITH TIME ZONE",
        {
            "category": "time",
            "description": "Time with time zone (PostgreSQL)",
            "min_bytes": 6,
            "max_bytes": 6,
            "max_precision": 6,
            "time_zone_support": True,
            "supported_dialects": [SQLDialect.POSTGRES],
            "min_value": "00:00:00+14",
            "max_value": "24:00:00-12",
            "optimal_type": "time_string",
            "format_hints": {
                "iso_format": "HH:MM:SS.ffffff+TZ",
                "use_time_class": True,
                "timezone_aware": True,
                "postgres_format": True,
                "datetime_string_format": "%H:%M:%S.%f",
            },
            "sql_parameters": {
                "required": [],
                "optional": ["precision"],
                "defaults": {"precision": 6},
                "default_format": "TIME WITH TIME ZONE",
                "alternate_formats": {"precision_only": "TIME({precision}) WITH TIME ZONE"},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("TIME", None),
                SQLDialect.MYSQL: ("TIME", None),
                SQLDialect.ORACLE: ("TIMESTAMP WITH TIME ZONE", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("TIME", None),
                SQLDialect.REDSHIFT: ("TIME", None),
            },
        },
    )
    TIME_WITHOUT_TIME_ZONE = (
        "TIME WITHOUT TIME ZONE",
        {
            "category": "time",
            "description": "Time without time zone (PostgreSQL)",
            "min_bytes": 3,
            "max_bytes": 6,
            "max_precision": 6,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES],
            "min_value": "00:00:00",
            "max_value": "24:00:00",
            "optimal_type": "time_string",
            "format_hints": {
                "iso_format": "HH:MM:SS.ffffff",
                "use_time_class": True,
                "timezone_naive": True,
                "postgres_local_time": True,
                "datetime_string_format": "%H:%M:%S.%f",
            },
            "sql_parameters": {
                "required": [],
                "optional": ["precision"],
                "defaults": {"precision": 6},
                "default_format": "TIME WITHOUT TIME ZONE",
                "alternate_formats": {"precision_only": "TIME({precision}) WITHOUT TIME ZONE"},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("TIME", None),
                SQLDialect.MYSQL: ("TIME", None),
                SQLDialect.ORACLE: ("DATE", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("TIME", None),
                SQLDialect.REDSHIFT: ("TIME", None),
            },
        },
    )
    DATETIMEOFFSET = (
        "datetimeoffset",
        {
            "category": "datetime",
            "description": "Date and time with time zone offset (SQL Server)",
            "min_bytes": 10,
            "max_bytes": 10,
            "max_precision": 7,
            "time_zone_support": True,
            "supported_dialects": [],  # [SQLDialect.SQLSERVER],
            "min_value": "0001-01-01 00:00:00.0000000-14:00",
            "max_value": "9999-12-31 23:59:59.9999999+14:00",
            "optimal_type": "datetime.datetime",
            "format_hints": {
                "iso_format": "YYYY-MM-DD HH:MM:SS.fffffff+TZ",
                "use_datetime_class": True,
                "timezone_aware": True,
                "sqlserver_offset": True,
                "datetime_string_format": "%Y-%m-%d %H:%M:%S.%f%z",
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("TIMESTAMP WITH TIME ZONE", None),
                SQLDialect.MYSQL: ("TIMESTAMP", None),
                SQLDialect.ORACLE: ("TIMESTAMP WITH TIME ZONE", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("TIMESTAMP", None),
                SQLDialect.REDSHIFT: ("TIMESTAMPTZ", None),
                SQLDialect.SQLSERVER: ("DATETIME2", None),
            },
        },
    )

    # Boolean Types
    BOOLEAN = (
        "boolean",
        {
            "category": "boolean",
            "description": "Boolean value (true/false)",
            "min_bytes": 1,
            "max_bytes": 1,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES, SQLDialect.MYSQL],  # Only dialects with native BOOLEAN support
            "min_value": False,
            "max_value": True,
            "optimal_type": bool,
            "format_hints": {
                "true_values": [True, 1, "1", "true", "TRUE", "t", "T", "yes", "YES"],
                "false_values": [False, 0, "0", "false", "FALSE", "f", "F", "no", "NO"],
                "null_handling": "strict",
            },
            "sql_parameters": {
                "required": [],  # No parameters required for BOOLEAN
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple BOOLEAN
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.ORACLE: ("NUMBER", (1, 0)),  # Oracle uses NUMBER(1,0) for boolean
                SQLDialect.SQLSERVER: ("BIT", None),
                SQLDialect.SQLITE: ("INTEGER", None),
                SQLDialect.BIGQUERY: ("BOOL", None),
                SQLDialect.REDSHIFT: ("BOOLEAN", None),
            },
        },
    )
    BOOL = (
        "bool",
        {
            "category": "boolean",
            "description": "Boolean value (alias for BOOLEAN)",
            "min_bytes": 1,
            "max_bytes": 1,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES, SQLDialect.MYSQL],  # Only dialects with native BOOL support
            "min_value": False,
            "max_value": True,
            "optimal_type": bool,
            "format_hints": {
                "true_values": [True, 1, "1", "true", "TRUE", "t", "T", "yes", "YES"],
                "false_values": [False, 0, "0", "false", "FALSE", "f", "F", "no", "NO"],
                "null_handling": "strict",
            },
            "sql_parameters": {
                "required": [],  # No parameters required for BOOL
                "optional": [],  # No optional parameters
                "defaults": {},
                "default_format": "{type_name}",  # Simple type name, no parameters
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.ORACLE: ("NUMBER", (1, 0)),  # Oracle uses NUMBER(1,0) for boolean
                SQLDialect.SQLSERVER: ("BIT", None),
                SQLDialect.SQLITE: ("INTEGER", None),
                SQLDialect.BIGQUERY: ("BOOL", None),
                SQLDialect.REDSHIFT: ("BOOLEAN", None),
            },
        },
    )
    BIT = (
        "bit",
        {
            "category": "boolean",
            "description": "Single bit or bit string",
            "min_bytes": 1,
            "max_bytes": 8000,
            "max_precision": 8000,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.SQLSERVER, SQLDialect.MYSQL],
            "min_value": 0,
            "max_value": 1,
            "optimal_type": int,
            "format_hints": {"range_check": True, "bit_string_support": True, "binary_representation": True},
            "sql_parameters": {
                "required": [],  # No parameters required for basic BIT
                "optional": ["length"],  # Optional length for bit strings
                "defaults": {"length": 1},
                "default_format": "{type_name}",  # Simple BIT for single bit
                "alternate_formats": {"with_length": "{type_name}({length})"},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("BOOLEAN", None),
                SQLDialect.ORACLE: ("RAW", 1),
                SQLDialect.SQLITE: ("INTEGER", None),
                SQLDialect.BIGQUERY: ("BOOL", None),
                SQLDialect.REDSHIFT: ("BOOLEAN", None),
            },
        },
    )

    # Binary Types
    BINARY = (
        "binary",
        {
            "category": "binary",
            "description": "Fixed-length binary data",
            "min_bytes": 1,
            "max_bytes": 8000,
            "max_precision": 8000,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.SQLSERVER, SQLDialect.MYSQL],
            "min_value": None,
            "max_value": None,
            "optimal_type": bytes,
            "format_hints": {"encoding": "binary", "fixed_length": True, "padding_required": True},
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("BYTEA", None),
                SQLDialect.ORACLE: ("RAW", None),
                SQLDialect.SQLITE: ("BLOB", None),
                SQLDialect.BIGQUERY: ("BYTES", None),
                SQLDialect.REDSHIFT: ("VARBINARY", None),
            },
        },
    )
    VARBINARY = (
        "varbinary",
        {
            "category": "binary",
            "description": "Variable-length binary data",
            "min_bytes": 0,
            "max_bytes": 8000,
            "max_precision": 8000,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.SQLSERVER, SQLDialect.MYSQL],
            "min_value": None,
            "max_value": None,
            "optimal_type": bytes,
            "format_hints": {"encoding": "binary", "variable_length": True, "base64_option": True},
            "sql_parameters": {
                "required": [],
                "optional": ["length"],
                "defaults": {"length": 255},
                "default_format": "{type_name}({length})",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("BYTEA", None),
                SQLDialect.ORACLE: ("RAW", None),
                SQLDialect.SQLITE: ("BLOB", None),
                SQLDialect.BIGQUERY: ("BYTES", None),
                SQLDialect.REDSHIFT: ("VARBINARY", None),
            },
        },
    )
    BYTEA = (
        "bytea",
        {
            "category": "binary",
            "description": "Variable-length binary data (PostgreSQL)",
            "min_bytes": 0,
            "max_bytes": 1073741823,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES],
            "min_value": None,
            "max_value": None,
            "optimal_type": bytes,
            "format_hints": {"encoding": "binary", "variable_length": True, "hex_format": True, "escape_format": True},
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("VARBINARY", "MAX"),
                SQLDialect.MYSQL: ("LONGBLOB", None),
                SQLDialect.ORACLE: ("BLOB", None),
                SQLDialect.SQLITE: ("BLOB", None),
                SQLDialect.BIGQUERY: ("BYTES", None),
                SQLDialect.REDSHIFT: ("VARBINARY", "MAX"),
            },
        },
    )
    BLOB = (
        "blob",
        {
            "category": "binary_large",
            "description": "Binary Large Object",
            "min_bytes": 0,
            "max_bytes": 4294967295,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.ORACLE, SQLDialect.MYSQL, SQLDialect.SQLITE],
            "min_value": None,
            "max_value": None,
            "optimal_type": bytes,
            "format_hints": {
                "encoding": "binary",
                "variable_length": True,
                "large_object": True,
                "streaming_recommended": True,
            },
            "special_properties": {
                SQLDialect.MYSQL: {
                    "max_bytes": 65535,  # 64KB for BLOB
                    "description": "Binary data, max 65,535 bytes - MySQL BLOB",
                    "format_hints": {"encoding": "binary", "max_size": "64KB", "mysql_blob": True},
                },
                SQLDialect.POSTGRES: {
                    "max_bytes": 1073741823,  # ~1GB
                    "description": "Binary data (BYTEA), max ~1GB - PostgreSQL",
                    "format_hints": {"encoding": "binary", "hex_format": True, "escape_format": True},
                },
                SQLDialect.SQLSERVER: {
                    "max_bytes": 2147483647,  # 2GB
                    "description": "Binary data (VARBINARY(MAX)), max 2GB - SQL Server",
                    "format_hints": {"encoding": "binary", "varbinary_max": True, "max_size": "2GB"},
                },
                SQLDialect.ORACLE: {
                    "max_bytes": 4294967295,  # 4GB
                    "description": "Binary Large Object, max 4GB - Oracle",
                    "format_hints": {"encoding": "binary", "oracle_blob": True, "streaming_recommended": True},
                },
                SQLDialect.SQLITE: {
                    "max_bytes": 1000000000,  # 1GB limit
                    "description": "Binary data (BLOB), max ~1GB - SQLite",
                    "format_hints": {"encoding": "binary", "affinity": "BLOB", "max_size": "1GB"},
                },
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("BYTEA", None),
                SQLDialect.SQLSERVER: ("VARBINARY", "MAX"),
                SQLDialect.REDSHIFT: ("VARBINARY", "MAX"),
            },
        },
    )
    LONGBLOB = (
        "longblob",
        {
            "category": "binary_large",
            "description": "Very large binary object (MySQL)",
            "min_bytes": 0,
            "max_bytes": 4294967295,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.MYSQL],
            "min_value": None,
            "max_value": None,
            "optimal_type": bytes,
            "format_hints": {
                "encoding": "binary",
                "very_large_size": True,
                "streaming_recommended": True,
                "max_size": "4GB",
            },
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("VARBINARY", "(MAX)"),
                SQLDialect.POSTGRES: ("BYTEA", None),
                SQLDialect.ORACLE: ("BLOB", None),
                SQLDialect.SQLITE: ("BLOB", None),
                SQLDialect.BIGQUERY: ("BYTES", None),
                SQLDialect.REDSHIFT: ("VARBINARY", "(MAX)"),
            },
        },
    )
    MEDIUMBLOB = (
        "mediumblob",
        {
            "category": "binary_large",
            "description": "Medium-sized binary object (MySQL)",
            "min_bytes": 0,
            "max_bytes": 16777215,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.MYSQL],
            "min_value": None,
            "max_value": None,
            "optimal_type": bytes,
            "format_hints": {"encoding": "binary", "medium_size": True, "max_size": "16MB"},
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("VARBINARY", "(MAX)"),
                SQLDialect.POSTGRES: ("BYTEA", None),
                SQLDialect.ORACLE: ("BLOB", None),
                SQLDialect.SQLITE: ("BLOB", None),
                SQLDialect.BIGQUERY: ("BYTES", None),
                SQLDialect.REDSHIFT: ("VARBINARY", "(MAX)"),
            },
        },
    )
    TINYBLOB = (
        "tinyblob",
        {
            "category": "binary_large",
            "description": "Small binary object (MySQL)",
            "min_bytes": 0,
            "max_bytes": 255,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.MYSQL],
            "min_value": None,
            "max_value": None,
            "optimal_type": bytes,
            "format_hints": {"encoding": "binary", "small_size": True, "max_size": "255 bytes"},
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("VARBINARY", "(255)"),
                SQLDialect.POSTGRES: ("BYTEA", None),
                SQLDialect.ORACLE: ("RAW", "(255)"),
                SQLDialect.SQLITE: ("BLOB", None),
                SQLDialect.BIGQUERY: ("BYTES", None),
                SQLDialect.REDSHIFT: ("VARBINARY", "(255)"),
            },
        },
    )
    RAW = (
        "raw",
        {
            "category": "binary",
            "description": "Variable-length binary data (Oracle)",
            "min_bytes": 0,
            "max_bytes": 32767,
            "max_precision": 32767,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.ORACLE],
            "min_value": None,
            "max_value": None,
            "optimal_type": bytes,
            "format_hints": {"encoding": "binary", "variable_length": True, "hex_format": True, "oracle_raw": True},
            "sql_parameters": {
                "required": ["length"],
                "optional": [],
                "defaults": {"length": 255},
                "default_format": "{type_name}({length})",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("VARBINARY", "({length})"),
                SQLDialect.POSTGRES: ("BYTEA", None),
                SQLDialect.MYSQL: ("VARBINARY", "({length})"),
                SQLDialect.SQLITE: ("BLOB", None),
                SQLDialect.BIGQUERY: ("BYTES", None),
                SQLDialect.REDSHIFT: ("VARBINARY", "({length})"),
            },
        },
    )
    LONG_RAW = (
        "long_raw",
        {
            "category": "binary_large",
            "description": "Large variable-length binary data (Oracle legacy)",
            "min_bytes": 0,
            "max_bytes": 2147483647,
            "max_precision": 32767,
            "time_zone_support": False,
            "supported_dialects": [],
            "min_value": None,
            "max_value": None,
            "optimal_type": bytes,
            "format_hints": {"encoding": "binary", "large_object": True, "deprecated": True, "use_blob_instead": True},
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.ORACLE: ("BLOB", None),
                SQLDialect.SQLSERVER: ("VARBINARY", "(MAX)"),
                SQLDialect.POSTGRES: ("BYTEA", None),
                SQLDialect.MYSQL: ("LONGBLOB", None),
                SQLDialect.SQLITE: ("BLOB", None),
                SQLDialect.BIGQUERY: ("BYTES", None),
                SQLDialect.REDSHIFT: ("VARBINARY", "(MAX)"),
            },
        },
    )

    # JSON Types
    JSON = (
        "json",
        {
            "category": "json",
            "description": "JSON (JavaScript Object Notation) data",
            "min_bytes": 0,
            "max_bytes": 1073741823,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES, SQLDialect.MYSQL, SQLDialect.BIGQUERY, SQLDialect.ORACLE],
            "min_value": None,
            "max_value": None,
            "optimal_type": "json",
            "format_hints": {
                "serialization": "json.dumps",
                "deserialization": "json.loads",
                "validation_required": True,
                "unicode_support": True,
            },
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "special_properties": {
                SQLDialect.MYSQL: {"optimal_type": "json_str"},
                SQLDialect.POSTGRES: {"optimal_type": "json_str"},
                SQLDialect.ORACLE: {"optimal_type": "json_str"},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("NVARCHAR", "(MAX)"),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "(MAX)"),
            },
        },
    )
    JSONB = (
        "jsonb",
        {
            "category": "json",
            "description": "Binary JSON data (PostgreSQL)",
            "min_bytes": 0,
            "max_bytes": 1073741823,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES],
            "min_value": None,
            "max_value": None,
            "optimal_type": "json_str",
            "format_hints": {
                "serialization": "json.dumps",
                "deserialization": "json.loads",
                "binary_storage": True,
                "indexable": True,
            },
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "special_properties": {},
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("NVARCHAR", "(MAX)"),
                SQLDialect.MYSQL: ("JSON", None),
                SQLDialect.ORACLE: ("JSON", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("JSON", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "(MAX)"),
            },
        },
    )

    # XML Types
    XML = (
        "xml",
        {
            "category": "xml",
            "description": "XML data",
            "min_bytes": 0,
            "max_bytes": 2147483647,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.SQLSERVER, SQLDialect.POSTGRES],
            "min_value": None,
            "max_value": None,
            "optimal_type": str,
            "format_hints": {
                "well_formed_required": True,
                "encoding": "UTF-8",
                "schema_validation": False,
                "namespace_support": True,
            },
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.MYSQL: ("TEXT", None),
                SQLDialect.ORACLE: ("CLOB", None),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "MAX"),
            },
        },
    )

    # UUID/GUID Types
    UUID = (
        "uuid",
        {
            "category": "uuid",
            "description": "Universally Unique Identifier",
            "min_bytes": 16,
            "max_bytes": 16,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.POSTGRES, SQLDialect.SQLITE],
            "min_value": None,
            "max_value": None,
            "optimal_type": "uuid.UUID",
            "format_hints": {
                "string_format": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "hyphenated": True,
                "case_insensitive": True,
                "validation_required": True,
            },
            "sql_parameters": {
                "required": [],
                "optional": [],
                "defaults": {},
                "default_format": "{type_name}",
                "alternate_formats": {},
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("UNIQUEIDENTIFIER", None),
                SQLDialect.MYSQL: ("VARCHAR", "(36)"),
                SQLDialect.ORACLE: ("VARCHAR2", "(36)"),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "(36)"),
            },
        },
    )
    UNIQUEIDENTIFIER = (
        "uniqueidentifier",
        {
            "category": "uuid",
            "description": "Globally Unique Identifier (SQL Server)",
            "min_bytes": 16,
            "max_bytes": 16,
            "max_precision": None,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.SQLSERVER],
            "min_value": None,
            "max_value": None,
            "optimal_type": "uuid.UUID",
            "format_hints": {
                "string_format": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "hyphenated": True,
                "case_insensitive": True,
                "sqlserver_format": True,
            },
            "dialect_overrides": {
                SQLDialect.POSTGRES: ("UUID", None),
                SQLDialect.MYSQL: ("VARCHAR", "(36)"),
                SQLDialect.ORACLE: ("VARCHAR2", "(36)"),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.BIGQUERY: ("STRING", None),
                SQLDialect.REDSHIFT: ("VARCHAR", "(36)"),
            },
        },
    )

    BIGNUMERIC = (
        "bignumeric",
        {
            "category": "numeric_decimal",
            "description": "High precision decimal (BigQuery)",
            "min_bytes": 1,
            "max_bytes": 48,
            "max_precision": 76,
            "time_zone_support": False,
            "supported_dialects": [SQLDialect.BIGQUERY],
            "min_value": None,
            "max_value": None,
            "optimal_type": "float",
            "format_hints": {"max_precision": 76, "max_scale": 38, "high_precision": True, "scientific_notation": True},
            "sql_parameters": {
                "required": [],
                "optional": ["precision", "scale"],
                "defaults": {"precision": 76, "scale": 38},
                "default_format": "{type_name}",
                "alternate_formats": {
                    "precision_only": "{type_name}({precision})",
                    "precision_scale": "{type_name}({precision},{scale})",
                },
            },
            "dialect_overrides": {
                SQLDialect.SQLSERVER: ("DECIMAL", "(38,10)"),
                SQLDialect.POSTGRES: ("NUMERIC", "(76,38)"),
                SQLDialect.MYSQL: ("DECIMAL", "(65,30)"),
                SQLDialect.ORACLE: ("NUMBER", "(38,10)"),
                SQLDialect.SQLITE: ("TEXT", None),
                SQLDialect.REDSHIFT: ("DECIMAL", "(38,10)"),
            },
        },
    )

    @property
    def name_value(self) -> str:
        """
        Get the string name of the column data type.

        Returns
        -------
        str
            Lowercase string identifier for this data type (e.g., 'varchar', 'integer').

        Examples
        --------
        >>> COLUMNDTYPE.VARCHAR.name_value
        'varchar'
        >>> COLUMNDTYPE.INTEGER.name_value
        'integer'
        """
        return self.value[0]

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Get the complete metadata dictionary for this data type.

        The metadata dictionary contains all properties including category,
        description, byte sizes, precision limits, supported dialects,
        format hints, and dialect-specific overrides.

        Returns
        -------
        Dict[str, Any]
            Complete metadata dictionary with all type properties.

        Examples
        --------
        >>> meta = COLUMNDTYPE.VARCHAR.metadata
        >>> meta['category']
        'text_variable'
        >>> meta['max_precision']
        8000
        """
        return self.value[1]

    @property
    def category(self) -> str:
        """
        Get the category of this column data type.

        Returns
        -------
        str
            Type category string (e.g., 'numeric_integer', 'text_variable', 'datetime').

        Examples
        --------
        >>> COLUMNDTYPE.INTEGER.category
        'numeric_integer'
        >>> COLUMNDTYPE.VARCHAR.category
        'text_variable'
        >>> COLUMNDTYPE.TIMESTAMP.category
        'datetime'
        """
        return self.metadata["category"]

    @property
    def description(self) -> str:
        """
        Get the human-readable description of this data type.

        Returns
        -------
        str
            Descriptive string explaining what this data type represents.

        Examples
        --------
        >>> COLUMNDTYPE.VARCHAR.description
        'Variable-length character string'
        >>> COLUMNDTYPE.INTEGER.description
        'Standard integer (32-bit signed)'
        """
        return self.metadata["description"]

    @property
    def min_bytes(self) -> int:
        """
        Get the minimum storage size in bytes for this data type.

        Returns
        -------
        int
            Minimum number of bytes required to store this type.

        Examples
        --------
        >>> COLUMNDTYPE.TINYINT.min_bytes
        1
        >>> COLUMNDTYPE.INTEGER.min_bytes
        4
        """
        return self.metadata["min_bytes"]

    @property
    def max_bytes(self) -> int:
        """
        Get the maximum storage size in bytes for this data type.

        Note that this value may vary by dialect. Use get_property() with
        a specific dialect to get dialect-specific values.

        Returns
        -------
        int
            Maximum number of bytes this type can occupy.

        Examples
        --------
        >>> COLUMNDTYPE.TINYINT.max_bytes
        1
        >>> COLUMNDTYPE.VARCHAR.max_bytes
        65535
        >>> # Get dialect-specific max_bytes
        >>> COLUMNDTYPE.VARCHAR.get_property('max_bytes', SQLDialect.ORACLE)
        4000
        """
        return self.metadata["max_bytes"]

    @property
    def max_precision(self) -> Optional[int]:
        """
        Get the maximum precision or length allowed for this data type.

        For numeric types, this is the maximum number of digits.
        For string types, this is the maximum character length.
        Returns None if precision is not applicable.

        Returns
        -------
        Optional[int]
            Maximum precision/length, or None if not applicable.

        Examples
        --------
        >>> COLUMNDTYPE.DECIMAL.max_precision
        38
        >>> COLUMNDTYPE.VARCHAR.max_precision
        8000
        >>> COLUMNDTYPE.INTEGER.max_precision
        None
        """
        return self.metadata.get("max_precision")

    @property
    def time_zone_support(self) -> bool:
        """
        Check if this data type supports timezone information.

        Returns
        -------
        bool
            True if the type can store timezone data, False otherwise.

        Examples
        --------
        >>> COLUMNDTYPE.TIMESTAMPTZ.time_zone_support
        True
        >>> COLUMNDTYPE.TIMESTAMP.time_zone_support
        False
        >>> COLUMNDTYPE.VARCHAR.time_zone_support
        False
        """
        return self.metadata["time_zone_support"]

    @property
    def supported_dialects(self) -> List["SQLDialect"]:
        """
        Get the list of SQL dialects that natively support this data type.

        Returns
        -------
        List[SQLDialect]
            List of SQLDialect enums that support this type natively.

        Examples
        --------
        >>> SQLDialect.MYSQL in COLUMNDTYPE.TINYINT.supported_dialects
        True
        >>> SQLDialect.POSTGRES in COLUMNDTYPE.TINYINT.supported_dialects
        False
        >>> len(COLUMNDTYPE.VARCHAR.supported_dialects)
        6
        """
        return self.metadata.get("supported_dialects", [])

    @property
    def min_value(self) -> Optional[Union[int, float]]:
        """
        Get the minimum value for numeric data types.

        Returns None for non-numeric types or types without defined limits.

        Returns
        -------
        Optional[Union[int, float]]
            Minimum value this type can store, or None if not applicable.

        Examples
        --------
        >>> COLUMNDTYPE.TINYINT.min_value
        -128
        >>> COLUMNDTYPE.INTEGER.min_value
        -2147483648
        >>> COLUMNDTYPE.VARCHAR.min_value
        None
        """
        return self.metadata.get("min_value")

    @property
    def max_value(self) -> Optional[Union[int, float]]:
        """
        Get the maximum value for numeric data types.

        Returns None for non-numeric types or types without defined limits.

        Returns
        -------
        Optional[Union[int, float]]
            Maximum value this type can store, or None if not applicable.

        Examples
        --------
        >>> COLUMNDTYPE.TINYINT.max_value
        127
        >>> COLUMNDTYPE.INTEGER.max_value
        2147483647
        >>> COLUMNDTYPE.VARCHAR.max_value
        None
        """
        return self.metadata.get("max_value")

    def get_property(self, property_name: str, dialect: Optional[SQLDialect] = None, default: Any = None) -> Any:
        """
        Get any property value with optional dialect-specific override.

        This method provides a flexible way to access any property from the
        metadata dictionary, with automatic fallback to dialect-specific
        overrides when available. It implements an intelligent lookup chain:
        1. Check dialect-specific special_properties (if dialect provided)
        2. Check base metadata dictionary
        3. Return default value if property not found

        Parameters
        ----------
        property_name : str
            Name of the property to retrieve (e.g., 'max_bytes', 'description').
        dialect : Optional[SQLDialect], optional
            SQL dialect for dialect-specific property overrides. Default is None.
        default : Any, optional
            Default value to return if property is not found. Default is None.

        Returns
        -------
        Any
            Property value with dialect override if available, otherwise base
            value, otherwise the default value.

        Examples
        --------
        >>> # Get base property
        >>> COLUMNDTYPE.VARCHAR.get_property('max_bytes')
        65535
        >>> # Get dialect-specific property
        >>> COLUMNDTYPE.VARCHAR.get_property('max_bytes', SQLDialect.ORACLE)
        4000
        >>> # Get with default value
        >>> COLUMNDTYPE.INTEGER.get_property('nonexistent', default='N/A')
        'N/A'
        """
        # First check for dialect-specific override in special_properties.
        if dialect and "special_properties" in self.metadata:
            dialect_props = self.metadata["special_properties"].get(dialect, {})
            if property_name in dialect_props:
                return dialect_props[property_name]

        # Check base metadata for the property.
        if property_name in self.metadata:
            return self.metadata[property_name]

        # Return default value (which could be None).
        return default

    def is_fixed_length(self, dialect: Optional[SQLDialect] = None) -> bool:
        """
        Check if this data type is fixed-length for a specific dialect.

        Fixed-length types always occupy the same amount of storage regardless
        of the actual data content. Variable-length types use only the space
        needed for the actual data (plus overhead).

        Parameters
        ----------
        dialect : Optional[SQLDialect], optional
            SQL dialect to check for dialect-specific behavior. Default is None.

        Returns
        -------
        bool
            True if the type is fixed-length, False if variable-length.

        Examples
        --------
        >>> COLUMNDTYPE.CHAR.is_fixed_length()
        True
        >>> COLUMNDTYPE.VARCHAR.is_fixed_length()
        False
        >>> COLUMNDTYPE.INTEGER.is_fixed_length()
        True
        """
        # Check for explicit dialect-specific override.
        fixed_length_override = self.get_property("fixed_length", dialect)
        if fixed_length_override is not None:
            return fixed_length_override

        # Default logic: fixed length if min_bytes equals max_bytes.
        min_b = self.get_property("min_bytes", dialect, self.min_bytes)
        max_b = self.get_property("max_bytes", dialect, self.max_bytes)
        if min_b is not None and max_b is not None:
            return min_b == max_b

        # For text types, assume variable length unless explicitly specified.
        category = self.get_property("category", dialect, self.category)
        return category in ["text_fixed", "binary"]

    def supports_dialect(self, dialect: SQLDialect) -> bool:
        """
        Check if this data type is natively supported by a SQL dialect.

        Parameters
        ----------
        dialect : SQLDialect
            The SQL dialect to check for support.

        Returns
        -------
        bool
            True if the dialect natively supports this type, False otherwise.

        Examples
        --------
        >>> COLUMNDTYPE.VARCHAR.supports_dialect(SQLDialect.POSTGRES)
        True
        >>> COLUMNDTYPE.TINYINT.supports_dialect(SQLDialect.POSTGRES)
        False
        >>> COLUMNDTYPE.NUMBER.supports_dialect(SQLDialect.ORACLE)
        True
        """
        # Use resolved alias to handle dialect aliases (e.g., POSTGRESQL -> POSTGRES).
        return dialect.resolved_alias in self.supported_dialects

    def __str__(self) -> str:
        return self.name_value

    @classmethod
    def get_by_category(cls, category: str) -> List["COLUMNDTYPE"]:
        """
        Get all data types belonging to a specific category.

        Categories organize related data types together (e.g., all integer
        types, all text types, all datetime types).

        Parameters
        ----------
        category : str
            The category name to filter by (e.g., 'numeric_integer',
            'text_variable', 'datetime').

        Returns
        -------
        List[COLUMNDTYPE]
            List of all data types in the specified category.

        Examples
        --------
        >>> int_types = COLUMNDTYPE.get_by_category('numeric_integer')
        >>> COLUMNDTYPE.INTEGER in int_types
        True
        >>> COLUMNDTYPE.BIGINT in int_types
        True
        >>> text_types = COLUMNDTYPE.get_by_category('text_variable')
        >>> COLUMNDTYPE.VARCHAR in text_types
        True
        """
        return [dtype for dtype in cls if dtype.category == category]

    def get_types_for_dialect(self, dialect: SQLDialect) -> "Column_Type":
        """
        Get a Column_Type named tuple with dialect-specific properties resolved.

        This method resolves all dialect-specific property overrides from the
        special_properties dictionary and returns a clean Column_Type object
        with all properties materialized. This eliminates the need for runtime
        property lookups and provides efficient access to type metadata.

        Parameters
        ----------
        dialect : SQLDialect
            The SQL dialect to resolve properties for.

        Returns
        -------
        Column_Type
            Named tuple with all dialect-specific properties resolved and
            materialized. The special_properties dictionary is removed since
            all overrides have been applied.

        Examples
        --------
        >>> # Get PostgreSQL-specific VARCHAR type
        >>> varchar = COLUMNDTYPE.VARCHAR
        >>> pg_varchar = varchar.get_types_for_dialect(SQLDialect.POSTGRES)
        >>> print(pg_varchar.max_bytes)
        10485760
        >>> print(type(pg_varchar).__name__)
        Column_Type

        >>> # Oracle VARCHAR has different max_bytes
        >>> oracle_varchar = varchar.get_types_for_dialect(SQLDialect.ORACLE)
        >>> print(oracle_varchar.max_bytes)
        4000
        """
        # Start with a copy of the base metadata dictionary.
        clean_metadata = self.metadata.copy()

        # Apply dialect-specific property overrides if they exist.
        # This merges special_properties for the target dialect into clean_metadata.
        if "special_properties" in clean_metadata:
            if dialect in clean_metadata["special_properties"]:
                dialect_overrides = clean_metadata["special_properties"][dialect]
                # Update the metadata with dialect-specific values.
                clean_metadata.update(dialect_overrides)

            # Remove special_properties since all overrides are now materialized.
            del clean_metadata["special_properties"]

        # Lazy import to avoid circular dependency.
        # This pattern allows type checking without importing at module load time.
        try:
            from validation.identifiers import SQL_DIALECT_REGISTRY
        except ImportError:
            from ..validation.identifiers import SQL_DIALECT_REGISTRY

        # Create and return a Column_Type named tuple with resolved properties.
        # All fields are populated from the clean metadata dictionary.
        return Column_Type(
            name=self.name,  # Enum member name (e.g., 'VARCHAR')
            name_value=self.name_value,  # String type name (e.g., 'varchar')
            category=clean_metadata.get("category", ""),  # Type category
            description=clean_metadata.get("description", ""),  # Description
            min_bytes=clean_metadata.get("min_bytes", 0),  # Minimum storage bytes
            max_bytes=clean_metadata.get("max_bytes", 0),  # Maximum storage bytes
            max_precision=clean_metadata.get("max_precision"),  # Max precision/length
            time_zone_support=clean_metadata.get("time_zone_support", False),  # TZ support
            supported_dialects=clean_metadata.get("supported_dialects", []),  # Supported dialects
            min_value=clean_metadata.get("min_value"),  # Min value (numeric types)
            max_value=clean_metadata.get("max_value"),  # Max value (numeric types)
            metadata=clean_metadata,  # Full metadata for additional properties
            dialect=dialect,  # Target dialect
            dtype=self,  # Original enum member reference
            driver=SQL_DIALECT_REGISTRY.get_best_available_driver(dialect=dialect),  # Best driver
        )

    @classmethod
    def get_all_clean_enums_for_dialect(cls, dialect: SQLDialect) -> Dict[str, "Column_Type"]:
        """
        Get all COLUMNDTYPE members as clean named tuples for a specific dialect.
        Only includes data types that are actually supported by the given dialect.

        Args:
            dialect: The SQL dialect to resolve values for

        Returns:
            Dictionary mapping member names to CleanColumnType named tuples
            (only for data types supported by the dialect)

        Usage:
            >>> clean_enums = COLUMNDTYPE.get_all_clean_enums_for_dialect(SQLDialect.POSTGRES)
            >>> varchar_enum = clean_enums['VARCHAR']
            >>> print(varchar_enum.max_bytes)  # Shows PostgreSQL-specific value
            >>> print(type(varchar_enum).__name__)  # 'CleanColumnType'
            >>> 'MEDIUMINT' in clean_enums  # False - MySQL only type
        """
        clean_enums = {}

        for member in cls:
            # Only include data types supported by this dialect
            if member.supports_dialect(dialect):
                clean_enums[member.name] = member.get_types_for_dialect(dialect)

        return clean_enums

    @classmethod
    def get_optimal_types_by_category(cls, dialect: SQLDialect) -> Dict[str, Dict[str, "Column_Type"]]:
        """
        Get Column_Type enums organized by data type category.

        Args:
            dialect: Optional dialect to filter by. If provided, only includes types supported by that dialect.

        Returns:
            Dict mapping categories to dicts of {type_name: Column_Type}

        Usage:
            >>> types_by_cat = COLUMNDTYPE.get_optimal_types_by_category(SQLDialect.POSTGRES)
            >>> print(types_by_cat['numeric_integer'])  # {'INTEGER': Column_Type(...), 'BIGINT': Column_Type(...), ...}
            >>> varchar_type = types_by_cat['text_variable']['VARCHAR']
            >>> print(varchar_type.optimal_type)  # <class 'str'>
            >>> print(varchar_type.max_bytes)     # PostgreSQL-specific max_bytes value
        """
        result = {}

        for member in cls:
            # Skip if dialect is specified and this type doesn't support it
            if dialect and not member.supports_dialect(dialect.resolved_alias):
                continue

            category = member.category
            if category not in result:
                result[category] = {}

            # Get the Column_Type enum with dialect-specific properties resolved
            result[category][member.name] = member.get_types_for_dialect(dialect.resolved_alias)

        return result

    @classmethod
    def get_dialect_compatible_type(
        cls, datatype: "COLUMNDTYPE", target_dialect: SQLDialect
    ) -> Tuple["COLUMNDTYPE", Any]:
        """
        Get the most compatible data type for a target dialect.

        If the specified datatype is supported by the target dialect, returns the same type.
        If not supported, checks sql_parameters.dialect_overrides for the target dialect.

        Args:
            datatype: The original COLUMNDTYPE to map
            target_dialect: The target SQL dialect

        Returns:
            COLUMNDTYPE that is compatible with the target dialect

        Usage:
            >>> # Oracle doesn't support TINYINT, maps to NUMBER via dialect_overrides
            >>> compatible = COLUMNDTYPE.get_dialect_compatible_type(COLUMNDTYPE.TINYINT, SQLDialect.ORACLE)
            >>> print(compatible)  # COLUMNDTYPE.DECIMAL (Oracle NUMBER)

            >>> # PostgreSQL supports INTEGER directly
            >>> compatible = COLUMNDTYPE.get_dialect_compatible_type(COLUMNDTYPE.INTEGER, SQLDialect.POSTGRES)
            >>> print(compatible)  # COLUMNDTYPE.INTEGER (same type)
        """
        target_dialect = target_dialect.resolved_alias  # Use resolved alias for consistency
        # If the datatype is already supported by the target dialect, return it as-is
        if datatype.supports_dialect(target_dialect):
            return (datatype, None)  # don't need any extra parameters

        # Check root-level dialect_overrides (use resolved alias for consistency)
        if "dialect_overrides" in datatype.metadata:
            dialect_overrides = datatype.metadata["dialect_overrides"]
            if target_dialect in dialect_overrides:
                override_info = dialect_overrides[target_dialect]

                assert isinstance(override_info, tuple), "Dialect override must be a tuple"
                assert isinstance(override_info[0], str), "Override type name must be a string"

                base_type = override_info[0].upper().strip()

                for member in cls:
                    if member.name_value.upper() == base_type:
                        return (member, override_info[1])  # Return the member and any extra parameters
                raise ValueError(f"Unsupported dialect override type: {base_type}")

        raise ValueError(
            f"Data type {datatype.name_value} is not supported by dialect {target_dialect.name_value}. And there is no published crosswalking method for it."
        )

    @classmethod
    def to_sql_string(
        cls,
        datatype: "COLUMNDTYPE",
        target_dialect: SQLDialect,
        size_spec: Union[int, Tuple[int, ...], str, None] = None,
    ) -> str:
        """
        Convert a COLUMNDTYPE to a SQL type string for the target dialect.

        This method uses the sql_parameters specification in the enum to generate
        properly formatted SQL type strings with appropriate parameters.

        Args:
            datatype: The COLUMNDTYPE enum value
            target_dialect: The target SQL dialect
            size_spec: Size specification for the type:
                - int: length for VARCHAR/CHAR, precision for DECIMAL, or time precision for temporal types
                - tuple: (precision, scale) for DECIMAL, (length,) for VARCHAR
                - str: custom size specification like "10,2" or "255"
                - None: use defaults

        Returns:
            SQL type string appropriate for the target dialect

        Examples:
            >>> COLUMNDTYPE.to_sql_string(COLUMNDTYPE.VARCHAR, SQLDialect.POSTGRESQL, 255)
            'VARCHAR(255)'
            >>> COLUMNDTYPE.to_sql_string(COLUMNDTYPE.VARCHAR, SQLDialect.ORACLE, 255)
            'VARCHAR2(255)'
            >>> COLUMNDTYPE.to_sql_string(COLUMNDTYPE.DECIMAL, SQLDialect.POSTGRESQL, (10, 2))
            'DECIMAL(10,2)'
            >>> COLUMNDTYPE.to_sql_string(COLUMNDTYPE.TIME, SQLDialect.SQLSERVER, 6)
            'TIME(6)'
            >>> COLUMNDTYPE.to_sql_string(COLUMNDTYPE.DATETIME2, SQLDialect.SQLSERVER, 3)
            'DATETIME2(3)'
        """
        # Get the compatible type and parameters for the target dialect
        compatible_type, dialect_params = cls.get_dialect_compatible_type(datatype, target_dialect)

        # For temporal types with precision, use alternate formats if available
        if isinstance(size_spec, int) and datatype.category in ["time", "datetime"]:
            # Get the clean enum for this dialect to access sql_parameters
            clean_enum = datatype.get_types_for_dialect(target_dialect)
            sql_params = clean_enum.metadata.get("sql_parameters", {})

            # Check if precision is supported
            optional_params = sql_params.get("optional", [])
            alternate_formats = sql_params.get("alternate_formats", {})

            if "precision" in optional_params and alternate_formats:
                type_name = compatible_type.name_value.upper()

                # Format with precision using the alternate format
                if "with_precision" in alternate_formats:
                    return alternate_formats["with_precision"].format(type_name=type_name, precision=size_spec)
                elif "precision_only" in alternate_formats:
                    return alternate_formats["precision_only"].format(type_name=type_name, precision=size_spec)

        size_spec = size_spec or dialect_params  # Use provided size_spec or dialect-specific params if available

        # Format the size specification properly
        if isinstance(size_spec, int):
            # Single integer: VARCHAR(255), DECIMAL(10)
            formatted_spec = f"({size_spec})"
        elif isinstance(size_spec, tuple):
            # Tuple: Handle (precision,scale) or (precision,)
            if len(size_spec) == 1:
                # Single-element tuple: FLOAT(53) not FLOAT(53,)
                formatted_spec = f"({size_spec[0]})"
            elif len(size_spec) == 2:
                # Two-element tuple: DECIMAL(10,2)
                formatted_spec = f"({size_spec[0]},{size_spec[1]})"
            else:
                # Handle tuples with more elements if needed
                formatted_spec = f"({','.join(str(x) for x in size_spec)})"
        elif isinstance(size_spec, str):
            # String: Could be "MAX", "10,2", etc.
            # If it already has parentheses, use as-is; otherwise wrap in parentheses
            if size_spec.strip().startswith("("):
                formatted_spec = size_spec
            else:
                formatted_spec = f"({size_spec})"
        else:
            # No size spec
            formatted_spec = ""

        return f"{compatible_type.name_value.upper()}{formatted_spec}"

    @classmethod
    def _parse_size_spec(
        cls, size_spec: Union[int, Tuple[int, ...], str, None], sql_params: Dict[str, Any]
    ) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Parse size_spec into length, precision, and scale."""
        length = None
        precision = None
        scale = None

        if size_spec is None:
            # Use defaults if available
            defaults = sql_params.get("defaults", {})
            length = defaults.get("length")
            precision = defaults.get("precision")
            scale = defaults.get("scale")

        elif isinstance(size_spec, int):
            # Single integer - could be length or precision depending on type
            required_params = sql_params.get("required", [])
            if "length" in required_params:
                length = size_spec
            elif "precision" in required_params:
                precision = size_spec
            else:
                # Default to length for most types
                length = size_spec

        elif isinstance(size_spec, tuple):
            if len(size_spec) == 1:
                # (length,) or (precision,)
                required_params = sql_params.get("required", [])
                if "length" in required_params:
                    length = size_spec[0]
                elif "precision" in required_params:
                    precision = size_spec[0]

            elif len(size_spec) == 2:
                # (precision, scale)
                precision, scale = size_spec

        elif isinstance(size_spec, str):
            # Parse string format like "10,2" or "255"
            if "," in size_spec:
                parts = size_spec.split(",")
                if len(parts) == 2:
                    try:
                        precision = int(parts[0].strip())
                        scale = int(parts[1].strip())
                    except ValueError:
                        pass
            else:
                try:
                    value = int(size_spec.strip())
                    # Determine if this is length or precision
                    required_params = sql_params.get("required", [])
                    if "length" in required_params:
                        length = value
                    elif "precision" in required_params:
                        precision = value
                    else:
                        length = value
                except ValueError:
                    pass

        return length, precision, scale

    @classmethod
    def _format_sql_type(
        cls, format_string: str, size_spec: Union[int, Tuple[int, ...], str, None], sql_params: Dict[str, Any]
    ) -> str:
        """Format a SQL type string with parameters."""
        length, precision, scale = cls._parse_size_spec(size_spec, sql_params)

        # Simple format string substitution
        return format_string.format(length=length or "", precision=precision or "", scale=scale or "")

    @classmethod
    def get_optimal_type_for_data(
        cls,
        core_type: CoreDataType,
        dialect: SQLDialect,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        precision: Optional[int] = None,
        scale: Optional[int] = None,
        max_length: Optional[int] = None,
        timezone_aware: bool = True,
        use_fixed_length: bool = False,
        safety_threshold: Optional[float] = None,
        time_precision: Optional[Literal["second", "millisecond", "microsecond", "nanosecond", "ms", "us", "ns", "auto"]] = None,
        min_char_bytes: int = 1,
    ) -> Tuple["COLUMNDTYPE", Optional[Union[int, Tuple[int, int], str]]]:
        """
        Select the optimal COLUMNDTYPE for data based on CoreDataType and value metadata.

        This method maps platform-agnostic CoreDataType to dialect-specific SQL types,
        selecting the most efficient type that can safely store the data values.

        Parameters
        ----------
        core_type : CoreDataType
            The core data type from metadata analysis (e.g., CoreDataType.INTEGER).
        dialect : SQLDialect
            Target SQL dialect for the column type.
        min_value : int or float, optional
            Minimum value in the data (for numeric type optimization).
        max_value : int or float, optional
            Maximum value in the data (for numeric type optimization).
        precision : int, optional
            Decimal precision (total digits) for DECIMAL types.
        scale : int, optional
            Decimal scale (digits after decimal point) for DECIMAL types.
        max_length : int, optional
            Maximum string length in bytes for VARCHAR/CHAR types.
        timezone_aware : bool, default True
            Whether datetime types should include timezone support.
        use_fixed_length : bool, default False
            Whether to use fixed-length CHAR instead of VARCHAR for strings.
        safety_threshold : float, optional
            Safety margin to expand numeric ranges (0.0-1.0). For example, 0.1 expands
            the range by 10% on each side to accommodate future data growth.
        time_precision : str, optional
            Precision for temporal types: 'second', 'millisecond', 'microsecond',
            'nanosecond' (or 'ms', 'us', 'ns'). If 'auto', determines from data.
        min_char_bytes : int, default 1
            Minimum bytes/length for character columns (VARCHAR/CHAR).

        Returns
        -------
        Tuple[COLUMNDTYPE, Optional[Union[int, Tuple[int, int]]]]
            Tuple of (optimal COLUMNDTYPE, size specification).
            Size specification is:
            - int for VARCHAR length or single-param types
            - Tuple[int, int] for DECIMAL (precision, scale)
            - None if no size specification needed

        Examples
        --------
        >>> # Integer with small range -> TINYINT
        >>> dtype, spec = COLUMNDTYPE.get_optimal_type_for_data(
        ...     CoreDataType.INTEGER, SQLDialect.POSTGRES, min_value=0, max_value=100
        ... )
        >>> print(dtype.name)
        SMALLINT  # TINYINT maps to SMALLINT in Postgres

        >>> # String with known max length
        >>> dtype, spec = COLUMNDTYPE.get_optimal_type_for_data(
        ...     CoreDataType.STRING, SQLDialect.POSTGRES, max_length=255
        ... )
        >>> print(dtype.name, spec)
        VARCHAR 255

        >>> # Decimal with precision/scale
        >>> dtype, spec = COLUMNDTYPE.get_optimal_type_for_data(
        ...     CoreDataType.DECIMAL, SQLDialect.POSTGRES, precision=10, scale=2
        ... )
        >>> print(dtype.name, spec)
        DECIMAL (10, 2)
        """
        dialect = dialect.resolved_alias

        # Apply safety threshold to expand numeric ranges
        if safety_threshold is not None and min_value is not None and max_value is not None:
            min_value = min_value - abs(min_value * safety_threshold)
            max_value = max_value + abs(max_value * safety_threshold)

        # Integer types - select smallest type that fits the value range
        if core_type == CoreDataType.INTEGER:
            return cls._select_optimal_integer(dialect, min_value, max_value)

        # Float types
        elif core_type == CoreDataType.FLOAT:
            return cls._select_optimal_float(dialect)

        # Decimal types
        elif core_type == CoreDataType.DECIMAL:
            return cls._select_optimal_decimal(dialect, precision, scale)

        # String types
        elif core_type in (CoreDataType.STRING, CoreDataType.CATEGORICAL):
            return cls._select_optimal_string(dialect, max_length, use_fixed_length, min_char_bytes)

        # Boolean type
        elif core_type == CoreDataType.BOOLEAN:
            return cls._select_optimal_boolean(dialect)

        # Date type
        elif core_type == CoreDataType.DATE:
            return cls.get_dialect_compatible_type(cls.DATE, dialect)

        # Time type
        elif core_type == CoreDataType.TIME:
            return cls.get_dialect_compatible_type(cls.TIME, dialect)

        # Datetime type
        elif core_type == CoreDataType.DATETIME:
            return cls._select_optimal_datetime(dialect, timezone_aware, time_precision)

        # Timedelta/Duration type - store as BIGINT (microseconds)
        elif core_type == CoreDataType.TIMEDELTA:
            return cls.get_dialect_compatible_type(cls.BIGINT, dialect)

        # Binary/Bytes type
        elif core_type == CoreDataType.BYTES:
            return cls._select_optimal_binary(dialect, max_length)

        # UUID type
        elif core_type == CoreDataType.UUID:
            return cls.get_dialect_compatible_type(cls.UUID, dialect)

        # Null/None type - cannot determine type from null data
        elif core_type == CoreDataType.NONE_TYPE:
            raise ValueError(
                "Cannot determine SQL type for column containing only NULL values. "
                "Please specify the column type explicitly or exclude this column."
            )

        # Default fallback - use TEXT with dialect compatibility
        else:
            return cls.get_dialect_compatible_type(cls.TEXT, dialect)

    @classmethod
    def _select_optimal_integer(
        cls, dialect: SQLDialect, min_value: Optional[Union[int, float]], max_value: Optional[Union[int, float]]
    ) -> Tuple["COLUMNDTYPE", None]:
        """Select smallest integer type that fits the value range."""
        min_val = int(min_value) if min_value is not None else 0
        max_val = int(max_value) if max_value is not None else 0

        # Define integer types in order of size (smallest to largest)
        int_types = [
            (cls.TINYINT, -128, 127),
            (cls.SMALLINT, -32768, 32767),
            (cls.INTEGER, -2147483648, 2147483647),
            (cls.BIGINT, -9223372036854775808, 9223372036854775807),
        ]

        for dtype, type_min, type_max in int_types:
            if min_val >= type_min and max_val <= type_max:
                # Get dialect-compatible version
                compatible, params = cls.get_dialect_compatible_type(dtype, dialect)
                return (compatible, params)

        # Default to BIGINT for very large values
        compatible, params = cls.get_dialect_compatible_type(cls.BIGINT, dialect)
        return (compatible, params)

    @classmethod
    def _select_optimal_float(cls, dialect: SQLDialect) -> Tuple["COLUMNDTYPE", Optional[Any]]:
        """Select appropriate float type for dialect."""
        # Use FLOAT as base and let get_dialect_compatible_type handle mapping
        return cls.get_dialect_compatible_type(cls.FLOAT, dialect)

    @classmethod
    def _select_optimal_decimal(
        cls, dialect: SQLDialect, precision: Optional[int], scale: Optional[int]
    ) -> Tuple["COLUMNDTYPE", Optional[Tuple[int, int]]]:
        """Select DECIMAL type with appropriate precision/scale."""
        prec = precision or 18
        sc = scale or 0

        # Get dialect-compatible DECIMAL type
        compatible, _ = cls.get_dialect_compatible_type(cls.DECIMAL, dialect)
        return (compatible, (prec, sc))

    @classmethod
    def _select_optimal_string(
        cls, dialect: SQLDialect, max_length: Optional[int], use_fixed_length: bool, min_char_bytes: int = 1
    ) -> Tuple["COLUMNDTYPE", Optional[Union[int, str]]]:
        """Select appropriate string type."""
        # Ensure max_length is at least min_char_bytes
        effective_length = max(max_length, min_char_bytes) if max_length else None

        if use_fixed_length and effective_length:
            compatible, _ = cls.get_dialect_compatible_type(cls.NCHAR, dialect)
            return (compatible, effective_length)

        if effective_length:
            compatible, _ = cls.get_dialect_compatible_type(cls.NVARCHAR, dialect)
            return (compatible, effective_length)

        return cls.get_dialect_compatible_type(cls.TEXT, dialect)

    @classmethod
    def _select_optimal_boolean(cls, dialect: SQLDialect) -> Tuple["COLUMNDTYPE", Optional[Any]]:
        """Select appropriate boolean type for dialect."""
        # Use BOOLEAN as base and let get_dialect_compatible_type handle mapping
        return cls.get_dialect_compatible_type(cls.BOOLEAN, dialect)

    @classmethod
    def _select_optimal_datetime(
        cls,
        dialect: SQLDialect,
        timezone_aware: bool,
        time_precision: Optional[Literal["second", "millisecond", "microsecond", "nanosecond", "ms", "us", "ns", "auto"]] = None
    ) -> Tuple["COLUMNDTYPE", Optional[int]]:
        """Select appropriate datetime type with optional precision."""
        # Map precision names to numeric values (digits after decimal for seconds)
        precision_map = {
            'second': 0,
            'millisecond': 3, 'ms': 3,
            'microsecond': 6, 'us': 6,
            'nanosecond': 9, 'ns': 9,
            'auto': None,
        }
        precision_value = precision_map.get(str(time_precision).lower(), None)

        # Select base type based on timezone requirement
        base_type = cls.TIMESTAMPTZ if timezone_aware else cls.TIMESTAMP

        # Get dialect-compatible type
        compatible, params = cls.get_dialect_compatible_type(base_type, dialect)

        # Return with precision if specified, otherwise use any params from dialect mapping
        return (compatible, precision_value if precision_value is not None else params)

    @classmethod
    def _select_optimal_binary(
        cls, dialect: SQLDialect, max_length: Optional[int]
    ) -> Tuple["COLUMNDTYPE", Optional[Union[int, str]]]:
        """Select appropriate binary type."""
        if max_length:
            # Use VARBINARY with length
            compatible, _ = cls.get_dialect_compatible_type(cls.VARBINARY, dialect)
            return (compatible, max_length)

        # Use BLOB for unlimited binary - let dialect mapping handle it
        return cls.get_dialect_compatible_type(cls.BLOB, dialect)


class Column_Type(NamedTuple):
    """
    Named tuple representing a resolved column data type with dialect-specific properties.

    This immutable data structure provides efficient access to all column type
    properties with dialect-specific overrides already materialized. Unlike the
    COLUMNDTYPE enum which contains special_properties requiring runtime lookups,
    Column_Type has all properties resolved for a specific dialect.

    The Column_Type is created by calling COLUMNDTYPE.get_types_for_dialect()
    and provides a lightweight, high-performance way to work with type metadata.

    Attributes
    ----------
    name : str
        Enum member name (e.g., 'VARCHAR', 'INTEGER').
    name_value : str
        String name of the data type (e.g., 'varchar', 'integer').
    category : str
        Type category (e.g., 'numeric_integer', 'text_variable', 'datetime').
    description : str
        Human-readable description of the data type.
    min_bytes : int
        Minimum storage size in bytes for this type.
    max_bytes : int
        Maximum storage size in bytes for this type.
    max_precision : Optional[int]
        Maximum precision or length allowed (None if not applicable).
    time_zone_support : bool
        Whether this type supports timezone information.
    supported_dialects : List[SQLDialect]
        List of SQL dialects that natively support this type.
    min_value : Optional[Union[int, float]]
        Minimum value for numeric types (None for non-numeric types).
    max_value : Optional[Union[int, float]]
        Maximum value for numeric types (None for non-numeric types).
    metadata : Dict[str, Any]
        Complete metadata dictionary with all properties (dialect-specific
        overrides already applied, special_properties removed).
    dtype : COLUMNDTYPE
        Original enum member for reference back to the source type.
    dialect : SQLDialect
        The SQL dialect for which this type is resolved.
    driver : Dict[str, Any]
        Best available driver information for the dialect.

    Methods
    -------
    is_fixed_length(_dialect=None)
        Check if the type is fixed-length.
    supports_dialect(dialect)
        Check if this type is supported by a dialect.
    get_property(property_name, default=None)
        Get a property value from the metadata.
    validate_identifier(identifier, correction_method='normalize')
        Validate an identifier against column type rules.
    get_byte_size(precision_name)
        Get byte size for temporal types with specified precision.
    optimal_type
        Property returning the optimal Python type for this SQL type.
    format_hints
        Property returning format hints dictionary.
    get_upload_format_info()
        Get comprehensive upload format information.

    Examples
    --------
    >>> # Create a resolved type for PostgreSQL
    >>> pg_varchar = COLUMNDTYPE.VARCHAR.get_types_for_dialect(SQLDialect.POSTGRES)
    >>> print(pg_varchar.name)
    VARCHAR
    >>> print(pg_varchar.max_bytes)
    10485760
    >>> print(pg_varchar.category)
    text_variable

    >>> # Access optimal Python type
    >>> print(pg_varchar.optimal_type)
    <class 'str'>

    >>> # Check format hints
    >>> hints = pg_varchar.format_hints
    >>> print(hints['encoding'])
    utf-8
    """

    name: str  # Enum member name (e.g., 'VARCHAR')
    name_value: str  # String type name (e.g., 'varchar')
    category: str  # Type category (e.g., 'text_variable')
    description: str  # Human-readable description
    min_bytes: int  # Minimum storage bytes
    max_bytes: int  # Maximum storage bytes
    max_precision: Optional[int]  # Maximum precision/length
    time_zone_support: bool  # Timezone support flag
    supported_dialects: List["SQLDialect"]  # Supported SQL dialects
    min_value: Optional[Union[int, float]]  # Min value (numeric types)
    max_value: Optional[Union[int, float]]  # Max value (numeric types)
    metadata: Dict[str, Any]  # Full metadata dictionary
    dtype: COLUMNDTYPE  # Original enum member reference
    dialect: SQLDialect  # Dialect for which this type is resolved
    driver: Dict[str, Any]  # Driver information for the dialect

    def is_fixed_length(self, _dialect: Optional["SQLDialect"] = None) -> bool:
        """Return whether the data type is fixed length."""
        # Check for explicit override in metadata
        if "fixed_length" in self.metadata:
            return self.metadata["fixed_length"]

        # Default logic: fixed length if min_bytes == max_bytes
        if self.min_bytes is not None and self.max_bytes is not None:
            return self.min_bytes == self.max_bytes

        # For text types, assume variable length unless specified
        return self.category in ["text_fixed", "binary"]

    def supports_dialect(self, dialect: "SQLDialect") -> bool:
        """Check if this data type is supported by the specified SQL dialect."""
        return dialect.resolved_alias in self.supported_dialects

    def get_property(self, property_name: str, default: Any = None) -> Any:
        """Get a property value from the metadata."""
        return self.metadata.get(property_name, default)

    def validate_identifier(
        self, identifier: str, correction_method: Literal["encapsulate", "normalize"] = "normalize"
    ) -> Dict[str, Any]:
        """
        Validate an identifier against the column type's rules.

        Args:
            identifier: The identifier to validate

        Returns:
            Dict[str, Any]: Validation result with 'valid' boolean and 'message' string
        """
        # Lazy import to avoid circular dependency
        try:
            from validation.identifiers import SQL_DIALECT_REGISTRY
        except ImportError:
            from ..validation.identifiers import SQL_DIALECT_REGISTRY

        return SQL_DIALECT_REGISTRY.validate_identifier(
            identifier=identifier,
            dialect=self.dialect,
            context=DatabaseObjectType.COLUMN,
            correction_method=correction_method,
        )

    def get_byte_size(self, precision_name: PrecisionLevel) -> Optional[int]:
        """
        Get byte size for this column type with the specified precision.

        Uses the TemporalPrecision class with this column type's own dialect and dtype.
        This is particularly useful for temporal data types that have variable byte sizes
        based on precision (e.g., DATETIME2, TIME in SQL Server).

        Args:
            precision_name: The precision name ('second', 'millisecond', 'microsecond', 'nanosecond')
                          Also supports short forms: 'ms', 'us', 'ns'

        Returns:
            Optional[int]: Number of bytes required for this data type at the specified precision,
                          or None if precision is not supported or invalid

        Usage:
            >>> # SQL Server DATETIME2 with microsecond precision
            >>> dt2 = COLUMNDTYPE.DATETIME2.get_clean_enum_for_dialect(SQLDialect.SQLSERVER)
            >>> dt2.get_byte_size('microsecond')  # Returns 8
            >>> dt2.get_byte_size('millisecond')  # Returns 7

            >>> # PostgreSQL TIMESTAMP (always 8 bytes regardless of precision)
            >>> ts = COLUMNDTYPE.TIMESTAMP.get_clean_enum_for_dialect(SQLDialect.POSTGRES)
            >>> ts.get_byte_size('microsecond')  # Returns 8
        """
        return TemporalPrecision.get_byte_size(precision_name, self.dialect, self.dtype)

    @property
    def optimal_type(self) -> Union[type, str]:
        """
        Get the optimal Python type for this column data type.

        Returns:
            Union[type, str]: The optimal Python type (e.g., int, str, bytes) or
                             string representation for complex types (e.g., "decimal.Decimal", "datetime.date")

        Usage:
            >>> varchar = COLUMNDTYPE.VARCHAR.get_clean_enum_for_dialect(SQLDialect.POSTGRES)
            >>> varchar.get_optimal_type()  # Returns str

            >>> decimal_type = COLUMNDTYPE.DECIMAL.get_clean_enum_for_dialect(SQLDialect.POSTGRES)
            >>> decimal_type.get_optimal_type()  # Returns "decimal.Decimal"
        """
        return self.metadata.get("optimal_type", str)

    @property
    def format_hints(self) -> Dict[str, Any]:
        """
        Get format hints for this column data type.

        Returns:
            Dict[str, Any]: Dictionary containing format hints specific to this data type and dialect

        Usage:
            >>> varchar = COLUMNDTYPE.VARCHAR.get_clean_enum_for_dialect(SQLDialect.MYSQL)
            >>> hints = varchar.get_format_hints()
            >>> print(hints)  # {'encoding': 'utf8mb4', 'collation': 'utf8mb4_unicode_ci'}
        """
        return self.metadata.get("format_hints", {})

    def get_upload_format_info(self) -> Dict[str, Any]:
        """
        Get comprehensive upload format information for this column data type.

        Returns:
            Dict[str, Any]: Dictionary containing optimal type, format hints, and upload guidance

        Usage:
            >>> decimal_col = COLUMNDTYPE.DECIMAL.get_clean_enum_for_dialect(SQLDialect.POSTGRES)
            >>> info = decimal_col.get_upload_format_info()
            >>> print(info['optimal_type'])  # "decimal.Decimal"
            >>> print(info['format_hints']['precision_required'])  # True
        """
        return {
            "optimal_type": self.optimal_type,
            "format_hints": self.format_hints,
            "category": self.category,
            "dialect": self.dialect.value,
            "max_bytes": self.max_bytes,
            "max_precision": self.max_precision,
            "supports_null": True,  # Most database columns support NULL
            "time_zone_support": self.time_zone_support,
        }

    def __str__(self) -> str:
        return self.name_value

    def __repr__(self) -> str:
        return f"CleanColumnType({self.name})"


class TemporalPrecision:
    """
    Utility class for temporal data type precision calculations.

    This class provides methods for calculating storage byte sizes of temporal
    data types (datetime, timestamp, time) based on precision level and SQL
    dialect. Different database systems have varying storage requirements for
    temporal precision, and this class encapsulates those dialect-specific rules.

    Precision Levels
    ----------------
    The class supports the following precision levels:
    - 'second' (0): Second precision (no fractional seconds)
    - 'millisecond' or 'ms' (3): Millisecond precision (3 decimal places)
    - 'microsecond' or 'us' (6): Microsecond precision (6 decimal places)
    - 'nanosecond' or 'ns' (9): Nanosecond precision (9 decimal places)

    Storage Requirements by Dialect
    --------------------------------
    PostgreSQL, SQLite, BigQuery, Redshift:
        All temporal types use 8 bytes regardless of precision.

    SQL Server:
        Variable bytes based on precision and type:
        - DATETIME2: 6-8 bytes (depending on precision)
        - TIME: 3-5 bytes (depending on precision)
        - DATETIMEOFFSET: 8-10 bytes (depending on precision)
        - DATETIME: Fixed 8 bytes
        - SMALLDATETIME: Fixed 4 bytes

    MySQL:
        Variable bytes based on precision:
        - DATETIME: 5-7 bytes (depending on precision)
        - TIME: 3-5 bytes (depending on precision)
        - TIMESTAMP: 4 or 7 bytes (depending on precision)

    Oracle:
        - TIMESTAMP: 7 or 11 bytes (7 for precision 0, 11 otherwise)

    Class Attributes
    ----------------
    PRECISION_MAP : Dict[str, int]
        Mapping from precision names to numeric precision values.
    DIALECT_BYTE_MAP : Dict[SQLDialect, Union[int, Dict]]
        Mapping from dialects to byte size rules (fixed or type-specific).

    Methods
    -------
    get_byte_size(precision_name, dialect, data_type=COLUMNDTYPE.TIMESTAMP)
        Calculate byte size for a temporal type with specified precision.

    Examples
    --------
    >>> # PostgreSQL uses fixed 8 bytes for all temporal types
    >>> TemporalPrecision.get_byte_size('millisecond', SQLDialect.POSTGRES, COLUMNDTYPE.TIMESTAMP)
    8
    >>> TemporalPrecision.get_byte_size('microsecond', SQLDialect.POSTGRES, COLUMNDTYPE.TIMESTAMP)
    8

    >>> # SQL Server DATETIME2 uses variable bytes
    >>> TemporalPrecision.get_byte_size('millisecond', SQLDialect.SQLSERVER, COLUMNDTYPE.DATETIME2)
    7
    >>> TemporalPrecision.get_byte_size('microsecond', SQLDialect.SQLSERVER, COLUMNDTYPE.DATETIME2)
    8

    >>> # MySQL TIMESTAMP uses 4 or 7 bytes
    >>> TemporalPrecision.get_byte_size('second', SQLDialect.MYSQL, COLUMNDTYPE.TIMESTAMP)
    4
    >>> TemporalPrecision.get_byte_size('millisecond', SQLDialect.MYSQL, COLUMNDTYPE.TIMESTAMP)
    7

    >>> # Use short-form precision names
    >>> TemporalPrecision.get_byte_size('ms', SQLDialect.POSTGRES, COLUMNDTYPE.TIMESTAMP)
    8
    >>> TemporalPrecision.get_byte_size('us', SQLDialect.SQLSERVER, COLUMNDTYPE.DATETIME2)
    8
    """

    # Core precision mapping from precision names to numeric precision values.
    # Supports both full names and common abbreviations for convenience.
    PRECISION_MAP = {
        "second": 0,  # Second precision (no fractional seconds)
        "millisecond": 3,  # Millisecond precision (3 decimal places)
        "microsecond": 6,  # Microsecond precision (6 decimal places)
        "nanosecond": 9,  # Nanosecond precision (9 decimal places)
        "ms": 3,  # Abbreviation for millisecond
        "us": 6,  # Abbreviation for microsecond
        "ns": 9,  # Abbreviation for nanosecond
    }

    # Dialect-specific byte size mappings for temporal types.
    # Simple dialects use a fixed integer (all types same size).
    # Complex dialects use a dictionary mapping types to sizes or lambda functions.
    DIALECT_BYTE_MAP = {
        SQLDialect.POSTGRES: 8,  # All temporal types use 8 bytes in PostgreSQL.
        SQLDialect.SQLSERVER: {  # SQL Server uses variable bytes based on precision.
            # DATETIME2 uses 6-8 bytes depending on fractional precision.
            COLUMNDTYPE.DATETIME2: lambda p: 6 if p <= 2 else (7 if p <= 4 else 8),
            # TIME uses 3-5 bytes depending on fractional precision.
            COLUMNDTYPE.TIME: lambda p: 3 if p <= 2 else (4 if p <= 4 else 5),
            # DATETIMEOFFSET uses 8-10 bytes depending on fractional precision.
            COLUMNDTYPE.DATETIMEOFFSET: lambda p: 8 if p <= 2 else (9 if p <= 4 else 10),
            # DATETIME is always 8 bytes (fixed precision).
            COLUMNDTYPE.DATETIME: 8,
            # SMALLDATETIME is always 4 bytes (fixed precision).
            COLUMNDTYPE.SMALLDATETIME: 4,
        },
        SQLDialect.MYSQL: {  # MySQL uses variable bytes based on precision.
            # DATETIME uses 5-7 bytes depending on fractional precision.
            COLUMNDTYPE.DATETIME: lambda p: 5 if p == 0 else (6 if p <= 3 else 7),
            # TIME uses 3-5 bytes depending on fractional precision.
            COLUMNDTYPE.TIME: lambda p: 3 if p == 0 else (4 if p <= 3 else 5),
            # TIMESTAMP uses 4 or 7 bytes depending on fractional precision.
            COLUMNDTYPE.TIMESTAMP: lambda p: 4 if p == 0 else 7,
        },
        SQLDialect.ORACLE: {  # Oracle has special precision handling.
            # TIMESTAMP uses 7 bytes for precision 0, 11 bytes otherwise.
            COLUMNDTYPE.TIMESTAMP: lambda p: 7 if p == 0 else 11,
        },
        # Simple dialects with fixed byte sizes for all temporal types.
        SQLDialect.SQLITE: 8,
        SQLDialect.BIGQUERY: 8,
        SQLDialect.REDSHIFT: 8,
    }

    @classmethod
    def get_byte_size(
        cls, precision_name: PrecisionLevel, dialect: SQLDialect, data_type: COLUMNDTYPE = COLUMNDTYPE.TIMESTAMP
    ) -> Optional[int]:
        """
        Calculate byte size for a temporal data type with specified precision.

        This method determines the storage size in bytes for temporal data types
        (datetime, timestamp, time) based on the precision level and SQL dialect.
        Different databases have varying storage requirements for temporal precision.

        Parameters
        ----------
        precision_name : PrecisionLevel
            The precision level as a string. Supported values:
            - 'second', 'millisecond', 'microsecond', 'nanosecond'
            - Short forms: 'ms', 'us', 'ns'
        dialect : SQLDialect
            The SQL dialect to calculate byte size for.
        data_type : COLUMNDTYPE, optional
            The temporal data type (e.g., TIMESTAMP, DATETIME2, TIME).
            Default is COLUMNDTYPE.TIMESTAMP.

        Returns
        -------
        Optional[int]
            Number of bytes required for the specified type, dialect, and
            precision. Returns None if the precision is invalid or not supported.

        Examples
        --------
        >>> # PostgreSQL uses fixed 8 bytes for all temporal types
        >>> TemporalPrecision.get_byte_size('millisecond', SQLDialect.POSTGRES)
        8
        >>> TemporalPrecision.get_byte_size('us', SQLDialect.POSTGRES)
        8

        >>> # SQL Server DATETIME2 uses variable bytes
        >>> TemporalPrecision.get_byte_size('millisecond', SQLDialect.SQLSERVER, COLUMNDTYPE.DATETIME2)
        7
        >>> TemporalPrecision.get_byte_size('microsecond', SQLDialect.SQLSERVER, COLUMNDTYPE.DATETIME2)
        8

        >>> # MySQL TIMESTAMP varies by precision
        >>> TemporalPrecision.get_byte_size('second', SQLDialect.MYSQL, COLUMNDTYPE.TIMESTAMP)
        4
        >>> TemporalPrecision.get_byte_size('ms', SQLDialect.MYSQL, COLUMNDTYPE.TIMESTAMP)
        7
        """
        # Convert precision name to numeric precision value.
        precision_value = cls.PRECISION_MAP.get(precision_name.lower())
        if precision_value is None:
            # Invalid precision name.
            return None

        # Use resolved dialect alias to handle aliases (e.g., POSTGRESQL -> POSTGRES).
        dialect_enum = dialect.resolved_alias

        # Get byte size configuration for this dialect.
        dialect_config = cls.DIALECT_BYTE_MAP.get(dialect_enum)
        if dialect_config is None:
            # Dialect not found in mapping.
            return None

        # Simple case: dialect uses fixed bytes for all temporal types.
        if isinstance(dialect_config, int):
            return dialect_config

        # Complex case: dialect has type-specific byte size rules.
        data_type_enum = data_type
        if data_type_enum in dialect_config:
            type_config = dialect_config[data_type_enum]
            if callable(type_config):
                # Lambda function computes bytes based on precision value.
                result = type_config(precision_value)
                return int(result) if isinstance(result, (int, float)) else None
            else:
                # Fixed byte size for this specific type.
                return int(type_config) if isinstance(type_config, (int, float)) else type_config

        # Fallback for unlisted types: use 8 bytes if dialect has simple mapping.
        return (
            8
            if dialect_enum in [SQLDialect.POSTGRES, SQLDialect.SQLITE, SQLDialect.BIGQUERY, SQLDialect.REDSHIFT]
            else None
        )
