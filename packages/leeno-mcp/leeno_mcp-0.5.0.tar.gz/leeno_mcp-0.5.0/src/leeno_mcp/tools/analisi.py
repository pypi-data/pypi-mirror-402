"""
MCP Tools for Analisi di Prezzo (price analysis) operations.

These tools allow creating new prices when they don't exist in Elenco Prezzi,
following the LeenO workflow: create analysis -> add components -> transfer to EP.
"""

import logging
from typing import Optional, List

from mcp.server import FastMCP
from mcp.types import TextContent

from ..wrappers.analisi import AnalisiWrapper, AnalisiInput
from ..utils.exceptions import LeenoMCPError

logger = logging.getLogger(__name__)


def register_analisi_tools(server: FastMCP):
    """Register analisi di prezzo tools with the MCP server."""

    @server.tool()
    async def leeno_analisi_create(
        doc_id: str,
        codice: str,
        descrizione: str,
        unita_misura: str
    ) -> list[TextContent]:
        """
        Create a new Analisi di Prezzo (price analysis).

        Use this when a price code doesn't exist in Elenco Prezzi.
        After creating the analysis and adding components, transfer it to EP.

        Args:
            doc_id: Document ID
            codice: New price code (e.g., "NP.001")
            descrizione: Price description
            unita_misura: Unit of measurement (e.g., "mq", "m", "cad")

        Returns:
            Created analysis info with row position
        """
        try:
            wrapper = AnalisiWrapper(doc_id)
            input_data = AnalisiInput(
                codice=codice,
                descrizione=descrizione,
                unita_misura=unita_misura
            )
            analisi = wrapper.crea_analisi(input_data)

            lines = [
                "Analisi di Prezzo created successfully.",
                f"codice: {analisi.codice}",
                f"descrizione: {analisi.descrizione}",
                f"unita_misura: {analisi.unita_misura}",
                f"riga_inizio: {analisi.riga_inizio}",
                f"riga_fine: {analisi.riga_fine}",
                "",
                "Next steps:",
                "1. Use leeno_analisi_add_componente to add components",
                "2. Use leeno_analisi_transfer to move to Elenco Prezzi"
            ]
            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error creating analisi: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_analisi_add_componente(
        doc_id: str,
        riga: int,
        codice: Optional[str] = None,
        descrizione: Optional[str] = None,
        unita_misura: Optional[str] = None,
        quantita: Optional[float] = None,
        prezzo_unitario: Optional[float] = None
    ) -> list[TextContent]:
        """
        Add a component row to an existing Analisi di Prezzo.

        Components are the elements that make up the analyzed price
        (materials, labor, equipment, etc.).

        Args:
            doc_id: Document ID
            riga: Row index where to add component (inside the analysis block)
            codice: Component code (optional)
            descrizione: Component description (optional)
            unita_misura: Unit of measurement (optional)
            quantita: Quantity (optional)
            prezzo_unitario: Unit price (optional)

        Returns:
            Success status
        """
        try:
            wrapper = AnalisiWrapper(doc_id)

            componente = {}
            if codice:
                componente['codice'] = codice
            if descrizione:
                componente['descrizione'] = descrizione
            if unita_misura:
                componente['unita_misura'] = unita_misura
            if quantita is not None:
                componente['quantita'] = quantita
            if prezzo_unitario is not None:
                componente['prezzo_unitario'] = prezzo_unitario

            wrapper.aggiungi_componente(riga, componente)

            return [TextContent(
                type="text",
                text=f"Component added successfully at row {riga}."
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error adding component: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_analisi_transfer(doc_id: str) -> list[TextContent]:
        """
        Transfer current Analisi di Prezzo to Elenco Prezzi.

        After this operation, the analyzed price becomes available
        for use in COMPUTO.

        Args:
            doc_id: Document ID

        Returns:
            Success status
        """
        try:
            wrapper = AnalisiWrapper(doc_id)
            wrapper.trasferisci_a_elenco_prezzi()

            return [TextContent(
                type="text",
                text="Analysis transferred to Elenco Prezzi successfully.\n"
                     "The new price is now available for use in COMPUTO."
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error transferring analysis: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_analisi_list(doc_id: str) -> list[TextContent]:
        """
        List all Analisi di Prezzo in the document.

        Args:
            doc_id: Document ID

        Returns:
            List of all price analyses
        """
        try:
            wrapper = AnalisiWrapper(doc_id)
            analisi_list = wrapper.list_analisi()

            if not analisi_list:
                return [TextContent(
                    type="text",
                    text="No Analisi di Prezzo found in document."
                )]

            lines = [f"Found {len(analisi_list)} Analisi di Prezzo:"]
            for analisi in analisi_list:
                desc = analisi.descrizione[:50] + "..." if len(analisi.descrizione) > 50 else analisi.descrizione
                lines.append(
                    f"  [{analisi.codice}] {desc} "
                    f"({analisi.unita_misura}) - € {analisi.prezzo_totale:,.2f}"
                )

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error listing analisi: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_analisi_create_complete(
        doc_id: str,
        codice: str,
        descrizione: str,
        unita_misura: str,
        componenti: List[dict],
        transfer_to_ep: bool = True
    ) -> list[TextContent]:
        """
        Create a complete Analisi di Prezzo with components in one step.

        This is a convenience tool that combines create + add components + transfer.

        Args:
            doc_id: Document ID
            codice: New price code (e.g., "NP.001")
            descrizione: Price description
            unita_misura: Unit of measurement
            componenti: List of component dicts with keys:
                       codice, descrizione, unita_misura, quantita, prezzo_unitario
            transfer_to_ep: Whether to transfer to Elenco Prezzi (default: True)

        Returns:
            Created analysis info
        """
        try:
            wrapper = AnalisiWrapper(doc_id)
            input_data = AnalisiInput(
                codice=codice,
                descrizione=descrizione,
                unita_misura=unita_misura,
                componenti=componenti
            )
            analisi = wrapper.crea_analisi(input_data)

            lines = [
                "Analisi di Prezzo created successfully.",
                f"codice: {analisi.codice}",
                f"descrizione: {analisi.descrizione}",
                f"unita_misura: {analisi.unita_misura}",
                f"prezzo_totale: € {analisi.prezzo_totale:,.2f}",
                f"componenti: {len(componenti)}",
            ]

            if transfer_to_ep:
                wrapper.trasferisci_a_elenco_prezzi()
                lines.append("")
                lines.append("Transferred to Elenco Prezzi. Price is now available in COMPUTO.")

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error creating complete analisi: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
