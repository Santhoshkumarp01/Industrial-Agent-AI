import re
import logging
import uuid
from typing import List

import nltk

from models.schemas import ExtractedBlock, Chunk
from ingestion.table_parser import parse_table_to_prose
from config import config

logger = logging.getLogger(__name__)

# Patterns for quality gate filtering
_SEPARATOR_PATTERN = re.compile(r"^[\-=\.]{3,}$")
_REF_NUMBER_PATTERN = re.compile(r"^\s*[A-Z]+\s*-\s*\d{4,}\s*$")


def _token_count(text: str) -> int:
    """Approximate token count using whitespace split."""
    return len(text.split())


def _is_low_quality(text: str) -> bool:
    """Return True if the chunk should be dropped."""
    stripped = text.strip()
    if _token_count(stripped) < config.MIN_CHUNK_TOKENS:
        return True
    if _SEPARATOR_PATTERN.match(stripped):
        return True
    if _REF_NUMBER_PATTERN.match(stripped):
        return True
    if "|" in stripped:
        return True
    return False


def _make_chunk(
    block: ExtractedBlock,
    text: str,
    chunk_index: int,
) -> Chunk:
    return Chunk(
        chunk_id=str(uuid.uuid4()),
        doc_id=block.doc_id,
        doc_name=block.doc_name,
        equipment_tag=block.equipment_tag,
        block_type=block.block_type,
        text=text,
        page_number=block.page_number,
        bbox=block.bbox,
        section_heading=block.section_heading,
        chunk_index=chunk_index,
        token_count=_token_count(text),
    )


def _chunk_paragraph(block: ExtractedBlock, chunk_index_start: int) -> List[Chunk]:
    """Split paragraph block into sentence-overlapping chunks."""
    try:
        sentences = nltk.sent_tokenize(block.text)
    except Exception:
        sentences = block.text.split(". ")

    if not sentences:
        return []

    total_tokens = _token_count(block.text)
    if total_tokens <= config.CHUNK_SIZE_TOKENS:
        chunk_text = block.text.strip()
        if not _is_low_quality(chunk_text):
            return [_make_chunk(block, chunk_text, chunk_index_start)]
        return []

    chunks: List[Chunk] = []
    current_sentences: List[str] = []
    current_tokens = 0
    idx = chunk_index_start

    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        s_tokens = _token_count(sentence)

        if current_tokens + s_tokens > config.CHUNK_SIZE_TOKENS and current_sentences:
            # Emit chunk
            chunk_text = " ".join(current_sentences).strip()
            if not _is_low_quality(chunk_text):
                chunks.append(_make_chunk(block, chunk_text, idx))
                idx += 1

            # 1-sentence overlap: keep last sentence
            overlap = [current_sentences[-1]]
            current_sentences = overlap
            current_tokens = _token_count(overlap[0])
        else:
            current_sentences.append(sentence)
            current_tokens += s_tokens
            i += 1

    # Emit remaining
    if current_sentences:
        chunk_text = " ".join(current_sentences).strip()
        if not _is_low_quality(chunk_text):
            chunks.append(_make_chunk(block, chunk_text, idx))

    return chunks


def _chunk_heading(block: ExtractedBlock, chunk_index: int) -> List[Chunk]:
    """Store heading as a standalone chunk."""
    text = block.text.strip()
    if _is_low_quality(text):
        return []
    return [_make_chunk(block, text, chunk_index)]


def _chunk_list(block: ExtractedBlock, chunk_index_start: int, section_heading: str) -> List[Chunk]:
    """Pack list items under section heading into token-limited chunks."""
    prefix = f"Section: {section_heading}. " if section_heading else ""
    lines = [l.strip() for l in block.text.splitlines() if l.strip()]

    chunks: List[Chunk] = []
    current_lines: List[str] = []
    current_tokens = _token_count(prefix)
    idx = chunk_index_start

    for line in lines:
        lt = _token_count(line)
        if current_tokens + lt > config.CHUNK_SIZE_TOKENS and current_lines:
            chunk_text = prefix + " ".join(current_lines)
            if not _is_low_quality(chunk_text):
                chunks.append(_make_chunk(block, chunk_text, idx))
                idx += 1
            current_lines = []
            current_tokens = _token_count(prefix)
        current_lines.append(line)
        current_tokens += lt

    if current_lines:
        chunk_text = prefix + " ".join(current_lines)
        if not _is_low_quality(chunk_text):
            chunks.append(_make_chunk(block, chunk_text, idx))

    return chunks


def _chunk_table(block: ExtractedBlock, chunk_index_start: int) -> List[Chunk]:
    """Parse table → prose, then chunk the prose rows."""
    # Parse raw pipe-delimited text back into rows
    raw_rows = [
        [cell.strip() for cell in line.split("|")]
        for line in block.text.splitlines()
        if line.strip()
    ]

    try:
        prose_chunks = parse_table_to_prose(
            rows=raw_rows,
            document_title=block.doc_name,
            section_heading=block.section_heading,
            caption="",
        )
    except ValueError as e:
        logger.error(f"Table parser raised ValueError: {e} — skipping table block.")
        return []
    except Exception as e:
        logger.warning(f"Table parse failed: {e} — skipping table block.")
        return []

    chunks: List[Chunk] = []
    idx = chunk_index_start
    for prose in prose_chunks:
        if not _is_low_quality(prose):
            chunks.append(_make_chunk(block, prose, idx))
            idx += 1

    return chunks


def _chunk_figure_caption(block: ExtractedBlock, chunk_index: int) -> List[Chunk]:
    """Store figure caption as-is."""
    text = block.text.strip()
    if _is_low_quality(text):
        return []
    return [_make_chunk(block, text, chunk_index)]


def chunk_blocks(blocks: List[ExtractedBlock]) -> List[Chunk]:
    """
    Convert extracted blocks into chunks ready for embedding.

    Args:
        blocks: List of ExtractedBlock objects.

    Returns:
        List of Chunk objects.
    """
    all_chunks: List[Chunk] = []
    chunk_index = 0
    last_heading = ""

    for block in blocks:
        btype = block.block_type

        if btype == "heading":
            new_chunks = _chunk_heading(block, chunk_index)
            last_heading = block.text.strip()

        elif btype == "paragraph":
            # Prefix with heading for self-containment if available
            if last_heading and not block.text.startswith(last_heading):
                prefixed_block = block.model_copy(
                    update={"text": f"{last_heading}\n{block.text}"}
                )
            else:
                prefixed_block = block
            new_chunks = _chunk_paragraph(prefixed_block, chunk_index)

        elif btype == "list":
            new_chunks = _chunk_list(block, chunk_index, block.section_heading)

        elif btype == "table":
            new_chunks = _chunk_table(block, chunk_index)

        elif btype == "figure_caption":
            new_chunks = _chunk_figure_caption(block, chunk_index)

        else:
            new_chunks = _chunk_paragraph(block, chunk_index)

        all_chunks.extend(new_chunks)
        chunk_index += len(new_chunks)

    logger.info(f"Produced {len(all_chunks)} chunks from {len(blocks)} blocks.")
    return all_chunks
