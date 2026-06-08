"""
Text embedding using Google's gemini-embedding-001 model (768-dim).
"""

import logging
from typing import List
import time
from google import genai
from google.genai import types
from config import config

logger = logging.getLogger(__name__)

# Initialize Google AI client
_client = None

def _get_client():
    """Get or create singleton client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GOOGLE_API_KEY)
    return _client

# Retry configuration for network issues
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def encode_texts(texts: List[str]) -> List[List[float]]:
    """
    Encode a list of texts into embedding vectors using gemini-embedding-001 (768-dim).
    Includes retry logic for network issues.

    Args:
        texts: List of strings to encode.

    Returns:
        List of embedding vectors as plain Python lists.
    """
    client = _get_client()
    embeddings = []
    
    # Process in batches for efficiency
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        for text in batch:
            # Retry logic for each embedding
            for attempt in range(MAX_RETRIES):
                try:
                    result = client.models.embed_content(
                        model=config.EMBEDDING_MODEL,
                        contents=text,
                        config=types.EmbedContentConfig(
                            output_dimensionality=768,
                            task_type="RETRIEVAL_DOCUMENT"
                        )
                    )
                    
                    if hasattr(result, 'embeddings') and len(result.embeddings) > 0:
                        embeddings.append(result.embeddings[0].values)
                        break  # Success, exit retry loop
                    else:
                        raise ValueError("No embeddings in response")
                    
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Embedding attempt {attempt + 1} failed: {e}. Retrying in {RETRY_DELAY}s...")
                        time.sleep(RETRY_DELAY)
                    else:
                        logger.error(f"Failed to generate embedding after {MAX_RETRIES} attempts: {e}")
                        raise
    
    logger.info(f"Generated {len(embeddings)} embeddings using {config.EMBEDDING_MODEL} (768-dim)")
    return embeddings


def encode_query(query: str) -> List[float]:
    """
    Encode a single query string into an embedding vector (768-dim).
    Includes retry logic for network issues.

    Args:
        query: The search query.

    Returns:
        Embedding vector as a plain Python list.
    """
    client = _get_client()
    
    for attempt in range(MAX_RETRIES):
        try:
            result = client.models.embed_content(
                model=config.EMBEDDING_MODEL,
                contents=query,
                config=types.EmbedContentConfig(
                    output_dimensionality=768,
                    task_type="RETRIEVAL_QUERY"
                )
            )
            
            if hasattr(result, 'embeddings') and len(result.embeddings) > 0:
                return result.embeddings[0].values
            else:
                raise ValueError("No embeddings in response")
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Query embedding attempt {attempt + 1} failed: {e}. Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed to generate query embedding after {MAX_RETRIES} attempts: {e}")
                raise
