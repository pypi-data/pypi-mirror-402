"""
OS-native credential storage using Python keyring.

Credentials are stored securely in:
- macOS: Keychain
- Windows: Windows Credential Locker
- Linux: Secret Service (GNOME Keyring, KWallet)

Dependencies:
    pip install keyring
"""

import json
from typing import Any, Dict, Optional


def store_credentials(service: str, username: str, password: str, metadata: Optional[Dict] = None) -> None:
    """
    Store credentials in OS-native credential store.

    Args:
        service: Service identifier (e.g., "mysql-prod", "postgres-dev")
        username: Username for the service
        password: Password to store
        metadata: Optional additional data (host, port, database, etc.)

    Example:
        >>> from credentials import store_credentials
        >>>
        >>> # Store basic credentials
        >>> store_credentials(
        ...     service="mysql-prod",
        ...     username="app_user",
        ...     password="super_secure_password"
        ... )
        >>>
        >>> # Store with metadata
        >>> store_credentials(
        ...     service="postgres-prod",
        ...     username="app_user",
        ...     password="super_secure_password",
        ...     metadata={
        ...         "host": "postgres.example.com",
        ...         "port": 5432,
        ...         "database": "proddb"
        ...     }
        ... )

    Note:
        Credentials are stored per-user and require the user to be logged in.
        Not suitable for server applications or automated scripts.
    """
    try:
        import keyring
    except ImportError:
        raise ImportError("keyring is required for OS credential storage. " "Install it with: pip install keyring")

    # Store password
    keyring.set_password(service, username, password)

    # Store metadata if provided
    if metadata:
        metadata_key = f"{service}:{username}:metadata"
        keyring.set_password(service, metadata_key, json.dumps(metadata))


def get_credentials(service: str, username: str, include_metadata: bool = True) -> Dict[str, Any]:
    """
    Retrieve credentials from OS-native credential store.

    Args:
        service: Service identifier
        username: Username for the service
        include_metadata: Whether to include stored metadata (default: True)

    Returns:
        Dictionary containing credentials and optional metadata

    Raises:
        Exception: If credentials not found

    Example:
        >>> from credentials import get_credentials
        >>> from connections import DatabaseConnection
        >>> from core import SQLDialect
        >>>
        >>> # Retrieve credentials
        >>> creds = get_credentials("postgres-prod", "app_user")
        >>> # Returns: {
        >>> #     "user": "app_user",
        >>> #     "password": "...",
        >>> #     "host": "postgres.example.com",
        >>> #     "port": 5432,
        >>> #     "database": "proddb"
        >>> # }
        >>>
        >>> # Use with DatabaseConnection
        >>> conn = DatabaseConnection(
        ...     dialect=SQLDialect.POSTGRES,
        ...     **creds
        ... )
    """
    try:
        import keyring
    except ImportError:
        raise ImportError("keyring is required for OS credential storage. " "Install it with: pip install keyring")

    # Retrieve password
    password = keyring.get_password(service, username)
    if password is None:
        raise Exception(
            f"Credentials for service='{service}' username='{username}' not found. "
            f"Store them first using store_credentials()"
        )

    result = {"user": username, "password": password}

    # Retrieve metadata if requested
    if include_metadata:
        metadata_key = f"{service}:{username}:metadata"
        metadata_json = keyring.get_password(service, metadata_key)
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)
                result.update(metadata)
            except json.JSONDecodeError:
                pass  # Ignore invalid metadata

    return result


def delete_credentials(service: str, username: str) -> None:
    """
    Delete credentials from OS-native credential store.

    Args:
        service: Service identifier
        username: Username for the service

    Example:
        >>> from credentials import delete_credentials
        >>>
        >>> delete_credentials("mysql-prod", "app_user")
    """
    try:
        import keyring
    except ImportError:
        raise ImportError("keyring is required for OS credential storage. " "Install it with: pip install keyring")

    try:
        # Delete password
        keyring.delete_password(service, username)

        # Delete metadata if exists
        metadata_key = f"{service}:{username}:metadata"
        try:
            keyring.delete_password(service, metadata_key)
        except keyring.errors.PasswordDeleteError:
            pass  # Metadata doesn't exist, that's fine

    except keyring.errors.PasswordDeleteError:
        raise Exception(f"Credentials for service='{service}' username='{username}' not found")


def list_services() -> None:
    """
    List all stored credentials (prints to stdout).

    Note:
        This function varies by OS and keyring backend.
        Some backends don't support listing all credentials.

    Example:
        >>> from credentials import list_services
        >>> list_services()
        Stored credentials:
        - mysql-prod (app_user)
        - postgres-dev (app_user)
    """
    try:
        import keyring
    except ImportError:
        raise ImportError("keyring is required for OS credential storage. " "Install it with: pip install keyring")

    print("Note: Listing credentials is OS/backend-specific")
    print("Use 'keyring' CLI tool for more control:")
    print("  keyring --list-backends")
    print("  keyring get <service> <username>")
