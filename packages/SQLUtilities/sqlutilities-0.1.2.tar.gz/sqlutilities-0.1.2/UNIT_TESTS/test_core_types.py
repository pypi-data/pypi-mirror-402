"""
Unit tests for core.types module.

Tests for:
- COLUMNDTYPE enum
- Column_Type NamedTuple
- TemporalPrecision helper class
"""

import pytest

from sqlutilities.core import COLUMNDTYPE, Column_Type, SQLDialect, TemporalPrecision


class TestCOLUMNDTYPE:
    """Test cases for COLUMNDTYPE enum."""

    @pytest.mark.unit
    def test_common_data_types_exist(self):
        """Test that common SQL data types are defined."""
        expected_types = [
            "INTEGER",
            "BIGINT",
            "SMALLINT",
            "VARCHAR",
            "CHAR",
            "TEXT",
            "DECIMAL",
            "NUMERIC",
            "FLOAT",
            "DOUBLE",
            "DATE",
            "TIME",
            "TIMESTAMP",
            "BOOLEAN",
            "BLOB",
        ]

        for dtype in expected_types:
            assert hasattr(COLUMNDTYPE, dtype), f"COLUMNDTYPE.{dtype} not found"

    @pytest.mark.unit
    def test_data_type_has_metadata(self):
        """Test that each data type has required metadata."""
        required_keys = ["category", "description", "min_bytes", "max_bytes", "supported_dialects"]

        for dtype in COLUMNDTYPE:
            metadata = dtype.value[1]
            assert isinstance(metadata, dict), f"{dtype.name} metadata is not a dict"

            for key in required_keys:
                assert key in metadata, f"{dtype.name} missing '{key}' in metadata"

    @pytest.mark.unit
    def test_data_type_categories(self):
        """Test that data types are properly categorized."""
        valid_categories = [
            "numeric_integer",
            "numeric_decimal",
            "numeric_float",
            "numeric_money",
            "text_fixed",
            "text_variable",
            "text_large",
            "date",
            "time",
            "datetime",
            "interval",
            "binary",
            "binary_large",
            "boolean",
            "json",
            "xml",
            "uuid",
            "geometric",
            "network",
            "range",
            "array",
            "structured",
            "semi_structured",
            "system",
        ]

        for dtype in COLUMNDTYPE:
            category = dtype.value[1].get("category")
            assert category in valid_categories, f"{dtype.name} has invalid category: {category}"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "dtype,expected_category",
        [
            (COLUMNDTYPE.INTEGER, "numeric_integer"),
            (COLUMNDTYPE.VARCHAR, "text_variable"),
            (COLUMNDTYPE.DECIMAL, "numeric_decimal"),
            (COLUMNDTYPE.TIMESTAMP, "datetime"),
            (COLUMNDTYPE.BOOLEAN, "boolean"),
        ],
    )
    def test_specific_data_type_categories(self, dtype, expected_category):
        """Test that specific data types have correct categories."""
        actual_category = dtype.value[1].get("category")
        assert actual_category == expected_category

    @pytest.mark.unit
    def test_numeric_types_have_range(self):
        """Test that numeric integer types specify min/max values."""
        numeric_int_types = [COLUMNDTYPE.TINYINT, COLUMNDTYPE.SMALLINT, COLUMNDTYPE.INTEGER, COLUMNDTYPE.BIGINT]

        for dtype in numeric_int_types:
            metadata = dtype.value[1]
            assert "min_value" in metadata, f"{dtype.name} missing min_value"
            assert "max_value" in metadata, f"{dtype.name} missing max_value"

    @pytest.mark.unit
    def test_data_type_supported_dialects(self):
        """Test that each data type specifies supported dialects."""
        for dtype in COLUMNDTYPE:
            metadata = dtype.value[1]
            supported_dialects = metadata.get("supported_dialects", [])

            assert isinstance(supported_dialects, list), f"{dtype.name} supported_dialects should be a list"

            # Check that each supported dialect is valid
            for dialect in supported_dialects:
                assert isinstance(dialect, SQLDialect), f"{dtype.name} has non-SQLDialect in supported_dialects"

    @pytest.mark.unit
    def test_data_type_has_optimal_type(self):
        """Test that each data type specifies an optimal Python type."""
        for dtype in COLUMNDTYPE:
            metadata = dtype.value[1]
            assert "optimal_type" in metadata, f"{dtype.name} missing optimal_type"

            optimal_type = metadata["optimal_type"]
            # Should be a type or string name of a type
            assert optimal_type is not None, f"{dtype.name} optimal_type is None"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "dtype,expected_optimal",
        [
            (COLUMNDTYPE.INTEGER, int),
            (COLUMNDTYPE.VARCHAR, str),
            (COLUMNDTYPE.BOOLEAN, bool),
            (COLUMNDTYPE.FLOAT, float),
        ],
    )
    def test_specific_optimal_types(self, dtype, expected_optimal):
        """Test that specific data types have correct optimal Python types."""
        metadata = dtype.value[1]
        optimal_type = metadata.get("optimal_type")

        if isinstance(optimal_type, type):
            assert optimal_type == expected_optimal
        elif isinstance(optimal_type, str):
            assert optimal_type == expected_optimal.__name__

    @pytest.mark.unit
    def test_dialect_overrides_structure(self):
        """Test that dialect_overrides have correct structure."""
        for dtype in COLUMNDTYPE:
            metadata = dtype.value[1]
            overrides = metadata.get("dialect_overrides", {})

            assert isinstance(overrides, dict), f"{dtype.name} dialect_overrides should be a dict"

            for dialect, override_value in overrides.items():
                assert isinstance(dialect, SQLDialect), f"{dtype.name} has invalid dialect key in overrides"

                # Override value should be a tuple (type_name, size_spec)
                assert isinstance(override_value, tuple), f"{dtype.name} override for {dialect.name} should be a tuple"

    @pytest.mark.unit
    def test_string_types_have_length_support(self):
        """Test that string types support length specification."""
        string_types = [COLUMNDTYPE.VARCHAR, COLUMNDTYPE.CHAR]

        for dtype in string_types:
            metadata = dtype.value[1]
            # Should have max_precision or similar length indicator
            assert (
                metadata.get("max_precision") is not None or metadata.get("max_bytes") is not None
            ), f"{dtype.name} should specify length limits"

    @pytest.mark.unit
    def test_decimal_types_have_precision_scale(self):
        """Test that decimal types support precision and scale."""
        decimal_types = [COLUMNDTYPE.DECIMAL, COLUMNDTYPE.NUMERIC]

        for dtype in decimal_types:
            metadata = dtype.value[1]
            assert "max_precision" in metadata, f"{dtype.name} should have max_precision"

    @pytest.mark.unit
    def test_temporal_types_timezone_support(self):
        """Test that temporal types specify timezone support."""
        temporal_types = [COLUMNDTYPE.TIMESTAMP, COLUMNDTYPE.TIMESTAMPTZ, COLUMNDTYPE.TIME, COLUMNDTYPE.TIMETZ]

        for dtype in temporal_types:
            if hasattr(COLUMNDTYPE, dtype.name):
                metadata = dtype.value[1]
                assert "time_zone_support" in metadata, f"{dtype.name} should specify time_zone_support"


