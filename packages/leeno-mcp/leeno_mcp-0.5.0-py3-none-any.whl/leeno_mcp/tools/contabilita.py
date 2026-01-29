"""
MCP Tools for contabilità (work accounting) operations.
"""

import logging
from typing import Optional
from datetime import date

from mcp.server import FastMCP
from mcp.types import TextContent

from ..wrappers import ContabilitaWrapper
from ..models.contabilita import VoceContabilitaInput
from ..utils.exceptions import LeenoMCPError

logger = logging.getLogger(__name__)


def register_contabilita_tools(server: FastMCP):
    """Register contabilità management tools with the MCP server."""

    @server.tool()
    async def leeno_contab_add_voce(
        doc_id: str,
        codice: str,
        data: str,
        quantita: float,
        descrizione: Optional[str] = None
    ) -> list[TextContent]:
        """
        Add a new entry to contabilità.

        Args:
            doc_id: Document ID
            codice: Article code from Elenco Prezzi
            data: Date in YYYY-MM-DD format
            quantita: Quantity (positive for work done, negative for deductions)
            descrizione: Optional description override

        Returns:
            Created entry info
        """
        try:
            wrapper = ContabilitaWrapper(doc_id)

            # Parse date
            try:
                entry_date = date.fromisoformat(data)
            except ValueError:
                return [TextContent(type="text", text="Error: Invalid date format. Use YYYY-MM-DD.")]

            input_data = VoceContabilitaInput(
                codice=codice,
                data=entry_date,
                quantita=quantita,
                descrizione=descrizione
            )
            voce = wrapper.add_voce(input_data)

            return [TextContent(
                type="text",
                text=f"Contabilità entry added successfully.\n"
                     f"voce_id: {voce.voce_id}\n"
                     f"codice: {voce.codice}\n"
                     f"data: {voce.data}\n"
                     f"quantità: {voce.quantita_positiva - voce.quantita_negativa}\n"
                     f"importo: € {voce.importo:,.2f}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error adding contabilità voce: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_contab_list_voci(
        doc_id: str,
        sal: Optional[int] = None
    ) -> list[TextContent]:
        """
        List all entries in contabilità.

        Args:
            doc_id: Document ID
            sal: Filter by SAL number (optional)

        Returns:
            List of contabilità entries
        """
        try:
            wrapper = ContabilitaWrapper(doc_id)
            voci = wrapper.list_voci(sal)

            if not voci:
                msg = "No entries found in contabilità"
                if sal:
                    msg += f" for SAL {sal}"
                return [TextContent(type="text", text=msg + ".")]

            lines = [f"Found {len(voci)} entries:"]
            for v in voci:
                status = "[REG]" if v.registrato else ""
                quant = v.quantita_positiva - v.quantita_negativa
                lines.append(
                    f"  {v.numero}. {v.data} [{v.codice}] q:{quant:.2f} "
                    f"€ {v.importo:,.2f} {status}"
                )

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error listing contabilità voci: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_contab_get_sal(
        doc_id: str,
        numero: Optional[int] = None
    ) -> list[TextContent]:
        """
        Get SAL (Stato Avanzamento Lavori) information.

        Args:
            doc_id: Document ID
            numero: SAL number (None for latest)

        Returns:
            SAL information
        """
        try:
            wrapper = ContabilitaWrapper(doc_id)
            sal = wrapper.get_sal_info(numero)

            if not sal.registrato and sal.numero > 0:
                return [TextContent(type="text", text=f"SAL {sal.numero} not found or not registered.")]

            lines = [
                f"SAL {sal.numero}:",
                f"  Registrato: {'Sì' if sal.registrato else 'No'}",
                f"  Data emissione: {sal.data_emissione or 'N/A'}",
                f"  Importo lavori: € {sal.importo_lavori:,.2f}",
                f"  Oneri sicurezza: € {sal.importo_sicurezza:,.2f}",
                f"  Numero voci: {sal.num_voci}",
            ]

            if sal.importo_lavori_cumulativo:
                lines.append(f"  Cumulativo: € {sal.importo_lavori_cumulativo:,.2f}")

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error getting SAL info: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_contab_get_stato(doc_id: str) -> list[TextContent]:
        """
        Get overall contabilità status.

        Args:
            doc_id: Document ID

        Returns:
            Complete contabilità status
        """
        try:
            wrapper = ContabilitaWrapper(doc_id)
            stato = wrapper.get_stato()

            lines = [
                "Stato Contabilità:",
                f"  Totale lavori: € {stato.totale_lavori:,.2f}",
                f"  Oneri sicurezza: € {stato.totale_sicurezza:,.2f}",
                f"  Incidenza MDO: € {stato.totale_manodopera:,.2f}",
                "",
                f"  SAL emessi: {stato.num_sal_emessi}",
                f"  Importo registrato: € {stato.importo_registrato:,.2f}",
                f"  Da registrare: € {stato.importo_da_registrare:,.2f}",
                "",
                f"  Voci totali: {stato.num_voci_totali}",
                f"  Voci registrate: {stato.num_voci_registrate}",
            ]

            if stato.sal_list:
                lines.append("")
                lines.append("SAL emessi:")
                for sal in stato.sal_list:
                    lines.append(f"  SAL {sal.numero}: € {sal.importo_lavori:,.2f}")

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error getting contabilità stato: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_contab_emetti_sal(doc_id: str) -> list[TextContent]:
        """
        Emit a new SAL (Stato Avanzamento Lavori).

        Args:
            doc_id: Document ID

        Returns:
            New SAL information

        Note: This operation is complex and may require manual verification.
        """
        try:
            wrapper = ContabilitaWrapper(doc_id)
            sal = wrapper.emetti_sal()

            return [TextContent(
                type="text",
                text=f"SAL {sal.numero} emesso con successo.\n"
                     f"Importo: € {sal.importo_lavori:,.2f}\n"
                     f"Voci: {sal.num_voci}"
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error emitting SAL: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_contab_annulla_sal(doc_id: str, numero: int) -> list[TextContent]:
        """
        Cancel a SAL.

        Args:
            doc_id: Document ID
            numero: SAL number to cancel

        Returns:
            Success status

        Note: This operation is complex and may require manual verification.
        """
        try:
            wrapper = ContabilitaWrapper(doc_id)
            wrapper.annulla_sal(numero)

            return [TextContent(
                type="text",
                text=f"SAL {numero} annullato con successo."
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error canceling SAL: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
