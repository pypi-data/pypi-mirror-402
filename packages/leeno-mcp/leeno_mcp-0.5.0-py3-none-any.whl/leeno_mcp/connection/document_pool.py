"""
Document Pool - Manages open LeenO documents.

Tracks all documents opened through the MCP server,
providing document lifecycle management and lookup.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

from .uno_bridge import UnoBridge, get_bridge
from ..utils.exceptions import DocumentNotFoundError, InvalidDocumentError

logger = logging.getLogger(__name__)


@dataclass
class DocumentInfo:
    """Information about an open document."""

    doc_id: str
    uno_document: Any  # com.sun.star.sheet.SpreadsheetDocument
    path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    modified: bool = False
    is_leeno: bool = False

    @property
    def title(self) -> str:
        """Get document title."""
        try:
            return self.uno_document.Title or "Untitled"
        except Exception:
            return "Untitled"

    @property
    def sheet_names(self) -> List[str]:
        """Get list of sheet names."""
        try:
            sheets = self.uno_document.getSheets()
            return list(sheets.getElementNames())
        except Exception:
            return []

    def has_sheet(self, name: str) -> bool:
        """Check if document has a sheet with given name."""
        try:
            return self.uno_document.getSheets().hasByName(name)
        except Exception:
            return False

    def get_sheet(self, name: str):
        """Get sheet by name."""
        try:
            return self.uno_document.getSheets().getByName(name)
        except Exception:
            return None


class DocumentPool:
    """
    Pool of open LeenO documents.

    Manages document lifecycle and provides lookup by ID.
    """

    _instance: Optional['DocumentPool'] = None

    def __new__(cls, bridge: Optional[UnoBridge] = None) -> 'DocumentPool':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, bridge: Optional[UnoBridge] = None):
        if self._initialized:
            return

        self._bridge = bridge or get_bridge()
        self._documents: Dict[str, DocumentInfo] = {}
        self._path_index: Dict[str, str] = {}  # path -> doc_id
        self._initialized = True

    def _generate_doc_id(self) -> str:
        """Generate unique document ID."""
        return f"doc_{uuid.uuid4().hex[:8]}"

    def _check_is_leeno(self, doc: Any) -> bool:
        """Check if document is a valid LeenO document."""
        try:
            sheets = doc.getSheets()
            # LeenO documents must have S2 and COMPUTO sheets
            return sheets.hasByName("S2") and sheets.hasByName("COMPUTO")
        except Exception:
            return False

    def add(
        self,
        uno_doc: Any,
        path: Optional[str] = None,
        doc_id: Optional[str] = None
    ) -> DocumentInfo:
        """
        Add a document to the pool.

        Args:
            uno_doc: UNO document object
            path: File path (optional)
            doc_id: Document ID (optional, will be generated if not provided)

        Returns:
            DocumentInfo for the added document
        """
        if doc_id is None:
            doc_id = self._generate_doc_id()

        # Normalize path
        if path:
            path = str(Path(path).resolve())

        is_leeno = self._check_is_leeno(uno_doc)

        info = DocumentInfo(
            doc_id=doc_id,
            uno_document=uno_doc,
            path=path,
            is_leeno=is_leeno
        )

        self._documents[doc_id] = info

        if path:
            self._path_index[path] = doc_id

        logger.info(f"Added document to pool: {doc_id} (path={path}, is_leeno={is_leeno})")
        return info

    def get(self, doc_id: str) -> DocumentInfo:
        """
        Get document by ID.

        Args:
            doc_id: Document ID

        Returns:
            DocumentInfo

        Raises:
            DocumentNotFoundError: If document not found
        """
        if doc_id not in self._documents:
            raise DocumentNotFoundError(doc_id)
        return self._documents[doc_id]

    def get_by_path(self, path: str) -> Optional[DocumentInfo]:
        """
        Get document by file path.

        Args:
            path: File path

        Returns:
            DocumentInfo or None if not found
        """
        path = str(Path(path).resolve())
        doc_id = self._path_index.get(path)
        if doc_id:
            return self._documents.get(doc_id)
        return None

    def remove(self, doc_id: str, close: bool = True) -> bool:
        """
        Remove document from pool.

        Args:
            doc_id: Document ID
            close: Also close the document

        Returns:
            True if document was removed
        """
        if doc_id not in self._documents:
            return False

        info = self._documents[doc_id]

        # Remove from path index
        if info.path and info.path in self._path_index:
            del self._path_index[info.path]

        # Close document if requested
        if close:
            try:
                self._bridge.close_document(info.uno_document)
            except Exception as e:
                logger.warning(f"Error closing document {doc_id}: {e}")

        del self._documents[doc_id]
        logger.info(f"Removed document from pool: {doc_id}")
        return True

    def list_all(self) -> List[DocumentInfo]:
        """
        Get list of all open documents.

        Returns:
            List of DocumentInfo
        """
        return list(self._documents.values())

    def list_leeno(self) -> List[DocumentInfo]:
        """
        Get list of all LeenO documents.

        Returns:
            List of DocumentInfo for LeenO documents only
        """
        return [info for info in self._documents.values() if info.is_leeno]

    def count(self) -> int:
        """Get number of open documents."""
        return len(self._documents)

    def clear(self, close: bool = True) -> int:
        """
        Remove all documents from pool.

        Args:
            close: Also close all documents

        Returns:
            Number of documents removed
        """
        count = len(self._documents)
        doc_ids = list(self._documents.keys())
        for doc_id in doc_ids:
            self.remove(doc_id, close=close)
        return count

    def mark_modified(self, doc_id: str) -> None:
        """Mark document as modified."""
        if doc_id in self._documents:
            self._documents[doc_id].modified = True

    def mark_saved(self, doc_id: str, path: Optional[str] = None) -> None:
        """
        Mark document as saved.

        Args:
            doc_id: Document ID
            path: New path if saved to new location
        """
        if doc_id in self._documents:
            info = self._documents[doc_id]
            info.modified = False

            if path:
                # Update path index
                if info.path and info.path in self._path_index:
                    del self._path_index[info.path]

                path = str(Path(path).resolve())
                info.path = path
                self._path_index[path] = doc_id

    def ensure_leeno(self, doc_id: str) -> DocumentInfo:
        """
        Get document and ensure it's a LeenO document.

        Args:
            doc_id: Document ID

        Returns:
            DocumentInfo

        Raises:
            DocumentNotFoundError: If document not found
            InvalidDocumentError: If document is not a LeenO document
        """
        info = self.get(doc_id)
        if not info.is_leeno:
            raise InvalidDocumentError(f"Document '{doc_id}' is not a LeenO document")
        return info


# Global pool instance
_pool: Optional[DocumentPool] = None


def get_pool() -> DocumentPool:
    """Get or create global document pool instance."""
    global _pool
    if _pool is None:
        _pool = DocumentPool()
    return _pool
