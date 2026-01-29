"""Plugin server for executing nodes via JSON-RPC 2.0.

This server runs as a persistent process for warm execution of plugin nodes.
It discovers and loads NodePlugin classes from nodes/ directory, then
listens for JSON-RPC requests via stdin and responds via stdout.

Key features:
- Auto-discovery of NodePlugin classes
- ThreadPool for concurrent execution
- JSON-RPC 2.0 protocol support
- Health check (ping) endpoint
- Graceful shutdown
"""

import asyncio
import json
import logging
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from pathlib import Path
from typing import Any

from loco_sdk.plugin import NodePlugin

logger = logging.getLogger(__name__)


class PluginServer:
    """
    Persistent plugin server for warm execution.

    Discovers NodePlugin classes in nodes/ directory and executes them
    via JSON-RPC 2.0 protocol over stdin/stdout.

    Protocol:
        Request: {"jsonrpc": "2.0", "method": "execute_node", "params": {...}, "id": 1}
        Response: {"jsonrpc": "2.0", "result": {...}, "id": 1}
        Error: {"jsonrpc": "2.0", "error": {"code": -32000, "message": "..."}, "id": 1}

    Methods:
        - execute_node: Execute a plugin node
        - ping: Health check
        - shutdown: Graceful shutdown

    Args:
        plugin_dir: Path to plugin directory (must contain nodes/)
        max_workers: ThreadPool size for concurrent execution
    """

    def __init__(self, plugin_dir: Path, max_workers: int = 10):
        self.plugin_dir = plugin_dir
        self.nodes_dir = plugin_dir / "nodes"
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.nodes: dict[str, type[NodePlugin]] = {}
        self.running = False

    def discover_nodes(self) -> dict[str, type[NodePlugin]]:
        """
        Discover and load all NodePlugin classes from nodes/ directory.

        Returns:
            Dict mapping node names to NodePlugin classes

        Raises:
            FileNotFoundError: If nodes/ directory doesn't exist
        """
        if not self.nodes_dir.exists():
            raise FileNotFoundError(
                f"Nodes directory not found: {self.nodes_dir}"
            )

        nodes = {}
        sys.path.insert(0, str(self.plugin_dir))

        try:
            for node_file in self.nodes_dir.glob("*.py"):
                if node_file.name.startswith("_"):
                    continue

                module_name = f"nodes.{node_file.stem}"
                try:
                    module = import_module(module_name)

                    # Find NodePlugin subclasses
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, NodePlugin)
                            and attr is not NodePlugin
                        ):
                            node_name = node_file.stem
                            nodes[node_name] = attr
                            logger.info(
                                f"Loaded node: {node_name} ({attr.__name__})"
                            )
                            break

                except Exception as e:
                    logger.error(f"Failed to load node {node_file.name}: {e}")
                    traceback.print_exc()

        finally:
            sys.path.pop(0)

        return nodes

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Handle JSON-RPC 2.0 request.

        Args:
            request: JSON-RPC request dict

        Returns:
            JSON-RPC response dict
        """
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        try:
            if method == "execute_node":
                result = await self._execute_node(params)
                return {"jsonrpc": "2.0", "result": result, "id": request_id}

            elif method == "ping":
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "status": "ok",
                        "nodes": list(self.nodes.keys()),
                    },
                    "id": request_id,
                }

            elif method == "shutdown":
                self.running = False
                return {
                    "jsonrpc": "2.0",
                    "result": {"status": "shutting_down"},
                    "id": request_id,
                }

            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                    "id": request_id,
                }

        except Exception as e:
            logger.error(f"Request handling error: {e}")
            traceback.print_exc()
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
                "id": request_id,
            }

    async def _execute_node(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a plugin node.

        Args:
            params: Request parameters containing:
                - node_name: Name of the node to execute
                - inputs: Node inputs
                - context: Execution context

        Returns:
            Node execution result

        Raises:
            ValueError: If node not found or parameters invalid
        """
        node_name = params.get("node_name")
        if not node_name:
            raise ValueError("Missing required parameter: node_name")

        node_class = self.nodes.get(node_name)
        if not node_class:
            raise ValueError(f"Node not found: {node_name}")

        inputs = params.get("inputs", {})
        context = params.get("context", {})

        # Execute in thread pool (blocking operations)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self._execute_node_sync, node_class, inputs, context
        )

        return result

    def _execute_node_sync(
        self,
        node_class: type[NodePlugin],
        inputs: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Synchronous node execution (runs in thread pool).

        Args:
            node_class: NodePlugin class to instantiate
            inputs: Node inputs
            context: Execution context

        Returns:
            Node execution result
        """
        node = node_class()

        # Run async execute in new event loop (thread-safe)
        result = asyncio.run(node.execute(inputs, context))

        return result

    async def run(self):
        """
        Run plugin server main loop.

        Listens for JSON-RPC requests on stdin, executes them,
        and sends responses to stdout.
        """
        self.running = True

        # Discover nodes
        logger.info(f"Discovering nodes in {self.nodes_dir}")
        self.nodes = self.discover_nodes()
        logger.info(
            f"Loaded {len(self.nodes)} nodes: {list(self.nodes.keys())}"
        )

        # Signal ready
        ready_message = json.dumps(
            {"status": "ready", "nodes": list(self.nodes.keys())}
        )
        print(ready_message, flush=True)

        # Main loop: read stdin, process, write stdout
        logger.info("Plugin server ready, listening for requests...")

        try:
            while self.running:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    logger.info("EOF received, shutting down")
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    response_json = json.dumps(response)
                    print(response_json, flush=True)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": "Parse error"},
                        "id": None,
                    }
                    print(json.dumps(error_response), flush=True)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")

        finally:
            logger.info("Shutting down plugin server")
            self.executor.shutdown(wait=True)


async def main(plugin_dir: Path | None = None):
    """
    Main entry point for plugin server.

    Args:
        plugin_dir: Path to plugin directory. If None, uses current directory.
    """
    if plugin_dir is None:
        plugin_dir = Path.cwd()

    server = PluginServer(plugin_dir)
    await server.run()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Parse plugin directory from args
    plugin_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    asyncio.run(main(plugin_dir))
