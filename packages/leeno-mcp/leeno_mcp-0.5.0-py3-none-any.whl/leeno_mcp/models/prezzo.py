"""
Models for Elenco Prezzi (price list).
"""

from typing import Optional
from pydantic import BaseModel, Field


class Prezzo(BaseModel):
    """A price entry in the Elenco Prezzi."""

    codice: str = Field(..., description="Unique price code (e.g., '01.A01.001')")
    descrizione: str = Field(default="", description="Short description")
    descrizione_estesa: str = Field(default="", description="Extended description")
    unita_misura: str = Field(default="", description="Unit of measurement")
    prezzo_unitario: float = Field(default=0, description="Unit price", ge=0)
    sicurezza: float = Field(default=0, description="Safety percentage (0-100)", ge=0)
    manodopera: float = Field(default=0, description="Labor percentage (0-100)", ge=0)
    categoria: Optional[str] = Field(default=None, description="Category/Chapter")
    riga: int = Field(default=0, description="Row number in spreadsheet", ge=0)

    @property
    def importo_sicurezza(self) -> float:
        """Calculate safety amount for 1 unit."""
        return self.prezzo_unitario * (self.sicurezza / 100)

    @property
    def importo_manodopera(self) -> float:
        """Calculate labor amount for 1 unit."""
        return self.prezzo_unitario * (self.manodopera / 100)

    class Config:
        json_schema_extra = {
            "example": {
                "codice": "01.A01.001",
                "descrizione": "Scavo a sezione aperta",
                "descrizione_estesa": "Scavo a sezione aperta in terreno di qualsiasi natura e consistenza...",
                "unita_misura": "mc",
                "prezzo_unitario": 12.50,
                "sicurezza": 3.0,
                "manodopera": 30.0,
                "categoria": "01 - SCAVI E DEMOLIZIONI",
                "riga": 45
            }
        }


class PrezzoInput(BaseModel):
    """Input model for creating/updating a price entry."""

    codice: str = Field(..., description="Unique price code")
    descrizione: str = Field(..., description="Short description")
    descrizione_estesa: Optional[str] = Field(default="", description="Extended description")
    unita_misura: str = Field(..., description="Unit of measurement")
    prezzo_unitario: float = Field(..., description="Unit price", ge=0)
    sicurezza: float = Field(default=0, description="Safety percentage", ge=0, le=100)
    manodopera: float = Field(default=0, description="Labor percentage", ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "codice": "NP.001",
                "descrizione": "Nuova lavorazione personalizzata",
                "descrizione_estesa": "Descrizione completa della lavorazione...",
                "unita_misura": "mq",
                "prezzo_unitario": 25.00,
                "sicurezza": 3.0,
                "manodopera": 40.0
            }
        }


class PrezzoSearchResult(BaseModel):
    """Result of a price search."""

    codice: str
    descrizione: str
    unita_misura: str
    prezzo_unitario: float
    riga: int

    class Config:
        json_schema_extra = {
            "example": {
                "codice": "01.A01.001",
                "descrizione": "Scavo a sezione aperta",
                "unita_misura": "mc",
                "prezzo_unitario": 12.50,
                "riga": 45
            }
        }