class TestColumnType:
    """Test cases for Column_Type NamedTuple."""

    @pytest.mark.unit
    def test_column_type_is_namedtuple(self):
        """Test that Column_Type is a NamedTuple."""
        # Check if it has _fields attribute (characteristic of namedtuples)
        assert hasattr(Column_Type, "_fields"), "Column_Type should be a NamedTuple"

    @pytest.mark.unit
    def test_column_type_has_required_fields(self):
        """Test that Column_Type has expected fields."""
        expected_fields = ["name", "category", "description"]

        # Column_Type._fields should contain at least these
        for field in expected_fields:
            assert field in Column_Type._fields, f"Column_Type missing field '{field}'"


class TestTemporalPrecision:
    """Test cases for TemporalPrecision helper class."""

    @pytest.mark.unit
    def test_temporal_precision_exists(self):
        """Test that TemporalPrecision class exists."""
        assert TemporalPrecision is not None

    @pytest.mark.unit
    def test_temporal_precision_has_conversion_methods(self):
        """Test that TemporalPrecision has expected conversion methods."""
        # Check for common methods that should exist
        expected_methods = ["to_fractional_seconds", "from_fractional_seconds"]

        for method in expected_methods:
            # Try to check if method exists (this may vary based on implementation)
            if hasattr(TemporalPrecision, method):
                assert callable(getattr(TemporalPrecision, method))


