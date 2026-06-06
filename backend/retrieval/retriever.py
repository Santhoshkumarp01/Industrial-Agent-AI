import logging
from typing import List, Optional

from embeddings.embedder import encode_query
from vectorstore import qdrant_store
from retrieval.reranker import rerank
from models.schemas import RetrievedChunk
import config

logger = logging.getLogger(__name__)


def retrieve(
    query: str,
    equipment_tag: Optional[str] = None,
    top_k: int = config.TOP_K_RETRIEVAL,
) -> List[RetrievedChunk]:
    """
    Full retrieval pipeline: embed → hybrid vector search → rerank → assign citations.

    Args:
        query: Natural language question from the engineer.
        equipment_tag: Optional filter to scope retrieval to a specific equipment tag.
        top_k: Number of candidates to fetch before reranking.

    Returns:
        List of top-ranked RetrievedChunk objects with citation refs assigned.
    """
    # Step 1: Encode query (dense vector)
    logger.info(f"Encoding query: {query[:80]}...")
    query_embedding = encode_query(query)

    if equipment_tag:
        logger.info(f"Applying equipment_tag filter: {equipment_tag}")

    # Step 2: Hybrid search — passes both dense vector AND raw text for BM25
    candidates = qdrant_store.query(
        query_dense=query_embedding,
        query_text=query,           # raw text → BM25 sparse encoding inside qdrant_store
        top_k=top_k,
        equipment_tag=equipment_tag,
    )
    logger.info(f"Retrieved {len(candidates)} candidates from Qdrant (hybrid search).")

    if not candidates:
        return []

    # Step 3: Rerank with cross-encoder
    reranked = rerank(query=query, chunks=candidates, top_k=config.TOP_K_FINAL)
    logger.info(f"Reranked to {len(reranked)} final chunks.")

    # Step 4: Assign citation refs [C1], [C2], ...
    final_chunks: List[RetrievedChunk] = []
    for i, chunk in enumerate(reranked):
        cited = chunk.model_copy(update={"citation_ref": f"[C{i + 1}]"})
        final_chunks.append(cited)

    return final_chunks
