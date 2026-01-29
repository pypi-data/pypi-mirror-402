"""
Contabilità wrapper for work accounting operations.
"""

import logging
from typing import Optional, List, Any
from datetime import date

from .base import LeenoWrapper
from ..connection import get_pool, get_macros
from ..models.contabilita import VoceContabilita, VoceContabilitaInput, SALInfo, StatoContabilita
from ..utils.exceptions import VoceNotFoundError, OperationError, ContabilitaError

logger = logging.getLogger(__name__)


class ContabilitaWrapper(LeenoWrapper):
    """
    Wrapper for CONTABILITA sheet operations.

    Handles work accounting entries and SAL management.
    """

    def __init__(self, doc_id: str):
        """
        Initialize contabilità wrapper.

        Args:
            doc_id: Document ID
        """
        pool = get_pool()
        doc_info = pool.ensure_leeno(doc_id)
        super().__init__(doc_info)

        if not self.has_sheet(self.SHEET_CONTABILITA):
            raise ContabilitaError("Document does not have CONTABILITA sheet")

        self._sheet = self.get_sheet(self.SHEET_CONTABILITA)

    @property
    def sheet(self) -> Any:
        """Get the contabilità sheet."""
        return self._sheet

    def add_voce(self, input_data: VoceContabilitaInput) -> VoceContabilita:
        """
        Add a new entry to contabilità using LeenO native macro.

        Uses insertVoceContabilita which copies the template from S5 sheet
        and sets up all styles correctly.

        Args:
            input_data: VoceContabilitaInput with entry data

        Returns:
            Created VoceContabilita
        """
        self.ensure_leeno()
        macros = get_macros()

        if not macros.is_initialized:
            raise OperationError("add_voce", "LeenO macros not initialized - cannot add voce")

        with self.suspend_refresh():
            try:
                # Find insertion point
                insert_row = self._find_insertion_point()

                # Use native LeenO macro to insert voce template
                # This is the ONLY correct way
                macros.insertVoceContabilita(self._sheet, insert_row)

                # Set entry data
                self.set_cell_value(self._sheet, 1, insert_row + 1, input_data.codice)

                # Set date (convert to LibreOffice serial date)
                serial_date = input_data.data.toordinal() - 693594  # Days since 1899-12-30
                self.set_cell_value(self._sheet, 1, insert_row + 2, serial_date)

                # Set quantity
                if input_data.quantita >= 0:
                    self.set_cell_value(self._sheet, 9, insert_row + 4, input_data.quantita)
                else:
                    self.set_cell_value(self._sheet, 9, insert_row + 4, input_data.quantita)

                # Generate voce ID
                voce_id = f"VC{len(self.list_voci()):03d}"

                # Renumber voci
                self._numera_voci()

                # Parse and return created voce
                return self._parse_voce_at_row(insert_row, voce_id)

            except Exception as e:
                logger.error(f"Error adding contabilità voce: {e}")
                raise OperationError("add_voce", str(e))

    def list_voci(self, sal: Optional[int] = None) -> List[VoceContabilita]:
        """
        List all entries in contabilità.

        Args:
            sal: Optional SAL number filter

        Returns:
            List of VoceContabilita
        """
        voci = []
        last_row = self.get_last_row(self._sheet)
        voce_num = 0

        row = 4
        while row <= last_row:
            style = self.get_cell_style(self._sheet, 0, row)

            if style in (self.STYLE_VOCE_START, "Comp Start Attributo_R"):
                voce_num += 1
                voce = self._parse_voce_at_row(row, f"VC{voce_num:03d}")

                if voce:
                    if sal is None or voce.num_sal == sal:
                        voci.append(voce)
                    row = voce.riga_fine

            row += 1

        return voci

    def get_sal_info(self, numero: Optional[int] = None) -> SALInfo:
        """
        Get SAL information.

        Args:
            numero: SAL number (None for latest)

        Returns:
            SALInfo
        """
        if numero is None:
            numero = self._get_ultimo_sal()

        if numero == 0:
            return SALInfo(
                numero=0,
                importo_lavori=0,
                importo_sicurezza=0,
                registrato=False
            )

        # Get SAL range
        named_range_name = f"_Lib_{numero}"
        if not self._uno_doc.NamedRanges.hasByName(named_range_name):
            return SALInfo(numero=numero, registrato=False)

        named_range = self._uno_doc.NamedRanges.getByName(named_range_name)
        range_addr = named_range.ReferredCells.RangeAddress

        # Calculate totals for this SAL
        importo = 0
        sicurezza = 0
        num_voci = 0

        for row in range(range_addr.StartRow, range_addr.EndRow + 1):
            style = self.get_cell_style(self._sheet, 0, row)
            if style in ("Comp End Attributo", "Comp End Attributo_R"):
                importo += float(self.get_cell_value(self._sheet, 15, row) or 0)
                sicurezza += float(self.get_cell_value(self._sheet, 17, row) or 0)
                num_voci += 1

        return SALInfo(
            numero=numero,
            importo_lavori=importo,
            importo_sicurezza=sicurezza,
            num_voci=num_voci,
            registrato=True
        )

    def get_stato(self) -> StatoContabilita:
        """
        Get overall contabilità status.

        Returns:
            StatoContabilita
        """
        # Get all voci
        voci = self.list_voci()

        # Calculate totals
        totale_lavori = sum(v.importo for v in voci)
        totale_sicurezza = sum(v.sicurezza for v in voci)
        totale_manodopera = sum(v.manodopera for v in voci)

        # Get SAL info
        num_sal = self._get_ultimo_sal()
        sal_list = []
        importo_registrato = 0

        for i in range(1, num_sal + 1):
            sal_info = self.get_sal_info(i)
            sal_list.append(sal_info)
            if sal_info.registrato:
                importo_registrato += sal_info.importo_lavori

        # Count registered voci
        num_voci_registrate = sum(1 for v in voci if v.registrato)

        return StatoContabilita(
            totale_lavori=totale_lavori,
            totale_sicurezza=totale_sicurezza,
            totale_manodopera=totale_manodopera,
            num_sal_emessi=num_sal,
            ultimo_sal=num_sal if num_sal > 0 else None,
            importo_registrato=importo_registrato,
            importo_da_registrare=totale_lavori - importo_registrato,
            num_voci_totali=len(voci),
            num_voci_registrate=num_voci_registrate,
            sal_list=sal_list
        )

    def emetti_sal(self) -> SALInfo:
        """
        Emit a new SAL.

        Returns:
            SALInfo for the new SAL
        """
        # This is a complex operation that requires careful handling
        # For now, raise not implemented
        raise OperationError("emetti_sal", "Operation not yet implemented via MCP")

    def annulla_sal(self, numero: int) -> bool:
        """
        Cancel a SAL.

        Args:
            numero: SAL number to cancel

        Returns:
            True if cancelled
        """
        # This is a complex operation
        raise OperationError("annulla_sal", "Operation not yet implemented via MCP")

    # ==================== HELPER METHODS ====================

    def _get_ultimo_sal(self) -> int:
        """Get the latest SAL number."""
        for i in range(1, 100):
            if not self._uno_doc.NamedRanges.hasByName(f"_Lib_{i}"):
                return i - 1
        return 0

    def _find_insertion_point(self) -> int:
        """Find row for new entry insertion."""
        last_row = self.get_last_row(self._sheet)

        for row in range(last_row, 3, -1):
            style = self.get_cell_style(self._sheet, 0, row)
            if style == "Comp TOTALI":
                return row

        return 5

    def _parse_voce_at_row(self, row: int, voce_id: str) -> Optional[VoceContabilita]:
        """Parse contabilità entry at given row."""
        try:
            # Find entry end
            end_row = row
            last_row = self.get_last_row(self._sheet)
            for r in range(row, min(row + 20, last_row + 1)):
                style = self.get_cell_style(self._sheet, 0, r)
                if style in ("Comp End Attributo", "Comp End Attributo_R"):
                    end_row = r
                    break

            # Extract data
            numero = int(self.get_cell_value(self._sheet, 0, row + 1) or 0)
            codice = str(self.get_cell_value(self._sheet, 1, row + 1) or "")
            descrizione = str(self.get_cell_value(self._sheet, 2, row + 1) or "")

            # Date is stored as serial number
            date_value = self.get_cell_value(self._sheet, 1, row + 2)
            if date_value:
                try:
                    serial = int(date_value)
                    entry_date = date.fromordinal(serial + 693594)
                except (ValueError, TypeError):
                    entry_date = date.today()
            else:
                entry_date = date.today()

            um = str(self.get_cell_value(self._sheet, 9, row + 1) or "")
            quantita = float(self.get_cell_value(self._sheet, 9, end_row) or 0)
            prezzo = float(self.get_cell_value(self._sheet, 13, end_row) or 0)
            importo = float(self.get_cell_value(self._sheet, 15, end_row) or 0)
            sicurezza = float(self.get_cell_value(self._sheet, 17, end_row) or 0)
            manodopera = float(self.get_cell_value(self._sheet, 30, end_row) or 0)

            # SAL number
            num_sal = int(self.get_cell_value(self._sheet, 23, row + 1) or 0)

            # Check if registered
            flag = str(self.get_cell_value(self._sheet, 22, row + 1) or "")
            registrato = flag == "#reg"

            return VoceContabilita(
                voce_id=voce_id,
                numero=numero,
                codice=codice,
                descrizione=descrizione,
                data=entry_date,
                unita_misura=um,
                quantita_positiva=quantita if quantita > 0 else 0,
                quantita_negativa=abs(quantita) if quantita < 0 else 0,
                prezzo_unitario=prezzo,
                importo=importo,
                sicurezza=sicurezza,
                manodopera=manodopera,
                num_sal=num_sal,
                registrato=registrato,
                riga_inizio=row,
                riga_fine=end_row
            )

        except Exception as e:
            logger.warning(f"Error parsing contabilità voce at row {row}: {e}")
            return None

    def _numera_voci(self) -> int:
        """Renumber all entries using native LeenO macro. Returns count."""
        macros = get_macros()

        if not macros.is_initialized:
            raise OperationError("_numera_voci", "LeenO macros not initialized")

        # Use native macro - the ONLY correct way
        return macros.numeraVoci(self._sheet, 0, 1)
