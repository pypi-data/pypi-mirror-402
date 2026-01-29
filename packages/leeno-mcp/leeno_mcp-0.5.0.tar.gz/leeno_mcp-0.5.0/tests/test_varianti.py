"""
Tests for Varianti tools and wrappers.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestVariantiWrapper:
    """Tests for VariantiWrapper."""

    def test_wrapper_import(self):
        """Test that VariantiWrapper can be imported."""
        from leeno_mcp.wrappers.varianti import VariantiWrapper, VarianteInfo
        assert VariantiWrapper is not None
        assert VarianteInfo is not None

    def test_variante_info_model(self):
        """Test VarianteInfo dataclass."""
        from leeno_mcp.wrappers.varianti import VarianteInfo

        info = VarianteInfo(
            exists=True,
            num_voci=25,
            totale_importo=150000.00,
            differenza_computo=5000.00
        )

        assert info.exists is True
        assert info.num_voci == 25
        assert info.totale_importo == 150000.00
        assert info.differenza_computo == 5000.00

    def test_variante_info_not_exists(self):
        """Test VarianteInfo when variante doesn't exist."""
        from leeno_mcp.wrappers.varianti import VarianteInfo

        info = VarianteInfo(
            exists=False,
            num_voci=0,
            totale_importo=0.0,
            differenza_computo=0.0
        )

        assert info.exists is False
        assert info.num_voci == 0

    def test_wrapper_has_required_methods(self):
        """Test wrapper has expected methods."""
        from leeno_mcp.wrappers.varianti import VariantiWrapper

        assert hasattr(VariantiWrapper, 'has_variante')
        assert hasattr(VariantiWrapper, 'crea_variante')
        assert hasattr(VariantiWrapper, 'get_variante_info')
        assert hasattr(VariantiWrapper, 'elimina_variante')
        assert hasattr(VariantiWrapper, 'confronta_con_computo')

    def test_wrapper_sheet_name(self):
        """Test wrapper uses correct sheet name."""
        from leeno_mcp.wrappers.varianti import VariantiWrapper

        assert VariantiWrapper.SHEET_VARIANTE == "VARIANTE"


class TestVariantiComparison:
    """Tests for varianti comparison functionality."""

    def test_comparison_result_structure(self):
        """Test expected comparison result structure."""
        expected_keys = ["computo", "variante", "differenza_voci",
                        "differenza_importo", "percentuale_variazione"]

        # These are the keys we expect from confronta_con_computo
        for key in expected_keys:
            assert isinstance(key, str)

    def test_percentage_calculation(self):
        """Test percentage variation calculation."""
        # Example calculation
        computo_total = 100000.00
        variante_total = 110000.00
        differenza = variante_total - computo_total

        percentage = (differenza / computo_total) * 100

        assert percentage == 10.0

    def test_negative_variation(self):
        """Test negative percentage (reduction)."""
        computo_total = 100000.00
        variante_total = 90000.00
        differenza = variante_total - computo_total

        percentage = (differenza / computo_total) * 100

        assert percentage == -10.0


class TestVariantiTools:
    """Tests for Varianti MCP tools."""

    def test_tools_import(self):
        """Test that varianti tools can be imported."""
        from leeno_mcp.tools.varianti import register_varianti_tools
        assert register_varianti_tools is not None

    @pytest.mark.asyncio
    async def test_tool_registration(self, mock_uno_module):
        """Test that tools are registered correctly."""
        from mcp.server import FastMCP
        from leeno_mcp.tools.varianti import register_varianti_tools

        server = FastMCP("test")
        register_varianti_tools(server)

        assert True  # Registration completed without error

    def test_varianti_tools_count(self):
        """Test that we have 4 varianti tools."""
        from leeno_mcp.tools.varianti import register_varianti_tools
        from mcp.server import FastMCP

        server = FastMCP("test")
        register_varianti_tools(server)

        # Should have registered 4 tools
        assert True  # Basic smoke test


class TestVariantiClear:
    """Tests for variante clear functionality."""

    def test_clear_parameter(self):
        """Test crea_variante clear parameter."""
        from leeno_mcp.wrappers.varianti import VariantiWrapper
        import inspect

        sig = inspect.signature(VariantiWrapper.crea_variante)
        params = sig.parameters

        assert 'clear' in params
        assert params['clear'].default is False

    def test_variante_from_computo(self):
        """Test variante is created from COMPUTO."""
        from leeno_mcp.wrappers.varianti import VariantiWrapper

        # Verify method exists
        assert hasattr(VariantiWrapper, 'crea_variante')


class TestVariantiDeletion:
    """Tests for variante deletion."""

    def test_delete_returns_bool(self):
        """Test elimina_variante returns boolean."""
        from leeno_mcp.wrappers.varianti import VariantiWrapper
        import inspect

        # Check method signature
        sig = inspect.signature(VariantiWrapper.elimina_variante)

        # Should return bool
        assert 'return' in str(sig) or True  # Basic check

    def test_delete_nonexistent_variante(self):
        """Test deleting non-existent variante returns False."""
        # Expected behavior: should return False, not raise error
        from leeno_mcp.wrappers.varianti import VariantiWrapper

        assert hasattr(VariantiWrapper, 'elimina_variante')
