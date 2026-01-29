"""
Analisi Prezzi wrapper for LeenO price analysis operations.

Provides functionality to create and manage Analisi di Prezzo (price analysis)
for new prices not in Elenco Prezzi, using native LeenO macros.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from .base import LeenoWrapper, parse_currency
from ..connection import get_pool, get_macros
from ..utils.exceptions import OperationError, SheetNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class ComponenteAnalisi:
    """Component of a price analysis."""
    codice: str
    descrizione: str
    unita_misura: str
    quantita: float
    prezzo_unitario: float
    importo: float


@dataclass
class AnalisiPrezzo:
    """Price analysis data model."""
    codice: str
    descrizione: str
    unita_misura: str
    prezzo_totale: float
    componenti: List[ComponenteAnalisi]
    riga_inizio: int
    riga_fine: int


@dataclass
class AnalisiInput:
    """Input data for creating a new price analysis."""
    codice: str
    descrizione: str
    unita_misura: str
    componenti: Optional[List[Dict[str, Any]]] = None


class AnalisiWrapper(LeenoWrapper):
    """
    Wrapper for Analisi di Prezzo sheet operations.

    Uses native LeenO macros for:
    - inizializzaAnalisi: Create new analysis block
    - copia_riga_analisi: Add component rows
    - MENU_analisi_in_ElencoPrezzi: Transfer to Elenco Prezzi
    """

    def __init__(self, doc_id: str):
        """
        Initialize analisi wrapper.

        Args:
            doc_id: Document ID
        """
        pool = get_pool()
        doc_info = pool.ensure_leeno(doc_id)
        super().__init__(doc_info)

        self._sheet_name = self.SHEET_ANALISI
        self._sheet = None

    @property
    def sheet(self) -> Any:
        """Get the Analisi di Prezzo sheet, creating if needed."""
        if self._sheet is None:
            if self.has_sheet(self._sheet_name):
                self._sheet = self.get_sheet(self._sheet_name)
        return self._sheet

    def crea_analisi(self, input_data: AnalisiInput) -> AnalisiPrezzo:
        """
        Create a new Analisi di Prezzo using native LeenO macro.

        This is the correct way to create new prices when they don't exist
        in Elenco Prezzi. The analysis can then be transferred to EP.

        Args:
            input_data: AnalisiInput with analysis data

        Returns:
            Created AnalisiPrezzo

        Raises:
            OperationError: If operation fails
        """
        self.ensure_leeno()
        macros = get_macros()

        if not macros.is_initialized:
            raise OperationError("crea_analisi", "LeenO macros not initialized")

        with self.suspend_refresh():
            try:
                # Use native macro to initialize analysis and get start row
                oSheet, startRow = macros.inizializzaAnalisi(self._uno_doc)
                self._sheet = oSheet

                # Set analysis header data
                # Column B (1): Codice
                self.set_cell_value(oSheet, 1, startRow, input_data.codice)
                # Column C (2): Unità misura
                self.set_cell_value(oSheet, 2, startRow, input_data.unita_misura)
                # Column D (3): Descrizione
                self.set_cell_value(oSheet, 3, startRow, input_data.descrizione)

                # Add component rows if provided
                if input_data.componenti:
                    current_row = startRow + 1
                    for comp in input_data.componenti:
                        # Use native macro to add component row
                        try:
                            macros.copia_riga_analisi(current_row)
                        except Exception as e:
                            logger.warning(f"copia_riga_analisi failed: {e}")
                            self.insert_rows(oSheet, current_row, 1)

                        # Set component data
                        if 'codice' in comp:
                            self.set_cell_value(oSheet, 1, current_row, comp['codice'])
                        if 'descrizione' in comp:
                            self.set_cell_value(oSheet, 3, current_row, comp['descrizione'])
                        if 'unita_misura' in comp:
                            self.set_cell_value(oSheet, 2, current_row, comp['unita_misura'])
                        if 'quantita' in comp:
                            self.set_cell_value(oSheet, 5, current_row, comp['quantita'])
                        if 'prezzo_unitario' in comp:
                            self.set_cell_value(oSheet, 6, current_row, comp['prezzo_unitario'])

                        current_row += 1

                # Find end row
                end_row = self._find_analisi_end(oSheet, startRow)

                # Calculate total
                prezzo_totale = parse_currency(self.get_cell_value(oSheet, 7, end_row))

                return AnalisiPrezzo(
                    codice=input_data.codice,
                    descrizione=input_data.descrizione,
                    unita_misura=input_data.unita_misura,
                    prezzo_totale=prezzo_totale,
                    componenti=[],
                    riga_inizio=startRow,
                    riga_fine=end_row
                )

            except Exception as e:
                logger.error(f"Error creating analisi: {e}")
                raise OperationError("crea_analisi", str(e))

    def aggiungi_componente(self, riga: int, componente: Dict[str, Any]) -> bool:
        """
        Add a component row to an existing analysis.

        Args:
            riga: Row index where to add component
            componente: Component data dict

        Returns:
            True if successful
        """
        macros = get_macros()

        if not macros.is_initialized:
            raise OperationError("aggiungi_componente", "LeenO macros not initialized")

        oSheet = self.sheet
        if oSheet is None:
            raise SheetNotFoundError(self._sheet_name)

        with self.suspend_refresh():
            try:
                # Use native macro to add component row
                macros.copia_riga_analisi(riga)

                # Set component data
                if 'codice' in componente:
                    self.set_cell_value(oSheet, 1, riga, componente['codice'])
                if 'descrizione' in componente:
                    self.set_cell_value(oSheet, 3, riga, componente['descrizione'])
                if 'unita_misura' in componente:
                    self.set_cell_value(oSheet, 2, riga, componente['unita_misura'])
                if 'quantita' in componente:
                    self.set_cell_value(oSheet, 5, riga, componente['quantita'])
                if 'prezzo_unitario' in componente:
                    self.set_cell_value(oSheet, 6, riga, componente['prezzo_unitario'])

                return True

            except Exception as e:
                logger.error(f"Error adding componente: {e}")
                raise OperationError("aggiungi_componente", str(e))

    def trasferisci_a_elenco_prezzi(self) -> bool:
        """
        Transfer the current analysis to Elenco Prezzi.

        Uses native LeenO macro MENU_analisi_in_ElencoPrezzi.
        After this, the price can be used in COMPUTO.

        Returns:
            True if successful

        Raises:
            OperationError: If operation fails
        """
        macros = get_macros()

        if not macros.is_initialized:
            raise OperationError("trasferisci_a_elenco_prezzi", "LeenO macros not initialized")

        try:
            macros.MENU_analisi_in_ElencoPrezzi()
            logger.info("Analysis transferred to Elenco Prezzi")
            return True

        except Exception as e:
            logger.error(f"Error transferring to Elenco Prezzi: {e}")
            raise OperationError("trasferisci_a_elenco_prezzi", str(e))

    def _find_analisi_end(self, oSheet: Any, start_row: int) -> int:
        """Find the end row of an analysis block."""
        last_row = self.get_last_row(oSheet)

        for row in range(start_row, min(start_row + 100, last_row + 1)):
            style = self.get_cell_style(oSheet, 0, row)
            if style in ("An End Attributo", "An-sfondo-basso"):
                return row

        return start_row + 10  # Default

    def list_analisi(self) -> List[AnalisiPrezzo]:
        """
        List all analyses in the sheet.

        Returns:
            List of AnalisiPrezzo
        """
        analisi_list = []
        oSheet = self.sheet

        if oSheet is None:
            return analisi_list

        last_row = self.get_last_row(oSheet)

        row = 4
        while row <= last_row:
            style = self.get_cell_style(oSheet, 0, row)

            if style in ("An Start Attributo", "An-sfondo-alto"):
                codice = str(self.get_cell_value(oSheet, 1, row) or "")
                um = str(self.get_cell_value(oSheet, 2, row) or "")
                descrizione = str(self.get_cell_value(oSheet, 3, row) or "")

                end_row = self._find_analisi_end(oSheet, row)
                prezzo = parse_currency(self.get_cell_value(oSheet, 7, end_row))

                analisi_list.append(AnalisiPrezzo(
                    codice=codice,
                    descrizione=descrizione,
                    unita_misura=um,
                    prezzo_totale=prezzo,
                    componenti=[],
                    riga_inizio=row,
                    riga_fine=end_row
                ))

                row = end_row

            row += 1

        return analisi_list
