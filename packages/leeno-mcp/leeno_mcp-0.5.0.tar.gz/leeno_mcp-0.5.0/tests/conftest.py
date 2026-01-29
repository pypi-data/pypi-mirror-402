"""
Pytest configuration and fixtures for LeenO MCP Server tests.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import mocks
from leeno_mcp.mocks.uno_mock import (
    MockDocument,
    MockSheet,
    MockContext,
    create_mock_uno_module,
    create_leeno_document,
    setup_computo_sheet,
    setup_elenco_prezzi_sheet,
)


# ============================================
# UNO Module Mocking
# ============================================

@pytest.fixture(scope="session", autouse=True)
def mock_uno_module():
    """
    Mock the uno module for all tests.
    This runs once per test session.
    """
    mock_uno = create_mock_uno_module()

    # Mock com.sun.star modules
    mock_connection = MagicMock()
    mock_connection.NoConnectException = Exception

    mock_beans = MagicMock()
    mock_beans.PropertyValue = MagicMock

    # Patch uno and com.sun.star modules
    with patch.dict(sys.modules, {
        'uno': mock_uno,
        'com': MagicMock(),
        'com.sun': MagicMock(),
        'com.sun.star': MagicMock(),
        'com.sun.star.connection': mock_connection,
        'com.sun.star.beans': mock_beans,
    }):
        yield mock_uno


# ============================================
# Document Fixtures
# ============================================

@pytest.fixture
def mock_document() -> MockDocument:
    """Create a basic mock document."""
    return MockDocument()


@pytest.fixture
def leeno_document() -> MockDocument:
    """Create a mock LeenO document with standard sheets and sample data."""
    return create_leeno_document()


@pytest.fixture
def empty_sheet() -> MockSheet:
    """Create an empty mock sheet."""
    return MockSheet("TestSheet")


@pytest.fixture
def computo_sheet() -> MockSheet:
    """Create a mock COMPUTO sheet with sample data."""
    sheet = MockSheet("COMPUTO")
    setup_computo_sheet(sheet)
    return sheet


@pytest.fixture
def elenco_prezzi_sheet() -> MockSheet:
    """Create a mock Elenco Prezzi sheet with sample data."""
    sheet = MockSheet("Elenco Prezzi")
    setup_elenco_prezzi_sheet(sheet)
    return sheet


# ============================================
# DocumentInfo Fixture
# ============================================

@dataclass
class MockDocumentInfo:
    """Mock DocumentInfo for testing wrappers."""
    doc_id: str = "test_doc_001"
    uno_document: Any = None
    path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    modified: bool = False
    is_leeno: bool = True


@pytest.fixture
def document_info(leeno_document) -> MockDocumentInfo:
    """Create a DocumentInfo with a LeenO document."""
    return MockDocumentInfo(
        doc_id="test_doc_001",
        uno_document=leeno_document,
        is_leeno=True
    )


@pytest.fixture
def non_leeno_document_info(mock_document) -> MockDocumentInfo:
    """Create a DocumentInfo with a non-LeenO document."""
    return MockDocumentInfo(
        doc_id="test_doc_002",
        uno_document=mock_document,
        is_leeno=False
    )


# ============================================
# Config Fixtures
# ============================================

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    @dataclass
    class MockUnoConfig:
        host: str = "localhost"
        port: int = 2002
        retry_attempts: int = 3
        retry_delay: float = 1.0

        @property
        def connection_string(self) -> str:
            return f"uno:socket,host={self.host},port={self.port};urp;StarOffice.ComponentContext"

    @dataclass
    class MockServerConfig:
        name: str = "leeno-mcp-test"
        version: str = "0.1.0"
        log_level: str = "DEBUG"
        log_file: Optional[str] = None
        uno: MockUnoConfig = field(default_factory=MockUnoConfig)

    return MockServerConfig()


# ============================================
# Bridge Fixtures
# ============================================

@pytest.fixture
def mock_bridge(mock_uno_module, leeno_document):
    """Create a mock UnoBridge for testing."""
    from leeno_mcp.connection.uno_bridge import UnoBridge

    # Reset singleton
    UnoBridge._instance = None
    UnoBridge._initialized = False

    bridge = UnoBridge()

    # Mock connection state
    bridge._connected = True
    bridge._context = MockContext()
    bridge._desktop = MagicMock()
    bridge._desktop.loadComponentFromURL.return_value = leeno_document

    yield bridge

    # Cleanup singleton
    UnoBridge._instance = None
    UnoBridge._initialized = False


# ============================================
# Document Pool Fixtures
# ============================================

@pytest.fixture
def document_pool():
    """Create a fresh document pool for testing."""
    from leeno_mcp.connection.document_pool import DocumentPool

    pool = DocumentPool()
    yield pool

    # Cleanup
    pool._documents.clear()
    pool._path_index.clear()


# ============================================
# Wrapper Fixtures
# ============================================

@pytest.fixture
def base_wrapper(document_info):
    """Create a base wrapper for testing."""
    from leeno_mcp.wrappers.base import LeenoWrapper
    return LeenoWrapper(document_info)


@pytest.fixture
def computo_wrapper(document_info):
    """Create a computo wrapper for testing."""
    from leeno_mcp.wrappers.computo import ComputoWrapper
    return ComputoWrapper(document_info)


@pytest.fixture
def elenco_prezzi_wrapper(document_info):
    """Create an elenco prezzi wrapper for testing."""
    from leeno_mcp.wrappers.elenco_prezzi import ElencoPrezziWrapper
    return ElencoPrezziWrapper(document_info)


@pytest.fixture
def contabilita_wrapper(document_info):
    """Create a contabilita wrapper for testing."""
    from leeno_mcp.wrappers.contabilita import ContabilitaWrapper
    return ContabilitaWrapper(document_info)


@pytest.fixture
def export_wrapper(document_info):
    """Create an export wrapper for testing."""
    from leeno_mcp.wrappers.export import ExportWrapper
    return ExportWrapper(document_info)


# ============================================
# Model Data Fixtures
# ============================================

@pytest.fixture
def sample_voce_data():
    """Sample data for creating a VoceComputo."""
    return {
        "voce_id": "V001",
        "numero": 1,
        "codice": "01.A01.001",
        "descrizione": "Scavo a sezione aperta in terreno di qualsiasi natura",
        "unita_misura": "mc",
        "quantita": 125.50,
        "prezzo_unitario": 12.50,
        "importo": 1568.75,
        "sicurezza": 47.06,
        "manodopera": 470.63,
        "riga_inizio": 10,
        "riga_fine": 18,
        "capitolo": "CAP_001",
        "misure": []
    }


@pytest.fixture
def sample_prezzo_data():
    """Sample data for creating a Prezzo."""
    return {
        "codice": "01.A01.001",
        "descrizione": "Scavo a sezione aperta in terreno di qualsiasi natura",
        "unita_misura": "mc",
        "prezzo_unitario": 12.50,
        "incidenza_manodopera": 30.0,
        "incidenza_sicurezza": 3.0,
        "riga": 10
    }


@pytest.fixture
def sample_capitolo_data():
    """Sample data for creating a Capitolo."""
    return {
        "capitolo_id": "CAP_001",
        "nome": "OPERE MURARIE",
        "livello": 0,
        "numero": "1",
        "importo_totale": 15000.00,
        "importo_sicurezza": 450.00,
        "importo_manodopera": 4500.00,
        "riga": 5
    }


@pytest.fixture
def sample_misura_data():
    """Sample data for creating a RigaMisura."""
    return {
        "descrizione": "Muro perimetrale piano terra",
        "parti_uguali": 1,
        "lunghezza": 12.50,
        "larghezza": 0.30,
        "altezza": 3.00,
        "quantita": 0,
        "riga": 15
    }


# ============================================
# Async Test Support
# ============================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================
# Temporary Files Fixtures
# ============================================

@pytest.fixture
def temp_ods_file(tmp_path):
    """Create a temporary ODS file path."""
    return tmp_path / "test_document.ods"


@pytest.fixture
def temp_pdf_file(tmp_path):
    """Create a temporary PDF file path."""
    return tmp_path / "test_export.pdf"


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file path."""
    return tmp_path / "test_export.csv"


@pytest.fixture
def temp_xlsx_file(tmp_path):
    """Create a temporary XLSX file path."""
    return tmp_path / "test_export.xlsx"