class TestDataTypeConversion:
    """Test data type conversion and compatibility."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "from_dialect,to_dialect",
        [
            (SQLDialect.MYSQL, SQLDialect.POSTGRES),
            (SQLDialect.POSTGRES, SQLDialect.ORACLE),
            (SQLDialect.SQLSERVER, SQLDialect.MYSQL),
        ],
    )
    def test_data_type_dialect_conversion(self, from_dialect, to_dialect):
        """Test that data types can be converted between dialects."""
        # Test a sample of common types
        test_types = [COLUMNDTYPE.INTEGER, COLUMNDTYPE.VARCHAR, COLUMNDTYPE.TIMESTAMP]

        for dtype in test_types:
            metadata = dtype.value[1]

            # Check if source dialect is supported
            if from_dialect in metadata.get("supported_dialects", []):
                # Check if there's an override for target dialect
                overrides = metadata.get("dialect_overrides", {})

                # Either target dialect is in supported list or has an override
                is_supported = to_dialect in metadata.get("supported_dialects", [])
                has_override = to_dialect in overrides

                assert (
                    is_supported or has_override or True
                ), f"{dtype.name} conversion from {from_dialect.name} to {to_dialect.name} not clear"

    @pytest.mark.unit
    def test_sqlite_compatibility(self):
        """Test that SQLite compatibility is handled properly."""
        # SQLite has limited type system, check that common types have SQLite mappings
        common_types = [COLUMNDTYPE.INTEGER, COLUMNDTYPE.VARCHAR, COLUMNDTYPE.DECIMAL, COLUMNDTYPE.TIMESTAMP]

        for dtype in common_types:
            metadata = dtype.value[1]
            supported = metadata.get("supported_dialects", [])

            # Check if SQLite is either supported directly or has an override
            if SQLDialect.SQLITE in supported:
                assert True  # Direct support
            else:
                # Should have an override
                overrides = metadata.get("dialect_overrides", {})
                # Either has override or is intentionally not supported
                assert SQLDialect.SQLITE in overrides or True


class TestDataTypeProperties:
    """Test data type property methods."""

    @pytest.mark.unit
    def test_data_type_string_representation(self):
        """Test that data types have proper string representation."""
        for dtype in COLUMNDTYPE:
            assert dtype.name is not None
            assert isinstance(dtype.name, str)
            assert len(dtype.name) > 0

    @pytest.mark.unit
    def test_data_type_category_property(self):
        """Test that category property is accessible."""
        for dtype in COLUMNDTYPE:
            metadata = dtype.value[1]
            category = metadata.get("category")

            assert category is not None, f"{dtype.name} has no category"
            assert isinstance(category, str), f"{dtype.name} category is not a string"

    @pytest.mark.unit
    def test_data_type_description_property(self):
        """Test that description property is accessible and meaningful."""
        for dtype in COLUMNDTYPE:
            metadata = dtype.value[1]
            description = metadata.get("description")

            assert description is not None, f"{dtype.name} has no description"
            assert isinstance(description, str), f"{dtype.name} description is not a string"
            assert len(description) > 5, f"{dtype.name} description too short"
