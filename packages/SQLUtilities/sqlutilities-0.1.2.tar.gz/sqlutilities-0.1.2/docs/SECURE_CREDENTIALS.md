# Secure Credential Management Guide

This guide covers enterprise-grade alternatives to storing credentials in environment variables or scripts.

## 🚀 NEW: Automatic Credential Retrieval

`DatabaseConnection` now **automatically retrieves credentials** from secure sources! No manual fetching required.

```python
# Simply pass the secret identifier - credentials retrieved automatically!
conn = DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    aws_secret_name="prod/mysql/credentials",
    aws_secret_region="us-east-1"
)
```

**📖 See [AUTOMATIC_CREDENTIAL_RETRIEVAL.md](AUTOMATIC_CREDENTIAL_RETRIEVAL.md) for:**
- Complete setup guides for all 7 credential sources
- **Exact JSON structure required for each secret manager**
- **Key naming conventions** (user vs username, etc.)
- Priority order and usage examples
- Troubleshooting guide

**Quick Reference - Required Secret Structure:**
```json
{
  "host": "database.example.com",
  "port": 5432,
  "database": "mydb",
  "user": "myuser",        // or "username"
  "password": "mypassword"
}
```

---

## Table of Contents
1. [Cloud Secrets Managers](#cloud-secrets-managers)
2. [HashiCorp Vault](#hashicorp-vault)
3. [OS Credential Stores](#os-credential-stores)
4. [IAM Roles & Managed Identities](#iam-roles--managed-identities)
5. [Encrypted Configuration Files](#encrypted-configuration-files)
6. [Certificate-Based Authentication](#certificate-based-authentication)
7. [Comparison Matrix](#comparison-matrix)

---

## Cloud Secrets Managers

### AWS Secrets Manager

**Best for:** Applications running in AWS

```python
import boto3
from botocore.exceptions import ClientError
import json

def get_secret(secret_name: str, region_name: str = "us-east-1") -> dict:
    """
    Retrieve secret from AWS Secrets Manager.

    Requires AWS credentials configured via:
    - IAM role (recommended for EC2/ECS/Lambda)
    - AWS CLI configuration
    - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    """
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        raise Exception(f"Failed to retrieve secret: {e}")

# Usage with SQLUtils
from connections import DatabaseConnection
from core import SQLDialect

# Retrieve database credentials
db_credentials = get_secret("prod/mysql/credentials")

# Connect using retrieved credentials
conn = DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    host=db_credentials['host'],
    port=db_credentials['port'],
    database=db_credentials['database'],
    user=db_credentials['username'],
    password=db_credentials['password']
)
```

**Setup:**
```bash
# Install AWS SDK
pip install boto3

# Create secret in AWS
aws secretsmanager create-secret \
    --name prod/mysql/credentials \
    --secret-string '{
        "host": "mysql.example.com",
        "port": 3306,
        "database": "proddb",
        "username": "app_user",
        "password": "super_secure_password"
    }'

# Grant access via IAM policy
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "secretsmanager:GetSecretValue",
            "Resource": "arn:aws:secretsmanager:us-east-1:123456789:secret:prod/mysql/credentials-*"
        }
    ]
}
```

**Advantages:**
- Automatic rotation support
- Audit logging (CloudTrail)
- Fine-grained IAM permissions
- No credentials in code/config
- Encryption at rest (AWS KMS)

**Cost:** ~$0.40/secret/month + $0.05 per 10,000 API calls

---

### Google Secret Manager

**Best for:** Applications running in GCP

```python
from google.cloud import secretmanager
import json

def get_gcp_secret(project_id: str, secret_id: str, version: str = "latest") -> dict:
    """
    Retrieve secret from Google Secret Manager.

    Requires authentication via:
    - Service account (recommended for GCE/GKE/Cloud Run)
    - Application Default Credentials
    - GOOGLE_APPLICATION_CREDENTIALS env var
    """
    client = secretmanager.SecretManagerServiceClient()

    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(request={"name": name})

    return json.loads(response.payload.data.decode("UTF-8"))

# Usage
from connections import DatabaseConnection
from core import SQLDialect

credentials = get_gcp_secret("my-project", "postgres-prod-credentials")

conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    **credentials  # Unpack the credentials dict
)
```

**Setup:**
```bash
# Install GCP SDK
pip install google-cloud-secret-manager

# Create secret
echo -n '{
    "host": "postgres.example.com",
    "port": 5432,
    "database": "proddb",
    "user": "app_user",
    "password": "super_secure_password"
}' | gcloud secrets create postgres-prod-credentials --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding postgres-prod-credentials \
    --member="serviceAccount:app@project.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

---

### Azure Key Vault

**Best for:** Applications running in Azure

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import json

def get_azure_secret(vault_url: str, secret_name: str) -> dict:
    """
    Retrieve secret from Azure Key Vault.

    Authenticates via:
    - Managed Identity (recommended for Azure VMs/App Service)
    - Azure CLI credentials
    - Environment variables
    """
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)

    secret = client.get_secret(secret_name)
    return json.loads(secret.value)

# Usage
from connections import DatabaseConnection
from core import SQLDialect

vault_url = "https://myvault.vault.azure.net"
credentials = get_azure_secret(vault_url, "sqlserver-prod-credentials")

conn = DatabaseConnection(
    dialect=SQLDialect.SQLSERVER,
    **credentials
)
```

**Setup:**
```bash
# Install Azure SDK
pip install azure-identity azure-keyvault-secrets

# Create Key Vault
az keyvault create --name myvault --resource-group mygroup --location eastus

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

---

## HashiCorp Vault

**Best for:** Multi-cloud or on-premise deployments

```python
import hvac
import os

def get_vault_secret(path: str, mount_point: str = "secret") -> dict:
    """
    Retrieve secret from HashiCorp Vault.

    Authenticates via:
    - Token (VAULT_TOKEN env var)
    - AppRole
    - Kubernetes
    - AWS IAM
    """
    client = hvac.Client(
        url=os.getenv("VAULT_ADDR", "http://localhost:8200"),
        token=os.getenv("VAULT_TOKEN")
    )

    if not client.is_authenticated():
        raise Exception("Vault authentication failed")

    response = client.secrets.kv.v2.read_secret_version(
        path=path,
        mount_point=mount_point
    )

    return response['data']['data']

# Usage with dynamic database credentials
def get_dynamic_db_credentials(role_name: str) -> dict:
    """
    Generate short-lived database credentials from Vault.
    Vault automatically creates and rotates these credentials.
    """
    client = hvac.Client(
        url=os.getenv("VAULT_ADDR"),
        token=os.getenv("VAULT_TOKEN")
    )

    # Request dynamic credentials (valid for configured TTL)
    response = client.secrets.database.generate_credentials(
        name=role_name,
        mount_point='database'
    )

    return {
        'username': response['data']['username'],
        'password': response['data']['password'],
        'lease_duration': response['lease_duration']
    }

# Usage
from connections import DatabaseConnection
from core import SQLDialect

# Static secret
static_creds = get_vault_secret("database/postgres/prod")

# Or dynamic credentials (recommended)
dynamic_creds = get_dynamic_db_credentials("postgres-prod-role")

conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    host="postgres.example.com",
    port=5432,
    database="proddb",
    user=dynamic_creds['username'],
    password=dynamic_creds['password']
)
```

**Setup:**
```bash
# Install Vault client
pip install hvac

# Start Vault (dev mode for testing)
vault server -dev

# Enable database secrets engine
vault secrets enable database

# Configure database connection
vault write database/config/postgres \
    plugin_name=postgresql-database-plugin \
    allowed_roles="postgres-prod-role" \
    connection_url="postgresql://{{username}}:{{password}}@postgres.example.com:5432/proddb" \
    username="vault_admin" \
    password="vault_admin_password"

# Create role for dynamic credentials
vault write database/roles/postgres-prod-role \
    db_name=postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"
```

**Advantages:**
- Dynamic credentials (auto-generated, short-lived)
- Multi-cloud support
- Automatic secret rotation
- Encryption as a service
- Audit logging
- Fine-grained access policies

---

## OS Credential Stores

### Python Keyring (Cross-Platform)

**Best for:** Desktop applications, local development

```python
import keyring
from keyring.backends import OS_X_Keychain, Windows, SecretService

def store_credentials(service: str, username: str, password: str):
    """Store credentials in OS-native credential store."""
    keyring.set_password(service, username, password)

def get_credentials(service: str, username: str) -> str:
    """Retrieve credentials from OS-native credential store."""
    return keyring.get_password(service, username)

# Usage
from connections import DatabaseConnection
from core import SQLDialect

# One-time setup (store credentials)
# store_credentials("mysql-prod", "app_user", "super_secure_password")

# Retrieve and use
password = get_credentials("mysql-prod", "app_user")

conn = DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    host="mysql.example.com",
    port=3306,
    database="proddb",
    user="app_user",
    password=password
)
```

**Setup:**
```bash
# Install keyring
pip install keyring

# Store credentials (one-time)
python -c "import keyring; keyring.set_password('mysql-prod', 'app_user', 'your_password')"

# Credentials are stored in:
# - macOS: Keychain
# - Windows: Windows Credential Locker
# - Linux: Secret Service (GNOME Keyring, KWallet)
```

**Advantages:**
- No external dependencies
- OS-native security
- Works offline
- User-specific credentials

**Limitations:**
- Not suitable for server applications
- Requires interactive login

---

### Pass (Unix Password Manager)

**Best for:** Linux/Unix systems, CLI tools

```python
import subprocess
import json

def get_pass_secret(pass_name: str) -> dict:
    """
    Retrieve secret from pass (the standard Unix password manager).
    Secrets are stored as GPG-encrypted files.
    """
    try:
        result = subprocess.run(
            ['pass', 'show', pass_name],
            capture_output=True,
            text=True,
            check=True
        )
        # Assume JSON format
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to retrieve password: {e}")

# Usage
credentials = get_pass_secret("database/postgres/prod")

from connections import DatabaseConnection
from core import SQLDialect

conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    **credentials
)
```

**Setup:**
```bash
# Install pass
# macOS: brew install pass
# Ubuntu: apt-get install pass

# Initialize pass with GPG key
pass init your-gpg-key-id

# Store credentials
pass insert -m database/postgres/prod
# Then paste JSON:
# {
#   "host": "postgres.example.com",
#   "port": 5432,
#   "database": "proddb",
#   "user": "app_user",
#   "password": "super_secure_password"
# }
```

---

## IAM Roles & Managed Identities

### AWS RDS IAM Authentication

**Best for:** Applications running in AWS connecting to RDS

```python
import boto3
from connections import DatabaseConnection
from core import SQLDialect

def get_rds_iam_token(host: str, port: int, username: str, region: str = "us-east-1") -> str:
    """
    Generate temporary authentication token for RDS using IAM.
    No password needed - uses IAM role permissions.
    Token valid for 15 minutes.
    """
    client = boto3.client('rds', region_name=region)

    token = client.generate_db_auth_token(
        DBHostname=host,
        Port=port,
        DBUsername=username,
        Region=region
    )

    return token

# Usage - No password stored anywhere!
from connections import DatabaseConnection
from core import SQLDialect

# Application uses its IAM role to generate temporary token
auth_token = get_rds_iam_token(
    host="mydb.123456789.us-east-1.rds.amazonaws.com",
    port=5432,
    username="iam_db_user",
    region="us-east-1"
)

conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    host="mydb.123456789.us-east-1.rds.amazonaws.com",
    port=5432,
    database="proddb",
    user="iam_db_user",
    password=auth_token,  # Temporary token, not a real password
    ssl_ca="/path/to/rds-ca-bundle.pem"  # Required for IAM auth
)
```

**Setup:**
```bash
# 1. Create IAM policy for RDS access
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "rds-db:connect",
            "Resource": "arn:aws:rds-db:us-east-1:123456789:dbuser:*/iam_db_user"
        }
    ]
}

