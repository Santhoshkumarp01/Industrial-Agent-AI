import logging
from typing import List

from sentence_transformers import CrossEncoder

from models.schemas import RetrievedChunk

logger = logging.getLogger(__name__)

_CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_cross_encoder: CrossEncoder | None = None


def _get_cross_encoder() -> CrossEncoder:
    """Return singleton CrossEncoder, loading on first call."""
    global _cross_encoder
    if _cross_encoder is None:
        logger.info(f"Loading cross-encoder model: {_CROSS_ENCODER_MODEL}")
        _cross_encoder = CrossEncoder(_CROSS_ENCODER_MODEL)
        logger.info("Cross-encoder model loaded.")
    return _cross_encoder


def rerank(query: str, chunks: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]:
    """
    Rerank retrieved chunks using a cross-encoder model.

    Args:
        query: The original search query.
        chunks: Candidate chunks from initial retrieval.
        top_k: Number of chunks to return after reranking.

    Returns:
        Top-k chunks sorted by cross-encoder relevance score (descending).
    """
    if not chunks:
        return []

    cross_encoder = _get_cross_encoder()

    pairs = [(query, chunk.text) for chunk in chunks]
    scores = cross_encoder.predict(pairs)

    # Attach updated relevance scores
    scored = list(zip(scores, chunks))
    scored.sort(key=lambda x: x[0], reverse=True)

    result: List[RetrievedChunk] = []
    for score, chunk in scored[:top_k]:
        updated = chunk.model_copy(update={"relevance_score": float(score)})
        result.append(updated)

    return result
