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
from google import genai
from google.genai import types
from config import config

logger = logging.getLogger(__name__)

# Initialize client
_client = None

def _get_client():
    """Get or create singleton client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GOOGLE_API_KEY)
    return _client


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
    relevance_scores = [c.relevance_score for c in retrieved_chunks[:5]]
    scores["retrieval_quality"] = np.mean(relevance_scores) if relevance_scores else 0.0
    
    # 2. Top Chunk Score (best match)
    scores["top_chunk_score"] = retrieved_chunks[0].relevance_score if retrieved_chunks else 0.0
    
    # 3. Chunk Consistency (do chunks agree?)
    # Simple heuristic: if top 3 chunks have similar scores, they're consistent
    if len(retrieved_chunks) >= 3:
        top_3_scores = [c.relevance_score for c in retrieved_chunks[:3]]
        score_variance = np.var(top_3_scores)
        # Low variance = high consistency
        scores["chunk_consistency"] = max(0.0, 1.0 - (score_variance * 2))
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
    
    # Determine confidence level
    if confidence_score >= 0.75:
        confidence_level = "HIGH"
    elif confidence_score >= 0.45:
        confidence_level = "MEDIUM"
    else:
        confidence_level = "LOW"
    
    details = {
        "score": round(confidence_score, 2),
        "level": confidence_level,
        "breakdown": {k: round(v, 2) for k, v in scores.items()},
        "num_chunks": len(retrieved_chunks),
        "top_score": round(scores["top_chunk_score"], 2),
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
    
    Returns:
        Message to display to user about answer quality
    """
    if confidence_level == "HIGH":
        return f"✓ High confidence answer (score: {confidence_score:.0%}) based on {details['num_chunks']} relevant manual sections."
    
    elif confidence_level == "MEDIUM":
        return f"⚠ Moderate confidence (score: {confidence_score:.0%}). Answer based on {details['num_chunks']} chunks. Please verify with supervisor if critical."
    
    else:  # LOW
        reasons = []
        breakdown = details.get("breakdown", {})
        
        if breakdown.get("top_chunk_score", 0) < 0.4:
            reasons.append("low relevance")
        if breakdown.get("coverage", 0) < 0.4:
            reasons.append("insufficient detail")
        if breakdown.get("chunk_consistency", 0) < 0.4:
            reasons.append("inconsistent information")
        
        reason_text = ", ".join(reasons) if reasons else "limited evidence"
        return f"⚠ Low confidence (score: {confidence_score:.0%}) due to {reason_text}. Answer may be incomplete or unreliable. Please consult manual directly."


def assess_answer_quality_with_llm(
    query: str,
    answer: str,
    retrieved_chunks: List[RetrievedChunk]
) -> Tuple[float, str]:
    """
    Use LLM to assess if the generated answer actually addresses the query.
    
    This is a more sophisticated check than just retrieval scores.
    
    Returns:
        Tuple of (quality_score, explanation)
    """
    try:
        client = _get_client()
        
        chunk_texts = "\n\n".join([
            f"Chunk {i+1}: {c.text[:200]}..."
            for i, c in enumerate(retrieved_chunks[:3])
        ])
        
        prompt = f"""Assess the quality of this answer to the user's query.

Query: "{query}"

Answer: "{answer}"

Source Chunks:
{chunk_texts}

Rate the answer quality on these criteria:
1. Completeness: Does it fully address the query?
2. Accuracy: Is it consistent with the source chunks?
3. Clarity: Is it clear and actionable?

Respond with:
Score: [0.0-1.0]
Reason: [One sentence explanation]

Format:
Score: 0.85
Reason: Answer is complete and accurate but could be more specific about torque values."""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=100,
                temperature=0.1,
            )
        )
        
        text = response.text.strip()
        
        # Parse response
        score = 0.5
        reason = "Unable to assess"
        
        for line in text.split('\n'):
            if line.startswith('Score:'):
                try:
                    score = float(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith('Reason:'):
                reason = line.split(':', 1)[1].strip()
        
        logger.info(f"LLM quality assessment: {score:.2f} - {reason}")
        return score, reason
        
    except Exception as e:
        logger.error(f"LLM quality assessment failed: {e}")
        return 0.5, "Assessment unavailable"
