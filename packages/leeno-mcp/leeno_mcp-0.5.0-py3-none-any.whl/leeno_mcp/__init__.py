"""
LeenO MCP Server - Computi Metrici management through LibreOffice headless.

This package provides an MCP (Model Context Protocol) server for managing
LeenO documents through LibreOffice in headless mode.

Usage:
    # Start LibreOffice headless first:
    # soffice --headless --accept="socket,host=localhost,port=2002;urp;"

    # Then run the server:
    # leeno-mcp

Example:
    from leeno_mcp.server import create_server, run_server

    server = create_server()
    asyncio.run(run_server(server))
"""

__version__ = "0.1.0"
__author__ = "LeenO Team"

from .server import create_server, main

__all__ = [
    "__version__",
    "create_server",
    "main",
]
