"""Code Editor Pro Server - Advanced code analysis and transformation tools."""

from .server import mcp

__version__ = "0.1.0"


def main():
    """Entry point for code_editor_pro module - runs as MCP server."""
    from .server import mcp
    mcp.run()


__all__ = ["main", "mcp", "__version__"]
