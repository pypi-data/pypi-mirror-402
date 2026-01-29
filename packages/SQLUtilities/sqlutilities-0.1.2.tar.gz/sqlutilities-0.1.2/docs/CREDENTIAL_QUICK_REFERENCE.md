# Credential Retrieval Quick Reference

Quick lookup for automatic credential retrieval parameters in `DatabaseConnection`.

## Quick Start

```python
from connections import DatabaseConnection
from core import SQLDialect

# Just pass the credential source parameters
conn = DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    aws_secret_name="prod/mysql/credentials",  # <-- Automatic retrieval!
    aws_secret_region="us-east-1"
)
```

## Parameters by Provider

| Provider | Parameters | Example |
|----------|------------|---------|
| **AWS Secrets Manager** | `aws_secret_name`<br>`aws_secret_region` (default: "us-east-1") | `aws_secret_name="prod/mysql/creds"`<br>`aws_secret_region="us-west-2"` |
| **AWS RDS IAM** | `host`, `port`, `username`, `database`<br>`aws_rds_iam=True`<br>`aws_rds_region` (default: "us-east-1")<br>`ssl_ca` (required) | `host="mydb.abc.rds.amazonaws.com"`<br>`port=5432`<br>`username="iam_user"`<br>`aws_rds_iam=True`<br>`ssl_ca="/path/to/cert.pem"` |
| **Google Secret Manager** | `gcp_secret_project`<br>`gcp_secret_name` | `gcp_secret_project="my-project"`<br>`gcp_secret_name="db-creds"` |
| **Azure Key Vault** | `azure_vault_url`<br>`azure_secret_name` | `azure_vault_url="https://vault.vault.azure.net"`<br>`azure_secret_name="sqlserver-creds"` |
| **Vault (Static)** | `vault_path`<br>`vault_mount` (default: "secret") | `vault_path="database/postgres/prod"`<br>`vault_mount="secret"` |
| **Vault (Dynamic)** | `host`, `port`, `database`<br>`vault_dynamic_role` | `host="postgres.example.com"`<br>`port=5432`<br>`database="proddb"`<br>`vault_dynamic_role="pg-prod-role"` |
| **OS Keyring** | `keyring_service`<br>`keyring_username` | `keyring_service="mysql-dev"`<br>`keyring_username="dev_user"` |

## Priority Order

If multiple sources are specified, this priority is used (highest to lowest):

1. **AWS RDS IAM** (`aws_rds_iam=True`)
2. **Vault Dynamic** (`vault_dynamic_role`)
3. **AWS Secrets** (`aws_secret_name`)
4. **GCP Secrets** (`gcp_secret_project` + `gcp_secret_name`)
5. **Azure Secrets** (`azure_vault_url` + `azure_secret_name`)
6. **Vault Static** (`vault_path`)
7. **OS Keyring** (`keyring_service` + `keyring_username`)

## Secret Structure

All secrets (except RDS IAM and Vault Dynamic) must be JSON with these keys:

```json
{
  "host": "database.example.com",
  "port": 5432,
  "database": "mydb",
  "user": "myuser",        // or "username" - both accepted
  "password": "mypassword"
}
```

## Code Examples

### AWS Secrets Manager
```python
conn = DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    aws_secret_name="prod/mysql/credentials",
    aws_secret_region="us-east-1"
)
```

### AWS RDS IAM (No Password!)
```python
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    host="mydb.abc123.us-east-1.rds.amazonaws.com",
    port=5432,
    database="proddb",
    username="iam_user",
    aws_rds_iam=True,
    ssl_ca="/path/to/rds-ca-bundle.pem"
)
```

### Google Cloud Secret Manager
```python
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    gcp_secret_project="my-production-project",
    gcp_secret_name="postgres-prod-credentials"
)
```

### Azure Key Vault
```python
conn = DatabaseConnection(
    dialect=SQLDialect.SQLSERVER,
    azure_vault_url="https://myvault.vault.azure.net",
    azure_secret_name="sqlserver-prod-credentials"
)
```

