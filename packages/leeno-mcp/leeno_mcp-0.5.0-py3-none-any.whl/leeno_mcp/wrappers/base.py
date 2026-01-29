"""
Base wrapper class for LeenO operations.

Provides common functionality for all LeenO wrappers.
"""

import logging
import re
from typing import Any, Optional, List, Union
from contextlib import contextmanager

from ..connection.document_pool import DocumentInfo
from ..utils.exceptions import SheetNotFoundError, InvalidDocumentError

logger = logging.getLogger(__name__)


def parse_percentage(value: Any) -> float:
    """
    Parse a percentage value.

    Handles formats like:
    - "50.11%" or "50,11%"
    - 0.5011 (decimal form, will be multiplied by 100)
    - 50.11 (already a percentage)

    Args:
        value: Value to parse (string or numeric)

    Returns:
        Float value as percentage (0-100)
    """
    if isinstance(value, (int, float)):
        # If value is small (< 1), assume it's decimal form
        if abs(value) < 1:
            return value * 100
        return float(value)

    if not value or value == "":
        return 0.0

    # Convert to string and strip
    s = str(value).strip()

    # Handle percentage sign
    is_percentage = '%' in s
    s = s.replace('%', '').strip()

    # Handle Italian decimal comma
    s = s.replace(',', '.')

    # Remove any remaining non-numeric characters
    s = re.sub(r'[^\d.\-]', '', s)

    if not s:
        return 0.0

    try:
        result = float(s)
        # If it was explicitly a percentage string, it's already in correct form
        # If it's a small decimal without %, multiply by 100
        if not is_percentage and abs(result) < 1:
            result *= 100
        return result
    except ValueError:
        logger.warning(f"Could not parse percentage value: {value}")
        return 0.0


def parse_currency(value: Any) -> float:
    """
    Parse a currency value that may have Italian formatting.

    Handles formats like:
    - "€ 67,75" or "€ 67.75"
    - "€ 36.066,51" (Italian: dot as thousands, comma as decimal)
    - "€ 36,066.51" (US: comma as thousands, dot as decimal)
    - Plain numbers: 67.75, 67,75

    Args:
        value: Value to parse (string or numeric)

    Returns:
        Float value
    """
    if isinstance(value, (int, float)):
        return float(value)

    if not value or value == "":
        return 0.0

    # Convert to string and strip
    s = str(value).strip()

    # Remove currency symbols and whitespace
    s = re.sub(r'[€$£¥\s]', '', s)

    # Handle special characters that might appear as currency symbol
    s = s.replace('�', '').strip()

    # If empty after cleaning, return 0
    if not s or s in ('#N/D', '#N/A', '#REF!', '#VALUE!', '-'):
        return 0.0

    # Detect format: Italian (1.234,56) vs US (1,234.56)
    # Count dots and commas
    dots = s.count('.')
    commas = s.count(',')

    if dots > 0 and commas > 0:
        # Both present - determine which is decimal separator
        last_dot = s.rfind('.')
        last_comma = s.rfind(',')

        if last_comma > last_dot:
            # Italian format: 1.234,56 -> comma is decimal
            s = s.replace('.', '').replace(',', '.')
        else:
            # US format: 1,234.56 -> dot is decimal
            s = s.replace(',', '')
    elif commas == 1 and dots == 0:
        # Single comma - treat as decimal separator (Italian)
        s = s.replace(',', '.')
    elif commas > 1:
        # Multiple commas - thousands separators (US format, no decimals)
        s = s.replace(',', '')
    # else: dots only or no separators - use as-is

    try:
        return float(s)
    except ValueError:
        logger.warning(f"Could not parse currency value: {value}")
        return 0.0


