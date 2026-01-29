"""
MCP Tools for elenco prezzi (price list) operations.
"""

import logging
from typing import Optional

from mcp.server import FastMCP
from mcp.types import TextContent

from ..wrappers import ElencoPrezziWrapper
from ..models.prezzo import PrezzoInput
from ..utils.exceptions import LeenoMCPError

logger = logging.getLogger(__name__)


def register_elenco_prezzi_tools(server: FastMCP):
    """Register price list management tools with the MCP server."""

    @server.tool()
    async def leeno_prezzi_search(
        doc_id: str,
        query: str,
        campo: str = "descrizione",
        limit: int = 20
    ) -> list[TextContent]:
        """
        Search prices in the elenco prezzi.

        Args:
            doc_id: Document ID
            query: Search query
            campo: Field to search ("codice", "descrizione", or "all")
            limit: Maximum results (default 20)

        Returns:
            List of matching prices
        """
        try:
            wrapper = ElencoPrezziWrapper(doc_id)
            results = wrapper.search(query, campo, limit)

            if not results:
                return [TextContent(type="text", text=f"No prices found matching '{query}'.")]

            lines = [f"Found {len(results)} prices:"]
            for p in results:
                lines.append(
                    f"  [{p.codice}] {p.descrizione[:40]}... "
                    f"{p.unita_misura} € {p.prezzo_unitario:,.2f}"
                )

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error searching prezzi: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_prezzi_get(doc_id: str, codice: str) -> list[TextContent]:
        """
        Get detailed info about a specific price.

        Args:
            doc_id: Document ID
            codice: Price code

        Returns:
            Detailed price information
        """
        try:
            wrapper = ElencoPrezziWrapper(doc_id)
            prezzo = wrapper.get_prezzo(codice)

            lines = [
                f"Prezzo: {prezzo.codice}",
                f"Descrizione: {prezzo.descrizione}",
                f"Descrizione estesa: {prezzo.descrizione_estesa[:100]}..." if prezzo.descrizione_estesa else "",
                f"Unità misura: {prezzo.unita_misura}",
                f"Prezzo unitario: € {prezzo.prezzo_unitario:,.2f}",
                f"Sicurezza: {prezzo.sicurezza:.1f}%",
                f"Manodopera: {prezzo.manodopera:.1f}%",
                f"Categoria: {prezzo.categoria or 'N/A'}",
                f"Riga: {prezzo.riga}",
            ]

            return [TextContent(type="text", text="\n".join(filter(None, lines)))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error getting prezzo: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_prezzi_add(
        doc_id: str,
        codice: str,
        descrizione: str,
        unita_misura: str,
        prezzo_unitario: float,
        descrizione_estesa: str = "",
        sicurezza: float = 0,
        manodopera: float = 0
    ) -> list[TextContent]:
        """
        Add a new price to the elenco prezzi.

        Args:
            doc_id: Document ID
            codice: Unique price code
            descrizione: Short description
            unita_misura: Unit of measurement
            prezzo_unitario: Unit price
            descrizione_estesa: Extended description (optional)
            sicurezza: Safety percentage 0-100 (optional)
            manodopera: Labor percentage 0-100 (optional)

        Returns:
            Created price info
        """
        try:
            wrapper = ElencoPrezziWrapper(doc_id)
            input_data = PrezzoInput(
                codice=codice,
                descrizione=descrizione,
                descrizione_estesa=descrizione_estesa,
                unita_misura=unita_misura,
                prezzo_unitario=prezzo_unitario,
                sicurezza=sicurezza,
                manodopera=manodopera
            )
            prezzo = wrapper.add_prezzo(input_data)

            return [TextContent(
                type="text",
                text=f"Prezzo added successfully.\n"
                     f"codice: {prezzo.codice}\n"
                     f"prezzo: € {prezzo.prezzo_unitario:,.2f}\n"
                     f"riga: {prezzo.riga}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error adding prezzo: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_prezzi_edit(
        doc_id: str,
        codice: str,
        descrizione: Optional[str] = None,
        prezzo_unitario: Optional[float] = None,
        sicurezza: Optional[float] = None,
        manodopera: Optional[float] = None
    ) -> list[TextContent]:
        """
        Edit an existing price.

        Args:
            doc_id: Document ID
            codice: Price code to edit
            descrizione: New description (optional)
            prezzo_unitario: New unit price (optional)
            sicurezza: New safety % (optional)
            manodopera: New labor % (optional)

        Returns:
            Updated price info
        """
        try:
            wrapper = ElencoPrezziWrapper(doc_id)

            updates = {}
            if descrizione is not None:
                updates["descrizione"] = descrizione
            if prezzo_unitario is not None:
                updates["prezzo_unitario"] = prezzo_unitario
            if sicurezza is not None:
                updates["sicurezza"] = sicurezza
            if manodopera is not None:
                updates["manodopera"] = manodopera

            if not updates:
                return [TextContent(type="text", text="No updates specified.")]

            prezzo = wrapper.edit_prezzo(codice, updates)

            return [TextContent(
                type="text",
                text=f"Prezzo {codice} updated successfully.\n"
                     f"New values:\n"
                     f"  descrizione: {prezzo.descrizione}\n"
                     f"  prezzo: € {prezzo.prezzo_unitario:,.2f}\n"
                     f"  sicurezza: {prezzo.sicurezza:.1f}%\n"
                     f"  manodopera: {prezzo.manodopera:.1f}%"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error editing prezzo: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_prezzi_delete(doc_id: str, codice: str) -> list[TextContent]:
        """
        Delete a price from the elenco prezzi.

        Args:
            doc_id: Document ID
            codice: Price code to delete

        Returns:
            Success status
        """
        try:
            wrapper = ElencoPrezziWrapper(doc_id)
            wrapper.delete_prezzo(codice)

            return [TextContent(
                type="text",
                text=f"Prezzo {codice} deleted successfully."
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error deleting prezzo: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_prezzi_list(
        doc_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> list[TextContent]:
        """
        List prices with pagination.

        Args:
            doc_id: Document ID
            limit: Maximum results (default 50)
            offset: Number to skip (default 0)

        Returns:
            List of prices
        """
        try:
            wrapper = ElencoPrezziWrapper(doc_id)
            prezzi = wrapper.list_prezzi(limit, offset)
            total = wrapper.count()

            if not prezzi:
                return [TextContent(type="text", text="No prices in elenco prezzi.")]

            lines = [f"Prices {offset + 1}-{offset + len(prezzi)} of {total}:"]
            for p in prezzi:
                lines.append(
                    f"  [{p.codice}] {p.descrizione[:35]}... "
                    f"{p.unita_misura} € {p.prezzo_unitario:,.2f}"
                )

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error listing prezzi: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_prezzi_count(doc_id: str) -> list[TextContent]:
        """
        Count total prices in elenco prezzi.

        Args:
            doc_id: Document ID

        Returns:
            Total count
        """
        try:
            wrapper = ElencoPrezziWrapper(doc_id)
            count = wrapper.count()

            return [TextContent(
                type="text",
                text=f"Total prices in elenco: {count}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error counting prezzi: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
