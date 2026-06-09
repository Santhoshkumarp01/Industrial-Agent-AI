import logging
from typing import List
import torch

from sentence_transformers import CrossEncoder

from models.schemas import RetrievedChunk

logger = logging.getLogger(__name__)

_CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_cross_encoder: CrossEncoder | None = None


def _get_cross_encoder() -> CrossEncoder:
    """
    Return singleton CrossEncoder, loading on first call.
    Model is cached in memory after first load for fast subsequent calls.
    """
    global _cross_encoder
    if _cross_encoder is None:
        logger.info(f"Loading cross-encoder model (first time only): {_CROSS_ENCODER_MODEL}")
        logger.info("This may take 10-15 seconds on first load...")
        
        # Load with cache directory to persist downloaded model
        _cross_encoder = CrossEncoder(
            _CROSS_ENCODER_MODEL,
            max_length=512,
            device='cpu'  # Use CPU on Mac (MPS not fully supported for cross-encoders)
        )
        
        logger.info("✓ Cross-encoder model loaded and cached in memory.")
        logger.info("  Subsequent reranking calls will be fast (~1-2 seconds).")
    return _cross_encoder


def normalize_score(raw_score: float) -> float:
    """
    Normalize cross-encoder logit score to 0-1 probability.
    
    Cross-encoder models return raw logits which can be negative.
    This function converts them to calibrated probabilities using sigmoid.
    
    Args:
        raw_score: Raw logit score from cross-encoder (can be negative)
    
    Returns:
        Normalized score between 0 and 1
    
    Example:
        -196.0 → ~0.0 (very low confidence)
        0.0 → 0.5 (neutral)
        5.0 → ~0.99 (high confidence)
    """
    # CRITICAL: Handle NaN/Inf values BEFORE normalization
    import numpy as np
    if not isinstance(raw_score, (int, float)) or np.isnan(raw_score) or np.isinf(raw_score):
        logger.warning(f"Invalid raw_score: {raw_score}, using fallback 0.0")
        return 0.0
    
    return float(torch.sigmoid(torch.tensor(raw_score)))


def rerank(query: str, chunks: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]:
    """
    Rerank retrieved chunks using a cross-encoder model.
    
    IMPORTANT: Scores are normalized from raw logits to 0-1 probabilities.

    Args:
        query: The original search query.
        chunks: Candidate chunks from initial retrieval.
        top_k: Number of chunks to return after reranking.

    Returns:
        Top-k chunks sorted by cross-encoder relevance score (descending).
        Scores are normalized to 0-1 range.
    """
    import numpy as np
    
    if not chunks:
        return []

    cross_encoder = _get_cross_encoder()

    pairs = [(query, chunk.text) for chunk in chunks]
    
    try:
        # Use smaller batch size and disable progress bar to prevent hanging
        raw_scores = cross_encoder.predict(
            pairs,
            batch_size=16,  # Smaller batches for stability
            show_progress_bar=False  # Disable tqdm progress bar that can cause issues
        )
    except Exception as e:
        logger.error(f"Cross-encoder prediction failed: {e}. Using fallback scores.")
        raw_scores = [0.0] * len(pairs)

    # Normalize raw logit scores to 0-1 probabilities
    # Handle any NaN/Inf values that come from the model
    normalized_scores = []
    for i, score in enumerate(raw_scores):
        if not isinstance(score, (int, float)) or np.isnan(score) or np.isinf(score):
            logger.warning(f"Invalid score at index {i}: {score}, using fallback 0.0")
            normalized_scores.append(0.0)
        else:
            normalized_scores.append(normalize_score(score))

    # Attach updated relevance scores
    scored = list(zip(normalized_scores, chunks))
    scored.sort(key=lambda x: x[0], reverse=True)

    result: List[RetrievedChunk] = []
    for score, chunk in scored[:top_k]:
        # Ensure score is valid before assigning
        final_score = 0.0 if np.isnan(score) or np.isinf(score) else float(score)
        updated = chunk.model_copy(update={"relevance_score": final_score})
        result.append(updated)

    if result:
        top_score = result[0].relevance_score
        logger.info(f"Reranked {len(chunks)} chunks, top score: {top_score:.3f}")
    else:
        logger.info("No chunks to rerank")
        
    return result
