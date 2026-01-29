"""
Unit tests for core.enums module.

Tests for:
- SQLDialect enum
- DatabaseObjectType enum
- Dialect properties and metadata
"""

import pytest

from sqlutilities.core import DatabaseObjectType, SQLDialect


class TestSQLDialect:
    """Test cases for SQLDialect enum."""

    @pytest.mark.unit
    def test_all_dialects_exist(self):
        """Test that all expected dialects are defined."""
        expected_dialects = ["MYSQL", "POSTGRES", "ORACLE", "SQLSERVER", "BIGQUERY", "REDSHIFT", "SQLITE"]

        for dialect_name in expected_dialects:
            assert hasattr(SQLDialect, dialect_name), f"SQLDialect.{dialect_name} not found"

    @pytest.mark.unit
    def test_dialect_has_description(self, all_dialects):
        """Test that each dialect has a description."""
        for dialect in all_dialects:
            assert hasattr(dialect, "description"), f"{dialect.name} missing description"
            assert isinstance(dialect.description, str), f"{dialect.name} description not a string"
            assert len(dialect.description) > 0, f"{dialect.name} description is empty"

    @pytest.mark.unit
    def test_dialect_has_quote_character(self, all_dialects):
        """Test that each dialect has a quote character."""
        for dialect in all_dialects:
            assert hasattr(dialect, "quote_character"), f"{dialect.name} missing quote_character"
            assert isinstance(dialect.quote_character, str), f"{dialect.name} quote_character not a string"
            assert len(dialect.quote_character) > 0, f"{dialect.name} quote_character is empty"

    @pytest.mark.unit
    def test_dialect_has_identifier_rules(self, all_dialects):
        """Test that each dialect has identifier rules."""
        for dialect in all_dialects:
            assert hasattr(dialect, "identifier_rules"), f"{dialect.name} missing identifier_rules"
            rules = dialect.identifier_rules
            assert isinstance(rules, dict), f"{dialect.name} identifier_rules not a dict"

            # Check required keys in identifier rules
            required_keys = ["max_length", "case_sensitive", "allowed_chars"]
            for key in required_keys:
                assert key in rules, f"{dialect.name} identifier_rules missing '{key}'"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "dialect,expected_quote",
        [
            (SQLDialect.MYSQL, "`"),
            (SQLDialect.POSTGRES, '"'),
            (SQLDialect.ORACLE, '"'),
            (SQLDialect.SQLSERVER, '"'),
            (SQLDialect.BIGQUERY, "`"),
            (SQLDialect.REDSHIFT, '"'),
            (SQLDialect.SQLITE, '"'),
        ],
    )
    def test_dialect_specific_quote_characters(self, dialect, expected_quote):
        """Test that each dialect has the correct quote character."""
        assert dialect.quote_character == expected_quote

    @pytest.mark.unit
    def test_dialect_equality(self):
        """Test dialect equality comparison."""
        assert SQLDialect.MYSQL == SQLDialect.MYSQL
        assert SQLDialect.POSTGRES != SQLDialect.MYSQL

    @pytest.mark.unit
    def test_dialect_name_property(self, all_dialects):
        """Test that dialect name property returns correct value."""
        for dialect in all_dialects:
            assert isinstance(dialect.name, str)
            assert dialect.name == dialect.name.upper()

    @pytest.mark.unit
    def test_dialect_value_is_tuple(self, all_dialects):
        """Test that dialect values are tuples with metadata."""
        for dialect in all_dialects:
            assert isinstance(dialect.value, tuple)
            assert len(dialect.value) >= 2  # At least name and metadata dict

    @pytest.mark.unit
    def test_resolved_alias(self, all_dialects):
        """Test that resolved_alias property works."""
        for dialect in all_dialects:
            resolved = dialect.resolved_alias
            assert isinstance(resolved, SQLDialect)


class TestDatabaseObjectType:
    """Test cases for DatabaseObjectType enum."""

    @pytest.mark.unit
    def test_common_object_types_exist(self):
        """Test that common database object types are defined."""
        expected_types = [
            "TABLE",
            "COLUMN",
            "VIEW",
            "INDEX",
            "SCHEMA",
            "DATABASE",
            "CONSTRAINT",
            "PRIMARY_KEY",
            "FOREIGN_KEY",
        ]

        for obj_type in expected_types:
            assert hasattr(DatabaseObjectType, obj_type), f"DatabaseObjectType.{obj_type} not found"

    @pytest.mark.unit
    def test_object_type_has_description(self):
        """Test that each object type has a description."""
        for obj_type in DatabaseObjectType:
            assert hasattr(obj_type, "description"), f"{obj_type.name} missing description"
            assert isinstance(obj_type.description, str), f"{obj_type.name} description not a string"

    @pytest.mark.unit
    def test_object_type_equality(self):
        """Test object type equality comparison."""
        assert DatabaseObjectType.TABLE == DatabaseObjectType.TABLE
        assert DatabaseObjectType.TABLE != DatabaseObjectType.VIEW

    @pytest.mark.unit
    def test_object_type_value_is_tuple(self):
        """Test that object type values are tuples."""
        for obj_type in DatabaseObjectType:
            assert isinstance(obj_type.value, tuple)
            assert len(obj_type.value) == 2  # Name and description

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "obj_type,expected_value",
        [
            (DatabaseObjectType.TABLE, "table"),
            (DatabaseObjectType.COLUMN, "column"),
            (DatabaseObjectType.VIEW, "view"),
            (DatabaseObjectType.INDEX, "index"),
        ],
    )
    def test_specific_object_type_values(self, obj_type, expected_value):
        """Test that specific object types have expected values."""
        assert obj_type.value[0] == expected_value


class TestDialectCompatibility:
    """Test dialect compatibility and feature support."""

    @pytest.mark.unit
    def test_all_dialects_have_unique_names(self, all_dialects):
        """Test that all dialect names are unique."""
        names = [dialect.name for dialect in all_dialects]
        assert len(names) == len(set(names)), "Duplicate dialect names found"

    @pytest.mark.unit
    def test_dialect_identifier_max_length(self, all_dialects):
        """Test that each dialect specifies a maximum identifier length."""
        for dialect in all_dialects:
            max_length = dialect.identifier_rules.get("max_length")
            assert max_length is None or isinstance(max_length, int), f"{dialect.name} max_length should be None or int"
            if max_length is not None:
                assert max_length > 0, f"{dialect.name} max_length should be positive"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "dialect,expected_case_sensitive",
        [
            (SQLDialect.MYSQL, False),
            (SQLDialect.POSTGRES, True),
            (SQLDialect.ORACLE, False),
            (SQLDialect.SQLSERVER, False),
        ],
    )
    def test_dialect_case_sensitivity(self, dialect, expected_case_sensitive):
        """Test dialect case sensitivity settings."""
        case_sensitive = dialect.identifier_rules.get("case_sensitive", False)
        assert case_sensitive == expected_case_sensitive, f"{dialect.name} case sensitivity mismatch"

    @pytest.mark.unit
    def test_dialect_allowed_chars_pattern(self, all_dialects):
        """Test that allowed_chars contains valid regex patterns."""
        import re

        for dialect in all_dialects:
            allowed_chars = dialect.identifier_rules.get("allowed_chars", {})
            assert isinstance(allowed_chars, dict), f"{dialect.name} allowed_chars should be a dict"

            # Test that 'raw' pattern is valid regex
            if "raw" in allowed_chars:
                try:
                    re.compile(allowed_chars["raw"])
                except re.error as e:
                    pytest.fail(f"{dialect.name} 'raw' pattern is invalid regex: {e}")
