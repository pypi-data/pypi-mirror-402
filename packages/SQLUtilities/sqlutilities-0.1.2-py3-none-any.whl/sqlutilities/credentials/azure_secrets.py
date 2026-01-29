"""
Azure Key Vault utilities.

Dependencies:
    pip install azure-identity azure-keyvault-secrets
"""

import json
from typing import Any, Dict


def get_azure_secret(vault_url: str, secret_name: str) -> Dict[str, Any]:
    """
    Retrieve secret from Azure Key Vault.

    Args:
        vault_url: Key Vault URL (e.g., "https://myvault.vault.azure.net")
        secret_name: Secret name

    Returns:
        Dictionary containing the secret data

    Raises:
        Exception: If secret retrieval fails

    Example:
        >>> from credentials import get_azure_secret
        >>> from connections import DatabaseConnection
        >>> from core import SQLDialect
        >>>
        >>> vault_url = "https://myvault.vault.azure.net"
        >>> creds = get_azure_secret(vault_url, "sqlserver-prod-credentials")
        >>> conn = DatabaseConnection(
        ...     dialect=SQLDialect.SQLSERVER,
        ...     **creds
        ... )

    Setup:
        # Create Key Vault
        az keyvault create --name myvault --resource-group mygroup --location eastus

        # Store secret
        az keyvault secret set \\
            --vault-name myvault \\
            --name sqlserver-prod-credentials \\
            --value '{
                "host": "sqlserver.database.windows.net",
                "port": 1433,
                "database": "proddb",
                "user": "app_user",
                "password": "super_secure_password"
            }'

        # Grant access to managed identity
        az keyvault set-policy \\
            --name myvault \\
            --object-id <managed-identity-id> \\
            --secret-permissions get
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
    except ImportError:
        raise ImportError(
            "azure-identity and azure-keyvault-secrets are required for Azure Key Vault. "
            "Install them with: pip install azure-identity azure-keyvault-secrets"
        )

    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)

    try:
        secret = client.get_secret(secret_name)

        try:
            return json.loads(secret.value)
        except json.JSONDecodeError:
            return {"value": secret.value}

    except Exception as e:
        raise Exception(f"Failed to retrieve Azure secret '{secret_name}': {e}")
