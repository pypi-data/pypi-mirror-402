"""Barie Facia MCP Server - facial analysis tools via the Model Context Protocol."""

__version__ = "0.1.0"

from facia_mcp.client import FaciaClient
from facia_mcp.server import cli_main

__all__ = ["FaciaClient", "cli_main"]
