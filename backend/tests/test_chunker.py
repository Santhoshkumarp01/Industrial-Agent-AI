"""
Tests for ingestion/chunker.py

Covers:
- Long paragraph splitting into multiple chunks
- 1-sentence overlap between consecutive paragraph chunks
- Chunks below MIN_CHUNK_TOKENS are dropped
- Table chunker raises ValueError if | remains in output
"""

import uuid
import pytest

from models.schemas import ExtractedBlock
from ingestion.chunker import chunk_blocks
from ingestion import table_parser
from config import config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_block(text: str, block_type: str = "paragraph", section_heading: str = "Test Section") -> ExtractedBlock:
    return ExtractedBlock(
        doc_id=str(uuid.uuid4()),
        doc_name="test_manual.pdf",
        equipment_tag="Rolling Mill",
        block_type=block_type,
        text=text,
        page_number=1,
        bbox=(10.0, 10.0, 400.0, 50.0),
        font_size=11.0,
        is_bold=False,
        section_heading=section_heading,
    )


def _long_paragraph(num_sentences: int = 60) -> str:
    """Generate a paragraph long enough to exceed CHUNK_SIZE_TOKENS."""
    sentence = "The rolling mill bearing assembly requires lubrication every 500 hours of operation."
    return " ".join([sentence] * num_sentences)


# ---------------------------------------------------------------------------
# Test: long paragraph is split into multiple chunks
# ---------------------------------------------------------------------------

def test_long_paragraph_splits_into_multiple_chunks():
    """A paragraph exceeding CHUNK_SIZE_TOKENS should produce multiple chunks."""
    long_text = _long_paragraph(num_sentences=60)
    # Verify it actually exceeds the token limit
    assert len(long_text.split()) > config.CHUNK_SIZE_TOKENS, (
        "Test text must exceed CHUNK_SIZE_TOKENS for this test to be valid."
    )

    block = _make_block(long_text, block_type="paragraph")
    chunks = chunk_blocks([block])

    assert len(chunks) > 1, (
        f"Expected multiple chunks for a long paragraph, got {len(chunks)}. "
        f"CHUNK_SIZE_TOKENS={config.CHUNK_SIZE_TOKENS}, text_tokens={len(long_text.split())}"
    )

    # Each chunk should be within token limit (allow slight overage for overlap sentence)
    for chunk in chunks:
        assert chunk.token_count <= config.CHUNK_SIZE_TOKENS + 50, (
            f"Chunk token count {chunk.token_count} exceeds limit by too much."
        )


# ---------------------------------------------------------------------------
# Test: 1-sentence overlap between consecutive paragraph chunks
# ---------------------------------------------------------------------------

def test_one_sentence_overlap_between_consecutive_chunks():
    """
    The last sentence of chunk N should appear as the first sentence of chunk N+1.
    """
    # Build text with distinct sentences so we can track them
    sentences = [
        f"Sentence number {i} describes a specific maintenance procedure step for rolling mill equipment." 
        for i in range(1, 50)
    ]
    long_text = " ".join(sentences)
    assert len(long_text.split()) > config.CHUNK_SIZE_TOKENS

    block = _make_block(long_text, block_type="paragraph")
    chunks = chunk_blocks([block])

    assert len(chunks) >= 2, "Need at least 2 chunks to test overlap."

    # For each consecutive pair, the last sentence of chunk[i] should appear
    # at the start of chunk[i+1]
    for i in range(len(chunks) - 1):
        current_text = chunks[i].text
        next_text = chunks[i + 1].text

        # Split both chunks into sentences to find the last sentence of current
        import nltk
        try:
            current_sentences = nltk.sent_tokenize(current_text)
        except Exception:
            current_sentences = current_text.split(". ")

        last_sentence = current_sentences[-1].strip()

        # The last sentence of the current chunk should appear in the next chunk
        assert last_sentence in next_text, (
            f"1-sentence overlap not found between chunk {i} and chunk {i+1}.\n"
            f"Last sentence of chunk {i}: '{last_sentence[:80]}...'\n"
            f"Start of chunk {i+1}: '{next_text[:80]}...'"
        )


# ---------------------------------------------------------------------------
# Test: chunks below MIN_CHUNK_TOKENS are dropped
# ---------------------------------------------------------------------------

