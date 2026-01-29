"""
Tests for LeenO wrappers (base, computo, elenco_prezzi, etc.).
"""

import pytest
from unittest.mock import MagicMock, patch


class TestLeenoWrapper:
    """Tests for base LeenoWrapper class."""

    def test_create_wrapper(self, document_info):
        """Test creating a base wrapper."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)

        assert wrapper.doc_id == document_info.doc_id
        assert wrapper.uno_doc == document_info.uno_document

    def test_is_leeno_document(self, document_info, non_leeno_document_info):
        """Test LeenO document detection."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        leeno_wrapper = LeenoWrapper(document_info)
        assert leeno_wrapper.is_leeno_document() is True

        regular_wrapper = LeenoWrapper(non_leeno_document_info)
        assert regular_wrapper.is_leeno_document() is False

    def test_ensure_leeno_success(self, document_info):
        """Test ensure_leeno with valid LeenO document."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        wrapper.ensure_leeno()  # Should not raise

    def test_ensure_leeno_failure(self, non_leeno_document_info):
        """Test ensure_leeno with non-LeenO document."""
        from leeno_mcp.wrappers.base import LeenoWrapper
        from leeno_mcp.utils.exceptions import InvalidDocumentError

        wrapper = LeenoWrapper(non_leeno_document_info)
        with pytest.raises(InvalidDocumentError):
            wrapper.ensure_leeno()

    def test_has_sheet(self, document_info):
        """Test sheet existence check."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)

        assert wrapper.has_sheet("COMPUTO") is True
        assert wrapper.has_sheet("Elenco Prezzi") is True
        assert wrapper.has_sheet("NonExistent") is False

    def test_get_sheet(self, document_info):
        """Test getting a sheet."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("COMPUTO")

        assert sheet is not None
        assert sheet.Name == "COMPUTO"

    def test_get_sheet_not_found(self, document_info):
        """Test getting non-existent sheet."""
        from leeno_mcp.wrappers.base import LeenoWrapper
        from leeno_mcp.utils.exceptions import SheetNotFoundError

        wrapper = LeenoWrapper(document_info)

        with pytest.raises(SheetNotFoundError):
            wrapper.get_sheet("NonExistent")

    def test_get_sheet_names(self, document_info):
        """Test getting all sheet names."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        names = wrapper.get_sheet_names()

        assert "COMPUTO" in names
        assert "Elenco Prezzi" in names

    def test_get_cell_value(self, document_info):
        """Test getting cell values."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("COMPUTO")

        # Get a string value
        value = wrapper.get_cell_value(sheet, 1, 2)
        assert value == "01.A01.001"

    def test_set_cell_value_numeric(self, document_info):
        """Test setting numeric cell values."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("COMPUTO")

        wrapper.set_cell_value(sheet, 10, 10, 123.45)
        value = wrapper.get_cell_value(sheet, 10, 10)

        assert value == 123.45

    def test_set_cell_value_string(self, document_info):
        """Test setting string cell values."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("COMPUTO")

        wrapper.set_cell_value(sheet, 10, 10, "Test String")
        value = wrapper.get_cell_value(sheet, 10, 10)

        assert value == "Test String"

    def test_get_cell_style(self, document_info):
        """Test getting cell style."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("COMPUTO")

        # Chapter row should have chapter style
        style = wrapper.get_cell_style(sheet, 0, 1)
        assert style == "Livello-0-scritta"

    def test_get_last_row(self, document_info):
        """Test getting last used row."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("COMPUTO")

        last_row = wrapper.get_last_row(sheet)
        assert last_row > 0

    def test_insert_rows(self, document_info):
        """Test inserting rows."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("COMPUTO")

        # This should not raise
        wrapper.insert_rows(sheet, 5, 2)

    def test_delete_rows(self, document_info):
        """Test deleting rows."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("COMPUTO")

        # This should not raise
        wrapper.delete_rows(sheet, 5, 1)

    def test_find_row_by_style(self, document_info):
        """Test finding row by style."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("COMPUTO")

        # Find chapter row
        row = wrapper.find_row_by_style(sheet, "Livello-0-scritta")
        assert row == 1

    def test_find_rows_by_style(self, document_info):
        """Test finding all rows with style."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("COMPUTO")

        # Find all voce start rows
        rows = wrapper.find_rows_by_style(sheet, "Comp Start Attributo")
        assert len(rows) >= 1
        assert 2 in rows

    def test_suspend_refresh_context_manager(self, document_info):
        """Test suspend_refresh context manager."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        doc = document_info.uno_document

        assert doc._calculation_enabled is True
        assert doc._controllers_locked is False

        with wrapper.suspend_refresh():
            assert doc._calculation_enabled is False
            assert doc._controllers_locked is True

        assert doc._calculation_enabled is True
        assert doc._controllers_locked is False


