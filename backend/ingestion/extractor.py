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

    # Heading: large font OR bold with short text
    if (font_size > 13 or is_bold) and len(text_stripped) < 120:
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


def extract_blocks(file_path: str, doc_id: str, doc_name: str, equipment_tag: str) -> List[ExtractedBlock]:
    """
    Extract text blocks from a PDF with full bbox metadata.

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

    try:
        pdf = fitz.open(file_path)
    except Exception as e:
        logger.error(f"Failed to open PDF {file_path}: {e}")
        raise

    for page_idx in range(len(pdf)):
        page = pdf[page_idx]
        page_number = page_idx + 1

        # Track table bboxes to avoid double-extracting table text
        table_bboxes = set()

        # Extract proper tables using find_tables()
        try:
            tables = page.find_tables()
            for table in tables:
                try:
                    rows = table.extract()
                    if not rows:
                        continue

                    # Serialize rows to text for storage
                    table_text = "\n".join(
                        " | ".join(str(cell) if cell is not None else "" for cell in row)
                        for row in rows
                    )

                    bbox = tuple(table.bbox)
                    table_bboxes.add(bbox)

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

        # Extract text blocks from page dict
        page_dict = page.get_text("dict")
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

            if not full_text:
                continue

            font_size, is_bold = _get_block_font_info(block)
            block_bbox = tuple(block.get("bbox", (0, 0, 0, 0)))

            # Check if this bbox overlaps a table already extracted
            is_table_region = any(
                block_bbox[0] >= tb[0] - 2 and block_bbox[1] >= tb[1] - 2 and
                block_bbox[2] <= tb[2] + 2 and block_bbox[3] <= tb[3] + 2
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

    pdf.close()
    logger.info(f"Extracted {len(blocks)} blocks from {doc_name} ({len(pdf)} pages)")
    return blocks
