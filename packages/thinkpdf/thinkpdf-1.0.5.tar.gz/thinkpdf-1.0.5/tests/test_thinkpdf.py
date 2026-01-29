"""Unit tests for thinkpdf package.

Run with: pytest tests/ -v
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest


class TestEngine:
    """Tests for the conversion engine."""

    def test_import_convert(self):
        """Test that convert function can be imported."""
        from thinkpdf import convert
        assert callable(convert)

    def test_import_extractor(self):
        """Test that PDFExtractor can be imported."""
        from thinkpdf import PDFExtractor
        assert PDFExtractor is not None

    def test_import_converter(self):
        """Test that PDFConverter can be imported."""
        from thinkpdf import PDFConverter
        assert PDFConverter is not None

    def test_version_exists(self):
        """Test that version is defined."""
        from thinkpdf import __version__
        assert __version__
        assert isinstance(__version__, str)

    def test_engine_initialization(self):
        """Test that engine can be initialized."""
        from thinkpdf.engine import thinkpdfEngine
        
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = thinkpdfEngine(
                cache_dir=Path(tmpdir) / "cache",
                use_cache=False,
                engine="pdfmd",
            )
            assert engine is not None
            assert engine.engine == "pdfmd"

    def test_engine_file_hash(self):
        """Test file hash calculation."""
        from thinkpdf.engine import thinkpdfEngine
        
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = thinkpdfEngine(
                cache_dir=Path(tmpdir) / "cache",
                use_cache=False,
            )
            
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello World")
            
            hash1 = engine.get_file_hash(test_file)
            hash2 = engine.get_file_hash(test_file)
            
            assert hash1 == hash2
            assert len(hash1) == 16

    def test_convert_nonexistent_file_raises(self):
        """Test that converting nonexistent file raises error."""
        from thinkpdf import convert
        
        with pytest.raises(FileNotFoundError):
            convert("/nonexistent/file.pdf")


class TestAnalyze:
    """Tests for PDF analysis functions."""

    def test_has_encoding_issues_clean(self):
        """Test encoding detection with clean text."""
        from thinkpdf.engine import has_encoding_issues
        
        assert has_encoding_issues("Hello World") is False
        assert has_encoding_issues("Olá Mundo") is False

    def test_has_encoding_issues_corrupted(self):
        """Test encoding detection with corrupted text."""
        from thinkpdf.engine import has_encoding_issues
        
        corrupted = "Hello \ufffd\ufffd\ufffd World"
        assert has_encoding_issues(corrupted) is True

    def test_has_encoding_issues_empty(self):
        """Test encoding detection with empty text."""
        from thinkpdf.engine import has_encoding_issues
        
        assert has_encoding_issues("") is False
        assert has_encoding_issues(None) is False


class TestCache:
    """Tests for cache functionality."""

    def test_cache_manager_init(self):
        """Test cache manager initialization."""
        from thinkpdf.cache.cache_manager import CacheManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=Path(tmpdir))
            assert cache is not None

    def test_cache_stats(self):
        """Test cache statistics."""
        from thinkpdf.cache.cache_manager import CacheManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=Path(tmpdir))
            stats = cache.get_stats()
            
            assert "entries" in stats
            assert "total_size_mb" in stats
            assert stats["entries"] == 0


class TestLogger:
    """Tests for logging module."""

    def test_logger_import(self):
        """Test logger can be imported."""
        from thinkpdf.logger import logger, get_logger
        assert logger is not None
        assert callable(get_logger)

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        from thinkpdf.logger import get_logger
        import logging
        
        log = get_logger("test")
        assert isinstance(log, logging.Logger)


class TestCLI:
    """Tests for CLI functionality."""

    def test_create_parser(self):
        """Test argument parser creation."""
        from thinkpdf.cli import create_parser
        
        parser = create_parser()
        assert parser is not None

    def test_parser_version(self):
        """Test parser has version argument."""
        from thinkpdf.cli import create_parser
        
        parser = create_parser()
        
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        
        assert exc_info.value.code == 0

    def test_parser_help(self):
        """Test parser has help."""
        from thinkpdf.cli import create_parser
        
        parser = create_parser()
        
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        
        assert exc_info.value.code == 0


class TestModels:
    """Tests for data models."""

    def test_options_default(self):
        """Test Options with defaults."""
        from thinkpdf.core.models import Options
        
        opts = Options()
        assert opts.ocr_mode in ("off", "auto", None)

    def test_pagetext_creation(self):
        """Test PageText model creation."""
        from thinkpdf.core.models import PageText, Block, Line, Span
        
        span = Span(text="Hello")
        line = Line(spans=[span])
        block = Block(lines=[line])
        page = PageText(blocks=[block])
        
        assert len(page.blocks) == 1
        assert len(page.blocks[0].lines) == 1
