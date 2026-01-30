"""
Zotero MCP Lite - A lightweight Model Context Protocol server for Zotero.

Provides 9 atomic tools for AI assistants to interact with Zotero libraries.
"""

from ._version import __version__
from .server import mcp

__all__ = ["__version__", "mcp"]
