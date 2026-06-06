import logging
from typing import List

import anthropic

from config import config
from models.schemas import RetrievedChunk, AnswerResponse
from citation.citation_mapper import map_citations

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None

_SYSTEM_PROMPT = """You are an expert industrial maintenance engineer AI assistant for steel manufacturing plants. \
You answer questions based ONLY on the provided maintenance documents and knowledge base.

Rules:
- Always cite your sources inline using [C1], [C2], etc.
- Every factual claim must have a citation.
- If information is not in the context, say "This information is not available in the uploaded documents."
- Be specific about equipment names, part numbers, and measurements.
- Structure your answer: first a brief summary, then detailed steps or analysis.
- Never guess or invent maintenance procedures."""


def _get_client() -> anthropic.Anthropic:
    """Return the singleton Anthropic client."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
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


def generate_answer(query: str, chunks: List[RetrievedChunk]) -> AnswerResponse:
    """
    Generate a cited answer using the Anthropic LLM.

    Args:
        query: The engineer's natural language question.
        chunks: Reranked and citation-labelled chunks from retriever.

    Returns:
        AnswerResponse with answer text, resolved citations, and source chunks.
    """
    if not chunks:
        return AnswerResponse(
            answer="This information is not available in the uploaded documents.",
            citations=[],
            retrieved_chunks=[],
        )

    client = _get_client()
    user_message = _build_context_message(query, chunks)

    logger.info(f"Calling LLM ({config.LLM_MODEL}) for query: {query[:80]}...")

    response = client.messages.create(
        model=config.LLM_MODEL,
        max_tokens=config.LLM_MAX_TOKENS,
        temperature=config.LLM_TEMPERATURE,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    answer_text = response.content[0].text
    logger.info(f"LLM response received ({len(answer_text)} chars).")

    # Map citation refs in the answer back to source metadata
    citations = map_citations(answer_text, chunks)

    return AnswerResponse(
        answer=answer_text,
        citations=citations,
        retrieved_chunks=chunks,
    )
