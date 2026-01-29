"""
Unit tests for validation.identifiers module.

Tests for:
- SQL_DIALECT_REGISTRY class
- Identifier validation and normalization
- Reserved word checking
- Dialect-specific identifier rules
"""

import pytest

from sqlutilities.core import DatabaseObjectType, SQLDialect
from sqlutilities.validation import SQL_DIALECT_REGISTRY


class TestSQLDialectRegistry:
    """Test cases for SQL_DIALECT_REGISTRY class."""

    @pytest.mark.unit
    def test_registry_class_exists(self):
        """Test that SQL_DIALECT_REGISTRY class exists."""
        assert SQL_DIALECT_REGISTRY is not None

    @pytest.mark.unit
    def test_get_reserved_words(self, all_dialects):
        """Test retrieving reserved words for each dialect."""
        for dialect in all_dialects:
            reserved_words = SQL_DIALECT_REGISTRY.get(dialect, "reserved_words")

            assert reserved_words is not None, f"{dialect.name} has no reserved words"
            assert isinstance(reserved_words, set), f"{dialect.name} reserved_words should be a set"
            assert len(reserved_words) > 0, f"{dialect.name} should have reserved words"

    @pytest.mark.unit
    def test_common_reserved_words(self, all_dialects):
        """Test that common SQL keywords are reserved in all dialects."""
        common_keywords = ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE"]

        for dialect in all_dialects:
            reserved_words = SQL_DIALECT_REGISTRY.get(dialect, "reserved_words")

            for keyword in common_keywords:
                assert keyword in reserved_words, f"{keyword} should be reserved in {dialect.name}"

    @pytest.mark.unit
    def test_get_dialect_objects(self, all_dialects):
        """Test retrieving supported objects for each dialect."""
        for dialect in all_dialects:
            objects = SQL_DIALECT_REGISTRY.get(dialect, "objects")

            assert objects is not None, f"{dialect.name} has no objects"
            assert isinstance(objects, set), f"{dialect.name} objects should be a set"

            # Common objects should be supported
            assert DatabaseObjectType.TABLE in objects, f"{dialect.name} should support TABLE"
            assert DatabaseObjectType.COLUMN in objects, f"{dialect.name} should support COLUMN"

    @pytest.mark.unit
    def test_get_identifier_rules(self, all_dialects):
        """Test retrieving identifier rules for each dialect."""
        for dialect in all_dialects:
            rules = SQL_DIALECT_REGISTRY.get(dialect, "identifier_rules")

            assert rules is not None, f"{dialect.name} has no identifier rules"
            assert isinstance(rules, dict), f"{dialect.name} identifier_rules should be a dict"

            # Check required keys
            required_keys = ["max_length", "case_sensitive", "allowed_chars"]
            for key in required_keys:
                assert key in rules, f"{dialect.name} identifier_rules missing '{key}'"


