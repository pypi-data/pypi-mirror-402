# Quick Start Guide

## Running Tests (Simple)

```bash
# From project root
python -m pytest UNIT_TESTS/test_core_enums.py -v

# Or use the test runner
cd UNIT_TESTS
python run_tests.py --unit-only
```

## What Works

✅ **Core Enums Tests** - Fully working
```bash
python -m pytest UNIT_TESTS/test_core_enums.py -v
```

✅ **Core Types Tests** - Fully working
```bash
python -m pytest UNIT_TESTS/test_core_types.py -v
```

## Current Issues

⚠️ Some test modules have import errors due to circular dependencies in the source code.
The tests themselves are correct - the issue is in how the source modules import each other.

## Running Specific Tests

```bash
# Run a specific test file
python -m pytest UNIT_TESTS/test_core_enums.py -v

# Run a specific test class
python -m pytest UNIT_TESTS/test_core_enums.py::TestSQLDialect -v

# Run a specific test
python -m pytest UNIT_TESTS/test_core_enums.py::TestSQLDialect::test_all_dialects_exist -v

# Run with output
python -m pytest UNIT_TESTS/test_core_enums.py -xvs
```

## Test Structure

```
UNIT_TESTS/
├── conftest.py                      # Test configuration
├── test_core_enums.py              # ✅ WORKING
├── test_core_types.py              # ✅ WORKING
├── test_drivers.py                  # ⚠️ Import issues
├── test_validation_identifiers.py   # ⚠️ Import issues
├── test_connections.py              # ⚠️ Import issues
├── test_transactions.py             # ⚠️ Import issues
├── test_errors.py                   # ⚠️ Import issues
├── test_tables.py                   # ⚠️ Import issues
└── run_tests.py                     # Test runner script
```

## Full Documentation

See [README.md](README.md) for complete documentation.
