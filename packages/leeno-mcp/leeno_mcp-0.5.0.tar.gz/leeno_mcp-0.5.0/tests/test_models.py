"""
Tests for Pydantic models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestRigaMisura:
    """Tests for RigaMisura model."""

    def test_create_basic(self):
        """Test creating a basic RigaMisura."""
        from leeno_mcp.models.voce import RigaMisura

        misura = RigaMisura(
            descrizione="Muro esterno",
            parti_uguali=1,
            lunghezza=10.0,
            larghezza=0.30,
            altezza=3.0
        )

        assert misura.descrizione == "Muro esterno"
        assert misura.parti_uguali == 1
        assert misura.lunghezza == 10.0
        assert misura.larghezza == 0.30
        assert misura.altezza == 3.0

    def test_quantita_calcolata(self):
        """Test automatic quantity calculation."""
        from leeno_mcp.models.voce import RigaMisura

        misura = RigaMisura(
            descrizione="Test",
            parti_uguali=2,
            lunghezza=5.0,
            larghezza=2.0,
            altezza=3.0
        )

        # 2 * 5 * 2 * 3 = 60
        assert misura.quantita_calcolata == 60.0

    def test_quantita_calcolata_with_forced_quantity(self):
        """Test that forced quantity overrides calculation."""
        from leeno_mcp.models.voce import RigaMisura

        misura = RigaMisura(
            descrizione="Test",
            parti_uguali=2,
            lunghezza=5.0,
            quantita=100.0  # Forced quantity
        )

        assert misura.quantita_calcolata == 100.0

    def test_quantita_calcolata_partial_dimensions(self):
        """Test calculation with partial dimensions."""
        from leeno_mcp.models.voce import RigaMisura

        # Only length
        misura = RigaMisura(lunghezza=10.0)
        assert misura.quantita_calcolata == 10.0

        # Length and width
        misura = RigaMisura(lunghezza=10.0, larghezza=2.0)
        assert misura.quantita_calcolata == 20.0

    def test_default_values(self):
        """Test default values."""
        from leeno_mcp.models.voce import RigaMisura

        misura = RigaMisura()

        assert misura.descrizione == ""
        assert misura.parti_uguali == 0
        assert misura.lunghezza == 0
        assert misura.larghezza == 0
        assert misura.altezza == 0
        assert misura.quantita == 0
        assert misura.riga == 0


class TestVoceComputo:
    """Tests for VoceComputo model."""

    def test_create_voce(self, sample_voce_data):
        """Test creating a VoceComputo."""
        from leeno_mcp.models.voce import VoceComputo

        voce = VoceComputo(**sample_voce_data)

        assert voce.voce_id == "V001"
        assert voce.codice == "01.A01.001"
        assert voce.quantita == 125.50
        assert voce.prezzo_unitario == 12.50
        assert voce.importo == 1568.75

    def test_importo_calcolato(self):
        """Test automatic import calculation."""
        from leeno_mcp.models.voce import VoceComputo

        voce = VoceComputo(
            voce_id="V001",
            codice="01.A01.001",
            quantita=10.0,
            prezzo_unitario=25.0
        )

        assert voce.importo_calcolato == 250.0

    def test_quantita_totale_with_misure(self):
        """Test total quantity from measurements."""
        from leeno_mcp.models.voce import VoceComputo, RigaMisura

        misure = [
            RigaMisura(lunghezza=10.0),  # 10
            RigaMisura(lunghezza=5.0),   # 5
            RigaMisura(quantita=20.0),   # 20 (forced)
        ]

        voce = VoceComputo(
            voce_id="V001",
            codice="01.A01.001",
            misure=misure
        )

        assert voce.quantita_totale == 35.0

    def test_quantita_totale_without_misure(self):
        """Test total quantity without measurements."""
        from leeno_mcp.models.voce import VoceComputo

        voce = VoceComputo(
            voce_id="V001",
            codice="01.A01.001",
            quantita=100.0
        )

        assert voce.quantita_totale == 100.0

    def test_required_fields(self):
        """Test that required fields are enforced."""
        from leeno_mcp.models.voce import VoceComputo

        with pytest.raises(ValidationError):
            VoceComputo()  # Missing voce_id and codice

        with pytest.raises(ValidationError):
            VoceComputo(voce_id="V001")  # Missing codice


class TestVoceComputoInput:
    """Tests for VoceComputoInput model."""

    def test_create_input(self):
        """Test creating a VoceComputoInput."""
        from leeno_mcp.models.voce import VoceComputoInput

        inp = VoceComputoInput(
            codice="01.A01.001",
            quantita=100.0
        )

        assert inp.codice == "01.A01.001"
        assert inp.quantita == 100.0
        assert inp.descrizione is None

    def test_required_codice(self):
        """Test that codice is required."""
        from leeno_mcp.models.voce import VoceComputoInput

        with pytest.raises(ValidationError):
            VoceComputoInput(quantita=100.0)


class TestMisuraInput:
    """Tests for MisuraInput model."""

    def test_create_input(self, sample_misura_data):
        """Test creating a MisuraInput."""
        from leeno_mcp.models.voce import MisuraInput

        del sample_misura_data["riga"]  # MisuraInput doesn't have riga
        inp = MisuraInput(**sample_misura_data)

        assert inp.descrizione == "Muro perimetrale piano terra"
        assert inp.lunghezza == 12.50
        assert inp.larghezza == 0.30
        assert inp.altezza == 3.00


class TestPrezzo:
    """Tests for Prezzo model."""

    def test_create_prezzo(self, sample_prezzo_data):
        """Test creating a Prezzo."""
        from leeno_mcp.models.prezzo import Prezzo

        # Adjust sample data to match Prezzo model
        data = {
            "codice": sample_prezzo_data["codice"],
            "descrizione": sample_prezzo_data["descrizione"],
            "unita_misura": sample_prezzo_data["unita_misura"],
            "prezzo_unitario": sample_prezzo_data["prezzo_unitario"],
            "manodopera": sample_prezzo_data["incidenza_manodopera"],
            "sicurezza": sample_prezzo_data["incidenza_sicurezza"],
        }

        prezzo = Prezzo(**data)

        assert prezzo.codice == "01.A01.001"
        assert prezzo.prezzo_unitario == 12.50
        assert prezzo.manodopera == 30.0
        assert prezzo.sicurezza == 3.0

    def test_importo_sicurezza(self):
        """Test safety amount calculation."""
        from leeno_mcp.models.prezzo import Prezzo

        prezzo = Prezzo(
            codice="01.A01.001",
            prezzo_unitario=100.0,
            sicurezza=5.0
        )

        assert prezzo.importo_sicurezza == 5.0

    def test_importo_manodopera(self):
        """Test labor amount calculation."""
        from leeno_mcp.models.prezzo import Prezzo

        prezzo = Prezzo(
            codice="01.A01.001",
            prezzo_unitario=100.0,
            manodopera=30.0
        )

        assert prezzo.importo_manodopera == 30.0

    def test_percentage_validation(self):
        """Test that percentages are validated."""
        from leeno_mcp.models.prezzo import Prezzo

        # Values > 100 are now allowed (some documents have unusual percentages)
        prezzo = Prezzo(codice="01.A01.001", sicurezza=150.0)
        assert prezzo.sicurezza == 150.0

        # Negative values should still raise an error
        with pytest.raises(ValidationError):
            Prezzo(codice="01.A01.001", manodopera=-5.0)  # < 0


class TestPrezzoInput:
    """Tests for PrezzoInput model."""

    def test_required_fields(self):
        """Test that required fields are enforced."""
        from leeno_mcp.models.prezzo import PrezzoInput

        with pytest.raises(ValidationError):
            PrezzoInput(codice="01.A01.001")  # Missing descrizione, unita_misura, prezzo_unitario

    def test_create_input(self):
        """Test creating a PrezzoInput."""
        from leeno_mcp.models.prezzo import PrezzoInput

        inp = PrezzoInput(
            codice="NP.001",
            descrizione="Nuova lavorazione",
            unita_misura="mq",
            prezzo_unitario=25.0
        )

        assert inp.codice == "NP.001"
        assert inp.descrizione == "Nuova lavorazione"


class TestPrezzoSearchResult:
    """Tests for PrezzoSearchResult model."""

    def test_create_result(self):
        """Test creating a search result."""
        from leeno_mcp.models.prezzo import PrezzoSearchResult

        result = PrezzoSearchResult(
            codice="01.A01.001",
            descrizione="Scavo",
            unita_misura="mc",
            prezzo_unitario=12.50,
            riga=10
        )

        assert result.codice == "01.A01.001"
        assert result.prezzo_unitario == 12.50


class TestCapitolo:
    """Tests for Capitolo model."""

    def test_create_capitolo(self, sample_capitolo_data):
        """Test creating a Capitolo."""
        from leeno_mcp.models.capitolo import Capitolo

        cap = Capitolo(**sample_capitolo_data)

        assert cap.capitolo_id == "CAP_001"
        assert cap.nome == "OPERE MURARIE"
        assert cap.livello == 0

    def test_tipo_property(self):
        """Test chapter type property."""
        from leeno_mcp.models.capitolo import Capitolo

        cap0 = Capitolo(capitolo_id="CAP_001", nome="Test", livello=0)
        cap1 = Capitolo(capitolo_id="CAP_002", nome="Test", livello=1)
        cap2 = Capitolo(capitolo_id="CAP_003", nome="Test", livello=2)

        assert cap0.tipo == "SuperCapitolo"
        assert cap1.tipo == "Capitolo"
        assert cap2.tipo == "SottoCapitolo"

    def test_livello_validation(self):
        """Test that level is validated."""
        from leeno_mcp.models.capitolo import Capitolo

        with pytest.raises(ValidationError):
            Capitolo(capitolo_id="CAP_001", nome="Test", livello=3)  # > 2

        with pytest.raises(ValidationError):
            Capitolo(capitolo_id="CAP_001", nome="Test", livello=-1)  # < 0


class TestCapitoloInput:
    """Tests for CapitoloInput model."""

    def test_create_input(self):
        """Test creating a CapitoloInput."""
        from leeno_mcp.models.capitolo import CapitoloInput

        inp = CapitoloInput(nome="OPERE MURARIE", livello=1)

        assert inp.nome == "OPERE MURARIE"
        assert inp.livello == 1

    def test_required_nome(self):
        """Test that nome is required."""
        from leeno_mcp.models.capitolo import CapitoloInput

        with pytest.raises(ValidationError):
            CapitoloInput(livello=1)


class TestStrutturaComputo:
    """Tests for StrutturaComputo model."""

    def test_create_struttura(self):
        """Test creating a StrutturaComputo."""
        from leeno_mcp.models.capitolo import StrutturaComputo, Capitolo

        cap = Capitolo(capitolo_id="CAP_001", nome="Test", importo=1000.0)

        struttura = StrutturaComputo(
            capitoli=[cap],
            totale_importo=1000.0,
            num_voci_totali=5
        )

        assert len(struttura.capitoli) == 1
        assert struttura.totale_importo == 1000.0
        assert struttura.num_voci_totali == 5


class TestDocumentoInfo:
    """Tests for DocumentoInfo model."""

    def test_create_info(self):
        """Test creating a DocumentoInfo."""
        from leeno_mcp.models.documento import DocumentoInfo

        info = DocumentoInfo(
            doc_id="doc_001",
            path="/tmp/test.ods",
            title="test.ods",
            is_leeno=True,
            sheets=["COMPUTO", "Elenco Prezzi"]
        )

        assert info.doc_id == "doc_001"
        assert info.is_leeno is True
        assert len(info.sheets) == 2

    def test_default_values(self):
        """Test default values."""
        from leeno_mcp.models.documento import DocumentoInfo

        info = DocumentoInfo(doc_id="doc_001")

        assert info.path is None
        assert info.title == "Untitled"
        assert info.is_leeno is False
        assert info.modified is False
        assert info.sheets == []
        assert isinstance(info.created_at, datetime)


class TestDocumentoStats:
    """Tests for DocumentoStats model."""

    def test_create_stats(self):
        """Test creating DocumentoStats."""
        from leeno_mcp.models.documento import DocumentoStats

        stats = DocumentoStats(
            doc_id="doc_001",
            num_voci_computo=45,
            totale_computo=125000.50,
            num_prezzi=1523,
            has_contabilita=True,
            num_sal=3
        )

        assert stats.num_voci_computo == 45
        assert stats.totale_computo == 125000.50
        assert stats.has_contabilita is True
        assert stats.num_sal == 3


class TestDocumentoCreateResult:
    """Tests for DocumentoCreateResult model."""

    def test_create_result(self):
        """Test creating a DocumentoCreateResult."""
        from leeno_mcp.models.documento import DocumentoCreateResult

        result = DocumentoCreateResult(
            doc_id="doc_001",
            is_leeno=True
        )

        assert result.doc_id == "doc_001"
        assert result.path is None
        assert result.is_leeno is True


class TestDocumentoOpenResult:
    """Tests for DocumentoOpenResult model."""

    def test_create_result(self):
        """Test creating a DocumentoOpenResult."""
        from leeno_mcp.models.documento import DocumentoOpenResult, DocumentoInfo

        info = DocumentoInfo(doc_id="doc_001", is_leeno=True)

        result = DocumentoOpenResult(
            doc_id="doc_001",
            path="/tmp/test.ods",
            is_leeno=True,
            info=info
        )

        assert result.doc_id == "doc_001"
        assert result.path == "/tmp/test.ods"
        assert result.info.is_leeno is True


class TestDocumentoSaveResult:
    """Tests for DocumentoSaveResult model."""

    def test_create_result(self):
        """Test creating a DocumentoSaveResult."""
        from leeno_mcp.models.documento import DocumentoSaveResult

        result = DocumentoSaveResult(
            success=True,
            path="/tmp/test.ods"
        )

        assert result.success is True
        assert result.path == "/tmp/test.ods"
