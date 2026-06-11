"""
Chunking with parent-child retrieval support.

Strategy:
- Small child chunks (150-250 tokens) → Precise matching
- Parent sections (entire semantic block) → Complete context
- Query matches child → Retrieve parent for LLM
"""

import re
import logging
import uuid
from typing import List, Tuple

import nltk

from models.schemas import ExtractedBlock, Chunk, ParentSection
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
    
    # Special case: if text contains numbered list items, keep it even if short
    if any(stripped.startswith(f"{i}.") for i in range(1, 10)):
        return _token_count(stripped) < 10  # Lower threshold for lists

    # Phase 1 Fix: lowered from 25 → 10 to keep short spec values (e.g. "nmax = 4500 rpm")
    if _token_count(stripped) < 10:
        return True
    if _SEPARATOR_PATTERN.match(stripped):
        return True
    if _REF_NUMBER_PATTERN.match(stripped):
        return True
    # Removed pipe filtering - tables are handled by block_type="table" path
    return False


def _make_chunk(
    block: ExtractedBlock,
    text: str,
    chunk_index: int,
    parent_id: str = None,
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
        parent_id=parent_id,
    )


def _chunk_paragraph_with_parent(block: ExtractedBlock, chunk_index_start: int, parent_id: str) -> List[Chunk]:
    """Split paragraph into small child chunks (150-250 tokens) linked to parent."""
    try:
        sentences = nltk.sent_tokenize(block.text)
    except Exception:
        sentences = block.text.split(". ")

    if not sentences:
        return []

    # Target smaller chunks for precise matching
    target_tokens = 200  # Sweet spot for child chunks
    
    total_tokens = _token_count(block.text)
    if total_tokens <= target_tokens:
        chunk_text = block.text.strip()
        if not _is_low_quality(chunk_text):
            return [_make_chunk(block, chunk_text, chunk_index_start, parent_id)]
        return []

    chunks: List[Chunk] = []
    current_sentences: List[str] = []
    current_tokens = 0
    idx = chunk_index_start

    for sentence in sentences:
        s_tokens = _token_count(sentence)

        if current_tokens + s_tokens > target_tokens and current_sentences:
            chunk_text = " ".join(current_sentences).strip()
            if not _is_low_quality(chunk_text):
                chunks.append(_make_chunk(block, chunk_text, idx, parent_id))
                idx += 1
            
            # Small overlap for context
            current_sentences = [current_sentences[-1]] if current_sentences else []
            current_tokens = _token_count(current_sentences[0]) if current_sentences else 0
        
        current_sentences.append(sentence)
        current_tokens += s_tokens

    # Emit remaining
    if current_sentences:
        chunk_text = " ".join(current_sentences).strip()
        if not _is_low_quality(chunk_text):
            chunks.append(_make_chunk(block, chunk_text, idx, parent_id))

    return chunks


def _chunk_list_with_parent(block: ExtractedBlock, chunk_index_start: int, section_heading: str, parent_id: str) -> List[Chunk]:
    """Lists kept as single chunks but linked to parent."""
    prefix = f"Section: {section_heading}. " if section_heading else ""
    full_text = prefix + block.text.strip()
    
    # Keep entire list together
    token_count = _token_count(full_text)
    
    if token_count <= 800:
        if not _is_low_quality(full_text):
            return [_make_chunk(block, full_text, chunk_index_start, parent_id)]
        return []
    
    # For very long lists, split but keep parent link
    lines = [l.strip() for l in block.text.splitlines() if l.strip()]
    chunks: List[Chunk] = []
    current_group: List[str] = []
    current_tokens = _token_count(prefix)
    idx = chunk_index_start
    
    for line in lines:
        lt = _token_count(line)
        
        if current_tokens + lt > 600 and current_group:
            chunk_text = prefix + "\n".join(current_group)
            if not _is_low_quality(chunk_text):
                chunks.append(_make_chunk(block, chunk_text, idx, parent_id))
                idx += 1
            current_group = []
            current_tokens = _token_count(prefix)
        
        current_group.append(line)
        current_tokens += lt
    
    if current_group:
        chunk_text = prefix + "\n".join(current_group)
        if not _is_low_quality(chunk_text):
            chunks.append(_make_chunk(block, chunk_text, idx, parent_id))
    
    return chunks


