import logging
from typing import List

from sentence_transformers import SentenceTransformer

from config import config

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Return the singleton SentenceTransformer model, loading it on first call."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
        logger.info("Embedding model loaded.")
    return _model


def encode_texts(texts: List[str]) -> List[List[float]]:
    """
    Encode a list of texts into embedding vectors.

    Args:
        texts: List of strings to encode.

    Returns:
        List of embedding vectors as plain Python lists.
    """
    model = get_model()
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
    # Convert numpy arrays to plain Python lists (Qdrant needs lists not numpy arrays)
    return [emb.tolist() for emb in embeddings]


def encode_query(query: str) -> List[float]:
    """
    Encode a single query string into an embedding vector.

    Args:
        query: The search query.

    Returns:
        Embedding vector as a plain Python list.
    """
    model = get_model()
    embedding = model.encode([query], show_progress_bar=False)[0]
    return embedding.tolist()
