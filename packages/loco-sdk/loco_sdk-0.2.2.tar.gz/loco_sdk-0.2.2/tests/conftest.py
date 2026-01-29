"""Test configuration and fixtures."""

import pytest


@pytest.fixture
def mock_auth_oauth2():
    """Mock OAuth2 authentication data."""
    return {
        "auth_type": "oauth2",
        "provider": "google",
        "access_token": "ya29.fake_token",
        "refresh_token": "1//fake_refresh",
        "token_type": "Bearer",
        "expires_at": "2026-12-31T23:59:59+00:00",
        "scopes": [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
        ],
        "extra": {
            "credential_id": "test_credential_123",
        },
    }


@pytest.fixture
def mock_auth_api_key():
    """Mock API key authentication data."""
    return {
        "auth_type": "api_key",
        "api_key": "sk-fake_api_key_12345",
        "header_name": "X-API-Key",
        "prefix": "",
    }


@pytest.fixture
def mock_auth_basic():
    """Mock basic authentication data."""
    return {
        "auth_type": "basic",
        "username": "testuser",
        "password": "testpass123",
    }


@pytest.fixture
def mock_context(mock_auth_oauth2):
    """Mock workflow execution context."""
    return {
        "sys_vars": {
            "timestamp": "2026-01-14T10:00:00+00:00",
            "user_id": "user_123",
            "username": "admin",
            "app_id": "app_456",
            "workflow_id": "workflow_789",
        },
        "app_vars": {},
        "workflow_vars": {},
        "auth": mock_auth_oauth2,
    }