# 2. Enable IAM authentication on RDS instance
aws rds modify-db-instance \
    --db-instance-identifier mydb \
    --enable-iam-database-authentication

# 3. Create database user and grant IAM authentication
# In PostgreSQL:
CREATE USER iam_db_user;
GRANT rds_iam TO iam_db_user;
GRANT ALL PRIVILEGES ON DATABASE proddb TO iam_db_user;

# In MySQL:
CREATE USER iam_db_user IDENTIFIED WITH AWSAuthenticationPlugin AS 'RDS';
GRANT ALL PRIVILEGES ON proddb.* TO iam_db_user;
```

**Advantages:**
- **No passwords** - uses IAM roles
- Automatic credential rotation (tokens expire in 15 min)
- Centralized access control via IAM
- Audit via CloudTrail
- Works with EC2, ECS, Lambda, etc.

---

### Azure Managed Identity for Azure SQL

```python
from azure.identity import DefaultAzureCredential
import struct

def get_azure_sql_token(resource: str = "https://database.windows.net/") -> bytes:
    """
    Get Azure AD token for Azure SQL Database.
    Uses Managed Identity - no credentials needed.
    """
    credential = DefaultAzureCredential()
    token = credential.get_token(resource)

    # Convert token to bytes for SQL Server connection
    token_bytes = token.token.encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)

    return token_struct

