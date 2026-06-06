import logging
from typing import List

logger = logging.getLogger(__name__)

# Keywords used to detect the "subject" / key column
KEY_COLUMN_KEYWORDS = [
    "parameter", "description", "component", "equipment",
    "fault", "symptom", "action", "part", "name", "item",
]


def _detect_key_column(headers: List[str]) -> int:
    """
    Scan headers for known subject keywords.
    Returns the index of the key column, or 0 as default.
    """
    for idx, header in enumerate(headers):
        if header.strip().lower() in KEY_COLUMN_KEYWORDS:
            return idx
    return 0  # default to first column


def _row_to_sentence(headers: List[str], row: List[str], key_col_idx: int) -> str:
    """Convert a table row to natural language prose."""
    key_val = str(row[key_col_idx]).strip() if key_col_idx < len(row) else ""
    parts = []
    for i, (header, cell) in enumerate(zip(headers, row)):
        if i == key_col_idx:
            continue
        cell_str = str(cell).strip() if cell is not None else ""
        if cell_str:
            parts.append(f"{header.strip()} is {cell_str}")
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

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    data_rows = rows[1:]

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
