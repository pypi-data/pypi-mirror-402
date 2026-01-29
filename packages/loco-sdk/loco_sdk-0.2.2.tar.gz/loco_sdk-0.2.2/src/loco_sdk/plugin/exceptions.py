"""Plugin SDK exceptions.

Base exception classes for plugin development.
"""


class PluginError(Exception):
    """Base exception for all plugin errors."""

    pass


class AuthenticationError(PluginError):
    """Authentication failed or credentials invalid."""

    pass


class ValidationError(PluginError):
    """Input validation failed."""

    pass


class ManifestLoadError(PluginError):
    """Exception raised when plugin manifest loading fails.

    This includes issues with:
    - Missing or invalid plugin.yaml
    - Invalid node file references
    - Invalid provider file references
    - YAML parsing errors
    """

    pass


class OAuthError(PluginError):
    """Base exception for OAuth errors."""

    pass


class OAuthProviderError(OAuthError):
    """Error from OAuth provider.

    Raised when the OAuth provider returns an error during
    authorization or token exchange.
    """

    def __init__(
        self,
        provider_name: str,
        error: str,
        error_description: str | None = None,
    ):
        self.provider_name = provider_name
        self.error = error
        self.error_description = error_description
        message = f"OAuth provider '{provider_name}' error: {error}"
        if error_description:
            message += f" - {error_description}"
        super().__init__(message)


class OAuthRefreshError(OAuthError):
    """Failed to refresh OAuth token.

    Raised when automatic token refresh fails, indicating
    the user may need to re-authorize.
    """

    def __init__(
        self,
        plugin_id: str,
        provider_name: str,
        reason: str | None = None,
    ):
        self.plugin_id = plugin_id
        self.provider_name = provider_name
        self.reason = reason
        message = (
            f"Failed to refresh OAuth token for plugin '{plugin_id}' "
            f"provider '{provider_name}'"
        )
        if reason:
            message += f": {reason}"
        super().__init__(message)


__all__ = [
    "PluginError",
    "AuthenticationError",
    "ValidationError",
    "ManifestLoadError",
    "OAuthError",
    "OAuthProviderError",
    "OAuthRefreshError",
]