class TestReservedWordChecking:
    """Test reserved word detection."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "dialect,keyword",
        [
            (SQLDialect.MYSQL, "SELECT"),
            (SQLDialect.POSTGRES, "WHERE"),
            (SQLDialect.ORACLE, "TABLE"),
            (SQLDialect.SQLSERVER, "INDEX"),
        ],
    )
    def test_is_reserved_word_common_keywords(self, dialect, keyword):
        """Test that common SQL keywords are detected as reserved."""
        is_reserved = SQL_DIALECT_REGISTRY.is_reserved_word(dialect, DatabaseObjectType.TABLE, keyword)
        assert is_reserved, f"{keyword} should be reserved in {dialect.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "dialect,identifier",
        [
            (SQLDialect.MYSQL, "my_table"),
            (SQLDialect.POSTGRES, "user_data"),
            (SQLDialect.ORACLE, "employee_records"),
            (SQLDialect.SQLSERVER, "order_items"),
        ],
    )
    def test_is_not_reserved_word_valid_identifiers(self, dialect, identifier):
        """Test that valid identifiers are not detected as reserved."""
        is_reserved = SQL_DIALECT_REGISTRY.is_reserved_word(dialect, DatabaseObjectType.TABLE, identifier)
        assert not is_reserved, f"{identifier} should not be reserved in {dialect.name}"

    @pytest.mark.unit
    def test_case_insensitive_reserved_check(self):
        """Test that reserved word checking is case-insensitive."""
        variants = ["SELECT", "select", "Select", "SeLeCt"]

        for variant in variants:
            is_reserved = SQL_DIALECT_REGISTRY.is_reserved_word(SQLDialect.MYSQL, DatabaseObjectType.TABLE, variant)
            assert is_reserved, f"{variant} should be detected as reserved"

    @pytest.mark.unit
    def test_context_specific_exemptions(self):
        """Test that context-specific exemptions work."""
        # Some dialects allow certain reserved words in specific contexts
        # This is dialect-specific behavior
        exemptions = SQL_DIALECT_REGISTRY.get(SQLDialect.SQLITE, "context_exemptions")

        assert isinstance(exemptions, dict), "Context exemptions should be a dict"


class TestIdentifierValidation:
    """Test identifier validation and normalization."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "dialect,identifier",
        [
            (SQLDialect.MYSQL, "valid_table_name"),
            (SQLDialect.POSTGRES, "user_table"),
            (SQLDialect.ORACLE, "EMPLOYEES"),
            (SQLDialect.SQLSERVER, "OrderDetails"),
        ],
    )
    def test_validate_valid_identifiers(self, dialect, identifier):
        """Test validation of valid identifiers."""
        result = SQL_DIALECT_REGISTRY.validate_identifier(dialect, identifier, DatabaseObjectType.TABLE)

        assert result["valid"], f"{identifier} should be valid for {dialect.name}"
        assert result["original"] == identifier, "Original identifier should be preserved"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "dialect,identifier",
        [
            (SQLDialect.MYSQL, "SELECT"),  # Reserved word
            (SQLDialect.POSTGRES, "123table"),  # Starts with digit
            (SQLDialect.ORACLE, "table-name"),  # Invalid character
        ],
    )
    def test_validate_problematic_identifiers(self, dialect, identifier):
        """Test validation of problematic identifiers."""
        result = SQL_DIALECT_REGISTRY.validate_identifier(
            dialect, identifier, DatabaseObjectType.TABLE, correction_method="normalize"
        )

        # Should apply corrections
        assert "final" in result, "Result should have 'final' key"
        assert "correction_applied" in result, "Result should have 'correction_applied' key"

    @pytest.mark.unit
    @pytest.mark.parametrize("dialect", [SQLDialect.MYSQL, SQLDialect.POSTGRES, SQLDialect.ORACLE])
    def test_encapsulation_correction(self, dialect):
        """Test identifier encapsulation for reserved words."""
        result = SQL_DIALECT_REGISTRY.validate_identifier(
            dialect, "SELECT", DatabaseObjectType.TABLE, correction_method="encapsulate"
        )

        # Should encapsulate the identifier
        assert result["correction_applied"] == "encapsulated", f"Should encapsulate reserved word for {dialect.name}"

        # Final identifier should be quoted
        quote_char = dialect.quote_character
        assert result["final"].startswith(quote_char) and result["final"].endswith(
            quote_char
        ), f"Encapsulated identifier should be quoted with {quote_char}"

    @pytest.mark.unit
    def test_normalize_correction(self):
        """Test identifier normalization."""
        result = SQL_DIALECT_REGISTRY.validate_identifier(
            SQLDialect.MYSQL,
            "123invalid",
            DatabaseObjectType.TABLE,
            correction_method="normalize",
            default_prefix_correction="tbl_",
        )

        # Should add prefix to fix invalid start
        assert result["final"].startswith("tbl_"), "Should add prefix to fix invalid identifier"

    @pytest.mark.unit
    def test_validation_result_structure(self):
        """Test that validation result has expected structure."""
        result = SQL_DIALECT_REGISTRY.validate_identifier(SQLDialect.MYSQL, "test_table", DatabaseObjectType.TABLE)

        required_keys = ["valid", "original", "final", "is_reserved", "correction_applied"]
        for key in required_keys:
            assert key in result, f"Validation result missing '{key}'"

        # Check types
        assert isinstance(result["valid"], bool)
        assert isinstance(result["original"], str)
        assert isinstance(result["final"], str)
        assert isinstance(result["is_reserved"], bool)
        assert isinstance(result["correction_applied"], str)

    @pytest.mark.unit
    @pytest.mark.parametrize("dialect", [SQLDialect.MYSQL, SQLDialect.POSTGRES, SQLDialect.ORACLE])
    def test_max_length_enforcement(self, dialect):
        """Test that max length is enforced."""
        rules = SQL_DIALECT_REGISTRY.get(dialect, "identifier_rules")
        max_length = rules.get("max_length")

        if max_length:
            # Create identifier longer than max
            long_identifier = "a" * (max_length + 10)

            result = SQL_DIALECT_REGISTRY.validate_identifier(dialect, long_identifier, DatabaseObjectType.TABLE)

            # Should truncate to max length
            assert (
                len(result["final"]) <= max_length
            ), f"Identifier should be truncated to {max_length} for {dialect.name}"

    @pytest.mark.unit
    def test_unicode_handling(self):
        """Test handling of unicode characters in identifiers."""
        unicode_identifier = "tábla_üñíçødé"

        result = SQL_DIALECT_REGISTRY.validate_identifier(
            SQLDialect.MYSQL, unicode_identifier, DatabaseObjectType.TABLE
        )

        # Should convert to ASCII (unidecode)
        assert result["final"].isascii(), "Unicode should be converted to ASCII"

    @pytest.mark.unit
    def test_empty_identifier_handling(self):
        """Test that empty identifiers are rejected."""
        with pytest.raises(AssertionError):
            SQL_DIALECT_REGISTRY.validate_identifier(SQLDialect.MYSQL, "", DatabaseObjectType.TABLE)

    @pytest.mark.unit
    def test_whitespace_stripping(self):
        """Test that leading/trailing whitespace is stripped."""
        result = SQL_DIALECT_REGISTRY.validate_identifier(SQLDialect.MYSQL, "  test_table  ", DatabaseObjectType.TABLE)

        assert not result["final"].startswith(" "), "Leading whitespace should be stripped"
        assert not result["final"].endswith(" "), "Trailing whitespace should be stripped"


