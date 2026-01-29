#!/usr/bin/env python3
"""
Test Runner for SQLUtils Unit Tests

This script provides a convenient way to run tests with dialect filtering
and other common testing scenarios.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --dialect mysql    # Run MySQL tests only
    python run_tests.py --dialect all      # Run all dialect tests
    python run_tests.py --unit-only        # Run only unit tests (no integration)
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --verbose          # Run with verbose output
    python run_tests.py --coverage         # Run with coverage report
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


class TestRunner:
    """Test runner with convenient command-line interface."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = Path(__file__).parent

    def run_pytest(self, args: List[str]) -> int:
        """
        Run pytest with given arguments.

        Args:
            args: List of command-line arguments for pytest

        Returns:
            Exit code from pytest
        """
        cmd = ["python", "-m", "pytest"] + args

        print(f"Running: {' '.join(cmd)}")
        print("=" * 80)

        result = subprocess.run(cmd, cwd=str(self.project_root))
        return result.returncode

    def run_all_tests(self, verbose: bool = False, coverage: bool = False) -> int:
        """Run all tests."""
        args = [str(self.test_dir)]

        if verbose:
            args.append("-v")

        if coverage:
            args.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])

        return self.run_pytest(args)

    def run_dialect_tests(self, dialect: str, verbose: bool = False, coverage: bool = False) -> int:
        """
        Run tests for a specific dialect.

        Args:
            dialect: Dialect name (mysql, postgres, oracle, sqlserver, bigquery, redshift, sqlite, all)
            verbose: Enable verbose output
            coverage: Enable coverage reporting

        Returns:
            Exit code from pytest
        """
        args = [str(self.test_dir), f"--dialect={dialect}"]

        if verbose:
            args.append("-v")

        if coverage:
            args.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])

        return self.run_pytest(args)

    def run_unit_tests_only(self, verbose: bool = False, coverage: bool = False) -> int:
        """Run only unit tests (skip integration tests)."""
        args = [str(self.test_dir), "--skip-integration", "-m", "unit"]

        if verbose:
            args.append("-v")

        if coverage:
            args.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])

        return self.run_pytest(args)

    def run_integration_tests_only(self, verbose: bool = False, coverage: bool = False) -> int:
        """Run only integration tests."""
        args = [str(self.test_dir), "-m", "integration"]

        if verbose:
            args.append("-v")

        if coverage:
            args.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])

        return self.run_pytest(args)

    def run_specific_module(self, module: str, verbose: bool = False, coverage: bool = False) -> int:
        """
        Run tests for a specific module.

        Args:
            module: Module name (core, drivers, validation, connections, transactions, errors, tables)
            verbose: Enable verbose output
            coverage: Enable coverage reporting

        Returns:
            Exit code from pytest
        """
        test_file = self.test_dir / f"test_{module}.py"

        if not test_file.exists():
            print(f"Error: Test file not found: {test_file}")
            return 1

        args = [str(test_file)]

        if verbose:
            args.append("-v")

        if coverage:
            args.extend([f"--cov=src/{module}", "--cov-report=html", "--cov-report=term"])

        return self.run_pytest(args)

    def check_docker_containers(self) -> None:
        """Check status of database containers."""
        print("Checking database container status...")
        print("=" * 80)

        try:
            result = subprocess.run(
                ["bash", "tst/docker/db_test.sh", "status"], cwd=str(self.project_root), capture_output=True, text=True
            )

            print(result.stdout)

            if result.returncode != 0:
                print("Warning: Could not check container status")
                print(result.stderr)

        except FileNotFoundError:
            print("Warning: db_test.sh script not found")
        except Exception as e:
            print(f"Warning: Error checking containers: {e}")

        print("=" * 80)
        print()


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Run SQLUtils unit tests with various options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_tests.py

  # Run MySQL tests only
  python run_tests.py --dialect mysql

  # Run unit tests only (no integration tests)
  python run_tests.py --unit-only

  # Run integration tests for PostgreSQL
  python run_tests.py --dialect postgres --integration

  # Run tests for specific module
  python run_tests.py --module connections

  # Run with coverage report
  python run_tests.py --coverage

  # Verbose output
  python run_tests.py -v

  # Check database container status
  python run_tests.py --check-containers
        """,
    )

    parser.add_argument(
        "--dialect",
        choices=["mysql", "postgres", "oracle", "sqlserver", "bigquery", "redshift", "sqlite", "all"],
        help="Run tests for specific database dialect",
    )

    parser.add_argument(
        "--module",
        choices=[
            "core_enums",
            "core_types",
            "drivers",
            "validation",
            "connections",
            "transactions",
            "errors",
            "tables",
        ],
        help="Run tests for specific module",
    )

    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests (skip integration tests)")

    parser.add_argument("--integration", action="store_true", help="Run only integration tests")

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")

    parser.add_argument(
        "--check-containers", action="store_true", help="Check status of database containers before running tests"
    )

    parser.add_argument("--pytest-args", nargs=argparse.REMAINDER, help="Additional arguments to pass to pytest")

    args = parser.parse_args()

    runner = TestRunner()

    # Check containers if requested
    if args.check_containers:
        runner.check_docker_containers()

    # Determine which tests to run
    try:
        if args.module:
            # Run tests for specific module
            exit_code = runner.run_specific_module(args.module, verbose=args.verbose, coverage=args.coverage)

        elif args.unit_only:
            # Run unit tests only
            exit_code = runner.run_unit_tests_only(verbose=args.verbose, coverage=args.coverage)

        elif args.integration:
            # Run integration tests only
            exit_code = runner.run_integration_tests_only(verbose=args.verbose, coverage=args.coverage)

        elif args.dialect:
            # Run tests for specific dialect
            exit_code = runner.run_dialect_tests(args.dialect, verbose=args.verbose, coverage=args.coverage)

        else:
            # Run all tests
            exit_code = runner.run_all_tests(verbose=args.verbose, coverage=args.coverage)

        # Print summary
        print("\n" + "=" * 80)
        if exit_code == 0:
            print("✓ All tests passed!")
        else:
            print(f"✗ Tests failed with exit code: {exit_code}")
        print("=" * 80)

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError running tests: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
