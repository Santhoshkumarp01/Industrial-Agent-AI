import logging
from typing import List
import re

logger = logging.getLogger(__name__)

# Keywords used to detect the "subject" / key column
KEY_COLUMN_KEYWORDS = [
    "parameter", "description", "component", "equipment",
    "fault", "symptom", "action", "part", "name", "item",
    # Phase 1 Fix: added more domain-relevant keywords
    "programme", "program", "course", "type", "motor", "model",
    "category", "specification", "property", "feature", "metric",
]


def _clean_cell(text: str) -> str:
    """
    Clean a table cell: collapse internal whitespace and newlines.

    Phase 1 Fix: PyMuPDF extracts table cells with embedded newlines
    (e.g. 'Engineering\\nand\\nTechnology*'). This collapses them to
    clean single-line text so the model can read values clearly.
    """
    if text is None:
        return ""
    # Replace any combination of whitespace (including \n) with a single space
    cleaned = re.sub(r'\s+', ' ', str(text)).strip()
    return cleaned


def _detect_key_column(headers: List[str]) -> int:
    """
    Scan headers for known subject keywords.
    Returns the index of the key column, or 0 as default.
    """
    for idx, header in enumerate(headers):
        if _clean_cell(header).lower() in KEY_COLUMN_KEYWORDS:
            return idx
    return 0  # default to first column


def _row_to_sentence(headers: List[str], row: List[str], key_col_idx: int) -> str:
    """
    Convert a table row to natural language prose.

    Phase 1 Fix: cells are cleaned before conversion to remove embedded newlines.
    """
    key_val = _clean_cell(row[key_col_idx]) if key_col_idx < len(row) else ""
    parts = []
    for i, (header, cell) in enumerate(zip(headers, row)):
        if i == key_col_idx:
            continue
        cell_str = _clean_cell(cell)
        header_str = _clean_cell(header)
        if cell_str and cell_str not in ("-", "—", "N/A", ""):
            parts.append(f"{header_str} is {cell_str}")
    sentence = f"{key_val}: " + "; ".join(parts) + "." if parts else f"{key_val}."
    return sentence


def parse_table_to_prose(
    rows: List[List[str]],
    document_title: str,
    section_heading: str,
    caption: str,
    chunk_size_rows: int = 20,
) -> List[str]:
    """
    Convert a table (list of rows) to natural language prose chunks.

    Phase 1 Fix: All cells are cleaned (newlines collapsed) before processing.
    This fixes tables where PyMuPDF stores multi-line cell values.

    Args:
        rows: Table rows including the header row as rows[0].
        document_title: Name of the source document.
        section_heading: Section heading context.
        caption: Table caption or label.
        chunk_size_rows: Max data rows per prose chunk.

    Returns:
        List of prose string chunks, each prefixed with context.

    Raises:
        ValueError: If any output chunk still contains | characters.
    """
    if not rows or len(rows) < 2:
        logger.warning("Table has no data rows, skipping.")
        return []

    # Phase 1 Fix: clean all headers and cells upfront
    headers = [_clean_cell(h) for h in rows[0]]
    data_rows = [[_clean_cell(cell) for cell in row] for row in rows[1:]]

    # Filter completely empty data rows
    data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]

    if not data_rows:
        logger.warning("Table has no non-empty data rows after cleaning.")
        return []

    key_col_idx = _detect_key_column(headers)
    prefix = f"From {document_title}, Section: {section_heading}, Table: {caption}. "

    chunks: List[str] = []
    i = 0
    while i < len(data_rows):
        # Apply 1-row overlap: include last row of previous chunk as first row
        start = max(0, i - 1) if i > 0 else 0
        end = min(i + chunk_size_rows, len(data_rows))
        window = data_rows[start:end]

        sentences = []
        for row in window:
            try:
                sentence = _row_to_sentence(headers, row, key_col_idx)
                sentences.append(sentence)
            except Exception as e:
                logger.warning(f"Failed to convert row to sentence: {e}")

        prose = prefix + " ".join(sentences)

        # Validate no pipe characters remain
        if "|" in prose:
            raise ValueError(
                f"Table prose chunk still contains '|' characters. "
                f"Table parse failed for: {document_title}, {caption}"
            )

        chunks.append(prose)
        i += chunk_size_rows

    return chunks
