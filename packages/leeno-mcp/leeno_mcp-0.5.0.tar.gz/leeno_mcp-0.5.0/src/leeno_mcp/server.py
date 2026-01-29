"""
LeenO MCP Server - Entry point.

This server provides MCP tools for managing LeenO documents
through LibreOffice running in headless mode.
"""

import asyncio
import logging
import sys
from typing import Optional

from mcp.server import FastMCP

from .config import get_config, ServerConfig
from .connection import get_bridge, get_pool
from .tools import (
    register_document_tools,
    register_computo_tools,
    register_elenco_prezzi_tools,
    register_contabilita_tools,
    register_export_tools,
    register_analisi_tools,
    register_import_tools,
    register_varianti_tools,
    register_giornale_tools,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    config = get_config()

    server = FastMCP(config.name)

    # Register all tools
    register_document_tools(server)
    register_computo_tools(server)
    register_elenco_prezzi_tools(server)
    register_contabilita_tools(server)
    register_export_tools(server)
    register_analisi_tools(server)
    register_import_tools(server)
    register_varianti_tools(server)
    register_giornale_tools(server)

    logger.info(f"LeenO MCP Server {config.version} initialized")

    return server


async def run_server(server: FastMCP):
    """Run the MCP server with stdio transport."""
    logger.info("Starting LeenO MCP Server...")

    # Try to connect to LibreOffice
    try:
        bridge = get_bridge()
        bridge.connect()
        logger.info("Connected to LibreOffice")
    except Exception as e:
        logger.warning(f"Could not connect to LibreOffice: {e}")
        logger.warning("Server will start, but document operations will fail until LibreOffice is available.")

    # Run server using FastMCP's stdio method
    await server.run_stdio_async()


def main():
    """Main entry point."""
    try:
        server = create_server()
        asyncio.run(run_server(server))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            pool = get_pool()
            closed = pool.clear(close=True)
            if closed > 0:
                logger.info(f"Closed {closed} documents")
        except Exception:
            pass


if __name__ == "__main__":
    main()
