"""
Import Prezzi wrapper for LeenO price list import operations.

Provides functionality to import price lists from various regional XML formats.
"""

import logging
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .base import LeenoWrapper
from ..connection import get_pool, get_macros
from ..utils.exceptions import OperationError, ValidationError

logger = logging.getLogger(__name__)


# Supported import formats with descriptions
IMPORT_FORMATS = {
    "six": "SIX format (standard XML)",
    "toscana": "Regione Toscana",
    "calabria": "Regione Calabria (uses Toscana parser)",
    "campania": "Regione Campania (uses Toscana parser)",
    "sardegna": "Regione Sardegna",
    "liguria": "Regione Liguria",
    "veneto": "Regione Veneto",
    "basilicata": "Regione Basilicata",
    "lombardia": "Regione Lombardia",
    "xpwe": "XPWE format (LeenO native)",
    "auto": "Auto-detect format from file content",
}


@dataclass
class ImportResult:
    """Result of a price import operation."""
    success: bool
    format_detected: str
    num_articoli: int
    num_capitoli: int
    errors: List[str]
    warnings: List[str]


class ImportPrezziWrapper(LeenoWrapper):
    """
    Wrapper for importing price lists into LeenO documents.

    Supports various regional XML formats used in Italy.
    """

    def __init__(self, doc_id: str):
        """
        Initialize import wrapper.

        Args:
            doc_id: Document ID
        """
        pool = get_pool()
        doc_info = pool.ensure_leeno(doc_id)
        super().__init__(doc_info)

    def get_supported_formats(self) -> Dict[str, str]:
        """Get list of supported import formats."""
        return IMPORT_FORMATS.copy()

    def detect_format(self, file_path: str) -> Optional[str]:
        """
        Detect the format of an XML price list file.

        Args:
            file_path: Path to the XML file

        Returns:
            Detected format name or None if unknown
        """
        if not os.path.exists(file_path):
            raise ValidationError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(10000)  # Read first 10KB for detection
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read(10000)

        # Pattern matching for format detection
        patterns = {
            'xmlns="six.xsd"': "six",
            'autore="Regione Toscana"': "toscana",
            'autore="Regione Calabria"': "calabria",
            'autore="Regione Campania"': "campania",
            'autore="Regione Sardegna"': "sardegna",
            'autore="Regione Liguria"': "liguria",
            'rks=': "veneto",
            '<pdf>Prezzario_Regione_Basilicata': "basilicata",
            '<autore>Regione Lombardia': "lombardia",
            '<autore>LOM': "lombardia",
        }

        for pattern, format_name in patterns.items():
            if pattern in content:
                return format_name

        # Check for XPWE
        if '<XPWE' in content or '<xpwe' in content:
            return "xpwe"

        return None

    def import_prezzi(
        self,
        file_path: str,
        formato: str = "auto",
        sovrascrivi: bool = False
    ) -> ImportResult:
        """
        Import a price list from file.

        Args:
            file_path: Path to the price list file (XML, XPWE)
            formato: Format type or "auto" for auto-detection
            sovrascrivi: Whether to overwrite existing prices

        Returns:
            ImportResult with operation details

        Raises:
            ValidationError: If file not found or invalid format
            OperationError: If import fails
        """
        self.ensure_leeno()

        if not os.path.exists(file_path):
            raise ValidationError(f"File not found: {file_path}")

        # Detect format if auto
        if formato == "auto":
            detected = self.detect_format(file_path)
            if detected is None:
                raise ValidationError(
                    "Could not detect file format. Please specify format explicitly."
                )
            formato = detected

        if formato not in IMPORT_FORMATS and formato != "auto":
            raise ValidationError(
                f"Unsupported format: {formato}. "
                f"Supported: {', '.join(IMPORT_FORMATS.keys())}"
            )

        macros = get_macros()
        errors = []
        warnings = []
        num_articoli = 0
        num_capitoli = 0

        with self.suspend_refresh():
            try:
                # Read file content
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        xml_content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        xml_content = f.read()

                # Get appropriate parser from LeenO
                if macros.is_initialized:
                    try:
                        import LeenoImport
                        parser = LeenoImport.findXmlParser(xml_content)

                        if parser is None:
                            raise OperationError(
                                "import_prezzi",
                                "No suitable parser found for this file format"
                            )

                        # Parse the XML
                        dati = parser(xml_content)

                        if dati and 'articoli' in dati:
                            num_articoli = len(dati.get('articoli', []))
                            num_capitoli = len(dati.get('capitoli', []))

                            # Compile into Elenco Prezzi
                            LeenoImport.compilaElencoPrezzi(
                                self._uno_doc,
                                dati,
                                progress=None
                            )

                    except ImportError as e:
                        logger.error(f"LeenoImport not available: {e}")
                        raise OperationError("import_prezzi", f"LeenoImport module not available: {e}")

                else:
                    raise OperationError(
                        "import_prezzi",
                        "LeenO macros not initialized. Cannot import without native macros."
                    )

                return ImportResult(
                    success=True,
                    format_detected=formato,
                    num_articoli=num_articoli,
                    num_capitoli=num_capitoli,
                    errors=errors,
                    warnings=warnings
                )

            except OperationError:
                raise
            except Exception as e:
                logger.error(f"Error importing prezzi: {e}")
                raise OperationError("import_prezzi", str(e))

    def import_from_url(self, url: str, formato: str = "auto") -> ImportResult:
        """
        Import a price list from URL.

        Args:
            url: URL to the price list file
            formato: Format type or "auto"

        Returns:
            ImportResult with operation details
        """
        # Download to temp file first
        import tempfile
        import urllib.request

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp:
                urllib.request.urlretrieve(url, tmp.name)
                result = self.import_prezzi(tmp.name, formato)
                os.unlink(tmp.name)
                return result
        except Exception as e:
            raise OperationError("import_from_url", str(e))
