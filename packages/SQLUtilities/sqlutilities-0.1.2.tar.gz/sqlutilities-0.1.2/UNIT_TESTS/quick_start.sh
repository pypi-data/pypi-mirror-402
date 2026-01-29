#!/bin/bash
# Quick Start Script for SQLUtils Unit Tests
# This script helps you get started with testing quickly

set -e

echo "================================================"
echo "SQLUtils Test Environment Quick Start"
echo "================================================"
echo

# Check if we're in the right directory
if [ ! -f "run_tests.py" ]; then
    echo "Error: Please run this script from the UNIT_TESTS directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
echo "Checking Python installation..."
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"
echo

# Check if pytest is installed
echo "Checking test dependencies..."
if $PYTHON_CMD -c "import pytest" 2>/dev/null; then
    echo "✓ pytest is installed"
else
    echo "✗ pytest not found"
    echo
    echo "Installing test dependencies..."
    $PYTHON_CMD -m pip install -r ../requirements-test.txt
    echo "✓ Test dependencies installed"
fi
echo

# Check database containers
echo "Checking database containers..."
if command_exists docker; then
    cd ../tst/docker
    bash db_test.sh status
    cd - > /dev/null
    echo
else
    echo "⚠ Docker not found - integration tests will be skipped"
fi
echo

# Show menu
echo "================================================"
echo "What would you like to do?"
echo "================================================"
echo "1) Run all unit tests (no database required)"
echo "2) Run all tests (unit + integration)"
echo "3) Run tests for specific dialect"
echo "4) Start database containers"
echo "5) Check container status"
echo "6) Run tests with coverage report"
echo "7) Exit"
echo

read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        echo
        echo "Running unit tests only..."
        $PYTHON_CMD run_tests.py --unit-only -v
        ;;
    2)
        echo
        echo "Running all tests..."
        $PYTHON_CMD run_tests.py -v
        ;;
    3)
        echo
        echo "Available dialects:"
        echo "  - mysql"
        echo "  - postgres"
        echo "  - oracle"
        echo "  - sqlserver"
        echo "  - bigquery"
        echo "  - redshift"
        echo "  - sqlite"
        echo "  - all"
        echo
        read -p "Enter dialect name: " dialect
        echo
        echo "Running tests for $dialect..."
        $PYTHON_CMD run_tests.py --dialect $dialect -v
        ;;
    4)
        echo
        echo "Starting database containers..."
        cd ../tst/docker
        bash db_test.sh start
        cd - > /dev/null
        ;;
    5)
        echo
        echo "Checking container status..."
        cd ../tst/docker
        bash db_test.sh status
        cd - > /dev/null
        ;;
    6)
        echo
        echo "Running tests with coverage..."
        $PYTHON_CMD run_tests.py --coverage -v
        echo
        echo "Opening coverage report..."
        if [ -d "../htmlcov" ]; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                open ../htmlcov/index.html
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                xdg-open ../htmlcov/index.html 2>/dev/null || echo "Please open htmlcov/index.html in your browser"
            else
                echo "Please open htmlcov/index.html in your browser"
            fi
        fi
        ;;
    7)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo
echo "================================================"
echo "Done!"
echo "================================================"
echo
echo "Useful commands:"
echo "  - Run specific module:    python run_tests.py --module connections"
echo "  - Run with verbose:       python run_tests.py -v"
echo "  - Skip integration:       python run_tests.py --unit-only"
echo "  - Check containers:       python run_tests.py --check-containers"
echo
echo "For more options: python run_tests.py --help"
echo "Full documentation: cat README.md"
echo
