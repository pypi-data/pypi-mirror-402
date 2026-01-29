"""Tests for exception classes."""

from loco_sdk.plugin import (
    AuthenticationError,
    ManifestLoadError,
    OAuthError,
    OAuthProviderError,
    OAuthRefreshError,
    PluginError,
    ValidationError,
)


def test_plugin_error():
    """Test base PluginError."""
    error = PluginError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


def test_authentication_error():
    """Test AuthenticationError."""
    error = AuthenticationError("Invalid credentials")
    assert str(error) == "Invalid credentials"
    assert isinstance(error, PluginError)


def test_validation_error():
    """Test ValidationError."""
    error = ValidationError("Invalid input format")
    assert str(error) == "Invalid input format"
    assert isinstance(error, PluginError)


def test_manifest_load_error():
    """Test ManifestLoadError."""
    error = ManifestLoadError("Failed to parse plugin.yaml")
    assert str(error) == "Failed to parse plugin.yaml"
    assert isinstance(error, PluginError)


def test_oauth_error():
    """Test base OAuthError."""
    error = OAuthError("OAuth failed")
    assert str(error) == "OAuth failed"
    assert isinstance(error, PluginError)


def test_oauth_provider_error():
    """Test OAuthProviderError."""
    error = OAuthProviderError(
        provider_name="google",
        error="invalid_grant",
        error_description="Token has been expired or revoked",
    )

    assert "google" in str(error)
    assert "invalid_grant" in str(error)
    assert "Token has been expired" in str(error)
    assert error.provider_name == "google"
    assert error.error == "invalid_grant"
    assert isinstance(error, OAuthError)


def test_oauth_provider_error_no_description():
    """Test OAuthProviderError without description."""
    error = OAuthProviderError(
        provider_name="github",
        error="access_denied",
    )

    assert "github" in str(error)
    assert "access_denied" in str(error)
    assert error.error_description is None


def test_oauth_refresh_error():
    """Test OAuthRefreshError."""
    error = OAuthRefreshError(
        plugin_id="loco/gmail",
        provider_name="google",
        reason="Refresh token expired",
    )

    assert "loco/gmail" in str(error)
    assert "google" in str(error)
    assert "Refresh token expired" in str(error)
    assert error.plugin_id == "loco/gmail"
    assert error.provider_name == "google"
    assert isinstance(error, OAuthError)


def test_oauth_refresh_error_no_reason():
    """Test OAuthRefreshError without reason."""
    error = OAuthRefreshError(
        plugin_id="loco/slack",
        provider_name="slack",
    )

    assert "loco/slack" in str(error)
    assert "slack" in str(error)
    assert error.reason is None