def test_short_chunks_are_dropped():
    """Blocks with fewer than MIN_CHUNK_TOKENS tokens should produce no chunks."""
    # Text with only a few tokens — well below MIN_CHUNK_TOKENS
    short_texts = [
        "OK.",
        "Yes.",
        "N/A",
        "---",
        "See above.",
    ]

    for short_text in short_texts:
        token_count = len(short_text.split())
        if token_count < config.MIN_CHUNK_TOKENS:
            block = _make_block(short_text, block_type="paragraph")
            chunks = chunk_blocks([block])
            assert len(chunks) == 0, (
                f"Expected 0 chunks for short text '{short_text}' "
                f"({token_count} tokens < MIN_CHUNK_TOKENS={config.MIN_CHUNK_TOKENS}), "
                f"but got {len(chunks)}."
            )


def test_separator_only_chunks_are_dropped():
    """Chunks consisting only of separator characters should be dropped."""
    separator_texts = ["------", "======", "......", "--------"]

    for sep in separator_texts:
        block = _make_block(sep, block_type="paragraph")
        chunks = chunk_blocks([block])
        assert len(chunks) == 0, (
            f"Expected separator '{sep}' to produce 0 chunks, got {len(chunks)}."
        )


# ---------------------------------------------------------------------------
# Test: table chunker raises ValueError if | remains in output
# ---------------------------------------------------------------------------

def test_table_parse_raises_value_error_on_pipe_in_output():
    """
    table_parser.parse_table_to_prose should raise ValueError if any output
    chunk still contains a | character.
    """
    # Craft rows where cell values contain literal pipe characters that
    # would leak into the output — this simulates a malformed table
    rows_with_pipes = [
        ["Component", "Specification"],
        ["Bearing | Type", "SKF-22318 | Heavy Duty"],
        ["Gear | Box", "Model 7A | 800 RPM"],
    ]

    with pytest.raises(ValueError, match=r"\|"):
        table_parser.parse_table_to_prose(
            rows=rows_with_pipes,
            document_title="Test Manual",
            section_heading="Specifications",
            caption="Table 1",
        )


def test_valid_table_produces_no_pipes():
    """A clean table should produce prose chunks with no | characters."""
    rows = [
        ["Component", "Max Temperature", "RPM"],
        ["Bearing SKF-22318", "85C", "1500"],
        ["Gear Box 7A", "95C", "800"],
        ["Drive Shaft", "70C", "1200"],
    ]

    prose_chunks = table_parser.parse_table_to_prose(
        rows=rows,
        document_title="Rolling Mill Manual",
        section_heading="Component Specifications",
        caption="Table 2",
    )

    assert len(prose_chunks) >= 1
    for chunk in prose_chunks:
        assert "|" not in chunk, (
            f"Pipe character found in prose chunk: '{chunk[:100]}'"
        )


# ---------------------------------------------------------------------------
# Test: chunk metadata is correctly populated
# ---------------------------------------------------------------------------

def test_chunk_metadata_populated():
    """Each chunk should carry the correct metadata from the source block."""
    sentences = [
        "The blast furnace requires daily inspection of the cooling system components.",
        "Maintenance engineers must check pressure values every four hours during operation.",
        "All readings should be logged in the plant maintenance management system.",
    ]
    text = " ".join(sentences * 5)  # repeat to ensure enough tokens

    block = _make_block(text, block_type="paragraph", section_heading="Daily Checks")
    block = block.model_copy(update={
        "doc_id": "doc-xyz",
        "doc_name": "blast_furnace_sop.pdf",
        "equipment_tag": "Blast Furnace #1",
        "page_number": 7,
        "bbox": (20.0, 30.0, 500.0, 80.0),
    })

    chunks = chunk_blocks([block])
    assert len(chunks) > 0

    for chunk in chunks:
        assert chunk.doc_id == "doc-xyz"
        assert chunk.doc_name == "blast_furnace_sop.pdf"
        assert chunk.equipment_tag == "Blast Furnace #1"
        assert chunk.page_number == 7
        assert chunk.bbox == (20.0, 30.0, 500.0, 80.0)
        assert chunk.token_count > 0
        assert chunk.chunk_id  # non-empty UUID string


# ---------------------------------------------------------------------------
# Test: heading block stored as standalone chunk
# ---------------------------------------------------------------------------

def test_heading_stored_as_standalone_chunk():
    """Heading blocks should produce exactly one chunk with the heading text."""
    heading_text = "Section 3: Lubrication Procedures for Rolling Mill Bearings"
    block = _make_block(heading_text, block_type="heading", section_heading="")

    chunks = chunk_blocks([block])

    # Heading should produce exactly 1 chunk (assuming it meets MIN_CHUNK_TOKENS)
    if len(heading_text.split()) >= config.MIN_CHUNK_TOKENS:
        assert len(chunks) == 1
        assert heading_text in chunks[0].text
