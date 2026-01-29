"""
LeenO Macros Integration - Provides access to native LeenO macro functions.

This module sets up the environment to use LeenO's native Python macros
from external Python code, enabling faster and more reliable operations.

Usage:
    from leeno_mcp.connection.leeno_macros import LeenoMacros

    macros = LeenoMacros()
    macros.initialize(ctx)  # Pass UNO context

    # Now use native functions
    macros.insertVoceComputoGrezza(oSheet, row)
    macros.copia_riga_computo(row)
"""

import sys
import os
import logging
from typing import Any, Optional, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)


def _find_leeno_pythonpath() -> Optional[str]:
    """
    Auto-detect LeenO pythonpath location.

    Search order:
    1. LEENO_PYTHONPATH environment variable
    2. LEENO_PATH environment variable + /python/pythonpath
    3. LibreOffice user extensions (Windows/Linux/Mac)
    4. Project sibling folder (development)
    5. Common installation paths

    Returns:
        Path to LeenO pythonpath or None if not found
    """
    # 1. Direct environment variable
    if env_path := os.environ.get("LEENO_PYTHONPATH"):
        if os.path.exists(env_path):
            return env_path

    # 2. LEENO_PATH + /python/pythonpath
    if leeno_path := os.environ.get("LEENO_PATH"):
        pythonpath = os.path.join(leeno_path, "python", "pythonpath")
        if os.path.exists(pythonpath):
            return pythonpath

    # 3. LibreOffice user extensions
    appdata_paths = []

    # Windows
    if os.name == 'nt':
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            appdata_paths.append(Path(appdata) / "LibreOffice" / "4" / "user" / "uno_packages" / "cache" / "uno_packages")

    # Linux
    appdata_paths.append(Path.home() / ".config" / "libreoffice" / "4" / "user" / "uno_packages" / "cache" / "uno_packages")

    # macOS
    appdata_paths.append(Path.home() / "Library" / "Application Support" / "LibreOffice" / "4" / "user" / "uno_packages" / "cache" / "uno_packages")

    for appdata_path in appdata_paths:
        if appdata_path.exists():
            for entry in appdata_path.iterdir():
                if entry.is_dir():
                    # Look for LeenO extension
                    for ext_dir in entry.iterdir():
                        if ext_dir.is_dir() and "leeno" in ext_dir.name.lower():
                            pythonpath = ext_dir / "python" / "pythonpath"
                            if pythonpath.exists():
                                return str(pythonpath)

    # 4. Project sibling folder (development setup)
    project_root = Path(__file__).parent.parent.parent.parent.parent  # leeno-mcp-server/../
    dev_paths = [
        project_root / "LeenO" / "python" / "pythonpath",
        project_root.parent / "LeenO" / "python" / "pythonpath",
    ]

    for dev_path in dev_paths:
        if dev_path.exists() and (dev_path / "pyleeno.py").exists():
            return str(dev_path)

    # 5. Common system paths
    system_paths = [
        Path("/usr/share/libreoffice/share/Scripts/python/LeenO/python/pythonpath"),
        Path("/opt/libreoffice/share/Scripts/python/LeenO/python/pythonpath"),
        Path("C:/Program Files/LibreOffice/share/Scripts/python/LeenO/python/pythonpath"),
    ]

    for sys_path in system_paths:
        if sys_path.exists():
            return str(sys_path)

    return None


# Auto-detect LeenO pythonpath
LEENO_PYTHONPATH = _find_leeno_pythonpath()


