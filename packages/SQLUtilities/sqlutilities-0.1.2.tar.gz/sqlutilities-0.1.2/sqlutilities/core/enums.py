"""
Core SQL Enumerations.

This module contains the fundamental enumerations used across the SQL package
for standardizing database object types and SQL dialect configurations.

The module provides two main enumerations:
- DatabaseObjectType: Comprehensive enumeration of database object types
  across major SQL dialects (tables, views, indexes, constraints, etc.)
- SQLDialect: Supported SQL database dialects with complete identifier
  validation rules, quoting rules, and syntax support

These enumerations ensure consistent handling of database objects and
dialect-specific features throughout the SQL utilities package.

Author
------
DataScience ToolBox

Examples
--------
>>> from core.enums import DatabaseObjectType, SQLDialect
>>> obj_type = DatabaseObjectType.TABLE
>>> print(obj_type.description)
Data storage structure with rows and columns
>>> dialect = SQLDialect.POSTGRES
>>> print(dialect.quote_character)
"
"""

from enum import Enum

# Forward reference for type hints
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, cast

if TYPE_CHECKING:
    pass


class DatabaseObjectType(Enum):
    """
    Comprehensive enumeration of all database object types across major SQL dialects.

    This enum provides a standardized way to reference database objects across
    different database management systems (DBMS) including Oracle, PostgreSQL,
    SQL Server, MySQL, SQLite, BigQuery, and Redshift.

    Each enum member contains a tuple with:
    - name_value: String identifier for the database object type
    - description: Human-readable description of the object type

    The enum is organized into logical categories:
    - Core Data Objects: Tables, columns, views, materialized views
    - Schema Objects: Schemas, databases, catalogs
    - Index Objects: Various index types (unique, clustered, partial, etc.)
    - Constraint Objects: Primary keys, foreign keys, unique constraints, etc.
    - Sequence and Identity Objects: Auto-incrementing sequences
    - Stored Code Objects: Procedures, functions, triggers, packages
    - User-Defined Types: Custom types, domains, aggregates
    - Access Control Objects: Users, roles, privileges, grants
    - Specialized Objects: Partitions, tablespaces, synonyms, links
    - Cloud Data Warehouse Objects: Datasets, external tables, distribution keys
    - Temporal and System Objects: Temporal tables, system tables, temporary tables

    Attributes
    ----------
    name_value : str
        The string name of the database object type.
    description : str
        Human-readable description of the database object type.

    Examples
    --------
    >>> obj_type = DatabaseObjectType.TABLE
    >>> print(obj_type.value)
    ('table', 'Data storage structure with rows and columns')
    >>> print(obj_type.name_value)
    table
    >>> print(obj_type.description)
    Data storage structure with rows and columns
    >>> core_objects = DatabaseObjectType.get_core_objects()
    >>> len(core_objects)
    9
    """

    # Core Data Objects
    TABLE = ("table", "Data storage structure with rows and columns")
    COLUMN = ("column", "Individual data field within a table or view")
    VIEW = ("view", "Virtual table based on a SQL query")
    MATERIALIZED_VIEW = ("materialized_view", "Physical copy of view data stored on disk")

    # Schema Objects
    SCHEMA = ("schema", "Namespace container for database objects")
    DATABASE = ("database", "Top-level container for all database objects")
    CATALOG = ("catalog", "Collection of schemas (SQL standard term)")

    # Index Objects
    INDEX = ("index", "Data structure to improve query performance")
    UNIQUE_INDEX = ("unique_index", "Index that enforces uniqueness constraint")
    CLUSTERED_INDEX = ("clustered_index", "Index that determines physical storage order")
    NONCLUSTERED_INDEX = ("nonclustered_index", "Index that doesn't affect physical storage order")
    PARTIAL_INDEX = ("partial_index", "Index on subset of rows meeting a condition")
    FUNCTIONAL_INDEX = ("functional_index", "Index on computed expressions")

    # Constraint Objects
    CONSTRAINT = ("constraint", "Rule that enforces data integrity")
    PRIMARY_KEY = ("primary_key", "Constraint that uniquely identifies table rows")
    FOREIGN_KEY = ("foreign_key", "Constraint that references primary key in another table")
    UNIQUE_CONSTRAINT = ("unique_constraint", "Constraint that ensures column values are unique")
    CHECK_CONSTRAINT = ("check_constraint", "Constraint that validates column values against condition")
    NOT_NULL_CONSTRAINT = ("not_null_constraint", "Constraint that prevents NULL values")
    DEFAULT_CONSTRAINT = ("default_constraint", "Constraint that provides default column values")

    # Sequence and Identity Objects
    SEQUENCE = ("sequence", "Object that generates unique numeric values")
    IDENTITY = ("identity", "Auto-incrementing column property")
    GENERATOR = ("generator", "Firebird/InterBase sequence equivalent")

    # Stored Code Objects
    PROCEDURE = ("procedure", "Stored procedure that performs operations")
    FUNCTION = ("function", "Stored function that returns a value")
    TRIGGER = ("trigger", "Code that automatically executes on data changes")
    PACKAGE = ("package", "Collection of procedures and functions (Oracle)")

    # User-Defined Types
    TYPE = ("type", "User-defined data type")
    DOMAIN = ("domain", "Named data type with constraints")
    AGGREGATE = ("aggregate", "User-defined aggregate function")

    # Access Control Objects
    USER = ("user", "Database user account")
    ROLE = ("role", "Collection of privileges that can be granted")
    PRIVILEGE = ("privilege", "Permission to perform specific operations")
    GRANT = ("grant", "Assignment of privileges to users or roles")

    # Specialized Objects
    PARTITION = ("partition", "Subset of table data stored separately")
    TABLESPACE = ("tablespace", "Storage location for database objects")
    SYNONYM = ("synonym", "Alias for database object")
    LINK = ("link", "Connection to remote database")
    COMPUTED_COLUMN = ("computed_column", "Column with value calculated from other columns")
    VIRTUAL_COLUMN = ("virtual_column", "Column with value computed on-the-fly")

    # Advanced Objects
    CURSOR = ("cursor", "Pointer to query result set")
    COMMENT = ("comment", "Documentation attached to database objects")
    RULE = ("rule", "Query rewrite rule (PostgreSQL)")
    OPERATOR = ("operator", "User-defined operator")
    CAST = ("cast", "Data type conversion specification")

    # Cloud Data Warehouse Objects
    DATASET = ("dataset", "Collection of tables and views (BigQuery)")
    EXTERNAL_TABLE = ("external_table", "Table referencing external data source")
    DISTRIBUTION_KEY = ("distribution_key", "Column(s) used for data distribution (Redshift)")
    SORT_KEY = ("sort_key", "Column(s) used for data sorting (Redshift)")

    # Temporal and System Objects
    TEMPORAL_TABLE = ("temporal_table", "Table that tracks data changes over time")
    SYSTEM_TABLE = ("system_table", "Internal database metadata table")
    TEMPORARY_TABLE = ("temporary_table", "Table that exists only during session")

    @property
    def name_value(self) -> str:
        """
        Get the string name of the database object type.

        Returns
        -------
        str
            The lowercase string identifier for this database object type.

        Examples
        --------
        >>> DatabaseObjectType.TABLE.name_value
        'table'
        >>> DatabaseObjectType.PRIMARY_KEY.name_value
        'primary_key'
        """
        return self.value[0]

    @property
    def description(self) -> str:
        """
        Get the human-readable description of the database object type.

        Returns
        -------
        str
            A descriptive string explaining what this database object type represents.

        Examples
        --------
        >>> DatabaseObjectType.TABLE.description
        'Data storage structure with rows and columns'
        >>> DatabaseObjectType.INDEX.description
        'Data structure to improve query performance'
        """
        return self.value[1]

    def __str__(self) -> str:
        return self.name_value

    @classmethod
    def get_core_objects(cls) -> List["DatabaseObjectType"]:
        """
        Get the most commonly used database object types.

        Returns
        -------
        List[DatabaseObjectType]
            List containing TABLE, COLUMN, VIEW, INDEX, CONSTRAINT, SEQUENCE,
            PROCEDURE, FUNCTION, and TRIGGER object types.

        Examples
        --------
        >>> core_objs = DatabaseObjectType.get_core_objects()
        >>> DatabaseObjectType.TABLE in core_objs
        True
        >>> len(core_objs)
        9
        """
        return [
            cls.TABLE,
            cls.COLUMN,
            cls.VIEW,
            cls.INDEX,
            cls.CONSTRAINT,
            cls.SEQUENCE,
            cls.PROCEDURE,
            cls.FUNCTION,
            cls.TRIGGER,
        ]

    @classmethod
    def get_constraint_types(cls) -> List["DatabaseObjectType"]:
        """
        Get all constraint-related database object types.

        Returns
        -------
        List[DatabaseObjectType]
            List of all constraint types including primary keys, foreign keys,
            unique constraints, check constraints, not null constraints, and
            default constraints.

        Examples
        --------
        >>> constraint_types = DatabaseObjectType.get_constraint_types()
        >>> DatabaseObjectType.PRIMARY_KEY in constraint_types
        True
        >>> DatabaseObjectType.FOREIGN_KEY in constraint_types
        True
        """
        return [
            cls.CONSTRAINT,
            cls.PRIMARY_KEY,
            cls.FOREIGN_KEY,
            cls.UNIQUE_CONSTRAINT,
            cls.CHECK_CONSTRAINT,
            cls.NOT_NULL_CONSTRAINT,
            cls.DEFAULT_CONSTRAINT,
        ]

    @classmethod
    def get_index_types(cls) -> List["DatabaseObjectType"]:
        """
        Get all index-related database object types.

        Returns
        -------
        List[DatabaseObjectType]
            List of all index types including standard indexes, unique indexes,
            clustered indexes, nonclustered indexes, partial indexes, and
            functional indexes.

        Examples
        --------
        >>> index_types = DatabaseObjectType.get_index_types()
        >>> DatabaseObjectType.INDEX in index_types
        True
        >>> DatabaseObjectType.CLUSTERED_INDEX in index_types
        True
        """
        return [
            cls.INDEX,
            cls.UNIQUE_INDEX,
            cls.CLUSTERED_INDEX,
            cls.NONCLUSTERED_INDEX,
            cls.PARTIAL_INDEX,
            cls.FUNCTIONAL_INDEX,
        ]

    @classmethod
    def get_stored_code_types(cls) -> List["DatabaseObjectType"]:
        """
        Get all stored code database object types.

        Returns
        -------
        List[DatabaseObjectType]
            List of stored code types including procedures, functions, triggers,
            and packages.

        Examples
        --------
        >>> code_types = DatabaseObjectType.get_stored_code_types()
        >>> DatabaseObjectType.PROCEDURE in code_types
        True
        >>> DatabaseObjectType.TRIGGER in code_types
        True
        """
        return [cls.PROCEDURE, cls.FUNCTION, cls.TRIGGER, cls.PACKAGE]

    @classmethod
    def get_access_control_types(cls) -> List["DatabaseObjectType"]:
        """
        Get all access control database object types.

        Returns
        -------
        List[DatabaseObjectType]
            List of access control types including users, roles, privileges,
            and grants.

        Examples
        --------
        >>> access_types = DatabaseObjectType.get_access_control_types()
        >>> DatabaseObjectType.USER in access_types
        True
        >>> DatabaseObjectType.ROLE in access_types
        True
        """
        return [cls.USER, cls.ROLE, cls.PRIVILEGE, cls.GRANT]

    @classmethod
    def get_column_related_types(cls) -> List["DatabaseObjectType"]:
        """
        Get all column-related database object types.

        Returns
        -------
        List[DatabaseObjectType]
            List of column types including regular columns, computed columns,
            virtual columns, and identity columns.

        Examples
        --------
        >>> column_types = DatabaseObjectType.get_column_related_types()
        >>> DatabaseObjectType.COLUMN in column_types
        True
        >>> DatabaseObjectType.COMPUTED_COLUMN in column_types
        True
        """
        return [cls.COLUMN, cls.COMPUTED_COLUMN, cls.VIRTUAL_COLUMN, cls.IDENTITY]

    @classmethod
    def get_cloud_warehouse_types(cls) -> List["DatabaseObjectType"]:
        """
        Get cloud data warehouse specific database object types.

        Returns
        -------
        List[DatabaseObjectType]
            List of cloud warehouse types including datasets, external tables,
            distribution keys, and sort keys.

        Examples
        --------
        >>> cloud_types = DatabaseObjectType.get_cloud_warehouse_types()
        >>> DatabaseObjectType.DATASET in cloud_types
        True
        >>> DatabaseObjectType.EXTERNAL_TABLE in cloud_types
        True
        """
        return [cls.DATASET, cls.EXTERNAL_TABLE, cls.DISTRIBUTION_KEY, cls.SORT_KEY]


