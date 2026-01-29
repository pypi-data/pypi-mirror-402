"""Tests for NodePlugin base class."""

import pytest

from loco_sdk import NodePlugin


class TestNode(NodePlugin):
    """Test implementation of NodePlugin."""

    async def execute(self, inputs, context):
        """Echo back inputs."""
        return {
            "echo": inputs,
            "user": context.get("sys_vars", {}).get("username"),
        }


class TestNodeWithInit(NodePlugin):
    """Test node with initialization."""

    def __init__(self):
        super().__init__()
        self.initialized_value = None

    async def initialize(self):
        """Set initialized value."""
        await super().initialize()
        self.initialized_value = "initialized"

    async def execute(self, inputs, context):
        """Return initialized value."""
        return {"value": self.initialized_value}

    async def cleanup(self):
        """Clear initialized value."""
        self.initialized_value = None
        await super().cleanup()


@pytest.mark.asyncio
async def test_node_plugin_execute():
    """Test basic NodePlugin execution."""
    node = TestNode()
    await node.initialize()

    result = await node.execute(
        inputs={"message": "hello"},
        context={"sys_vars": {"username": "testuser"}},
    )

    assert result["echo"]["message"] == "hello"
    assert result["user"] == "testuser"

    await node.cleanup()


@pytest.mark.asyncio
async def test_node_plugin_lifecycle():
    """Test NodePlugin lifecycle."""
    node = TestNodeWithInit()

    # Before initialization
    assert not node.is_initialized
    assert node.initialized_value is None

    # Initialize
    await node.initialize()
    assert node.is_initialized
    assert node.initialized_value == "initialized"

    # Execute
    result = await node.execute({}, {})
    assert result["value"] == "initialized"

    # Cleanup
    await node.cleanup()
    assert not node.is_initialized
    assert node.initialized_value is None


@pytest.mark.asyncio
async def test_node_plugin_with_config():
    """Test NodePlugin with configuration."""
    node = TestNode(config={"api_key": "secret", "timeout": 30})

    assert node.get_config("api_key") == "secret"
    assert node.get_config("timeout") == 30
    assert node.get_config("missing", "default") == "default"


@pytest.mark.asyncio
async def test_node_plugin_context_integration(mock_context):
    """Test NodePlugin with full context."""
    node = TestNode()
    await node.initialize()

    result = await node.execute(
        inputs={"query": "test search"},
        context=mock_context,
    )

    assert result["echo"]["query"] == "test search"
    assert result["user"] == "admin"

    await node.cleanup()
