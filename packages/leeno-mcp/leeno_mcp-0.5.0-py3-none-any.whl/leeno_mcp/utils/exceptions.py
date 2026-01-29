"""
Custom exceptions for LeenO MCP Server.
"""

from typing import Optional, Dict, Any


class LeenoMCPError(Exception):
    """Base exception for LeenO MCP Server."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for MCP response."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


class ConnectionError(LeenoMCPError):
    """Error connecting to LibreOffice."""

    def __init__(
        self,
        message: str = "Cannot connect to LibreOffice",
        details: Optional[Dict] = None
    ):
        super().__init__("CONNECTION_ERROR", message, details)


class LibreOfficeNotRunningError(LeenoMCPError):
    """LibreOffice is not running in headless mode."""

    def __init__(
        self,
        message: str = "LibreOffice is not running. Start it with: soffice --headless --accept=\"socket,host=localhost,port=2002;urp;\""
    ):
        super().__init__("LIBREOFFICE_NOT_RUNNING", message)


class DocumentError(LeenoMCPError):
    """Base error for document operations."""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__("DOCUMENT_ERROR", message, details)


class DocumentNotFoundError(LeenoMCPError):
    """Document not found in pool."""

    def __init__(self, doc_id: str):
        self.doc_id = doc_id
        super().__init__(
            "DOCUMENT_NOT_FOUND",
            f"Document '{doc_id}' not found",
            {"doc_id": doc_id}
        )


class InvalidDocumentError(LeenoMCPError):
    """Document is not a valid LeenO document."""

    def __init__(self, message: str = "Document is not a valid LeenO document"):
        super().__init__("INVALID_DOCUMENT", message)


class SheetNotFoundError(LeenoMCPError):
    """Sheet not found in document."""

    def __init__(self, sheet_name: str):
        self.sheet_name = sheet_name
        super().__init__(
            "SHEET_NOT_FOUND",
            f"Sheet '{sheet_name}' not found",
            {"sheet_name": sheet_name}
        )


class ComputoError(LeenoMCPError):
    """Base error for computo operations."""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__("COMPUTO_ERROR", message, details)


class VoceNotFoundError(LeenoMCPError):
    """Voce not found in computo."""

    def __init__(self, voce_id: str):
        self.voce_id = voce_id
        super().__init__(
            "VOCE_NOT_FOUND",
            f"Voce '{voce_id}' not found",
            {"voce_id": voce_id}
        )


class PrezzoNotFoundError(LeenoMCPError):
    """Prezzo not found in elenco prezzi."""

    def __init__(self, codice: str):
        self.codice = codice
        super().__init__(
            "PREZZO_NOT_FOUND",
            f"Prezzo with code '{codice}' not found",
            {"codice": codice}
        )


class ImportError(LeenoMCPError):
    """Error importing prezzario."""

    def __init__(self, message: str, file_path: Optional[str] = None):
        details = {"file_path": file_path} if file_path else {}
        super().__init__("IMPORT_ERROR", message, details)


class ExportError(LeenoMCPError):
    """Error exporting document."""

    def __init__(self, message: str, output_path: Optional[str] = None):
        details = {"output_path": output_path} if output_path else {}
        super().__init__("EXPORT_ERROR", message, details)


class ContabilitaError(LeenoMCPError):
    """Error with contabilità operations."""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__("CONTABILITA_ERROR", message, details)


class OperationError(LeenoMCPError):
    """Generic operation error."""

    def __init__(self, operation: str, message: str):
        super().__init__(
            "OPERATION_ERROR",
            f"Error in {operation}: {message}",
            {"operation": operation}
        )


class ValidationError(LeenoMCPError):
    """Input validation error."""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(
            "VALIDATION_ERROR",
            f"Validation error for '{field}': {message}",
            {"field": field}
        )


class LeenoModuleError(LeenoMCPError):
    """Error loading LeenO modules."""

    def __init__(self, module: str, reason: str):
        self.module = module
        self.reason = reason
        super().__init__(
            "MODULE_ERROR",
            f"Failed to load module {module}: {reason}",
            {"module": module, "reason": reason}
        )
