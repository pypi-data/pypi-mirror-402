"""
VAP MCP Server - Media generation tools for Claude Desktop.

This package provides an MCP (Model Context Protocol) server that enables
Claude Desktop to generate AI images and videos via the VAP API.

Quick Start:
    1. Install: pip install vap-mcp
    2. Configure Claude Desktop with your VAP_API_KEY
    3. Ask Claude to generate images or videos!

Example Claude Desktop config:
    {
        "mcpServers": {
            "vap": {
                "command": "uvx",
                "args": ["vap-mcp"],
                "env": {"VAP_API_KEY": "vap_xxx"}
            }
        }
    }
"""

__version__ = "0.1.0"
__author__ = "VAP Team"

from .server import main, run_server

__all__ = ["main", "run_server", "__version__"]