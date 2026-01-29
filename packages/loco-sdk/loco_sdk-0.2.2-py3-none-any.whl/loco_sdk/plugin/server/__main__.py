"""
Entry point for running plugin server as module.

Usage:
    python -m loco_sdk.plugin.server [plugin_dir]

If plugin_dir not provided, uses current working directory.
Expects nodes/ directory to exist in plugin_dir.

Example:
    cd plugins/loco/gmail@1.0.0/
    python -m loco_sdk.plugin.server
"""

import asyncio
import logging
import sys
from pathlib import Path

from loco_sdk.plugin.server import main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    # Parse plugin directory from args (convert to absolute path)
    plugin_dir = (
        Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    )
    asyncio.run(main(plugin_dir))
