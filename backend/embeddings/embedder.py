"""
Local text embedding using sentence-transformers.
Fully offline - runs on device using all-mpnet-base-v2 (768-dim).
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Local model singleton
_local_model = None


def _get_local_model():
    """Get or create singleton local embedding model."""
    global _local_model
    if _local_model is None:
        logger.info("Loading local embedding model: sentence-transformers/all-mpnet-base-v2 (768-dim)")
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        logger.info("✓ Local embedding model loaded successfully")
    return _local_model


def encode_texts(texts: List[str]) -> List[List[float]]:
    """
    Encode texts using local sentence-transformers model.
    
    Args:
        texts: List of strings to encode.
    
    Returns:
        List of embedding vectors (768-dim).
    """
    model = _get_local_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True
    )
    logger.info(f"Generated {len(embeddings)} local embeddings (768-dim)")
    return [emb.tolist() for emb in embeddings]


def encode_query(query: str) -> List[float]:
    """
    Encode query using local sentence-transformers model.
    
    Args:
        query: The search query.
    
    Returns:
        Embedding vector (768-dim).
    """
    model = _get_local_model()
    embedding = model.encode(query, show_progress_bar=False, convert_to_numpy=True)
    return embedding.tolist()
