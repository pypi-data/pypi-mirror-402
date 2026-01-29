"""
MCP Tools for computo metrico operations.
"""

import logging
from typing import Optional

from mcp.server import FastMCP
from mcp.types import TextContent

from ..wrappers import ComputoWrapper
from ..models.voce import VoceComputoInput, MisuraInput
from ..models.capitolo import CapitoloInput
from ..utils.exceptions import LeenoMCPError

logger = logging.getLogger(__name__)


def register_computo_tools(server: FastMCP):
    """Register computo management tools with the MCP server."""

    @server.tool()
    async def leeno_computo_add_voce(
        doc_id: str,
        codice: str,
        descrizione: Optional[str] = None,
        unita_misura: Optional[str] = None,
        quantita: Optional[float] = None,
        prezzo_unitario: Optional[float] = None
    ) -> list[TextContent]:
        """
        Add a new voce (item) to the computo.

        Args:
            doc_id: Document ID
            codice: Article code (e.g., "01.A01.001")
            descrizione: Work description (optional)
            unita_misura: Unit of measurement (optional)
            quantita: Quantity (optional)
            prezzo_unitario: Unit price (optional)

        Returns:
            Created voce info
        """
        try:
            wrapper = ComputoWrapper(doc_id)
            input_data = VoceComputoInput(
                codice=codice,
                descrizione=descrizione,
                unita_misura=unita_misura,
                quantita=quantita,
                prezzo_unitario=prezzo_unitario
            )
            voce = wrapper.add_voce(input_data)

            lines = [
                "Voce added successfully.",
                f"voce_id: {voce.voce_id}",
                f"numero: {voce.numero}",
                f"codice: {voce.codice}",
                f"descrizione: {voce.descrizione[:60]}..." if len(voce.descrizione) > 60 else f"descrizione: {voce.descrizione}",
                f"unita_misura: {voce.unita_misura}",
                f"quantita: {voce.quantita}",
                f"prezzo_unitario: € {voce.prezzo_unitario:,.2f}",
                f"importo: € {voce.importo:,.2f}",
                f"riga: {voce.riga_inizio}"
            ]
            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error adding voce: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_computo_list_voci(
        doc_id: str,
        capitolo: Optional[str] = None
    ) -> list[TextContent]:
        """
        List all voci in the computo.

        Args:
            doc_id: Document ID
            capitolo: Filter by chapter (optional)

        Returns:
            List of voci with summary info
        """
        try:
            wrapper = ComputoWrapper(doc_id)
            voci = wrapper.list_voci(capitolo)

            if not voci:
                return [TextContent(type="text", text="No voci found in computo.")]

            lines = [f"Found {len(voci)} voci:"]
            for voce in voci:
                lines.append(
                    f"  {voce.numero}. [{voce.codice}] {voce.descrizione[:50]}... "
                    f"€ {voce.importo:,.2f}"
                )

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error listing voci: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_computo_get_voce(
        doc_id: str,
        voce_id: str
    ) -> list[TextContent]:
        """
        Get detailed info about a specific voce.

        Args:
            doc_id: Document ID
            voce_id: Voce ID (e.g., "V001")

        Returns:
            Detailed voce information
        """
        try:
            wrapper = ComputoWrapper(doc_id)
            voce = wrapper.get_voce(voce_id)

            lines = [
                f"Voce: {voce.voce_id}",
                f"Numero: {voce.numero}",
                f"Codice: {voce.codice}",
                f"Descrizione: {voce.descrizione}",
                f"Unità misura: {voce.unita_misura}",
                f"Quantità: {voce.quantita}",
                f"Prezzo unitario: € {voce.prezzo_unitario:,.2f}",
                f"Importo: € {voce.importo:,.2f}",
                f"Sicurezza: € {voce.sicurezza:,.2f}",
                f"Manodopera: € {voce.manodopera:,.2f}",
                f"Capitolo: {voce.capitolo or 'N/A'}",
                f"Righe: {voce.riga_inizio} - {voce.riga_fine}",
            ]

            if voce.misure:
                lines.append(f"Misure: {len(voce.misure)} righe")

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error getting voce: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_computo_delete_voce(
        doc_id: str,
        voce_id: str
    ) -> list[TextContent]:
        """
        Delete a voce from the computo.

        Args:
            doc_id: Document ID
            voce_id: Voce ID to delete

        Returns:
            Success status
        """
        try:
            wrapper = ComputoWrapper(doc_id)
            wrapper.delete_voce(voce_id)

            return [TextContent(
                type="text",
                text=f"Voce {voce_id} deleted successfully."
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error deleting voce: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_computo_add_capitolo(
        doc_id: str,
        nome: str,
        livello: int = 1
    ) -> list[TextContent]:
        """
        Add a new chapter to the computo.

        Args:
            doc_id: Document ID
            nome: Chapter name
            livello: Hierarchy level (0=Super, 1=Capitolo, 2=Sotto)

        Returns:
            Created chapter info
        """
        try:
            wrapper = ComputoWrapper(doc_id)
            input_data = CapitoloInput(nome=nome, livello=livello)
            capitolo = wrapper.add_capitolo(input_data)

            return [TextContent(
                type="text",
                text=f"Capitolo added successfully.\n"
                     f"capitolo_id: {capitolo.capitolo_id}\n"
                     f"nome: {capitolo.nome}\n"
                     f"livello: {capitolo.livello} ({capitolo.tipo})\n"
                     f"riga: {capitolo.riga}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error adding capitolo: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_computo_add_misura(
        doc_id: str,
        voce_id: str,
        descrizione: str = "",
        parti_uguali: float = 1,
        lunghezza: float = 0,
        larghezza: float = 0,
        altezza: float = 0,
        quantita: Optional[float] = None
    ) -> list[TextContent]:
        """
        Add a measurement row to a voce.

        Args:
            doc_id: Document ID
            voce_id: Voce ID
            descrizione: Measurement description
            parti_uguali: Number of equal parts
            lunghezza: Length
            larghezza: Width
            altezza: Height/Depth
            quantita: Forced quantity (optional)

        Returns:
            Success status
        """
        try:
            wrapper = ComputoWrapper(doc_id)
            misura = MisuraInput(
                descrizione=descrizione,
                parti_uguali=parti_uguali,
                lunghezza=lunghezza,
                larghezza=larghezza,
                altezza=altezza,
                quantita=quantita
            )
            wrapper.add_misura(voce_id, misura)

            return [TextContent(
                type="text",
                text=f"Misura added to voce {voce_id} successfully."
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error adding misura: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_computo_get_totale(doc_id: str) -> list[TextContent]:
        """
        Get computo totals.

        Args:
            doc_id: Document ID

        Returns:
            Totals (importo, sicurezza, manodopera)
        """
        try:
            wrapper = ComputoWrapper(doc_id)
            totals = wrapper.get_totale()

            return [TextContent(
                type="text",
                text=f"Computo Totals:\n"
                     f"  Importo lavori: € {totals['totale']:,.2f}\n"
                     f"  Oneri sicurezza: € {totals['sicurezza']:,.2f}\n"
                     f"  Incidenza MDO: € {totals['manodopera']:,.2f}\n"
                     f"  ---\n"
                     f"  TOTALE: € {totals['totale'] + totals['sicurezza']:,.2f}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error getting totale: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_computo_get_struttura(doc_id: str) -> list[TextContent]:
        """
        Get complete computo structure (chapters and totals).

        Args:
            doc_id: Document ID

        Returns:
            Computo structure with chapters
        """
        try:
            wrapper = ComputoWrapper(doc_id)
            struttura = wrapper.get_struttura()

            lines = [
                "Struttura Computo:",
                f"Totale voci: {struttura.num_voci_totali}",
                f"Totale importo: € {struttura.totale_importo:,.2f}",
                "",
                "Capitoli:"
            ]

            for cap in struttura.capitoli:
                indent = "  " * cap.livello
                lines.append(f"{indent}- {cap.nome}")

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error getting struttura: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