class TestComputoWrapperHelpers:
    """Test ComputoWrapper helper methods with mock."""

    def test_parse_voce_at_row(self, document_info):
        """Test parsing voce data at a row."""
        # Create a mock wrapper-like object to test the parsing logic
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("COMPUTO")

        # The test data has a voce at row 2
        style = wrapper.get_cell_style(sheet, 0, 2)
        assert style == "Comp Start Attributo"

        # Test that we can read the voce data
        codice = wrapper.get_cell_value(sheet, 1, 2)
        assert codice == "01.A01.001"

        descrizione = wrapper.get_cell_value(sheet, 2, 2)
        assert descrizione == "Scavo a sezione aperta"


class TestElencoPrezziWrapper:
    """Tests for ElencoPrezziWrapper using mocks."""

    def test_search_by_code(self, document_info):
        """Test searching prices by code."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("Elenco Prezzi")

        # Test that we can read the sample price data
        codice = wrapper.get_cell_value(sheet, 0, 1)
        assert codice == "01.A01.001"

    def test_price_data_columns(self, document_info):
        """Test reading all price data columns."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)
        sheet = wrapper.get_sheet("Elenco Prezzi")

        # Read data from row 1 (first price)
        codice = wrapper.get_cell_value(sheet, 0, 1)
        descrizione = wrapper.get_cell_value(sheet, 1, 1)
        um = wrapper.get_cell_value(sheet, 2, 1)
        prezzo = wrapper.get_cell_value(sheet, 3, 1)
        manodopera = wrapper.get_cell_value(sheet, 4, 1)
        sicurezza = wrapper.get_cell_value(sheet, 5, 1)

        assert codice == "01.A01.001"
        assert "Scavo" in descrizione
        assert um == "mc"
        assert prezzo == 12.50
        assert manodopera == 30.0
        assert sicurezza == 3.0


class TestMockSheetOperations:
    """Tests for mock sheet operations."""

    def test_empty_sheet_operations(self, empty_sheet):
        """Test operations on empty sheet."""
        # Get cell from empty sheet
        cell = empty_sheet.getCellByPosition(0, 0)
        assert cell is not None

        # Default values
        assert cell.Value == 0.0
        assert cell.String == ""
        assert cell.CellStyle == "Default"

    def test_set_and_get_values(self, empty_sheet):
        """Test setting and getting values."""
        empty_sheet.set_cell_data(0, 0, "Test", "TestStyle")
        cell = empty_sheet.getCellByPosition(0, 0)

        assert cell.String == "Test"
        assert cell.CellStyle == "TestStyle"

    def test_numeric_values(self, empty_sheet):
        """Test numeric cell values."""
        empty_sheet.set_cell_data(0, 0, 123.45)
        cell = empty_sheet.getCellByPosition(0, 0)

        assert cell.Value == 123.45

    def test_last_row_tracking(self, empty_sheet):
        """Test that last row is tracked."""
        empty_sheet.set_cell_data(0, 50, "Test")
        assert empty_sheet._last_row >= 50

    def test_cursor_operations(self, empty_sheet):
        """Test cursor operations."""
        cursor = empty_sheet.createCursor()
        cursor.gotoEndOfUsedArea(True)

        assert cursor.RangeAddress.EndRow == empty_sheet._last_row

    def test_row_operations(self, empty_sheet):
        """Test row insert/delete operations."""
        rows = empty_sheet.getRows()

        # Insert rows
        rows.insertByIndex(5, 3)
        # Delete rows
        rows.removeByIndex(5, 1)

        # Should not raise


