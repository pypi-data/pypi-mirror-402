"""
Test Azure Key Vault credential retrieval.
"""

import pytest

from sqlutilities.connections.database_connection import DatabaseConnection
from sqlutilities.core.enums import SQLDialect


def test_azure_keyvault_connection():
    """Test that DatabaseConnection can retrieve credentials from Azure Key Vault."""

    print("\n" + "=" * 60)
    print("Testing Azure Key Vault credential retrieval...")
    print("=" * 60)

    try:
        conn = DatabaseConnection(
            dialect=SQLDialect.SQLSERVER,
            azure_vault_url="https://demovault24.vault.azure.net",
            azure_secret_name="sql-demo",
        )

        print("✓ Connection created successfully!")
        print("\nAttempting to query SQL Server version...")

        result = conn.read_sql_connector_x("SELECT @@VERSION AS SQLServerVersion")
        print("\n✓ Query successful!")
        print(result)

    except ImportError as e:
        pytest.skip(f"Azure dependencies not installed: {e}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    test_azure_keyvault_connection()