class LeenoMacros:
    """
    Singleton for accessing LeenO native macro functions.

    Initializes the LeenO environment (pythonpath, global context) and
    provides access to commonly used macro functions for COMPUTO, CONTABILITA,
    and ANALISI operations.
    """

    _instance: Optional['LeenoMacros'] = None
    _initialized: bool = False

    # Lazy-loaded module references
    _LeenoUtils: Any = None
    _LeenoComputo: Any = None
    _LeenoContab: Any = None
    _LeenoAnalysis: Any = None
    _LeenoSheetUtils: Any = None
    _SheetUtils: Any = None
    _pyleeno: Any = None

    def __new__(cls) -> 'LeenoMacros':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if LeenoMacros._initialized:
            return

        self._ctx: Optional[Any] = None
        self._setup_pythonpath()
        LeenoMacros._initialized = True

    def _setup_pythonpath(self) -> None:
        """Add LeenO pythonpath to sys.path if not present."""
        if LEENO_PYTHONPATH is None:
            logger.warning("LeenO pythonpath not found. Set LEENO_PYTHONPATH or LEENO_PATH environment variable.")
            return

        if LEENO_PYTHONPATH not in sys.path:
            sys.path.insert(0, LEENO_PYTHONPATH)
            logger.info(f"Added LeenO pythonpath: {LEENO_PYTHONPATH}")

    def initialize(self, ctx: Any) -> bool:
        """
        Initialize LeenO macros with UNO context.

        Must be called after connecting to LibreOffice.

        Args:
            ctx: UNO component context from UnoBridge

        Returns:
            True if initialization successful
        """
        if self._ctx is not None:
            logger.debug("LeenO macros already initialized")
            return True

        self._ctx = ctx

        try:
            # Import and configure LeenoUtils
            import LeenoUtils
            LeenoUtils.__global_context__ = ctx
            self._LeenoUtils = LeenoUtils
            logger.info("LeenO macros initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize LeenO macros: {e}")
            self._ctx = None
            return False

    @property
    def is_initialized(self) -> bool:
        """Check if macros are initialized."""
        return self._ctx is not None

    def _ensure_initialized(self) -> None:
        """Ensure macros are initialized, raise if not."""
        if not self.is_initialized:
            raise RuntimeError("LeenO macros not initialized. Call initialize(ctx) first.")

    # ==================== MODULE ACCESSORS ====================

    @property
    def LeenoUtils(self) -> Any:
        """Get LeenoUtils module."""
        self._ensure_initialized()
        if self._LeenoUtils is None:
            import LeenoUtils
            self._LeenoUtils = LeenoUtils
        return self._LeenoUtils

    @property
    def LeenoComputo(self) -> Any:
        """Get LeenoComputo module."""
        self._ensure_initialized()
        if self._LeenoComputo is None:
            import LeenoComputo
            self._LeenoComputo = LeenoComputo
        return self._LeenoComputo

    @property
    def LeenoContab(self) -> Any:
        """Get LeenoContab module."""
        self._ensure_initialized()
        if self._LeenoContab is None:
            import LeenoContab
            self._LeenoContab = LeenoContab
        return self._LeenoContab

    @property
    def LeenoAnalysis(self) -> Any:
        """Get LeenoAnalysis module."""
        self._ensure_initialized()
        if self._LeenoAnalysis is None:
            import LeenoAnalysis
            self._LeenoAnalysis = LeenoAnalysis
        return self._LeenoAnalysis

    @property
    def LeenoSheetUtils(self) -> Any:
        """Get LeenoSheetUtils module."""
        self._ensure_initialized()
        if self._LeenoSheetUtils is None:
            import LeenoSheetUtils
            self._LeenoSheetUtils = LeenoSheetUtils
        return self._LeenoSheetUtils

    @property
    def SheetUtils(self) -> Any:
        """Get SheetUtils module."""
        self._ensure_initialized()
        if self._SheetUtils is None:
            import SheetUtils
            self._SheetUtils = SheetUtils
        return self._SheetUtils

    @property
    def pyleeno(self) -> Any:
        """Get pyleeno module."""
        self._ensure_initialized()
        if self._pyleeno is None:
            import pyleeno
            self._pyleeno = pyleeno
        return self._pyleeno

    # ==================== COMPUTO OPERATIONS ====================

    def insertVoceComputoGrezza(self, oSheet: Any, lrow: int) -> None:
        """
        Insert a new voce in COMPUTO using the S5 template.

        Copies the template structure from S5 sheet (rows 8-11) to the
        specified position. This is the correct way to insert new voci,
        ensuring all styles and formulas are properly set.

        Args:
            oSheet: COMPUTO sheet object
            lrow: Row index where to insert (0-based)
        """
        self._ensure_initialized()
        self.LeenoComputo.insertVoceComputoGrezza(oSheet, lrow)

    def circoscriveVoceComputo(self, oSheet: Any, lrow: int) -> Optional[Any]:
        """
        Find the boundaries of a voce at the given row.

        Returns a range encompassing the entire voce from start to end.

        Args:
            oSheet: COMPUTO sheet object
            lrow: Row index within the voce (0-based)

        Returns:
            Cell range of the voce, or None if not found
        """
        self._ensure_initialized()
        return self.LeenoComputo.circoscriveVoceComputo(oSheet, lrow)

    def datiVoceComputo(self, oSheet: Any, lrow: int) -> Optional[Tuple]:
        """
        Get data from a voce at the given row.

        Args:
            oSheet: COMPUTO sheet object
            lrow: Row index within the voce (0-based)

        Returns:
            Tuple with voce data (numero, codice, descrizione, um, qty, prezzo, importo)
            or None if not found
        """
        self._ensure_initialized()
        return self.LeenoComputo.datiVoceComputo(oSheet, lrow)

    def copia_riga_computo(self, lrow: int) -> None:
        """
        Insert a measurement row in COMPUTO at the given position.

        Uses the template from S5 sheet to ensure correct styling.

        Args:
            lrow: Row index where to insert (0-based)
        """
        self._ensure_initialized()
        self.pyleeno.copia_riga_computo(lrow)

    # ==================== CONTABILITA OPERATIONS ====================

    def insertVoceContabilita(self, oSheet: Any, lrow: int) -> None:
        """
        Insert a new voce in CONTABILITA using the template.

        Args:
            oSheet: CONTABILITA sheet object
            lrow: Row index where to insert (0-based)
        """
        self._ensure_initialized()
        self.LeenoContab.insertVoceContabilita(oSheet, lrow)

    def copia_riga_contab(self, lrow: int) -> None:
        """
        Insert a measurement row in CONTABILITA.

        Args:
            lrow: Row index where to insert (0-based)
        """
        self._ensure_initialized()
        self.pyleeno.copia_riga_contab(lrow)

    # ==================== ANALISI OPERATIONS ====================

    def inizializzaAnalisi(self, oDoc: Any) -> Tuple[Any, int]:
        """
        Initialize or create the Analisi di Prezzo sheet and insert new block.

        Args:
            oDoc: Document object

        Returns:
            Tuple (oSheet, startRow) - the Analisi sheet and starting row
        """
        self._ensure_initialized()
        return self.LeenoAnalysis.inizializzaAnalisi(oDoc)

    def copia_riga_analisi(self, lrow: int) -> None:
        """
        Insert a component row in Analisi di Prezzo.

        Args:
            lrow: Row index where to insert (0-based)
        """
        self._ensure_initialized()
        self.pyleeno.copia_riga_analisi(lrow)

    def MENU_analisi_in_ElencoPrezzi(self) -> None:
        """
        Transfer the current Analisi di Prezzo to Elenco Prezzi.

        Makes the analyzed price available for use in COMPUTO.
        """
        self._ensure_initialized()
        self.pyleeno.MENU_analisi_in_ElencoPrezzi()

    # ==================== SHEET UTILITIES ====================

    def numeraVoci(self, oSheet: Any, lrow: int = 0, flag: int = 1) -> int:
        """
        Renumber all voci in the sheet.

        Args:
            oSheet: Sheet object
            lrow: Starting row (0-based)
            flag: Numbering flag

        Returns:
            Count of renumbered voci
        """
        self._ensure_initialized()
        return self.LeenoSheetUtils.numeraVoci(oSheet, lrow, flag)

    def cercaUltimaVoce(self, oSheet: Any) -> int:
        """
        Find the last voce in the sheet.

        Args:
            oSheet: Sheet object

        Returns:
            Row index of the last voce (0-based)
        """
        self._ensure_initialized()
        return self.LeenoSheetUtils.cercaUltimaVoce(oSheet)

    def prossimaVoce(self, oSheet: Any, lrow: int, direzione: int = 1) -> int:
        """
        Find the next or previous voce.

        Args:
            oSheet: Sheet object
            lrow: Current row (0-based)
            direzione: 1 for next, -1 for previous

        Returns:
            Row index of the found voce (0-based)
        """
        self._ensure_initialized()
        return self.LeenoSheetUtils.prossimaVoce(oSheet, lrow, direzione)

    # ==================== DOCUMENT UTILITIES ====================

    def getDocument(self) -> Optional[Any]:
        """
        Get the current document.

        Returns:
            Document object or None
        """
        self._ensure_initialized()
        return self.LeenoUtils.getDocument()

    def isLeenoDocument(self) -> bool:
        """
        Check if the current document is a LeenO document.

        Returns:
            True if LeenO document
        """
        self._ensure_initialized()
        return self.LeenoUtils.isLeenoDocument()


# Global macros instance
_macros: Optional[LeenoMacros] = None


def get_macros() -> LeenoMacros:
    """Get or create global LeenO macros instance."""
    global _macros
    if _macros is None:
        _macros = LeenoMacros()
    return _macros