class SQLDialect(Enum):
    """
    Enumeration of supported SQL database dialects with comprehensive identifier rules.

    This enum standardizes dialect names used throughout the SQL utilities and
    provides complete identifier validation rules, quoting conventions, and
    syntax support for each supported database dialect.

    Each dialect enum member contains a tuple with:
    - name_value: String identifier for the dialect (e.g., 'postgres', 'oracle')
    - description: Human-readable description of the database system
    - identifier_rules: Complete dictionary of identifier validation rules including:
        * max_length: Maximum identifier length
        * case_sensitive: Whether identifiers are case-sensitive
        * case_conversion: Default case conversion ('upper', 'lower', or None)
        * delimiter: Quote character(s) for identifiers
        * allowed_chars: Regular expressions for valid identifier characters
        * first_char_rules: Regular expression for valid first character
        * reserved_prefixes: Set of reserved identifier prefixes
        * quoted_identifiers: Whether quoted identifiers are supported
        * if_exists: List of object types supporting IF EXISTS clause
        * if_not_exists: List of object types supporting IF NOT EXISTS clause
        * parameter_format_preference: Preferred parameter format ('tuple' or 'dict')
        * parameter_style_preference: Preferred parameter style ('qmark', 'format', etc.)
    - sql_alchemy_dialect: SQLAlchemy dialect name for compatibility

    Supported Dialects
    ------------------
    - ORACLE: Oracle Database (11g and later)
    - POSTGRES/POSTGRESQL: PostgreSQL (aliases for the same dialect)
    - SQLSERVER/MSSQL: Microsoft SQL Server (aliases for the same dialect)
    - MYSQL: MySQL and MariaDB
    - SQLITE: SQLite embedded database
    - BIGQUERY: Google BigQuery cloud data warehouse
    - REDSHIFT: Amazon Redshift cloud data warehouse

    Attributes
    ----------
    name_value : str
        The string identifier for this SQL dialect.
    description : str
        Human-readable description of the database system.
    identifier_rules : Dict[str, Any]
        Complete dictionary of identifier validation and quoting rules.
    sql_alchemy_dialect : str
        SQLAlchemy dialect name for ORM compatibility.

    Examples
    --------
    >>> dialect = SQLDialect.POSTGRES
    >>> print(dialect.name_value)
    postgres
    >>> print(dialect.quote_character)
    "
    >>> dialect.supports_if_exists(DatabaseObjectType.TABLE)
    True
    >>> dialect.parameter_format_preference
    'tuple'
    """

    ORACLE = (
        "oracle",
        "Oracle Database",
        {
            "max_length": 128,
            "case_sensitive": False,  # Oracle converts to uppercase unless quoted
            "case_conversion": "upper",
            "delimiter": '"',
            "allowed_chars": {"raw": r"^[A-Za-z][A-Za-z0-9_\$#]*$", "encapsulated": [r'^(?:(?:"")|[^"])*$']},
            "first_char_rules": r"^[A-Za-z]",  # Must be letter
            "reserved_prefixes": {"SYS_", "ORA$", "X$"},
            "quoted_identifiers": True,
            "if_exists": [],
            "if_not_exists": [],
            "quoted_case_sensitive": True,
            "parameter_format_preference": "tuple",  # Oracle strongly prefers tuple format for parameters
            "parameter_style_preference": "numeric",  # Oracle uses numeric style (:1, :2, :3), compatible with tuples
            "special_rules": {},
        },
        "oracle",
    )

    # Define PostgreSQL configuration once (canonical).
    # This configuration is shared between POSTGRES and POSTGRESQL enum members.
    _POSTGRES_CONFIG = {
        "max_length": 63,  # PostgreSQL truncates identifiers longer than 63 characters.
        "case_sensitive": True,  # PostgreSQL is case-sensitive when quoted.
        "case_conversion": "lower",  # Unquoted identifiers are converted to lowercase.
        "delimiter": '"',  # Double quotes are used for quoted identifiers.
        "allowed_chars": {
            "raw": r"^[A-Za-z_][A-Za-z0-9_]*$",  # Unquoted: letter/underscore then alphanumeric/underscore.
            "encapsulated": [r'^(?:(?:"")|[^"])*$'],  # Quoted: any char except unescaped quote.
        },
        "first_char_rules": r"^[A-Za-z_]",  # Must start with letter or underscore.
        "reserved_prefixes": {"pg_", "sql_"},  # System-reserved identifier prefixes.
        "quoted_identifiers": True,  # Quoted identifiers are supported.
        "if_exists": [
            DatabaseObjectType.DATABASE,
            DatabaseObjectType.SCHEMA,
            DatabaseObjectType.TABLE,
            DatabaseObjectType.VIEW,
            DatabaseObjectType.INDEX,
            DatabaseObjectType.FUNCTION,
            DatabaseObjectType.PROCEDURE,
            DatabaseObjectType.SEQUENCE,
        ],
        "if_not_exists": [
            DatabaseObjectType.DATABASE,
            DatabaseObjectType.SCHEMA,
            DatabaseObjectType.TABLE,
            DatabaseObjectType.VIEW,
            DatabaseObjectType.INDEX,
            DatabaseObjectType.FUNCTION,
            DatabaseObjectType.PROCEDURE,
            DatabaseObjectType.SEQUENCE,
        ],
        "quoted_case_sensitive": True,  # Quoted identifiers preserve case.
        "parameter_format_preference": "tuple",  # psycopg2 works better with tuples for executemany.
        "parameter_style_preference": "format",  # PostgreSQL uses format style (%s).
        "special_rules": {},
    }

    POSTGRES = ("postgres", "PostgreSQL", _POSTGRES_CONFIG, "postgresql")
    POSTGRESQL = ("postgres", "PostgreSQL", _POSTGRES_CONFIG, "postgresql")  # Alias for POSTGRES

    # Define SQL Server configuration once (canonical)
    _SQLSERVER_CONFIG = {
        "max_length": 128,
        "case_sensitive": False,  # Depends on collation, but typically case-insensitive
        "case_conversion": None,  # Preserves original case
        "delimiter": ['"', "]"],
        "allowed_chars": {
            "raw": r"^[A-Za-z_@#][A-Za-z0-9_@\$#]*$",
            "encapsulated": [r'^(?:(?:"")|[^"])*$', r"^(?:\]\]|[^\]])*$"],
        },
        "first_char_rules": r"^[A-Za-z_@#]",  # Letter, underscore, at-sign, or hash
        "reserved_prefixes": {"sys", "INFORMATION_SCHEMA"},
        "quoted_identifiers": True,
        "if_exists": [DatabaseObjectType.TABLE, DatabaseObjectType.INDEX],
        "if_not_exists": [],
        "quoted_case_sensitive": True,
        "parameter_format_preference": "tuple",  # SQL Server pyodbc driver requires tuple/list format for executemany
        "parameter_style_preference": "qmark",  # SQL Server with pyodbc uses qmark style (?), compatible with tuples
        "special_rules": {},
    }

    SQLSERVER = ("sqlserver", "Microsoft SQL Server", _SQLSERVER_CONFIG, "mssql")
    MSSQL = ("sqlserver", "Microsoft SQL Server", _SQLSERVER_CONFIG, "mssql")  # Alias for SQLSERVER

    MYSQL = (
        "mysql",
        "MySQL",
        {
            "max_length": 64,
            "case_sensitive": False,  # MySQL is generally case-insensitive for identifiers
            "case_conversion": None,
            "delimiter": "`",
            "allowed_chars": {"raw": r"^[A-Za-z_][A-Za-z0-9_\$]*$", "encapsulated": [r"^(?:``|[^`])*$"]},
            "first_char_rules": r"^[A-Za-z_]",  # Letter or underscore (dollar not allowed as first char)
            "reserved_prefixes": {"mysql_", "performance_schema", "information_schema"},
            "quoted_identifiers": True,
            "if_exists": [
                DatabaseObjectType.TABLE,
                DatabaseObjectType.VIEW,
                DatabaseObjectType.INDEX,
                DatabaseObjectType.FUNCTION,
                DatabaseObjectType.PROCEDURE,
                DatabaseObjectType.TRIGGER,
                DatabaseObjectType.DATABASE,
            ],
            "if_not_exists": [
                DatabaseObjectType.TABLE,
                DatabaseObjectType.VIEW,
                DatabaseObjectType.INDEX,
                DatabaseObjectType.DATABASE,
                DatabaseObjectType.TRIGGER,
            ],
            "quoted_case_sensitive": True,
            "parameter_format_preference": "dict",  # MySQL typically uses dict format with MySQLdb/PyMySQL
            "parameter_style_preference": "pyformat",  # MySQL with MySQLdb/PyMySQL uses pyformat style (%(name)s), compatible with dicts
            "special_rules": {},
        },
        "mysql",
    )

    SQLITE = (
        "sqlite",
        "SQLite",
        {
            "max_length": None,  # No hard limit
            "case_sensitive": False,
            "case_conversion": None,  # Preserves case but comparisons are case-insensitive
            "delimiter": ['"', "'", "]"],
            "allowed_chars": {
                "raw": r"^.+$",  # any non-empty string
                "encapsulated": [r'^(?:(?:"")|[^"])*$', r"^(?:''|[^'])*$", r"^(?:\]\]|[^\]])*$"],
            },
            "first_char_rules": r"^.",  # Any character (very permissive)
            "reserved_prefixes": {"sqlite_"},
            "quoted_identifiers": True,
            "if_exists": [
                DatabaseObjectType.TABLE,
                DatabaseObjectType.VIEW,
                DatabaseObjectType.INDEX,
                DatabaseObjectType.TRIGGER,
            ],
            "if_not_exists": [
                DatabaseObjectType.TABLE,
                DatabaseObjectType.VIEW,
                DatabaseObjectType.INDEX,
                DatabaseObjectType.TRIGGER,
            ],
            "quoted_case_sensitive": False,
            "parameter_format_preference": "tuple",  # SQLite strongly prefers tuple format for parameters
            "parameter_style_preference": "qmark",  # SQLite uses qmark style (?), compatible with tuples
            "special_rules": {},
        },
        "sqlite",
    )

    BIGQUERY = (
        "bigquery",
        "Google BigQuery",
        {
            "max_length": 1024,
            "case_sensitive": False,
            "case_conversion": None,
            "delimiter": "`",
            "allowed_chars": {"raw": r"^[A-Za-z_][A-Za-z0-9_]*$", "encapsulated": [r"^(?:``|[^`])*$"]},
            "first_char_rules": r"^[A-Za-z_]",  # Letter or underscore
            "reserved_prefixes": {"_TABLE_", "_FILE_", "_PARTITION"},
            "quoted_identifiers": True,
            "if_exists": [
                DatabaseObjectType.TABLE,
                DatabaseObjectType.VIEW,
                DatabaseObjectType.SCHEMA,
                DatabaseObjectType.COLUMN,
            ],
            "if_not_exists": [
                DatabaseObjectType.TABLE,
                DatabaseObjectType.VIEW,
                DatabaseObjectType.SCHEMA,
                DatabaseObjectType.COLUMN,
            ],
            "quoted_case_sensitive": False,
            "parameter_format_preference": "dict",  # BigQuery typically uses dict format for parameters
            "parameter_style_preference": "pyformat",  # BigQuery uses pyformat style (%(name)s), compatible with dicts
            "special_rules": {DatabaseObjectType.COLUMN: {"max_length": 300}},
        },
        "bigquery",
    )

    REDSHIFT = (
        "redshift",
        "Amazon Redshift",
        {
            "max_length": 127,
            "case_sensitive": False,
            "case_conversion": "lower",
            "delimiter": '"',
            "allowed_chars": {"raw": r"^[A-Za-z_][A-Za-z0-9_]*$", "encapsulated": [r'^(?:(?:"")|[^"])*$']},
            "first_char_rules": r"^[A-Za-z_]",  # Letter or underscore
            "reserved_prefixes": set(),
            "quoted_identifiers": True,
            "if_exists": [DatabaseObjectType.TABLE, DatabaseObjectType.VIEW],
            "if_not_exists": [DatabaseObjectType.TABLE, DatabaseObjectType.VIEW],
            "quoted_case_sensitive": True,
            "parameter_format_preference": "tuple",  # Redshift (PostgreSQL-based) prefers tuple format
            "parameter_style_preference": "format",  # Redshift uses format style (%s), compatible with tuples
            "special_rules": {},
        },
        "redshift",
    )

    @property
    def name_value(self) -> str:
        """
        Get the string identifier for this SQL dialect.

        Returns
        -------
        str
            The lowercase string identifier for this dialect (e.g., 'postgres', 'oracle').

        Examples
        --------
        >>> SQLDialect.POSTGRES.name_value
        'postgres'
        >>> SQLDialect.ORACLE.name_value
        'oracle'
        """
        return cast(Tuple[str, str, Dict[str, Any], str], self.value)[0]

    @property
    def description(self) -> str:
        """
        Get the human-readable description of this SQL dialect.

        Returns
        -------
        str
            A descriptive string identifying the database system.

        Examples
        --------
        >>> SQLDialect.POSTGRES.description
        'PostgreSQL'
        >>> SQLDialect.SQLSERVER.description
        'Microsoft SQL Server'
        """
        return cast(Tuple[str, str, Dict[str, Any], str], self.value)[1]

    @property
    def identifier_rules(self) -> Dict[str, Any]:
        """
        Get the complete identifier rules dictionary for this SQL dialect.

        The identifier rules include validation rules, quoting rules, case
        sensitivity, parameter preferences, and syntax support.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing all identifier validation and formatting rules
            including max_length, case_sensitive, delimiter, allowed_chars,
            parameter preferences, and special rules.

        Examples
        --------
        >>> rules = SQLDialect.POSTGRES.identifier_rules
        >>> rules['max_length']
        63
        >>> rules['delimiter']
        '"'
        """
        return cast(Tuple[str, str, Dict[str, Any], str], self.value)[2]

    @property
    def parameter_format_preference(self) -> str:
        """
        Get the preferred parameter format for this SQL dialect.

        Different database drivers handle parameters differently. This property
        indicates whether the driver works best with tuple/list positional
        parameters or dictionary named parameters.

        Returns
        -------
        str
            'tuple' for dialects preferring positional parameters
            (Oracle, PostgreSQL, SQLite, Redshift, SQL Server).
            'dict' for dialects preferring named parameters
            (MySQL, BigQuery).

        Examples
        --------
        >>> SQLDialect.POSTGRES.parameter_format_preference
        'tuple'
        >>> SQLDialect.MYSQL.parameter_format_preference
        'dict'
        """
        return self.identifier_rules.get("parameter_format_preference", "tuple")

    @property
    def parameter_style_preference(self) -> str:
        """
        Get the preferred parameter style for this SQL dialect.

        The parameter style determines the placeholder syntax used in SQL
        statements. Common styles include qmark (?), format (%s), numeric (:1),
        named (:name), and pyformat (%(name)s).

        Returns
        -------
        str
            The parameter style string that works best with this dialect's
            parameter format preference. Possible values:
            - 'qmark': Question mark style (?)
            - 'format': printf-style format (%s)
            - 'numeric': Numeric positional style (:1, :2, :3)
            - 'named': Named style (:name)
            - 'pyformat': Python extended format (%(name)s)

        Examples
        --------
        >>> SQLDialect.POSTGRES.parameter_style_preference
        'format'
        >>> SQLDialect.ORACLE.parameter_style_preference
        'numeric'
        >>> SQLDialect.SQLITE.parameter_style_preference
        'qmark'
        """
        return self.identifier_rules.get("parameter_style_preference", "format")

    @property
    def sql_alchemy_dialect(self) -> str:
        """
        Get the SQLAlchemy dialect name for this SQL dialect.

        This property provides the dialect name used by SQLAlchemy ORM and Core
        for compatibility with SQLAlchemy-based tools and applications.

        Returns
        -------
        str
            The SQLAlchemy dialect identifier string.

        Examples
        --------
        >>> SQLDialect.POSTGRES.sql_alchemy_dialect
        'postgresql'
        >>> SQLDialect.SQLSERVER.sql_alchemy_dialect
        'mssql'
        >>> SQLDialect.ORACLE.sql_alchemy_dialect
        'oracle'
        """
        return cast(Tuple[str, str, Dict[str, Any], str], self.value)[3]

    def __str__(self) -> str:
        return self.name_value

    @property
    def resolved_alias(self) -> "SQLDialect":
        """
        Get the resolved dialect, handling aliases.

        Since POSTGRESQL and POSTGRES share the same configuration (and name_value),
        as do MSSQL and SQLSERVER, they are already effectively the same.
        This property exists for backward compatibility and returns self.

        Returns
        -------
        SQLDialect
            The same dialect enum member (self).

        Examples
        --------
        >>> SQLDialect.POSTGRESQL.resolved_alias == SQLDialect.POSTGRESQL
        True
        >>> SQLDialect.POSTGRES.resolved_alias == SQLDialect.POSTGRES
        True
        """
        return self

    def get_identifier_rule(self, rule_name: str, default: Any = None) -> Any:
        """
        Get a specific identifier rule value for this dialect.

        Parameters
        ----------
        rule_name : str
            Name of the identifier rule to retrieve (e.g., 'max_length',
            'case_sensitive', 'delimiter').
        default : Any, optional
            Default value to return if the rule is not found. Default is None.

        Returns
        -------
        Any
            The value of the specified rule, or the default value if not found.

        Examples
        --------
        >>> SQLDialect.POSTGRES.get_identifier_rule('max_length')
        63
        >>> SQLDialect.ORACLE.get_identifier_rule('case_conversion')
        'upper'
        >>> SQLDialect.MYSQL.get_identifier_rule('nonexistent', 'default_value')
        'default_value'
        """
        return self.identifier_rules.get(rule_name, default)

    def supports_if_exists(self, object_type: DatabaseObjectType) -> bool:
        """
        Check if this dialect supports the IF EXISTS clause for an object type.

        The IF EXISTS clause is used in DROP statements to prevent errors when
        attempting to drop objects that don't exist.

        Parameters
        ----------
        object_type : DatabaseObjectType
            The database object type to check for IF EXISTS support.

        Returns
        -------
        bool
            True if IF EXISTS is supported for the specified object type,
            False otherwise.

        Examples
        --------
        >>> SQLDialect.POSTGRES.supports_if_exists(DatabaseObjectType.TABLE)
        True
        >>> SQLDialect.ORACLE.supports_if_exists(DatabaseObjectType.TABLE)
        False
        """
        return object_type in self.identifier_rules.get("if_exists", [])

    def supports_if_not_exists(self, object_type: DatabaseObjectType) -> bool:
        """
        Check if this dialect supports the IF NOT EXISTS clause for an object type.

        The IF NOT EXISTS clause is used in CREATE statements to prevent errors
        when attempting to create objects that already exist.

        Parameters
        ----------
        object_type : DatabaseObjectType
            The database object type to check for IF NOT EXISTS support.

        Returns
        -------
        bool
            True if IF NOT EXISTS is supported for the specified object type,
            False otherwise.

        Examples
        --------
        >>> SQLDialect.POSTGRES.supports_if_not_exists(DatabaseObjectType.TABLE)
        True
        >>> SQLDialect.SQLSERVER.supports_if_not_exists(DatabaseObjectType.TABLE)
        False
        """
        return object_type in self.identifier_rules.get("if_not_exists", [])

    @property
    def quote_character(self) -> str:
        """
        Get the primary quote character for identifiers in this dialect.

        Some dialects support multiple quote characters (e.g., SQL Server
        supports both " and []). This property returns the primary (preferred)
        quote character.

        Returns
        -------
        str
            The primary quote character (e.g., '"', '`', '[').

        Examples
        --------
        >>> SQLDialect.POSTGRES.quote_character
        '"'
        >>> SQLDialect.MYSQL.quote_character
        '`'
        >>> SQLDialect.SQLSERVER.quote_character
        '"'
        """
        delimiter = self.identifier_rules.get("delimiter", '"')
        # Return the first delimiter if multiple are supported.
        if isinstance(delimiter, list):
            return delimiter[0]
        return delimiter

    def is_quoted_identifier(self, identifier: str) -> bool:
        """
        Check if the given identifier is a quoted identifier in this dialect.

        Quoted identifiers are enclosed in quote characters specific to the
        dialect (e.g., double quotes, backticks, or square brackets).

        Parameters
        ----------
        identifier : str
            The identifier string to check.

        Returns
        -------
        bool
            True if the identifier is quoted, False otherwise.

        Examples
        --------
        >>> SQLDialect.POSTGRES.is_quoted_identifier('"my_table"')
        True
        >>> SQLDialect.POSTGRES.is_quoted_identifier('my_table')
        False
        >>> SQLDialect.MYSQL.is_quoted_identifier('`my_table`')
        True
        """
        # Check each supported delimiter for this dialect.
        for quote_char in self.identifier_rules.get("delimiter", []):
            if identifier.startswith(quote_char) and identifier.endswith(quote_char):
                return True
        return False

    @property
    def is_case_sensitive(self) -> bool:
        """
        Check if this dialect is case-sensitive for identifiers.

        Case sensitivity determines whether 'Table', 'TABLE', and 'table'
        are treated as the same identifier or different identifiers.

        Returns
        -------
        bool
            True if the dialect is case-sensitive for identifiers,
            False otherwise.

        Examples
        --------
        >>> SQLDialect.POSTGRES.is_case_sensitive
        True
        >>> SQLDialect.ORACLE.is_case_sensitive
        False
        >>> SQLDialect.MYSQL.is_case_sensitive
        False
        """
        return self.identifier_rules.get("case_sensitive", False)

    @property
    def case_conversion(self) -> Optional[str]:
        """
        Get the case conversion rule for unquoted identifiers in this dialect.

        Some dialects automatically convert unquoted identifiers to a specific
        case. For example, Oracle converts to uppercase, PostgreSQL converts
        to lowercase.

        Returns
        -------
        Optional[str]
            'upper' if identifiers are converted to uppercase,
            'lower' if identifiers are converted to lowercase,
            None if no automatic case conversion is performed.

        Examples
        --------
        >>> SQLDialect.ORACLE.case_conversion
        'upper'
        >>> SQLDialect.POSTGRES.case_conversion
        'lower'
        >>> SQLDialect.MYSQL.case_conversion
        None
        """
        return self.identifier_rules.get("case_conversion")
