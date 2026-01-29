"""MCP Server for PDF to Markdown conversion with progress notifications."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Callable

from .engine import thinkpdfEngine, HAS_DOCLING


class thinkpdfMCPServer:
    """
    MCP Server for thinkpdf v2.

    Allows Cursor, Antigravity, and other MCP-compatible tools to
    convert and read PDFs directly.
    
    Features:
    - Progress notifications for long-running operations (throttled to 1/sec)
    - Fast pdfmd engine by default
    - Optional docling for high-quality table extraction
    """

    def __init__(self):
        self.engine = thinkpdfEngine()
        self._stdout = None
        self._last_progress_time = 0.0

    def _send_progress(self, token: str, progress: int, total: int, message: str, force: bool = False):
        """Send a progress notification to the client (throttled to max 1/second)."""
        if self._stdout is None:
            return
        
        now = time.time()
        if not force and (now - self._last_progress_time) < 1.0:
            return
        
        self._last_progress_time = now
        
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/progress",
            "params": {
                "progressToken": token,
                "progress": progress,
                "total": total,
                "message": message,
            }
        }
        try:
            self._stdout.write(json.dumps(notification) + "\n")
            self._stdout.flush()
        except Exception:
            pass

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle an incoming MCP request."""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        is_notification = request_id is None
        
        # Extract progress token from _meta if provided
        meta = params.get("_meta", {})
        progress_token = meta.get("progressToken")

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "initialized":
                return None
            elif method == "notifications/initialized":
                return None
            elif method == "tools/list":
                result = self._handle_list_tools()
            elif method == "tools/call":
                result = self._handle_tool_call(params, progress_token)
            elif method == "ping":
                result = {}
            elif method == "resources/list":
                result = {"resources": []}
            elif method == "prompts/list":
                result = {"prompts": []}
            else:
                if is_notification:
                    return None
                return self._error_response(
                    request_id, -32601, f"Method not found: {method}"
                )

            if is_notification:
                return None

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }

        except Exception as e:
            if is_notification:
                return None
            return self._error_response(request_id, -32603, str(e))

    def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request."""
        engine_info = "Docling (IBM)" if HAS_DOCLING else "pdfmd"

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": "thinkpdf",
                "version": "2.0.0",
                "description": f"PDF to Markdown converter powered by {engine_info}",
            },
        }

    def _handle_list_tools(self) -> Dict[str, Any]:
        """Return list of available tools."""
        return {
            "tools": [
                {
                    "name": "read_pdf",
                    "description": "Read a PDF file and return its content as Markdown. Fast by default, use engine='docling' for high-quality tables.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the PDF file",
                            },
                            "engine": {
                                "type": "string",
                                "description": "Conversion engine: 'pdfmd' (fast, default), 'docling' (high quality, slow), or 'auto'",
                                "enum": ["pdfmd", "docling", "auto"],
                                "default": "pdfmd",
                            },
                        },
                        "required": ["path"],
                    },
                },
                {
                    "name": "convert_pdf",
                    "description": "Convert a PDF file to Markdown and save to disk.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the PDF file",
                            },
                            "output": {
                                "type": "string",
                                "description": "Output path for markdown file (optional)",
                            },
                            "engine": {
                                "type": "string",
                                "description": "Conversion engine: 'pdfmd' (fast, default), 'docling' (high quality, slow), or 'auto'",
                                "enum": ["pdfmd", "docling", "auto"],
                                "default": "pdfmd",
                            },
                        },
                        "required": ["path"],
                    },
                },
                {
                    "name": "get_document_info",
                    "description": "Get information about a document (page count, size, etc.)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the document",
                            },
                        },
                        "required": ["path"],
                    },
                },
            ],
        }

    def _handle_tool_call(self, params: Dict[str, Any], progress_token: Optional[str] = None) -> Dict[str, Any]:
        """Handle a tool call with optional progress reporting."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name == "read_pdf":
            return self._tool_read_pdf(arguments, progress_token)
        elif tool_name == "convert_pdf":
            return self._tool_convert_pdf(arguments, progress_token)
        elif tool_name == "get_document_info":
            return self._tool_get_document_info(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _tool_read_pdf(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> Dict[str, Any]:
        """Read a PDF and return content as markdown."""
        path = args.get("path")
        engine_choice = args.get("engine", "pdfmd")
        if not path:
            raise ValueError("path is required")

        pdf_path = Path(path)
        if not pdf_path.exists():
            raise ValueError(f"File not found: {path}")

        if progress_token:
            self._send_progress(progress_token, 0, 100, f"Starting conversion of {pdf_path.name}...", force=True)

        def on_progress(done: int, total: int):
            if progress_token:
                pct = int(done * 100 / total) if total > 0 else 0
                self._send_progress(progress_token, pct, 100, f"Converting... {pct}%")

        temp_engine = thinkpdfEngine(engine=engine_choice)
        markdown = temp_engine.convert(pdf_path, progress_callback=on_progress)

        if progress_token:
            self._send_progress(progress_token, 100, 100, "Conversion complete", force=True)

        word_count = len(markdown.split())

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"# Content from: {pdf_path.name}\n\n**Words:** {word_count}\n\n---\n\n{markdown}",
                },
            ],
            "isError": False,
        }

    def _tool_convert_pdf(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> Dict[str, Any]:
        """Convert PDF to markdown file."""
        path = args.get("path")
        engine_choice = args.get("engine", "pdfmd")
        if not path:
            raise ValueError("path is required")

        pdf_path = Path(path)
        if not pdf_path.exists():
            raise ValueError(f"File not found: {path}")

        output = args.get("output")
        if output:
            output_path = Path(output)
        else:
            output_path = pdf_path.with_suffix(".md")

        if progress_token:
            self._send_progress(progress_token, 0, 100, f"Starting conversion of {pdf_path.name}...", force=True)

        def on_progress(done: int, total: int):
            if progress_token:
                pct = int(done * 100 / total) if total > 0 else 0
                self._send_progress(progress_token, pct, 100, f"Converting... {pct}%")

        temp_engine = thinkpdfEngine(engine=engine_choice)
        markdown = temp_engine.convert(pdf_path, output_path, progress_callback=on_progress)
        word_count = len(markdown.split())

        if progress_token:
            self._send_progress(progress_token, 100, 100, "Conversion complete", force=True)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Converted {pdf_path.name} to {output_path.name}\n"
                    f"Words: {word_count}\n"
                    f"Output: {output_path}",
                },
            ],
            "isError": False,
        }

    def _tool_get_document_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get document information."""
        path = args.get("path")
        if not path:
            raise ValueError("path is required")

        doc_path = Path(path)
        if not doc_path.exists():
            raise ValueError(f"File not found: {path}")

        info = self.engine.get_document_info(doc_path)

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(info, indent=2),
                },
            ],
            "isError": False,
        }

    def _error_response(
        self, request_id: Any, code: int, message: str
    ) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message,
            },
        }

    def run_stdio(self):
        """Run the server on stdio."""
        import io

        sys.stderr = io.StringIO()
        self._stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")
        sys.stdout = self._stdout

        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                request = json.loads(line)
                response = self.handle_request(request)

                if response is not None:
                    self._stdout.write(json.dumps(response) + "\n")
                    self._stdout.flush()

            except json.JSONDecodeError:
                continue
            except KeyboardInterrupt:
                break
            except Exception:
                continue


def main():
    """Entry point for MCP server."""
    server = thinkpdfMCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
