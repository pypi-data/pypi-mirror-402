"""Unified plugin development module.

This module consolidates all plugin-related functionality:
- Base classes (NodePlugin, ExtensionPlugin, TriggerPlugin)
- Exceptions (PluginError, AuthenticationError, etc.)
- Contexts (AuthContext)
- Server implementation (plugin server)
"""

# Base classes
from loco_sdk.plugin.base import (
    ExtensionPlugin,
    NodePlugin,
    PluginBase,
    TriggerPlugin,
)

# Contexts
from loco_sdk.plugin.context import AuthContext

# Exceptions
from loco_sdk.plugin.exceptions import (
    AuthenticationError,
    ManifestLoadError,
    OAuthError,
    OAuthProviderError,
    OAuthRefreshError,
    PluginError,
    ValidationError,
)

# File handling for plugins
from loco_sdk.plugin.files import (
    PluginFile,
    create_plugin_file,
    extract_files_from_inputs,
    is_plugin_file,
)

__all__ = [
    # Base classes
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
    # Contexts
    "AuthContext",
    # File handling
    "PluginFile",
    "is_plugin_file",
    "create_plugin_file",
    "extract_files_from_inputs",
]
