"""
Models for Contabilità Lavori (work accounting).
"""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class VoceContabilita(BaseModel):
    """A voce in the Contabilità sheet."""

    voce_id: str = Field(..., description="Internal voce ID")
    numero: int = Field(default=0, description="Progressive number")
    codice: str = Field(..., description="Article code")
    descrizione: str = Field(default="", description="Work description")
    data: date = Field(..., description="Date of the entry")
    unita_misura: str = Field(default="", description="Unit of measurement")
    quantita_positiva: float = Field(default=0, description="Positive quantity (work done)")
    quantita_negativa: float = Field(default=0, description="Negative quantity (deductions)")
    prezzo_unitario: float = Field(default=0, description="Unit price")
    importo: float = Field(default=0, description="Total amount")
    sicurezza: float = Field(default=0, description="Safety amount")
    manodopera: float = Field(default=0, description="Labor amount")
    num_sal: int = Field(default=0, description="SAL number this entry belongs to")
    registrato: bool = Field(default=False, description="Entry is registered in SAL")
    riga_inizio: int = Field(default=0, description="Start row in spreadsheet")
    riga_fine: int = Field(default=0, description="End row in spreadsheet")

    @property
    def quantita_netta(self) -> float:
        """Net quantity (positive - negative)."""
        return self.quantita_positiva - abs(self.quantita_negativa)

    class Config:
        json_schema_extra = {
            "example": {
                "voce_id": "VC001",
                "numero": 1,
                "codice": "01.A01.001",
                "descrizione": "Scavo a sezione aperta",
                "data": "2024-01-15",
                "unita_misura": "mc",
                "quantita_positiva": 50.00,
                "quantita_negativa": 0,
                "prezzo_unitario": 12.50,
                "importo": 625.00,
                "sicurezza": 18.75,
                "manodopera": 187.50,
                "num_sal": 1,
                "registrato": True,
                "riga_inizio": 10,
                "riga_fine": 15
            }
        }


class VoceContabilitaInput(BaseModel):
    """Input model for adding a contabilità entry."""

    codice: str = Field(..., description="Article code from Elenco Prezzi")
    data: date = Field(..., description="Date of the entry")
    quantita: float = Field(..., description="Quantity (positive for work done, negative for deductions)")
    descrizione: Optional[str] = Field(default=None, description="Optional description override")

    class Config:
        json_schema_extra = {
            "example": {
                "codice": "01.A01.001",
                "data": "2024-01-15",
                "quantita": 50.00
            }
        }


class SALInfo(BaseModel):
    """Information about a SAL (Stato Avanzamento Lavori)."""

    numero: int = Field(..., description="SAL number", ge=1)
    data_emissione: Optional[date] = Field(default=None, description="Issue date")

    # Amounts
    importo_lavori: float = Field(default=0, description="Total work amount in this SAL")
    importo_sicurezza: float = Field(default=0, description="Safety amount in this SAL")
    importo_manodopera: float = Field(default=0, description="Labor amount in this SAL")

    # Cumulative
    importo_lavori_cumulativo: float = Field(default=0, description="Cumulative work amount")
    importo_sicurezza_cumulativo: float = Field(default=0, description="Cumulative safety amount")

    # Stats
    num_voci: int = Field(default=0, description="Number of voci in this SAL")
    registrato: bool = Field(default=False, description="SAL is registered/emitted")

    class Config:
        json_schema_extra = {
            "example": {
                "numero": 1,
                "data_emissione": "2024-01-31",
                "importo_lavori": 25000.00,
                "importo_sicurezza": 750.00,
                "importo_manodopera": 7500.00,
                "importo_lavori_cumulativo": 25000.00,
                "importo_sicurezza_cumulativo": 750.00,
                "num_voci": 15,
                "registrato": True
            }
        }


class StatoContabilita(BaseModel):
    """Overall status of Contabilità."""

    totale_lavori: float = Field(default=0, description="Total work amount")
    totale_sicurezza: float = Field(default=0, description="Total safety amount")
    totale_manodopera: float = Field(default=0, description="Total labor amount")

    num_sal_emessi: int = Field(default=0, description="Number of SAL emitted")
    ultimo_sal: Optional[int] = Field(default=None, description="Last SAL number")

    importo_registrato: float = Field(default=0, description="Amount in registered SAL")
    importo_da_registrare: float = Field(default=0, description="Amount not yet registered")

    num_voci_totali: int = Field(default=0, description="Total number of voci")
    num_voci_registrate: int = Field(default=0, description="Number of registered voci")

    sal_list: List[SALInfo] = Field(default_factory=list, description="List of all SAL")

    class Config:
        json_schema_extra = {
            "example": {
                "totale_lavori": 85000.00,
                "totale_sicurezza": 2550.00,
                "totale_manodopera": 25500.00,
                "num_sal_emessi": 3,
                "ultimo_sal": 3,
                "importo_registrato": 75000.00,
                "importo_da_registrare": 10000.00,
                "num_voci_totali": 45,
                "num_voci_registrate": 40,
                "sal_list": []
            }
        }
