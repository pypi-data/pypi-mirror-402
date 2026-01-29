"""
PDF Extractor - Core extraction engine using PyMuPDF.

This module handles the low-level extraction of content from PDF files,
including text, images, tables, and metadata.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
import fitz


@dataclass
class TextSpan:
    """A span of text with formatting information."""

    text: str
    font: str = ""
    size: float = 0.0
    flags: int = 0
    color: int = 0

    @property
    def is_bold(self) -> bool:
        return bool(self.flags & 2**4)

    @property
    def is_italic(self) -> bool:
        return bool(self.flags & 2**1)


@dataclass
class TextLine:
    """A line of text containing multiple spans."""

    spans: List[TextSpan] = field(default_factory=list)
    bbox: tuple = (0, 0, 0, 0)

    @property
    def text(self) -> str:
        return "".join(span.text for span in self.spans)


@dataclass
class TextBlock:
    """A block of text containing multiple lines."""

    lines: List[TextLine] = field(default_factory=list)
    bbox: tuple = (0, 0, 0, 0)
    block_type: str = "text"

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)


@dataclass
class PageContent:
    """Content extracted from a single page."""

    page_number: int
    blocks: List[TextBlock] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0

    @property
    def text(self) -> str:
        return "\n\n".join(block.text for block in self.blocks)


@dataclass
class DocumentContent:
    """Content extracted from an entire document."""

    pages: List[PageContent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_hash: str = ""

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)

    @property
    def page_count(self) -> int:
        return len(self.pages)


class PDFExtractor:
    """
    Extract content from PDF files using PyMuPDF.

    Features:
    - Fast text extraction with formatting preservation
    - Image extraction with metadata
    - Support for password-protected PDFs
    - Progress callbacks for large documents
    """

    def __init__(
        self,
        extract_images: bool = False,
        preserve_formatting: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ):
        self.extract_images = extract_images
        self.preserve_formatting = preserve_formatting
        self.progress_callback = progress_callback

    def extract(
        self,
        pdf_path: str | Path,
        password: Optional[str] = None,
        page_range: Optional[tuple[int, int]] = None,
    ) -> DocumentContent:
        """
        Extract content from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            password: Optional password for encrypted PDFs
            page_range: Optional (start, end) page range (0-indexed, inclusive)

        Returns:
            DocumentContent with extracted pages and metadata
        """
        pdf_path = Path(pdf_path)

        file_hash = self._calculate_hash(pdf_path)

        doc = fitz.open(pdf_path)

        if doc.is_encrypted:
            if password:
                doc.authenticate(password)
            else:
                raise ValueError("PDF is encrypted and no password provided")

        start_page = 0
        end_page = doc.page_count - 1

        if page_range:
            start_page = max(0, page_range[0])
            end_page = min(doc.page_count - 1, page_range[1])

        metadata = {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", ""),
            "page_count": doc.page_count,
            "file_path": str(pdf_path),
        }

        pages = []
        total_pages = end_page - start_page + 1

        for i, page_num in enumerate(range(start_page, end_page + 1)):
            page = doc[page_num]
            page_content = self._extract_page(page, page_num)
            pages.append(page_content)

            if self.progress_callback:
                self.progress_callback(i + 1, total_pages)

        doc.close()

        return DocumentContent(
            pages=pages,
            metadata=metadata,
            file_hash=file_hash,
        )

    def _extract_page(self, page: fitz.Page, page_number: int) -> PageContent:
        """Extract content from a single page."""
        blocks = []
        images = []

        rect = page.rect
        width, height = rect.width, rect.height

        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:
                text_block = self._parse_text_block(block)
                if text_block.text.strip():
                    blocks.append(text_block)
            elif block.get("type") == 1 and self.extract_images:
                image_info = self._extract_image_info(block, page)
                if image_info:
                    images.append(image_info)

        return PageContent(
            page_number=page_number,
            blocks=blocks,
            images=images,
            width=width,
            height=height,
        )

    def _parse_text_block(self, block: dict) -> TextBlock:
        """Parse a PyMuPDF text block into our format."""
        lines = []
        bbox = block.get("bbox", (0, 0, 0, 0))

        for line in block.get("lines", []):
            spans = []
            line_bbox = line.get("bbox", (0, 0, 0, 0))

            for span in line.get("spans", []):
                text_span = TextSpan(
                    text=span.get("text", ""),
                    font=span.get("font", ""),
                    size=span.get("size", 0.0),
                    flags=span.get("flags", 0),
                    color=span.get("color", 0),
                )
                spans.append(text_span)

            if spans:
                lines.append(TextLine(spans=spans, bbox=line_bbox))

        return TextBlock(lines=lines, bbox=bbox, block_type="text")

    def _extract_image_info(
        self, block: dict, page: fitz.Page
    ) -> Optional[Dict[str, Any]]:
        """Extract image information from a block."""
        try:
            bbox = block.get("bbox", (0, 0, 0, 0))
            return {
                "bbox": bbox,
                "width": bbox[2] - bbox[0],
                "height": bbox[3] - bbox[1],
                "page": page.number,
            }
        except Exception:
            return None

    def _calculate_hash(self, pdf_path: Path) -> str:
        """Calculate SHA256 hash of the PDF file."""
        sha256 = hashlib.sha256()
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()


def extract_pdf(
    pdf_path: str | Path,
    password: Optional[str] = None,
    extract_images: bool = False,
) -> DocumentContent:
    """
    Quick extraction of PDF content.

    Args:
        pdf_path: Path to PDF file
        password: Optional password
        extract_images: Whether to extract image info

    Returns:
        DocumentContent with extracted content
    """
    extractor = PDFExtractor(extract_images=extract_images)
    return extractor.extract(pdf_path, password=password)
