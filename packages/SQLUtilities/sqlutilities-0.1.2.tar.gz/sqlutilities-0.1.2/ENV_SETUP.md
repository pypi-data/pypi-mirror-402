# Environment Setup Guide

This guide explains how to configure your environment variables for SQLUtils-Python development and testing.

## Quick Start

1. **Copy the template file:**
   ```bash
   cp .env.template .env
   ```

2. **Edit the `.env` file with your actual credentials:**
   ```bash
   # Use your preferred editor
   nano .env
   # or
   vim .env
   # or
   code .env
   ```

3. **Update the placeholder values:**
   - Change all `your_secure_password_here` to actual strong passwords
   - Update `/path/to/your/credentials.json` for BigQuery
   - Adjust ports if needed to avoid conflicts with other services

4. **Secure your `.env` file:**
   ```bash
   chmod 600 .env
   ```

## Database-Specific Setup

### MySQL
- Default port: `3306`
- Update: `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`
- Start container: `cd tst/docker && bash MYSQL.sh`

### PostgreSQL
- Default port: `54333` (non-standard to avoid conflicts)
- Update: `POSTGRES_PASSWORD`
- Start container: `cd tst/docker && bash PostgreSQL.sh`

### Oracle XE
- Default port: `15210`
- Update: `ORACLE_PASSWORD`
- Service name: `XEPDB1` (pluggable database)
- Start container: `cd tst/docker && bash ORACLE.sh`
- **Note:** Oracle container takes 2-3 minutes to initialize

### SQL Server
- Default port: `14333`
- Update: `SQLSERVER_PASSWORD`
- Password requirements: min 8 chars, uppercase, lowercase, digits, symbols
- Start container: `cd tst/docker && bash SQLSERVER.sh`

### BigQuery
- **Requires a Google Cloud service account:**
  1. Go to [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
  2. Create a service account or use existing
  3. Download JSON credentials file
  4. Update `GOOGLE_APPLICATION_CREDENTIALS` path in `.env`
  5. Update `BIGQUERY_DATASET` name (will be created automatically)

### Redshift (Emulator)
- Default port: `5444`
- Update: `REDSHIFT_POSTGRES_PASSWORD`
- Uses `pgredshift` emulator (not real AWS Redshift)
- Start container: `cd tst/docker && bash REDSHIFT.sh`

### SQLite
- No configuration needed (uses built-in Python sqlite3 module)
- Test database created in temp directory automatically

## Managing Database Containers

### Start All Databases
```bash
cd tst/docker
bash db_test.sh start
```

### Check Database Status
```bash
cd tst/docker
bash db_test.sh status
```

### Stop All Databases
```bash
cd tst/docker
bash db_test.sh stop
```

## Environment Files

### File Structure
```
SQLUtils-Python/
├── .env.template          # Template (committed to git)
├── .env                   # Your config (gitignored, DO NOT commit)
├── tst/docker/.env        # Test DB config (gitignored, DO NOT commit)
└── .gitignore             # Ensures .env files are not committed
```

### Multiple Environments

You can create environment-specific files:

```bash
# Development
.env.dev

# Staging
.env.staging

# Production
.env.production
```

All these files are automatically gitignored. Load them explicitly:

```bash
# Using python-dotenv
from dotenv import load_dotenv
load_dotenv('.env.dev')

# Or using shell
export $(cat .env.dev | xargs)
```

## Security Best Practices

### 1. Never Commit Credentials
- `.env` files are gitignored by default
- Always double-check before committing
- Use `git status` to verify

### 2. Use Strong Passwords
```bash
# Generate strong passwords (Linux/macOS)
openssl rand -base64 32

# Or use a password manager
```

### 3. Restrict File Permissions
```bash
# Only owner can read/write
chmod 600 .env
chmod 600 tst/docker/.env

# Verify permissions
ls -l .env
```

### 4. Rotate Credentials Regularly
- Change passwords periodically
- Update both `.env` and running containers
- For containers: stop, remove, recreate with new credentials

### 5. Use Secrets Management (Production)
For production environments, consider:
- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Secret Manager**

### 6. Environment Variables in CI/CD
For GitHub Actions, GitLab CI, etc.:
- Store secrets in the CI/CD platform's secret manager
- Never hardcode in workflow files
- Use masked variables in logs

## Testing Configuration

### Verify Environment Setup
```bash
# Check if databases are accessible
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('MySQL Host:', os.getenv('MYSQL_HOST'))
print('Postgres Port:', os.getenv('POSTGRES_HOST_PORT'))
print('BigQuery Creds:', os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
"
```

### Run Tests with Specific Database
```bash
# Test only MySQL
pytest UNIT_TESTS/ --dialect=mysql -v

# Test only PostgreSQL
pytest UNIT_TESTS/ --dialect=postgres -v

# Test all available databases
pytest UNIT_TESTS/ -v
```

### Skip Integration Tests
```bash
# Run only unit tests (no database connections needed)
pytest UNIT_TESTS/ --skip-integration -v
```

## Troubleshooting

### Issue: Container port already in use
```bash
# Find what's using the port
lsof -i :3306  # For MySQL

# Change port in .env
MYSQL_HOST_PORT=3307

# Restart container
cd tst/docker && bash MYSQL.sh
```

### Issue: Permission denied on .env
```bash
# Fix permissions
chmod 600 .env

# Verify
ls -l .env
```

### Issue: BigQuery credentials not found
```bash
# Check file exists
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Verify it's a valid JSON file
cat $GOOGLE_APPLICATION_CREDENTIALS | python -m json.tool

# Check permissions
chmod 600 $GOOGLE_APPLICATION_CREDENTIALS
```

### Issue: Oracle container won't start
```bash
# Oracle needs more resources
# Increase Docker Desktop memory to at least 4GB

# Check container logs
docker logs oracle-xe-test

# Wait longer (Oracle takes 2-3 minutes to initialize)
sleep 180
bash tst/docker/db_test.sh status
```

## Additional Resources

- [Docker Setup Guide](tst/docker/README.md)
- [Testing Guide](UNIT_TESTS/README.md)
- [Poetry Installation](https://python-poetry.org/docs/#installation)
- [python-dotenv Documentation](https://pypi.org/project/python-dotenv/)

## Support

If you encounter issues:
1. Check the container logs: `docker logs <container-name>`
2. Verify `.env` file syntax (no spaces around `=`)
3. Ensure all required variables are set (no empty values)
4. Check database status: `cd tst/docker && bash db_test.sh status`

For more help, open an issue on GitHub.
