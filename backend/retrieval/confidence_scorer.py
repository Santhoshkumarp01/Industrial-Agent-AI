"""
Confidence Scorer — Estimates answer quality before presenting to user.

Scoring Factors:
1. Retrieval relevance scores
2. Semantic similarity between query and retrieved chunks
3. Coverage (how much of query is addressed)
4. Source quality (manual vs feedback)
5. Consistency (chunks agree or contradict)

Confidence Levels:
- HIGH (0.8-1.0): Strong evidence, clear answer
- MEDIUM (0.5-0.8): Some evidence, possibly incomplete
- LOW (0.0-0.5): Weak evidence, may be unreliable
"""

import logging
import numpy as np
from typing import List, Tuple
from models.schemas import RetrievedChunk

logger = logging.getLogger(__name__)


def calculate_confidence(
    query: str,
    retrieved_chunks: List[RetrievedChunk],
    generated_answer: str = None
) -> Tuple[float, str, dict]:
    """
    Calculate confidence score for the retrieval + answer.
    
    Args:
        query: User's original query
        retrieved_chunks: Retrieved chunks from vector DB
        generated_answer: LLM-generated answer (optional)
    
    Returns:
        Tuple of (confidence_score, confidence_level, details)
        - confidence_score: 0.0-1.0
        - confidence_level: "HIGH" | "MEDIUM" | "LOW"
        - details: Dict with scoring breakdown
    """
    if not retrieved_chunks:
        return 0.0, "LOW", {"reason": "No relevant chunks found"}
    
    scores = {
        "retrieval_quality": 0.0,
        "top_chunk_score": 0.0,
        "chunk_consistency": 0.0,
        "coverage": 0.0,
        "source_quality": 0.0,
    }
    
    # 1. Retrieval Quality (average of top chunks)
    relevance_scores = [c.relevance_score for c in retrieved_chunks[:5] if not np.isnan(c.relevance_score)]
    scores["retrieval_quality"] = float(np.mean(relevance_scores)) if relevance_scores else 0.0
    
    # 2. Top Chunk Score (best match)
    top_score = retrieved_chunks[0].relevance_score if retrieved_chunks else 0.0
    scores["top_chunk_score"] = 0.0 if np.isnan(top_score) else float(top_score)
    
    # 3. Chunk Consistency (do chunks agree?)
    # Simple heuristic: if top 3 chunks have similar scores, they're consistent
    if len(retrieved_chunks) >= 3:
        top_3_scores = [c.relevance_score for c in retrieved_chunks[:3] if not np.isnan(c.relevance_score)]
        if len(top_3_scores) >= 2:
            score_variance = float(np.var(top_3_scores))
            # Low variance = high consistency (handle NaN case)
            scores["chunk_consistency"] = max(0.0, min(1.0, 1.0 - (score_variance * 2)))
        else:
            scores["chunk_consistency"] = 0.5
    else:
        scores["chunk_consistency"] = 0.7  # Default for few chunks
    
    # 4. Coverage (are chunks long enough to answer?)
    total_tokens = sum(c.text.count(' ') + 1 for c in retrieved_chunks[:5])
    # Assume 100+ tokens needed for good coverage
    scores["coverage"] = min(1.0, total_tokens / 100.0)
    
    # 5. Source Quality (manuals > feedback corrections)
    manual_chunks = sum(1 for c in retrieved_chunks[:5] if c.block_type != "feedback_correction")
    scores["source_quality"] = manual_chunks / min(5, len(retrieved_chunks))
    
    # Weighted combination
    weights = {
        "retrieval_quality": 0.35,
        "top_chunk_score": 0.25,
        "chunk_consistency": 0.15,
        "coverage": 0.15,
        "source_quality": 0.10,
    }
    
    confidence_score = sum(scores[k] * weights[k] for k in scores.keys())
    
    # CRITICAL: Ensure confidence_score is never NaN or infinite
    if np.isnan(confidence_score) or np.isinf(confidence_score):
        logger.warning(f"Invalid confidence score detected: {confidence_score}. Using fallback value 0.1")
        confidence_score = 0.1  # Fallback to low confidence
    
    # Ensure it's in valid range
    confidence_score = float(max(0.0, min(1.0, confidence_score)))
    
    # Phase 4 Fix: Recalibrated thresholds
    # Old thresholds (HIGH ≥ 0.75, MEDIUM 0.45–0.75) were too strict.
    # Cross-encoder child scores (0.5–0.93) after parent retrieval (all set to 0.95)
    # means effective range for correct answers is 0.55–0.80.
    # New thresholds match the realistic score distribution.
    if confidence_score >= 0.60:
        confidence_level = "HIGH"
    elif confidence_score >= 0.35:
        confidence_level = "MEDIUM"
    else:
        confidence_level = "LOW"
    
    details = {
        "score": float(round(confidence_score, 2)),
        "level": confidence_level,
        "breakdown": {k: float(round(v, 2)) for k, v in scores.items()},
        "num_chunks": len(retrieved_chunks),
        "top_score": float(round(scores["top_chunk_score"], 2)),
    }
    
    logger.info(
        f"Confidence: {confidence_level} ({confidence_score:.2f}) - "
        f"Top chunk: {scores['top_chunk_score']:.2f}, "
        f"Coverage: {scores['coverage']:.2f}"
    )
    
    return confidence_score, confidence_level, details


