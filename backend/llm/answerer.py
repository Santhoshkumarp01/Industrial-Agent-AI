import logging
from typing import List, Tuple

from config import config
from models.schemas import RetrievedChunk, AnswerResponse
from citation.citation_mapper import map_citations
from retrieval.confidence_scorer import generate_confidence_message
from llm.local_llm import generate as llm_generate

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a strict maintenance QA assistant for the 1PH718 motor manual.

TASK:
Answer the user's question only from the provided manual context.

STRICT RULES:
1. Use only the retrieved manual text. Do not add outside knowledge unless the manual is silent.
2. If the question uses different words than the manual, map them to the closest manual term only when the meaning clearly matches.
   Example: "lockout/tagout" maps to "isolate," "protect against reconnection," and "verify that the equipment is not live."
3. If the manual does not explicitly state the answer, say: "The manual does not explicitly state this, but the closest related instruction is..."
4. Do not invent safety levels, procedures, or technical details.
5. Keep the answer short, direct, and factual.
6. If the retrieved context is weak or unrelated, say: "I could not confirm this from the manual."
7. For safety questions, prefer exact manual wording over general safety language.
8. Never answer with assumptions.

CITATION RULES:
- Always cite your sources inline using [C1], [C2], etc.
- Every factual claim must have a citation.
- Always include the page number when information is found.

ANSWER FORMAT:
- Direct answer in 1-2 sentences.
- Then, if needed, a short note: "Based on page/section..."

EXAMPLE:
User: When preparing to work on a 1PH718 motor, which action best reflects the lockout/tagout safety rule?
Answer: Isolate the motor from power, protect against reconnection, and verify that it is not live before starting maintenance [C1]. This matches the manual's safety rules on page 57."""


def _build_context_message(query: str, chunks: List[RetrievedChunk]) -> str:
    """Format retrieved chunks as context for the LLM."""
    context_parts = []
    for chunk in chunks:
        context_parts.append(
            f"{chunk.citation_ref} (Page {chunk.page_number}, {chunk.doc_name}, "
            f"Section: {chunk.section_heading})\n{chunk.text}"
        )

    context_block = "\n\n".join(context_parts)
    return f"Context documents:\n{context_block}\n\nQuestion: {query}"


def generate_answer(
    query: str, 
    chunks: List[RetrievedChunk],
    confidence_score: float = None,
    confidence_level: str = None,
    confidence_details: dict = None
) -> Tuple[AnswerResponse, dict]:
    """
    Generate a cited answer with confidence awareness.

    Args:
        query: The engineer's natural language question.
        chunks: Reranked and citation-labelled chunks from retriever.
        confidence_score: Confidence score from retriever
        confidence_level: "HIGH" | "MEDIUM" | "LOW"
        confidence_details: Detailed confidence breakdown

    Returns:
        Tuple of (AnswerResponse, metadata)
    """
    metadata = {
        "confidence_score": confidence_score or 0.0,
        "confidence_level": confidence_level or "UNKNOWN",
        "confidence_message": "",
    }
    
    if not chunks:
        metadata["confidence_message"] = "No relevant information found"
        return AnswerResponse(
            answer="This information is not available in the uploaded documents.",
            citations=[],
            retrieved_chunks=[],
        ), metadata

    # Generate confidence message
    if confidence_score is not None and confidence_level and confidence_details:
        confidence_msg = generate_confidence_message(
            confidence_score, confidence_level, confidence_details
        )
        metadata["confidence_message"] = confidence_msg
        logger.info(f"Confidence: {confidence_msg}")

    # Add confidence context to prompt for LOW confidence
    confidence_context = ""
    if confidence_level == "LOW":
        confidence_context = "\n\n⚠ NOTE: Confidence in retrieved information is LOW. Be explicit about limitations and recommend manual verification."
    elif confidence_level == "MEDIUM":
        confidence_context = "\n\n⚠ NOTE: Confidence is MODERATE. Provide the answer but suggest verification for critical operations."
    
    user_message = _build_context_message(query, chunks) + confidence_context

    logger.info(f"Calling fine-tuned model with {confidence_level} confidence...")

    try:
        # Use fine-tuned model for RAG answer generation
        answer_text = llm_generate(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_message,
            max_tokens=800
        )
        
        # Prepend confidence message to answer
        if metadata["confidence_message"] and confidence_level != "HIGH":
            answer_text = f"{metadata['confidence_message']}\n\n{answer_text}"
        
        logger.info(f"Model response received ({len(answer_text)} chars).")
    except Exception as e:
        logger.error(f"Model inference error: {type(e).__name__}: {e}")
        answer_text = f"Error generating response: {str(e)}. The model may still be loading."

    # Map citation refs in the answer back to source metadata
    citations = map_citations(answer_text, chunks)

    return AnswerResponse(
        answer=answer_text,
        citations=citations,
        retrieved_chunks=chunks,
    ), metadata
