"""thinkpdf - PDF to Markdown converter."""

__version__ = "1.0.5"

from thinkpdf.engine import convert
from thinkpdf.core.extractor import PDFExtractor
from thinkpdf.core.converter import PDFConverter

__all__ = ["convert", "PDFExtractor", "PDFConverter", "__version__"]
