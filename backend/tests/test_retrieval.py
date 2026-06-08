"""
Tests for retrieval/retriever.py and retrieval/reranker.py

Covers:
- retriever.retrieve() returns at most TOP_K_FINAL results
- Citation refs [C1], [C2], ... are assigned sequentially
- equipment_tag filter reduces results to matching docs only

These tests mock Qdrant and the embedding/reranking models so no live
services are needed.
"""

import uuid
from unittest.mock import patch, MagicMock
import pytest

from models.schemas import RetrievedChunk
from config import config


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_retrieved_chunk(
    doc_name: str = "manual.pdf",
    equipment_tag: str = "Rolling Mill",
    chunk_id: str = None,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id or str(uuid.uuid4()),
        doc_id="test-doc-id",  # ← Added missing field
        doc_name=doc_name,
        equipment_tag=equipment_tag,
        block_type="paragraph",  # ← FIXED: Added block_type
        text="This is a sample maintenance chunk about bearing lubrication procedures.",
        page_number=3,
        bbox=(10.0, 20.0, 400.0, 60.0),
        section_heading="Lubrication",
        relevance_score=0.85,
        citation_ref="",
    )


def _make_mock_chunks(n: int, equipment_tag: str = "Rolling Mill") -> list[RetrievedChunk]:
    return [_make_retrieved_chunk(equipment_tag=equipment_tag) for _ in range(n)]


# ---------------------------------------------------------------------------
# Test: retriever returns at most TOP_K_FINAL results
# ---------------------------------------------------------------------------

@patch("retrieval.retriever.rerank")
@patch("retrieval.retriever.qdrant_store")
@patch("retrieval.retriever.encode_query")
def test_retrieve_returns_at_most_top_k_final(mock_encode, mock_store, mock_rerank):
    """retrieve() must never return more than TOP_K_FINAL chunks."""
    from retrieval.retriever import retrieve

    candidates = _make_mock_chunks(config.TOP_K_RETRIEVAL)
    mock_encode.return_value = [0.1] * 384
    mock_store.query.return_value = candidates

    top_k_chunks = _make_mock_chunks(config.TOP_K_FINAL)
    mock_rerank.return_value = top_k_chunks

    result = retrieve("What is the lubrication interval for bearings?")

    assert len(result) <= config.TOP_K_FINAL, (
        f"Expected at most {config.TOP_K_FINAL} results, got {len(result)}."
    )


@patch("retrieval.retriever.rerank")
@patch("retrieval.retriever.qdrant_store")
@patch("retrieval.retriever.encode_query")
def test_retrieve_returns_fewer_when_less_available(mock_encode, mock_store, mock_rerank):
    """retrieve() should return all chunks when fewer than TOP_K_FINAL are available."""
    from retrieval.retriever import retrieve

    candidates = _make_mock_chunks(2)
    mock_encode.return_value = [0.1] * 384
    mock_store.query.return_value = candidates
    mock_rerank.return_value = candidates

    result = retrieve("Bearing maintenance?")
    assert len(result) <= config.TOP_K_FINAL
    assert len(result) == 2


# ---------------------------------------------------------------------------
# Test: citation refs are assigned sequentially [C1], [C2], ...
# ---------------------------------------------------------------------------

@patch("retrieval.retriever.rerank")
@patch("retrieval.retriever.qdrant_store")
@patch("retrieval.retriever.encode_query")
def test_citation_refs_assigned_sequentially(mock_encode, mock_store, mock_rerank):
    """Citation refs must be [C1], [C2], [C3], ... in order."""
    from retrieval.retriever import retrieve

    n = config.TOP_K_FINAL
    candidates = _make_mock_chunks(n)
    mock_encode.return_value = [0.1] * 384
    mock_store.query.return_value = candidates
    mock_rerank.return_value = candidates

    result = retrieve("How to replace rolling mill bearings?")

    assert len(result) == n
    for i, chunk in enumerate(result):
        expected_ref = f"[C{i + 1}]"
        assert chunk.citation_ref == expected_ref, (
            f"Expected citation_ref '{expected_ref}' at index {i}, "
            f"got '{chunk.citation_ref}'."
        )


@patch("retrieval.retriever.rerank")
@patch("retrieval.retriever.qdrant_store")
@patch("retrieval.retriever.encode_query")
def test_citation_refs_start_at_c1(mock_encode, mock_store, mock_rerank):
    """First citation ref must always be [C1], not [C0]."""
    from retrieval.retriever import retrieve

    candidates = _make_mock_chunks(3)
    mock_encode.return_value = [0.1] * 384
    mock_store.query.return_value = candidates
    mock_rerank.return_value = candidates

    result = retrieve("Inspection schedule?")

    assert result[0].citation_ref == "[C1]", (
        f"First citation ref should be [C1], got '{result[0].citation_ref}'."
    )


# ---------------------------------------------------------------------------
# Test: equipment_tag filter reduces results to matching docs only
# ---------------------------------------------------------------------------