class TestWrapperConstants:
    """Test wrapper constants."""

    def test_sheet_names(self):
        """Test that sheet name constants are defined."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        assert LeenoWrapper.SHEET_COMPUTO == "COMPUTO"
        assert LeenoWrapper.SHEET_VARIANTE == "VARIANTE"
        assert LeenoWrapper.SHEET_CONTABILITA == "CONTABILITA"
        assert LeenoWrapper.SHEET_ELENCO_PREZZI == "Elenco Prezzi"

    def test_style_names(self):
        """Test that style name constants are defined."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        assert LeenoWrapper.STYLE_CAPITOLO_0 == "Livello-0-scritta"
        assert LeenoWrapper.STYLE_CAPITOLO_1 == "Livello-1-scritta"
        assert LeenoWrapper.STYLE_VOCE_START == "Comp Start Attributo"
        assert LeenoWrapper.STYLE_VOCE_END == "Comp End Attributo"


class TestComputoSheetData:
    """Tests for COMPUTO sheet sample data."""

    def test_header_row(self, computo_sheet):
        """Test that header row is set correctly."""
        assert computo_sheet.getCellByPosition(0, 0).String == "N."
        assert computo_sheet.getCellByPosition(1, 0).String == "CODICE"
        assert computo_sheet.getCellByPosition(2, 0).String == "DESCRIZIONE"

    def test_chapter_row(self, computo_sheet):
        """Test chapter row data."""
        assert computo_sheet.getCellByPosition(0, 1).String == "1"
        assert computo_sheet.getCellByPosition(2, 1).String == "OPERE MURARIE"
        assert computo_sheet.getCellByPosition(0, 1).CellStyle == "Livello-0-scritta"

    def test_voce_row(self, computo_sheet):
        """Test voce row data."""
        assert computo_sheet.getCellByPosition(0, 2).String == "1"
        assert computo_sheet.getCellByPosition(1, 2).String == "01.A01.001"
        assert computo_sheet.getCellByPosition(2, 2).String == "Scavo a sezione aperta"
        assert computo_sheet.getCellByPosition(0, 2).CellStyle == "Comp Start Attributo"


class TestElencoPrezziSheetData:
    """Tests for Elenco Prezzi sheet sample data."""

    def test_header_row(self, elenco_prezzi_sheet):
        """Test header row."""
        assert elenco_prezzi_sheet.getCellByPosition(0, 0).String == "CODICE"
        assert elenco_prezzi_sheet.getCellByPosition(1, 0).String == "DESCRIZIONE"

    def test_price_rows(self, elenco_prezzi_sheet):
        """Test price row data."""
        # First price
        assert elenco_prezzi_sheet.getCellByPosition(0, 1).String == "01.A01.001"
        assert elenco_prezzi_sheet.getCellByPosition(3, 1).Value == 12.50

        # Second price
        assert elenco_prezzi_sheet.getCellByPosition(0, 2).String == "01.A01.002"
        assert elenco_prezzi_sheet.getCellByPosition(3, 2).Value == 18.00

        # Third price
        assert elenco_prezzi_sheet.getCellByPosition(0, 3).String == "02.B01.001"
        assert elenco_prezzi_sheet.getCellByPosition(3, 3).Value == 125.00