class LeenoWrapper:
    """
    Base class for LeenO document operations.

    Provides common methods for accessing sheets, cells, and ranges.
    All specific wrappers (Computo, Prezzi, etc.) inherit from this.
    """

    # Standard LeenO sheet names
    SHEET_COMPUTO = "COMPUTO"
    SHEET_VARIANTE = "VARIANTE"
    SHEET_CONTABILITA = "CONTABILITA"
    SHEET_ELENCO_PREZZI = "Elenco Prezzi"
    SHEET_ANALISI = "Analisi di Prezzo"
    SHEET_GIORNALE = "GIORNALE"
    SHEET_M1 = "M1"
    SHEET_S1 = "S1"
    SHEET_S2 = "S2"
    SHEET_S5 = "S5"

    # Cell styles used in LeenO
    STYLE_CAPITOLO_0 = "Livello-0-scritta"
    STYLE_CAPITOLO_1 = "Livello-1-scritta"
    STYLE_CAPITOLO_2 = "livello2 valuta"
    STYLE_VOCE_START = "Comp Start Attributo"
    STYLE_VOCE_END = "Comp End Attributo"
    STYLE_VOCE_PROGRESS = "comp progress"
    STYLE_EP_CODE = "EP-Cs"
    STYLE_EP_CODE_ALT = "EP-aS"  # Alternative style used in some EP sheets
    EP_CODE_STYLES = ("EP-Cs", "EP-aS")  # All valid EP code styles

    def __init__(self, document: DocumentInfo):
        """
        Initialize wrapper with document.

        Args:
            document: DocumentInfo from the document pool
        """
        self._doc = document
        self._uno_doc = document.uno_document

    @property
    def doc_id(self) -> str:
        """Get document ID."""
        return self._doc.doc_id

    @property
    def uno_doc(self) -> Any:
        """Get UNO document object."""
        return self._uno_doc

    def is_leeno_document(self) -> bool:
        """Check if this is a valid LeenO document."""
        return self._doc.is_leeno

    def ensure_leeno(self) -> None:
        """
        Ensure this is a LeenO document.

        Raises:
            InvalidDocumentError: If not a LeenO document
        """
        if not self.is_leeno_document():
            raise InvalidDocumentError(f"Document '{self.doc_id}' is not a valid LeenO document")

    def has_sheet(self, name: str) -> bool:
        """Check if document has a sheet with given name."""
        try:
            return self._uno_doc.getSheets().hasByName(name)
        except Exception:
            return False

    def get_sheet(self, name: str) -> Any:
        """
        Get sheet by name.

        Args:
            name: Sheet name

        Returns:
            com.sun.star.sheet.Spreadsheet

        Raises:
            SheetNotFoundError: If sheet not found
        """
        try:
            sheets = self._uno_doc.getSheets()
            if not sheets.hasByName(name):
                raise SheetNotFoundError(name)
            return sheets.getByName(name)
        except SheetNotFoundError:
            raise
        except Exception:
            raise SheetNotFoundError(name)

    def get_sheet_names(self) -> List[str]:
        """Get list of all sheet names."""
        try:
            return list(self._uno_doc.getSheets().getElementNames())
        except Exception:
            return []

    def get_cell(self, sheet: Any, col: int, row: int) -> Any:
        """
        Get cell by column and row index.

        Args:
            sheet: Sheet object
            col: Column index (0-based)
            row: Row index (0-based)

        Returns:
            Cell object
        """
        return sheet.getCellByPosition(col, row)

    def get_cell_value(self, sheet: Any, col: int, row: int) -> Any:
        """Get cell value (numeric or string)."""
        cell = self.get_cell(sheet, col, row)
        if cell.Type.value == "VALUE":
            return cell.Value
        return cell.String

    def set_cell_value(self, sheet: Any, col: int, row: int, value: Any) -> None:
        """Set cell value."""
        cell = self.get_cell(sheet, col, row)
        if isinstance(value, (int, float)):
            cell.Value = value
        else:
            cell.String = str(value)

    def get_cell_style(self, sheet: Any, col: int, row: int) -> str:
        """Get cell style name."""
        return self.get_cell(sheet, col, row).CellStyle

    def get_range(self, sheet: Any, start_col: int, start_row: int, end_col: int, end_row: int) -> Any:
        """Get cell range."""
        return sheet.getCellRangeByPosition(start_col, start_row, end_col, end_row)

    def get_last_row(self, sheet: Any) -> int:
        """
        Get last used row in sheet.

        Returns:
            Last row index (0-based)
        """
        try:
            cursor = sheet.createCursor()
            cursor.gotoEndOfUsedArea(True)
            return cursor.RangeAddress.EndRow
        except Exception:
            return 0

    def get_last_column(self, sheet: Any) -> int:
        """
        Get last used column in sheet.

        Returns:
            Last column index (0-based)
        """
        try:
            cursor = sheet.createCursor()
            cursor.gotoEndOfUsedArea(True)
            return cursor.RangeAddress.EndColumn
        except Exception:
            return 0

    @contextmanager
    def suspend_refresh(self):
        """
        Context manager to suspend document refresh for faster operations.

        Usage:
            with wrapper.suspend_refresh():
                # Do many operations
                pass
        """
        try:
            self._uno_doc.enableAutomaticCalculation(False)
            self._uno_doc.lockControllers()
            self._uno_doc.addActionLock()
            yield
        finally:
            self._uno_doc.removeActionLock()
            self._uno_doc.unlockControllers()
            self._uno_doc.enableAutomaticCalculation(True)
            self._uno_doc.calculateAll()

    def insert_rows(self, sheet: Any, row: int, count: int = 1) -> None:
        """
        Insert rows at position.

        Args:
            sheet: Sheet object
            row: Row index where to insert
            count: Number of rows to insert
        """
        sheet.getRows().insertByIndex(row, count)

    def delete_rows(self, sheet: Any, row: int, count: int = 1) -> None:
        """
        Delete rows at position.

        Args:
            sheet: Sheet object
            row: Row index where to start deletion
            count: Number of rows to delete
        """
        sheet.getRows().removeByIndex(row, count)

    def copy_range(self, source_sheet: Any, source_range: Any, dest_sheet: Any, dest_row: int, dest_col: int = 0) -> None:
        """
        Copy a range to destination.

        Args:
            source_sheet: Source sheet
            source_range: Range to copy
            dest_sheet: Destination sheet
            dest_row: Destination start row
            dest_col: Destination start column
        """
        dest_cell = dest_sheet.getCellByPosition(dest_col, dest_row)
        dest_sheet.copyRange(dest_cell.getCellAddress(), source_range.getRangeAddress())

    def find_row_by_style(self, sheet: Any, style: str, start_row: int = 0, col: int = 0) -> Optional[int]:
        """
        Find first row with given cell style.

        Args:
            sheet: Sheet object
            style: Cell style name to find
            start_row: Row to start searching from
            col: Column to check

        Returns:
            Row index or None if not found
        """
        last_row = self.get_last_row(sheet)
        for row in range(start_row, last_row + 1):
            if self.get_cell_style(sheet, col, row) == style:
                return row
        return None

    def find_rows_by_style(self, sheet: Any, style: str, start_row: int = 0, col: int = 0) -> List[int]:
        """
        Find all rows with given cell style.

        Args:
            sheet: Sheet object
            style: Cell style name to find
            start_row: Row to start searching from
            col: Column to check

        Returns:
            List of row indices
        """
        result = []
        last_row = self.get_last_row(sheet)
        for row in range(start_row, last_row + 1):
            if self.get_cell_style(sheet, col, row) == style:
                result.append(row)
        return result
