# Automatic Credential Retrieval in DatabaseConnection

`DatabaseConnection` can automatically retrieve database credentials from secure sources during initialization. No manual credential fetching required!

## Table of Contents
- [Overview](#overview)
- [Priority Order](#priority-order)
- [Secret Structure Reference](#secret-structure-reference)
- [Setup Guides by Provider](#setup-guides-by-provider)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

## Overview

Simply pass the secret identifier parameters to `DatabaseConnection` and it automatically retrieves credentials from your chosen secure source:

```python
from connections import DatabaseConnection
from core import SQLDialect

# Credentials are automatically retrieved from AWS Secrets Manager
conn = DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    aws_secret_name="prod/mysql/credentials",
    aws_secret_region="us-east-1"
)
```

## Priority Order

When multiple credential sources are specified, `DatabaseConnection` uses this priority:

1. **AWS RDS IAM Authentication** (no password needed!)
2. **HashiCorp Vault Dynamic Credentials** (auto-generated, time-limited)
3. **AWS Secrets Manager**
4. **Google Secret Manager**
5. **Azure Key Vault**
6. **HashiCorp Vault Static Secrets**
7. **OS Keyring** (Keychain/Windows Credential Locker)

**Important**: Only specify ONE credential source. If multiple sources are configured, the highest priority one is used and a warning is logged.

## Secret Structure Reference

### Required Keys

All secrets must be stored as **JSON strings** containing these keys:

| Key | Accepted Aliases | Type | Required | Description |
|-----|-----------------|------|----------|-------------|
| `host` | - | string | Yes | Database hostname or IP |
| `port` | - | integer | Yes | Database port number |
| `database` | - | string | Yes | Database name |
| `user` | `username` | string | Yes* | Database user (*except RDS IAM) |
| `password` | - | string | Yes* | Database password (*except RDS IAM/Vault Dynamic) |

### Key Naming Rules

1. **Username field**: Can be either `"user"` or `"username"` - both are accepted
2. **All other fields**: Must use the exact names listed above
3. **Case sensitive**: Use lowercase for all keys
4. **Types matter**: `port` must be a number, not a string

### Valid Secret Structures

**Minimal structure** (all databases):
```json
{
  "host": "localhost",
  "port": 3306,
  "database": "mydb",
  "user": "myuser",
  "password": "mypassword"
}
```

**Using "username" instead of "user"**:
```json
{
  "host": "localhost",
  "port": 3306,
  "database": "mydb",
  "username": "myuser",
  "password": "mypassword"
}
```

**With optional SSL/TLS settings**:
```json
{
  "host": "postgres.example.com",
  "port": 5432,
  "database": "proddb",
  "user": "app_user",
  "password": "secure_password",
  "ssl_ca": "/path/to/ca-cert.pem",
  "ssl_cert": "/path/to/client-cert.pem",
  "ssl_key": "/path/to/client-key.pem"
}
```

## Setup Guides by Provider

### 1. AWS Secrets Manager

**Secret Structure**:
```json
{
  "host": "mysql.abc123.us-east-1.rds.amazonaws.com",
  "port": 3306,
  "database": "proddb",
  "user": "app_user",
  "password": "super_secure_password"
}
```

**Setup Command**:
```bash
aws secretsmanager create-secret \
    --name prod/mysql/credentials \
    --secret-string '{
        "host": "mysql.abc123.us-east-1.rds.amazonaws.com",
        "port": 3306,
        "database": "proddb",
        "user": "app_user",
        "password": "super_secure_password"
    }' \
    --region us-east-1
```

**Python Usage**:
```python
conn = DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    aws_secret_name="prod/mysql/credentials",
    aws_secret_region="us-east-1"
)
```

**Required IAM Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/mysql/credentials-*"
    }
  ]
}
```

**Dependencies**:
```bash
pip install boto3
```

---

### 2. AWS RDS IAM Authentication

**No Secret Structure Required** - Credentials generated dynamically using IAM!

**Setup Steps**:

1. **Enable IAM authentication on RDS instance**:
```bash
aws rds modify-db-instance \
    --db-instance-identifier mydb \
    --enable-iam-database-authentication \
    --apply-immediately
```

2. **Create database user with IAM authentication**:
```sql
-- For MySQL/MariaDB:
CREATE USER 'iam_user' IDENTIFIED WITH AWSAuthenticationPlugin AS 'RDS';
GRANT SELECT, INSERT, UPDATE, DELETE ON mydb.* TO 'iam_user'@'%';

-- For PostgreSQL:
CREATE USER iam_user;
GRANT rds_iam TO iam_user;
GRANT ALL PRIVILEGES ON DATABASE mydb TO iam_user;
```

3. **Attach IAM policy to your application role**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds-db:connect"
      ],
      "Resource": "arn:aws:rds-db:us-east-1:123456789012:dbuser:db-ABCDEFGHIJK123/iam_user"
    }
  ]
}
```

**Python Usage**:
```python
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    host="mydb.abc123.us-east-1.rds.amazonaws.com",
    port=5432,
    database="proddb",
    username="iam_user",  # Must provide these explicitly
    aws_rds_iam=True,     # Enable IAM authentication
    aws_rds_region="us-east-1",
    ssl_ca="/path/to/rds-ca-bundle.pem"  # SSL required for IAM auth
)
```

**Important Notes**:
- Authentication tokens are valid for **15 minutes**
- SSL/TLS connection is **required**
- Download RDS CA bundle: https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
- No password needed - token generated automatically!

**Dependencies**:
```bash
pip install boto3
```

---

### 3. Google Cloud Secret Manager

**Secret Structure**:
```json
{
  "host": "10.1.2.3",
  "port": 5432,
  "database": "proddb",
  "user": "app_user",
  "password": "super_secure_password"
}
```

**Setup Command**:
```bash
# Create secret from JSON string
echo -n '{
    "host": "10.1.2.3",
    "port": 5432,
    "database": "proddb",
    "user": "app_user",
    "password": "super_secure_password"
}' | gcloud secrets create postgres-prod-credentials \
    --data-file=- \
    --replication-policy="automatic"

# Grant access to service account
gcloud secrets add-iam-policy-binding postgres-prod-credentials \
    --member="serviceAccount:my-app@my-project.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

**Python Usage**:
```python
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    gcp_secret_project="my-gcp-project",
    gcp_secret_name="postgres-prod-credentials"
)
```

**Authentication**:
- Uses Application Default Credentials (ADC)
- Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to service account key JSON
- Or use workload identity on GKE/Cloud Run

**Dependencies**:
```bash
pip install google-cloud-secret-manager
```

---

### 4. Azure Key Vault

**Secret Structure**:
```json
{
  "host": "sqlserver.database.windows.net",
  "port": 1433,
  "database": "proddb",
  "user": "app_user",
  "password": "super_secure_password"
}
```

**Setup Command**:
```bash
# Create Key Vault
az keyvault create \
    --name myvault \
    --resource-group mygroup \
    --location eastus

