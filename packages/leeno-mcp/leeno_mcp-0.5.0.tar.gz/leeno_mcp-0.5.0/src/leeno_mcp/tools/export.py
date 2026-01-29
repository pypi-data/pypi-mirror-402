"""
MCP Tools for export operations.
"""

import logging
from typing import Optional, List

from mcp.server import FastMCP
from mcp.types import TextContent

from ..wrappers import ExportWrapper
from ..utils.exceptions import LeenoMCPError

logger = logging.getLogger(__name__)


def register_export_tools(server: FastMCP):
    """Register export tools with the MCP server."""

    @server.tool()
    async def leeno_export_pdf(
        doc_id: str,
        output_path: str,
        sheets: Optional[List[str]] = None
    ) -> list[TextContent]:
        """
        Export document to PDF.

        Args:
            doc_id: Document ID
            output_path: Full path for output PDF file
            sheets: List of sheet names to export (optional, all if not specified)

        Returns:
            Success status and path
        """
        try:
            wrapper = ExportWrapper(doc_id)
            path = wrapper.export_pdf(output_path, sheets)

            return [TextContent(
                type="text",
                text=f"PDF exported successfully.\n"
                     f"path: {path}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_export_csv(
        doc_id: str,
        output_path: str,
        sheet_name: str,
        delimiter: str = ","
    ) -> list[TextContent]:
        """
        Export a sheet to CSV.

        Args:
            doc_id: Document ID
            output_path: Full path for output CSV file
            sheet_name: Name of sheet to export
            delimiter: Field delimiter ("," or ";" or "\\t")

        Returns:
            Success status and path
        """
        try:
            wrapper = ExportWrapper(doc_id)

            # Handle tab delimiter
            if delimiter == "\\t":
                delimiter = "\t"

            path = wrapper.export_csv(output_path, sheet_name, delimiter)

            return [TextContent(
                type="text",
                text=f"CSV exported successfully.\n"
                     f"path: {path}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_export_xlsx(
        doc_id: str,
        output_path: str
    ) -> list[TextContent]:
        """
        Export document to Excel XLSX format.

        Args:
            doc_id: Document ID
            output_path: Full path for output XLSX file

        Returns:
            Success status and path
        """
        try:
            wrapper = ExportWrapper(doc_id)
            path = wrapper.export_xlsx(output_path)

            return [TextContent(
                type="text",
                text=f"XLSX exported successfully.\n"
                     f"path: {path}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error exporting XLSX: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_export_xpwe(
        doc_id: str,
        output_path: str
    ) -> list[TextContent]:
        """
        Export document to XPWE format (Primus exchange format).

        Args:
            doc_id: Document ID
            output_path: Full path for output XPWE file

        Returns:
            Success status and path

        Note: XPWE export is not yet implemented via MCP.
        """
        try:
            wrapper = ExportWrapper(doc_id)
            path = wrapper.export_xpwe(output_path)

            return [TextContent(
                type="text",
                text=f"XPWE exported successfully.\n"
                     f"path: {path}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error exporting XPWE: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_export_formats() -> list[TextContent]:
        """
        Get list of supported export formats.

        Returns:
            List of available export formats
        """
        formats = [
            {"id": "pdf", "name": "PDF Document", "ext": ".pdf"},
            {"id": "csv", "name": "CSV File", "ext": ".csv"},
            {"id": "xlsx", "name": "Excel Spreadsheet", "ext": ".xlsx"},
            {"id": "ods", "name": "ODS Spreadsheet", "ext": ".ods"},
            {"id": "xpwe", "name": "XPWE (Primus)", "ext": ".xpwe", "note": "not yet implemented"},
        ]

        lines = ["Supported export formats:"]
        for f in formats:
            note = f" ({f['note']})" if 'note' in f else ""
            lines.append(f"  - {f['id']}: {f['name']} ({f['ext']}){note}")

        return [TextContent(type="text", text="\n".join(lines))]
