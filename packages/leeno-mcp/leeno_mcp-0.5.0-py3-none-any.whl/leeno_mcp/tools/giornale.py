"""
MCP Tools for Giornale dei Lavori (work diary) operations.

The Giornale is a daily log of construction site activities.
"""

import logging
from typing import Optional

from mcp.server import FastMCP
from mcp.types import TextContent

from ..wrappers.giornale import GiornaleWrapper
from ..utils.exceptions import LeenoMCPError

logger = logging.getLogger(__name__)


def register_giornale_tools(server: FastMCP):
    """Register giornale lavori tools with the MCP server."""

    @server.tool()
    async def leeno_giornale_create(doc_id: str) -> list[TextContent]:
        """
        Create a new Giornale dei Lavori (work diary).

        Opens a new document from the Giornale template.

        Args:
            doc_id: Document ID (for context, actual giornale is new doc)

        Returns:
            Creation status
        """
        try:
            wrapper = GiornaleWrapper(doc_id)
            info = wrapper.crea_giornale()

            return [TextContent(
                type="text",
                text="Giornale dei Lavori created successfully.\n"
                     f"Days: {info.num_giorni}\n"
                     "Use leeno_giornale_nuovo_giorno to add daily entries."
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error creating giornale: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_giornale_nuovo_giorno(
        doc_id: str,
        data: Optional[str] = None
    ) -> list[TextContent]:
        """
        Add a new day entry to the work diary.

        Args:
            doc_id: Document ID
            data: Date string (format: DD/MM/YYYY), uses today if not provided

        Returns:
            New day entry info
        """
        try:
            wrapper = GiornaleWrapper(doc_id)
            giorno = wrapper.nuovo_giorno(data)

            return [TextContent(
                type="text",
                text=f"New day added to Giornale.\n"
                     f"Date: {giorno.data}\n"
                     f"Row: {giorno.riga}\n"
                     "Use leeno_giornale_add_nota to add notes."
            )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error adding new day: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_giornale_info(doc_id: str) -> list[TextContent]:
        """
        Get information about the work diary.

        Args:
            doc_id: Document ID

        Returns:
            Giornale information
        """
        try:
            wrapper = GiornaleWrapper(doc_id)
            info = wrapper.get_giornale_info()

            if not info.exists:
                return [TextContent(
                    type="text",
                    text="No Giornale dei Lavori found in document.\n"
                         "Use leeno_giornale_create to create one."
                )]

            lines = [
                "Giornale dei Lavori:",
                f"  Total days: {info.num_giorni}",
            ]

            if info.data_inizio:
                lines.append(f"  First day: {info.data_inizio}")
            if info.data_fine:
                lines.append(f"  Last day: {info.data_fine}")

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error getting giornale info: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_giornale_list_giorni(doc_id: str) -> list[TextContent]:
        """
        List all day entries in the work diary.

        Args:
            doc_id: Document ID

        Returns:
            List of all days with notes
        """
        try:
            wrapper = GiornaleWrapper(doc_id)
            giorni = wrapper.list_giorni()

            if not giorni:
                return [TextContent(
                    type="text",
                    text="No day entries found in Giornale."
                )]

            lines = [f"Found {len(giorni)} day entries:"]
            for giorno in giorni:
                note_preview = giorno.note[:50] + "..." if len(giorno.note) > 50 else giorno.note
                lines.append(f"  [{giorno.data}] Row {giorno.riga}: {note_preview or '(no notes)'}")

            return [TextContent(type="text", text="\n".join(lines))]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error listing giorni: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.tool()
    async def leeno_giornale_add_nota(
        doc_id: str,
        riga: int,
        nota: str
    ) -> list[TextContent]:
        """
        Add a note to a day entry in the work diary.

        Args:
            doc_id: Document ID
            riga: Row index of the day entry
            nota: Note text to add

        Returns:
            Success status
        """
        try:
            wrapper = GiornaleWrapper(doc_id)
            success = wrapper.aggiungi_nota(riga, nota)

            if success:
                return [TextContent(
                    type="text",
                    text=f"Note added successfully to row {riga}."
                )]
            else:
                return [TextContent(
                    type="text",
                    text="Could not add note. Check the row index."
                )]

        except LeenoMCPError as e:
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except Exception as e:
            logger.error(f"Error adding nota: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
