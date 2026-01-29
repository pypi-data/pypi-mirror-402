"""PDF to Markdown conversion engine with hybrid Docling/pdfmd support."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Union, Callable
from datetime import datetime

from .logger import logger
from . import __version__

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    HAS_DOCLING = True
except ImportError:
    HAS_DOCLING = False
    DocumentConverter = None

try:
    from .core.pipeline import pdf_to_markdown as pdfmd_convert
    from .core.models import Options as PdfmdOptions

    HAS_PDFMD = True
except ImportError:
    HAS_PDFMD = False

try:
    import fitz

    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


def has_encoding_issues(text: str) -> bool:
    """Check if extracted text has encoding problems.

    Detects:
    - Replacement characters (U+FFFD)
    - High ratio of non-printable characters
    - Common encoding corruption patterns
    """
    if not text:
        return False

    replacement_count = text.count("\ufffd")
    if replacement_count > len(text) * 0.01:  # More than 1% replacement chars
        return True

    non_printable = sum(1 for c in text if not c.isprintable() and c not in "\n\r\t")
    if non_printable > len(text) * 0.05:  # More than 5% non-printable
        return True

    return False


def analyze_pdf_complexity(file_path: Path) -> dict:
    """
    Analyze PDF to determine optimal conversion engine.

    Returns dict with:
    - page_count: number of pages
    - has_images: True if PDF contains images
    - is_scanned: True if PDF appears to be scanned (little text, many images)
    - has_tables: True if PDF likely contains tables
    - has_encoding_issues: True if text extraction has encoding problems
    - recommended_engine: 'docling' or 'pdfmd'
    """
    if not HAS_PYMUPDF:
        return {"recommended_engine": "docling"}

    try:
        doc = fitz.open(str(file_path))
        page_count = len(doc)

        total_text_chars = 0
        total_images = 0
        table_indicators = 0
        encoding_issues = False
        sample_text = ""

        sample_pages = min(5, page_count)

        for i in range(sample_pages):
            page = doc[i]
            text = page.get_text()
            sample_text += text
            total_text_chars += len(text)
            images = page.get_images()
            total_images += len(images)

            drawings = page.get_drawings()
            lines = [
                d
                for d in drawings
                if d.get("items")
                and any(item[0] in ("l", "re") for item in d.get("items", []))
            ]
            if len(lines) > 10:
                table_indicators += 1

            blocks = page.get_text("dict")["blocks"]
            if len(blocks) > 5:
                table_indicators += 1

        doc.close()

        encoding_issues = has_encoding_issues(sample_text)

        avg_chars_per_page = total_text_chars / sample_pages if sample_pages > 0 else 0
        avg_images_per_page = total_images / sample_pages if sample_pages > 0 else 0

        is_scanned = avg_chars_per_page < 100 and avg_images_per_page > 0
        has_tables = table_indicators >= 2
        has_images = total_images > 0

        if encoding_issues:
            recommended_engine = "docling"
        elif is_scanned:
            recommended_engine = "docling"
        elif has_tables:
            recommended_engine = "docling"
        elif page_count > 50 and not has_tables:
            recommended_engine = "pdfmd"
        elif page_count <= 10 and not has_tables and not is_scanned:
            recommended_engine = "pdfmd"
        else:
            recommended_engine = "docling"

        return {
            "page_count": page_count,
            "has_images": has_images,
            "is_scanned": is_scanned,
            "has_tables": has_tables,
            "has_encoding_issues": encoding_issues,
            "avg_chars_per_page": int(avg_chars_per_page),
            "recommended_engine": recommended_engine,
        }

    except Exception as e:
        return {"recommended_engine": "docling", "error": str(e)}


class thinkpdfEngine:
    """
    Unified PDF to Markdown conversion engine.

    Uses:
    - Docling (IBM) for maximum quality when available
    - pdfmd as fallback for simpler documents
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        use_cache: bool = True,
        engine: str = "pdfmd",  # "pdfmd" (fast), "docling" (quality), "auto"
    ):
        self.cache_dir = cache_dir or Path.home() / ".thinkpdf" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.use_cache = use_cache
        self.engine = engine
        self.docling_pipeline = None
        self.docling_model = None
        self._docling_converter = None

        logger.info(f"thinkpdf {__version__} - Hybrid PDF Engine")

        if HAS_DOCLING and engine in ("auto", "docling"):
            self._init_docling()

    def _init_docling(self):
        """Initialize Docling converter with optimal settings."""
        try:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.do_table_structure = True

            self._docling_converter = DocumentConverter(
                allowed_formats=[
                    InputFormat.PDF,
                    InputFormat.DOCX,
                    InputFormat.PPTX,
                    InputFormat.HTML,
                    InputFormat.IMAGE,
                ]
            )
        except Exception as e:
            logger.warning(f"Could not initialize Docling: {e}")
            self._docling_converter = None

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for caching."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    def get_cached(self, file_path: Path) -> Optional[str]:
        """Get cached conversion if available and valid."""
        if not self.use_cache:
            return None

        file_hash = self.get_file_hash(file_path)
        cache_file = self.cache_dir / f"{file_hash}.md"
        meta_file = self.cache_dir / f"{file_hash}.json"

        if cache_file.exists() and meta_file.exists():
            try:
                with open(meta_file, "r") as f:
                    meta = json.load(f)

                source_mtime = file_path.stat().st_mtime
                if meta.get("source_mtime") == source_mtime:
                    return cache_file.read_text(encoding="utf-8")
            except Exception:
                pass

        return None

    def cache_result(self, file_path: Path, markdown: str):
        """Cache the conversion result."""
        if not self.use_cache:
            return

        file_hash = self.get_file_hash(file_path)
        cache_file = self.cache_dir / f"{file_hash}.md"
        meta_file = self.cache_dir / f"{file_hash}.json"

        cache_file.write_text(markdown, encoding="utf-8")

        meta = {
            "source_file": str(file_path),
            "source_mtime": file_path.stat().st_mtime,
            "converted_at": datetime.now().isoformat(),
            "engine": self.engine,
        }
        with open(meta_file, "w") as f:
            json.dump(meta, f)

    def convert(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """
        Convert a document to Markdown.

        Args:
            input_path: Path to PDF, DOCX, PPTX, or HTML file
            output_path: Optional path to save markdown
            progress_callback: Optional callback for progress updates

        Returns:
            Markdown content as string
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        cached = self.get_cached(input_path)
        if cached:
            if output_path:
                Path(output_path).write_text(cached, encoding="utf-8")
            return cached

        use_engine = self.engine

        if use_engine == "auto" and input_path.suffix.lower() == ".pdf":
            analysis = analyze_pdf_complexity(input_path)
            use_engine = analysis.get("recommended_engine", "docling")

        if use_engine == "docling" and self._docling_converter:
            markdown = self._convert_with_docling(input_path, progress_callback)
        elif (
            use_engine == "pdfmd" and HAS_PDFMD and input_path.suffix.lower() == ".pdf"
        ):
            markdown = self._convert_with_pdfmd(input_path, progress_callback)
        elif self._docling_converter:
            markdown = self._convert_with_docling(input_path, progress_callback)
        elif HAS_PDFMD and input_path.suffix.lower() == ".pdf":
            markdown = self._convert_with_pdfmd(input_path, progress_callback)
        else:
            raise RuntimeError(
                "No conversion engine available. Install docling or pdfmd."
            )

        if not markdown.strip():
            pass

        self.cache_result(input_path, markdown)

        if output_path:
            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(markdown, encoding="utf-8")

        return markdown

    def _convert_with_docling(
        self,
        input_path: Path,
        progress_callback: Optional[Callable] = None,
    ) -> str:
        """Convert using IBM Docling (highest quality)."""
        if progress_callback:
            progress_callback(0, 100)

        result = self._docling_converter.convert(str(input_path))

        if progress_callback:
            progress_callback(50, 100)

        markdown = result.document.export_to_markdown()

        if progress_callback:
            progress_callback(100, 100)

        return markdown

    def _convert_with_pdfmd(
        self,
        input_path: Path,
        progress_callback: Optional[Callable] = None,
    ) -> str:
        """Convert using pdfmd (fallback)."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            options = PdfmdOptions()
            pdfmd_convert(
                input_pdf=str(input_path),
                output_md=tmp_path,
                options=options,
                progress_cb=progress_callback,
            )

            return Path(tmp_path).read_text(encoding="utf-8")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def get_document_info(self, input_path: Union[str, Path]) -> dict:
        """Get information about a document."""
        input_path = Path(input_path)

        return {
            "filename": input_path.name,
            "path": str(input_path.absolute()),
            "size_bytes": input_path.stat().st_size,
            "size_mb": round(input_path.stat().st_size / (1024 * 1024), 2),
            "extension": input_path.suffix.lower(),
            "file_hash": self.get_file_hash(input_path),
            "has_docling": HAS_DOCLING,
            "has_pdfmd": HAS_PDFMD,
        }


_engine: Optional[thinkpdfEngine] = None


def get_engine() -> thinkpdfEngine:
    """Get or create the global engine instance."""
    global _engine
    if _engine is None:
        _engine = thinkpdfEngine()
    return _engine


def convert(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
) -> str:
    """Quick conversion function."""
    return get_engine().convert(input_path, output_path)
