"""
Examples of using secure credential management with SQLUtils.

DatabaseConnection automatically retrieves credentials from secure sources.
Just pass the secret identifiers and the connection handles the rest!

This demonstrates various methods to securely manage database credentials
without storing them in environment variables or hardcoding them in scripts.
"""

from connections import DatabaseConnection
from core import SQLDialect


# ============================================================================
# Example 1: OS Keyring (Best for local development)
# ============================================================================
def example_keyring():
    """
    Use OS-native credential store (Keychain/Windows Credential Locker/etc.)

    One-time setup:
        from credentials import store_credentials

        store_credentials(
            service="mysql-dev",
            username="dev_user",
            password="your_password",
            metadata={
                "host": "localhost",
                "port": 3306,
                "database": "devdb"
            }
        )
    """
    # AUTOMATIC RETRIEVAL - DatabaseConnection pulls credentials automatically!
    conn = DatabaseConnection(
        dialect=SQLDialect.MYSQL,
        keyring_service="mysql-dev",
        keyring_username="dev_user"
    )

    print("Connected automatically via OS keyring")
    return conn


# ============================================================================
# Example 2: AWS Secrets Manager (Best for AWS workloads)
# ============================================================================
def example_aws_secrets():
    """
    Use AWS Secrets Manager.

    Setup:
        aws secretsmanager create-secret \\
            --name prod/mysql/credentials \\
            --secret-string '{
                "host": "mysql.prod.example.com",
                "port": 3306,
                "database": "proddb",
                "user": "app_user",
                "password": "super_secure_password"
            }'
    """
    # AUTOMATIC RETRIEVAL - Just pass the secret name!
    conn = DatabaseConnection(
        dialect=SQLDialect.MYSQL,
        aws_secret_name="prod/mysql/credentials",
        aws_secret_region="us-east-1"
    )

    print("Connected automatically via AWS Secrets Manager")
    return conn


# ============================================================================
# Example 3: AWS RDS IAM Authentication (No password needed!)
# ============================================================================
def example_rds_iam():
    """
    Use IAM authentication for AWS RDS - NO PASSWORD NEEDED!

    This is the most secure option for AWS RDS/Aurora.
    The application uses its IAM role to generate temporary tokens.

    Setup:
        1. Enable IAM auth on RDS instance
        2. Create database user with IAM authentication
        3. Grant IAM policy to your EC2/ECS/Lambda role
    """
    # AUTOMATIC RETRIEVAL - DatabaseConnection generates IAM token automatically!
    conn = DatabaseConnection(
        dialect=SQLDialect.POSTGRES,
        host="mydb.abc123.us-east-1.rds.amazonaws.com",
        port=5432,
        database="proddb",
        username="iam_db_user",
        aws_rds_iam=True,  # Enable IAM authentication
        aws_rds_region="us-east-1",
        ssl_ca="/path/to/rds-ca-bundle.pem"  # Required for RDS IAM
    )

    print("Connected automatically via IAM authentication (no password!)")
    return conn


# ============================================================================
# Example 4: Google Cloud Secret Manager
# ============================================================================
def example_gcp_secrets():
    """
    Use Google Cloud Secret Manager.

    Setup:
        echo -n '{
            "host": "postgres.prod.example.com",
            "port": 5432,
            "database": "proddb",
            "user": "app_user",
            "password": "super_secure_password"
        }' | gcloud secrets create postgres-prod-credentials --data-file=-
    """
    # AUTOMATIC RETRIEVAL - Just pass project and secret ID!
    conn = DatabaseConnection(
        dialect=SQLDialect.POSTGRES,
        gcp_secret_project="my-gcp-project",
        gcp_secret_name="postgres-prod-credentials"
    )

    print("Connected automatically via GCP Secret Manager")
    return conn


# ============================================================================
# Example 5: Azure Key Vault
# ============================================================================
def example_azure_keyvault():
    """
    Use Azure Key Vault.

    Setup:
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
    """
    # AUTOMATIC RETRIEVAL - Just pass vault URL and secret name!
    conn = DatabaseConnection(
        dialect=SQLDialect.SQLSERVER,
        azure_vault_url="https://myvault.vault.azure.net",
        azure_secret_name="sqlserver-prod-credentials"
    )

    print("Connected automatically via Azure Key Vault")
    return conn