def should_answer(
    query: str,
    retrieved_chunks: List[RetrievedChunk],
    min_confidence: float = 0.3
) -> Tuple[bool, str]:
    """
    Decide whether to answer the query or admit uncertainty.
    
    Args:
        query: User query
        retrieved_chunks: Retrieved chunks
        min_confidence: Minimum confidence threshold
    
    Returns:
        Tuple of (should_answer, reason)
    """
    confidence_score, level, details = calculate_confidence(query, retrieved_chunks)
    
    if confidence_score < min_confidence:
        reason = f"Confidence too low ({confidence_score:.2f}). "
        
        if not retrieved_chunks:
            reason += "No relevant information found in knowledge base."
        elif details["breakdown"]["coverage"] < 0.3:
            reason += "Retrieved chunks don't contain enough detail to answer."
        elif details["breakdown"]["top_chunk_score"] < 0.3:
            reason += "Retrieved information has low relevance to your query."
        else:
            reason += "Retrieved information may be incomplete or unclear."
        
        return False, reason
    
    return True, f"Answering with {level} confidence ({confidence_score:.2f})"


def generate_confidence_message(
    confidence_score: float,
    confidence_level: str,
    details: dict
) -> str:
    """
    Generate user-friendly confidence message.

    Phase 4 Fix:
    - HIGH → no prefix (clean answer)
    - MEDIUM → brief verification note
    - LOW → explicit warning with reason
    - Answers from memory (no citation) get a special note instead

    Returns:
        Message to prepend to answer, or empty string for HIGH confidence.
    """
    if confidence_level == "HIGH":
        # Phase 4 Fix: No prefix for HIGH confidence — don't clutter correct answers
        return ""

    elif confidence_level == "MEDIUM":
        return (
            f"⚠ Moderate confidence ({confidence_score:.0%}). "
            f"Verify with manual if used for critical operations."
        )

    else:  # LOW
        reasons = []
        breakdown = details.get("breakdown", {})

        if breakdown.get("top_chunk_score", 0) < 0.4:
            reasons.append("low retrieval relevance")
        if breakdown.get("coverage", 0) < 0.4:
            reasons.append("insufficient context detail")
        if breakdown.get("chunk_consistency", 0) < 0.4:
            reasons.append("inconsistent sources")

        reason_text = ", ".join(reasons) if reasons else "limited evidence in retrieved sections"
        return (
            f"⚠ Low confidence ({confidence_score:.0%}) — {reason_text}. "
            f"Please consult the manual directly for critical decisions."
        )


def assess_answer_quality_with_llm(
    query: str,
    answer: str,
    retrieved_chunks: List[RetrievedChunk]
) -> Tuple[float, str]:
    """
    Rule-based answer quality assessment.
    
    Returns:
        Tuple of (quality_score, explanation)
    """
    # Simple rule-based quality check
    score = 0.5
    reason = "Answer generated from retrieved knowledge"
    
    # Check if answer is not empty
    if not answer or len(answer.strip()) < 20:
        return 0.2, "Answer too short or empty"
    
    # Check if we have good retrieval
    if retrieved_chunks and len(retrieved_chunks) > 0:
        avg_relevance = np.mean([c.relevance_score for c in retrieved_chunks[:3]])
        score = min(0.95, 0.5 + (avg_relevance * 0.5))
        reason = f"Answer based on {len(retrieved_chunks)} retrieved chunks with avg relevance {avg_relevance:.2f}"
    
    logger.info(f"Rule-based quality assessment: {score:.2f} - {reason}")
    return score, reason
