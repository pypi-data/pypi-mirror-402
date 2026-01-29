"""
Models for Capitoli (chapters) in Computo Metrico.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class Capitolo(BaseModel):
    """A chapter in the Computo Metrico structure."""

    capitolo_id: str = Field(..., description="Internal chapter ID (e.g., 'CAP_001')")
    nome: str = Field(..., description="Chapter name")
    livello: int = Field(default=1, description="Hierarchy level (0=SuperCapitolo, 1=Capitolo, 2=SottoCapitolo)", ge=0, le=2)
    riga: int = Field(default=0, description="Row number in spreadsheet", ge=0)
    parent_id: Optional[str] = Field(default=None, description="Parent chapter ID")
    importo: float = Field(default=0, description="Total amount for this chapter")
    sicurezza: float = Field(default=0, description="Total safety amount")
    manodopera: float = Field(default=0, description="Total labor amount")
    num_voci: int = Field(default=0, description="Number of voci in this chapter")

    @property
    def tipo(self) -> str:
        """Get chapter type based on level."""
        types = {0: "SuperCapitolo", 1: "Capitolo", 2: "SottoCapitolo"}
        return types.get(self.livello, "Capitolo")

    class Config:
        json_schema_extra = {
            "example": {
                "capitolo_id": "CAP_001",
                "nome": "OPERE MURARIE",
                "livello": 1,
                "riga": 8,
                "parent_id": None,
                "importo": 45000.00,
                "sicurezza": 1350.00,
                "manodopera": 13500.00,
                "num_voci": 12
            }
        }


class CapitoloInput(BaseModel):
    """Input model for creating a chapter."""

    nome: str = Field(..., description="Chapter name")
    livello: int = Field(default=1, description="Hierarchy level (0, 1, or 2)", ge=0, le=2)

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "OPERE MURARIE",
                "livello": 1
            }
        }


class StrutturaComputo(BaseModel):
    """Complete structure of a Computo Metrico."""

    capitoli: List[Capitolo] = Field(default_factory=list, description="List of all chapters")
    totale_importo: float = Field(default=0, description="Total computo amount")
    totale_sicurezza: float = Field(default=0, description="Total safety amount")
    totale_manodopera: float = Field(default=0, description="Total labor amount")
    num_voci_totali: int = Field(default=0, description="Total number of voci")

    class Config:
        json_schema_extra = {
            "example": {
                "capitoli": [
                    {
                        "capitolo_id": "CAP_001",
                        "nome": "OPERE MURARIE",
                        "livello": 1,
                        "importo": 45000.00
                    }
                ],
                "totale_importo": 125000.00,
                "totale_sicurezza": 3750.00,
                "totale_manodopera": 37500.00,
                "num_voci_totali": 35
            }
        }