# ============================================================================
# Example 6: HashiCorp Vault (Static Secrets)
# ============================================================================
def example_vault_static():
    """
    Use HashiCorp Vault with static secrets.

    Setup:
        vault kv put secret/database/postgres/prod \\
            host=postgres.example.com \\
            port=5432 \\
            database=proddb \\
            user=app_user \\
            password=super_secure_password
    """
    # AUTOMATIC RETRIEVAL - Just pass the vault path!
    conn = DatabaseConnection(
        dialect=SQLDialect.POSTGRES,
        vault_path="database/postgres/prod",
        vault_mount="secret"  # Optional, defaults to "secret"
    )

    print("Connected automatically via HashiCorp Vault")
    return conn


# ============================================================================
# Example 7: HashiCorp Vault (Dynamic Credentials) - MOST SECURE!
# ============================================================================
def example_vault_dynamic():
    """
    Use HashiCorp Vault with dynamic credentials.

    This is the most secure option:
    - Vault generates unique, short-lived credentials
    - Credentials automatically expire after TTL
    - Each application instance gets different credentials
    - Automatic credential rotation

    Setup:
        vault secrets enable database
        vault write database/config/postgres ...
        vault write database/roles/postgres-prod-role ...
    """
    # AUTOMATIC RETRIEVAL - Vault generates credentials automatically!
    # DatabaseConnection will retrieve username, password, and lease info
    conn = DatabaseConnection(
        dialect=SQLDialect.POSTGRES,
        host="postgres.example.com",
        port=5432,
        database="proddb",
        vault_dynamic_role="postgres-prod-role"  # Vault generates creds from this role
    )

    print("Connected automatically with dynamic credentials (auto-expiring!)")
    return conn


# ============================================================================
# Example 8: Combining Multiple Methods (Environment-based)
# ============================================================================
def example_multi_environment():
    """
    Use different credential methods based on environment.

    This is a production-ready pattern that works across dev/staging/prod.
    """
    import os

    environment = os.getenv("APP_ENVIRONMENT", "development")

    if environment == "development":
        # Local development: Use OS keyring
        conn = DatabaseConnection(
            dialect=SQLDialect.MYSQL,
            keyring_service="mysql-dev",
            keyring_username="dev_user"
        )

    elif environment == "staging":
        # Staging in AWS: Use AWS Secrets Manager
        conn = DatabaseConnection(
            dialect=SQLDialect.MYSQL,
            aws_secret_name="staging/mysql/credentials",
            aws_secret_region="us-east-1"
        )

    elif environment == "production":
        # Production with Vault: Use dynamic credentials
        conn = DatabaseConnection(
            dialect=SQLDialect.MYSQL,
            host="mysql.prod.example.com",
            port=3306,
            database="proddb",
            vault_dynamic_role="mysql-prod-role"  # Auto-generates temp credentials
        )

    else:
        raise ValueError(f"Unknown environment: {environment}")

    print(f"Connected automatically in {environment} environment")
    return conn


# ============================================================================
# Main demonstration
# ============================================================================
if __name__ == "__main__":
    print("SQLUtils Secure Credentials Examples")
    print("=" * 60)

    # Uncomment the example you want to try:

    # Example 1: OS Keyring (for local development)
    # conn = example_keyring()

    # Example 2: AWS Secrets Manager
    # conn = example_aws_secrets()

    # Example 3: AWS RDS IAM (no password!)
    # conn = example_rds_iam()

    # Example 4: GCP Secret Manager
    # conn = example_gcp_secrets()

    # Example 5: Azure Key Vault
    # conn = example_azure_keyvault()

    # Example 6: HashiCorp Vault (static)
    # conn = example_vault_static()

    # Example 7: HashiCorp Vault (dynamic) - MOST SECURE
    # conn = example_vault_dynamic()

    # Example 8: Multi-environment pattern
    # conn = example_multi_environment()

    print("\nSee docs/SECURE_CREDENTIALS.md for full documentation")
