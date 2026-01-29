"""Unit tests for anymd package."""

import tempfile
from pathlib import Path
import pytest


class TestAnymd:
    """Tests for anymd core functionality."""

    def test_import(self):
        """Test that anymd can be imported."""
        from anymd import convert, detect_format, __version__
        assert callable(convert)
        assert callable(detect_format)
        assert __version__ == "1.1.0"

    def test_detect_format_pdf(self):
        """Test PDF format detection."""
        from anymd import detect_format
        assert detect_format("test.pdf") == "pdf"
        assert detect_format("TEST.PDF") == "pdf"

    def test_detect_format_epub(self):
        """Test EPUB format detection."""
        from anymd import detect_format
        assert detect_format("book.epub") == "epub"

    def test_detect_format_html(self):
        """Test HTML format detection."""
        from anymd import detect_format
        assert detect_format("page.html") == "html"
        assert detect_format("page.htm") == "html"

    def test_detect_format_docx(self):
        """Test DOCX format detection."""
        from anymd import detect_format
        assert detect_format("doc.docx") == "docx"

    def test_detect_format_pptx(self):
        """Test PPTX format detection."""
        from anymd import detect_format
        assert detect_format("slides.pptx") == "pptx"

    def test_detect_format_image(self):
        """Test image formats detection."""
        from anymd import detect_format
        assert detect_format("image.png") == "image"
        assert detect_format("photo.jpg") == "image"
        assert detect_format("scan.tiff") == "image"

    def test_detect_format_unknown(self):
        """Test unknown format returns 'unknown'."""
        from anymd import detect_format
        assert detect_format("file.xyz") == "unknown"

    def test_convert_text_file(self):
        """Test converting plain text file."""
        from anymd import convert
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Hello World\nThis is a test.")
            temp_path = f.name
        
        try:
            result = convert(temp_path)
            assert "Hello World" in result
            assert "This is a test" in result
        finally:
            Path(temp_path).unlink()

    def test_convert_html_file(self):
        """Test converting HTML file."""
        from anymd import convert
        
        html_content = """
        <html>
        <body>
        <h1>Title</h1>
        <p>Paragraph text.</p>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_path = f.name
        
        try:
            result = convert(temp_path)
            assert "# Title" in result
            assert "Paragraph text" in result
        finally:
            Path(temp_path).unlink()

    def test_convert_nonexistent_file_raises(self):
        """Test converting nonexistent file raises error."""
        from anymd import convert
        
        with pytest.raises(FileNotFoundError):
            convert("/nonexistent/file.pdf")

    def test_convert_unsupported_format_raises(self):
        """Test converting unsupported format raises error."""
        from anymd import convert
        
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                convert(temp_path)
        finally:
            Path(temp_path).unlink()


class TestAnymdCLI:
    """Tests for anymd CLI."""

    def test_create_parser(self):
        """Test CLI parser creation."""
        from anymd.cli import create_parser
        
        parser = create_parser()
        assert parser is not None

    def test_parser_version(self):
        """Test parser has version argument."""
        from anymd.cli import create_parser
        
        parser = create_parser()
        
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        
        assert exc_info.value.code == 0