# Store secret
az keyvault secret set \
    --vault-name myvault \
    --name sqlserver-prod-credentials \
    --value '{
        "host": "sqlserver.database.windows.net",
        "port": 1433,
        "database": "proddb",
        "user": "app_user",
        "password": "super_secure_password"
    }'

# Grant access to managed identity
az keyvault set-policy \
    --name myvault \
    --object-id <managed-identity-id> \
    --secret-permissions get
```

**Python Usage**:
```python
conn = DatabaseConnection(
    dialect=SQLDialect.SQLSERVER,
    azure_vault_url="https://myvault.vault.azure.net",
    azure_secret_name="sqlserver-prod-credentials"
)
```

**Authentication**:
- Uses `DefaultAzureCredential` (tries multiple methods)
- Best practice: Use Managed Identity on Azure VMs/App Service/AKS
- For local dev: `az login` or set `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`

**Dependencies**:
```bash
pip install azure-identity azure-keyvault-secrets
```

---

### 5. HashiCorp Vault (Static Secrets)

**Secret Structure** (KV v2):
```json
{
  "host": "postgres.example.com",
  "port": 5432,
  "database": "proddb",
  "user": "app_user",
  "password": "super_secure_password"
}
```

**Setup Commands**:
```bash
# Enable KV v2 secrets engine (if not already enabled)
vault secrets enable -path=secret kv-v2

# Store secret
vault kv put secret/database/postgres/prod \
    host=postgres.example.com \
    port=5432 \
    database=proddb \
    user=app_user \
    password=super_secure_password

# Or from JSON file
vault kv put secret/database/postgres/prod @credentials.json

# Grant policy
vault policy write postgres-prod-reader - <<EOF
path "secret/data/database/postgres/prod" {
  capabilities = ["read"]
}
EOF

# Attach policy to token/role
vault token create -policy=postgres-prod-reader
```

**Python Usage**:
```python
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    vault_path="database/postgres/prod",     # Path without mount point prefix
    vault_mount="secret"                     # Mount point (default: "secret")
)
```

**Environment Variables**:
```bash
export VAULT_ADDR="https://vault.example.com:8200"
export VAULT_TOKEN="s.xxxxxxxxxxxxxx"
# Or use other auth methods (AppRole, Kubernetes, etc.)
```

**Dependencies**:
```bash
pip install hvac
```

---

### 6. HashiCorp Vault (Dynamic Credentials)

**No Secret Structure Required** - Vault generates credentials dynamically!

**Setup Commands**:

1. **Enable database secrets engine**:
```bash
vault secrets enable database
```

2. **Configure database connection**:

For **PostgreSQL**:
```bash
vault write database/config/postgres \
    plugin_name=postgresql-database-plugin \
    allowed_roles="postgres-prod-role" \
    connection_url="postgresql://{{username}}:{{password}}@postgres.example.com:5432/proddb?sslmode=require" \
    username="vault_admin" \
    password="vault_admin_password"
