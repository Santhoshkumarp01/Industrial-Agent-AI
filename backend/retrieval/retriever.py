"""
Retrieval with parent-child support, query rewriting, and confidence scoring.

Strategy:
1. Rewrite query for better matching
2. Query matches small child chunks (precise)
3. Retrieve parent sections (complete context)
4. Calculate confidence score
5. Send parent text to LLM (not fragments)
"""

import re
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
    
    CRITICAL: Parent sections are MANDATORY for list/enumeration questions.
    If parent fetch fails, we must try harder before falling back to child chunks.
    
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
        
        logger.info(f"Fetching {len(parent_ids)} parent sections...")
        
        # Fetch parent sections using get_parent_sections utility
        parents_map = qdrant_store.get_parent_sections(list(parent_ids))
        
        if not parents_map:
            logger.error(f"⚠️ CRITICAL: Parent fetch returned 0 sections for {len(parent_ids)} IDs. This may cause list truncation!")
            return []
        
        # Convert parent data to RetrievedChunk format
        parent_chunks = []
        for parent_id, parent_data in parents_map.items():
            import json
            
            bbox = parent_data.get("bbox", [0, 0, 0, 0])
            if isinstance(bbox, str):
                bbox = json.loads(bbox)
            
            parent_chunk = RetrievedChunk(
                chunk_id=parent_id,
                doc_id=parent_data.get("doc_id", ""),
                doc_name=parent_data.get("doc_name", ""),
                equipment_tag=parent_data.get("equipment_tag", ""),
                block_type="parent_section",
                text=parent_data.get("full_text", ""),  # ← Complete section text
                page_number=parent_data.get("page_number", 0),
                bbox=tuple(bbox),
                section_heading=parent_data.get("section_heading", ""),
                relevance_score=0.95,  # High relevance since child matched
                citation_ref="",  # Will be assigned later
                parent_id=None,
            )
            parent_chunks.append(parent_chunk)
        
        logger.info(f"✓ Successfully fetched {len(parent_chunks)} parent sections with complete context.")
        return parent_chunks
            
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
        
        if equipment_tag:
            logger.info(f"🔍 Equipment filter active: '{equipment_tag}' - retrieved {len(candidates)} candidates")
        else:
            logger.info(f"🔍 No equipment filter - searching all documents - retrieved {len(candidates)} candidates")
        
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

    # Step 4: Calculate CHILD confidence (used as baseline before parent upgrade)
    confidence_score, confidence_level, confidence_details = calculate_confidence(
        query=query,
        retrieved_chunks=reranked
    )
    metadata["confidence_score"] = confidence_score
    metadata["confidence_level"] = confidence_level
    metadata["confidence_details"] = confidence_details
    
    # Step 5: Parent-child retrieval (fetch full context)
    # CRITICAL: For list questions, parent sections are MANDATORY (not optional)
    query_lower = query.lower()
    is_list_question = bool(
        # Match list questions regardless of specific count
        re.search(r'\b(five|three|four|six|seven|eight|ten|all|any)\s+(rules?|levels?|features?|steps?|requirements?|procedures?|instructions?)\b', query_lower) or
        re.search(r'\bwhat are the\s+\d*\s*(rules?|levels?|features?|steps?|requirements?|procedures?|instructions?)\b', query_lower) or
        re.search(r'\b(list|enumerate)\b', query_lower) or
        # NEW: Match questions asking for items without specific count
        re.search(r'\bwhat.*\b(safety|maintenance|operational)\b.*(rules?|levels?|features?|steps?|procedures?|instructions?)\b', query_lower)
    )
    
    parent_fetch_succeeded = False
    
    if use_parent_retrieval and (is_list_question or confidence_score >= 0.3):
        try:
            logger.info("Fetching parent sections for complete context...")
            parent_chunks = _fetch_parent_sections(reranked)
            
            if parent_chunks:
                logger.info(f"✓ Retrieved {len(parent_chunks)} parent sections with full context.")
                # Use parent sections instead of child fragments
                reranked = parent_chunks
                parent_fetch_succeeded = True

                # Phase 2 Fix: Recalculate confidence using parent sections.
                # Parent sections have relevance_score=0.95 (high match since child matched).
                # This avoids cross-encoder child scores (0.5-0.75) dragging confidence to MEDIUM.
                parent_confidence, parent_level, parent_details = calculate_confidence(
                    query=query,
                    retrieved_chunks=reranked
                )
                # Only upgrade confidence — never downgrade from child-level assessment
                if parent_confidence > confidence_score:
                    metadata["confidence_score"] = parent_confidence
                    metadata["confidence_level"] = parent_level
                    metadata["confidence_details"] = parent_details
                    logger.info(f"Confidence upgraded after parent retrieval: {confidence_level}→{parent_level} ({confidence_score:.2f}→{parent_confidence:.2f})")
            else:
                if is_list_question:
                    logger.error("⚠️ CRITICAL: Parent sections not found for LIST QUESTION. Answer may be incomplete!")
                    if reranked:
                        logger.warning(f"Falling back to single best child chunk (score: {reranked[0].relevance_score:.3f})")
                        reranked = reranked[:1]
                logger.warning("Parent sections not found, using child chunks.")
        except Exception as e:
            logger.error(f"Parent retrieval failed: {e}. Using child chunks.")
            if is_list_question and reranked:
                logger.warning(f"LIST QUESTION: Using only top chunk to avoid fragment merging")
                reranked = reranked[:1]
    
    # Mark retrieval as degraded if parent fetch failed for list question
    if is_list_question and not parent_fetch_succeeded:
        metadata["retrieval_degraded"] = True
        metadata["degradation_reason"] = "Parent section fetch failed for list question"
        logger.warning(f"⚠️ DEGRADED RETRIEVAL: {metadata['degradation_reason']}")
    
    # Step 6: Assign citations
    final_chunks: List[RetrievedChunk] = []
    for i, chunk in enumerate(reranked):
        cited = chunk.model_copy(update={"citation_ref": f"[C{i + 1}]"})
        final_chunks.append(cited)

    return final_chunks, metadata
