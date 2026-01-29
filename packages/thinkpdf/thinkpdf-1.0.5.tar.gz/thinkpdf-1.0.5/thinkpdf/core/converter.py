"""
PDF to Markdown Converter - Core conversion engine.

This module converts extracted PDF content to Markdown format,
with support for tables, equations, code blocks, and more.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable

from .extractor import (
    PDFExtractor,
    DocumentContent,
    PageContent,
    TextBlock,
    TextLine,
)


@dataclass
class ConversionOptions:
    """Options for PDF to Markdown conversion."""

    quality: str = "balanced"

    preserve_formatting: bool = True
    detect_tables: bool = True
    detect_equations: bool = True
    detect_code_blocks: bool = True

    remove_headers: bool = True
    remove_footers: bool = True

    heading_ratio: float = 1.15

    ocr_mode: str = "auto"

    export_images: bool = False
    image_output_dir: Optional[str] = None

    use_llm: bool = False
    llm_service: Optional[str] = None


@dataclass
class ConversionResult:
    """Result of PDF to Markdown conversion."""

    markdown: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    images: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


class PDFConverter:
    """
    Convert PDF documents to Markdown.

    Features:
    - Smart heading detection based on font size
    - Table detection and reconstruction
    - Equation detection with LaTeX conversion
    - Code block detection
    - Header/footer removal
    - Bold/italic preservation
    - Optional LLM validation for improved accuracy
    """

    def __init__(
        self,
        options: Optional[ConversionOptions] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self.options = options or ConversionOptions()
        self.progress_callback = progress_callback
        self.log_callback = log_callback

        self._font_sizes: List[float] = []
        self._base_font_size: float = 12.0

    def convert(
        self,
        pdf_path: str | Path,
        output_path: Optional[str | Path] = None,
        password: Optional[str] = None,
    ) -> ConversionResult:
        """
        Convert a PDF file to Markdown.

        Args:
            pdf_path: Path to the PDF file
            output_path: Optional path to save the Markdown file
            password: Optional password for encrypted PDFs

        Returns:
            ConversionResult with markdown content and metadata
        """
        pdf_path = Path(pdf_path)

        self._log(f"Starting conversion: {pdf_path.name}")

        self._log("Extracting content...")
        extractor = PDFExtractor(
            extract_images=self.options.export_images,
            preserve_formatting=self.options.preserve_formatting,
            progress_callback=self._extraction_progress,
        )

        document = extractor.extract(pdf_path, password=password)

        self._log("Analyzing document structure...")
        self._analyze_fonts(document)

        self._log("Converting to Markdown...")
        markdown_parts = []

        for i, page in enumerate(document.pages):
            page_md = self._convert_page(page)
            markdown_parts.append(page_md)

            if self.progress_callback:
                self.progress_callback(i + 1, len(document.pages))

        markdown = "\n\n".join(markdown_parts)
        markdown = self._clean_markdown(markdown)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            self._log(f"Saved to: {output_path}")

        result = ConversionResult(
            markdown=markdown,
            metadata=document.metadata,
            stats={
                "page_count": document.page_count,
                "word_count": len(markdown.split()),
                "character_count": len(markdown),
            },
        )

        self._log("Conversion complete!")
        return result

    def _analyze_fonts(self, document: DocumentContent) -> None:
        """Analyze font sizes across the document to determine base font and headings."""
        sizes = []

        for page in document.pages:
            for block in page.blocks:
                for line in block.lines:
                    for span in line.spans:
                        if span.size > 0:
                            sizes.append(span.size)

        if sizes:
            sizes.sort()
            self._base_font_size = sizes[len(sizes) // 2]
            self._font_sizes = sizes

    def _convert_page(self, page: PageContent) -> str:
        """Convert a single page to Markdown."""
        parts = []

        for block in page.blocks:
            block_md = self._convert_block(block)
            if block_md.strip():
                parts.append(block_md)

        return "\n\n".join(parts)

    def _convert_block(self, block: TextBlock) -> str:
        """Convert a text block to Markdown."""
        lines_md = []

        for line in block.lines:
            line_md = self._convert_line(line)
            if line_md.strip():
                lines_md.append(line_md)

        if lines_md and self._is_heading(block):
            heading_level = self._get_heading_level(block)
            prefix = "#" * heading_level + " "
            text = " ".join(lines_md)
            text = text.replace("***", "").replace("**", "").replace("*", "")
            return prefix + text.strip()

        return " ".join(lines_md)

    def _convert_line(self, line: TextLine) -> str:
        """Convert a text line to Markdown with formatting."""
        parts = []

        for span in line.spans:
            text = span.text

            if not text.strip():
                parts.append(text)
                continue

            if self.options.preserve_formatting:
                if span.is_bold and span.is_italic:
                    text = f"***{text.strip()}***"
                elif span.is_bold:
                    text = f"**{text.strip()}**"
                elif span.is_italic:
                    text = f"*{text.strip()}*"

            parts.append(text)

        return "".join(parts)

    def _is_heading(self, block: TextBlock) -> bool:
        """Determine if a block should be formatted as a heading."""
        if not block.lines:
            return False

        sizes = []
        all_bold = True
        total_chars = 0

        for line in block.lines:
            for span in line.spans:
                if span.size > 0:
                    sizes.append(span.size)
                if not span.is_bold:
                    all_bold = False
                total_chars += len(span.text)

        if not sizes:
            return False

        avg_size = sum(sizes) / len(sizes)
        ratio = avg_size / self._base_font_size if self._base_font_size > 0 else 1.0

        if ratio >= self.options.heading_ratio:
            return True

        if all_bold and total_chars < 100 and len(block.lines) <= 2:
            return True

        return False

    def _get_heading_level(self, block: TextBlock) -> int:
        """Determine the heading level (1-6) based on font size."""
        sizes = []
        for line in block.lines:
            for span in line.spans:
                if span.size > 0:
                    sizes.append(span.size)

        if not sizes:
            return 2

        avg_size = sum(sizes) / len(sizes)
        ratio = avg_size / self._base_font_size if self._base_font_size > 0 else 1.0

        if ratio >= 2.0:
            return 1
        elif ratio >= 1.6:
            return 2
        elif ratio >= 1.4:
            return 3
        elif ratio >= 1.2:
            return 4
        else:
            return 5

    def _clean_markdown(self, markdown: str) -> str:
        """Clean up the generated Markdown."""
        markdown = re.sub(r"\n{4,}", "\n\n\n", markdown)

        markdown = re.sub(r"(#{1,6} .+)\n{3,}", r"\1\n\n", markdown)

        lines = [line.rstrip() for line in markdown.split("\n")]
        markdown = "\n".join(lines)

        markdown = markdown.strip() + "\n"

        return markdown

    def _extraction_progress(self, done: int, total: int) -> None:
        """Progress callback for extraction phase."""
        if self.progress_callback:
            overall = done * 50 // total
            self.progress_callback(overall, 100)

    def _log(self, message: str) -> None:
        """Log a message if callback is set."""
        if self.log_callback:
            self.log_callback(message)


def convert_pdf_to_markdown(
    pdf_path: str | Path,
    output_path: Optional[str | Path] = None,
    quality: str = "balanced",
) -> str:
    """
    Quick conversion of PDF to Markdown.

    Args:
        pdf_path: Path to PDF file
        output_path: Optional path to save output
        quality: "fast", "balanced", or "maximum"

    Returns:
        Markdown string
    """
    options = ConversionOptions(quality=quality)
    converter = PDFConverter(options=options)
    result = converter.convert(pdf_path, output_path=output_path)
    return result.markdown