@patch("retrieval.retriever.rerank")
@patch("retrieval.retriever.qdrant_store")
@patch("retrieval.retriever.encode_query")
def test_equipment_tag_filter_passed_to_qdrant(mock_encode, mock_store, mock_rerank):
    """
    When equipment_tag is provided, qdrant_store.query must be called
    with the equipment_tag argument.
    """
    from retrieval.retriever import retrieve

    mock_encode.return_value = [0.1] * 384
    mock_store.query.return_value = []
    mock_rerank.return_value = []

    retrieve("Cooling water flow rate?", equipment_tag="Blast Furnace #2")

    call_kwargs = mock_store.query.call_args
    assert call_kwargs is not None, "qdrant_store.query was not called."

    kwargs = call_kwargs.kwargs if call_kwargs.kwargs else {}
    args = call_kwargs.args if call_kwargs.args else ()

    # equipment_tag is a keyword arg in qdrant_store.query
    tag_arg = kwargs.get("equipment_tag") or (args[3] if len(args) > 3 else None)
    assert tag_arg == "Blast Furnace #2", (
        f"Expected equipment_tag 'Blast Furnace #2', got: {tag_arg}"
    )


@patch("retrieval.retriever.rerank")
@patch("retrieval.retriever.qdrant_store")
@patch("retrieval.retriever.encode_query")
def test_no_equipment_tag_when_not_provided(mock_encode, mock_store, mock_rerank):
    """When no equipment_tag is given, it should be None in the store call."""
    from retrieval.retriever import retrieve

    mock_encode.return_value = [0.1] * 384
    mock_store.query.return_value = []
    mock_rerank.return_value = []

    retrieve("General maintenance procedures?")

    call_kwargs = mock_store.query.call_args
    assert call_kwargs is not None

    kwargs = call_kwargs.kwargs if call_kwargs.kwargs else {}
    tag_arg = kwargs.get("equipment_tag")
    assert tag_arg is None, (
        f"Expected equipment_tag=None when not provided, got: {tag_arg}"
    )


# ---------------------------------------------------------------------------
# Test: raw query text is passed to qdrant_store (needed for BM25 sparse)
# ---------------------------------------------------------------------------

@patch("retrieval.retriever.rerank")
@patch("retrieval.retriever.qdrant_store")
@patch("retrieval.retriever.encode_query")
def test_query_text_passed_to_qdrant(mock_encode, mock_store, mock_rerank):
    """qdrant_store.query must receive the raw query_text for BM25 encoding."""
    from retrieval.retriever import retrieve

    mock_encode.return_value = [0.1] * 384
    mock_store.query.return_value = []
    mock_rerank.return_value = []

    query_text = "SKF-22318 bearing replacement procedure"
    retrieve(query_text)

    call_kwargs = mock_store.query.call_args
    assert call_kwargs is not None

    kwargs = call_kwargs.kwargs if call_kwargs.kwargs else {}
    text_arg = kwargs.get("query_text")
    assert text_arg == query_text, (
        f"Expected query_text='{query_text}', got: '{text_arg}'"
    )


# ---------------------------------------------------------------------------
# Test: empty retrieval returns empty list gracefully
# ---------------------------------------------------------------------------

@patch("retrieval.retriever.rerank")
@patch("retrieval.retriever.qdrant_store")
@patch("retrieval.retriever.encode_query")
def test_empty_retrieval_returns_empty_list(mock_encode, mock_store, mock_rerank):
    """retrieve() should return [] when Qdrant has no results."""
    from retrieval.retriever import retrieve

    mock_encode.return_value = [0.1] * 384
    mock_store.query.return_value = []
    mock_rerank.return_value = []

    result = retrieve("Unknown procedure XYZ123?")
    assert result == []


# ---------------------------------------------------------------------------
# Test: reranker returns top_k or fewer
# ---------------------------------------------------------------------------

def test_reranker_returns_at_most_top_k():
    """reranker.rerank() must return at most top_k chunks."""
    from retrieval.reranker import rerank

    chunks = _make_mock_chunks(8)

    with patch("retrieval.reranker._get_cross_encoder") as mock_get_encoder:
        mock_encoder = MagicMock()
        mock_encoder.predict.return_value = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
        mock_get_encoder.return_value = mock_encoder

        result = rerank("test query", chunks, top_k=3)

    assert len(result) <= 3, f"Expected at most 3 results from reranker, got {len(result)}."


def test_reranker_returns_all_when_fewer_than_top_k():
    """reranker.rerank() returns all chunks when input < top_k."""
    from retrieval.reranker import rerank

    chunks = _make_mock_chunks(2)

    with patch("retrieval.reranker._get_cross_encoder") as mock_get_encoder:
        mock_encoder = MagicMock()
        mock_encoder.predict.return_value = [0.9, 0.7]
        mock_get_encoder.return_value = mock_encoder

        result = rerank("test query", chunks, top_k=5)

    assert len(result) == 2


def test_reranker_sorts_by_score_descending():
    """Reranked chunks must be sorted highest score first."""
    from retrieval.reranker import rerank

    chunks = _make_mock_chunks(4)
    scores = [0.3, 0.9, 0.1, 0.7]

    with patch("retrieval.reranker._get_cross_encoder") as mock_get_encoder:
        mock_encoder = MagicMock()
        mock_encoder.predict.return_value = scores
        mock_get_encoder.return_value = mock_encoder

        result = rerank("test query", chunks, top_k=4)

    result_scores = [c.relevance_score for c in result]
    assert result_scores == sorted(result_scores, reverse=True), (
        f"Results not sorted descending: {result_scores}"
    )
