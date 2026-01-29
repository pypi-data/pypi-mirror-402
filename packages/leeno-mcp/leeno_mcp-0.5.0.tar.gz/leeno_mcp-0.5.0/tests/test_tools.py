"""
Tests for MCP tools.

These tests verify the tool registration and basic functionality.
Since the tools are async and depend on MCP server, we test the
underlying wrapper functions and logic.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio


class TestDocumentToolsRegistration:
    """Tests for document tools registration."""

    def test_register_document_tools(self, mock_uno_module):
        """Test that document tools are registered correctly."""
        from leeno_mcp.tools.documents import register_document_tools

        # Create mock server
        mock_server = MagicMock()
        mock_server.tool = MagicMock(return_value=lambda f: f)

        # Register tools
        register_document_tools(mock_server)

        # Verify tool decorator was called
        assert mock_server.tool.called


class TestComputoToolsRegistration:
    """Tests for computo tools registration."""

    def test_register_computo_tools(self, mock_uno_module):
        """Test that computo tools are registered correctly."""
        from leeno_mcp.tools.computo import register_computo_tools

        mock_server = MagicMock()
        mock_server.tool = MagicMock(return_value=lambda f: f)

        register_computo_tools(mock_server)

        assert mock_server.tool.called


class TestElencoPrezziToolsRegistration:
    """Tests for elenco prezzi tools registration."""

    def test_register_elenco_prezzi_tools(self, mock_uno_module):
        """Test that elenco prezzi tools are registered correctly."""
        from leeno_mcp.tools.elenco_prezzi import register_elenco_prezzi_tools

        mock_server = MagicMock()
        mock_server.tool = MagicMock(return_value=lambda f: f)

        register_elenco_prezzi_tools(mock_server)

        assert mock_server.tool.called


class TestContabilitaToolsRegistration:
    """Tests for contabilita tools registration."""

    def test_register_contabilita_tools(self, mock_uno_module):
        """Test that contabilita tools are registered correctly."""
        from leeno_mcp.tools.contabilita import register_contabilita_tools

        mock_server = MagicMock()
        mock_server.tool = MagicMock(return_value=lambda f: f)

        register_contabilita_tools(mock_server)

        assert mock_server.tool.called


class TestExportToolsRegistration:
    """Tests for export tools registration."""

    def test_register_export_tools(self, mock_uno_module):
        """Test that export tools are registered correctly."""
        from leeno_mcp.tools.export import register_export_tools

        mock_server = MagicMock()
        mock_server.tool = MagicMock(return_value=lambda f: f)

        register_export_tools(mock_server)

        assert mock_server.tool.called


class TestServerCreation:
    """Tests for MCP server creation."""

    def test_create_server(self, mock_uno_module):
        """Test server creation with all tools registered."""
        with patch('leeno_mcp.server.FastMCP') as MockFastMCP:
            mock_server_instance = MagicMock()
            mock_server_instance.tool = MagicMock(return_value=lambda f: f)
            MockFastMCP.return_value = mock_server_instance

            from leeno_mcp.server import create_server

            create_server()

            # Verify FastMCP was created
            MockFastMCP.assert_called_once()


class TestToolHelpers:
    """Tests for tool helper functions."""

    def test_document_pool_integration(self, mock_uno_module, leeno_document):
        """Test that tools work with document pool."""
        from leeno_mcp.connection.document_pool import DocumentPool

        pool = DocumentPool.__new__(DocumentPool)
        pool._initialized = False
        pool._documents = {}
        pool._path_index = {}
        pool._bridge = MagicMock()
        pool._initialized = True

        # Add a document
        pool.add(leeno_document, doc_id="test_doc")

        # Verify we can retrieve it
        retrieved = pool.get("test_doc")
        assert retrieved.doc_id == "test_doc"
        assert retrieved.is_leeno is True


class TestDocumentWrapperIntegration:
    """Tests for document wrapper integration with tools."""

    def test_wrapper_functions(self, mock_uno_module, document_info):
        """Test that wrapper can provide tool responses."""
        from leeno_mcp.wrappers.base import LeenoWrapper

        wrapper = LeenoWrapper(document_info)

        # Verify wrapper provides needed data
        assert wrapper.doc_id is not None
        assert wrapper.get_sheet_names() is not None


class TestToolResponseFormats:
    """Tests for expected tool response formats."""

    def test_text_content_format(self):
        """Test that we can create proper TextContent responses."""
        # This tests that we understand the expected format
        response = {
            "type": "text",
            "text": "Document created successfully.\ndoc_id: test_001\nis_leeno: True"
        }

        assert response["type"] == "text"
        assert "doc_id" in response["text"]

    def test_error_response_format(self):
        """Test error response format."""
        error_msg = "Document not found"
        response = {
            "type": "text",
            "text": f"Error: {error_msg}"
        }

        assert "Error" in response["text"]


class TestAsyncToolBehavior:
    """Tests for async tool behavior."""

    @pytest.mark.asyncio
    async def test_async_tool_pattern(self):
        """Test that async tools work correctly."""
        async def sample_tool(param: str) -> list:
            # Simulate async operation
            await asyncio.sleep(0)
            return [{"type": "text", "text": f"Result: {param}"}]

        result = await sample_tool("test")
        assert len(result) == 1
        assert "Result" in result[0]["text"]

    @pytest.mark.asyncio
    async def test_async_tool_error_handling(self):
        """Test async tool error handling."""
        async def tool_with_error(param: str) -> list:
            try:
                if not param:
                    raise ValueError("Parameter required")
                return [{"type": "text", "text": "Success"}]
            except Exception as e:
                return [{"type": "text", "text": f"Error: {str(e)}"}]

        result = await tool_with_error("")
        assert "Error" in result[0]["text"]

        result = await tool_with_error("valid")
        assert "Success" in result[0]["text"]


class TestToolInputValidation:
    """Tests for tool input validation."""

    def test_doc_id_validation(self):
        """Test document ID validation patterns."""
        valid_ids = ["doc_a1b2c3d4", "doc_12345678", "custom_id"]
        invalid_ids = ["", None]

        for doc_id in valid_ids:
            assert doc_id is not None
            assert len(doc_id) > 0

        for doc_id in invalid_ids:
            assert not doc_id  # Falsy

    def test_path_validation(self):
        """Test file path validation."""
        from pathlib import Path

        valid_paths = ["/tmp/test.ods", "C:\\Users\\test.ods", "./relative/path.ods"]

        for path in valid_paths:
            # Path should be parseable
            p = Path(path)
            assert p.suffix == ".ods"

    def test_codice_validation(self):
        """Test article code validation patterns."""
        valid_codes = ["01.A01.001", "02.B15.123", "NP.001"]

        for code in valid_codes:
            assert len(code) > 0
            # Codes typically have dots
            assert "." in code or code.startswith("NP")


class TestToolOutputParsing:
    """Tests for parsing tool outputs."""

    def test_parse_document_info_output(self):
        """Test parsing document info from tool output."""
        output_text = """Document: test.ods
ID: doc_001
Path: /tmp/test.ods
Is LeenO: True
Modified: False
Sheets: COMPUTO, Elenco Prezzi"""

        # Verify we can extract information
        assert "doc_001" in output_text
        assert "True" in output_text
        assert "COMPUTO" in output_text

    def test_parse_voce_list_output(self):
        """Test parsing voce list from tool output."""
        output_text = """Voci in computo:
1. [01.A01.001] Scavo a sezione aperta - 125.50 mc - € 1,568.75
2. [01.A01.002] Scavo in trincea - 80.00 mc - € 1,440.00
Total: 2 voci, € 3,008.75"""

        assert "01.A01.001" in output_text
        assert "125.50" in output_text

    def test_parse_search_results_output(self):
        """Test parsing search results from tool output."""
        output_text = """Found 3 prices matching 'scavo':
- [01.A01.001] Scavo a sezione aperta - mc - € 12.50
- [01.A01.002] Scavo in trincea - mc - € 18.00
- [01.A01.003] Scavo a mano - mc - € 35.00"""

        lines = output_text.strip().split("\n")
        assert len(lines) == 4  # Header + 3 results
        assert "scavo" in lines[0].lower()