# Usage with pyodbc
import pyodbc

token = get_azure_sql_token()

connection_string = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=myserver.database.windows.net;"
    "Database=mydatabase;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)

conn = pyodbc.connect(connection_string, attrs_before={1256: token})
```

---

## Encrypted Configuration Files

### SOPS (Secrets OPerationS)

**Best for:** GitOps, configuration files in version control

```yaml
# secrets.enc.yaml (encrypted with SOPS)
database:
    mysql:
        host: mysql.example.com
        port: ENC[AES256_GCM,data:MTIz,iv:xxx,tag:xxx,type:int]
        password: ENC[AES256_GCM,data:c3VwZXJfc2VjdXJl,iv:xxx,tag:xxx,type:str]
```

```python
import subprocess
import yaml

def load_sops_config(file_path: str) -> dict:
    """
    Decrypt and load SOPS-encrypted configuration file.
    """
    result = subprocess.run(
        ['sops', '--decrypt', file_path],
        capture_output=True,
        text=True,
        check=True
    )
    return yaml.safe_load(result.stdout)

# Usage
config = load_sops_config('secrets.enc.yaml')

from connections import DatabaseConnection
from core import SQLDialect

conn = DatabaseConnection(
    dialect=SQLDialect.MYSQL,
    **config['database']['mysql']
)
```

**Setup:**
```bash
# Install SOPS
# macOS: brew install sops
# Linux: download from GitHub releases

