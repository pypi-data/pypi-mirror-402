"""
Document wrapper for LeenO document operations.
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from .base import LeenoWrapper
from ..connection import get_bridge, get_pool, DocumentInfo
from ..models.documento import DocumentoInfo, DocumentoStats
from ..config import get_config

logger = logging.getLogger(__name__)


class DocumentWrapper(LeenoWrapper):
    """
    Wrapper for LeenO document-level operations.

    Handles document creation, opening, saving, and info retrieval.
    """

    @classmethod
    def create(cls, template: str = "computo") -> 'DocumentWrapper':
        """
        Create a new LeenO document from template.

        Args:
            template: Template type ("computo" or "usobollo")

        Returns:
            DocumentWrapper for the new document
        """
        bridge = get_bridge()
        pool = get_pool()
        config = get_config()

        # Determine template path
        if config.leeno.template_path:
            if template == "computo":
                template_file = Path(config.leeno.template_path) / "leeno" / "Computo_LeenO.ots"
            elif template == "usobollo":
                template_file = Path(config.leeno.template_path) / "offmisc" / "UsoBollo.ott"
            else:
                template_file = None

            if template_file and template_file.exists():
                uno_doc = bridge.create_document(str(template_file))
            else:
                logger.warning(f"Template not found: {template_file}, creating blank document")
                uno_doc = bridge.create_document()
        else:
            # No template path configured, create blank
            uno_doc = bridge.create_document()

        # Add to pool
        doc_info = pool.add(uno_doc)

        return cls(doc_info)

    @classmethod
    def open(cls, file_path: str, read_only: bool = False) -> 'DocumentWrapper':
        """
        Open an existing document.

        Args:
            file_path: Path to document file
            read_only: Open in read-only mode

        Returns:
            DocumentWrapper for the opened document
        """
        bridge = get_bridge()
        pool = get_pool()

        # Check if already open
        existing = pool.get_by_path(file_path)
        if existing:
            logger.info(f"Document already open: {file_path}")
            return cls(existing)

        # Open document
        uno_doc = bridge.open_document(file_path, read_only)

        # Add to pool
        doc_info = pool.add(uno_doc, path=file_path)

        return cls(doc_info)

    @classmethod
    def get(cls, doc_id: str) -> 'DocumentWrapper':
        """
        Get wrapper for an existing document by ID.

        Args:
            doc_id: Document ID

        Returns:
            DocumentWrapper
        """
        pool = get_pool()
        doc_info = pool.get(doc_id)
        return cls(doc_info)

    def save(self, path: Optional[str] = None) -> str:
        """
        Save the document.

        Args:
            path: Path to save to (optional)

        Returns:
            Path where document was saved
        """
        bridge = get_bridge()
        pool = get_pool()

        saved_path = bridge.save_document(self._uno_doc, path)
        pool.mark_saved(self.doc_id, saved_path)

        logger.info(f"Document saved: {saved_path}")
        return saved_path

    def close(self) -> bool:
        """
        Close the document.

        Returns:
            True if closed successfully
        """
        pool = get_pool()
        return pool.remove(self.doc_id, close=True)

    def get_info(self) -> DocumentoInfo:
        """
        Get document information.

        Returns:
            DocumentoInfo model
        """
        return DocumentoInfo(
            doc_id=self.doc_id,
            path=self._doc.path,
            title=self._doc.title,
            is_leeno=self._doc.is_leeno,
            modified=self._doc.modified,
            created_at=self._doc.created_at,
            sheets=self.get_sheet_names()
        )

    def get_stats(self) -> DocumentoStats:
        """
        Get document statistics.

        Returns:
            DocumentoStats model with all statistics
        """
        stats = DocumentoStats(doc_id=self.doc_id)

        # Check if LeenO document
        if not self.is_leeno_document():
            return stats

        # Get COMPUTO stats
        if self.has_sheet(self.SHEET_COMPUTO):
            try:
                computo_sheet = self.get_sheet(self.SHEET_COMPUTO)
                stats.num_voci_computo = self._count_voci(computo_sheet)
                totals = self._get_computo_totals(computo_sheet)
                stats.totale_computo = totals.get("importo", 0)
                stats.totale_sicurezza = totals.get("sicurezza", 0)
                stats.totale_manodopera = totals.get("manodopera", 0)
                stats.num_capitoli = self._count_capitoli(computo_sheet)
            except Exception as e:
                logger.warning(f"Error getting COMPUTO stats: {e}")

        # Get Elenco Prezzi stats
        if self.has_sheet(self.SHEET_ELENCO_PREZZI):
            try:
                ep_sheet = self.get_sheet(self.SHEET_ELENCO_PREZZI)
                stats.num_prezzi = self._count_prezzi(ep_sheet)
            except Exception as e:
                logger.warning(f"Error getting Elenco Prezzi stats: {e}")

        # Get CONTABILITA stats
        stats.has_contabilita = self.has_sheet(self.SHEET_CONTABILITA)
        if stats.has_contabilita:
            try:
                contab_sheet = self.get_sheet(self.SHEET_CONTABILITA)
                stats.num_sal = self._count_sal()
                totals = self._get_contab_totals(contab_sheet)
                stats.totale_contabilita = totals.get("importo", 0)
            except Exception as e:
                logger.warning(f"Error getting CONTABILITA stats: {e}")

        # Get VARIANTE stats
        stats.has_variante = self.has_sheet(self.SHEET_VARIANTE)
        if stats.has_variante:
            try:
                var_sheet = self.get_sheet(self.SHEET_VARIANTE)
                totals = self._get_computo_totals(var_sheet)
                stats.totale_variante = totals.get("importo", 0)
            except Exception as e:
                logger.warning(f"Error getting VARIANTE stats: {e}")

        return stats

    def _count_voci(self, sheet: Any) -> int:
        """Count voci in a computo/variante sheet."""
        count = 0
        last_row = self.get_last_row(sheet)
        for row in range(4, last_row + 1):
            style = self.get_cell_style(sheet, 0, row)
            if style == self.STYLE_VOCE_START:
                count += 1
        return count

    def _count_capitoli(self, sheet: Any) -> int:
        """Count chapters in a computo sheet."""
        count = 0
        last_row = self.get_last_row(sheet)
        for row in range(4, last_row + 1):
            style = self.get_cell_style(sheet, 0, row)
            if style in (self.STYLE_CAPITOLO_0, self.STYLE_CAPITOLO_1, self.STYLE_CAPITOLO_2):
                count += 1
        return count

    def _count_prezzi(self, sheet: Any) -> int:
        """Count prices in elenco prezzi."""
        count = 0
        last_row = self.get_last_row(sheet)
        for row in range(4, last_row + 1):
            style = self.get_cell_style(sheet, 0, row)
            if style in self.EP_CODE_STYLES:
                count += 1
        return count

    def _count_sal(self) -> int:
        """Count number of SAL emitted."""
        count = 0
        named_ranges = self._uno_doc.NamedRanges
        for i in range(1, 100):
            if named_ranges.hasByName(f"_Lib_{i}"):
                count += 1
            else:
                break
        return count

    def _get_computo_totals(self, sheet: Any) -> Dict[str, float]:
        """Get totals from computo/variante sheet."""
        # Find totals row (usually has style "Comp TOTALI")
        last_row = self.get_last_row(sheet)
        totals = {"importo": 0, "sicurezza": 0, "manodopera": 0}

        for row in range(last_row, 0, -1):
            style = self.get_cell_style(sheet, 0, row)
            if style == "Comp TOTALI":
                totals["importo"] = self.get_cell_value(sheet, 18, row) or 0
                totals["sicurezza"] = self.get_cell_value(sheet, 17, row) or 0
                totals["manodopera"] = self.get_cell_value(sheet, 30, row) or 0
                break

        return totals

    def _get_contab_totals(self, sheet: Any) -> Dict[str, float]:
        """Get totals from contabilità sheet."""
        last_row = self.get_last_row(sheet)
        totals = {"importo": 0}

        for row in range(last_row, 0, -1):
            style = self.get_cell_style(sheet, 0, row)
            if style == "Comp TOTALI":
                totals["importo"] = self.get_cell_value(sheet, 15, row) or 0
                break

        return totals


def create_document(template: str = "computo") -> DocumentWrapper:
    """Create a new LeenO document."""
    return DocumentWrapper.create(template)


def open_document(file_path: str, read_only: bool = False) -> DocumentWrapper:
    """Open an existing document."""
    return DocumentWrapper.open(file_path, read_only)


def get_document(doc_id: str) -> DocumentWrapper:
    """Get wrapper for existing document."""
    return DocumentWrapper.get(doc_id)