### HashiCorp Vault (Static Secrets)
```python
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    vault_path="database/postgres/prod",
    vault_mount="secret"  # Optional, defaults to "secret"
)
```

### HashiCorp Vault (Dynamic Credentials)
```python
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    host="postgres.example.com",
    port=5432,
    database="proddb",
    vault_dynamic_role="postgres-prod-role"
)
```

### OS Keyring (Local Development)
```python
conn = DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    keyring_service="mysql-dev",
    keyring_username="dev_user"
)
```

### Multi-Environment Pattern
```python
import os

env = os.getenv("ENVIRONMENT", "dev")

if env == "dev":
    conn = DatabaseConnection(
        dialect=SQLDialect.MYSQL,
        keyring_service="mysql-dev",
        keyring_username="dev_user"
    )
elif env == "staging":
    conn = DatabaseConnection(
        dialect=SQLDialect.MYSQL,
        aws_secret_name="staging/mysql/credentials"
    )
elif env == "prod":
    conn = DatabaseConnection(
        dialect=SQLDialect.MYSQL,
        host="mysql.prod.example.com",
        port=3306,
        database="proddb",
        vault_dynamic_role="mysql-prod-role"
    )
```

## Setup Commands

### AWS Secrets Manager
```bash
# Install
pip install boto3

# Create secret
aws secretsmanager create-secret \
    --name prod/mysql/credentials \
    --secret-string '{"host":"mysql.example.com","port":3306,"database":"proddb","user":"app_user","password":"secret"}'
```

### Google Cloud
```bash
# Install
pip install google-cloud-secret-manager

# Create secret
echo -n '{"host":"postgres.example.com","port":5432,"database":"proddb","user":"app_user","password":"secret"}' | \
    gcloud secrets create postgres-prod-credentials --data-file=-
```

### Azure
```bash
# Install
pip install azure-identity azure-keyvault-secrets

# Create secret
az keyvault secret set \
    --vault-name myvault \
    --name sqlserver-prod-credentials \
    --value '{"host":"sqlserver.database.windows.net","port":1433,"database":"proddb","user":"app_user","password":"secret"}'
```

### HashiCorp Vault (Static)
```bash
# Install
pip install hvac

# Create secret
vault kv put secret/database/postgres/prod \
    host=postgres.example.com \
    port=5432 \
    database=proddb \
    user=app_user \
    password=secret
```

### HashiCorp Vault (Dynamic)
```bash
# Install
pip install hvac

# Enable and configure
vault secrets enable database
vault write database/config/postgres \
    plugin_name=postgresql-database-plugin \
    connection_url="postgresql://{{username}}:{{password}}@postgres.example.com:5432/proddb" \
    username="vault_admin" \
    password="vault_admin_password"

# Create role
vault write database/roles/postgres-prod-role \
    db_name=postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"
```

### OS Keyring
```bash
# Install
pip install keyring

# Store credentials (one-time setup)
python -c "
from credentials import store_credentials
store_credentials(
    service='mysql-dev',
    username='dev_user',
    password='my_password',
    metadata={'host': 'localhost', 'port': 3306, 'database': 'devdb'}
)
"
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Failed to import credential module" | Install required package: `pip install boto3` / `google-cloud-secret-manager` / etc. |
| "Secret retrieval failed" | Check authentication and IAM/role permissions |
| "KeyError: 'host'" | Secret must be JSON with required keys: host, port, database, user, password |
| "Multiple credential sources" | Only specify ONE source - remove extra parameters |
| "aws_rds_iam requires host, port, username" | RDS IAM needs explicit connection parameters |
| "SSL connection required" | RDS IAM requires `ssl_ca` parameter with CA bundle path |

## See Full Documentation

- **[AUTOMATIC_CREDENTIAL_RETRIEVAL.md](AUTOMATIC_CREDENTIAL_RETRIEVAL.md)** - Complete guide with detailed setup instructions
- **[SECURE_CREDENTIALS.md](SECURE_CREDENTIALS.md)** - Overview of secure credential management
- **[examples/secure_credentials_example.py](examples/secure_credentials_example.py)** - Working code examples