def _chunk_table_with_parent(block: ExtractedBlock, chunk_index_start: int, parent_id: str) -> List[Chunk]:
    """
    Convert table to prose chunks linked to parent.

    Phase 1 Fix: Section heading prefix is already in block.text (added by extractor).
    parse_table_to_prose receives the full text including the section prefix,
    so each prose chunk carries context like '§3.3.1 Terminal assignment: ...'
    """
    raw_rows = [
        [cell.strip() for cell in line.split("|")]
        for line in block.text.splitlines()
        if line.strip()
    ]

    try:
        prose_chunks_text = parse_table_to_prose(
            rows=raw_rows,
            document_title=block.doc_name,
            section_heading=block.section_heading,
            caption="",
        )
    except Exception as e:
        logger.warning(f"Table parse failed: {e}")
        # Phase 1 Fix: fallback — store raw pipe-delimited rows as single chunk
        # so spec values are not silently lost
        raw_text = block.text.strip()
        if raw_text and not _is_low_quality(raw_text):
            return [_make_chunk(block, raw_text, chunk_index_start, parent_id)]
        return []

    chunks: List[Chunk] = []
    idx = chunk_index_start
    for prose in prose_chunks_text:
        if not _is_low_quality(prose):
            chunks.append(_make_chunk(block, prose, idx, parent_id))
            idx += 1

    # Phase 1 Fix: if prose conversion produced nothing, store raw text as fallback
    if not chunks:
        raw_text = block.text.strip()
        if raw_text and not _is_low_quality(raw_text):
            chunks.append(_make_chunk(block, raw_text, chunk_index_start, parent_id))

    return chunks


def _chunk_figure_with_parent(block: ExtractedBlock, chunk_index: int, parent_id: str) -> List[Chunk]:
    """Store figure/caption as single chunk linked to parent."""
    text = block.text.strip()
    if _is_low_quality(text):
        return []
    return [_make_chunk(block, text, chunk_index, parent_id)]


# Legacy chunking functions (kept for compatibility)
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
    """
    Keep entire numbered/bullet lists as single chunks - NEVER SPLIT.
    This preserves procedures, safety rules, and sequential instructions.
    """
    prefix = f"Section: {section_heading}. " if section_heading else ""
    full_text = prefix + block.text.strip()
    
    # Check if this is a complete numbered list (e.g., "five safety rules")
    # Keep it as ONE chunk regardless of token count
    token_count = _token_count(full_text)
    
    # For numbered lists, always keep as single chunk up to 800 tokens
    if re.search(r'\d+\.', block.text) and token_count <= 800:
        if not _is_low_quality(full_text):
            return [_make_chunk(block, full_text, chunk_index_start)]
        return []
    
    # For very long lists (>800 tokens), split at major boundaries only
    # but keep related items together
    if token_count > 800:
        lines = [l.strip() for l in block.text.splitlines() if l.strip()]
        chunks: List[Chunk] = []
        current_group: List[str] = []
        current_tokens = _token_count(prefix)
        idx = chunk_index_start
        
        for line in lines:
            lt = _token_count(line)
            
            # If adding this line exceeds 600 tokens, emit current group
            if current_tokens + lt > 600 and current_group:
                chunk_text = prefix + "\n".join(current_group)
                if not _is_low_quality(chunk_text):
                    chunks.append(_make_chunk(block, chunk_text, idx))
                    idx += 1
                current_group = []
                current_tokens = _token_count(prefix)
            
            current_group.append(line)
            current_tokens += lt
        
        # Emit remaining
        if current_group:
            chunk_text = prefix + "\n".join(current_group)
            if not _is_low_quality(chunk_text):
                chunks.append(_make_chunk(block, chunk_text, idx))
        
        return chunks
    
    # For short lists, keep as-is
    if not _is_low_quality(full_text):
        return [_make_chunk(block, full_text, chunk_index_start)]
    
    return []


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


