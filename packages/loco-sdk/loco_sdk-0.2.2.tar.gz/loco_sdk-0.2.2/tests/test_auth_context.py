"""Tests for AuthContext class."""

import pytest

from loco_sdk.plugin import AuthContext


def test_auth_context_oauth2_get_header(mock_auth_oauth2):
    """Test OAuth2 header generation."""
    auth = AuthContext(mock_auth_oauth2)
    header = auth.get_header()

    assert "Authorization" in header
    assert header["Authorization"] == "Bearer ya29.fake_token"


def test_auth_context_api_key_get_header(mock_auth_api_key):
    """Test API key header generation."""
    auth = AuthContext(mock_auth_api_key)
    header = auth.get_header()

    assert "X-API-Key" in header
    assert header["X-API-Key"] == "sk-fake_api_key_12345"


def test_auth_context_basic_get_header(mock_auth_basic):
    """Test basic auth header generation."""
    auth = AuthContext(mock_auth_basic)
    header = auth.get_header()

    assert "Authorization" in header
    assert header["Authorization"].startswith("Basic ")


def test_auth_context_get_token_oauth2(mock_auth_oauth2):
    """Test getting OAuth2 token."""
    auth = AuthContext(mock_auth_oauth2)
    token = auth.get_token()

    assert token == "ya29.fake_token"


def test_auth_context_get_token_api_key(mock_auth_api_key):
    """Test getting API key."""
    auth = AuthContext(mock_auth_api_key)
    token = auth.get_token()

    assert token == "sk-fake_api_key_12345"


def test_auth_context_is_expired_future():
    """Test token expiry check - future date."""
    auth = AuthContext(
        {
            "auth_type": "oauth2",
            "access_token": "token",
            "expires_at": "2099-12-31T23:59:59+00:00",
        }
    )

    assert not auth.is_expired()


def test_auth_context_is_expired_past():
    """Test token expiry check - past date."""
    auth = AuthContext(
        {
            "auth_type": "oauth2",
            "access_token": "token",
            "expires_at": "2020-01-01T00:00:00+00:00",
        }
    )

    assert auth.is_expired()


def test_auth_context_is_expired_no_expiry():
    """Test token expiry check - no expiry date."""
    auth = AuthContext(
        {
            "auth_type": "api_key",
            "api_key": "key",
        }
    )

    assert not auth.is_expired()


def test_auth_context_properties(mock_auth_oauth2):
    """Test AuthContext properties."""
    auth = AuthContext(mock_auth_oauth2)

    assert auth.auth_type == "oauth2"
    assert auth.provider == "google"
    assert len(auth.scopes) == 2
    assert auth.credential_id == "test_credential_123"


def test_auth_context_dict_access(mock_auth_oauth2):
    """Test dict-like access."""
    auth = AuthContext(mock_auth_oauth2)

    assert auth["access_token"] == "ya29.fake_token"
    assert auth.get("token_type") == "Bearer"
    assert auth.get("nonexistent", "default") == "default"


def test_auth_context_invalid_type():
    """Test unsupported auth type."""
    auth = AuthContext(
        {
            "auth_type": "unsupported",
        }
    )

    with pytest.raises(ValueError, match="Unsupported auth type"):
        auth.get_header()


def test_auth_context_missing_token():
    """Test missing token."""
    auth = AuthContext(
        {
            "auth_type": "oauth2",
        }
    )

    with pytest.raises(ValueError, match="access_token is missing"):
        auth.get_header()


def test_auth_context_repr(mock_auth_oauth2):
    """Test string representation."""
    auth = AuthContext(mock_auth_oauth2)
    repr_str = repr(auth)

    assert "AuthContext" in repr_str
    assert "oauth2" in repr_str
    assert "google" in repr_str
