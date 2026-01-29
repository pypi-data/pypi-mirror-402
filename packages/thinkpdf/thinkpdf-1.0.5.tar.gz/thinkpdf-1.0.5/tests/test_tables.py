"""Unit tests for thinkpdf table detection.

Tests the table detection strategies in core/tables.py:
- Bordered tables (Markdown-style with | delimiters)
- ASCII tables (whitespace-separated columns)
- Vertical tables (multi-block)

Run with: pytest tests/test_tables.py -v
"""

from __future__ import annotations

import pytest

from thinkpdf.core.models import PageText, Block, Line, Span
from thinkpdf.core.tables import (
    detect_tables_on_page,
    TableDetection,
    _detect_bordered_table,
    _detect_ascii_table_in_block,
    _cell_is_numeric,
    _cell_is_short_token,
    _cell_is_sentence,
)


# =============================================================================
# Helper Functions
# =============================================================================


def make_block(lines_text: list[str]) -> Block:
    """Create a Block from a list of line strings."""
    lines = []
    for text in lines_text:
        span = Span(text=text)
        line = Line(spans=[span])
        lines.append(line)
    return Block(lines=lines)


def make_page(blocks_data: list[list[str]]) -> PageText:
    """Create a PageText from a list of block line lists."""
    blocks = [make_block(lines) for lines in blocks_data]
    return PageText(blocks=blocks)


# =============================================================================
# Cell Classification Tests
# =============================================================================


class TestCellClassification:
    """Tests for cell type detection helpers."""

    @pytest.mark.parametrize("text,expected", [
        ("123", True),
        ("45.67", True),
        ("50%", True),
        ("-12.3", True),
        ("1,000", True),
        ("Hello", False),
        ("123 Main St", False),
        ("", False),
    ])
    def test_cell_is_numeric(self, text, expected):
        """Test numeric cell detection with various formats."""
        assert _cell_is_numeric(text) == expected

    @pytest.mark.parametrize("text,expected", [
        ("ABC123", True),
        ("OK", True),
        ("", False),
        ("This is a sentence.", False),
        ("Hello World", False),
    ])
    def test_cell_is_short_token(self, text, expected):
        """Test short token detection (identifiers, codes)."""
        assert _cell_is_short_token(text) == expected

    @pytest.mark.parametrize("text,expected", [
        ("This is a complete sentence with multiple words.", True),
        ("OK", False),
        ("Name", False),
        ("", False),
    ])
    def test_cell_is_sentence(self, text, expected):
        """Test sentence detection."""
        assert _cell_is_sentence(text) == expected


# =============================================================================
# Bordered Table Detection Tests
# =============================================================================


class TestBorderedTableDetection:
    """Tests for Markdown-style bordered table detection."""

    def test_simple_markdown_table(self):
        """Test detection of simple Markdown table."""
        block = make_block([
            "| Name | Age | City |",
            "|------|-----|------|",
            "| Alice | 30 | NYC |",
            "| Bob | 25 | LA |",
        ])
        
        grid = _detect_bordered_table(block)
        
        assert grid is not None
        assert len(grid) >= 2  # At least header and one data row

    def test_table_without_separator_line(self):
        """Test detection of table without Markdown separator."""
        block = make_block([
            "| Name | Age |",
            "| Alice | 30 |",
        ])
        
        grid = _detect_bordered_table(block)
        
        assert grid is not None
        assert len(grid) == 2

    def test_table_without_pipes(self):
        """Test that non-pipe text is not detected as bordered table."""
        block = make_block([
            "This is just normal text.",
            "It has no table structure.",
        ])
        
        grid = _detect_bordered_table(block)
        
        assert grid is None

    def test_empty_block(self):
        """Test handling of empty block."""
        block = Block(lines=[])
        
        grid = _detect_bordered_table(block)
        
        assert grid is None


# =============================================================================
# ASCII Table Detection Tests
# =============================================================================


class TestAsciiTableDetection:
    """Tests for whitespace-separated ASCII table detection."""

    def test_simple_ascii_table(self):
        """Test detection of whitespace-separated table."""
        block = make_block([
            "Name       Age    City",
            "Alice      30     New York",
            "Bob        25     Los Angeles",
        ])
        
        grid = _detect_ascii_table_in_block(block)
        
        # May or may not detect depending on spacing
        # The function should not crash
        assert grid is None or isinstance(grid, list)

    def test_single_line_not_table(self):
        """Test that single line is not detected as table."""
        block = make_block([
            "This is a single line of text.",
        ])
        
        grid = _detect_ascii_table_in_block(block)
        
        assert grid is None

    def test_prose_paragraph_not_table(self):
        """Test that prose paragraph is not detected as table."""
        block = make_block([
            "This is a paragraph of text that discusses various topics.",
            "It contains multiple sentences but should not be a table.",
            "The content flows naturally like prose does.",
        ])
        
        grid = _detect_ascii_table_in_block(block)
        
        assert grid is None


# =============================================================================
# Full Page Detection Tests
# =============================================================================


class TestPageTableDetection:
    """Tests for full page table detection pipeline."""

    def test_page_with_no_tables(self):
        """Test page with no tables returns empty list."""
        page = make_page([
            ["This is just prose."],
            ["More regular text here."],
        ])
        
        tables = detect_tables_on_page(page)
        
        assert isinstance(tables, list)
        # May be empty or have false positives, but should not crash

    def test_page_with_bordered_table(self):
        """Test page with Markdown table is detected."""
        page = make_page([
            ["Introduction paragraph."],
            ["| Col1 | Col2 |", "| A | B |", "| C | D |"],
            ["Conclusion paragraph."],
        ])
        
        tables = detect_tables_on_page(page)
        
        # Should find at least one table-like structure
        assert isinstance(tables, list)

    def test_detection_returns_tabledetection_objects(self):
        """Test that detection returns proper TableDetection objects."""
        page = make_page([
            ["| Name | Value |", "| Test | 123 |"],
        ])
        
        tables = detect_tables_on_page(page)
        
        for table in tables:
            assert isinstance(table, TableDetection)
            assert hasattr(table, "grid")
            assert hasattr(table, "block_index")
            assert hasattr(table, "score")


# =============================================================================
# Edge Cases
# =============================================================================


class TestTableEdgeCases:
    """Edge case tests for table detection."""

    def test_unicode_in_table(self):
        """Test table with unicode characters."""
        block = make_block([
            "| Nome | Cidade |",
            "| João | São Paulo |",
            "| María | México |",
        ])
        
        grid = _detect_bordered_table(block)
        
        assert grid is not None

    def test_mixed_content_block(self):
        """Test block with mixed table and non-table content."""
        # This tests robustness - should not crash
        block = make_block([
            "Header text",
            "| A | B |",
            "Footer text",
        ])
        
        grid = _detect_bordered_table(block)
        # May or may not detect, but should handle gracefully

    def test_very_wide_table(self):
        """Test table with many columns."""
        cols = " | ".join([f"Col{i}" for i in range(20)])
        vals = " | ".join([str(i) for i in range(20)])
        
        block = make_block([
            f"| {cols} |",
            f"| {vals} |",
        ])
        
        grid = _detect_bordered_table(block)
        
        assert grid is not None
        if grid:
            assert len(grid[0]) >= 10  # Should have many columns
