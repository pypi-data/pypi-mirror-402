"""
MCP Tools for importing price lists (prezzari) into LeenO documents.

Supports various regional XML formats used in Italy.
"""

import logging
from typing import Optional

from mcp.server import FastMCP
from mcp.types import TextContent

from ..wrappers.import_prezzi import ImportPrezziWrapper, IMPORT_FORMATS
from ..utils.exceptions import LeenoMCPError

logger = logging.getLogger(__name__)


def register_import_tools(server: FastMCP):
    """Register import prezzari tools with the MCP server."""

    @server.tool()
    async def leeno_prezzi_import(
        doc_id: str,
        file_path: str,
        formato: str = "auto"
    ) -> list[TextContent]:
        """
        Import a price list (prezzario) from file.

        Supports various Italian regional formats including:
        - SIX (standard XML)
        - Regione Toscana, Calabria, Campania
        - Regione Sardegna
        - Regione Liguria
        - Regione Veneto
        - Regione Basilicata
        - Regione Lombardia
        - XPWE (LeenO native format)

        Args:
            doc_id: Document ID
            file_path: Path to the price list file (XML)
            formato: Format type or "auto" for auto-detection

        Returns:
            Import result with count of imported items
        """
        try:
            wrapper = ImportPrezziWrapper(doc_id)
            result = wrapper.import_prezzi(file_path, formato)

            if result.success:
                lines = [
                    "Price list imported successfully.",
                    f"Format: {result.format_detected}",
                    f"Articles imported: {result.num_articoli}",
                    f"Chapters imported: {result.num_capitoli}",
                ]

                if result.warnings:
                    lines.append("")
                    lines.append("Warnings:")
                    for w in result.warnings[:5]:
                        lines.append(f"  - {w}")

                return [TextContent(type="text", text="\n".join(lines))]
            else:
                return [TextContent(
                    type="text",
                    text=f"Import failed: {'; '.join(result.errors)}"
                )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error importing prezzi: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_prezzi_detect_format(file_path: str) -> list[TextContent]:
        """
        Detect the format of a price list file.

        Analyzes the file content to determine which regional format it uses.

        Args:
            file_path: Path to the price list file

        Returns:
            Detected format information
        """
        try:
            # File-based detection, no document needed
            import os
            if not os.path.exists(file_path):
                return [TextContent(type="text", text=f"Error: File not found: {file_path}")]

            # Read file for detection
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(10000)
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read(10000)

            # Pattern matching
            patterns = {
                'xmlns="six.xsd"': "SIX (standard XML format)",
                'autore="Regione Toscana"': "Regione Toscana",
                'autore="Regione Calabria"': "Regione Calabria",
                'autore="Regione Campania"': "Regione Campania",
                'autore="Regione Sardegna"': "Regione Sardegna",
                'autore="Regione Liguria"': "Regione Liguria",
                'rks=': "Regione Veneto",
                '<pdf>Prezzario_Regione_Basilicata': "Regione Basilicata",
                '<autore>Regione Lombardia': "Regione Lombardia",
                '<autore>LOM': "Regione Lombardia",
            }

            detected = None
            for pattern, format_name in patterns.items():
                if pattern in content:
                    detected = format_name
                    break

            if '<XPWE' in content or '<xpwe' in content:
                detected = "XPWE (LeenO native format)"

            if detected:
                return [TextContent(
                    type="text",
                    text=f"Detected format: {detected}\n"
                         f"File: {file_path}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Could not detect format for: {file_path}\n"
                         f"Please specify format manually when importing."
                )]

        except Exception as e:
            logger.error(f"Error detecting format: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_prezzi_list_formats() -> list[TextContent]:
        """
        List all supported price list import formats.

        Returns:
            List of supported formats with descriptions
        """
        lines = ["Supported price list formats:", ""]

        for code, description in IMPORT_FORMATS.items():
            lines.append(f"  {code}: {description}")

        lines.append("")
        lines.append("Use 'auto' to automatically detect the format from file content.")

        return [TextContent(type="text", text="\n".join(lines))]

    @server.tool()
    async def leeno_prezzi_import_url(
        doc_id: str,
        url: str,
        formato: str = "auto"
    ) -> list[TextContent]:
        """
        Import a price list from URL.

        Downloads the file and imports it into the document.

        Args:
            doc_id: Document ID
            url: URL to the price list file
            formato: Format type or "auto"

        Returns:
            Import result
        """
        try:
            wrapper = ImportPrezziWrapper(doc_id)
            result = wrapper.import_from_url(url, formato)

            if result.success:
                return [TextContent(
                    type="text",
                    text=f"Price list imported from URL successfully.\n"
                         f"Format: {result.format_detected}\n"
                         f"Articles: {result.num_articoli}\n"
                         f"Chapters: {result.num_capitoli}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Import failed: {'; '.join(result.errors)}"
                )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error importing from URL: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
