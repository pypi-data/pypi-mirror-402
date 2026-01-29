"""
Models for LeenO documents.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentoInfo(BaseModel):
    """Information about a LeenO document."""

    doc_id: str = Field(..., description="Document ID")
    path: Optional[str] = Field(default=None, description="File path")
    title: str = Field(default="Untitled", description="Document title")
    is_leeno: bool = Field(default=False, description="Is a valid LeenO document")
    modified: bool = Field(default=False, description="Has unsaved changes")
    created_at: datetime = Field(default_factory=datetime.now, description="When document was opened")
    sheets: List[str] = Field(default_factory=list, description="List of sheet names")

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_a1b2c3d4",
                "path": "/home/user/documents/computo_progetto.ods",
                "title": "computo_progetto.ods",
                "is_leeno": True,
                "modified": False,
                "created_at": "2024-01-20T10:30:00",
                "sheets": ["M1", "S1", "S2", "S5", "Elenco Prezzi", "COMPUTO", "CONTABILITA"]
            }
        }


class DocumentoStats(BaseModel):
    """Statistics for a LeenO document."""

    doc_id: str = Field(..., description="Document ID")

    # Computo stats
    num_voci_computo: int = Field(default=0, description="Number of voci in COMPUTO")
    totale_computo: float = Field(default=0, description="Total computo amount")
    totale_sicurezza: float = Field(default=0, description="Total safety amount")
    totale_manodopera: float = Field(default=0, description="Total labor amount")
    num_capitoli: int = Field(default=0, description="Number of chapters")

    # Elenco Prezzi stats
    num_prezzi: int = Field(default=0, description="Number of prices in elenco")

    # Contabilità stats
    has_contabilita: bool = Field(default=False, description="Has CONTABILITA sheet")
    num_sal: int = Field(default=0, description="Number of SAL emitted")
    totale_contabilita: float = Field(default=0, description="Total contabilità amount")

    # Variante stats
    has_variante: bool = Field(default=False, description="Has VARIANTE sheet")
    totale_variante: float = Field(default=0, description="Total variante amount")

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_a1b2c3d4",
                "num_voci_computo": 45,
                "totale_computo": 125000.50,
                "totale_sicurezza": 3750.00,
                "totale_manodopera": 37500.15,
                "num_capitoli": 8,
                "num_prezzi": 1523,
                "has_contabilita": True,
                "num_sal": 3,
                "totale_contabilita": 85000.00,
                "has_variante": False,
                "totale_variante": 0
            }
        }


class DocumentoCreateResult(BaseModel):
    """Result of document creation."""

    doc_id: str = Field(..., description="Created document ID")
    path: Optional[str] = Field(default=None, description="File path (if saved)")
    is_leeno: bool = Field(default=True, description="Is a LeenO document")

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_a1b2c3d4",
                "path": None,
                "is_leeno": True
            }
        }


class DocumentoOpenResult(BaseModel):
    """Result of opening a document."""

    doc_id: str = Field(..., description="Document ID")
    path: str = Field(..., description="File path")
    is_leeno: bool = Field(..., description="Is a valid LeenO document")
    info: DocumentoInfo = Field(..., description="Document information")

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_a1b2c3d4",
                "path": "/home/user/documents/computo.ods",
                "is_leeno": True,
                "info": {
                    "doc_id": "doc_a1b2c3d4",
                    "path": "/home/user/documents/computo.ods",
                    "title": "computo.ods",
                    "is_leeno": True,
                    "modified": False,
                    "sheets": ["M1", "S1", "S2", "S5", "Elenco Prezzi", "COMPUTO"]
                }
            }
        }


class DocumentoSaveResult(BaseModel):
    """Result of saving a document."""

    success: bool = Field(..., description="Save was successful")
    path: str = Field(..., description="Path where document was saved")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "path": "/home/user/documents/computo_progetto.ods"
            }
        }
