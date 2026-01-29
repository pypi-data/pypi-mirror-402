"""
Database type mapping and column metadata extraction module.

This module provides comprehensive type mapping between database-specific type
codes/names and Python types across multiple SQL dialects. It handles the
conversion of cursor description metadata into standardized Python type
information for proper dataframe construction.

The module supports:
- Type mapping for 5 SQL dialects (PostgreSQL, MySQL, Oracle, SQL Server, SQLite)
- Cursor description parsing with multiple format support
- SQLite-specific type inference using query parsing
- Expression type inference for derived columns
- Graceful fallback for unknown types

Type mappings reflect the ACTUAL Python types returned by database drivers,
not theoretical conversions (e.g., PostgreSQL NUMERIC returns float, not Decimal).

Constants
---------
DB_TYPE_MAPPINGS : Dict[SQLDialect, Dict[Union[int, str], type]]
    Comprehensive mapping of database type codes and names to Python types
    for each supported SQL dialect.

Functions
---------
_map_db_type_to_python
    Map database type code or name to Python type for a specific dialect.
_extract_column_metadata_from_description
    Extract standardized column metadata from cursor description.
_infer_sqlite_column_types_from_query
    Infer SQLite column types using query parsing and PRAGMA inspection.
_infer_expression_type
    Infer Python type from a SQLGlot expression node.
_create_fallback_columns
    Create generic column metadata when no description is available.

Examples
--------
>>> from drivers.type_mapping import _map_db_type_to_python
>>> from core.enums import SQLDialect
>>>
>>> # Map PostgreSQL type code to Python type
>>> python_type = _map_db_type_to_python(23, None, SQLDialect.POSTGRES)
>>> print(python_type)
<class 'int'>
>>>
>>> # Extract metadata from cursor description
>>> cursor = connection.execute("SELECT id, name FROM users")
>>> columns = _extract_column_metadata_from_description(cursor.description, SQLDialect.MYSQL)
>>> print(columns)
{'id': <class 'int'>, 'name': <class 'str'>}

Notes
-----
- Type mappings are based on actual driver behavior, not SQL standard definitions
- Oracle DATE always maps to datetime.datetime (includes time component)
- SQLite requires special handling due to its dynamic type system
- JSON/JSONB types map to dict (parsed JSON) not str
- DECIMAL/NUMERIC map to float (driver behavior) not decimal.Decimal

See Also
--------
DatabaseConnection : Connection interface providing cursor access
execute_query_with_metadata : Query execution with type metadata
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from ..core.enums import SQLDialect

if TYPE_CHECKING:
    from ..connections.database_connection import DatabaseConnection

# Optional dependency: SQLGlot for SQL query parsing and type inference
try:
    from sqlglot import exp, parse_one

    SQLGLOT_AVAILABLE = True
except ImportError:
    # SQLGlot not available - SQLite type inference will be limited
    parse_one = None
    exp = None
    SQLGLOT_AVAILABLE = False


from CoreUtilities import LogLevel, get_logger

# Configure module logger with emoji support for better readability
logger = get_logger("type_mapping", include_performance=False, include_emoji=True)

# Database type code to Python type mappings
# Maps database-specific type codes (integers) and type names (strings) to Python types
# Note: These reflect ACTUAL types returned by database drivers, not theoretical conversions
# For example: PostgreSQL NUMERIC returns float (not Decimal), Oracle DATE returns datetime
DB_TYPE_MAPPINGS = {
    # PostgreSQL type mappings (psycopg2/psycopg3 drivers)
    # Type codes are OID values from PostgreSQL system catalogs
    SQLDialect.POSTGRES: {
        16: bool,  # BOOLEAN -> bool
        20: int,  # BIGINT -> int
        21: int,  # SMALLINT -> int
        23: int,  # INTEGER -> int
        25: str,  # TEXT -> str
        114: dict,  # JSON -> dict (parsed JSON)
        3802: dict,  # JSONB -> dict (parsed JSON)
        700: float,  # REAL -> float
        701: float,  # DOUBLE PRECISION -> float
        1082: datetime.date,  # DATE -> datetime.date object
        1083: datetime.time,  # TIME -> datetime.time object
        1114: datetime.datetime,  # TIMESTAMP -> datetime.datetime object
        1184: datetime.datetime,  # TIMESTAMPTZ -> datetime.datetime object
        1266: datetime.time,  # TIMETZ -> datetime.time with timezone
        1700: float,  # NUMERIC -> decimal.Decimal object
        2950: str,  # UUID -> str
        142: str,  # XML -> str
        # String representations for common types
        "boolean": bool,
        "bigint": int,
        "integer": int,
        "smallint": int,
        "text": str,
        "varchar": str,
        "char": str,
        "json": dict,  # JSON is parsed to dict
        "jsonb": dict,  # JSONB is parsed to dict
        "real": float,
        "double precision": float,
        "numeric": float,
        "decimal": float,
        "date": datetime.date,
        "time": datetime.time,
        "timestamp": datetime.datetime,
        "timestamptz": datetime.datetime,
        "uuid": str,
        "bytea": bytes,  # Binary data -> bytes
        "timetz": datetime.time,  # TIME WITH TIME ZONE -> datetime.time
        "xml": str,  # XML -> str
    },
    # MySQL type codes and names
    SQLDialect.MYSQL: {
        0: float,  # DECIMAL -> decimal.Decimal
        1: int,  # TINY -> int
        2: int,  # SHORT -> int
        3: int,  # LONG -> int
        4: float,  # FLOAT -> float
        5: float,  # DOUBLE -> float
        7: datetime.datetime,  # TIMESTAMP -> datetime.datetime
        8: int,  # LONGLONG -> int
        9: int,  # INT24 -> int
        10: datetime.date,  # DATE -> datetime.date
        11: datetime.time,  # TIME -> datetime.time or datetime.timedelta
        12: datetime.datetime,  # DATETIME -> datetime.datetime
        13: int,  # YEAR -> int
        15: str,  # VARCHAR -> str
        16: int,  # BIT -> int (MySQL returns as int)
        246: float,  # NEWDECIMAL -> decimal.Decimal
        252: str,  # BLOB -> str (for TEXT types) or bytes (for binary BLOB)
        253: str,  # VAR_STRING -> str
        254: str,  # STRING -> str
        # String representations
        "tinyint": int,
        "smallint": int,
        "mediumint": int,
        "int": int,
        "integer": int,
        "bigint": int,
        "float": float,
        "double": float,
        "decimal": float,
        "numeric": float,
        "date": datetime.date,
        "time": datetime.time,
        "datetime": datetime.datetime,
        "timestamp": datetime.datetime,
        "year": int,
        "char": str,
        "varchar": str,
        "text": str,  # TEXT should be str, not bytes
        "tinytext": str,  # TINYTEXT -> str
        "mediumtext": str,  # MEDIUMTEXT -> str
        "longtext": str,  # LONGTEXT -> str
        "blob": bytes,  # BLOB is binary -> bytes
        "tinyblob": bytes,  # TINYBLOB -> bytes
        "mediumblob": bytes,  # MEDIUMBLOB -> bytes
        "longblob": bytes,  # LONGBLOB -> bytes
        "json": dict,  # MySQL JSON is parsed to dict
        "bit": int,
        "boolean": bool,  # MySQL BOOLEAN -> bool
        "bool": bool,  # MySQL BOOL -> bool
    },
    # Oracle type codes and names
    SQLDialect.ORACLE: {
        1: str,  # VARCHAR2 -> str
        2: float,  # NUMBER -> float (will be overridden by scale check)
        8: str,  # LONG -> str
        12: datetime.datetime,  # DATE -> datetime.datetime (Oracle DATE includes time)
        23: bytes,  # RAW -> bytes
        24: bytes,  # LONG RAW -> bytes
        96: str,  # CHAR -> str
        112: str,  # CLOB -> str (or file-like object for large)
        113: bytes,  # BLOB -> bytes (or file-like object for large)
        180: datetime.datetime,  # TIMESTAMP -> datetime.datetime
        181: datetime.datetime,  # TIMESTAMP WITH TIME ZONE -> datetime.datetime
        231: datetime.datetime,  # TIMESTAMP WITH LOCAL TIME ZONE -> datetime.datetime
        # String representations
        "varchar2": str,
        "varchar": str,
        "char": str,
        "nchar": str,
        "nvarchar2": str,
        "number": float,
        "float": float,
        "binary_float": float,
        "binary_double": float,
        "date": datetime.datetime,  # Oracle DATE always includes time
        "timestamp": datetime.datetime,
        "clob": str,
        "nclob": str,
        "blob": bytes,
        "raw": bytes,
        "long": str,
        "long raw": bytes,
        "DB_TYPE_VARCHAR": str,  # VARCHAR2/VARCHAR -> str
        "DB_TYPE_NVARCHAR": str,  # NVARCHAR2 -> str
        "DB_TYPE_CHAR": str,  # CHAR -> str
        "DB_TYPE_NCHAR": str,  # NCHAR -> str
        "DB_TYPE_NUMBER": float,  # NUMBER -> float/int (depending on scale)
        "DB_TYPE_BINARY_INTEGER": int,  # BINARY_INTEGER -> int
        "DB_TYPE_BINARY_FLOAT": float,  # BINARY_FLOAT -> float
        "DB_TYPE_BINARY_DOUBLE": float,  # BINARY_DOUBLE -> float
        "DB_TYPE_DATE": datetime.datetime,  # DATE -> datetime.datetime
        "DB_TYPE_TIMESTAMP": datetime.datetime,  # TIMESTAMP -> datetime.datetime
        "DB_TYPE_TIMESTAMP_LTZ": datetime.datetime,  # TIMESTAMP WITH LOCAL TIME ZONE -> datetime.datetime
        "DB_TYPE_TIMESTAMP_TZ": datetime.datetime,  # TIMESTAMP WITH TIME ZONE -> datetime.datetime
        "DB_TYPE_INTERVAL_DS": str,  # INTERVAL DAY TO SECOND -> str (or timedelta)
        "DB_TYPE_INTERVAL_YM": str,  # INTERVAL YEAR TO MONTH -> str
        "DB_TYPE_CLOB": str,  # CLOB -> str
        "DB_TYPE_NCLOB": str,  # NCLOB -> str
        "DB_TYPE_BLOB": bytes,  # BLOB -> bytes
        "DB_TYPE_BFILE": str,  # BFILE -> str (file reference)
        "DB_TYPE_RAW": bytes,  # RAW -> bytes
        "DB_TYPE_LONG": str,  # LONG -> str
        "DB_TYPE_LONG_RAW": bytes,  # LONG RAW -> bytes
        "DB_TYPE_ROWID": str,  # ROWID -> str
        "DB_TYPE_UROWID": str,  # UROWID -> str
        "DB_TYPE_XMLTYPE": str,  # XMLType -> str
        "DB_TYPE_JSON": dict,  # JSON -> dict (parsed JSON)
        "DB_TYPE_BOOLEAN": bool,  # BOOLEAN -> bool (Oracle 23c+)
    },
    # SQLite type names (SQLite uses dynamic typing, returns Python native types)
    SQLDialect.SQLITE: {
        "integer": int,
        "real": float,
        "text": str,
        "blob": bytes,
        "numeric": float,
        "boolean": bool,  # SQLite doesn't have native bool, but some adapters convert
        "date": datetime.date,  # Depends on adapter
        "datetime": datetime.datetime,
        "time": datetime.time,
    },
    # SQL Server type codes and names
    SQLDialect.SQLSERVER: {
        -7: bool,  # BIT -> bool (pyodbc converts to True/False)
        -6: int,  # TINYINT -> int
        5: int,  # SMALLINT -> int
        4: int,  # INT -> int
        -5: int,  # BIGINT -> int
        6: float,  # FLOAT -> float
        7: float,  # REAL -> float
        2: float,  # NUMERIC -> decimal.Decimal
        3: float,  # DECIMAL -> decimal.Decimal
        1: str,  # CHAR -> str
        12: str,  # VARCHAR -> str
        -1: str,  # TEXT -> str
        -8: str,  # NCHAR -> str
        -9: str,  # NVARCHAR -> str
        -10: str,  # NTEXT -> str
        91: datetime.date,  # DATE -> datetime.date
        92: datetime.time,  # TIME -> datetime.time
        93: datetime.datetime,  # TIMESTAMP/DATETIME -> datetime.datetime
        -2: bytes,  # BINARY -> bytes
        -3: bytes,  # VARBINARY -> bytes
        -4: bytes,  # IMAGE -> bytes
        # String representations
        "bit": bool,
        "tinyint": int,
        "smallint": int,
        "int": int,
        "bigint": int,
        "float": float,
        "real": float,
        "decimal": float,
        "numeric": float,
        "money": float,
        "smallmoney": float,
        "char": str,
        "varchar": str,
        "text": str,
        "nchar": str,
        "nvarchar": str,
        "ntext": str,
        "date": datetime.date,
        "time": datetime.time,
        "datetime": datetime.datetime,
        "datetime2": datetime.datetime,
        "smalldatetime": datetime.datetime,
        "datetimeoffset": datetime.datetime,
        "binary": bytes,
        "varbinary": bytes,
        "image": bytes,
        "uniqueidentifier": str,
        "xml": str,
    },
}


def _map_db_type_to_python(db_type: Any, scale: Optional[int], dialect: SQLDialect) -> type:
    """
    Map database-specific type code or name to Python type.

    This function translates database-specific type identifiers (integer codes
    or string names) into Python types based on the SQL dialect. It handles
    special cases like NUMERIC with scale=0 (returns int instead of float).

    Parameters
    ----------
    db_type : Any
        Database type code (int) or type name (str). Can also be a type object
        or object with __name__ or name attributes.
    scale : int, optional
        Numeric scale for decimal types. When scale=0, NUMERIC/DECIMAL types
        are mapped to int instead of float. Default is None.
    dialect : SQLDialect
        SQL dialect enum value indicating which database's type system to use.

    Returns
    -------
    type
        Python type class representing the actual type returned by the database
        driver. Returns object for unknown types or unsupported dialects.

    Examples
    --------
    >>> from core.enums import SQLDialect
    >>> # PostgreSQL INTEGER (type code 23)
    >>> _map_db_type_to_python(23, None, SQLDialect.POSTGRES)
    <class 'int'>
    >>>
    >>> # PostgreSQL NUMERIC with scale=2 (returns float)
    >>> _map_db_type_to_python(1700, 2, SQLDialect.POSTGRES)
    <class 'float'>
    >>>
    >>> # PostgreSQL NUMERIC with scale=0 (returns int, not float)
    >>> _map_db_type_to_python(1700, 0, SQLDialect.POSTGRES)
    <class 'int'>
    >>>
    >>> # MySQL VARCHAR by name
    >>> _map_db_type_to_python('varchar', None, SQLDialect.MYSQL)
    <class 'str'>

    Notes
    -----
    - If db_type is already a Python type, it is returned unchanged
    - NUMERIC/DECIMAL types with scale=0 are treated as integers (database stores whole numbers)
    - Unknown types return object as a safe fallback
    - Type mappings reflect actual driver behavior, not SQL standard definitions
    """
    # Return object for missing type or unsupported dialect
    if (not db_type) or (dialect not in DB_TYPE_MAPPINGS):
        return object

    # If already a Python type, return as-is
    elif isinstance(db_type, type):
        return db_type

    # Lookup type in dialect-specific mapping
    mapping = DB_TYPE_MAPPINGS[dialect]

    # Try multiple lookup strategies for different type representation formats
    # 1. Direct lookup (int code or str name)
    # 2. Lookup by __name__ attribute (type objects)
    # 3. Lookup by name attribute (some driver objects)
    # 4. Fallback to string representation
    out: type = mapping.get(
        db_type,
        mapping.get(
            (
                db_type.__name__
                if hasattr(db_type, "__name__")
                else db_type.name if hasattr(db_type, "name") else str(db_type)
            ),
            "unknown",
        ),
    )

    # Special case: NUMERIC/DECIMAL with scale=0 should return int, not float
    # This handles cases like NUMERIC(10,0) which stores only integers
    return int if ((out == float) and (scale is not None and scale == 0)) else out


def _extract_column_metadata_from_description(description: Any, dialect: SQLDialect) -> Dict[str, Any]:
    """
    Extract standardized column metadata from cursor description.

    This function parses cursor description tuples (from DB-API 2.0 compliant
    drivers) and extracts column names and Python types. It handles multiple
    description formats used by different database drivers.

    The standard DB-API 2.0 cursor.description format is:
    (name, type_code, display_size, internal_size, precision, scale, null_ok)

    Parameters
    ----------
    description : Any
        Cursor description sequence. Can be:
        - List/tuple of tuples (standard DB-API format)
        - List of objects with name/type_code attributes
        - Other iterable metadata structures
    dialect : SQLDialect
        SQL dialect enum value for type mapping.

    Returns
    -------
    Dict[str, Any]
        Dictionary mapping column names to Python type classes.
        Returns empty dict if description is None or empty.

    Examples
    --------
    >>> # Standard tuple format (PostgreSQL)
    >>> description = [
    ...     ('id', 23, None, None, None, None, None),
    ...     ('name', 25, None, None, None, None, None),
    ...     ('salary', 1700, None, None, 10, 2, None)
    ... ]
    >>> columns = _extract_column_metadata_from_description(description, SQLDialect.POSTGRES)
    >>> print(columns)
    {'id': <class 'int'>, 'name': <class 'str'>, 'salary': <class 'float'>}
    >>>
    >>> # Object format (Oracle)
    >>> class ColDesc:
    ...     def __init__(self, name, type_code, scale):
    ...         self.name = name
    ...         self.type_code = type_code
    ...         self.scale = scale
    >>> description = [ColDesc('emp_id', 2, 0), ColDesc('salary', 2, 2)]
    >>> columns = _extract_column_metadata_from_description(description, SQLDialect.ORACLE)
    >>> print(columns)
    {'emp_id': <class 'int'>, 'salary': <class 'float'>}

    Notes
    -----
    - Unnamed columns are assigned generated names: 'unnamed_column_0', 'unnamed_column_1', etc.
    - Unknown types are marked as 'unknown' string for graceful degradation
    - The scale field (index 5 in tuple format) is used to distinguish integers from floats
    """
    columns = {}

    # Return empty dict for None or empty description
    if not description:
        return columns

    # Iterate through column descriptions and extract metadata
    for i, col_desc in enumerate(description):
        # Format 1: Standard DB-API 2.0 tuple/list format
        # (name, type_code, display_size, internal_size, precision, scale, null_ok)
        if isinstance(col_desc, (tuple, list)) and len(col_desc) >= 2:
            # Extract column name (fallback to generated name if None)
            col_name = str(col_desc[0]) if col_desc[0] else f"unnamed_column_{i}"

            # Map database type code to Python type using scale for numeric precision
            # col_desc[1] = type_code, col_desc[5] = scale (if available)
            col_type = _map_db_type_to_python(col_desc[1], col_desc[5] if len(col_desc) > 5 else None, dialect)

            columns[col_name] = col_type

        # Format 2: Object with name and type_code attributes (some Oracle/MySQL drivers)
        elif hasattr(col_desc, "name") and hasattr(col_desc, "type_code"):
            # Extract name from object attribute
            col_name = str(col_desc.name) if col_desc.name else f"unnamed_column_{i}"  # type: ignore

            # Map type using object's type_code and scale attributes
            col_type = _map_db_type_to_python(
                col_desc.type_code,  # type: ignore
                col_desc.scale if hasattr(col_desc, "scale") else None,  # type: ignore
                dialect,
            )
            columns[col_name] = col_type

        # Format 3: Unknown format - fallback to string representation
        else:
            # Use string representation as column name (last resort)
            col_name = str(col_desc) if col_desc else f"unnamed_column_{i}"
            columns[col_name] = "unknown"

    return columns


def _infer_sqlite_column_types_from_query(query: str, connection: DatabaseConnection) -> Dict[str, type]:
    """
    Infer column types for SQLite using query parsing and schema inspection.

    SQLite's dynamic type system and cursor.description limitations make type
    inference unreliable. This function uses SQLGlot to parse the query, extract
    referenced tables, and query PRAGMA table_info to get actual column types.

    The function also handles:
    - Aliased columns and expressions
    - Computed columns (COUNT, SUM, etc.)
    - Multiple tables in joins

    Parameters
    ----------
    query : str
        SQL query string to analyze. Should be a valid SQLite SELECT statement.
    connection : DatabaseConnection
        Active SQLite database connection for PRAGMA queries.

    Returns
    -------
    Dict[str, type]
        Dictionary mapping column names (including aliases) to Python type classes.
        Returns empty dict if SQLGlot is not available or parsing fails.

    Raises
    ------
    No exceptions raised - errors are logged and empty dict is returned.

    Examples
    --------
    >>> conn = DatabaseConnection(dialect="sqlite", database="test.db")
    >>> query = "SELECT id, name, salary FROM employees WHERE salary > 50000"
    >>> columns = _infer_sqlite_column_types_from_query(query, conn)
    >>> print(columns)
    {'id': <class 'int'>, 'name': <class 'str'>, 'salary': <class 'float'>}
    >>>
    >>> # With aliases and computed columns
    >>> query = "SELECT COUNT(*) as total, AVG(salary) as avg_sal FROM employees"
    >>> columns = _infer_sqlite_column_types_from_query(query, conn)
    >>> print(columns)
    {'total': <class 'int'>, 'avg_sal': <class 'float'>}

    Notes
    -----
    - Requires SQLGlot to be installed for query parsing
    - Uses PRAGMA table_info() to get accurate type information from table schema
    - Falls back to expression type inference for computed columns
    - SQLite affinity rules: INT/INTEGER->int, REAL/FLOAT->float, TEXT/CHAR->str, BLOB->bytes
    - Returns empty dict if SQLGlot is unavailable (graceful degradation)

    See Also
    --------
    _infer_expression_type : Infer types for computed columns and expressions
    """
    columns = {}

    # Check if SQLGlot is available for parsing
    if not SQLGLOT_AVAILABLE or parse_one is None or exp is None:
        logger.warning("SQLGlot not available, cannot parse query for SQLite type inference")
        return columns

    try:
        # Parse SQL query into abstract syntax tree
        parsed = parse_one(query, dialect="sqlite")

        # Extract all table names referenced in the query
        tables = set()
        for table in parsed.find_all(exp.Table):
            tables.add(table.name)

        # Query schema for each table using PRAGMA table_info
        for table_name in tables:
            try:
                # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
                pragma_query = f"PRAGMA table_info({table_name})"
                pragma_result = connection.execute_query(pragma_query)

                if pragma_result:
                    for row in pragma_result:
                        col_name = row[1]  # Column name (index 1)
                        col_type = row[2].lower()  # Column type string (index 2)

                        # Map SQLite affinity types to Python types
                        # SQLite uses type affinity: any type name containing these keywords
                        if "int" in col_type:
                            columns[col_name] = int
                        elif "real" in col_type or "float" in col_type or "double" in col_type:
                            columns[col_name] = float
                        elif "text" in col_type or "char" in col_type or "clob" in col_type:
                            columns[col_name] = str
                        elif "blob" in col_type:
                            columns[col_name] = bytes
                        elif "bool" in col_type:
                            columns[col_name] = bool
                        elif "date" in col_type:
                            # Distinguish between DATE and DATETIME
                            if "time" in col_type:
                                columns[col_name] = datetime.datetime
                            else:
                                columns[col_name] = datetime.date
                        else:
                            # SQLite default: TEXT affinity for unknown types
                            columns[col_name] = str

            except Exception as e:
                # Log but don't fail - continue with other tables
                logger.debug(f"Could not get schema for table {table_name}: {e}")
                continue

        # Handle SELECT expressions (aliased columns, computed values, etc.)
        if hasattr(parsed, "expressions"):
            for expr in parsed.expressions:
                # Check for aliased expressions: SELECT col AS alias, COUNT(*) AS total
                if hasattr(expr, "alias") and expr.alias:
                    alias_name = expr.alias
                    # Only infer if not already found in table schema
                    if alias_name not in columns:
                        # Infer type from expression (COUNT->int, AVG->float, etc.)
                        columns[alias_name] = _infer_expression_type(expr)

    except Exception as e:
        # Log parsing errors but return what we have
        logger.debug(f"Error parsing query with SQLGlot: {e}")

    return columns


def _infer_expression_type(expr) -> type:
    """
    Infer Python type from a SQLGlot expression node.

    This function analyzes SQLGlot expression AST nodes to determine the
    appropriate Python type for computed columns, literals, and CAST operations.

    Handles:
    - Literal values (strings, numbers)
    - Aggregate functions (COUNT, SUM, AVG, MAX, MIN)
    - CAST expressions with target type inspection
    - Default fallback to str for unknown expressions

    Parameters
    ----------
    expr : sqlglot.expressions.Expression
        SQLGlot expression object from parsed query AST.

    Returns
    -------
    type
        Python type class inferred from the expression.
        Returns str as fallback for unknown or complex expressions.

    Examples
    --------
    >>> from sqlglot import parse_one, exp
    >>> # COUNT expression
    >>> query = parse_one("SELECT COUNT(*) FROM users")
    >>> count_expr = query.expressions[0]
    >>> _infer_expression_type(count_expr)
    <class 'int'>
    >>>
    >>> # AVG expression
    >>> query = parse_one("SELECT AVG(salary) FROM employees")
    >>> avg_expr = query.expressions[0]
    >>> _infer_expression_type(avg_expr)
    <class 'float'>
    >>>
    >>> # CAST expression
    >>> query = parse_one("SELECT CAST(id AS TEXT) FROM users")
    >>> cast_expr = query.expressions[0]
    >>> _infer_expression_type(cast_expr)
    <class 'str'>

    Notes
    -----
    - Requires SQLGlot to be available (returns str if not installed)
    - COUNT always returns int
    - SUM, AVG, MAX, MIN return float (may contain decimal results)
    - Literal number detection checks for decimal point
    - CAST target types use SQLite affinity rules
    """
    # Return str if SQLGlot not available
    if not SQLGLOT_AVAILABLE or exp is None:
        return str

    try:
        # Expression type 1: Literal values
        if isinstance(expr, exp.Literal):
            # String literal: 'hello', "world"
            if expr.is_string:
                return str
            # Numeric literal: 123, 45.67
            elif expr.is_number:
                # Check for decimal point to distinguish int from float
                return float if "." in str(expr) else int
            else:
                return str

        # Expression type 2: COUNT aggregation (always returns integer count)
        elif isinstance(expr, exp.Count):
            return int

        # Expression type 3: Numeric aggregations (may return decimals)
        elif isinstance(expr, (exp.Sum, exp.Avg, exp.Max, exp.Min)):
            return float

        # Expression type 4: CAST operations (check target type)
        elif isinstance(expr, exp.Cast):
            # Extract target type from CAST(expr AS target_type)
            target_type = str(expr.to).lower()

            # Map CAST target types to Python types using affinity rules
            if "int" in target_type:
                return int
            elif "float" in target_type or "real" in target_type:
                return float
            elif "text" in target_type or "char" in target_type:
                return str
            elif "date" in target_type:
                # Distinguish DATE from DATETIME
                return datetime.date if "time" not in target_type else datetime.datetime
            else:
                return str

        # Unknown expression type - default to string
        else:
            return str

    except Exception:
        # Exception during type inference - safe fallback to str
        return str


def _create_fallback_columns(data_rows: List[Any]) -> Dict[str, Any]:
    """
    Create generic column metadata when cursor description is unavailable.

    This function provides a fallback mechanism for creating column metadata
    when the database driver doesn't provide cursor.description or when the
    description is malformed. It generates generic column names based on the
    number of columns in the first data row.

    Parameters
    ----------
    data_rows : List[Any]
        List of data rows (each row is a sequence/tuple of values).
        Used to determine the number of columns.

    Returns
    -------
    Dict[str, Any]
        Dictionary mapping generated column names ('column_0', 'column_1', etc.)
        to the string 'unknown'. Returns empty dict if data_rows is empty.

    Examples
    --------
    >>> # Sample data rows
    >>> data = [(1, 'Alice', 50000), (2, 'Bob', 60000)]
    >>> columns = _create_fallback_columns(data)
    >>> print(columns)
    {'column_0': 'unknown', 'column_1': 'unknown', 'column_2': 'unknown'}
    >>>
    >>> # Empty data
    >>> columns = _create_fallback_columns([])
    >>> print(columns)
    {}

    Notes
    -----
    - Generated column names follow the pattern: 'column_0', 'column_1', 'column_2', etc.
    - All types are marked as 'unknown' since no type information is available
    - Only examines the first row to determine column count
    - Assumes all rows have the same number of columns
    - This is a last-resort fallback for rare driver edge cases
    """
    columns = {}

    # Check if we have any data to work with
    if data_rows and len(data_rows) > 0:
        # Use first row to determine column count
        first_row = data_rows[0]

        # Generate generic column names: column_0, column_1, column_2, ...
        for i in range(len(first_row)):
            columns[f"column_{i}"] = "unknown"

    return columns