class TestDialectSpecificBehavior:
    """Test dialect-specific identifier behavior."""

    @pytest.mark.unit
    @pytest.mark.mysql
    def test_mysql_backtick_encapsulation(self):
        """Test MySQL uses backticks for encapsulation."""
        result = SQL_DIALECT_REGISTRY.validate_identifier(
            SQLDialect.MYSQL, "SELECT", DatabaseObjectType.TABLE, correction_method="encapsulate"
        )

        assert result["final"].startswith("`") and result["final"].endswith("`"), "MySQL should use backticks"

    @pytest.mark.unit
    @pytest.mark.postgres
    def test_postgres_double_quote_encapsulation(self):
        """Test PostgreSQL uses double quotes for encapsulation."""
        result = SQL_DIALECT_REGISTRY.validate_identifier(
            SQLDialect.POSTGRES, "SELECT", DatabaseObjectType.TABLE, correction_method="encapsulate"
        )

        assert result["final"].startswith('"') and result["final"].endswith('"'), "PostgreSQL should use double quotes"

    @pytest.mark.unit
    @pytest.mark.oracle
    def test_oracle_case_conversion(self):
        """Test Oracle identifier case handling."""
        rules = SQL_DIALECT_REGISTRY.get(SQLDialect.ORACLE, "identifier_rules")

        # Oracle typically converts unquoted identifiers to uppercase
        if rules.get("case_conversion") == "upper":
            result = SQL_DIALECT_REGISTRY.validate_identifier(
                SQLDialect.ORACLE, "table_name", DatabaseObjectType.TABLE, correction_method="normalize"
            )

            assert result["final"].isupper(), "Oracle should convert identifiers to uppercase"


class TestDataTypeRetrieval:
    """Test data type retrieval and categorization."""

    @pytest.mark.unit
    def test_retrieve_datatypes_all_dialects(self, all_dialects):
        """Test retrieving data types for all dialects."""
        for dialect in all_dialects:
            datatypes = SQL_DIALECT_REGISTRY.retrieve_datatypes(dialect)

            assert datatypes is not None, f"Should retrieve datatypes for {dialect.name}"
            assert isinstance(datatypes, dict), f"Datatypes should be a dict for {dialect.name}"

    @pytest.mark.unit
    def test_retrieve_datatypes_structure(self):
        """Test the structure of retrieved datatypes."""
        datatypes = SQL_DIALECT_REGISTRY.retrieve_datatypes(SQLDialect.MYSQL)

        # Should have main categories
        expected_categories = ["numeric", "character", "datetime", "binary", "boolean"]

        for category in expected_categories:
            assert category in datatypes, f"Missing category: {category}"
            assert isinstance(datatypes[category], dict), f"Category {category} should be a dict"

    @pytest.mark.unit
    def test_retrieve_datatypes_numeric_subcategories(self):
        """Test numeric type subcategories."""
        datatypes = SQL_DIALECT_REGISTRY.retrieve_datatypes(SQLDialect.POSTGRES)

        numeric_types = datatypes.get("numeric", {})
        expected_subcategories = ["integers", "decimals", "floats"]

        for subcat in expected_subcategories:
            assert subcat in numeric_types, f"Numeric types missing subcategory: {subcat}"

    @pytest.mark.unit
    def test_retrieve_datatypes_character_subcategories(self):
        """Test character type subcategories."""
        datatypes = SQL_DIALECT_REGISTRY.retrieve_datatypes(SQLDialect.MYSQL)

        character_types = datatypes.get("character", {})
        expected_subcategories = ["fixed_length", "variable_length", "large_text"]

        for subcat in expected_subcategories:
            assert subcat in character_types, f"Character types missing subcategory: {subcat}"
