"""
AWS Secrets Manager and RDS IAM authentication utilities.

Dependencies:
    pip install boto3
"""

import json
from typing import Dict, Optional

from botocore.exceptions import ClientError


def get_aws_secret(
    secret_name: str, region_name: str = "us-east-1", profile_name: Optional[str] = None
) -> Dict[str, any]:
    """
    Retrieve secret from AWS Secrets Manager.

    Args:
        secret_name: Name or ARN of the secret
        region_name: AWS region (default: us-east-1)
        profile_name: AWS profile name (optional, uses default if not specified)

    Returns:
        Dictionary containing the secret data

    Raises:
        Exception: If secret retrieval fails

    Example:
        >>> from credentials import get_aws_secret
        >>> from connections import DatabaseConnection
        >>> from core import SQLDialect
        >>>
        >>> creds = get_aws_secret("prod/mysql/credentials")
        >>> conn = DatabaseConnection(
        ...     dialect=SQLDialect.MYSQL,
        ...     **creds
        ... )

    Setup:
        # Create secret in AWS
        aws secretsmanager create-secret \\
            --name prod/mysql/credentials \\
            --secret-string '{
                "host": "mysql.example.com",
                "port": 3306,
                "database": "proddb",
                "user": "app_user",
                "password": "super_secure_password"
            }'
    """
    try:
        import boto3
    except ImportError:
        raise ImportError("boto3 is required for AWS Secrets Manager. " "Install it with: pip install boto3")

    session = boto3.session.Session(profile_name=profile_name)
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)

        # Secret can be string or binary
        if "SecretString" in response:
            secret = response["SecretString"]
            try:
                return json.loads(secret)
            except json.JSONDecodeError:
                # Return as-is if not JSON
                return {"value": secret}
        else:
            # Binary secret
            import base64

            return {"value": base64.b64decode(response["SecretBinary"])}

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            raise Exception(f"Secret '{secret_name}' not found in region {region_name}")
        elif error_code == "InvalidRequestException":
            raise Exception(f"Invalid request for secret '{secret_name}': {e}")
        elif error_code == "InvalidParameterException":
            raise Exception(f"Invalid parameter for secret '{secret_name}': {e}")
        elif error_code == "DecryptionFailure":
            raise Exception(f"Cannot decrypt secret '{secret_name}': {e}")
        elif error_code == "InternalServiceError":
            raise Exception(f"AWS service error retrieving secret '{secret_name}': {e}")
        else:
            raise Exception(f"Error retrieving secret '{secret_name}': {e}")


def get_rds_iam_token(
    host: str, port: int, username: str, region: str = "us-east-1", profile_name: Optional[str] = None
) -> str:
    """
    Generate IAM authentication token for RDS/Aurora.

    This eliminates the need for passwords - uses IAM role permissions instead.
    Token is valid for 15 minutes.

    Args:
        host: RDS instance hostname
        port: Database port (3306 for MySQL, 5432 for PostgreSQL)
        username: Database username configured for IAM auth
        region: AWS region (default: us-east-1)
        profile_name: AWS profile name (optional)

    Returns:
        Authentication token (use as password)

    Example:
        >>> from credentials import get_rds_iam_token
        >>> from connections import DatabaseConnection
        >>> from core import SQLDialect
        >>>
        >>> # No password needed - uses IAM role!
        >>> token = get_rds_iam_token(
        ...     host="mydb.123456.us-east-1.rds.amazonaws.com",
        ...     port=5432,
        ...     username="iam_db_user"
        ... )
        >>>
        >>> conn = DatabaseConnection(
        ...     dialect=SQLDialect.POSTGRES,
        ...     host="mydb.123456.us-east-1.rds.amazonaws.com",
        ...     port=5432,
        ...     database="proddb",
        ...     user="iam_db_user",
        ...     password=token,  # Temporary token, not a real password!
        ...     ssl_ca="/path/to/rds-ca-bundle.pem"
        ... )

    Setup:
        # 1. Enable IAM auth on RDS instance
        aws rds modify-db-instance \\
            --db-instance-identifier mydb \\
            --enable-iam-database-authentication

        # 2. Create database user with IAM auth
        # PostgreSQL:
        CREATE USER iam_db_user;
        GRANT rds_iam TO iam_db_user;

        # MySQL:
        CREATE USER iam_db_user IDENTIFIED WITH AWSAuthenticationPlugin AS 'RDS';

        # 3. Grant IAM policy to EC2 role/user
        {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": "rds-db:connect",
                "Resource": "arn:aws:rds-db:us-east-1:123456:dbuser:*/iam_db_user"
            }]
        }
    """
    try:
        import boto3
    except ImportError:
        raise ImportError("boto3 is required for RDS IAM authentication. " "Install it with: pip install boto3")

    session = boto3.session.Session(profile_name=profile_name)
    client = session.client("rds", region_name=region)

    try:
        token = client.generate_db_auth_token(DBHostname=host, Port=port, DBUsername=username, Region=region)
        return token
    except ClientError as e:
        raise Exception(f"Failed to generate RDS IAM token: {e}")
