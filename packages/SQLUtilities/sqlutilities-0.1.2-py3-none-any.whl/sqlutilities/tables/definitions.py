"""
Table Definition Classes

This module contains dataclasses for defining table components.
- ColumnDefinition: Comprehensive column definition
- ConstraintDefinition: Table constraint definition
- IndexDefinition: Index definition
- TableDefinition: Complete table definition

Author: DataScience ToolBox
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# Use try/except to handle both absolute and relative imports
try:
    from core.enums import SQLDialect
    from core.types import COLUMNDTYPE
except ImportError:
    from ..core.enums import SQLDialect
    from ..core.types import COLUMNDTYPE


class TableComponentType(Enum):
    """Types of table components that can be managed."""

    COLUMN = "column"
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    UNIQUE_CONSTRAINT = "unique_constraint"
    CHECK_CONSTRAINT = "check_constraint"
    NOT_NULL_CONSTRAINT = "not_null_constraint"
    DEFAULT_CONSTRAINT = "default_constraint"
    INDEX = "index"
    UNIQUE_INDEX = "unique_index"
    TRIGGER = "trigger"


class TableOperation(Enum):
    """Operations that can be performed on tables and components."""

    CREATE = "create"
    DROP = "drop"
    ALTER = "alter"
    RECREATE = "recreate"
    EXIST_CHECK = "exist_check"
    DESCRIBE = "describe"
    BACKUP = "backup"
    RESTORE = "restore"


@dataclass
class ColumnDefinition:
    """
    Comprehensive definition of a table column with all possible attributes.

    This dataclass defines a database column with support for data type
    specifications, constraints, defaults, identity columns, computed columns,
    and comprehensive metadata. It supports all major SQL dialects with
    dialect-specific attribute handling.

    Parameters
    ----------
    name : str
        Column name
    data_type : COLUMNDTYPE
        Column data type from COLUMNDTYPE enum
    dialect : SQLDialect
        Target SQL dialect for the column
    length : int or str, optional
        Length for character types (VARCHAR, CHAR)
    precision : int, optional
        Precision for numeric types (DECIMAL, NUMERIC)
    scale : int, optional
        Scale for numeric types (DECIMAL, NUMERIC)
    time_precision : int, optional
        Precision for temporal types (0-9: second to nanosecond)
    nullable : bool, default=True
        Whether column allows NULL values
    default_value : str, optional
        Static default value for the column
    default_expression : str, optional
        Dynamic default expression (e.g., CURRENT_TIMESTAMP)
    is_identity : bool, default=False
        Whether column is an identity/auto-increment column
    identity_seed : int, optional
        Starting value for identity column
    identity_increment : int, optional
        Increment value for identity column
    character_set : str, optional
        Character set for string columns
    collation : str, optional
        Collation for string columns
    check_constraint : str, optional
        Check constraint expression for this column
    check_constraint_name : str, optional
        Name for the check constraint
    is_computed : bool, default=False
        Whether this is a computed/generated column
    computed_expression : str, optional
        Expression for computed column
    is_stored : bool, default=False
        Whether computed column is stored (vs virtual)
    comment : str, optional
        Short comment for the column
    description : str, optional
        Extended description for documentation
    ordinal_position : int, optional
        Position of column in table (1-based)
    after_column : str, optional
        For MySQL, position column after specified column
    extra_attributes : dict, default_factory=dict
        Dialect-specific attributes

    Attributes
    ----------
    full_data_type : str
        Complete data type specification including size parameters
    is_string_type : bool
        Whether the column data type is a string/text type

    Examples
    --------
    Simple column definition:
        >>> col = ColumnDefinition(
        ...     name='id',
        ...     data_type=COLUMNDTYPE.INTEGER,
        ...     dialect=SQLDialect.POSTGRESQL,
        ...     is_identity=True,
        ...     nullable=False
        ... )

    Column with length and default:
        >>> col = ColumnDefinition(
        ...     name='email',
        ...     data_type=COLUMNDTYPE.VARCHAR,
        ...     dialect=SQLDialect.MYSQL,
        ...     length=255,
        ...     nullable=False,
        ...     default_expression="'user@example.com'"
        ... )

    Computed column:
        >>> col = ColumnDefinition(
        ...     name='full_name',
        ...     data_type=COLUMNDTYPE.VARCHAR,
        ...     dialect=SQLDialect.SQLSERVER,
        ...     is_computed=True,
        ...     computed_expression='first_name + \' \' + last_name',
        ...     is_stored=True
        ... )

    Notes
    -----
    Primary key, foreign key, and unique constraints should be defined
    separately using ConstraintDefinition for proper constraint management.
    """

    # Core column properties
    name: str
    data_type: COLUMNDTYPE
    dialect: SQLDialect

    # Data type specifications
    length: Optional[int | str] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    time_precision: Optional[int] = (
        None  # For temporal types (0-9, where 0=second, 3=millisecond, 6=microsecond, 9=nanosecond)
    )

    # Nullability and defaults
    nullable: bool = True
    default_value: Optional[str] = None
    default_expression: Optional[str] = None  # For computed defaults like CURRENT_TIMESTAMP

    # Identity/Auto-increment settings
    is_identity: bool = False
    identity_seed: Optional[int] = 1  # Starting value for identity
    identity_increment: Optional[int] = 1  # Increment value for identity

    # Character set and collation (for string types)
    character_set: Optional[str] = None
    collation: Optional[str] = None

    # Column-level check constraint
    check_constraint: Optional[str] = None
    check_constraint_name: Optional[str] = None

    # Generated/computed columns
    is_computed: bool = False
    computed_expression: Optional[str] = None
    is_stored: bool = False  # Whether computed column is stored or virtual

    # Column metadata
    comment: Optional[str] = None
    description: Optional[str] = None  # Extended description for documentation

    # Column ordering and positioning
    ordinal_position: Optional[int] = None
    after_column: Optional[str] = None  # For MySQL ALTER TABLE ... ADD COLUMN ... AFTER

    # Dialect-specific attributes
    extra_attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate column definition after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Column name cannot be empty")

        if self.is_identity and self.default_value:
            raise ValueError("Identity columns cannot have default values")

        if self.is_computed and not self.computed_expression:
            raise ValueError("Computed columns must have a computed_expression")

        if self.default_value and self.default_expression:
            raise ValueError("Column cannot have both default_value and default_expression")

        if self.precision is not None and self.precision <= 0:
            raise ValueError("Precision must be positive")

        if self.scale is not None and self.scale < 0:
            raise ValueError("Scale cannot be negative")

        if self.scale is not None and self.precision is not None and self.scale > self.precision:
            raise ValueError("Scale cannot be greater than precision")

    @property
    def full_data_type(
        self,
    ) -> str:
        """Get the complete data type specification including size parameters."""
        return COLUMNDTYPE.to_sql_string(
            datatype=self.data_type,
            target_dialect=self.dialect,
            size_spec=(
                (self.precision, self.scale)
                if isinstance(self.precision, int) and isinstance(self.scale, int)
                else (
                    self.precision
                    if isinstance(self.precision, int)
                    else self.length if isinstance(self.length, (int | str)) else None
                )
            ),
        )

    @property
    def is_string_type(self) -> bool:
        """Check if the column data type is a string/text type."""
        string_types = {
            COLUMNDTYPE.VARCHAR,
            COLUMNDTYPE.CHAR,
            COLUMNDTYPE.TEXT,
            COLUMNDTYPE.NVARCHAR,
            COLUMNDTYPE.NCHAR,
            COLUMNDTYPE.CHARACTER,
            COLUMNDTYPE.LONGTEXT,
            COLUMNDTYPE.MEDIUMTEXT,
            COLUMNDTYPE.TINYTEXT,
            COLUMNDTYPE.VARCHAR2,
            COLUMNDTYPE.NVARCHAR2,
            COLUMNDTYPE.NCLOB,
        }
        return self.data_type in string_types


@dataclass
class ConstraintDefinition:
    """Definition of a table constraint."""

    name: str
    constraint_type: TableComponentType
    columns: List[str]
    reference_table: Optional[str] = None
    reference_columns: Optional[List[str]] = None
    check_expression: Optional[str] = None
    on_delete: Optional[str] = None
    on_update: Optional[str] = None


@dataclass
class IndexDefinition:
    """Definition of a table index."""

    name: str
    columns: List[str]
    is_unique: bool = False
    is_clustered: bool = False
    is_partial: bool = False
    where_clause: Optional[str] = None
    include_columns: Optional[List[str]] = None
    fill_factor: Optional[int] = None


@dataclass
class TableDefinition:
    """Complete definition of a table."""

    name: str
    schema: Optional[str] = None
    columns: List[ColumnDefinition] = field(default_factory=list)
    constraints: List[ConstraintDefinition] = field(default_factory=list)
    indexes: List[IndexDefinition] = field(default_factory=list)
    comment: Optional[str] = None
    tablespace: Optional[str] = None
