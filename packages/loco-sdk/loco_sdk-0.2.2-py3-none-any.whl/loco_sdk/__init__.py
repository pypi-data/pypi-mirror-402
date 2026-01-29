"""
Loco SDK

Public API for plugin development.

This module provides a compatibility layer for existing plugins.
New code should import from loco_sdk.plugin instead.
"""

# NEW: Import from unified plugin module
from loco_sdk.plugin import (
    AuthContext,
    AuthenticationError,
    ExtensionPlugin,
    ManifestLoadError,
    NodePlugin,
    OAuthError,
    OAuthProviderError,
    OAuthRefreshError,
    PluginBase,
    PluginError,
    TriggerPlugin,
    ValidationError,
)

from loco_sdk.version import __version__

__all__ = [
    # Version
    "__version__",
    # Core classes
    "PluginBase",
    "NodePlugin",
    "ExtensionPlugin",
    "TriggerPlugin",
    # Exceptions
    "PluginError",
    "AuthenticationError",
    "ValidationError",
    "ManifestLoadError",
    "OAuthError",
    "OAuthProviderError",
    "OAuthRefreshError",
    # Auth
    "AuthContext",
]