# Configure encryption key (AWS KMS example)
export SOPS_KMS_ARN="arn:aws:kms:us-east-1:123456789:key/xxx"

# Encrypt file
sops --encrypt secrets.yaml > secrets.enc.yaml

# Decrypt (automatic when reading)
sops secrets.enc.yaml

# Safe to commit secrets.enc.yaml to git!
```

---

## Certificate-Based Authentication

### PostgreSQL Certificate Authentication

```python
from connections import DatabaseConnection
from core import SQLDialect

# No password needed - uses client certificate
conn = DatabaseConnection(
    dialect=SQLDialect.POSTGRES,
    host="postgres.example.com",
    port=5432,
    database="proddb",
    user="cert_user",
    ssl_cert="/path/to/client-cert.pem",
    ssl_key="/path/to/client-key.pem",
    ssl_ca="/path/to/ca-cert.pem"
)
```

**Setup:**
```bash
# Generate client certificate
openssl req -new -nodes -text -out client.csr \
    -keyout client-key.pem -subj "/CN=cert_user"

# Sign with CA
openssl x509 -req -in client.csr -text -days 365 \
    -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial \
    -out client-cert.pem

# Configure PostgreSQL to require certificates
# In postgresql.conf:
ssl = on
ssl_ca_file = '/path/to/ca-cert.pem'

# In pg_hba.conf:
hostssl all cert_user all cert clientcert=verify-full
```

---

## Comparison Matrix

| Solution | Best For | Security | Ease of Use | Cost | Rotation |
|----------|----------|----------|-------------|------|----------|
| **AWS Secrets Manager** | AWS workloads | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $ | Automatic |
| **Google Secret Manager** | GCP workloads | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $ | Manual |
| **Azure Key Vault** | Azure workloads | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $ | Manual |
| **HashiCorp Vault** | Multi-cloud, On-prem | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Free/$$$ | Automatic |
| **IAM Authentication** | AWS RDS, Azure SQL | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Free | Automatic |
| **Python Keyring** | Local dev, Desktop apps | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free | Manual |
| **Pass** | Unix CLI | ⭐⭐⭐⭐ | ⭐⭐⭐ | Free | Manual |
| **SOPS** | GitOps, Config files | ⭐⭐⭐⭐ | ⭐⭐⭐ | Free | Manual |
| **Certificates** | High security | ⭐⭐⭐⭐⭐ | ⭐⭐ | Free | Manual |
| **Environment Variables** | None (least secure) | ⭐ | ⭐⭐⭐⭐⭐ | Free | Manual |

## Recommendations

### Development
- **Local**: Python Keyring or Pass
- **Team**: SOPS + git

### Production
- **AWS**: IAM Authentication (RDS) or Secrets Manager
- **GCP**: Secret Manager + Workload Identity
- **Azure**: Managed Identity + Key Vault
- **Multi-cloud**: HashiCorp Vault
- **On-premise**: HashiCorp Vault or certificate-based auth

### Key Principles
1. **Never** store credentials in code or unencrypted config files
2. **Prefer** IAM/Managed Identity (no credentials at all)
3. **Use** cloud secrets managers for cloud workloads
4. **Rotate** credentials regularly (or use dynamic credentials)
5. **Audit** all credential access
6. **Encrypt** credentials at rest and in transit
7. **Limit** credential scope (least privilege)

