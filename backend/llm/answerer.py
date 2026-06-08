import logging
from typing import List, Tuple

from google import genai
from google.genai import types

from config import config
from models.schemas import RetrievedChunk, AnswerResponse
from citation.citation_mapper import map_citations
from retrieval.confidence_scorer import generate_confidence_message

logger = logging.getLogger(__name__)

_client = None

_SYSTEM_PROMPT = """You are an expert industrial maintenance engineer AI assistant for steel manufacturing plants. \
You answer questions based ONLY on the provided maintenance documents and knowledge base.

Rules:
- Always cite your sources inline using [C1], [C2], etc.
- Every factual claim must have a citation.
- If information is partially available across multiple sources, COMBINE all retrieved evidence to provide a complete answer.
- Only say "This information is not available in the uploaded documents" when NO supporting evidence exists for the entire question.
- Be specific about equipment names, part numbers, and measurements.
- Structure your answer: first a brief summary, then detailed steps or analysis.
- Never guess or invent maintenance procedures.
- When answering questions about lists (e.g., "What are the five rules?"), always attempt to provide ALL items even if they appear in different sources.
- If the confidence level is LOW, acknowledge uncertainty and suggest manual verification."""


def _get_client():
    """Return the singleton Gemini client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GOOGLE_API_KEY)
    return _client


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

    client = _get_client()
    
    # Add confidence context to prompt for LOW confidence
    confidence_context = ""
    if confidence_level == "LOW":
        confidence_context = "\n\n⚠ NOTE: Confidence in retrieved information is LOW. Be explicit about limitations and recommend manual verification."
    elif confidence_level == "MEDIUM":
        confidence_context = "\n\n⚠ NOTE: Confidence is MODERATE. Provide the answer but suggest verification for critical operations."
    
    user_message = _build_context_message(query, chunks) + confidence_context

    logger.info(f"Calling LLM ({config.LLM_MODEL}) with {confidence_level} confidence...")

    try:
        # Build the full prompt with system instructions
        full_prompt = f"{_SYSTEM_PROMPT}\n\n{user_message}"
        
        response = client.models.generate_content(
            model=config.LLM_MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=config.LLM_MAX_TOKENS,
                temperature=config.LLM_TEMPERATURE,
            )
        )

        # Check if response was blocked or empty
        if not response.text:
            logger.warning("Empty response from Gemini API")
            answer_text = "I received an empty response. Please try rephrasing your question."
        else:
            answer_text = response.text
            
            # Prepend confidence message to answer
            if metadata["confidence_message"] and confidence_level != "HIGH":
                answer_text = f"{metadata['confidence_message']}\n\n{answer_text}"
            
            logger.info(f"LLM response received ({len(answer_text)} chars).")
    except AttributeError as e:
        logger.error(f"Gemini response blocked or invalid: {e}")
        answer_text = "I couldn't generate a response. The content may have been blocked by safety filters. Please try rephrasing your question."
    except Exception as e:
        logger.error(f"Gemini API error: {type(e).__name__}: {e}")
        answer_text = f"Error generating response: {str(e)}. Please check your Gemini API key and quota."

    # Map citation refs in the answer back to source metadata
    citations = map_citations(answer_text, chunks)

    return AnswerResponse(
        answer=answer_text,
        citations=citations,
        retrieved_chunks=chunks,
    ), metadata
