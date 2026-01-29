"""
Elenco Prezzi wrapper for price list operations.
"""

import logging
from typing import Optional, List, Any

from .base import LeenoWrapper, parse_currency, parse_percentage
from ..connection import get_pool
from ..models.prezzo import Prezzo, PrezzoInput, PrezzoSearchResult
from ..utils.exceptions import PrezzoNotFoundError, OperationError

logger = logging.getLogger(__name__)


class ElencoPrezziWrapper(LeenoWrapper):
    """
    Wrapper for Elenco Prezzi sheet operations.

    Handles price list management: search, add, edit, delete.
    """

    # Column indices in Elenco Prezzi sheet
    COL_CODICE = 0
    COL_DESCRIZIONE = 1
    COL_DESCRIZIONE_ESTESA = 2
    COL_UM = 3
    COL_SICUREZZA = 4
    COL_MANODOPERA = 5
    COL_PREZZO = 6

    def __init__(self, doc_id: str):
        """
        Initialize elenco prezzi wrapper.

        Args:
            doc_id: Document ID
        """
        pool = get_pool()
        doc_info = pool.ensure_leeno(doc_id)
        super().__init__(doc_info)

        self._sheet = self.get_sheet(self.SHEET_ELENCO_PREZZI)

    @property
    def sheet(self) -> Any:
        """Get the elenco prezzi sheet."""
        return self._sheet

    def get_prezzo(self, codice: str) -> Prezzo:
        """
        Get a price by code.

        Args:
            codice: Price code

        Returns:
            Prezzo model

        Raises:
            PrezzoNotFoundError: If price not found
        """
        row = self._find_row_by_codice(codice)
        if row is None:
            raise PrezzoNotFoundError(codice)

        return self._parse_prezzo_at_row(row)

    def search(
        self,
        query: str,
        campo: str = "descrizione",
        limit: int = 50
    ) -> List[PrezzoSearchResult]:
        """
        Search prices by query.

        Args:
            query: Search query
            campo: Field to search in ("codice", "descrizione", "all")
            limit: Maximum results

        Returns:
            List of PrezzoSearchResult
        """
        results = []
        query_lower = query.lower()
        last_row = self.get_last_row(self._sheet)

        for row in range(4, last_row + 1):
            style = self.get_cell_style(self._sheet, self.COL_CODICE, row)
            if style not in self.EP_CODE_STYLES:
                continue

            codice = str(self.get_cell_value(self._sheet, self.COL_CODICE, row) or "")
            descrizione = str(self.get_cell_value(self._sheet, self.COL_DESCRIZIONE, row) or "")

            match = False
            if campo == "codice":
                match = query_lower in codice.lower()
            elif campo == "descrizione":
                match = query_lower in descrizione.lower()
            else:  # all
                match = query_lower in codice.lower() or query_lower in descrizione.lower()

            if match:
                um = str(self.get_cell_value(self._sheet, self.COL_UM, row) or "")
                prezzo = parse_currency(self.get_cell_value(self._sheet, self.COL_PREZZO, row))

                results.append(PrezzoSearchResult(
                    codice=codice,
                    descrizione=descrizione,
                    unita_misura=um,
                    prezzo_unitario=prezzo,
                    riga=row
                ))

                if len(results) >= limit:
                    break

        return results

    def list_prezzi(self, limit: int = 100, offset: int = 0) -> List[Prezzo]:
        """
        List prices with pagination.

        Args:
            limit: Maximum results
            offset: Number of results to skip

        Returns:
            List of Prezzo
        """
        prezzi = []
        last_row = self.get_last_row(self._sheet)
        count = 0
        skipped = 0

        for row in range(4, last_row + 1):
            style = self.get_cell_style(self._sheet, self.COL_CODICE, row)
            if style not in self.EP_CODE_STYLES:
                continue

            if skipped < offset:
                skipped += 1
                continue

            prezzi.append(self._parse_prezzo_at_row(row))
            count += 1

            if count >= limit:
                break

        return prezzi

    def add_prezzo(self, input_data: PrezzoInput) -> Prezzo:
        """
        Add a new price to the list.

        Args:
            input_data: PrezzoInput with price data

        Returns:
            Created Prezzo

        Raises:
            OperationError: If code already exists
        """
        self.ensure_leeno()

        # Check if code already exists
        existing_row = self._find_row_by_codice(input_data.codice)
        if existing_row is not None:
            raise OperationError("add_prezzo", f"Price code '{input_data.codice}' already exists")

        with self.suspend_refresh():
            try:
                # Find insertion point
                insert_row = self._find_insertion_point()

                # Insert row
                self.insert_rows(self._sheet, insert_row, 1)

                # Set data
                self.set_cell_value(self._sheet, self.COL_CODICE, insert_row, input_data.codice)
                self.set_cell_value(self._sheet, self.COL_DESCRIZIONE, insert_row, input_data.descrizione)
                self.set_cell_value(self._sheet, self.COL_DESCRIZIONE_ESTESA, insert_row, input_data.descrizione_estesa or "")
                self.set_cell_value(self._sheet, self.COL_UM, insert_row, input_data.unita_misura)
                self.set_cell_value(self._sheet, self.COL_SICUREZZA, insert_row, input_data.sicurezza / 100)
                self.set_cell_value(self._sheet, self.COL_MANODOPERA, insert_row, input_data.manodopera / 100)
                self.set_cell_value(self._sheet, self.COL_PREZZO, insert_row, input_data.prezzo_unitario)

                # Set cell style
                self.get_cell(self._sheet, self.COL_CODICE, insert_row).CellStyle = self.STYLE_EP_CODE

                return self._parse_prezzo_at_row(insert_row)

            except Exception as e:
                logger.error(f"Error adding prezzo: {e}")
                raise OperationError("add_prezzo", str(e))

    def edit_prezzo(self, codice: str, updates: dict) -> Prezzo:
        """
        Edit an existing price.

        Args:
            codice: Price code to edit
            updates: Dict of fields to update

        Returns:
            Updated Prezzo

        Raises:
            PrezzoNotFoundError: If price not found
        """
        row = self._find_row_by_codice(codice)
        if row is None:
            raise PrezzoNotFoundError(codice)

        with self.suspend_refresh():
            try:
                if "descrizione" in updates:
                    self.set_cell_value(self._sheet, self.COL_DESCRIZIONE, row, updates["descrizione"])

                if "descrizione_estesa" in updates:
                    self.set_cell_value(self._sheet, self.COL_DESCRIZIONE_ESTESA, row, updates["descrizione_estesa"])

                if "unita_misura" in updates:
                    self.set_cell_value(self._sheet, self.COL_UM, row, updates["unita_misura"])

                if "prezzo_unitario" in updates:
                    self.set_cell_value(self._sheet, self.COL_PREZZO, row, updates["prezzo_unitario"])

                if "sicurezza" in updates:
                    self.set_cell_value(self._sheet, self.COL_SICUREZZA, row, updates["sicurezza"] / 100)

                if "manodopera" in updates:
                    self.set_cell_value(self._sheet, self.COL_MANODOPERA, row, updates["manodopera"] / 100)

                return self._parse_prezzo_at_row(row)

            except Exception as e:
                logger.error(f"Error editing prezzo: {e}")
                raise OperationError("edit_prezzo", str(e))

    def delete_prezzo(self, codice: str) -> bool:
        """
        Delete a price.

        Args:
            codice: Price code to delete

        Returns:
            True if deleted

        Raises:
            PrezzoNotFoundError: If price not found
        """
        row = self._find_row_by_codice(codice)
        if row is None:
            raise PrezzoNotFoundError(codice)

        with self.suspend_refresh():
            try:
                self.delete_rows(self._sheet, row, 1)
                return True

            except Exception as e:
                logger.error(f"Error deleting prezzo: {e}")
                raise OperationError("delete_prezzo", str(e))

    def count(self) -> int:
        """Count total prices."""
        count = 0
        last_row = self.get_last_row(self._sheet)

        for row in range(4, last_row + 1):
            style = self.get_cell_style(self._sheet, self.COL_CODICE, row)
            if style in self.EP_CODE_STYLES:
                count += 1

        return count

    # ==================== HELPER METHODS ====================

    def _find_row_by_codice(self, codice: str) -> Optional[int]:
        """Find row index for a price code."""
        last_row = self.get_last_row(self._sheet)

        for row in range(4, last_row + 1):
            style = self.get_cell_style(self._sheet, self.COL_CODICE, row)
            if style not in self.EP_CODE_STYLES:
                continue

            cell_value = self.get_cell_value(self._sheet, self.COL_CODICE, row)
            if str(cell_value) == codice:
                return row

        return None

    def _parse_prezzo_at_row(self, row: int) -> Prezzo:
        """Parse price data at given row."""
        codice = str(self.get_cell_value(self._sheet, self.COL_CODICE, row) or "")
        descrizione = str(self.get_cell_value(self._sheet, self.COL_DESCRIZIONE, row) or "")
        descrizione_estesa = str(self.get_cell_value(self._sheet, self.COL_DESCRIZIONE_ESTESA, row) or "")
        um = str(self.get_cell_value(self._sheet, self.COL_UM, row) or "")
        prezzo = parse_currency(self.get_cell_value(self._sheet, self.COL_PREZZO, row))

        # Sicurezza and manodopera - use parse_percentage to handle various formats
        sicurezza = parse_percentage(self.get_cell_value(self._sheet, self.COL_SICUREZZA, row))
        manodopera = parse_percentage(self.get_cell_value(self._sheet, self.COL_MANODOPERA, row))

        return Prezzo(
            codice=codice,
            descrizione=descrizione,
            descrizione_estesa=descrizione_estesa,
            unita_misura=um,
            prezzo_unitario=prezzo,
            sicurezza=sicurezza,
            manodopera=manodopera,
            riga=row
        )

    def _find_insertion_point(self) -> int:
        """Find row for new price insertion."""
        last_row = self.get_last_row(self._sheet)

        # Find last price row
        for row in range(last_row, 3, -1):
            style = self.get_cell_style(self._sheet, self.COL_CODICE, row)
            if style in self.EP_CODE_STYLES:
                return row + 1

        # Default: after header
        return 5
