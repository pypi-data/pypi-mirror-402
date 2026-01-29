"""
Google Cloud Secret Manager utilities.

Dependencies:
    pip install google-cloud-secret-manager
"""

import json
from typing import Dict, Optional


def get_gcp_secret(project_id: str, secret_id: str, version: str = "latest") -> Dict[str, any]:
    """
    Retrieve secret from Google Secret Manager.

    Args:
        project_id: GCP project ID
        secret_id: Secret name
        version: Version ID or "latest" (default: latest)

    Returns:
        Dictionary containing the secret data

    Raises:
        Exception: If secret retrieval fails

    Example:
        >>> from credentials import get_gcp_secret
        >>> from connections import DatabaseConnection
        >>> from core import SQLDialect
        >>>
        >>> creds = get_gcp_secret("my-project", "postgres-prod-credentials")
        >>> conn = DatabaseConnection(
        ...     dialect=SQLDialect.POSTGRES,
        ...     **creds
        ... )

    Setup:
        # Create secret
        echo -n '{
            "host": "postgres.example.com",
            "port": 5432,
            "database": "proddb",
            "user": "app_user",
            "password": "super_secure_password"
        }' | gcloud secrets create postgres-prod-credentials --data-file=-

        # Grant access
        gcloud secrets add-iam-policy-binding postgres-prod-credentials \\
            --member="serviceAccount:app@project.iam.gserviceaccount.com" \\
            --role="roles/secretmanager.secretAccessor"
    """
    try:
        from google.cloud import secretmanager
    except ImportError:
        raise ImportError(
            "google-cloud-secret-manager is required for GCP Secret Manager. "
            "Install it with: pip install google-cloud-secret-manager"
        )

    client = secretmanager.SecretManagerServiceClient()

    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"

    try:
        response = client.access_secret_version(request={"name": name})
        secret_data = response.payload.data.decode("UTF-8")

        try:
            return json.loads(secret_data)
        except json.JSONDecodeError:
            return {"value": secret_data}

    except Exception as e:
        raise Exception(f"Failed to retrieve GCP secret '{secret_id}': {e}")
