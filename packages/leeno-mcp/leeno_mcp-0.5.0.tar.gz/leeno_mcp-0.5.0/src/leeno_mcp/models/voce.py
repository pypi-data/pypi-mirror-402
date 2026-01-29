"""
Models for Computo Metrico voci (items).
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class RigaMisura(BaseModel):
    """A single measurement row within a voce."""

    descrizione: str = Field(default="", description="Description of the measurement")
    parti_uguali: float = Field(default=0, description="Number of equal parts", ge=0)
    lunghezza: float = Field(default=0, description="Length (L)", ge=0)
    larghezza: float = Field(default=0, description="Width (l)", ge=0)
    altezza: float = Field(default=0, description="Height/Depth (H/P)", ge=0)
    quantita: float = Field(default=0, description="Calculated or forced quantity")
    riga: int = Field(default=0, description="Row number in spreadsheet", ge=0)

    @property
    def quantita_calcolata(self) -> float:
        """Calculate quantity from dimensions."""
        if self.quantita != 0:
            return self.quantita

        result = self.parti_uguali if self.parti_uguali > 0 else 1

        if self.lunghezza > 0:
            result *= self.lunghezza
        if self.larghezza > 0:
            result *= self.larghezza
        if self.altezza > 0:
            result *= self.altezza

        return result

    class Config:
        json_schema_extra = {
            "example": {
                "descrizione": "Muro perimetrale piano terra",
                "parti_uguali": 1,
                "lunghezza": 12.50,
                "larghezza": 0.30,
                "altezza": 3.00,
                "quantita": 0,
                "riga": 15
            }
        }


class VoceComputo(BaseModel):
    """A voce (item) in the Computo Metrico."""

    voce_id: str = Field(..., description="Internal ID (e.g., 'V001')")
    numero: int = Field(default=0, description="Progressive number", ge=0)
    codice: str = Field(..., description="Article code (e.g., '01.A01.001')")
    descrizione: str = Field(default="", description="Work description")
    unita_misura: str = Field(default="", description="Unit of measurement")
    quantita: float = Field(default=0, description="Total quantity")
    prezzo_unitario: float = Field(default=0, description="Unit price", ge=0)
    importo: float = Field(default=0, description="Total amount (quantity * price)")
    sicurezza: float = Field(default=0, description="Safety amount", ge=0)
    manodopera: float = Field(default=0, description="Labor cost incidence", ge=0)
    riga_inizio: int = Field(default=0, description="Start row in spreadsheet", ge=0)
    riga_fine: int = Field(default=0, description="End row in spreadsheet", ge=0)
    capitolo: Optional[str] = Field(default=None, description="Parent chapter")
    misure: List[RigaMisura] = Field(default_factory=list, description="Measurement rows")

    @property
    def importo_calcolato(self) -> float:
        """Calculate total amount."""
        return self.quantita * self.prezzo_unitario

    @property
    def quantita_totale(self) -> float:
        """Sum of all measurement quantities."""
        if self.misure:
            return sum(m.quantita_calcolata for m in self.misure)
        return self.quantita

    class Config:
        json_schema_extra = {
            "example": {
                "voce_id": "V001",
                "numero": 1,
                "codice": "01.A01.001",
                "descrizione": "Scavo a sezione aperta in terreno di qualsiasi natura",
                "unita_misura": "mc",
                "quantita": 125.50,
                "prezzo_unitario": 12.50,
                "importo": 1568.75,
                "sicurezza": 47.06,
                "manodopera": 470.63,
                "riga_inizio": 10,
                "riga_fine": 18,
                "capitolo": "CAP_001",
                "misure": []
            }
        }


class VoceComputoInput(BaseModel):
    """Input model for creating/updating a voce."""

    codice: str = Field(..., description="Article code")
    descrizione: Optional[str] = Field(default=None, description="Work description")
    unita_misura: Optional[str] = Field(default=None, description="Unit of measurement")
    quantita: Optional[float] = Field(default=None, description="Quantity", ge=0)
    prezzo_unitario: Optional[float] = Field(default=None, description="Unit price", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "codice": "01.A01.001",
                "quantita": 125.50
            }
        }


class MisuraInput(BaseModel):
    """Input model for adding a measurement row."""

    descrizione: str = Field(default="", description="Description")
    parti_uguali: float = Field(default=1, description="Number of equal parts", ge=0)
    lunghezza: float = Field(default=0, description="Length", ge=0)
    larghezza: float = Field(default=0, description="Width", ge=0)
    altezza: float = Field(default=0, description="Height/Depth", ge=0)
    quantita: Optional[float] = Field(default=None, description="Forced quantity")

    class Config:
        json_schema_extra = {
            "example": {
                "descrizione": "Muro esterno lato nord",
                "parti_uguali": 1,
                "lunghezza": 10.00,
                "larghezza": 0.30,
                "altezza": 3.00
            }
        }
