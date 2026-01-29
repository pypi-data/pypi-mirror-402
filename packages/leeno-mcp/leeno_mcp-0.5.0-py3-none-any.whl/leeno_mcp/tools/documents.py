"""
MCP Tools for document operations.
"""

import logging
from typing import Optional

from mcp.server import FastMCP
from mcp.types import TextContent

from ..wrappers import DocumentWrapper, create_document, open_document, get_document
from ..connection import get_pool
from ..utils.exceptions import LeenoMCPError

logger = logging.getLogger(__name__)


def register_document_tools(server: FastMCP):
    """Register document management tools with the MCP server."""

    @server.tool()
    async def leeno_document_create(template: str = "computo") -> list[TextContent]:
        """
        Create a new LeenO document from template.

        Args:
            template: Template type - "computo" (default) or "usobollo"

        Returns:
            Document ID and info
        """
        try:
            wrapper = create_document(template)
            info = wrapper.get_info()

            return [TextContent(
                type="text",
                text=f"Document created successfully.\n"
                     f"doc_id: {info.doc_id}\n"
                     f"is_leeno: {info.is_leeno}\n"
                     f"sheets: {', '.join(info.sheets)}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_document_open(path: str, read_only: bool = False) -> list[TextContent]:
        """
        Open an existing LeenO document.

        Args:
            path: Full path to the document file
            read_only: Open in read-only mode

        Returns:
            Document ID and info
        """
        try:
            wrapper = open_document(path, read_only)
            info = wrapper.get_info()

            return [TextContent(
                type="text",
                text=f"Document opened successfully.\n"
                     f"doc_id: {info.doc_id}\n"
                     f"path: {info.path}\n"
                     f"is_leeno: {info.is_leeno}\n"
                     f"sheets: {', '.join(info.sheets)}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error opening document: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_document_save(doc_id: str, path: Optional[str] = None) -> list[TextContent]:
        """
        Save a document.

        Args:
            doc_id: Document ID
            path: Path to save to (optional, uses current path if not specified)

        Returns:
            Success status and path
        """
        try:
            wrapper = get_document(doc_id)
            saved_path = wrapper.save(path)

            return [TextContent(
                type="text",
                text=f"Document saved successfully.\n"
                     f"path: {saved_path}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_document_close(doc_id: str) -> list[TextContent]:
        """
        Close a document.

        Args:
            doc_id: Document ID to close

        Returns:
            Success status
        """
        try:
            wrapper = get_document(doc_id)
            wrapper.close()

            return [TextContent(
                type="text",
                text=f"Document {doc_id} closed successfully."
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error closing document: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_document_list() -> list[TextContent]:
        """
        List all open documents.

        Returns:
            List of open documents with their info
        """
        try:
            pool = get_pool()
            documents = pool.list_all()

            if not documents:
                return [TextContent(type="text", text="No documents currently open.")]

            lines = ["Open documents:"]
            for doc in documents:
                lines.append(
                    f"- {doc.doc_id}: {doc.title} "
                    f"({'LeenO' if doc.is_leeno else 'non-LeenO'}) "
                    f"{'[modified]' if doc.modified else ''}"
                )

            return [TextContent(type="text", text="\n".join(lines))]

        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_document_info(doc_id: str) -> list[TextContent]:
        """
        Get detailed information about a document.

        Args:
            doc_id: Document ID

        Returns:
            Document information including sheets and statistics
        """
        try:
            wrapper = get_document(doc_id)
            info = wrapper.get_info()
            stats = wrapper.get_stats()

            lines = [
                f"Document: {info.title}",
                f"ID: {info.doc_id}",
                f"Path: {info.path or 'Not saved'}",
                f"Is LeenO: {info.is_leeno}",
                f"Modified: {info.modified}",
                f"Sheets: {', '.join(info.sheets)}",
                "",
                "Statistics:"
            ]

            if info.is_leeno:
                lines.extend([
                    f"  Computo voci: {stats.num_voci_computo}",
                    f"  Computo totale: € {stats.totale_computo:,.2f}",
                    f"  Sicurezza: € {stats.totale_sicurezza:,.2f}",
                    f"  Manodopera: € {stats.totale_manodopera:,.2f}",
                    f"  Capitoli: {stats.num_capitoli}",
                    f"  Prezzi in elenco: {stats.num_prezzi}",
                ])

                if stats.has_contabilita:
                    lines.extend([
                        f"  SAL emessi: {stats.num_sal}",
                        f"  Totale contabilità: € {stats.totale_contabilita:,.2f}",
                    ])

                if stats.has_variante:
                    lines.append(f"  Totale variante: € {stats.totale_variante:,.2f}")

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error getting document info: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
