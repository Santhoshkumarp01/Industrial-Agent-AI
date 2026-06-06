"""
Tests for ingestion/extractor.py

These tests use a synthetic in-memory PDF created with PyMuPDF so no fixture
files are needed. Install PyMuPDF (pymupdf) before running.
"""

import tempfile
import os
import pytest
import fitz  # PyMuPDF

from ingestion.extractor import extract_blocks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_simple_pdf(tmp_path: str, content_pages: list[dict]) -> str:
    """
    Create a minimal PDF with one text block per page.

    content_pages: list of dicts with keys:
        - text: str
        - fontsize: float  (default 11)
        - bold: bool       (default False)
    """
    doc = fitz.open()
    for page_cfg in content_pages:
        page = doc.new_page(width=595, height=842)
        text = page_cfg["text"]
        fontsize = page_cfg.get("fontsize", 11)
        # Insert text as a simple text block
        page.insert_text(
            (50, 100),
            text,
            fontsize=fontsize,
            color=(0, 0, 0),
        )
    pdf_path = os.path.join(tmp_path, "test_doc.pdf")
    doc.save(pdf_path)
    doc.close()
    return pdf_path


# ---------------------------------------------------------------------------
# Test: blocks have non-empty bbox tuples
# ---------------------------------------------------------------------------

def test_blocks_have_non_empty_bbox(tmp_path):
    """Every extracted block must have a non-empty bbox tuple with 4 elements."""
    pdf_path = _create_simple_pdf(str(tmp_path), [
        {"text": "This is a simple paragraph with enough words to be a paragraph block."},
        {"text": "Second page paragraph about equipment maintenance procedures."},
    ])

    blocks = extract_blocks(pdf_path, doc_id="test-doc-id", doc_name="test.pdf", equipment_tag="Rolling Mill")

    assert len(blocks) > 0, "Should extract at least one block"
    for block in blocks:
        assert block.bbox is not None, "bbox must not be None"
        assert len(block.bbox) == 4, f"bbox must have 4 elements, got {len(block.bbox)}"
        # bbox values should be numeric (not all zeros in a real page)
        x0, y0, x1, y1 = block.bbox
        # x1 > x0 and y1 > y0 for any real text block
        assert x1 >= x0, f"x1 ({x1}) must be >= x0 ({x0})"
        assert y1 >= y0, f"y1 ({y1}) must be >= y0 ({y0})"


# ---------------------------------------------------------------------------
# Test: heading detection for bold large-font text
# ---------------------------------------------------------------------------

def test_heading_detection_large_font(tmp_path):
    """Blocks with font size > 13 should be classified as headings."""
    pdf_path = _create_simple_pdf(str(tmp_path), [
        {"text": "Maintenance Procedure Overview", "fontsize": 16},
        {"text": "This is body text that follows the heading paragraph.", "fontsize": 10},
    ])

    blocks = extract_blocks(pdf_path, doc_id="test-doc-id", doc_name="test.pdf", equipment_tag="Blast Furnace")

    heading_blocks = [b for b in blocks if b.block_type == "heading"]
    assert len(heading_blocks) >= 1, (
        "At least one heading block should be detected for large-font text. "
        f"Block types found: {[b.block_type for b in blocks]}"
    )
    # The large-font block text should contain our heading text
    heading_texts = " ".join(b.text for b in heading_blocks)
    assert "Maintenance" in heading_texts or "Overview" in heading_texts


# ---------------------------------------------------------------------------
# Test: table detection when | pipe characters are present
# ---------------------------------------------------------------------------

def test_table_detection_with_pipes(tmp_path):
    """Text blocks containing | characters should be classified as tables."""
    table_text = (
        "Component | Max Temperature | RPM\n"
        "Bearing SKF-22318 | 85C | 1500\n"
        "Gear Box 7A | 95C | 800\n"
    )
    pdf_path = _create_simple_pdf(str(tmp_path), [
        {"text": table_text, "fontsize": 10},
    ])

    blocks = extract_blocks(pdf_path, doc_id="test-doc-id", doc_name="test.pdf", equipment_tag="Rolling Mill")

    assert len(blocks) > 0
    block_types = [b.block_type for b in blocks]
    # The pipe-containing block should be detected as a table
    assert "table" in block_types, (
        f"Expected at least one 'table' block. Got block types: {block_types}"
    )


# ---------------------------------------------------------------------------
# Test: doc metadata is correctly propagated
# ---------------------------------------------------------------------------

def test_block_metadata_propagation(tmp_path):
    """doc_id, doc_name, equipment_tag should be on every block."""
    pdf_path = _create_simple_pdf(str(tmp_path), [
        {"text": "Equipment maintenance notes for the rolling mill assembly."},
    ])

    blocks = extract_blocks(
        pdf_path,
        doc_id="abc-123",
        doc_name="rolling_mill_manual.pdf",
        equipment_tag="Rolling Mill #3",
    )

    assert len(blocks) > 0
    for block in blocks:
        assert block.doc_id == "abc-123"
        assert block.doc_name == "rolling_mill_manual.pdf"
        assert block.equipment_tag == "Rolling Mill #3"
        assert block.page_number >= 1
