"""
Legacy PyMuPDF-based extractor as fallback when Docling fails.

Phase 1 Fix:
- Table rows now carry section_heading prefix so model number + value stay together
- Heading detection lowered to font_size > 11 to catch more section starts
- MIN block text length reduced from implicit 0 to filter pure noise
"""

import re
import logging
from typing import List

import fitz  # PyMuPDF

from models.schemas import ExtractedBlock

logger = logging.getLogger(__name__)


def _classify_block(text: str, font_size: float, is_bold: bool) -> str:
    """Classify a text block into a block type."""
    text_stripped = text.strip()

    # Figure/table caption
    if re.match(r"^(Fig\.?|Figure|Table)\s+\d+", text_stripped, re.IGNORECASE):
        return "figure_caption"

    # Heading: font > 11 OR bold with short text (lowered from 13 to catch more headings)
    if (font_size > 11 or is_bold) and len(text_stripped) < 120:
        # Exclude pure numbers/codes that are bold but not headings
        if not re.match(r"^[\d\.\-]+$", text_stripped):
            return "heading"

    # List item
    if re.match(r"^[\u2022\-\*]\s+", text_stripped) or re.match(r"^\d+\.\s+", text_stripped):
        return "list"

    # Table: contains pipe separators
    if "|" in text_stripped:
        return "table"

    return "paragraph"


def _get_block_font_info(block: dict) -> tuple[float, bool]:
    """Extract average font size and bold flag from a block's spans."""
    sizes = []
    is_bold = False
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            sizes.append(span.get("size", 12.0))
            flags = span.get("flags", 0)
            # Bold flag is bit 4 (value 16) in PyMuPDF
            if flags & 16:
                is_bold = True
    avg_size = sum(sizes) / len(sizes) if sizes else 12.0
    return avg_size, is_bold


def _serialize_table(rows: list, section_heading: str, page_number: int) -> str:
    """
    Serialize table rows to pipe-delimited text WITH section heading prefix.

    Phase 1 Fix: Prepend section_heading so every table chunk knows its context.
    This prevents model number + value from being split across chunks.

    Example output:
      §3.3.1 Terminal assignment:
      Motor type | Terminal box | Max current | At factor 0.6
      1PH7184 | 1XB7 322 | 63 A | 38 A
    """
    # Build header context
    prefix = f"§{section_heading}:\n" if section_heading else ""

    # Filter completely empty rows
    non_empty_rows = [
        row for row in rows
        if any(cell is not None and str(cell).strip() for cell in row)
    ]

    if not non_empty_rows:
        return ""

    serialized = prefix + "\n".join(
        " | ".join(str(cell).strip() if cell is not None else "" for cell in row)
        for row in non_empty_rows
    )
    return serialized


def extract_blocks_pymupdf(file_path: str, doc_id: str, doc_name: str, equipment_tag: str) -> List[ExtractedBlock]:
    """
    Extract text blocks from a PDF using PyMuPDF (legacy fallback).

    Phase 1 Fixes applied:
    1. Table rows carry section_heading prefix (model + value stay together)
    2. Heading font threshold lowered 13→11 (more section boundaries detected)
    3. Very short noise blocks (<3 chars) filtered before block creation
    4. Table bbox overlap check uses a small tolerance to avoid double-extraction

    Args:
        file_path: Path to the PDF file.
        doc_id: UUID for this document.
        doc_name: Original filename.
        equipment_tag: Equipment identifier (e.g., "Rolling Mill").

    Returns:
        List of ExtractedBlock objects.
    """
    blocks: List[ExtractedBlock] = []
    current_heading = ""
    pdf = None

    try:
        pdf = fitz.open(file_path)
        total_pages = len(pdf)

        for page_idx in range(total_pages):
            try:
                page = pdf[page_idx]
                page_number = page_idx + 1

                # Track table bboxes to avoid double-extracting table text
                table_bboxes = []

                # ── Extract tables using find_tables() ────────────────────
                try:
                    tables = page.find_tables()
                    for table in tables:
                        try:
                            rows = table.extract()
                            if not rows:
                                continue

                            # Phase 1 Fix: use _serialize_table with section prefix
                            table_text = _serialize_table(rows, current_heading, page_number)
                            if not table_text.strip():
                                continue

                            bbox = tuple(table.bbox)
                            table_bboxes.append(bbox)

                            blocks.append(ExtractedBlock(
                                doc_id=doc_id,
                                doc_name=doc_name,
                                equipment_tag=equipment_tag,
                                block_type="table",
                                text=table_text,
                                page_number=page_number,
                                bbox=bbox,
                                font_size=10.0,
                                is_bold=False,
                                section_heading=current_heading,
                            ))
                        except Exception as e:
                            logger.warning(f"Failed to extract table on page {page_number}: {e}")
                except Exception as e:
                    logger.warning(f"find_tables() failed on page {page_number}: {e}")

                # ── Extract text blocks ────────────────────────────────────
                try:
                    page_dict = page.get_text("dict")
                except Exception as e:
                    logger.warning(f"Failed to get text dict for page {page_number}: {e}")
                    continue

                for block in page_dict.get("blocks", []):
                    # Skip image blocks
                    if block.get("type") != 0:
                        continue

                    # Collect text from all lines/spans
                    lines_text = []
                    for line in block.get("lines", []):
                        line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                        lines_text.append(line_text)
                    full_text = "\n".join(lines_text).strip()

                    # Phase 1 Fix: filter pure noise (< 3 chars)
                    if not full_text or len(full_text) < 3:
                        continue

                    font_size, is_bold = _get_block_font_info(block)
                    block_bbox = tuple(block.get("bbox", (0, 0, 0, 0)))

                    # Check if this bbox overlaps a table already extracted
                    # Phase 1 Fix: use stored bbox list with tolerance
                    is_table_region = any(
                        block_bbox[0] >= tb[0] - 5 and block_bbox[1] >= tb[1] - 5 and
                        block_bbox[2] <= tb[2] + 5 and block_bbox[3] <= tb[3] + 5
                        for tb in table_bboxes
                    )
                    if is_table_region:
                        continue

                    block_type = _classify_block(full_text, font_size, is_bold)

                    # Update current heading tracker
                    if block_type == "heading":
                        current_heading = full_text.strip()

                    blocks.append(ExtractedBlock(
                        doc_id=doc_id,
                        doc_name=doc_name,
                        equipment_tag=equipment_tag,
                        block_type=block_type,
                        text=full_text,
                        page_number=page_number,
                        bbox=block_bbox,
                        font_size=font_size,
                        is_bold=is_bold,
                        section_heading=current_heading if block_type != "heading" else "",
                    ))
            except Exception as page_error:
                logger.warning(f"Error processing page {page_idx + 1}: {page_error}")
                continue

        logger.info(f"[PyMuPDF] Extracted {len(blocks)} blocks from {doc_name} ({total_pages} pages)")
        return blocks

    except Exception as e:
        logger.error(f"Failed to extract blocks from {file_path}: {e}")
        raise
    finally:
        if pdf is not None:
            try:
                pdf.close()
            except Exception:
                pass
