"""
SQL Identifier Validation

This module provides identifier validation and normalization across SQL dialects.
- SQL_DIALECT_REGISTRY: Main registry for identifier validation rules and reserved words

Author: DataScience ToolBox
"""

import re
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Set, Union

from unidecode import unidecode

# Use try/except to handle both absolute and relative imports
try:
    from core.enums import DatabaseObjectType, SQLDialect
except ImportError:
    from ..core.enums import DatabaseObjectType, SQLDialect

# Avoid circular import - lazy import COLUMNDTYPE when needed
if TYPE_CHECKING:
    from ..core.types import COLUMNDTYPE

from CoreUtilities import LogLevel, camel_to_snake_case, get_logger

# Configure logging
logger = get_logger("sql_identifiers", level=LogLevel.WARNING, include_performance=True, include_emoji=True)


class SQL_DIALECT_REGISTRY:
    """
    Static registry for SQL dialect-specific information including reserved words,
    database objects, drivers, and identifier validation rules.
    """

    # Database objects supported by each dialect
    _DIALECT_OBJECTS: Dict[SQLDialect, Set[DatabaseObjectType]] = {
        SQLDialect.ORACLE: {
            DatabaseObjectType.TABLE,
            DatabaseObjectType.COLUMN,
            DatabaseObjectType.VIEW,
            DatabaseObjectType.MATERIALIZED_VIEW,
            DatabaseObjectType.SCHEMA,
            DatabaseObjectType.INDEX,
            DatabaseObjectType.UNIQUE_INDEX,
            DatabaseObjectType.CONSTRAINT,
            DatabaseObjectType.PRIMARY_KEY,
            DatabaseObjectType.FOREIGN_KEY,
            DatabaseObjectType.UNIQUE_CONSTRAINT,
            DatabaseObjectType.CHECK_CONSTRAINT,
            DatabaseObjectType.SEQUENCE,
            DatabaseObjectType.PROCEDURE,
            DatabaseObjectType.FUNCTION,
            DatabaseObjectType.TRIGGER,
            DatabaseObjectType.PACKAGE,
            DatabaseObjectType.TYPE,
            DatabaseObjectType.USER,
            DatabaseObjectType.ROLE,
            DatabaseObjectType.TABLESPACE,
            DatabaseObjectType.SYNONYM,
            DatabaseObjectType.VIRTUAL_COLUMN,
        },
        SQLDialect.POSTGRES: {
            DatabaseObjectType.TABLE,
            DatabaseObjectType.COLUMN,
            DatabaseObjectType.VIEW,
            DatabaseObjectType.MATERIALIZED_VIEW,
            DatabaseObjectType.SCHEMA,
            DatabaseObjectType.INDEX,
            DatabaseObjectType.UNIQUE_INDEX,
            DatabaseObjectType.PARTIAL_INDEX,
            DatabaseObjectType.FUNCTIONAL_INDEX,
            DatabaseObjectType.CONSTRAINT,
            DatabaseObjectType.PRIMARY_KEY,
            DatabaseObjectType.FOREIGN_KEY,
            DatabaseObjectType.UNIQUE_CONSTRAINT,
            DatabaseObjectType.CHECK_CONSTRAINT,
            DatabaseObjectType.SEQUENCE,
            DatabaseObjectType.PROCEDURE,
            DatabaseObjectType.FUNCTION,
            DatabaseObjectType.TRIGGER,
            DatabaseObjectType.TYPE,
            DatabaseObjectType.DOMAIN,
            DatabaseObjectType.AGGREGATE,
            DatabaseObjectType.USER,
            DatabaseObjectType.ROLE,
            DatabaseObjectType.RULE,
            DatabaseObjectType.OPERATOR,
            DatabaseObjectType.CAST,
        },
        SQLDialect.SQLSERVER: {
            DatabaseObjectType.TABLE,
            DatabaseObjectType.COLUMN,
            DatabaseObjectType.VIEW,
            DatabaseObjectType.SCHEMA,
            DatabaseObjectType.INDEX,
            DatabaseObjectType.UNIQUE_INDEX,
            DatabaseObjectType.CLUSTERED_INDEX,
            DatabaseObjectType.NONCLUSTERED_INDEX,
            DatabaseObjectType.CONSTRAINT,
            DatabaseObjectType.PRIMARY_KEY,
            DatabaseObjectType.FOREIGN_KEY,
            DatabaseObjectType.UNIQUE_CONSTRAINT,
            DatabaseObjectType.CHECK_CONSTRAINT,
            DatabaseObjectType.DEFAULT_CONSTRAINT,
            DatabaseObjectType.IDENTITY,
            DatabaseObjectType.PROCEDURE,
            DatabaseObjectType.FUNCTION,
            DatabaseObjectType.TRIGGER,
            DatabaseObjectType.TYPE,
            DatabaseObjectType.USER,
            DatabaseObjectType.ROLE,
            DatabaseObjectType.PARTITION,
            DatabaseObjectType.TEMPORAL_TABLE,
            DatabaseObjectType.COMPUTED_COLUMN,
        },
        SQLDialect.MYSQL: {
            DatabaseObjectType.TABLE,
            DatabaseObjectType.COLUMN,
            DatabaseObjectType.VIEW,
            DatabaseObjectType.DATABASE,
            DatabaseObjectType.INDEX,
            DatabaseObjectType.UNIQUE_INDEX,
            DatabaseObjectType.CONSTRAINT,
            DatabaseObjectType.PRIMARY_KEY,
            DatabaseObjectType.FOREIGN_KEY,
            DatabaseObjectType.UNIQUE_CONSTRAINT,
            DatabaseObjectType.CHECK_CONSTRAINT,
            DatabaseObjectType.PROCEDURE,
            DatabaseObjectType.FUNCTION,
            DatabaseObjectType.TRIGGER,
            DatabaseObjectType.USER,
            DatabaseObjectType.ROLE,
            DatabaseObjectType.TEMPORARY_TABLE,
            DatabaseObjectType.VIRTUAL_COLUMN,
        },
        SQLDialect.SQLITE: {
            DatabaseObjectType.TABLE,
            DatabaseObjectType.COLUMN,
            DatabaseObjectType.VIEW,
            DatabaseObjectType.INDEX,
            DatabaseObjectType.UNIQUE_INDEX,
            DatabaseObjectType.TRIGGER,
            DatabaseObjectType.TEMPORARY_TABLE,
            DatabaseObjectType.SYSTEM_TABLE,
        },
        SQLDialect.BIGQUERY: {
            DatabaseObjectType.TABLE,
            DatabaseObjectType.COLUMN,
            DatabaseObjectType.VIEW,
            DatabaseObjectType.MATERIALIZED_VIEW,
            DatabaseObjectType.SCHEMA,
            DatabaseObjectType.DATABASE,
            DatabaseObjectType.FUNCTION,
            DatabaseObjectType.PROCEDURE,
            DatabaseObjectType.TYPE,
            DatabaseObjectType.USER,
            DatabaseObjectType.ROLE,
            DatabaseObjectType.PARTITION,
            DatabaseObjectType.CONSTRAINT,
            DatabaseObjectType.PRIMARY_KEY,
            DatabaseObjectType.FOREIGN_KEY,
            DatabaseObjectType.TEMPORARY_TABLE,
            DatabaseObjectType.COMMENT,
            DatabaseObjectType.DATASET,
            DatabaseObjectType.EXTERNAL_TABLE,
        },
        SQLDialect.REDSHIFT: {
            DatabaseObjectType.TABLE,
            DatabaseObjectType.COLUMN,
            DatabaseObjectType.VIEW,
            DatabaseObjectType.MATERIALIZED_VIEW,
            DatabaseObjectType.SCHEMA,
            DatabaseObjectType.DATABASE,
            DatabaseObjectType.INDEX,
            DatabaseObjectType.CONSTRAINT,
            DatabaseObjectType.PRIMARY_KEY,
            DatabaseObjectType.FOREIGN_KEY,
            DatabaseObjectType.UNIQUE_CONSTRAINT,
            DatabaseObjectType.CHECK_CONSTRAINT,
            DatabaseObjectType.NOT_NULL_CONSTRAINT,
            DatabaseObjectType.FUNCTION,
            DatabaseObjectType.PROCEDURE,
            DatabaseObjectType.USER,
            DatabaseObjectType.ROLE,
            DatabaseObjectType.TEMPORARY_TABLE,
            DatabaseObjectType.COMMENT,
            DatabaseObjectType.TYPE,
            DatabaseObjectType.EXTERNAL_TABLE,
            DatabaseObjectType.DISTRIBUTION_KEY,
            DatabaseObjectType.SORT_KEY,
        },
    }
    # Common SQL Standard Reserved Words (shared across most dialects)
    _COMMON_RESERVED_WORDS: Set[str] = {
        "SELECT",
        "FROM",
        "WHERE",
        "INSERT",
        "UPDATE",
        "DELETE",
        "CREATE",
        "DROP",
        "ALTER",
        "TABLE",
        "VIEW",
        "INDEX",
        "DATABASE",
        "SCHEMA",
        "COLUMN",
        "PRIMARY",
        "KEY",
        "FOREIGN",
        "UNIQUE",
        "NOT",
        "NULL",
        "DEFAULT",
        "CHECK",
        "CONSTRAINT",
        "REFERENCES",
        "ON",
        "INNER",
        "LEFT",
        "RIGHT",
        "OUTER",
        "JOIN",
        "UNION",
        "ALL",
        "DISTINCT",
        "ORDER",
        "BY",
        "GROUP",
        "HAVING",
        "LIMIT",
        "OFFSET",
        "AS",
        "AND",
        "OR",
        "IN",
        "EXISTS",
        "BETWEEN",
        "LIKE",
        "IS",
        "CASE",
        "WHEN",
        "THEN",
        "ELSE",
        "END",
        "IF",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "TRANSACTION",
        "GRANT",
        "REVOKE",
        "USER",
        "ROLE",
        "PRIVILEGE",
        "INTEGER",
        "INT",
        "BIGINT",
        "SMALLINT",
        "DECIMAL",
        "NUMERIC",
        "FLOAT",
        "REAL",
        "DOUBLE",
        "CHAR",
        "VARCHAR",
        "TEXT",
        "DATE",
        "TIME",
        "TIMESTAMP",
        "BOOLEAN",
        "TRUE",
        "FALSE",
        "UNKNOWN",
    }

    # Oracle-specific reserved words
    _ORACLE_RESERVED_WORDS: Set[str] = _COMMON_RESERVED_WORDS | {
        "ACCESS",
        "ADD",
        "ADMIN",
        "AFTER",
        "ANALYZE",
        "ARCHIVE",
        "ARCHIVELOG",
        "AUDIT",
        "BACKUP",
        "BECOME",
        "BEFORE",
        "BLOCK",
        "BODY",
        "CACHE",
        "CANCEL",
        "CASCADE",
        "CHANGE",
        "CHECKPOINT",
        "CLUSTER",
        "COBOL",
        "COMMENT",
        "COMPILE",
        "COMPRESS",
        "CONNECT",
        "CONTENTS",
        "CONTINUE",
        "CONTROLFILE",
        "CURSOR",
        "CYCLE",
        "DATAFILE",
        "DBA",
        "DEBUGOFF",
        "DEBUGON",
        "DECLARE",
        "DISABLE",
        "DISMOUNT",
        "DUMP",
        "EACH",
        "ENABLE",
        "EVENTS",
        "EXCEPT",
        "EXCEPTIONS",
        "EXCLUSIVE",
        "EXECUTE",
        "EXIT",
        "EXPLAIN",
        "EXTENT",
        "EXTERNALLY",
        "FETCH",
        "FILE",
        "FLUSH",
        "FOR",
        "FORCE",
        "FORTRAN",
        "FOUND",
        "FREELIST",
        "FREELISTS",
        "FUNCTION",
        "GOTO",
        "GROUPS",
        "IDENTIFIED",
        "IMMEDIATE",
        "INCLUDING",
        "INCREMENT",
        "INITIAL",
        "INITRANS",
        "INSTANCE",
        "INTERSECT",
        "INTO",
        "INVALIDATE",
        "ISOLATION",
        "LAYER",
        "LEVEL",
        "LINK",
        "LISTS",
        "LOCK",
        "LOGFILE",
        "LONG",
        "LOOP",
        "MANAGE",
        "MANUAL",
        "MAXDATAFILES",
        "MAXINSTANCES",
        "MAXLOGFILES",
        "MAXLOGHISTORY",
        "MAXLOGMEMBERS",
        "MAXTRANS",
        "MAXVALUE",
        "MERGE",
        "MINEXTENTS",
        "MINVALUE",
        "MOUNT",
        "MOVE",
        "NEXT",
        "NOARCHIVELOG",
        "NOAUDIT",
        "NOCACHE",
        "NOCYCLE",
        "NOMAXVALUE",
        "NOMINVALUE",
        "NONE",
        "NOORDER",
        "NORESETLOGS",
        "NORMAL",
        "NOSORT",
        "NOWAIT",
        "OPTIMAL",
        "OPTION",
        "OVER",
        "PACKAGE",
        "PARALLEL",
        "PARTITION",
        "PCTFREE",
        "PCTINCREASE",
        "PCTUSED",
        "PLAN",
        "PLI",
        "PRECISION",
        "PRIOR",
        "PRIVATE",
        "PROCEDURE",
        "PROFILE",
        "PUBLIC",
        "QUOTA",
        "READ",
        "RECOVER",
        "REFERENCING",
        "RENAME",
        "REPLACE",
        "RESETLOGS",
        "RESOURCE",
        "RESTRICTED",
        "RETURN",
        "REUSE",
        "ROW",
        "ROWID",
        "ROWNUM",
        "ROWS",
        "SAVEPOINT",
        "SCN",
        "SEGMENT",
        "SEQUENCE",
        "SERIALIZABLE",
        "SESSION",
        "SHARE",
        "SHARED",
        "SIZE",
        "SNAPSHOT",
        "SORT",
        "SQL",
        "SQLCODE",
        "SQLERROR",
        "STATEMENT",
        "STATISTICS",
        "STOP",
        "STORAGE",
        "SUCCESSFUL",
        "SWITCH",
        "SYNONYM",
        "SYSDATE",
        "SYSTEM",
        "TABLES",
        "TABLESPACE",
        "TEMPORARY",
        "THREAD",
        "TO",
        "TRACING",
        "TRIGGER",
        "TRUNCATE",
        "TYPE",
        "UID",
        "UNDER",
        "UNLIMITED",
        "UNTIL",
        "USE",
        "USING",
        "VALIDATE",
        "VALUES",
        "WHENEVER",
        "WHILE",
        "WITH",
        "WORK",
        "WRITE",
        "ZONE",
    }

    # PostgreSQL-specific reserved words
    _POSTGRES_RESERVED_WORDS: Set[str] = _COMMON_RESERVED_WORDS | {
        "ABORT",
        "ABSOLUTE",
        "ACCESS",
        "ACTION",
        "ADD",
        "ADMIN",
        "AFTER",
        "AGGREGATE",
        "ALSO",
        "ALTER",
        "ALWAYS",
        "ANALYSE",
        "ANALYZE",
        "ANY",
        "ARRAY",
        "ASSERTION",
        "ASSIGNMENT",
        "ASYMMETRIC",
        "AT",
        "ATTRIBUTE",
        "AUTHORIZATION",
        "BACKWARD",
        "BEFORE",
        "BIGINT",
        "BINARY",
        "BIT",
        "BOOLEAN",
        "BOTH",
        "CACHE",
        "CALLED",
        "CASCADE",
        "CASCADED",
        "CAST",
        "CATALOG",
        "CHAIN",
        "CHARACTERISTICS",
        "CHECK",
        "CHECKPOINT",
        "CLASS",
        "CLOSE",
        "CLUSTER",
        "COALESCE",
        "COLLATE",
        "COLLATION",
        "COMMENT",
        "COMMENTS",
        "COMMIT",
        "COMMITTED",
        "CONFIGURATION",
        "CONNECTION",
        "CONSTRAINT",
        "CONSTRAINTS",
        "CONTENT",
        "CONTINUE",
        "CONVERSION",
        "COPY",
        "COST",
        "CROSS",
        "CSV",
        "CURRENT",
        "CURSOR",
        "CYCLE",
        "DATA",
        "DATABASE",
        "DAY",
        "DEALLOCATE",
        "DECLARE",
        "DEFAULT",
        "DEFAULTS",
        "DEFERRABLE",
        "DEFERRED",
        "DEFINER",
        "DELETE",
        "DELIMITER",
        "DELIMITERS",
        "DISABLE",
        "DISCARD",
        "DISTINCT",
        "DO",
        "DOCUMENT",
        "DOMAIN",
        "DOUBLE",
        "DROP",
        "EACH",
        "ENABLE",
        "ENCODING",
        "ENCRYPTED",
        "ENUM",
        "ESCAPE",
        "EVENT",
        "EXCLUDE",
        "EXCLUDING",
        "EXCLUSIVE",
        "EXECUTE",
        "EXISTS",
        "EXPLAIN",
        "EXTENSION",
        "EXTERNAL",
        "EXTRACT",
        "FALSE",
        "FAMILY",
        "FETCH",
        "FILTER",
        "FIRST",
        "FLOAT",
        "FOLLOWING",
        "FOR",
        "FORCE",
        "FOREIGN",
        "FORWARD",
        "FREEZE",
        "FULL",
        "FUNCTION",
        "FUNCTIONS",
        "GLOBAL",
        "GRANTED",
        "GREATEST",
        "GROUPING",
        "HANDLER",
        "HEADER",
        "HOLD",
        "HOUR",
        "IDENTITY",
        "IF",
        "ILIKE",
        "IMMEDIATE",
        "IMMUTABLE",
        "IMPLICIT",
        "INCLUDING",
        "INCREMENT",
        "INHERITS",
        "INITIALLY",
        "INLINE",
        "INPUT",
        "INSENSITIVE",
        "INSERT",
        "INSTEAD",
        "INTERSECT",
        "INTERVAL",
        "INTO",
        "INVOKER",
        "ISOLATION",
        "JSON",
        "JSONB",
        "KEY",
        "LABEL",
        "LANGUAGE",
        "LARGE",
        "LAST",
        "LATERAL",
        "LEADING",
        "LEAKPROOF",
        "LEAST",
        "LEVEL",
        "LISTEN",
        "LOAD",
        "LOCAL",
        "LOCATION",
        "LOCK",
        "MAPPING",
        "MATCH",
        "MATERIALIZED",
        "MAXVALUE",
        "METHOD",
        "MINUTE",
        "MINVALUE",
        "MODE",
        "MONTH",
        "MOVE",
        "NAME",
        "NAMES",
        "NATIONAL",
        "NATURAL",
        "NCHAR",
        "NEXT",
        "NO",
        "NONE",
        "NOTIFY",
        "NOWAIT",
        "NULLIF",
        "NULLS",
        "OBJECT",
        "OF",
        "OFF",
        "OIDS",
        "OPERATOR",
        "OPTION",
        "OPTIONS",
        "ORDINALITY",
        "OUT",
        "OUTER",
        "OVER",
        "OVERLAPS",
        "OVERLAY",
        "OWNED",
        "OWNER",
        "PARALLEL",
        "PARSER",
        "PARTIAL",
        "PARTITION",
        "PASSING",
        "PASSWORD",
        "PATH",
        "PLANS",
        "POLICY",
        "POSITION",
        "PRECEDING",
        "PREPARE",
        "PREPARED",
        "PRESERVE",
        "PRIOR",
        "PRIVILEGES",
        "PROCEDURAL",
        "PROCEDURE",
        "PROGRAM",
        "QUOTE",
        "RANGE",
        "READ",
        "REAL",
        "REASSIGN",
        "RECHECK",
        "RECURSIVE",
        "REF",
        "REFRESH",
        "REINDEX",
        "RELATIVE",
        "RELEASE",
        "RENAME",
        "REPEATABLE",
        "REPLACE",
        "REPLICA",
        "RESET",
        "RESTART",
        "RESTRICT",
        "RETURNING",
        "RETURNS",
        "REVOKE",
        "RIGHT",
        "ROLE",
        "ROLLBACK",
        "ROLLUP",
        "ROW",
        "ROWS",
        "RULE",
        "SAVEPOINT",
        "SCHEMA",
        "SCROLL",
        "SEARCH",
        "SECOND",
        "SECURITY",
        "SELECT",
        "SEQUENCE",
        "SEQUENCES",
        "SERIALIZABLE",
        "SERVER",
        "SESSION",
        "SET",
        "SETOF",
        "SETS",
        "SHARE",
        "SHOW",
        "SIMILAR",
        "SIMPLE",
        "SKIP",
        "SMALLINT",
        "SNAPSHOT",
        "SOME",
        "STABLE",
        "STANDALONE",
        "START",
        "STATEMENT",
        "STATISTICS",
        "STDIN",
        "STDOUT",
        "STORAGE",
        "STRICT",
        "STRIP",
        "SUBSTRING",
        "SYMMETRIC",
        "SYSID",
        "SYSTEM",
        "TABLE",
        "TABLES",
        "TABLESPACE",
        "TEMP",
        "TEMPLATE",
        "TEMPORARY",
        "TEXT",
        "TIES",
        "TIME",
        "TIMESTAMP",
        "TO",
        "TRAILING",
        "TRANSACTION",
        "TREAT",
        "TRIGGER",
        "TRIM",
        "TRUE",
        "TRUNCATE",
        "TRUSTED",
        "TYPE",
        "TYPES",
        "UNBOUNDED",
        "UNCOMMITTED",
        "UNENCRYPTED",
        "UNION",
        "UNIQUE",
        "UNKNOWN",
        "UNLISTEN",
        "UNLOGGED",
        "UNTIL",
        "UPDATE",
        "USER",
        "USING",
        "VACUUM",
        "VALID",
        "VALIDATE",
        "VALIDATOR",
        "VALUE",
        "VALUES",
        "VARCHAR",
        "VARIADIC",
        "VARYING",
        "VERBOSE",
        "VERSION",
        "VIEW",
        "VIEWS",
        "VOLATILE",
        "WHEN",
        "WHERE",
        "WHITESPACE",
        "WINDOW",
        "WITH",
        "WITHIN",
        "WITHOUT",
        "WORK",
        "WRAPPER",
        "WRITE",
        "XML",
        "XMLATTRIBUTES",
        "XMLCONCAT",
        "XMLELEMENT",
        "XMLEXISTS",
        "XMLFOREST",
        "XMLPARSE",
        "XMLPI",
        "XMLROOT",
        "XMLSERIALIZE",
        "YEAR",
        "YES",
        "ZONE",
    }

    # SQL Server-specific reserved words
    _SQLSERVER_RESERVED_WORDS: Set[str] = _COMMON_RESERVED_WORDS | {
        "ADD",
        "ALL",
        "ALTER",
        "AND",
        "ANY",
        "AS",
        "ASC",
        "AUTHORIZATION",
        "BACKUP",
        "BEGIN",
        "BETWEEN",
        "BREAK",
        "BROWSE",
        "BULK",
        "BY",
        "CASCADE",
        "CASE",
        "CHECK",
        "CHECKPOINT",
        "CLOSE",
        "CLUSTERED",
        "COALESCE",
        "COLLATE",
        "COLUMN",
        "COMMIT",
        "COMPUTE",
        "CONSTRAINT",
        "CONTAINS",
        "CONTAINSTABLE",
        "CONTINUE",
        "CONVERT",
        "CREATE",
        "CROSS",
        "CURRENT",
        "CURRENT_DATE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
        "CURRENT_USER",
        "CURSOR",
        "DATABASE",
        "DBCC",
        "DEALLOCATE",
        "DECLARE",
        "DEFAULT",
        "DELETE",
        "DENY",
        "DESC",
        "DISK",
        "DISTINCT",
        "DISTRIBUTED",
        "DOUBLE",
        "DROP",
        "DUMP",
        "ELSE",
        "END",
        "ERRLVL",
        "ESCAPE",
        "EXCEPT",
        "EXEC",
        "EXECUTE",
        "EXISTS",
        "EXIT",
        "EXTERNAL",
        "FETCH",
        "FILE",
        "FILLFACTOR",
        "FOR",
        "FOREIGN",
        "FREETEXT",
        "FREETEXTTABLE",
        "FROM",
        "FULL",
        "FUNCTION",
        "GOTO",
        "GRANT",
        "GROUP",
        "HAVING",
        "HOLDLOCK",
        "IDENTITY",
        "IDENTITYCOL",
        "IDENTITY_INSERT",
        "IF",
        "IN",
        "INDEX",
        "INNER",
        "INSERT",
        "INTERSECT",
        "INTO",
        "IS",
        "JOIN",
        "KEY",
        "KILL",
        "LEFT",
        "LIKE",
        "LINENO",
        "LOAD",
        "MERGE",
        "NATIONAL",
        "NOCHECK",
        "NONCLUSTERED",
        "NOT",
        "NULL",
        "NULLIF",
        "OF",
        "OFF",
        "OFFSETS",
        "ON",
        "OPEN",
        "OPENDATASOURCE",
        "OPENQUERY",
        "OPENROWSET",
        "OPENXML",
        "OPTION",
        "OR",
        "ORDER",
        "OUTER",
        "OVER",
        "PERCENT",
        "PIVOT",
        "PLAN",
        "PRECISION",
        "PRIMARY",
        "PRINT",
        "PROC",
        "PROCEDURE",
        "PUBLIC",
        "RAISERROR",
        "READ",
        "READTEXT",
        "RECONFIGURE",
        "REFERENCES",
        "REPLICATION",
        "RESTORE",
        "RESTRICT",
        "RETURN",
        "REVERT",
        "REVOKE",
        "RIGHT",
        "ROLLBACK",
        "ROWCOUNT",
        "ROWGUIDCOL",
        "RULE",
        "SAVE",
        "SCHEMA",
        "SECURITYAUDIT",
        "SELECT",
        "SEMANTICKEYPHRASETABLE",
        "SEMANTICSIMILARITYDETAILSTABLE",
        "SEMANTICSIMILARITYTABLE",
        "SESSION_USER",
        "SET",
        "SETUSER",
        "SHUTDOWN",
        "SOME",
        "STATISTICS",
        "SYSTEM_USER",
        "TABLE",
        "TABLESAMPLE",
        "TEXTSIZE",
        "THEN",
        "TO",
        "TOP",
        "TRAN",
        "TRANSACTION",
        "TRIGGER",
        "TRUNCATE",
        "TRY_CONVERT",
        "TSEQUAL",
        "UNION",
        "UNIQUE",
        "UNPIVOT",
        "UPDATE",
        "UPDATETEXT",
        "USE",
        "USER",
        "VALUES",
        "VARYING",
        "VIEW",
        "WAITFOR",
        "WHEN",
        "WHERE",
        "WHILE",
        "WITH",
        "WITHIN",
        "WRITETEXT",
    }

    # MySQL-specific reserved words
    _MYSQL_RESERVED_WORDS: Set[str] = _COMMON_RESERVED_WORDS | {
        "ACCESSIBLE",
        "ADD",
        "ALL",
        "ALTER",
        "ANALYZE",
        "AND",
        "AS",
        "ASC",
        "ASENSITIVE",
        "BEFORE",
        "BETWEEN",
        "BIGINT",
        "BINARY",
        "BLOB",
        "BOTH",
        "BY",
        "CALL",
        "CASCADE",
        "CASE",
        "CHANGE",
        "CHAR",
        "CHARACTER",
        "CHECK",
        "COLLATE",
        "COLUMN",
        "CONDITION",
        "CONSTRAINT",
        "CONTINUE",
        "CONVERT",
        "CREATE",
        "CROSS",
        "CURRENT_DATE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
        "CURRENT_USER",
        "CURSOR",
        "DATABASE",
        "DATABASES",
        "DAY_HOUR",
        "DAY_MICROSECOND",
        "DAY_MINUTE",
        "DAY_SECOND",
        "DEC",
        "DECIMAL",
        "DECLARE",
        "DEFAULT",
        "DELAYED",
        "DELETE",
        "DESC",
        "DESCRIBE",
        "DETERMINISTIC",
        "DISTINCT",
        "DISTINCTROW",
        "DIV",
        "DOUBLE",
        "DROP",
        "DUAL",
        "EACH",
        "ELSE",
        "ELSEIF",
        "ENCLOSED",
        "ESCAPED",
        "EXISTS",
        "EXIT",
        "EXPLAIN",
        "FALSE",
        "FETCH",
        "FLOAT",
        "FLOAT4",
        "FLOAT8",
        "FOR",
        "FORCE",
        "FOREIGN",
        "FROM",
        "FULLTEXT",
        "GRANT",
        "GROUP",
        "HAVING",
        "HIGH_PRIORITY",
        "HOUR_MICROSECOND",
        "HOUR_MINUTE",
        "HOUR_SECOND",
        "IF",
        "IGNORE",
        "IN",
        "INDEX",
        "INFILE",
        "INNER",
        "INOUT",
        "INSENSITIVE",
        "INSERT",
        "INT",
        "INT1",
        "INT2",
        "INT3",
        "INT4",
        "INT8",
        "INTEGER",
        "INTERVAL",
        "INTO",
        "IS",
        "ITERATE",
        "JOIN",
        "KEY",
        "KEYS",
        "KILL",
        "LEADING",
        "LEAVE",
        "LEFT",
        "LIKE",
        "LIMIT",
        "LINEAR",
        "LINES",
        "LOAD",
        "LOCALTIME",
        "LOCALTIMESTAMP",
        "LOCK",
        "LONG",
        "LONGBLOB",
        "LONGTEXT",
        "LOOP",
        "LOW_PRIORITY",
        "MATCH",
        "MEDIUMBLOB",
        "MEDIUMINT",
        "MEDIUMTEXT",
        "MIDDLEINT",
        "MINUTE_MICROSECOND",
        "MINUTE_SECOND",
        "MOD",
        "MODIFIES",
        "NATURAL",
        "NOT",
        "NO_WRITE_TO_BINLOG",
        "NULL",
        "NUMERIC",
        "ON",
        "OPTIMIZE",
        "OPTION",
        "OPTIONALLY",
        "OR",
        "ORDER",
        "OUT",
        "OUTER",
        "OUTFILE",
        "PRECISION",
        "PRIMARY",
        "PROCEDURE",
        "PURGE",
        "RANGE",
        "READ",
        "READS",
        "READ_WRITE",
        "REAL",
        "REFERENCES",
        "REGEXP",
        "RELEASE",
        "RENAME",
        "REPEAT",
        "REPLACE",
        "REQUIRE",
        "RESTRICT",
        "RETURN",
        "REVOKE",
        "RIGHT",
        "RLIKE",
        "SCHEMA",
        "SCHEMAS",
        "SECOND_MICROSECOND",
        "SELECT",
        "SENSITIVE",
        "SEPARATOR",
        "SET",
        "SHOW",
        "SMALLINT",
        "SPATIAL",
        "SPECIFIC",
        "SQL",
        "SQLEXCEPTION",
        "SQLSTATE",
        "SQLWARNING",
        "SQL_BIG_RESULT",
        "SQL_CALC_FOUND_ROWS",
        "SQL_SMALL_RESULT",
        "SSL",
        "STARTING",
        "STRAIGHT_JOIN",
        "TABLE",
        "TERMINATED",
        "THEN",
        "TINYBLOB",
        "TINYINT",
        "TINYTEXT",
        "TO",
        "TRAILING",
        "TRIGGER",
        "TRUE",
        "UNDO",
        "UNION",
        "UNIQUE",
        "UNLOCK",
        "UNSIGNED",
        "UPDATE",
        "USAGE",
        "USE",
        "USING",
        "UTC_DATE",
        "UTC_TIME",
        "UTC_TIMESTAMP",
        "VALUES",
        "VARBINARY",
        "VARCHAR",
        "VARCHARACTER",
        "VARYING",
        "WHEN",
        "WHERE",
        "WHILE",
        "WITH",
        "WRITE",
        "X509",
        "XOR",
        "YEAR_MONTH",
        "ZEROFILL",
    }

    # SQLite-specific reserved words
    _SQLITE_RESERVED_WORDS: Set[str] = _COMMON_RESERVED_WORDS | {
        "ABORT",
        "ACTION",
        "ADD",
        "AFTER",
        "ALL",
        "ALTER",
        "ANALYZE",
        "AND",
        "AS",
        "ASC",
        "ATTACH",
        "AUTOINCREMENT",
        "BEFORE",
        "BEGIN",
        "BETWEEN",
        "BY",
        "CASCADE",
        "CASE",
        "CAST",
        "CHECK",
        "COLLATE",
        "COLUMN",
        "COMMIT",
        "CONFLICT",
        "CONSTRAINT",
        "CREATE",
        "CROSS",
        "CURRENT_DATE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
        "DATABASE",
        "DEFAULT",
        "DEFERRABLE",
        "DEFERRED",
        "DELETE",
        "DESC",
        "DETACH",
        "DISTINCT",
        "DROP",
        "EACH",
        "ELSE",
        "END",
        "ESCAPE",
        "EXCEPT",
        "EXCLUSIVE",
        "EXISTS",
        "EXPLAIN",
        "FAIL",
        "FOR",
        "FOREIGN",
        "FROM",
        "FULL",
        "GLOB",
        "GROUP",
        "HAVING",
        "IF",
        "IGNORE",
        "IMMEDIATE",
        "IN",
        "INDEX",
        "INDEXED",
        "INITIALLY",
        "INNER",
        "INSERT",
        "INSTEAD",
        "INTERSECT",
        "INTO",
        "IS",
        "ISNULL",
        "JOIN",
        "KEY",
        "LEFT",
        "LIKE",
        "LIMIT",
        "MATCH",
        "NATURAL",
        "NO",
        "NOT",
        "NOTNULL",
        "NULL",
        "OF",
        "OFFSET",
        "ON",
        "OR",
        "ORDER",
        "OUTER",
        "PLAN",
        "PRAGMA",
        "PRIMARY",
        "QUERY",
        "RAISE",
        "RECURSIVE",
        "REFERENCES",
        "REGEXP",
        "REINDEX",
        "RELEASE",
        "RENAME",
        "REPLACE",
        "RESTRICT",
        "RIGHT",
        "ROLLBACK",
        "ROW",
        "SAVEPOINT",
        "SELECT",
        "SET",
        "TABLE",
        "TEMP",
        "TEMPORARY",
        "THEN",
        "TO",
        "TRANSACTION",
        "TRIGGER",
        "UNION",
        "UNIQUE",
        "UPDATE",
        "USING",
        "VACUUM",
        "VALUES",
        "VIEW",
        "VIRTUAL",
        "WHEN",
        "WHERE",
        "WITH",
        "WITHOUT",
    }

    # BigQuery-specific reserved words
    _BIGQUERY_RESERVED_WORDS: Set[str] = _COMMON_RESERVED_WORDS | {
        "ALL",
        "AND",
        "ANY",
        "ARRAY",
        "AS",
        "ASC",
        "ASSERT_ROWS_MODIFIED",
        "AT",
        "BETWEEN",
        "BY",
        "CASE",
        "CAST",
        "COLLATE",
        "CONTAINS",
        "CREATE",
        "CROSS",
        "CUBE",
        "CURRENT",
        "DEFAULT",
        "DEFINE",
        "DESC",
        "DISTINCT",
        "ELSE",
        "END",
        "ENUM",
        "ESCAPE",
        "EXCEPT",
        "EXCLUDE",
        "EXISTS",
        "EXTRACT",
        "FALSE",
        "FETCH",
        "FOLLOWING",
        "FOR",
        "FROM",
        "FULL",
        "GROUP",
        "GROUPING",
        "GROUPS",
        "HASH",
        "HAVING",
        "IF",
        "IGNORE",
        "IN",
        "INNER",
        "INTERSECT",
        "INTERVAL",
        "INTO",
        "IS",
        "JOIN",
        "LATERAL",
        "LEFT",
        "LIKE",
        "LIMIT",
        "LOOKUP",
        "MERGE",
        "NATURAL",
        "NEW",
        "NO",
        "NOT",
        "NULL",
        "NULLS",
        "OF",
        "ON",
        "OR",
        "ORDER",
        "OUTER",
        "OVER",
        "PARTITION",
        "PRECEDING",
        "PROTO",
        "RANGE",
        "RECURSIVE",
        "RESPECT",
        "RIGHT",
        "ROLLUP",
        "ROWS",
        "SELECT",
        "SET",
        "SOME",
        "STRUCT",
        "TABLESAMPLE",
        "THEN",
        "TO",
        "TREAT",
        "TRUE",
        "UNBOUNDED",
        "UNION",
        "UNNEST",
        "USING",
        "WHEN",
        "WHERE",
        "WINDOW",
        "WITH",
        "WITHIN",
    }

    # Redshift-specific reserved words
    _REDSHIFT_RESERVED_WORDS: Set[str] = _COMMON_RESERVED_WORDS | {
        "AES128",
        "AES256",
        "ALL",
        "ALLOWOVERWRITE",
        "ANALYSE",
        "ANALYZE",
        "AND",
        "ANY",
        "ARRAY",
        "AS",
        "ASC",
        "AUTHORIZATION",
        "BACKUP",
        "BETWEEN",
        "BINARY",
        "BLANKSASNULL",
        "BOTH",
        "BYTEDICT",
        "BZIP2",
        "CASE",
        "CAST",
        "CHECK",
        "COLLATE",
        "COLUMN",
        "CONSTRAINT",
        "CREATE",
        "CREDENTIALS",
        "CROSS",
        "CURRENT_DATE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
        "CURRENT_USER",
        "CURRENT_USER_ID",
        "DEFAULT",
        "DEFERRABLE",
        "DEFLATE",
        "DEFRAG",
        "DELTA",
        "DELTA32K",
        "DESC",
        "DISABLE",
        "DISTINCT",
        "DO",
        "ELSE",
        "EMPTYASNULL",
        "ENABLE",
        "ENCODE",
        "ENCRYPT",
        "ENCRYPTION",
        "END",
        "EXCEPT",
        "EXPLICIT",
        "FALSE",
        "FOR",
        "FOREIGN",
        "FREEZE",
        "FROM",
        "FULL",
        "GLOBALDICT256",
        "GLOBALDICT64K",
        "GRANT",
        "GROUP",
        "GZIP",
        "HAVING",
        "IDENTITY",
        "IGNORE",
        "ILIKE",
        "IN",
        "INITIALLY",
        "INNER",
        "INTERSECT",
        "INTO",
        "IS",
        "ISNULL",
        "JOIN",
        "LEADING",
        "LEFT",
        "LIKE",
        "LIMIT",
        "LOCALTIME",
        "LOCALTIMESTAMP",
        "LUN",
        "LUNS",
        "LZO",
        "LZOP",
        "MINUS",
        "MOSTLY13",
        "MOSTLY32",
        "MOSTLY8",
        "NATURAL",
        "NEW",
        "NOT",
        "NOTNULL",
        "NULL",
        "NULLS",
        "OFF",
        "OFFLINE",
        "OFFSET",
        "OID",
        "OLD",
        "ON",
        "ONLY",
        "OPEN",
        "OR",
        "ORDER",
        "OUTER",
        "OVERLAPS",
        "PARALLEL",
        "PARTITION",
        "PERCENT",
        "PERMISSIONS",
        "PLACING",
        "PRIMARY",
        "RAW",
        "READRATIO",
        "RECOVER",
        "REFERENCES",
        "RESPECT",
        "REJECTLOG",
        "RESORT",
        "RESTORE",
        "RIGHT",
        "SELECT",
        "SESSION_USER",
        "SIMILAR",
        "SNAPSHOT",
        "SOME",
        "SYSDATE",
        "SYSTEM",
        "TABLE",
        "TAG",
        "TDES",
        "TEXT255",
        "TEXT32K",
        "THEN",
        "TIMESTAMP",
        "TO",
        "TOP",
        "TRAILING",
        "TRUE",
        "TRUNCATECOLUMNS",
        "UNION",
        "UNIQUE",
        "USER",
        "USING",
        "VERBOSE",
        "WALLET",
        "WHEN",
        "WHERE",
        "WITH",
        "WITHOUT",
    }

    # Comprehensive mapping of dialect to context-specific exceptions
    _DIALECT_CONTEXT_EXEMPTIONS: Dict[SQLDialect, Dict[DatabaseObjectType, Set[str]]] = {
        SQLDialect.SQLITE: {
            DatabaseObjectType.TABLE: {"VIEW", "KEY", "COLUMN"},  # These can be used as table names
            DatabaseObjectType.COLUMN: {"VIEW", "KEY", "COLUMN", "INDEX"},  # These can be used as column names
        },
        SQLDialect.POSTGRES: {
            DatabaseObjectType.COLUMN: {"COLUMN", "KEY", "TYPE", "ROLE"},  # Can be column names when quoted
        },
        SQLDialect.ORACLE: {
            DatabaseObjectType.COLUMN: {"COLUMN", "INDEX", "TYPE"},
        },
        SQLDialect.SQLSERVER: {
            DatabaseObjectType.COLUMN: {"KEY", "INDEX"},
            DatabaseObjectType.FUNCTION: {"KEY", "TYPE"},  # Different rules for function parameters
        },
        SQLDialect.MYSQL: {
            DatabaseObjectType.COLUMN: {"COLUMN", "KEY", "INDEX"},
        },
        # BigQuery and Redshift use global reserved words for now
        SQLDialect.BIGQUERY: {},
        SQLDialect.REDSHIFT: {},
    }

    @classmethod
    def get(
        cls,
        dialect: SQLDialect,
        property_name: Literal["objects", "reserved_words", "drivers", "context_exemptions", "identifier_rules"],
    ) -> Any:
        assert isinstance(dialect, SQLDialect), "Dialect must be an instance of SQLDialect enum"

        if property_name == "reserved_words":
            return getattr(cls, f"_{dialect.name}_RESERVED_WORDS", set())
        elif property_name == "objects":
            return cls._DIALECT_OBJECTS.get(dialect.resolved_alias, set())
        elif property_name == "context_exemptions":
            return cls._DIALECT_CONTEXT_EXEMPTIONS.get(dialect.resolved_alias, {})
        elif property_name == "identifier_rules":
            # Now get identifier rules directly from the SQLDialect enum
            return dialect.resolved_alias.identifier_rules
        elif property_name == "drivers":
            return cls._get_dialect_drivers(dialect)
        else:
            return {}

    @classmethod
    def _get_dialect_drivers(cls, dialect: SQLDialect) -> OrderedDict[str, Dict[str, Any]]:
        """
        Get driver mapping for the specified dialect.

        Args:
            dialect: The SQL dialect to get drivers for

        Returns:
            OrderedDict of driver priorities to driver information
        """
        try:
            from drivers.registry import get_drivers_for_dialect
        except ImportError:
            from ..drivers.registry import get_drivers_for_dialect
        # Get drivers from the registry for this dialect
        drivers_list = get_drivers_for_dialect(dialect)

        # Convert to the expected format
        result = OrderedDict()
        priority_names = ["primary", "alternative", "fallback", "tertiary"]

        for i, driver_config in enumerate(drivers_list):
            priority_name = priority_names[i] if i < len(priority_names) else f"option_{i+1}"
            result[priority_name] = {
                "name": driver_config.name,
                "package": getattr(driver_config, "module_name", driver_config.name),
                "connection_format": getattr(driver_config, "connection_string_format", "direct_params"),
                "description": f"{driver_config.name} driver for {dialect.description}",
                "available": cls._check_package_available(getattr(driver_config, "module_name", driver_config.name)),
                "driver_enum": driver_config,  # Return the actual driver enum config
            }

        return result

    @staticmethod
    def _check_package_available(package_name: Optional[str], import_name: Optional[str] = None) -> bool:
        """
        Check if a Python package is available in the current environment.

        Args:
            package_name: The package name (for pip install)
            import_name: The module name for import (if different from package_name)

        Returns:
            True if package is available, False otherwise
        """
        if package_name is None:
            # Built-in packages like sqlite3
            logger.debug("Checking built-in package availability", emoji="🔍")
            return True

        # Use import_name if provided, otherwise use package_name
        module_to_import = import_name or package_name

        # Handle special cases for import names
        if module_to_import == "mysql-connector-python":
            module_to_import = "mysql.connector"
        elif module_to_import == "psycopg2-binary":
            module_to_import = "psycopg2"
        elif module_to_import == "google-cloud-bigquery":
            module_to_import = "google.cloud.bigquery"
        elif module_to_import == "pandas-gbq":
            module_to_import = "pandas_gbq"

        try:
            __import__(module_to_import)
            logger.debug(f"Package '{package_name}' ({module_to_import}) is available", emoji="✅")
            return True
        except ImportError as e:
            logger.warning(f"Package '{package_name}' ({module_to_import}) is not available: {e}", emoji="📦")
            return False

    @classmethod
    def is_reserved_word(cls, dialect: SQLDialect, context: DatabaseObjectType, identifier: str) -> bool:
        """
        Check if an identifier is a reserved word in the specified SQL dialect and context.
        This method determines whether a given identifier conflicts with reserved words
        in a specific SQL dialect, taking into account context-specific exemptions where
        certain reserved words may be allowed.
        Args:
            dialect (SQLDialect): The SQL dialect to check against (e.g., MySQL, PostgreSQL, SQLite).
            context (DatabaseObjectType): The database object context where the identifier
                will be used (e.g., table name, column name, index name).
            identifier (str): The identifier string to validate against reserved words.
        Returns:
            bool: True if the identifier is a reserved word in the given dialect and context,
                False otherwise.
        Note:
            The method performs case-insensitive comparison by converting the identifier
            to uppercase. Context-specific exemptions are applied, meaning some reserved
            words may be allowed in certain database object contexts.
        Example:
            >>> cls.is_reserved_word(SQLDialect.MYSQL, DatabaseObjectType.TABLE, "SELECT")
            True
            >>> cls.is_reserved_word(SQLDialect.MYSQL, DatabaseObjectType.COLUMN, "order")
            True
        """

        if identifier.strip().upper() in cls.get(dialect, "reserved_words").difference(
            cls.get(dialect, "context_exemptions").get(context, set())
        ):
            logger.debug(f"'{identifier}' is reserved in {dialect.description} for {context.description}", emoji="🚨")
            return True

        return False

    @staticmethod
    def get_best_available_driver(dialect: SQLDialect) -> Dict[str, Any]:
        """
        Get the best available Python driver for a SQL dialect in the current environment.

        Args:
            dialect (SQLDialect): The SQL dialect to check for available drivers.

        Returns:
            Dict[str, Any]: The best available driver information including name, package,
                connection format, description, availability status, and driver_enum.
        """
        drivers = SQL_DIALECT_REGISTRY._get_dialect_drivers(dialect)

        # Find the first available driver in priority order
        for priority, driver_info in drivers.items():
            if driver_info["available"]:
                result = driver_info.copy()
                result.update({"priority": priority})
                return result

        return {}

    @staticmethod
    def _encapsulate_identifier(dialect: SQLDialect, identifier: str) -> str:
        """
        Encapsulate an identifier using the appropriate quoting for the SQL dialect.

        Args:
            dialect (SQLDialect): The SQL dialect to use for encapsulation
            identifier (str): The identifier to encapsulate

        Returns:
            str: The encapsulated identifier
        """
        assert isinstance(dialect, SQLDialect), "Invalid dialect type"
        assert isinstance(identifier, str), "Identifier must be a string"

        quote_char = dialect.quote_character

        logger.debug(f"Encapsulated identifier: '{identifier}' -> '{quote_char}{identifier}{quote_char}'", emoji="🔧")

        # Encapsulate the identifier with the appropriate quotes
        return f"{quote_char}{identifier}{quote_char}"

    @staticmethod
    def validate_identifier(
        dialect: SQLDialect,
        identifier: str,
        context: DatabaseObjectType,
        correction_method: Literal["encapsulate", "normalize"] = "normalize",
        default_prefix_correction: str = "col_",
    ) -> Dict[str, Any]:
        """
        Validate and auto-fix SQL identifiers against dialect-specific rules.

        Args:
            dialect (SQLDialect): The SQL dialect to validate against
            identifier (str): The identifier to validate
            context (DatabaseObjectType): The context (object type) where the identifier is used
            correction_method (str): Method for fixing issues ('encapsulate' or 'normalize')
                - 'encapsulate': Use quoting to preserve original identifier when possible
                - 'normalize': Modify the identifier to meet dialect rules

        Returns:
            Dict[str, Any]: Dictionary with validation results:
                - 'valid': bool - Whether identifier is valid after auto-fixing
                - 'original': str - Original identifier as provided
                - 'final': str - Final identifier after applying dialect rules and fixes
                - 'is_reserved': bool - Whether identifier is reserved in the given context
                - 'correction_applied': str - Type of correction applied ('none', 'encapsulated', 'normalized')
        """
        logger.debug(f"Validating identifier '{identifier}' for {dialect.description} {context.description}", emoji="�")

        assert isinstance(dialect, SQLDialect), "Invalid dialect type"
        assert isinstance(identifier, str), "Identifier must be a string"
        assert isinstance(context, DatabaseObjectType), "Invalid context type"
        assert correction_method in ["encapsulate", "normalize"], "Invalid correction method"
        assert isinstance(default_prefix_correction, str), "Default prefix correction must be a string"

        # Step 1: strip and convert identifier to ascii since most dialects don't support unicode identifiers
        output: Dict[str, Any] = {
            "valid": True,
            "original": identifier,
            "final": unidecode(identifier.strip()),
            "is_reserved": False,
            "correction_applied": "none",
        }

        formatted_replacement: str = unidecode(default_prefix_correction.strip())

        assert len(output.get("final", "")) > 0, "Identifier cannot be empty after stripping"

        # Step 2: Get dialect rules
        rules: Dict[str, Any] = dialect.identifier_rules.copy()

        rules.update(rules.get("special_rules", {}).get(context, {}))  # apply any special formatting for the context

        # Step 3: Check for invalid prefixes
        reserved_prefix_match = re.search(
            r"^" + r"|".join(rules.get("reserved_prefixes", [])), output.get("final", ""), re.IGNORECASE
        )
        valid_start_char = re.match(rules.get("first_char_rules", r"^."), output.get("final", ""))
        if reserved_prefix_match or (valid_start_char is None):

            if correction_method == "encapsulate":
                output["final"] = SQL_DIALECT_REGISTRY._encapsulate_identifier(dialect, output["final"])
                output["correction_applied"] = "encapsulated"
                logger.debug(
                    f"Identifier '{output.get('final', '')}' starts with {'reserved' if reserved_prefix_match else 'invalid first character'} {reserved_prefix_match.group() if isinstance(reserved_prefix_match, re.Match) else output.get('final', '')[:1]}. Suggestion: either rename identifier or apply autoformatting to maximize compatibility.",
                    emoji="🚨",
                )
            else:
                output["final"] = formatted_replacement + output.get("final", "")

                assert (
                    re.search(
                        r"^" + r"|".join(rules.get("reserved_prefixes", [])), output.get("final", ""), re.IGNORECASE
                    )
                    is None
                ), f"Identifier prefix replacement {output.get('final', '')} starts with reserved prefix"

                logger.debug(
                    f"Identifier '{output.get('final', '')}' starts with {'reserved' if reserved_prefix_match else 'invalid first character'} {reserved_prefix_match.group() if isinstance(reserved_prefix_match, re.Match) else output.get('final', '')[:1]}. {formatted_replacement} prefix added",
                    emoji="🔧",
                )
                output["correction_applied"] = "autoformatted"
                output["final"] = formatted_replacement + output.get("final", "")

        # Step 4: Check case sensitivity and apply case conversion if needed
        # 4.1: Check if the identifier is case sensitive
        # 4.2: Check if case_conversion is applied
        # 4.3: Check if the identifier is in the correct case case
        if rules.get("case_sensitive", False) or isinstance(rules.get("case_conversion", None), str):
            consider_encapsulate: bool = (
                rules.get("quoted_case_sensitive", False)
                and (output.get("correction_applied", "") != "encapsulated")
                and (correction_method == "encapsulate")
            )
            should_encapsulate: bool = False
            if rules.get("case_conversion") == "upper":
                if not output.get("final", "").isupper():
                    if consider_encapsulate:
                        should_encapsulate = True
                    else:
                        output["final"] = output.get("final", "").upper()
                        logger.debug(
                            f"Applied case conversion to upper: '{identifier}' -> '{output.get('final', '')}'",
                            emoji="🔠",
                        )
            else:
                if not output.get("final", "").islower():
                    if consider_encapsulate:
                        should_encapsulate = True
                    else:
                        output["final"] = camel_to_snake_case(output.get("final", "").lower(), preserve_acronyms=True)
                        logger.debug(
                            f"Applied case conversion to lower: '{identifier}' -> '{output.get('final', '')}'",
                            emoji="🔠",
                        )

            if should_encapsulate:
                output["final"] = SQL_DIALECT_REGISTRY._encapsulate_identifier(dialect, output.get("final", ""))
                output["correction_applied"] = "encapsulated"

        # Step 5: Check for reserved words
        if SQL_DIALECT_REGISTRY.is_reserved_word(dialect, context, output.get("final", "")):

            output["is_reserved"] = True

            if correction_method == "encapsulate":
                # If encapsulation is allowed, encapsulate the identifier
                logger.debug(
                    f"Identifier '{output.get('final', '')}' Is a reserved word. Suggestion: Rename identifier.",
                    emoji="🚨",
                )
                if output.get("correction_applied", "") != "encapsulated":
                    output["final"] = SQL_DIALECT_REGISTRY._encapsulate_identifier(dialect, output.get("final", ""))
                    output["correction_applied"] = "encapsulated"
            else:
                # If encapsulation is not allowed, append suffix
                output["final"] = output.get("final", "") + (
                    "_col".upper() if rules.get("case_conversion") == "upper" else "_col"
                )
                logger.warning(
                    f"Identifier '{output.get('final', '')}' is a reserved word in {dialect.description} for {context.description}. Added _col suffix for safety",
                    emoji="🔧",
                )

        # Step 6: Check for general invalid characters
        valid_raw = re.search(rules.get("allowed_chars", {}).get("raw", r"^.+$"), output.get("final", ""))
        invalid_encapsulated = re.search(
            r"|".join(rules.get("allowed_chars", {}).get("encapsulated", [r"^.+$"])), output.get("final", "")
        )

        if valid_raw or ((invalid_encapsulated is None) and (output.get("correction_applied", "") == "encapsulated")):
            pass  # Identifier is valid
        elif correction_method == "encapsulate":
            if invalid_encapsulated is not None:
                logger.debug(
                    f"Identifier '{output.get('final', '')}' contains invalid characters. Encapsulated to preserve original identifier after removal of invalid characters.",
                    emoji="🚨",
                )
                output["final"] = re.sub(
                    r"|".join(rules.get("allowed_chars", {}).get("encapsulated", [r"^.+$"])),
                    "",
                    output.get("final", ""),
                )

            if output.get("correction_applied", "") != "encapsulated":
                # If encapsulation is allowed, encapsulate the identifier to preserve original identifier, only do this if not done already
                output["final"] = SQL_DIALECT_REGISTRY._encapsulate_identifier(dialect, output.get("final", ""))
                output["correction_applied"] = "encapsulated"
        else:
            # keep all of the valid characters and remove the invalid characters
            temp = "".join(re.findall(rules.get("allowed_chars", {}).get("raw", r"^.+$")[1:-1], output["final"]))

            logger.debug(
                f"Identifier '{output.get('final', '')}' has invalid characters in {dialect.description}. Stripped invalid characters {output.get('final', '')} --> {temp}",
                emoji="🔧",
            )

            output["final"] = temp

        # Step 7: Check for length issues, since these are ascii characters, we can use the length of the string directly
        max_length = rules.get("max_length")
        if max_length is not None and len(output.get("final", "")) > max_length:

            if output.get("correction_applied", "") == "encapsulated":
                # If encapsulation is allowed, encapsulate the identifier
                output["final"] = (
                    output.get("final", "")[: max_length - 1] + output["final"][-1]
                )  # to preserve the encapsulation
            else:
                # If encapsulation is not allowed, truncate the identifier
                output["final"] = output.get("final", "")[:max_length]

            logger.debug(
                f"Identifier '{output.get('final', '')}' exceeds max length {max_length} by {len(output.get('final', '')) - max_length}. Truncated to {output.get('final', '')}",
                emoji="✂️",
            )

        if output.get("final", "") == "":
            output["valid"] = False
        else:
            output["valid"] = True

        if not isinstance(output.get("correction_applied", None), str) and (
            output.get("final", "") != output.get("original", "")
        ):
            output["correction_applied"] = "normalized"
        return output

    @staticmethod
    def retrieve_datatypes(dialect: SQLDialect) -> Dict[str, Dict[str, OrderedDict]]:
        """
        Retrieve a comprehensive categorization of clean data types organized by category and subcategory.

        Args:
            dialect (Optional[SQLDialect]): Specific dialect to filter types for (None for all types).
                If provided, returns clean enum instances with dialect-specific values resolved.

        Returns:
            Dict[str, Dict[str, OrderedDict]]: Nested dictionary structure:
                - Top level: General categories (numeric, datetime, character, etc.)
                - Second level: Specific subcategories (integers, time_zone_support, etc.)
                - Values: OrderedDict of clean COLUMNDTYPE enum instances sorted by max_bytes (smallest to largest)

        Note:
            When dialect is specified, returns clean enum instances with:
            - Dialect-specific overrides applied
            - No special_properties in metadata
            - Only types supported by the dialect

        Example structure:
        {
            "numeric": {
                "integers": OrderedDict([("TINYINT", clean_tinyint_enum), ...]),
                "decimals": OrderedDict([("DECIMAL", clean_decimal_enum), ...]),
                "floats": OrderedDict([("REAL", clean_real_enum), ...])
            },
            "datetime": {
                "time_zone_support": OrderedDict([("TIMESTAMPTZ", clean_timestamptz_enum), ...]),
                "no_time_zone": OrderedDict([("DATE", clean_date_enum), ...])
            },
            ...
        }
        """

        # Get clean data types based on dialect

        # Lazy import to avoid circular dependency
        try:
            from core.types import COLUMNDTYPE
        except ImportError:
            from ..core.types import COLUMNDTYPE

        # Get clean enum instances for the specified dialect (filtered and resolved)
        clean_enums = COLUMNDTYPE.get_all_clean_enums_for_dialect(dialect)
        data_types = list(clean_enums.values())

        # Initialize the result structure
        result = {
            "numeric": {
                "integers": OrderedDict(),
                "decimals": OrderedDict(),
                "floats": OrderedDict(),
                "money": OrderedDict(),
            },
            "character": {"fixed_length": OrderedDict(), "variable_length": OrderedDict(), "large_text": OrderedDict()},
            "datetime": {"time_zone_support": OrderedDict(), "no_time_zone": OrderedDict(), "intervals": OrderedDict()},
            "binary": {"fixed_length": OrderedDict(), "variable_length": OrderedDict(), "large_objects": OrderedDict()},
            "boolean": {"boolean_types": OrderedDict()},
            "specialized": {
                "json": OrderedDict(),
                "xml": OrderedDict(),
                "uuid": OrderedDict(),
                "geometric": OrderedDict(),
                "network": OrderedDict(),
                "range": OrderedDict(),
                "array": OrderedDict(),
                "structured": OrderedDict(),
                "system": OrderedDict(),
                "other": OrderedDict(),
            },
        }

        # Categorize each data type
        for dtype in data_types:

            category = dtype.category
            has_tz_support = dtype.time_zone_support

            # Numeric types
            if category == "numeric_integer":
                result["numeric"]["integers"][dtype.name] = dtype
            elif category == "numeric_decimal":
                result["numeric"]["decimals"][dtype.name] = dtype
            elif category == "numeric_float":
                result["numeric"]["floats"][dtype.name] = dtype
            elif category == "numeric_money":
                result["numeric"]["money"][dtype.name] = dtype

            # Character/Text types
            elif category == "text_fixed":
                result["character"]["fixed_length"][dtype.name] = dtype
            elif category == "text_variable":
                result["character"]["variable_length"][dtype.name] = dtype
            elif category == "text_large":
                result["character"]["large_text"][dtype.name] = dtype

            # Date/Time types
            elif category in ["date", "time", "datetime"]:
                if has_tz_support:
                    result["datetime"]["time_zone_support"][dtype.name] = dtype
                else:
                    result["datetime"]["no_time_zone"][dtype.name] = dtype
            elif category == "interval":
                result["datetime"]["intervals"][dtype.name] = dtype

            # Binary types - use is_fixed_length method for both clean and original enums
            elif category == "binary":
                if dtype.is_fixed_length(dialect):
                    result["binary"]["fixed_length"][dtype.name] = dtype
                else:
                    result["binary"]["variable_length"][dtype.name] = dtype
            elif category == "binary_large":
                result["binary"]["large_objects"][dtype.name] = dtype

            # Boolean types
            elif category == "boolean":
                result["boolean"]["boolean_types"][dtype.name] = dtype

            # Specialized types
            elif category == "json":
                result["specialized"]["json"][dtype.name] = dtype
            elif category == "xml":
                result["specialized"]["xml"][dtype.name] = dtype
            elif category == "uuid":
                result["specialized"]["uuid"][dtype.name] = dtype
            elif category == "geometric":
                result["specialized"]["geometric"][dtype.name] = dtype
            elif category == "network":
                result["specialized"]["network"][dtype.name] = dtype
            elif category == "range":
                result["specialized"]["range"][dtype.name] = dtype
            elif category == "array":
                result["specialized"]["array"][dtype.name] = dtype
            elif category in ["structured", "semi_structured"]:
                result["specialized"]["structured"][dtype.name] = dtype
            elif category == "system":
                result["specialized"]["system"][dtype.name] = dtype
            else:
                # Catch any uncategorized types
                result["specialized"]["other"][dtype.name] = dtype

        # Sort each subcategory by appropriate metric (smallest to largest)
        for main_category in result:
            for subcategory in result[main_category]:
                # Convert to list of tuples for sorting
                items = list(result[main_category][subcategory].items())

                # Sort by appropriate metric based on category
                def sort_key(item):
                    dtype = item[1]

                    # For numeric decimal types, sort by precision (more meaningful than bytes)
                    if main_category == "numeric" and subcategory == "decimals":
                        sort_val = dtype.max_precision
                    else:
                        # For all other types, sort by max_bytes
                        sort_val = dtype.max_bytes

                    return (sort_val is None, sort_val or float("inf"))

                sorted_items = sorted(items, key=sort_key)

                # Convert back to OrderedDict
                result[main_category][subcategory] = OrderedDict(sorted_items)

        return result