```

For **MySQL**:
```bash
vault write database/config/mysql \
    plugin_name=mysql-database-plugin \
    allowed_roles="mysql-prod-role" \
    connection_url="{{username}}:{{password}}@tcp(mysql.example.com:3306)/" \
    username="vault_admin" \
    password="vault_admin_password"
```

3. **Create role for dynamic credentials**:

For **PostgreSQL**:
```bash
vault write database/roles/postgres-prod-role \
    db_name=postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"
```

For **MySQL**:
```bash
vault write database/roles/mysql-prod-role \
    db_name=mysql \
    creation_statements="CREATE USER '{{name}}'@'%' IDENTIFIED BY '{{password}}'; \
        GRANT SELECT, INSERT, UPDATE, DELETE ON proddb.* TO '{{name}}'@'%';" \
    default_ttl="1h" \
    max_ttl="24h"
```

**Python Usage**:
```python
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    host="postgres.example.com",
    port=5432,
    database="proddb",
    vault_dynamic_role="postgres-prod-role"  # Vault generates temp credentials
)
```

**How It Works**:
1. `DatabaseConnection` requests credentials from Vault role
2. Vault creates a new database user with unique username (e.g., `v-token-postgres-prod-role-abc123xyz`)
3. Credentials are returned with lease duration (e.g., 3600 seconds = 1 hour)
4. After TTL expires, Vault automatically revokes the database user
5. Each application instance gets **unique, time-limited** credentials!

**Benefits**:
- Most secure option - credentials are ephemeral
- Automatic credential rotation
- Audit trail of who accessed what and when
- No shared passwords between applications

**Environment Variables**:
```bash
export VAULT_ADDR="https://vault.example.com:8200"
export VAULT_TOKEN="s.xxxxxxxxxxxxxx"
```

**Dependencies**:
```bash
pip install hvac
```

---

### 7. OS Keyring (Keychain / Windows Credential Locker)

**Secret Structure**:
The OS keyring stores credentials as:
- **Service**: A unique identifier (e.g., "mysql-dev")
- **Username**: Database username
- **Password**: Database password
- **Metadata**: JSON containing host, port, database

**Setup**:

```python
from credentials import store_credentials

# One-time setup - store credentials in OS keyring
store_credentials(
    service="mysql-dev",
    username="dev_user",
    password="my_secure_password",
    metadata={
        "host": "localhost",
        "port": 3306,
        "database": "devdb"
    }
)
```

**Python Usage**:
```python
conn = DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    keyring_service="mysql-dev",
    keyring_username="dev_user"
)
```

**How It Works**:
- macOS: Stores in Keychain.app
- Windows: Stores in Credential Locker
- Linux: Stores in Secret Service (GNOME Keyring, KWallet, etc.)

**Best For**:
- Local development
- Desktop applications
- Single-user systems

**Dependencies**:
```bash
pip install keyring
```

## Usage Examples

### Example 1: Simple AWS Secrets Manager Usage

```python
from connections import DatabaseConnection
from core import SQLDialect

# All credentials automatically retrieved
conn = DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    aws_secret_name="prod/mysql/credentials",
    aws_secret_region="us-east-1"
)

# Connection is ready to use
with conn.transaction() as txn:
    result = txn.execute_query("SELECT * FROM users LIMIT 10")
```

### Example 2: AWS RDS with IAM Authentication (Most Secure!)

```python
# No password needed - IAM token generated automatically
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

### Example 3: Multi-Environment Pattern

```python
import os
from connections import DatabaseConnection
from core import SQLDialect

environment = os.getenv("APP_ENVIRONMENT", "development")

if environment == "development":
    # Local dev: OS Keyring
    conn = DatabaseConnection(
        dialect=SQLDialect.MYSQL,
        keyring_service="mysql-dev",
        keyring_username="dev_user"
    )

elif environment == "staging":
    # Staging: AWS Secrets Manager
    conn = DatabaseConnection(
        dialect=SQLDialect.MYSQL,
        aws_secret_name="staging/mysql/credentials",
        aws_secret_region="us-east-1"
    )

elif environment == "production":
    # Production: Vault Dynamic Credentials
    conn = DatabaseConnection(
        dialect=SQLDialect.MYSQL,
        host="mysql.prod.example.com",
        port=3306,
        database="proddb",
        vault_dynamic_role="mysql-prod-role"
    )
```

### Example 4: Explicit Parameters Override Secrets

