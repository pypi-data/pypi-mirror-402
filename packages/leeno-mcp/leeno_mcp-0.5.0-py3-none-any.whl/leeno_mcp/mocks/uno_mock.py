"""
Mock UNO API for testing without LibreOffice.

Provides mock implementations of the key UNO interfaces used by LeenO MCP Server.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from unittest.mock import MagicMock


class CellTypeEnum(Enum):
    """Mock for com.sun.star.table.CellContentType"""
    EMPTY = "EMPTY"
    VALUE = "VALUE"
    TEXT = "TEXT"
    FORMULA = "FORMULA"


@dataclass
class MockCellAddress:
    """Mock for com.sun.star.table.CellAddress"""
    Sheet: int = 0
    Column: int = 0
    Row: int = 0


@dataclass
class MockRangeAddress:
    """Mock for com.sun.star.table.CellRangeAddress"""
    Sheet: int = 0
    StartColumn: int = 0
    StartRow: int = 0
    EndColumn: int = 0
    EndRow: int = 0


@dataclass
class MockCell:
    """Mock for com.sun.star.table.Cell"""
    _value: float = 0.0
    _string: str = ""
    _formula: str = ""
    CellStyle: str = "Default"

    @property
    def Value(self) -> float:
        return self._value

    @Value.setter
    def Value(self, val: float):
        self._value = val
        self._string = ""

    @property
    def String(self) -> str:
        return self._string if self._string else str(self._value) if self._value else ""

    @String.setter
    def String(self, val: str):
        self._string = val
        try:
            self._value = float(val)
        except ValueError:
            self._value = 0.0

    @property
    def Formula(self) -> str:
        return self._formula

    @Formula.setter
    def Formula(self, val: str):
        self._formula = val

    @property
    def Type(self) -> CellTypeEnum:
        if self._formula:
            return CellTypeEnum.FORMULA
        if self._value != 0:
            return CellTypeEnum.VALUE
        if self._string:
            return CellTypeEnum.TEXT
        return CellTypeEnum.EMPTY

    def getCellAddress(self) -> MockCellAddress:
        return MockCellAddress()


class MockRows:
    """Mock for sheet rows collection"""

    def __init__(self, sheet: 'MockSheet'):
        self._sheet = sheet

    def insertByIndex(self, row: int, count: int = 1):
        """Insert rows - shifts existing row data down"""
        # Since _cells is a dict, we just need to shift cell positions
        # For simplicity in mock, we just accept the call without actually shifting
        pass

    def removeByIndex(self, row: int, count: int = 1):
        """Remove rows - shifts existing row data up"""
        # Since _cells is a dict, we just need to shift cell positions
        # For simplicity in mock, we just accept the call without actually shifting
        pass


class MockCursor:
    """Mock for sheet cursor"""

    def __init__(self, sheet: 'MockSheet'):
        self._sheet = sheet
        self.RangeAddress = MockRangeAddress()

    def gotoEndOfUsedArea(self, expand: bool):
        self.RangeAddress.EndRow = self._sheet._last_row
        self.RangeAddress.EndColumn = self._sheet._last_col


class MockSheet:
    """Mock for com.sun.star.sheet.Spreadsheet"""

    def __init__(self, name: str):
        self.Name = name
        self._cells: Dict[Tuple[int, int], MockCell] = {}
        self._last_row = 10
        self._last_col = 10

    def getCellByPosition(self, col: int, row: int) -> MockCell:
        key = (col, row)
        if key not in self._cells:
            self._cells[key] = MockCell()
        return self._cells[key]

    def getCellRangeByPosition(self, start_col: int, start_row: int, end_col: int, end_row: int):
        range_obj = MagicMock()
        range_obj.getRangeAddress.return_value = MockRangeAddress(
            StartColumn=start_col, StartRow=start_row,
            EndColumn=end_col, EndRow=end_row
        )
        return range_obj

    def createCursor(self) -> MockCursor:
        return MockCursor(self)

    def getRows(self) -> MockRows:
        return MockRows(self)

    def copyRange(self, dest_address, source_address):
        pass

    def set_cell_data(self, col: int, row: int, value: Any, style: str = "Default"):
        """Helper to set up test data"""
        cell = self.getCellByPosition(col, row)
        if isinstance(value, (int, float)):
            cell.Value = value
        else:
            cell.String = str(value)
        cell.CellStyle = style
        self._last_row = max(self._last_row, row)
        self._last_col = max(self._last_col, col)


class MockSheets:
    """Mock for sheets collection"""

    def __init__(self):
        self._sheets: Dict[str, MockSheet] = {}

    def hasByName(self, name: str) -> bool:
        return name in self._sheets

    def getByName(self, name: str) -> MockSheet:
        return self._sheets[name]

    def getElementNames(self) -> Tuple[str, ...]:
        return tuple(self._sheets.keys())

    def insertNewByName(self, name: str, position: int):
        self._sheets[name] = MockSheet(name)

    def add_sheet(self, name: str) -> MockSheet:
        """Helper to add a sheet"""
        sheet = MockSheet(name)
        self._sheets[name] = sheet
        return sheet


class MockDocument:
    """Mock for com.sun.star.sheet.SpreadsheetDocument"""

    def __init__(self):
        self._sheets = MockSheets()
        self._url = ""
        self._modified = False
        self._closed = False
        self._calculation_enabled = True
        self._controllers_locked = False
        self._action_locked = False

    @property
    def URL(self) -> str:
        return self._url

    @URL.setter
    def URL(self, val: str):
        self._url = val

    def getSheets(self) -> MockSheets:
        return self._sheets

    def enableAutomaticCalculation(self, enable: bool):
        self._calculation_enabled = enable

    def lockControllers(self):
        self._controllers_locked = True

    def unlockControllers(self):
        self._controllers_locked = False

    def addActionLock(self):
        self._action_locked = True

    def removeActionLock(self):
        self._action_locked = False

    def calculateAll(self):
        pass

    def store(self):
        self._modified = False

    def storeToURL(self, url: str, props: tuple):
        self._url = url
        self._modified = False

    def close(self, deliver_ownership: bool):
        self._closed = True


class MockDesktop:
    """Mock for com.sun.star.frame.Desktop"""

    def __init__(self):
        self._documents: List[MockDocument] = []

    def loadComponentFromURL(self, url: str, target: str, flags: int, props: tuple) -> MockDocument:
        doc = MockDocument()
        doc.URL = url
        self._documents.append(doc)
        return doc


class MockServiceManager:
    """Mock for com.sun.star.lang.XMultiComponentFactory"""

    def __init__(self):
        self._desktop = MockDesktop()

    def createInstanceWithContext(self, service_name: str, context: Any) -> Any:
        if service_name == "com.sun.star.frame.Desktop":
            return self._desktop
        elif service_name == "com.sun.star.bridge.UnoUrlResolver":
            return MockResolver()
        return MagicMock()


class MockContext:
    """Mock for com.sun.star.uno.XComponentContext"""

    def __init__(self):
        self.ServiceManager = MockServiceManager()


class MockResolver:
    """Mock for com.sun.star.bridge.UnoUrlResolver"""

    def resolve(self, connection_string: str) -> MockContext:
        return MockContext()


def create_mock_uno_module():
    """Create a mock uno module"""
    mock_uno = MagicMock()
    mock_uno.getComponentContext.return_value = MockContext()
    mock_uno.systemPathToFileUrl = lambda path: f"file:///{path.replace(chr(92), '/')}"
    mock_uno.fileUrlToSystemPath = lambda url: url.replace("file:///", "").replace("/", chr(92))
    return mock_uno


def create_leeno_document() -> MockDocument:
    """Create a mock LeenO document with standard sheets"""
    doc = MockDocument()
    sheets = doc.getSheets()

    # Add standard LeenO sheets (S2 and COMPUTO required for _check_is_leeno)
    computo = sheets.add_sheet("COMPUTO")
    sheets.add_sheet("VARIANTE")
    sheets.add_sheet("CONTABILITA")
    elenco_prezzi = sheets.add_sheet("Elenco Prezzi")
    sheets.add_sheet("S2")  # Required for LeenO detection
    sheets.add_sheet("S5")  # Template sheet
    sheets.add_sheet("M1")
    sheets.add_sheet("S1")

    # Set up some sample data for COMPUTO
    setup_computo_sheet(computo)

    # Set up some sample data for Elenco Prezzi
    setup_elenco_prezzi_sheet(elenco_prezzi)

    return doc


def setup_computo_sheet(sheet: MockSheet):
    """Set up sample COMPUTO data"""
    # Header row
    sheet.set_cell_data(0, 0, "N.", "Header")
    sheet.set_cell_data(1, 0, "CODICE", "Header")
    sheet.set_cell_data(2, 0, "DESCRIZIONE", "Header")
    sheet.set_cell_data(3, 0, "U.M.", "Header")
    sheet.set_cell_data(4, 0, "QUANTITA", "Header")
    sheet.set_cell_data(5, 0, "PREZZO UNIT.", "Header")
    sheet.set_cell_data(6, 0, "IMPORTO", "Header")

    # Chapter
    sheet.set_cell_data(0, 1, "1", "Livello-0-scritta")
    sheet.set_cell_data(1, 1, "", "Livello-0-scritta")
    sheet.set_cell_data(2, 1, "OPERE MURARIE", "Livello-0-scritta")

    # Sample voce (start)
    sheet.set_cell_data(0, 2, "1", "Comp Start Attributo")
    sheet.set_cell_data(1, 2, "01.A01.001", "Comp Start Attributo")
    sheet.set_cell_data(2, 2, "Scavo a sezione aperta", "Comp Start Attributo")
    sheet.set_cell_data(3, 2, "mc", "Comp Start Attributo")

    # Measurement row
    sheet.set_cell_data(2, 3, "Muro esterno", "comp 1-a")
    sheet.set_cell_data(4, 3, 1, "comp 1-a")  # parti uguali
    sheet.set_cell_data(5, 3, 10.0, "comp 1-a")  # lunghezza
    sheet.set_cell_data(6, 3, 0.30, "comp 1-a")  # larghezza
    sheet.set_cell_data(7, 3, 3.0, "comp 1-a")  # altezza
    sheet.set_cell_data(8, 3, 9.0, "comp 1-a")  # quantità

    # Sample voce (end)
    sheet.set_cell_data(0, 4, "", "Comp End Attributo")
    sheet.set_cell_data(4, 4, 9.0, "Comp End Attributo")  # quantità totale
    sheet.set_cell_data(5, 4, 12.50, "Comp End Attributo")  # prezzo
    sheet.set_cell_data(6, 4, 112.50, "Comp End Attributo")  # importo

    sheet._last_row = 4


def setup_elenco_prezzi_sheet(sheet: MockSheet):
    """Set up sample Elenco Prezzi data"""
    # Header
    sheet.set_cell_data(0, 0, "CODICE", "Header")
    sheet.set_cell_data(1, 0, "DESCRIZIONE", "Header")
    sheet.set_cell_data(2, 0, "U.M.", "Header")
    sheet.set_cell_data(3, 0, "PREZZO", "Header")
    sheet.set_cell_data(4, 0, "% MO", "Header")
    sheet.set_cell_data(5, 0, "% SIC", "Header")

    # Sample prices
    sheet.set_cell_data(0, 1, "01.A01.001", "EP-Cs")
    sheet.set_cell_data(1, 1, "Scavo a sezione aperta in terreno di qualsiasi natura", "EP-Cs")
    sheet.set_cell_data(2, 1, "mc", "EP-Cs")
    sheet.set_cell_data(3, 1, 12.50, "EP-Cs")
    sheet.set_cell_data(4, 1, 30.0, "EP-Cs")
    sheet.set_cell_data(5, 1, 3.0, "EP-Cs")

    sheet.set_cell_data(0, 2, "01.A01.002", "EP-Cs")
    sheet.set_cell_data(1, 2, "Scavo in trincea per posa tubazioni", "EP-Cs")
    sheet.set_cell_data(2, 2, "mc", "EP-Cs")
    sheet.set_cell_data(3, 2, 18.00, "EP-Cs")
    sheet.set_cell_data(4, 2, 35.0, "EP-Cs")
    sheet.set_cell_data(5, 2, 3.0, "EP-Cs")

    sheet.set_cell_data(0, 3, "02.B01.001", "EP-Cs")
    sheet.set_cell_data(1, 3, "Calcestruzzo per fondazioni", "EP-Cs")
    sheet.set_cell_data(2, 3, "mc", "EP-Cs")
    sheet.set_cell_data(3, 3, 125.00, "EP-Cs")
    sheet.set_cell_data(4, 3, 25.0, "EP-Cs")
    sheet.set_cell_data(5, 3, 2.5, "EP-Cs")

    sheet._last_row = 3
