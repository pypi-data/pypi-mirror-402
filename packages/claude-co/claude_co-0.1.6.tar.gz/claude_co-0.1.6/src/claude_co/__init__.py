"""Claude-Co: Multi-agent coordination for Claude Code."""

from .client import CoordinatorClient, load_config, find_config_file
from .server import main

__version__ = "0.1.3"
__all__ = ["CoordinatorClient", "load_config", "find_config_file", "main"]
