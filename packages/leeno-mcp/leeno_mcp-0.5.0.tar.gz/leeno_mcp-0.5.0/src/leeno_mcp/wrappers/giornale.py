"""
Giornale Lavori wrapper for LeenO work diary operations.

Provides functionality to manage the construction site daily log (Giornale dei Lavori).
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, date

from .base import LeenoWrapper
from ..connection import get_pool, get_macros
from ..utils.exceptions import OperationError, SheetNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class GiornoLavori:
    """Entry in the work diary."""
    data: str
    riga: int
    note: str
    condizioni_meteo: Optional[str] = None
    operai: Optional[int] = None
    ore_lavorate: Optional[float] = None


@dataclass
class GiornaleInfo:
    """Information about the work diary."""
    exists: bool
    num_giorni: int
    data_inizio: Optional[str]
    data_fine: Optional[str]


class GiornaleWrapper(LeenoWrapper):
    """
    Wrapper for GIORNALE (work diary) operations.

    The Giornale dei Lavori is a daily log of construction activities.
    """

    SHEET_GIORNALE = "GIORNALE"
    SHEET_GIORNALE_BIANCO = "GIORNALE_BIANCO"

    def __init__(self, doc_id: str):
        """
        Initialize giornale wrapper.

        Args:
            doc_id: Document ID
        """
        pool = get_pool()
        doc_info = pool.ensure_leeno(doc_id)
        super().__init__(doc_info)

    def has_giornale(self) -> bool:
        """Check if GIORNALE sheet exists."""
        return self.has_sheet(self.SHEET_GIORNALE)

    def crea_giornale(self) -> GiornaleInfo:
        """
        Create a new Giornale dei Lavori.

        Uses LeenO native function to create from template.

        Returns:
            GiornaleInfo with diary details

        Raises:
            OperationError: If operation fails
        """
        macros = get_macros()

        try:
            if macros.is_initialized:
                try:
                    import LeenoGiornale
                    doc = LeenoGiornale.creaGiornale()
                    if doc:
                        logger.info("Giornale created from template")
                except ImportError as e:
                    logger.warning(f"LeenoGiornale not available: {e}")
                    raise OperationError("crea_giornale", "LeenoGiornale module not available")
            else:
                raise OperationError("crea_giornale", "LeenO macros not initialized")

            return self.get_giornale_info()

        except OperationError:
            raise
        except Exception as e:
            logger.error(f"Error creating giornale: {e}")
            raise OperationError("crea_giornale", str(e))

    def nuovo_giorno(self, data: Optional[str] = None) -> GiornoLavori:
        """
        Add a new day entry to the work diary.

        Args:
            data: Date string (optional, uses today if not provided)

        Returns:
            Created GiornoLavori entry

        Raises:
            OperationError: If operation fails
        """
        if not self.has_giornale():
            raise SheetNotFoundError(self.SHEET_GIORNALE)

        macros = get_macros()

        with self.suspend_refresh():
            try:
                if macros.is_initialized:
                    try:
                        import LeenoGiornale
                        LeenoGiornale.nuovo_giorno()
                        logger.info("New day added to giornale")
                    except ImportError as e:
                        logger.warning(f"LeenoGiornale not available: {e}")
                        return self._add_day_manual(data)
                else:
                    return self._add_day_manual(data)

                # Get info about the new entry
                oSheet = self.get_sheet(self.SHEET_GIORNALE)
                last_row = self.get_last_row(oSheet)

                return GiornoLavori(
                    data=data or datetime.now().strftime("%d/%m/%Y"),
                    riga=last_row - 5,
                    note=""
                )

            except Exception as e:
                logger.error(f"Error adding new day: {e}")
                raise OperationError("nuovo_giorno", str(e))

    def _add_day_manual(self, data: Optional[str] = None) -> GiornoLavori:
        """Add a new day entry manually."""
        oSheet = self.get_sheet(self.SHEET_GIORNALE)
        last_row = self.get_last_row(oSheet)

        # Insert new rows
        oSheet.getRows().insertByIndex(last_row + 1, 10)

        # Set date
        date_str = data or datetime.now().strftime("%d/%m/%Y")
        self.set_cell_value(oSheet, 0, last_row + 1, f"Data: {date_str}")

        return GiornoLavori(
            data=date_str,
            riga=last_row + 1,
            note=""
        )

    def get_giornale_info(self) -> GiornaleInfo:
        """
        Get information about the work diary.

        Returns:
            GiornaleInfo with current state
        """
        if not self.has_giornale():
            return GiornaleInfo(
                exists=False,
                num_giorni=0,
                data_inizio=None,
                data_fine=None
            )

        oSheet = self.get_sheet(self.SHEET_GIORNALE)
        last_row = self.get_last_row(oSheet)

        # Count days and find date range
        num_giorni = 0
        data_inizio = None
        data_fine = None

        for row in range(3, last_row):
            cell_value = str(self.get_cell_value(oSheet, 0, row) or "")
            if "Data:" in cell_value:
                num_giorni += 1
                date_str = cell_value.replace("Data:", "").strip()
                if data_inizio is None:
                    data_inizio = date_str
                data_fine = date_str

        return GiornaleInfo(
            exists=True,
            num_giorni=num_giorni,
            data_inizio=data_inizio,
            data_fine=data_fine
        )

    def list_giorni(self) -> List[GiornoLavori]:
        """
        List all day entries in the work diary.

        Returns:
            List of GiornoLavori entries
        """
        if not self.has_giornale():
            return []

        oSheet = self.get_sheet(self.SHEET_GIORNALE)
        last_row = self.get_last_row(oSheet)

        giorni = []
        for row in range(3, last_row):
            cell_value = str(self.get_cell_value(oSheet, 0, row) or "")
            if "Data:" in cell_value:
                date_str = cell_value.replace("Data:", "").strip()

                # Get notes from next rows
                note = ""
                for i in range(1, 10):
                    if row + i >= last_row:
                        break
                    next_val = str(self.get_cell_value(oSheet, 0, row + i) or "")
                    if "Data:" in next_val:
                        break
                    if next_val:
                        note += next_val + "\n"

                giorni.append(GiornoLavori(
                    data=date_str,
                    riga=row,
                    note=note.strip()
                ))

        return giorni

    def aggiungi_nota(self, riga: int, nota: str) -> bool:
        """
        Add a note to a day entry.

        Args:
            riga: Row index of the day entry
            nota: Note text to add

        Returns:
            True if successful
        """
        if not self.has_giornale():
            raise SheetNotFoundError(self.SHEET_GIORNALE)

        oSheet = self.get_sheet(self.SHEET_GIORNALE)

        with self.suspend_refresh():
            # Find the first empty row after the date
            for i in range(1, 10):
                cell_value = self.get_cell_value(oSheet, 0, riga + i)
                if not cell_value:
                    self.set_cell_value(oSheet, 0, riga + i, nota)
                    return True
                if "Data:" in str(cell_value):
                    # Insert new row before next date
                    oSheet.getRows().insertByIndex(riga + i, 1)
                    self.set_cell_value(oSheet, 0, riga + i, nota)
                    return True

        return False
