"""
Computo wrapper for LeenO computo metrico operations.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple

from .base import LeenoWrapper, parse_currency
from ..connection import get_pool, get_macros
from ..models.voce import VoceComputo, RigaMisura, VoceComputoInput, MisuraInput
from ..models.capitolo import Capitolo, CapitoloInput, StrutturaComputo
from ..utils.exceptions import VoceNotFoundError, SheetNotFoundError, OperationError, PrezzoNotFoundError

logger = logging.getLogger(__name__)


class ComputoWrapper(LeenoWrapper):
    """
    Wrapper for COMPUTO/VARIANTE sheet operations.

    Handles voci (items), capitoli (chapters), and measurements.
    """

    def __init__(self, doc_id: str, sheet_name: str = "COMPUTO"):
        """
        Initialize computo wrapper.

        Args:
            doc_id: Document ID
            sheet_name: Sheet name ("COMPUTO" or "VARIANTE")
        """
        pool = get_pool()
        doc_info = pool.ensure_leeno(doc_id)
        super().__init__(doc_info)

        self._sheet_name = sheet_name
        self._sheet = self.get_sheet(sheet_name)

    @property
    def sheet(self) -> Any:
        """Get the computo sheet."""
        return self._sheet

    # ==================== VOCE OPERATIONS ====================

    def get_voce(self, voce_id: str) -> VoceComputo:
        """
        Get a voce by ID.

        Args:
            voce_id: Voce ID (e.g., "V001")

        Returns:
            VoceComputo model

        Raises:
            VoceNotFoundError: If voce not found
        """
        # Find voce by searching for its ID in column 0
        voce_data = self._find_voce_by_id(voce_id)
        if not voce_data:
            raise VoceNotFoundError(voce_id)
        return voce_data

    def get_voce_by_codice(self, codice: str) -> Optional[VoceComputo]:
        """
        Get a voce by article code.

        Args:
            codice: Article code (e.g., "01.A01.001")

        Returns:
            VoceComputo or None if not found
        """
        voci = self.list_voci()
        for voce in voci:
            if voce.codice == codice:
                return voce
        return None

    def list_voci(self, capitolo: Optional[str] = None) -> List[VoceComputo]:
        """
        List all voci in the computo.

        Args:
            capitolo: Optional chapter filter

        Returns:
            List of VoceComputo
        """
        voci = []
        last_row = self.get_last_row(self._sheet)
        current_capitolo = None
        voce_num = 0

        row = 4  # Start after header
        while row <= last_row:
            style = self.get_cell_style(self._sheet, 0, row)

            # Track current chapter
            if style in (self.STYLE_CAPITOLO_0, self.STYLE_CAPITOLO_1, self.STYLE_CAPITOLO_2):
                current_capitolo = self.get_cell_value(self._sheet, 2, row)

            # Found voce start
            elif style == self.STYLE_VOCE_START:
                voce_num += 1
                voce = self._parse_voce_at_row(row, voce_num, current_capitolo)
                if voce:
                    if capitolo is None or voce.capitolo == capitolo:
                        voci.append(voce)
                    # Skip to end of voce
                    row = voce.riga_fine

            row += 1

        return voci

    def add_voce(self, input_data: VoceComputoInput) -> VoceComputo:
        """
        Add a new voce to the computo using LeenO native macro.

        Uses insertVoceComputoGrezza which copies the template from S5 sheet
        and sets up all styles and formulas correctly. VLOOKUP formulas
        automatically retrieve data from Elenco Prezzi based on the codice.

        Args:
            input_data: VoceComputoInput with voce data

        Returns:
            Created VoceComputo

        Raises:
            OperationError: If operation fails
        """
        self.ensure_leeno()
        macros = get_macros()

        if not macros.is_initialized:
            raise OperationError("add_voce", "LeenO macros not initialized - cannot add voce")

        with self.suspend_refresh():
            try:
                # Find insertion point (before totals row)
                insert_row = self._find_insertion_point()

                # Use native LeenO macro to insert voce template from S5
                # This is the ONLY correct way - copies rows 8-11 from S5 with all styles
                macros.insertVoceComputoGrezza(self._sheet, insert_row)

                # Set the codice articolo (column B, row +1)
                # This is the "primary key" - VLOOKUP formulas use this to fetch all other data
                self.set_cell_value(self._sheet, 1, insert_row + 1, input_data.codice)

                # Regenerate formulas in the voce to reference correct rows
                # The template formulas need row numbers updated after copy
                self._regenerate_voce_formulas(insert_row)

                # If quantity is provided, add it as a measurement row
                if input_data.quantita and input_data.quantita > 0:
                    # Set quantity in measurement row (row +2, column J=9)
                    self.set_cell_value(self._sheet, 9, insert_row + 2, input_data.quantita)

                # If user explicitly provided descrizione (override formula), set it
                if input_data.descrizione:
                    self.set_cell_value(self._sheet, 2, insert_row + 1, input_data.descrizione)

                # If user explicitly provided prezzo_unitario (override formula), set it
                if input_data.prezzo_unitario is not None:
                    self.set_cell_value(self._sheet, 11, insert_row + 3, input_data.prezzo_unitario)

                # Renumber voci using native macro if available
                self._numera_voci()

                # Generate voce ID
                voci_count = self._count_voci()
                voce_id = f"V{voci_count:03d}"

                # Parse and return created voce
                voce = self._parse_voce_at_row(insert_row, voci_count, None)
                if voce:
                    voce.voce_id = voce_id
                    return voce

                raise OperationError("add_voce", "Failed to create voce")

            except Exception as e:
                logger.error(f"Error adding voce: {e}")
                raise OperationError("add_voce", str(e))

    def _regenerate_voce_formulas(self, start_row: int) -> None:
        """
        Regenerate VLOOKUP formulas for a voce after template copy.

        Sets up the formulas to correctly reference the codice cell and
        calculate importo, sicurezza, manodopera.

        Args:
            start_row: First row of the voce (Comp Start Attributo row)
        """
        # Row references (1-indexed for formulas)
        article_row = start_row + 2  # Row with codice (0-indexed: start_row + 1)
        end_row = start_row + 4  # Row with totals (0-indexed: start_row + 3)
        measure_row = start_row + 3  # Measurement row (0-indexed: start_row + 2)

        # Column B in article row contains the codice
        codice_cell = f"$B${article_row}"

        # Set VLOOKUP formulas on the END row (totals row, 0-indexed: start_row + 3)

        # Column C (2): Descrizione - concatenated from elenco_prezzi
        desc_formula = f'=CONCATENATE(" ";VLOOKUP({codice_cell};elenco_prezzi;2;FALSE());" ")'
        self.get_cell(self._sheet, 2, start_row + 1).Formula = desc_formula

        # Column I (8): Unità misura with "SOMMANO" prefix
        um_formula = f'=CONCATENATE("SOMMANO [";VLOOKUP({codice_cell};elenco_prezzi;3;FALSE());"]")'
        self.get_cell(self._sheet, 8, start_row + 3).Formula = um_formula

        # Column J (9): Quantità totale - SUM of measurement rows
        qty_formula = f'=SUM(J{measure_row}:J{measure_row})'
        self.get_cell(self._sheet, 9, start_row + 3).Formula = qty_formula

        # Column L (11): Prezzo unitario from elenco_prezzi
        price_formula = f'=VLOOKUP({codice_cell};elenco_prezzi;5;FALSE())'
        self.get_cell(self._sheet, 11, start_row + 3).Formula = price_formula

        # Column S (18): Importo = Quantità * Prezzo (handles % unit)
        importo_formula = (
            f'=IF(VLOOKUP({codice_cell};elenco_prezzi;3;FALSE())="%";'
            f'J{end_row}*L{end_row}/100;J{end_row}*L{end_row})'
        )
        self.get_cell(self._sheet, 18, start_row + 3).Formula = importo_formula

        # Column AB (27): % Sicurezza from elenco_prezzi
        sic_pct_formula = f'=VLOOKUP({codice_cell};elenco_prezzi;4;FALSE())'
        self.get_cell(self._sheet, 27, start_row + 3).Formula = sic_pct_formula

        # Column R (17): Sicurezza = %Sicurezza * Quantità
        sic_formula = f'=AB{end_row}*J{end_row}'
        self.get_cell(self._sheet, 17, start_row + 3).Formula = sic_formula

        # Column AD (29): % Manodopera from elenco_prezzi
        mdo_pct_formula = f'=VLOOKUP({codice_cell};elenco_prezzi;6;FALSE())'
        self.get_cell(self._sheet, 29, start_row + 3).Formula = mdo_pct_formula

        # Column AE (30): Manodopera = %Manodopera * Importo
        mdo_formula = f'=IF(AD{end_row}<>"";PRODUCT(AD{end_row}*S{end_row}))'
        self.get_cell(self._sheet, 30, start_row + 3).Formula = mdo_formula

        # Column AJ (35): Reference to codice
        self.get_cell(self._sheet, 35, start_row + 3).Formula = f'={codice_cell}'

    def _count_voci(self) -> int:
        """Count total voci in computo."""
        count = 0
        last_row = self.get_last_row(self._sheet)

        for row in range(4, last_row + 1):
            style = self.get_cell_style(self._sheet, 0, row)
            if style == self.STYLE_VOCE_START:
                count += 1

        return count

    def delete_voce(self, voce_id: str) -> bool:
        """
        Delete a voce from the computo.

        Args:
            voce_id: Voce ID to delete

        Returns:
            True if deleted successfully

        Raises:
            VoceNotFoundError: If voce not found
        """
        voce = self.get_voce(voce_id)

        with self.suspend_refresh():
            try:
                # Delete rows from start to end
                num_rows = voce.riga_fine - voce.riga_inizio + 1
                self.delete_rows(self._sheet, voce.riga_inizio, num_rows)

                # Renumber remaining voci
                self._numera_voci()

                return True

            except Exception as e:
                logger.error(f"Error deleting voce: {e}")
                raise OperationError("delete_voce", str(e))

    def add_misura(self, voce_id: str, misura: MisuraInput) -> bool:
        """
        Add a measurement row to a voce using LeenO native macro.

        Uses copia_riga_computo which copies the measurement template from S5
        and sets up all styles correctly.

        Args:
            voce_id: Voce ID
            misura: MisuraInput with measurement data

        Returns:
            True if added successfully
        """
        voce = self.get_voce(voce_id)
        macros = get_macros()

        if not macros.is_initialized:
            raise OperationError("add_misura", "LeenO macros not initialized - cannot add misura")

        with self.suspend_refresh():
            try:
                # Find measurement area (between voce start and end)
                insert_row = voce.riga_fine  # Insert before totals row

                # Use native LeenO macro to insert measurement row
                macros.copia_riga_computo(insert_row)

                # Set measurement data
                self.set_cell_value(self._sheet, 2, insert_row, misura.descrizione)
                self.set_cell_value(self._sheet, 4, insert_row, misura.parti_uguali)
                self.set_cell_value(self._sheet, 5, insert_row, misura.lunghezza)
                self.set_cell_value(self._sheet, 6, insert_row, misura.larghezza)
                self.set_cell_value(self._sheet, 7, insert_row, misura.altezza)

                if misura.quantita is not None:
                    self.set_cell_value(self._sheet, 9, insert_row, misura.quantita)

                return True

            except Exception as e:
                logger.error(f"Error adding misura: {e}")
                raise OperationError("add_misura", str(e))

    # ==================== CAPITOLO OPERATIONS ====================

    def add_capitolo(self, input_data: CapitoloInput) -> Capitolo:
        """
        Add a new chapter to the computo.

        Args:
            input_data: CapitoloInput with chapter data

        Returns:
            Created Capitolo
        """
        self.ensure_leeno()

        with self.suspend_refresh():
            try:
                # Find insertion point
                insert_row = self._find_insertion_point()

                # Determine style based on level
                if input_data.livello == 0:
                    style = self.STYLE_CAPITOLO_0
                elif input_data.livello == 1:
                    style = self.STYLE_CAPITOLO_1
                else:
                    style = self.STYLE_CAPITOLO_2

                # Insert row
                self.insert_rows(self._sheet, insert_row, 1)

                # Set chapter name
                cell = self.get_cell(self._sheet, 2, insert_row)
                cell.String = input_data.nome
                cell.CellStyle = style

                # Set style for column 0
                self.get_cell(self._sheet, 0, insert_row).CellStyle = style

                # Generate chapter ID
                capitolo_id = f"CAP_{len(self.list_capitoli()) + 1:03d}"

                return Capitolo(
                    capitolo_id=capitolo_id,
                    nome=input_data.nome,
                    livello=input_data.livello,
                    riga=insert_row
                )

            except Exception as e:
                logger.error(f"Error adding capitolo: {e}")
                raise OperationError("add_capitolo", str(e))

    def list_capitoli(self) -> List[Capitolo]:
        """
        List all chapters in the computo.

        Returns:
            List of Capitolo
        """
        capitoli = []
        last_row = self.get_last_row(self._sheet)
        cap_num = 0

        for row in range(4, last_row + 1):
            style = self.get_cell_style(self._sheet, 0, row)

            if style == self.STYLE_CAPITOLO_0:
                cap_num += 1
                capitoli.append(Capitolo(
                    capitolo_id=f"CAP_{cap_num:03d}",
                    nome=str(self.get_cell_value(self._sheet, 2, row)),
                    livello=0,
                    riga=row
                ))
            elif style == self.STYLE_CAPITOLO_1:
                cap_num += 1
                capitoli.append(Capitolo(
                    capitolo_id=f"CAP_{cap_num:03d}",
                    nome=str(self.get_cell_value(self._sheet, 2, row)),
                    livello=1,
                    riga=row
                ))
            elif style == self.STYLE_CAPITOLO_2:
                cap_num += 1
                capitoli.append(Capitolo(
                    capitolo_id=f"CAP_{cap_num:03d}",
                    nome=str(self.get_cell_value(self._sheet, 2, row)),
                    livello=2,
                    riga=row
                ))

        return capitoli

    # ==================== TOTALS ====================

    def get_totale(self) -> Dict[str, float]:
        """
        Get computo totals.

        Returns:
            Dict with totale, sicurezza, manodopera
        """
        last_row = self.get_last_row(self._sheet)

        for row in range(last_row, 0, -1):
            style = self.get_cell_style(self._sheet, 0, row)
            if style == "Comp TOTALI":
                return {
                    "totale": parse_currency(self.get_cell_value(self._sheet, 18, row)),
                    "sicurezza": parse_currency(self.get_cell_value(self._sheet, 17, row)),
                    "manodopera": parse_currency(self.get_cell_value(self._sheet, 30, row))
                }

        return {"totale": 0, "sicurezza": 0, "manodopera": 0}

    def get_struttura(self) -> StrutturaComputo:
        """
        Get complete computo structure.

        Returns:
            StrutturaComputo with all chapters and totals
        """
        capitoli = self.list_capitoli()
        totals = self.get_totale()
        num_voci = len(self.list_voci())

        return StrutturaComputo(
            capitoli=capitoli,
            totale_importo=totals["totale"],
            totale_sicurezza=totals["sicurezza"],
            totale_manodopera=totals["manodopera"],
            num_voci_totali=num_voci
        )

    # ==================== HELPER METHODS ====================

    def _find_voce_by_id(self, voce_id: str) -> Optional[VoceComputo]:
        """Find voce by ID."""
        # Extract number from ID (e.g., "V001" -> 1)
        try:
            num = int(voce_id.replace("V", ""))
        except ValueError:
            return None

        voci = self.list_voci()
        for voce in voci:
            if voce.numero == num:
                return voce
        return None

    def _parse_voce_at_row(self, row: int, numero: int, capitolo: Optional[str]) -> Optional[VoceComputo]:
        """Parse voce data starting at given row."""
        try:
            # Find voce end
            end_row = row
            last_row = self.get_last_row(self._sheet)
            for r in range(row, min(row + 100, last_row + 1)):
                style = self.get_cell_style(self._sheet, 0, r)
                if style in (self.STYLE_VOCE_END, "Comp End Attributo_R"):
                    end_row = r
                    break

            # Extract data
            codice = str(self.get_cell_value(self._sheet, 1, row + 1) or "")
            descrizione = str(self.get_cell_value(self._sheet, 2, row + 1) or "")
            um_cell = str(self.get_cell_value(self._sheet, 8, end_row) or "")
            unita_misura = um_cell.replace("[", "").replace("]", "")

            quantita = parse_currency(self.get_cell_value(self._sheet, 9, end_row))
            prezzo = parse_currency(self.get_cell_value(self._sheet, 11, end_row))
            importo = parse_currency(self.get_cell_value(self._sheet, 18, end_row))
            sicurezza = parse_currency(self.get_cell_value(self._sheet, 17, end_row))
            manodopera = parse_currency(self.get_cell_value(self._sheet, 30, end_row))

            return VoceComputo(
                voce_id=f"V{numero:03d}",
                numero=numero,
                codice=codice,
                descrizione=descrizione,
                unita_misura=unita_misura,
                quantita=quantita,
                prezzo_unitario=prezzo,
                importo=importo,
                sicurezza=sicurezza,
                manodopera=manodopera,
                riga_inizio=row,
                riga_fine=end_row,
                capitolo=capitolo
            )

        except Exception as e:
            logger.warning(f"Error parsing voce at row {row}: {e}")
            return None

    def _find_insertion_point(self) -> int:
        """Find row where new voci/capitoli should be inserted."""
        last_row = self.get_last_row(self._sheet)

        # Find the totals row and insert before it
        for row in range(last_row, 3, -1):
            style = self.get_cell_style(self._sheet, 0, row)
            if style == "Comp TOTALI":
                return row

        # Default: after header
        return 5

    def _numera_voci(self) -> int:
        """Renumber all voci using native LeenO macro. Returns count."""
        macros = get_macros()

        if not macros.is_initialized:
            raise OperationError("_numera_voci", "LeenO macros not initialized")

        # Use native macro - the ONLY correct way
        return macros.numeraVoci(self._sheet, 0, 1)
