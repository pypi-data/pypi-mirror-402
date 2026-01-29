"""Authentication context wrapper.

Provides methods for accessing auth credentials in a plugin-friendly way.
"""

from datetime import datetime
from typing import Any


class AuthContext:
    """
    Authentication context wrapper.

    Wraps raw auth dict from workflow context to provide
    convenient methods for plugins to access credentials.

    Supports:
    - OAuth2 (access_token, refresh_token)
    - API Key (api_key, header_name, prefix)
    - Basic Auth (username, password)

    Example:
        # In plugin execute():
        auth = context.get("auth")
        if auth:
            headers = auth.get_header()
            # Use headers for API calls
    """

    def __init__(self, data: dict[str, Any]):
        """
        Initialize auth context.

        Args:
            data: Raw auth dict with credentials
        """
        self._data = data

    def get_header(self) -> dict[str, str]:
        """
        Get HTTP Authorization header.

        Returns:
            Dictionary with Authorization header
            Example: {"Authorization": "Bearer ya29.xxx"}

        Raises:
            ValueError: If auth type is unsupported
        """
        auth_type = self._data.get("auth_type")

        if auth_type == "oauth2":
            token_type = self._data.get("token_type", "Bearer")
            access_token = self._data.get("access_token")
            if not access_token:
                raise ValueError("OAuth2 access_token is missing")
            return {"Authorization": f"{token_type} {access_token}"}

        elif auth_type == "api_key":
            api_key = self._data.get("api_key")
            if not api_key:
                raise ValueError("API key is missing")
            header_name = self._data.get("header_name", "Authorization")
            prefix = self._data.get("prefix", "Bearer")
            value = f"{prefix} {api_key}" if prefix else api_key
            return {header_name: value}

        elif auth_type == "basic":
            import base64

            username = self._data.get("username", "")
            password = self._data.get("password", "")
            credentials = base64.b64encode(
                f"{username}:{password}".encode()
            ).decode()
            return {"Authorization": f"Basic {credentials}"}

        else:
            raise ValueError(f"Unsupported auth type: {auth_type}")

    def get_token(self) -> str:
        """
        Get access token or API key.

        Returns:
            Token string

        Raises:
            ValueError: If no token available
        """
        token = self._data.get("access_token") or self._data.get("api_key")
        if not token:
            raise ValueError("No access token or API key available")
        return token

    def is_expired(self) -> bool:
        """
        Check if token is expired.

        Returns:
            True if token is expired, False otherwise
        """
        expires_at = self._data.get("expires_at")
        if not expires_at:
            return False

        try:
            # Parse ISO format datetime
            expiry_time = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )
            return datetime.now(expiry_time.tzinfo) >= expiry_time
        except (ValueError, AttributeError):
            return False

    @property
    def auth_type(self) -> str | None:
        """Authentication type (oauth2, api_key, basic)."""
        return self._data.get("auth_type")

    @property
    def provider(self) -> str | None:
        """OAuth provider name (google, github, etc.)."""
        return self._data.get("provider")

    @property
    def scopes(self) -> list[str]:
        """OAuth scopes."""
        return self._data.get("scopes", [])

    @property
    def credential_id(self) -> str | None:
        """Credential ID for refresh/revoke."""
        extra = self._data.get("extra", {})
        return extra.get("credential_id")

    def __getitem__(self, key: str) -> Any:
        """Dict-like access."""
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get."""
        return self._data.get(key, default)

    def __repr__(self) -> str:
        """String representation."""
        auth_type = self.auth_type or "unknown"
        provider = self.provider or "custom"
        return f"<AuthContext type={auth_type} provider={provider}>"


__all__ = ["AuthContext"]
