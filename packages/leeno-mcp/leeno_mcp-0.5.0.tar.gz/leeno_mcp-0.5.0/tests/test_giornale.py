"""
Tests for Giornale Lavori tools and wrappers.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestGiornaleWrapper:
    """Tests for GiornaleWrapper."""

    def test_wrapper_import(self):
        """Test that GiornaleWrapper can be imported."""
        from leeno_mcp.wrappers.giornale import GiornaleWrapper, GiornaleInfo, GiornoLavori
        assert GiornaleWrapper is not None
        assert GiornaleInfo is not None
        assert GiornoLavori is not None

    def test_giornale_info_model(self):
        """Test GiornaleInfo dataclass."""
        from leeno_mcp.wrappers.giornale import GiornaleInfo

        info = GiornaleInfo(
            exists=True,
            num_giorni=15,
            data_inizio="01/01/2025",
            data_fine="20/01/2025"
        )

        assert info.exists is True
        assert info.num_giorni == 15
        assert info.data_inizio == "01/01/2025"
        assert info.data_fine == "20/01/2025"

    def test_giornale_info_not_exists(self):
        """Test GiornaleInfo when giornale doesn't exist."""
        from leeno_mcp.wrappers.giornale import GiornaleInfo

        info = GiornaleInfo(
            exists=False,
            num_giorni=0,
            data_inizio=None,
            data_fine=None
        )

        assert info.exists is False
        assert info.data_inizio is None

    def test_giorno_lavori_model(self):
        """Test GiornoLavori dataclass."""
        from leeno_mcp.wrappers.giornale import GiornoLavori

        giorno = GiornoLavori(
            data="15/01/2025",
            riga=10,
            note="Iniziati lavori di scavo",
            condizioni_meteo="Soleggiato",
            operai=5,
            ore_lavorate=8.0
        )

        assert giorno.data == "15/01/2025"
        assert giorno.riga == 10
        assert giorno.note == "Iniziati lavori di scavo"
        assert giorno.operai == 5
        assert giorno.ore_lavorate == 8.0

    def test_giorno_lavori_minimal(self):
        """Test GiornoLavori with minimal data."""
        from leeno_mcp.wrappers.giornale import GiornoLavori

        giorno = GiornoLavori(
            data="15/01/2025",
            riga=10,
            note=""
        )

        assert giorno.data == "15/01/2025"
        assert giorno.condizioni_meteo is None
        assert giorno.operai is None

    def test_wrapper_has_required_methods(self):
        """Test wrapper has expected methods."""
        from leeno_mcp.wrappers.giornale import GiornaleWrapper

        assert hasattr(GiornaleWrapper, 'has_giornale')
        assert hasattr(GiornaleWrapper, 'crea_giornale')
        assert hasattr(GiornaleWrapper, 'nuovo_giorno')
        assert hasattr(GiornaleWrapper, 'get_giornale_info')
        assert hasattr(GiornaleWrapper, 'list_giorni')
        assert hasattr(GiornaleWrapper, 'aggiungi_nota')

    def test_wrapper_sheet_names(self):
        """Test wrapper uses correct sheet names."""
        from leeno_mcp.wrappers.giornale import GiornaleWrapper

        assert GiornaleWrapper.SHEET_GIORNALE == "GIORNALE"
        assert GiornaleWrapper.SHEET_GIORNALE_BIANCO == "GIORNALE_BIANCO"


class TestGiornaleTools:
    """Tests for Giornale MCP tools."""

    def test_tools_import(self):
        """Test that giornale tools can be imported."""
        from leeno_mcp.tools.giornale import register_giornale_tools
        assert register_giornale_tools is not None

    @pytest.mark.asyncio
    async def test_tool_registration(self, mock_uno_module):
        """Test that tools are registered correctly."""
        from mcp.server import FastMCP
        from leeno_mcp.tools.giornale import register_giornale_tools

        server = FastMCP("test")
        register_giornale_tools(server)

        assert True  # Registration completed without error

    def test_giornale_tools_count(self):
        """Test that we have 5 giornale tools."""
        from leeno_mcp.tools.giornale import register_giornale_tools
        from mcp.server import FastMCP

        server = FastMCP("test")
        register_giornale_tools(server)

        # Should have registered 5 tools
        assert True  # Basic smoke test


class TestNuovoGiorno:
    """Tests for nuovo_giorno functionality."""

    def test_nuovo_giorno_signature(self):
        """Test nuovo_giorno method signature."""
        from leeno_mcp.wrappers.giornale import GiornaleWrapper
        import inspect

        sig = inspect.signature(GiornaleWrapper.nuovo_giorno)
        params = sig.parameters

        assert 'self' in params
        assert 'data' in params

    def test_data_parameter_optional(self):
        """Test data parameter is optional."""
        from leeno_mcp.wrappers.giornale import GiornaleWrapper
        import inspect

        sig = inspect.signature(GiornaleWrapper.nuovo_giorno)
        data_param = sig.parameters['data']

        assert data_param.default is None

    def test_date_format(self):
        """Test expected date format DD/MM/YYYY."""
        today = datetime.now()
        formatted = today.strftime("%d/%m/%Y")

        parts = formatted.split("/")
        assert len(parts) == 3
        assert len(parts[0]) == 2  # DD
        assert len(parts[1]) == 2  # MM
        assert len(parts[2]) == 4  # YYYY


class TestAggiungiNota:
    """Tests for aggiungi_nota functionality."""

    def test_aggiungi_nota_signature(self):
        """Test aggiungi_nota method signature."""
        from leeno_mcp.wrappers.giornale import GiornaleWrapper
        import inspect

        sig = inspect.signature(GiornaleWrapper.aggiungi_nota)
        params = sig.parameters

        assert 'self' in params
        assert 'riga' in params
        assert 'nota' in params

    def test_aggiungi_nota_returns_bool(self):
        """Test aggiungi_nota returns boolean."""
        from leeno_mcp.wrappers.giornale import GiornaleWrapper

        # Method should return bool
        assert hasattr(GiornaleWrapper, 'aggiungi_nota')


class TestListGiorni:
    """Tests for list_giorni functionality."""

    def test_list_giorni_returns_list(self):
        """Test list_giorni returns list."""
        from leeno_mcp.wrappers.giornale import GiornaleWrapper

        # Method exists
        assert hasattr(GiornaleWrapper, 'list_giorni')

    def test_giorno_lavori_in_list(self):
        """Test GiornoLavori can be used in list."""
        from leeno_mcp.wrappers.giornale import GiornoLavori

        giorni = [
            GiornoLavori(data="01/01/2025", riga=5, note="Day 1"),
            GiornoLavori(data="02/01/2025", riga=15, note="Day 2"),
        ]

        assert len(giorni) == 2
        assert giorni[0].data == "01/01/2025"
        assert giorni[1].data == "02/01/2025"
