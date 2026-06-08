"""
Retrieval with parent-child support, query rewriting, and confidence scoring.

Strategy:
1. Rewrite query for better matching
2. Query matches small child chunks (precise)
3. Retrieve parent sections (complete context)
4. Calculate confidence score
5. Send parent text to LLM (not fragments)
"""

import logging
from typing import List, Optional, Tuple

from embeddings.embedder import encode_query
from vectorstore import qdrant_store
from retrieval.reranker import rerank
from retrieval.query_rewriter import rewrite_query
from retrieval.confidence_scorer import calculate_confidence
from models.schemas import RetrievedChunk
from config import config

logger = logging.getLogger(__name__)


def retrieve(
    query: str,
    equipment_tag: Optional[str] = None,
    top_k: int = config.TOP_K_RETRIEVAL,
    use_query_rewriting: bool = True,
    use_parent_retrieval: bool = True,
) -> Tuple[List[RetrievedChunk], dict]:
    """
    Full retrieval pipeline with query rewriting and confidence scoring.

    Args:
        query: Natural language question
        equipment_tag: Optional filter
        top_k: Number of candidates before rerank
        use_query_rewriting: Enable query rewriting
        use_parent_retrieval: Enable parent-child retrieval

    Returns:
        Tuple of (chunks, metadata)
        - chunks: List of RetrievedChunk
        - metadata: Dict with confidence_score, queries_tried, etc.
    """
    metadata = {
        "original_query": query,
        "queries_tried": [query],
        "confidence_score": 0.0,
        "confidence_level": "LOW",
        "confidence_details": {},
    }
    
    # Step 1: Query Rewriting
    queries_to_try = [query]
    if use_query_rewriting:
        logger.info("Rewriting query for better retrieval...")
        queries_to_try = rewrite_query(query, use_variations=True)
        metadata["queries_tried"] = queries_to_try
        logger.info(f"Generated {len(queries_to_try)} query variations")
    
    # Step 2: Try each query variation and collect results
    all_candidates = []
    seen_chunk_ids = set()
    
    for q in queries_to_try:
        logger.info(f"Trying query: {q[:80]}...")
        
        # Encode and search
        query_embedding = encode_query(q)
        
        candidates = qdrant_store.query(
            query_dense=query_embedding,
            query_text=q,
            top_k=top_k,
            equipment_tag=equipment_tag,
        )
        
        # Deduplicate by chunk_id
        for c in candidates:
            if c.chunk_id not in seen_chunk_ids:
                all_candidates.append(c)
                seen_chunk_ids.add(c.chunk_id)
    
    logger.info(f"Retrieved {len(all_candidates)} unique candidates across all query variations.")

    if not all_candidates:
        return [], metadata

    # Step 3: Rerank using ORIGINAL query (most important)
    reranked = rerank(query=query, chunks=all_candidates, top_k=config.TOP_K_FINAL)
    logger.info(f"Reranked to {len(reranked)} child chunks.")

    # Step 4: Calculate confidence
    confidence_score, confidence_level, confidence_details = calculate_confidence(
        query=query,
        retrieved_chunks=reranked
    )
    metadata["confidence_score"] = confidence_score
    metadata["confidence_level"] = confidence_level
    metadata["confidence_details"] = confidence_details
    
    # Step 5: Parent-child retrieval (if enabled and confidence is reasonable)
    if use_parent_retrieval and confidence_score >= 0.3:
        logger.info("Parent-child retrieval enabled but not fully implemented yet")
        # TODO: Fetch parent sections based on parent_id
        # This requires updating RetrievedChunk to include parent_id
    
    # Step 6: Assign citations
    final_chunks: List[RetrievedChunk] = []
    for i, chunk in enumerate(reranked):
        cited = chunk.model_copy(update={"citation_ref": f"[C{i + 1}]"})
        final_chunks.append(cited)

    return final_chunks, metadata
