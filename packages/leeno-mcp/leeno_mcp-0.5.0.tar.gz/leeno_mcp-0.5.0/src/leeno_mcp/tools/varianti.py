"""
MCP Tools for project variant (VARIANTE) operations.

A VARIANTE is a modified copy of the COMPUTO that tracks project changes.
"""

import logging

from mcp.server import FastMCP
from mcp.types import TextContent

from ..wrappers.varianti import VariantiWrapper
from ..utils.exceptions import LeenoMCPError

logger = logging.getLogger(__name__)


def register_varianti_tools(server: FastMCP):
    """Register varianti tools with the MCP server."""

    @server.tool()
    async def leeno_variante_create(
        doc_id: str,
        clear: bool = False
    ) -> list[TextContent]:
        """
        Create a project variant (VARIANTE) from COMPUTO.

        The VARIANTE sheet is a copy of COMPUTO where you can make changes
        to track project modifications without altering the original.

        Args:
            doc_id: Document ID
            clear: If True, create empty variant; if False, copy all from COMPUTO

        Returns:
            Variant info
        """
        try:
            wrapper = VariantiWrapper(doc_id)
            info = wrapper.crea_variante(clear)

            if info.exists:
                lines = [
                    "Variante created successfully." if not wrapper.has_variante() else "Variante already exists.",
                    f"Number of voci: {info.num_voci}",
                    f"Total amount: € {info.totale_importo:,.2f}",
                ]
                if info.differenza_computo != 0:
                    lines.append(f"Difference from COMPUTO: € {info.differenza_computo:,.2f}")

                return [TextContent(type="text", text="\n".join(lines))]
            else:
                return [TextContent(type="text", text="Failed to create variante.")]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error creating variante: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_variante_info(doc_id: str) -> list[TextContent]:
        """
        Get information about the project variant.

        Args:
            doc_id: Document ID

        Returns:
            Variant information including totals and comparison with COMPUTO
        """
        try:
            wrapper = VariantiWrapper(doc_id)
            info = wrapper.get_variante_info()

            if not info.exists:
                return [TextContent(
                    type="text",
                    text="No VARIANTE sheet found in document.\n"
                         "Use leeno_variante_create to create one."
                )]

            lines = [
                "Variante Information:",
                f"  Number of voci: {info.num_voci}",
                f"  Total amount: € {info.totale_importo:,.2f}",
                f"  Difference from COMPUTO: € {info.differenza_computo:,.2f}",
            ]

            if info.differenza_computo != 0:
                pct = (info.differenza_computo / (info.totale_importo - info.differenza_computo) * 100) if (info.totale_importo - info.differenza_computo) > 0 else 0
                lines.append(f"  Variation percentage: {pct:+.2f}%")

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error getting variante info: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_variante_compare(doc_id: str) -> list[TextContent]:
        """
        Compare VARIANTE with COMPUTO.

        Shows detailed comparison between the original computo and the variant.

        Args:
            doc_id: Document ID

        Returns:
            Comparison details
        """
        try:
            wrapper = VariantiWrapper(doc_id)
            comparison = wrapper.confronta_con_computo()

            lines = [
                "Comparison COMPUTO vs VARIANTE:",
                "",
                "COMPUTO:",
                f"  Voci: {comparison['computo']['num_voci']}",
                f"  Total: € {comparison['computo']['totale']:,.2f}",
                "",
                "VARIANTE:",
                f"  Voci: {comparison['variante']['num_voci']}",
                f"  Total: € {comparison['variante']['totale']:,.2f}",
                "",
                "DIFFERENCES:",
                f"  Voci: {comparison['differenza_voci']:+d}",
                f"  Amount: € {comparison['differenza_importo']:+,.2f}",
                f"  Percentage: {comparison['percentuale_variazione']:+.2f}%",
            ]

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error comparing variante: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_variante_delete(doc_id: str) -> list[TextContent]:
        """
        Delete the VARIANTE sheet.

        This operation cannot be undone.

        Args:
            doc_id: Document ID

        Returns:
            Success status
        """
        try:
            wrapper = VariantiWrapper(doc_id)
            deleted = wrapper.elimina_variante()

            if deleted:
                return [TextContent(type="text", text="Variante sheet deleted successfully.")]
            else:
                return [TextContent(type="text", text="No VARIANTE sheet to delete.")]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error deleting variante: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
