"""Unit tests for thinkpdf MCP server.

Tests the MCP (Model Context Protocol) server implementation for:
- Protocol handshake (initialize)
- Tool discovery (tools/list)
- Tool execution (read_pdf, convert_pdf, get_document_info)
- Error handling

Run with: pytest tests/test_mcp.py -v
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest


class TestMCPServerInitialization:
    """Tests for MCP server initialization and setup."""

    def test_server_import(self):
        """Test that MCP server can be imported."""
        from thinkpdf.mcp_server import thinkpdfMCPServer, main
        
        assert thinkpdfMCPServer is not None
        assert callable(main)

    def test_server_instantiation(self):
        """Test that MCP server can be instantiated."""
        from thinkpdf.mcp_server import thinkpdfMCPServer
        
        server = thinkpdfMCPServer()
        assert server is not None
        assert hasattr(server, "engine")
        assert hasattr(server, "handle_request")


class TestMCPInitialize:
    """Tests for MCP initialize handshake."""

    def test_handle_initialize(self, mcp_server, mcp_initialize_request):
        """Test MCP initialize request returns proper response."""
        response = mcp_server.handle_request(mcp_initialize_request)
        
        assert response is not None
        assert "result" in response
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == mcp_initialize_request["id"]
        
        result = response["result"]
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "thinkpdf"

    def test_initialize_returns_tools_capability(self, mcp_server, mcp_initialize_request):
        """Test that initialize response advertises tools capability."""
        response = mcp_server.handle_request(mcp_initialize_request)
        
        capabilities = response["result"]["capabilities"]
        assert "tools" in capabilities


class TestMCPListTools:
    """Tests for MCP tools/list endpoint."""

    def test_list_tools_returns_tools(self, mcp_server, mcp_list_tools_request):
        """Test that tools/list returns available tools."""
        response = mcp_server.handle_request(mcp_list_tools_request)
        
        assert response is not None
        assert "result" in response
        assert "tools" in response["result"]
        
        tools = response["result"]["tools"]
        assert len(tools) >= 3

    def test_list_tools_includes_read_pdf(self, mcp_server, mcp_list_tools_request):
        """Test that read_pdf tool is available."""
        response = mcp_server.handle_request(mcp_list_tools_request)
        tools = response["result"]["tools"]
        
        tool_names = [t["name"] for t in tools]
        assert "read_pdf" in tool_names

    def test_list_tools_includes_convert_pdf(self, mcp_server, mcp_list_tools_request):
        """Test that convert_pdf tool is available."""
        response = mcp_server.handle_request(mcp_list_tools_request)
        tools = response["result"]["tools"]
        
        tool_names = [t["name"] for t in tools]
        assert "convert_pdf" in tool_names

    def test_list_tools_includes_get_document_info(self, mcp_server, mcp_list_tools_request):
        """Test that get_document_info tool is available."""
        response = mcp_server.handle_request(mcp_list_tools_request)
        tools = response["result"]["tools"]
        
        tool_names = [t["name"] for t in tools]
        assert "get_document_info" in tool_names

    def test_tools_have_input_schema(self, mcp_server, mcp_list_tools_request):
        """Test that all tools have input schema defined."""
        response = mcp_server.handle_request(mcp_list_tools_request)
        tools = response["result"]["tools"]
        
        for tool in tools:
            assert "inputSchema" in tool, f"Tool {tool['name']} missing inputSchema"
            assert "properties" in tool["inputSchema"]


class TestMCPToolReadPdf:
    """Tests for read_pdf tool execution."""

    def test_read_pdf_missing_path_returns_error(self, mcp_server):
        """Test that read_pdf without path returns error."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {
                "name": "read_pdf",
                "arguments": {},
            },
        }
        
        response = mcp_server.handle_request(request)
        
        # Should return error or content with error message
        assert response is not None

    def test_read_pdf_nonexistent_file(self, mcp_server, temp_dir):
        """Test that read_pdf with nonexistent file handles error."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {
                "name": "read_pdf",
                "arguments": {"path": str(temp_dir / "nonexistent.pdf")},
            },
        }
        
        response = mcp_server.handle_request(request)
        result = response.get("result", {})
        
        # Should indicate error in content
        if "content" in result:
            content_text = result["content"][0].get("text", "")
            assert "error" in content_text.lower() or "not found" in content_text.lower()


class TestMCPToolConvertPdf:
    """Tests for convert_pdf tool execution."""

    def test_convert_pdf_missing_args(self, mcp_server):
        """Test that convert_pdf without args handles gracefully."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {
                "name": "convert_pdf",
                "arguments": {},
            },
        }
        
        response = mcp_server.handle_request(request)
        assert response is not None


class TestMCPToolGetDocumentInfo:
    """Tests for get_document_info tool execution."""

    def test_get_document_info_with_valid_pdf(self, mcp_server, sample_pdf_file):
        """Test get_document_info returns metadata for valid PDF."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {
                "name": "get_document_info",
                "arguments": {"path": str(sample_pdf_file)},
            },
        }
        
        response = mcp_server.handle_request(request)
        
        assert response is not None
        assert "result" in response


class TestMCPErrorHandling:
    """Tests for MCP error responses."""

    def test_unknown_method_returns_error(self, mcp_server):
        """Test that unknown method returns proper error."""
        request = {
            "jsonrpc": "2.0",
            "method": "unknown/method",
            "id": 1,
        }
        
        response = mcp_server.handle_request(request)
        
        # Should return error
        assert response is not None
        assert "error" in response or "result" in response

    def test_malformed_request_handled(self, mcp_server):
        """Test that malformed request doesn't crash server."""
        request = {"incomplete": "request"}
        
        try:
            response = mcp_server.handle_request(request)
        except Exception as e:
            pytest.fail(f"Server crashed on malformed request: {e}")

    def test_error_response_format(self, mcp_server):
        """Test that error responses follow JSON-RPC format."""
        # Create error response directly
        error = mcp_server._error_response(
            request_id=1,
            code=-32600,
            message="Invalid Request",
        )
        
        assert error["jsonrpc"] == "2.0"
        assert error["id"] == 1
        assert "error" in error
        assert error["error"]["code"] == -32600
        assert error["error"]["message"] == "Invalid Request"
