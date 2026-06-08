"""
Text embedding with automatic fallback:
1. Try Hugging Face API (FREE - 30K/month, no per-minute limits)
2. Fallback to local sentence-transformers if network fails
"""

import logging
from typing import List
import requests
import os
import time

logger = logging.getLogger(__name__)

# Hugging Face API configuration
HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-mpnet-base-v2"
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY", None)

# Local model fallback
_local_model = None
_use_local = False  # Flag to skip API after first failure


def _get_local_model():
    """Get or create singleton local embedding model."""
    global _local_model
    if _local_model is None:
        logger.info("Loading local embedding model: sentence-transformers/all-mpnet-base-v2 (768-dim)")
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        logger.info("✓ Local embedding model loaded successfully")
    return _local_model


def _encode_with_api(texts: List[str]) -> List[List[float]]:
    """Try to encode using Hugging Face API."""
    if not HF_API_KEY:
        raise ValueError("HUGGINGFACE_API_KEY not found")
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    embeddings = []
    
    batch_size = 32
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json={"inputs": batch, "options": {"wait_for_model": True}},
            timeout=30
        )
        response.raise_for_status()
        
        batch_embeddings = response.json()
        if isinstance(batch_embeddings, list):
            embeddings.extend(batch_embeddings)
        else:
            raise ValueError(f"Unexpected response format: {batch_embeddings}")
    
    return embeddings


def _encode_with_local(texts: List[str]) -> List[List[float]]:
    """Encode using local sentence-transformers model."""
    model = _get_local_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True
    )
    return [emb.tolist() for emb in embeddings]


def encode_texts(texts: List[str]) -> List[List[float]]:
    """
    Encode texts with automatic fallback:
    1. Try Hugging Face API (no server CPU load)
    2. Fallback to local model if API fails
    
    Args:
        texts: List of strings to encode.
    
    Returns:
        List of embedding vectors (768-dim).
    """
    global _use_local
    
    # If we've already determined to use local, skip API
    if _use_local:
        logger.info(f"Using local embeddings for {len(texts)} texts (API unavailable)")
        return _encode_with_local(texts)
    
    # Try API first
    try:
        embeddings = _encode_with_api(texts)
        logger.info(f"Generated {len(embeddings)} embeddings using Hugging Face API (768-dim)")
        return embeddings
        
    except Exception as e:
        logger.warning(f"Hugging Face API failed: {e}. Falling back to local embeddings...")
        _use_local = True  # Skip API for future calls
        return _encode_with_local(texts)


def encode_query(query: str) -> List[float]:
    """
    Encode query with automatic fallback:
    1. Try Hugging Face API (no server CPU load)
    2. Fallback to local model if API fails
    
    Args:
        query: The search query.
    
    Returns:
        Embedding vector (768-dim).
    """
    global _use_local
    
    # If we've already determined to use local, skip API
    if _use_local:
        model = _get_local_model()
        embedding = model.encode(query, show_progress_bar=False, convert_to_numpy=True)
        return embedding.tolist()
    
    # Try API first
    try:
        if not HF_API_KEY:
            raise ValueError("HUGGINGFACE_API_KEY not found")
        
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json={"inputs": query, "options": {"wait_for_model": True}},
            timeout=30
        )
        response.raise_for_status()
        
        embedding = response.json()
        if isinstance(embedding, list):
            return embedding[0] if isinstance(embedding[0], list) else embedding
        else:
            raise ValueError(f"Unexpected response format")
            
    except Exception as e:
        logger.warning(f"Hugging Face API failed: {e}. Falling back to local embeddings...")
        _use_local = True  # Skip API for future calls
        model = _get_local_model()
        embedding = model.encode(query, show_progress_bar=False, convert_to_numpy=True)
        return embedding.tolist()
