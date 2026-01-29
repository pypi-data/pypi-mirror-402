"""Plugin base classes.

This module provides base classes for all plugin types.
Plugins should inherit from these classes instead of workflow engine classes.

Design principles:
- Simple interface: execute(inputs, context) -> dict
- No dependency on workflow engine internals
- Can run standalone on sandbox server
- Type-safe with Pydantic
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)


class PluginBase(ABC):
    """Base class for all plugins.

    Provides common functionality for plugin lifecycle management.
    All plugin types (NodePlugin, ExtensionPlugin, TriggerPlugin) inherit from this.

    Attributes:
        config: Plugin-level configuration (shared across all nodes)
        _initialized: Whether plugin has been initialized
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize plugin.

        Args:
            config: Plugin-level configuration (shared across all nodes)
        """
        self.config = config or {}
        self._initialized = False

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get plugin configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    async def initialize(self) -> None:
        """
        Initialize plugin resources.

        Override this to set up connections, load models, etc.
        Called once when plugin is loaded.
        """
        self._initialized = True

    async def cleanup(self) -> None:
        """
        Cleanup plugin resources.

        Override this to close connections, release resources, etc.
        Called when plugin is unloaded.
        """
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized


class NodePlugin(PluginBase):
    """
    Base class for node plugins.

    Node plugins add new workflow nodes for data processing.
    They provide a simple interface: execute(inputs, context) -> dict

    This is the recommended base class for all plugin nodes.
    It does NOT depend on workflow engine internals (NodeResult, NodeState).

    Example:
        class PythonNode(NodePlugin):
            async def execute(self, inputs, context):
                code = inputs.get("code", "")
                exec(code, exec_globals)
                return {"result": result}

    Lifecycle:
        1. Plugin is instantiated with config
        2. initialize() is called once
        3. execute() is called for each workflow execution
        4. cleanup() is called when plugin is unloaded
    """

    @abstractmethod
    async def execute(
        self, inputs: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute node logic.

        This is the main method that plugins must implement.

        Args:
            inputs: Input values from node configuration.
                   Keys match node definition inputs in YAML.
                   Values are already resolved (templates replaced).
                   Example: {"code": "x + y", "inputs": {"x": 1, "y": 2}}
            context: Workflow execution context.
                    Contains: workflow_id, execution_id, user_id,
                             previous node outputs, auth context, etc.

        Returns:
            Output values as dict.
            Keys should match node definition outputs in YAML.
            Example: {"result": 3, "variables": {"x": 1}}

        Raises:
            Exception: If execution fails. The error will be captured
                      and returned to the workflow engine.
        """
        pass


class ExtensionPlugin(PluginBase):
    """
    Base class for extension plugins.

    Extension plugins extend platform behavior at system level.
    They can hook into workflow lifecycle events.

    Example:
        class LoggingExtension(ExtensionPlugin):
            async def on_workflow_start(self, workflow_id, context):
                logger.info(f"Workflow {workflow_id} started")
    """

    async def on_workflow_start(
        self, workflow_id: str, context: dict[str, Any]
    ) -> None:
        """
        Called when workflow starts.

        Args:
            workflow_id: ID of the starting workflow
            context: Workflow execution context
        """
        pass

    async def on_workflow_end(
        self, workflow_id: str, context: dict[str, Any], success: bool
    ) -> None:
        """
        Called when workflow completes (success or failure).

        Args:
            workflow_id: ID of the completed workflow
            context: Workflow execution context
            success: Whether workflow completed successfully
        """
        pass

    async def on_node_execute(
        self, node_id: str, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Called before each node execution.
        Can modify inputs.

        Args:
            node_id: ID of the node being executed
            inputs: Node inputs (can be modified)

        Returns:
            Modified inputs dict
        """
        return inputs


class TriggerPlugin(PluginBase):
    """
    Base class for trigger plugins.

    Trigger plugins start workflows from external events.
    They listen for events and invoke a callback when triggered.

    Example:
        class WebhookTrigger(TriggerPlugin):
            async def start(self, callback):
                self.callback = callback
                # Start HTTP server to listen for webhooks

            async def stop(self):
                # Stop HTTP server
    """

    @abstractmethod
    async def start(
        self, callback: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Start listening for events.

        Args:
            callback: Async function to call when event occurs.
                     Signature: async def callback(event_data: dict)
                     The event_data will be passed as workflow inputs.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop listening for events."""
        pass


__all__ = [
    "PluginBase",
    "NodePlugin",
    "ExtensionPlugin",
    "TriggerPlugin",
]