```python
# Secret provides: host, port, database, user, password
# But you can override specific fields
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    aws_secret_name="prod/postgres/credentials",
    database="different_db"  # Overrides database from secret
)
```

### Example 5: GCP with Cloud SQL

```python
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    gcp_secret_project="my-production-project",
    gcp_secret_name="cloudsql-prod-credentials"
)
```

### Example 6: Azure SQL Database

```python
conn = DatabaseConnection(
    dialect=SQLDialect.SQLSERVER,
    azure_vault_url="https://prod-vault.vault.azure.net",
    azure_secret_name="sqlserver-prod-creds"
)
```

## Troubleshooting

### Error: "Failed to import credential module"

**Cause**: Missing optional dependency for the credential provider.

**Solution**: Install the required package:
```bash
# AWS
pip install boto3

# GCP
pip install google-cloud-secret-manager

# Azure
pip install azure-identity azure-keyvault-secrets

# Vault
pip install hvac

# Keyring
pip install keyring
```

### Error: "Secret retrieval failed" or "Access Denied"

**Cause**: Authentication or permission issues.

**Solutions**:

**AWS**:
```bash
# Check credentials
aws sts get-caller-identity

# Check IAM policy
aws iam get-role-policy --role-name MyRole --policy-name SecretsAccess
```

**GCP**:
```bash
# Check authentication
gcloud auth list

# Check permissions
gcloud secrets get-iam-policy postgres-prod-credentials
```

**Azure**:
```bash
# Check authentication
az account show

# Check access policies
az keyvault show --name myvault
```

**Vault**:
```bash
# Check authentication
vault token lookup

# Check policy
vault policy read postgres-prod-reader
```

### Error: "KeyError: 'host'" or "KeyError: 'user'"

**Cause**: Secret is not structured correctly as JSON with required keys.

**Solution**: Verify secret structure matches the [Secret Structure Reference](#secret-structure-reference):
```json
{
  "host": "...",
  "port": ...,
  "database": "...",
  "user": "...",      // or "username"
  "password": "..."
}
```

Retrieve and inspect your secret:
```bash
# AWS
aws secretsmanager get-secret-value --secret-id prod/mysql/credentials

# GCP
gcloud secrets versions access latest --secret=postgres-prod-credentials

# Azure
az keyvault secret show --vault-name myvault --name sqlserver-prod-credentials

# Vault
vault kv get secret/database/postgres/prod
```

### Warning: "Multiple credential sources specified"

**Cause**: You specified more than one credential source.

**Solution**: Only specify ONE credential source. Remove the others or use the priority order to your advantage.

### Error: "aws_rds_iam requires host, port, and username"

**Cause**: RDS IAM authentication needs explicit connection parameters.

**Solution**: Provide host, port, and username explicitly:
```python
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    host="mydb.abc123.us-east-1.rds.amazonaws.com",  # Required
    port=5432,                                        # Required
    database="proddb",
    username="iam_user",                              # Required
    aws_rds_iam=True
)
```

### Connection succeeds but queries fail with permission errors

**Cause**: Dynamic credentials (Vault) may have limited permissions.

**Solution**: Update the role's creation statements to grant necessary permissions:
```bash
vault write database/roles/postgres-prod-role \
    db_name=postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
        GRANT ALL PRIVILEGES ON DATABASE proddb TO \"{{name}}\"; \
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO \"{{name}}\"; \
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO \"{{name}}\";"
```

### RDS IAM authentication: "SSL connection required"

**Cause**: RDS IAM requires SSL/TLS connection.

**Solution**:
1. Download RDS CA bundle: https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
2. Specify `ssl_ca` parameter:
```python
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    host="mydb.abc123.us-east-1.rds.amazonaws.com",
    port=5432,
    database="proddb",
    username="iam_user",
    aws_rds_iam=True,
    ssl_ca="/path/to/global-bundle.pem"  # Required!
)
```

## Best Practices

1. **Use dynamic credentials when possible** (Vault Dynamic, RDS IAM) - most secure
2. **Store secrets as JSON** with consistent key naming
3. **Use environment-specific secrets** (dev/staging/prod)
4. **Rotate secrets regularly** if using static credentials
5. **Principle of least privilege** - grant only necessary database permissions
6. **Never commit secrets** to version control
7. **Use IAM roles/service accounts** instead of access keys when possible
8. **Enable audit logging** on your secret manager
9. **Monitor secret access** for unusual patterns
10. **Test credential retrieval** in development before deploying to production

## See Also

- [SECURE_CREDENTIALS.md](SECURE_CREDENTIALS.md) - Overview of secure credential management
- [examples/secure_credentials_example.py](examples/secure_credentials_example.py) - Working code examples
- [ENV_SETUP.md](../ENV_SETUP.md) - Environment variable setup (fallback method)
