#!/bin/bash
# Helper script to run tst.py with proper PYTHONPATH

# Set PYTHONPATH to include src directory
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Run the test script
python3 -c "
from connections.database_connection import DatabaseConnection
from core.enums import SQLDialect

print('Testing Azure Key Vault credential retrieval...')
print('=' * 60)

try:
    conn = DatabaseConnection(
        dialect=SQLDialect.SQLSERVER,
        azure_vault_url='https://demovault24.vault.azure.net',
        azure_secret_name='sql-demo'
    )

    print('✓ Connection created successfully!')
    print('\nAttempting to query SQL Server version...')

    result = conn.read_sql_connector_x('SELECT @@VERSION AS SQLServerVersion')
    print('\n✓ Query successful!')
    print(result)

except ImportError as e:
    print(f'✗ Import error: {e}')
    print('\nMissing dependencies? Try:')
    print('  pip install azure-identity azure-keyvault-secrets')

except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
"