def chunk_blocks(blocks: List[ExtractedBlock]) -> Tuple[List[Chunk], List[ParentSection]]:
    """
    Convert extracted blocks into chunks with parent-child relationships.
    
    Strategy:
    1. Each semantic block (heading + content) = 1 Parent Section
    2. Large blocks split into small Child Chunks (150-250 tokens)
    3. Child chunks link to parent via parent_id
    4. Query matches child → Retrieve parent for complete context

    Args:
        blocks: List of ExtractedBlock objects.

    Returns:
        Tuple of (chunks, parent_sections)
    """
    all_chunks: List[Chunk] = []
    all_parents: List[ParentSection] = []
    
    chunk_index = 0
    current_section_blocks: List[ExtractedBlock] = []
    current_heading = ""

    for i, block in enumerate(blocks):
        btype = block.block_type

        # Heading starts a new section
        if btype == "heading":
            # Finalize previous section
            if current_section_blocks:
                parent, chunks = _create_parent_child_section(
                    current_section_blocks, 
                    current_heading,
                    chunk_index
                )
                if parent and chunks:
                    all_parents.append(parent)
                    all_chunks.extend(chunks)
                    chunk_index += len(chunks)
            
            # Start new section
            current_heading = block.text.strip()
            current_section_blocks = [block]
        
        else:
            # Add block to current section
            current_section_blocks.append(block)
    
    # Finalize last section
    if current_section_blocks:
        parent, chunks = _create_parent_child_section(
            current_section_blocks,
            current_heading,
            chunk_index
        )
        if parent and chunks:
            all_parents.append(parent)
            all_chunks.extend(chunks)

    logger.info(
        f"Produced {len(all_chunks)} child chunks and "
        f"{len(all_parents)} parent sections from {len(blocks)} blocks."
    )
    return all_chunks, all_parents


def _create_parent_child_section(
    section_blocks: List[ExtractedBlock],
    heading: str,
    chunk_index_start: int
) -> Tuple[ParentSection, List[Chunk]]:
    """
    Create a parent section and its child chunks.
    
    Parent = Full section text (sent to LLM)
    Children = Small chunks (150-250 tokens, for embedding)
    """
    if not section_blocks:
        return None, []
    
    parent_id = str(uuid.uuid4())
    
    # Combine all blocks in section for parent text
    full_text_parts = []
    if heading:
        full_text_parts.append(f"## {heading}\n")
    
    block_types = []
    first_block = section_blocks[0]
    
    for block in section_blocks:
        if block.block_type != "heading":
            full_text_parts.append(block.text)
            if block.block_type not in block_types:
                block_types.append(block.block_type)
    
    full_text = "\n\n".join(full_text_parts)
    parent_token_count = _token_count(full_text)
    
    # Create child chunks from section blocks
    child_chunks = []
    chunk_idx = chunk_index_start
    
    for block in section_blocks:
        if block.block_type == "heading":
            continue  # Already included in parent
        
        btype = block.block_type
        
        # Chunk based on type - all reference parent_id
        if btype == "paragraph":
            new_chunks = _chunk_paragraph_with_parent(block, chunk_idx, parent_id)
        elif btype == "list":
            new_chunks = _chunk_list_with_parent(block, chunk_idx, heading, parent_id)
        elif btype == "table":
            new_chunks = _chunk_table_with_parent(block, chunk_idx, parent_id)
        elif btype == "figure" or btype == "figure_caption":
            new_chunks = _chunk_figure_with_parent(block, chunk_idx, parent_id)
        else:
            new_chunks = _chunk_paragraph_with_parent(block, chunk_idx, parent_id)
        
        child_chunks.extend(new_chunks)
        chunk_idx += len(new_chunks)
    
    if not child_chunks:
        return None, []
    
    # Create parent section
    parent = ParentSection(
        parent_id=parent_id,
        doc_id=first_block.doc_id,
        doc_name=first_block.doc_name,
        equipment_tag=first_block.equipment_tag,
        section_heading=heading,
        full_text=full_text,
        page_number=first_block.page_number,
        bbox=first_block.bbox,
        block_types=block_types,
        token_count=parent_token_count,
        child_chunk_ids=[c.chunk_id for c in child_chunks]
    )
    
    return parent, child_chunks
