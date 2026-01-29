"""
Varianti wrapper for LeenO project variant operations.

Provides functionality to create and manage project variants (VARIANTE sheet).
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .base import LeenoWrapper, parse_currency
from ..connection import get_pool, get_macros
from ..utils.exceptions import OperationError, SheetNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class VarianteInfo:
    """Information about a project variant."""
    exists: bool
    num_voci: int
    totale_importo: float
    differenza_computo: float


class VariantiWrapper(LeenoWrapper):
    """
    Wrapper for VARIANTE sheet operations.

    A VARIANTE is a copy of COMPUTO that tracks project changes/variants.
    """

    SHEET_VARIANTE = "VARIANTE"

    def __init__(self, doc_id: str):
        """
        Initialize varianti wrapper.

        Args:
            doc_id: Document ID
        """
        pool = get_pool()
        doc_info = pool.ensure_leeno(doc_id)
        super().__init__(doc_info)

    def has_variante(self) -> bool:
        """Check if VARIANTE sheet exists."""
        return self.has_sheet(self.SHEET_VARIANTE)

    def crea_variante(self, clear: bool = False) -> VarianteInfo:
        """
        Create a VARIANTE sheet from COMPUTO.

        If VARIANTE already exists, returns its info without changes.

        Args:
            clear: If True, create empty variant; if False, copy from COMPUTO

        Returns:
            VarianteInfo with variant details

        Raises:
            OperationError: If operation fails
        """
        self.ensure_leeno()
        macros = get_macros()

        with self.suspend_refresh():
            try:
                if macros.is_initialized:
                    try:
                        import LeenoVariante
                        LeenoVariante.generaVariante(self._uno_doc, clear)
                        logger.info(f"Variante created (clear={clear})")
                    except ImportError as e:
                        logger.warning(f"LeenoVariante not available: {e}")
                        self._create_variante_manual(clear)
                else:
                    self._create_variante_manual(clear)

                return self.get_variante_info()

            except Exception as e:
                logger.error(f"Error creating variante: {e}")
                raise OperationError("crea_variante", str(e))

    def _create_variante_manual(self, clear: bool) -> Any:
        """Create variante manually without macros."""
        sheets = self._uno_doc.getSheets()

        if sheets.hasByName(self.SHEET_VARIANTE):
            return sheets.getByName(self.SHEET_VARIANTE)

        if not sheets.hasByName(self.SHEET_COMPUTO):
            raise OperationError("crea_variante", "COMPUTO sheet not found")

        # Copy COMPUTO to VARIANTE
        sheets.copyByName(self.SHEET_COMPUTO, self.SHEET_VARIANTE, 4)
        oSheet = sheets.getByName(self.SHEET_VARIANTE)

        # Set variant title and color
        oSheet.getCellByPosition(2, 0).setString("VARIANTE")

        if clear:
            # Clear content except structure
            last_row = self.get_last_row(oSheet)
            if last_row > 10:
                oSheet.getRows().removeByIndex(3, last_row - 6)

        return oSheet

    def get_variante_info(self) -> VarianteInfo:
        """
        Get information about the VARIANTE sheet.

        Returns:
            VarianteInfo with current state
        """
        if not self.has_variante():
            return VarianteInfo(
                exists=False,
                num_voci=0,
                totale_importo=0.0,
                differenza_computo=0.0
            )

        oSheet = self.get_sheet(self.SHEET_VARIANTE)
        num_voci = 0
        totale_importo = 0.0

        # Count voci and calculate total
        last_row = self.get_last_row(oSheet)
        for row in range(3, last_row):
            style = self.get_cell_style(oSheet, 0, row)
            if style in ("Comp Start Attributo", "comp 1-a"):
                num_voci += 1

            # Look for totale
            val = self.get_cell_value(oSheet, 2, row)
            if val and "TOTALI" in str(val).upper():
                totale_importo = parse_currency(self.get_cell_value(oSheet, 13, row))
                break

        # Get COMPUTO total for comparison
        computo_totale = 0.0
        if self.has_sheet(self.SHEET_COMPUTO):
            computo = self.get_sheet(self.SHEET_COMPUTO)
            computo_last = self.get_last_row(computo)
            for row in range(3, computo_last):
                val = self.get_cell_value(computo, 2, row)
                if val and "TOTALI" in str(val).upper():
                    computo_totale = parse_currency(self.get_cell_value(computo, 13, row))
                    break

        return VarianteInfo(
            exists=True,
            num_voci=num_voci,
            totale_importo=totale_importo,
            differenza_computo=totale_importo - computo_totale
        )

    def elimina_variante(self) -> bool:
        """
        Delete the VARIANTE sheet.

        Returns:
            True if deleted, False if didn't exist
        """
        if not self.has_variante():
            return False

        sheets = self._uno_doc.getSheets()
        sheets.removeByName(self.SHEET_VARIANTE)
        logger.info("Variante sheet deleted")
        return True

    def confronta_con_computo(self) -> Dict[str, Any]:
        """
        Compare VARIANTE with COMPUTO.

        Returns:
            Dict with comparison details
        """
        if not self.has_variante():
            raise OperationError("confronta", "VARIANTE sheet not found")

        computo_info = self._get_sheet_summary(self.SHEET_COMPUTO)
        variante_info = self._get_sheet_summary(self.SHEET_VARIANTE)

        return {
            "computo": computo_info,
            "variante": variante_info,
            "differenza_voci": variante_info["num_voci"] - computo_info["num_voci"],
            "differenza_importo": variante_info["totale"] - computo_info["totale"],
            "percentuale_variazione": (
                ((variante_info["totale"] - computo_info["totale"]) / computo_info["totale"] * 100)
                if computo_info["totale"] > 0 else 0
            )
        }

    def _get_sheet_summary(self, sheet_name: str) -> Dict[str, Any]:
        """Get summary info for a sheet."""
        if not self.has_sheet(sheet_name):
            return {"num_voci": 0, "totale": 0.0}

        oSheet = self.get_sheet(sheet_name)
        num_voci = 0
        totale = 0.0

        last_row = self.get_last_row(oSheet)
        for row in range(3, last_row):
            style = self.get_cell_style(oSheet, 0, row)
            if style in ("Comp Start Attributo", "comp 1-a"):
                num_voci += 1

            val = self.get_cell_value(oSheet, 2, row)
            if val and "TOTALI" in str(val).upper():
                totale = parse_currency(self.get_cell_value(oSheet, 13, row))
                break

        return {"num_voci": num_voci, "totale": totale}
