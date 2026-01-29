"""
Secure credential management utilities for SQLUtils.

This module provides helper functions to retrieve database credentials
from various secure sources instead of environment variables.

Supported backends:
- AWS Secrets Manager (aws_secrets.py)
- Google Secret Manager (gcp_secrets.py)
- Azure Key Vault (azure_secrets.py)
- HashiCorp Vault (vault_secrets.py)
- Python Keyring (keyring_store.py)
- AWS RDS IAM Authentication (aws_secrets.py)

Each backend module is imported lazily only when needed, so you only need
to install the dependencies for the credential managers you actually use.

Examples
--------
AWS Secrets Manager:
    from sqlutilities.credentials.aws_secrets import get_aws_secret
    creds = get_aws_secret("my-db-secret", "us-east-1")

Azure Key Vault:
    from sqlutilities.credentials.azure_secrets import get_azure_secret
    creds = get_azure_secret("https://myvault.vault.azure.net", "db-secret")

Google Secret Manager:
    from sqlutilities.credentials.gcp_secrets import get_gcp_secret
    creds = get_gcp_secret("my-project", "db-secret")

HashiCorp Vault:
    from sqlutilities.credentials.vault_secrets import get_vault_secret
    creds = get_vault_secret("secret/data/db", "kv")

OS Keyring:
    from sqlutilities.credentials.keyring_store import get_credentials
    creds = get_credentials("myapp", "dbuser")
"""

# No eager imports - each module is imported only when explicitly needed
# This allows users to only install the dependencies they need

__all__ = [
    # Modules are available for direct import but not loaded here
    # to avoid requiring all optional dependencies
]
