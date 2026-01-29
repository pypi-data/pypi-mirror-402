"""claude-co: Multi-agent coordination for AI coding assistants."""

from .client import CoordinatorClient, load_config, find_config_file
from .server import main

__version__ = "0.2.0"
__all__ = ["CoordinatorClient", "load_config", "find_config_file", "main"]
