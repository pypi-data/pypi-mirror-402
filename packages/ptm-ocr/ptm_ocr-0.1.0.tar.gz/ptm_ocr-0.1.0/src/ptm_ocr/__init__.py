"""
PTM-OCR: Batch OCR Processing for Thai Documents
"""

__version__ = "0.1.0"

from .core import (
    process_single_page,
    process_pdf_file,
    process_folder,
    get_pdf_page_count,
)

__all__ = [
    "__version__",
    "process_single_page",
    "process_pdf_file",
    "process_folder",
    "get_pdf_page_count",
]
