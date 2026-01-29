"""
HashiCorp Vault utilities.

Dependencies:
    pip install hvac
"""

import os
from typing import Dict, Optional


def get_vault_secret(
    path: str, mount_point: str = "secret", vault_addr: Optional[str] = None, vault_token: Optional[str] = None
) -> Dict[str, any]:
    """
    Retrieve secret from HashiCorp Vault (KV v2).

    Args:
        path: Secret path (e.g., "database/postgres/prod")
        mount_point: Secrets engine mount point (default: "secret")
        vault_addr: Vault server address (default: VAULT_ADDR env var)
        vault_token: Vault token (default: VAULT_TOKEN env var)

    Returns:
        Dictionary containing the secret data

    Raises:
        Exception: If secret retrieval fails

    Example:
        >>> from credentials import get_vault_secret
        >>> from connections import DatabaseConnection
        >>> from core import SQLDialect
        >>>
        >>> creds = get_vault_secret("database/postgres/prod")
        >>> conn = DatabaseConnection(
        ...     dialect=SQLDialect.POSTGRES,
        ...     **creds
        ... )

    Setup:
        # Store secret in Vault
        vault kv put secret/database/postgres/prod \\
            host=postgres.example.com \\
            port=5432 \\
            database=proddb \\
            user=app_user \\
            password=super_secure_password
    """
    try:
        import hvac
    except ImportError:
        raise ImportError("hvac is required for HashiCorp Vault. " "Install it with: pip install hvac")

    vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = vault_token or os.getenv("VAULT_TOKEN")

    if not vault_token:
        raise Exception(
            "Vault token not provided. Set VAULT_TOKEN environment variable " "or pass vault_token parameter"
        )

    client = hvac.Client(url=vault_addr, token=vault_token)

    if not client.is_authenticated():
        raise Exception("Vault authentication failed. Check your token.")

    try:
        response = client.secrets.kv.v2.read_secret_version(path=path, mount_point=mount_point)
        return response["data"]["data"]

    except Exception as e:
        raise Exception(f"Failed to retrieve Vault secret at '{path}': {e}")


def get_vault_dynamic_credentials(
    role_name: str, mount_point: str = "database", vault_addr: Optional[str] = None, vault_token: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate short-lived database credentials from Vault's database secrets engine.

    Vault automatically creates these credentials and revokes them after TTL.
    This is the most secure option - credentials are unique and temporary.

    Args:
        role_name: Vault role name
        mount_point: Database secrets engine mount point (default: "database")
        vault_addr: Vault server address (default: VAULT_ADDR env var)
        vault_token: Vault token (default: VAULT_TOKEN env var)

    Returns:
        Dictionary with username, password, and lease_duration

    Example:
        >>> from credentials import get_vault_dynamic_credentials
        >>> from connections import DatabaseConnection
        >>> from core import SQLDialect
        >>>
        >>> # Vault generates unique, time-limited credentials
        >>> creds = get_vault_dynamic_credentials("postgres-prod-role")
        >>> # Returns: {
        >>> #     "username": "v-token-postgres-prod-role-abc123",
        >>> #     "password": "...",
        >>> #     "lease_duration": 3600  # Valid for 1 hour
        >>> # }
        >>>
        >>> conn = DatabaseConnection(
        ...     dialect=SQLDialect.POSTGRES,
        ...     host="postgres.example.com",
        ...     port=5432,
        ...     database="proddb",
        ...     user=creds['username'],
        ...     password=creds['password']
        ... )

    Setup:
        # Enable database secrets engine
        vault secrets enable database

        # Configure database connection
        vault write database/config/postgres \\
            plugin_name=postgresql-database-plugin \\
            allowed_roles="postgres-prod-role" \\
            connection_url="postgresql://{{username}}:{{password}}@postgres.example.com:5432/proddb" \\
            username="vault_admin" \\
            password="vault_admin_password"

        # Create role for dynamic credentials
        vault write database/roles/postgres-prod-role \\
            db_name=postgres \\
            creation_statements="CREATE ROLE \\"{{name}}\\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \\
                GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \\"{{name}}\\";" \\
            default_ttl="1h" \\
            max_ttl="24h"
    """
    try:
        import hvac
    except ImportError:
        raise ImportError("hvac is required for HashiCorp Vault. " "Install it with: pip install hvac")

    vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = vault_token or os.getenv("VAULT_TOKEN")

    if not vault_token:
        raise Exception(
            "Vault token not provided. Set VAULT_TOKEN environment variable " "or pass vault_token parameter"
        )

    client = hvac.Client(url=vault_addr, token=vault_token)

    if not client.is_authenticated():
        raise Exception("Vault authentication failed. Check your token.")

    try:
        response = client.secrets.database.generate_credentials(name=role_name, mount_point=mount_point)

        return {
            "username": response["data"]["username"],
            "password": response["data"]["password"],
            "lease_duration": response["lease_duration"],
        }

    except Exception as e:
        raise Exception(f"Failed to generate dynamic credentials for role '{role_name}': {e}")
