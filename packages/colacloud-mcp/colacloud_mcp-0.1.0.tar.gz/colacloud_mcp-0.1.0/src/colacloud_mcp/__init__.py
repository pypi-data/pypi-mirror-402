"""COLA Cloud MCP Server - access US alcohol label data from AI assistants."""

from colacloud_mcp.server import mcp

__all__ = ["mcp", "main"]


def main():
    """Entry point for the colacloud-mcp command."""
    mcp.run()
