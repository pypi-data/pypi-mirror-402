"""Barie AML Watcher MCP Server - A Model Context Protocol server for AML Watcher."""

__version__ = "0.1.0"

from aml_watcher_mcp.client import AMLWatcherClient
from aml_watcher_mcp.server import cli_main

__all__ = ["AMLWatcherClient", "cli_main"]
