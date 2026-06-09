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


def _fetch_parent_sections(child_chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
    """
    Fetch full parent sections for the given child chunks.
    
    Parent sections contain complete context (full paragraphs, complete lists, etc.)
    instead of fragments. This dramatically improves answer quality for structured content.
    
    Args:
        child_chunks: List of small child chunks from search
    
    Returns:
        List of parent sections with full context, or empty list if not found
    """
    try:
        # Extract unique parent IDs from child chunks
        parent_ids = set()
        for chunk in child_chunks:
            # Get parent_id from payload (stored during ingestion)
            if hasattr(chunk, 'parent_id') and chunk.parent_id:
                parent_ids.add(chunk.parent_id)
        
        if not parent_ids:
            logger.warning("No parent IDs found in child chunks - using child chunks directly")
            return []
        
        logger.info(f"Fetching {len(parent_ids)} parent sections from Qdrant...")
        
        # Fetch parent sections from parent collection
        parent_collection = f"{config.QDRANT_COLLECTION}_parents"
        parent_chunks = []
        
        try:
            client = qdrant_store.get_client()
            
            for parent_id in parent_ids:
                try:
                    # Retrieve parent by ID
                    result = client.retrieve(
                        collection_name=parent_collection,
                        ids=[parent_id],
                        with_payload=True,
                        with_vectors=False,
                    )
                    
                    if result:
                        # Convert parent point to RetrievedChunk format
                        parent_point = result[0]
                        parent_chunk = RetrievedChunk(
                            chunk_id=str(parent_point.id),
                            doc_id=parent_point.payload.get("doc_id", ""),
                            doc_name=parent_point.payload.get("doc_name", ""),
                            equipment_tag=parent_point.payload.get("equipment_tag", ""),
                            block_type=parent_point.payload.get("block_type", "parent_section"),
                            text=parent_point.payload.get("text", ""),
                            page_number=parent_point.payload.get("page_number", 0),
                            bbox=tuple(parent_point.payload.get("bbox", [0, 0, 0, 0])),
                            section_heading=parent_point.payload.get("section_heading", ""),
                            relevance_score=0.9,  # High relevance since child matched
                            citation_ref="",  # Will be assigned later
                            parent_id=None,
                        )
                        parent_chunks.append(parent_chunk)
                except Exception as e:
                    logger.error(f"Failed to fetch parent ID {parent_id}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(parent_chunks)} parent sections.")
            return parent_chunks
            
        except Exception as e:
            logger.error(f"Qdrant client error when fetching parent sections: {type(e).__name__}: {e}")
            logger.exception("Parent fetch traceback:")
            return []
    except Exception as e:
        logger.error(f"Unexpected error in _fetch_parent_sections: {type(e).__name__}: {e}")
        logger.exception("Parent fetch wrapper traceback:")
        return []


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
    
    # Step 5: Parent-child retrieval (fetch full context)
    if use_parent_retrieval and confidence_score >= 0.3:
        try:
            logger.info("Fetching parent sections for complete context...")
            parent_chunks = _fetch_parent_sections(reranked)
            
            if parent_chunks:
                logger.info(f"Retrieved {len(parent_chunks)} parent sections with full context.")
                # Use parent sections instead of child fragments
                reranked = parent_chunks
            else:
                logger.warning("Parent sections not found, using child chunks.")
        except Exception as e:
            logger.error(f"Parent retrieval failed: {e}. Using child chunks.")
            # Continue with child chunks on error
    
    # Step 6: Assign citations
    final_chunks: List[RetrievedChunk] = []
    for i, chunk in enumerate(reranked):
        cited = chunk.model_copy(update={"citation_ref": f"[C{i + 1}]"})
        final_chunks.append(cited)

    return final_chunks, metadata
