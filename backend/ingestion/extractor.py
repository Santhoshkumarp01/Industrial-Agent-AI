"""
PDF extraction using PyMuPDF for lightweight, fast processing.

Features:
- Text block extraction with structure detection
- Preserves headings and paragraphs
- Lightweight - no heavy ML dependencies
- Fast processing suitable for production
"""

import logging
from typing import List

from models.schemas import ExtractedBlock

logger = logging.getLogger(__name__)


def extract_blocks(file_path: str, doc_id: str, doc_name: str, equipment_tag: str) -> List[ExtractedBlock]:
    """
    Extract text blocks from PDF using PyMuPDF.
    
    Args:
        file_path: Path to the PDF file
        doc_id: UUID for this document
        doc_name: Original filename
        equipment_tag: Equipment identifier
    
    Returns:
        List of ExtractedBlock objects
    """
    # Use PyMuPDF extractor
    from ingestion.extractor_legacy import extract_blocks_pymupdf
    return extract_blocks_pymupdf(file_path, doc_id, doc_name, equipment_tag)
