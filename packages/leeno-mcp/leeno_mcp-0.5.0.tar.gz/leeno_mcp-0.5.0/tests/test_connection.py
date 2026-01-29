"""
Tests for connection layer (UnoBridge and DocumentPool).
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestUnoBridge:
    """Tests for UnoBridge connection manager."""

    def test_singleton_pattern(self, mock_uno_module):
        """Test that UnoBridge follows singleton pattern."""
        from leeno_mcp.connection.uno_bridge import UnoBridge

        # Reset singleton
        UnoBridge._instance = None
        UnoBridge._initialized = False

        bridge1 = UnoBridge()
        bridge2 = UnoBridge()

        assert bridge1 is bridge2

        # Cleanup
        UnoBridge._instance = None
        UnoBridge._initialized = False

    def test_initial_state(self, mock_uno_module):
        """Test initial connection state."""
        from leeno_mcp.connection.uno_bridge import UnoBridge

        UnoBridge._instance = None
        UnoBridge._initialized = False

        bridge = UnoBridge()

        assert bridge.is_connected is False
        assert bridge._context is None
        assert bridge._desktop is None

        UnoBridge._instance = None
        UnoBridge._initialized = False

    def test_get_bridge_function(self, mock_uno_module):
        """Test get_bridge helper function."""
        from leeno_mcp.connection import uno_bridge

        # Reset
        uno_bridge._bridge = None
        uno_bridge.UnoBridge._instance = None
        uno_bridge.UnoBridge._initialized = False

        bridge1 = uno_bridge.get_bridge()
        bridge2 = uno_bridge.get_bridge()

        assert bridge1 is bridge2

        # Cleanup
        uno_bridge._bridge = None
        uno_bridge.UnoBridge._instance = None
        uno_bridge.UnoBridge._initialized = False

    def test_disconnect(self, mock_bridge):
        """Test disconnection."""
        assert mock_bridge.is_connected is True

        mock_bridge.disconnect()

        assert mock_bridge.is_connected is False
        assert mock_bridge._context is None
        assert mock_bridge._desktop is None

    def test_path_to_url_conversion(self, mock_bridge):
        """Test path to URL conversion."""
        # Test with a simple path
        url = mock_bridge._path_to_url("/tmp/test.ods")
        assert url.startswith("file://")
        assert "test.ods" in url

    def test_url_to_path_conversion(self, mock_bridge):
        """Test URL to path conversion."""
        path = mock_bridge._url_to_path("file:///tmp/test.ods")
        assert "test.ods" in path


class TestDocumentInfo:
    """Tests for DocumentInfo dataclass."""

    def test_create_document_info(self, leeno_document):
        """Test creating a DocumentInfo."""
        from leeno_mcp.connection.document_pool import DocumentInfo

        info = DocumentInfo(
            doc_id="test_001",
            uno_document=leeno_document,
            path="/tmp/test.ods",
            is_leeno=True
        )

        assert info.doc_id == "test_001"
        assert info.path == "/tmp/test.ods"
        assert info.is_leeno is True
        assert info.modified is False
        assert isinstance(info.created_at, datetime)

    def test_sheet_names(self, leeno_document):
        """Test getting sheet names."""
        from leeno_mcp.connection.document_pool import DocumentInfo

        info = DocumentInfo(
            doc_id="test_001",
            uno_document=leeno_document,
            is_leeno=True
        )

        names = info.sheet_names
        assert "COMPUTO" in names
        assert "Elenco Prezzi" in names

    def test_has_sheet(self, leeno_document):
        """Test checking if sheet exists."""
        from leeno_mcp.connection.document_pool import DocumentInfo

        info = DocumentInfo(
            doc_id="test_001",
            uno_document=leeno_document,
            is_leeno=True
        )

        assert info.has_sheet("COMPUTO") is True
        assert info.has_sheet("NonExistent") is False

    def test_get_sheet(self, leeno_document):
        """Test getting a sheet."""
        from leeno_mcp.connection.document_pool import DocumentInfo

        info = DocumentInfo(
            doc_id="test_001",
            uno_document=leeno_document,
            is_leeno=True
        )

        sheet = info.get_sheet("COMPUTO")
        assert sheet is not None
        assert sheet.Name == "COMPUTO"

    def test_get_nonexistent_sheet(self, leeno_document):
        """Test getting a non-existent sheet."""
        from leeno_mcp.connection.document_pool import DocumentInfo

        info = DocumentInfo(
            doc_id="test_001",
            uno_document=leeno_document,
            is_leeno=True
        )

        sheet = info.get_sheet("NonExistent")
        assert sheet is None


class TestDocumentPool:
    """Tests for DocumentPool."""

    def test_add_document(self, mock_uno_module, leeno_document):
        """Test adding a document to the pool."""
        from leeno_mcp.connection.document_pool import DocumentPool

        # Create fresh pool (bypass singleton for testing)
        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        info = pool.add(leeno_document, path="/tmp/test.ods")

        assert info.doc_id is not None
        assert info.path is not None
        assert pool.count() == 1

    def test_add_document_with_custom_id(self, mock_uno_module, leeno_document):
        """Test adding a document with custom ID."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        info = pool.add(leeno_document, doc_id="custom_id")

        assert info.doc_id == "custom_id"

    def test_get_document(self, mock_uno_module, leeno_document):
        """Test getting a document by ID."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        added = pool.add(leeno_document, doc_id="test_doc")
        retrieved = pool.get("test_doc")

        assert retrieved is added

    def test_get_document_not_found(self, mock_uno_module):
        """Test getting a non-existent document."""
        from leeno_mcp.connection.document_pool import DocumentPool
        from leeno_mcp.utils.exceptions import DocumentNotFoundError

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        with pytest.raises(DocumentNotFoundError):
            pool.get("nonexistent")

    def test_get_by_path(self, mock_uno_module, leeno_document, tmp_path):
        """Test getting a document by path."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        test_path = str(tmp_path / "test.ods")
        pool.add(leeno_document, path=test_path, doc_id="test_doc")

        result = pool.get_by_path(test_path)
        assert result is not None
        assert result.doc_id == "test_doc"

    def test_get_by_path_not_found(self, mock_uno_module):
        """Test getting by non-existent path."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        result = pool.get_by_path("/nonexistent/path.ods")
        assert result is None

    def test_remove_document(self, mock_uno_module, leeno_document):
        """Test removing a document."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        pool.add(leeno_document, doc_id="test_doc")
        assert pool.count() == 1

        result = pool.remove("test_doc")
        assert result is True
        assert pool.count() == 0

    def test_remove_nonexistent_document(self, mock_uno_module):
        """Test removing a non-existent document."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        result = pool.remove("nonexistent")
        assert result is False

    def test_list_all(self, mock_uno_module, mock_document, leeno_document):
        """Test listing all documents."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        pool.add(leeno_document, doc_id="leeno_doc")
        pool.add(mock_document, doc_id="regular_doc")

        docs = pool.list_all()
        assert len(docs) == 2

    def test_list_leeno(self, mock_uno_module, mock_document, leeno_document):
        """Test listing only LeenO documents."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        pool.add(leeno_document, doc_id="leeno_doc")
        pool.add(mock_document, doc_id="regular_doc")

        docs = pool.list_leeno()
        assert len(docs) == 1
        assert docs[0].doc_id == "leeno_doc"

    def test_clear(self, mock_uno_module, leeno_document):
        """Test clearing all documents."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        pool.add(leeno_document, doc_id="doc1")
        pool.add(leeno_document, doc_id="doc2")
        assert pool.count() == 2

        count = pool.clear()
        assert count == 2
        assert pool.count() == 0

    def test_mark_modified(self, mock_uno_module, leeno_document):
        """Test marking document as modified."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        pool.add(leeno_document, doc_id="test_doc")
        assert pool.get("test_doc").modified is False

        pool.mark_modified("test_doc")
        assert pool.get("test_doc").modified is True

    def test_mark_saved(self, mock_uno_module, leeno_document, tmp_path):
        """Test marking document as saved."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        pool.add(leeno_document, doc_id="test_doc")
        pool.mark_modified("test_doc")
        assert pool.get("test_doc").modified is True

        new_path = str(tmp_path / "new_location.ods")
        pool.mark_saved("test_doc", path=new_path)

        info = pool.get("test_doc")
        assert info.modified is False
        assert info.path == new_path

    def test_ensure_leeno(self, mock_uno_module, leeno_document):
        """Test ensure_leeno with valid LeenO document."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        pool.add(leeno_document, doc_id="test_doc")

        info = pool.ensure_leeno("test_doc")
        assert info is not None
        assert info.is_leeno is True

    def test_ensure_leeno_with_non_leeno(self, mock_uno_module, mock_document):
        """Test ensure_leeno with non-LeenO document."""
        from leeno_mcp.connection.document_pool import DocumentPool
        from leeno_mcp.utils.exceptions import InvalidDocumentError

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        pool.add(mock_document, doc_id="regular_doc")

        with pytest.raises(InvalidDocumentError):
            pool.ensure_leeno("regular_doc")

    def test_check_is_leeno(self, mock_uno_module, leeno_document, mock_document):
        """Test LeenO document detection."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        # LeenO document has S2 and COMPUTO sheets
        assert pool._check_is_leeno(leeno_document) is True

        # Regular document doesn't
        assert pool._check_is_leeno(mock_document) is False

    def test_generate_doc_id(self, mock_uno_module):
        """Test document ID generation."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = True

        id1 = pool._generate_doc_id()
        id2 = pool._generate_doc_id()

        assert id1.startswith("doc_")
        assert id2.startswith("doc_")
        assert id1 != id2
        assert len(id1) == 12  # "doc_" + 8 hex chars
