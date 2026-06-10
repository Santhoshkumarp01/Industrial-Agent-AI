import logging
from typing import List, Tuple

from config import config
from models.schemas import RetrievedChunk, AnswerResponse
from citation.citation_mapper import map_citations
from retrieval.confidence_scorer import generate_confidence_message
from llm.local_llm import generate as llm_generate

logger = logging.getLogger(__name__)

# VERSION MARKER - Check this appears in logs to confirm code is loaded
ANSWERER_VERSION = "CITATION_FORMAT_ENFORCEMENT_v5"
logger.info(f"🔧 ANSWERER MODULE LOADED: {ANSWERER_VERSION}")

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

CRITICAL LIST RULES (NEVER VIOLATE):
9. If the user asks for a numbered list ("what are the X rules/steps/requirements"), you MUST return the COMPLETE list exactly as stated in the manual.
10. NEVER truncate, shorten, or summarize lists. If the manual has 5 items, return all 5 items.
11. NEVER paraphrase list items unless explicitly asked. Use the exact wording from the manual.
12. NEVER add generic advice (like "consult safety checklist") unless the manual explicitly includes it.
13. Preserve the exact numbering, order, and formatting from the source.
14. If the question says "five rules" or "three steps", verify the manual contains exactly that number. If not, state the actual count.

CRITICAL SECTION LOCK RULES (NEVER VIOLATE):
15. If you see "CRITICAL SECTION LOCK" in the context, you MUST use ONLY the specified section.
16. NEVER merge, combine, or supplement information from other sections or your memory.
17. NEVER cite a different section than the one you used for the answer.
18. NEVER substitute list items with similar items from other sections.
19. If the locked section is incomplete, say so explicitly - do NOT fill gaps from elsewhere.
20. The citation MUST match the section you extracted the list from. If you used Section 1.1, cite ONLY Section 1.1.

CITATION RULES:
- Always cite your sources inline using [C1], [C2], etc. - THIS IS MANDATORY, NOT OPTIONAL.
- Every factual claim must have a citation in square brackets.
- The citation MUST come from the exact section that provided the information.
- For list questions with section lock, use ONLY the locked section's citation (usually [C1]).
- Always include the page number when information is found.
- NEVER write "Reference:" or "Based on" or "According to" without the bracketed citation [C1].
- Correct format: "According to Section 1.1 [C1], the five safety rules are:"
- WRONG format: "Reference: Section 1.1" (missing [C1])

ANSWER FORMAT:
- For list questions: Return the complete numbered/bulleted list with citation from the EXACT section used.
- For other questions: Direct answer in 1-2 sentences, then if needed: "Based on page/section..."
- ALWAYS include at least one [Cn] citation in every answer.

EXAMPLES:
User: When preparing to work on a 1PH718 motor, which action best reflects the lockout/tagout safety rule?
Answer: Isolate the motor from power, protect against reconnection, and verify that it is not live before starting maintenance [C1]. This matches the manual's safety rules on page 57.

User: What are the five safety rules listed in the 1PH718 manual?
Answer: According to Section 1.1 "Observing the five safety rules" [C1], the five safety rules are:
1. Isolate.
2. Protect against reconnection.
3. Verify that the equipment is not live.
4. Ground and short circuit.
5. Cover or enclose adjacent components that are still live."""


def _select_best_section_for_list(query: str, chunks: List[RetrievedChunk]) -> RetrievedChunk:
    """
    For list questions, select the single best section that contains the complete list.
    
    Priority:
    1. Section heading matches query terms (e.g., "five safety rules" matches "Observing the five safety rules")
    2. Section contains complete numbered list (3+ items)
    3. Highest relevance score
    
    Returns:
        Single chunk that should be used exclusively for the answer
    """
    import re
    
    query_lower = query.lower()
    
    # Extract key terms from query
    key_terms = []
    
    # Extract number words (five, three, etc.)
    number_match = re.search(r'\b(five|three|four|six|seven|eight|ten|two|one)\b', query_lower)
    if number_match:
        key_terms.append(number_match.group(1))
    
    # Extract list type (rules, steps, etc.)
    type_match = re.search(r'\b(rules?|steps?|requirements?|procedures?|instructions?)\b', query_lower)
    if type_match:
        key_terms.append(type_match.group(1).rstrip('s'))  # Normalize to singular
    
    # Extract model/manual reference
    if '1ph718' in query_lower:
        key_terms.append('1ph718')
    
    logger.info(f"📌 Section selection key terms: {key_terms}")
    
    # Score each chunk
    best_chunk = None
    best_score = -1
    
    for chunk in chunks:
        score = 0
        section_heading_lower = chunk.section_heading.lower()
        
        # Priority 1: Heading match (highest weight)
        heading_matches = 0
        for term in key_terms:
            if term in section_heading_lower:
                heading_matches += 1
        score += heading_matches * 100  # High weight for heading match
        
        # Priority 2: Contains complete list
        list_items = re.findall(r'^\s*\d+[\.)]\s*.+$', chunk.text, re.MULTILINE)
        if len(list_items) >= 3:
            score += 50
            score += min(len(list_items), 10) * 5  # Bonus for more items (up to 10)
        
        # Priority 3: Relevance score
        score += chunk.relevance_score * 10
        
        logger.info(f"   - {chunk.citation_ref} '{chunk.section_heading}': "
                   f"score={score:.1f} (heading_matches={heading_matches}, "
                   f"list_items={len(list_items)}, relevance={chunk.relevance_score:.3f})")
        
        if score > best_score:
            best_score = score
            best_chunk = chunk
    
    if best_chunk:
        logger.info(f"✅ Selected section: {best_chunk.citation_ref} '{best_chunk.section_heading}' "
                   f"(page {best_chunk.page_number}) with score {best_score:.1f}")
    
    return best_chunk


def _build_context_message(query: str, chunks: List[RetrievedChunk]) -> Tuple[str, List[RetrievedChunk]]:
    """
    Format retrieved chunks as context for the LLM.
    
    CRITICAL: For list questions, enforce STRICT SECTION LOCKING:
    - Select the single best matching section
    - Provide ONLY that section to the LLM
    - RELABEL as [C1] for consistency
    - Add hard anti-merging instruction
    
    Returns:
        Tuple of (context_message, chunks_used_in_prompt)
        - chunks_used_in_prompt has stable, sequential citation labels [C1], [C2], etc.
    """
    import re
    
    query_lower = query.lower()
    is_list_question = bool(
        re.search(r'\b(five|three|four|six|seven|eight|ten|two|one)\b.*\b(rules?|steps?|requirements?|procedures?|instructions?)\b', query_lower) or
        re.search(r'\bwhat are (the\s+)?\d*\s*(rules?|steps?|requirements?|procedures?|instructions?)\b', query_lower) or
        re.search(r'\b(list|enumerate)\b', query_lower)
    )
    
    logger.info(f"🔍 List question detection: is_list_question={is_list_question} for query: '{query[:80]}'")
    
    # SECTION LOCK: For list questions, select ONLY the best matching section
    if is_list_question and chunks:
        logger.info("🔒 SECTION LOCK: List question detected - selecting best matching section only")
        logger.error("🔒🔒🔒 SECTION LOCK ACTIVATED - THIS SHOULD APPEAR IN LOGS 🔒🔒🔒")
        
        best_chunk = _select_best_section_for_list(query, chunks)
        
        logger.error(f"🔒 BEST CHUNK SELECTED: {best_chunk.citation_ref if best_chunk else 'NONE'}")
        
        if best_chunk:
            logger.error(f"🔒 ORIGINAL REF: {best_chunk.citation_ref}, Page: {best_chunk.page_number}, Section: '{best_chunk.section_heading}'")
            
            # CRITICAL: Relabel as [C1] for consistency between prompt and citation map
            locked_chunks = [best_chunk.model_copy(update={"citation_ref": "[C1]"})]
            
            logger.error(f"🔒 RELABELED TO: [C1], Page: {locked_chunks[0].page_number}, Section: '{locked_chunks[0].section_heading}'")
            logger.info(f"✅ CITATION STABILIZED: {best_chunk.citation_ref} → [C1] "
                       f"(Page {best_chunk.page_number}, Section '{best_chunk.section_heading}')")
            
            context_parts = []
            for chunk in locked_chunks:
                context_parts.append(
                    f"{chunk.citation_ref} (Page {chunk.page_number}, {chunk.doc_name}, "
                    f"Section: {chunk.section_heading})\n{chunk.text}"
                )
            
            context_block = "\n\n".join(context_parts)
            
            # Add HARD anti-merging instruction
            hard_lock = f"""

⚠️⚠️⚠️ CRITICAL SECTION LOCK ⚠️⚠️⚠️
This is a LIST QUESTION. You have been given EXACTLY ONE section that contains the complete answer.
- Use ONLY {locked_chunks[0].citation_ref} (Section: {locked_chunks[0].section_heading})
- Do NOT reference any other sections or pages
- Do NOT merge, combine, or substitute items from memory or other sources
- Extract the EXACT list from this section word-for-word
- If the list in this section is incomplete, say so - do NOT fill in from other sources"""
            
            return f"Context documents:\n{context_block}{hard_lock}\n\nQuestion: {query}", locked_chunks
    
    # For non-list questions, use all chunks with sequential relabeling
    # CRITICAL: Ensure sequential [C1], [C2], [C3] labels
    relabeled_chunks = []
    for i, chunk in enumerate(chunks):
        relabeled = chunk.model_copy(update={"citation_ref": f"[C{i + 1}]"})
        relabeled_chunks.append(relabeled)
    
    context_parts = []
    for chunk in relabeled_chunks:
        context_parts.append(
            f"{chunk.citation_ref} (Page {chunk.page_number}, {chunk.doc_name}, "
            f"Section: {chunk.section_heading})\n{chunk.text}"
        )

    context_block = "\n\n".join(context_parts)
    return f"Context documents:\n{context_block}\n\nQuestion: {query}", relabeled_chunks


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
    logger.info(f"🔧 GENERATE_ANSWER CALLED - VERSION: {ANSWERER_VERSION}")
    
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

    # DIAGNOSTICS: Log chunk sources BEFORE any processing
    logger.info(f"📋 INPUT CHUNKS TO ANSWERER:")
    for i, chunk in enumerate(chunks[:5]):
        logger.info(f"   - {chunk.citation_ref}: Page {chunk.page_number}, Section '{chunk.section_heading}'")
        logger.info(f"     Text preview: {chunk.text[:100]}...")
    
    if len(chunks) > 1:
        unique_sections = set([c.section_heading for c in chunks])
        if len(unique_sections) > 1:
            logger.warning(f"⚠️ Multiple sections in context: {list(unique_sections)[:3]}. Risk of list merging!")

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
    
    # Build context message and get the chunks actually used in the prompt
    # CRITICAL: This may filter/relabel chunks for section lock
    user_message, chunks_in_prompt = _build_context_message(query, chunks)
    user_message += confidence_context
    
    # Log the EXACT chunk table sent to the model
    logger.info(f"📋 PROMPT CHUNK TABLE:")
    for chunk in chunks_in_prompt:
        logger.info(f"   {chunk.citation_ref} → Page {chunk.page_number}, Section '{chunk.section_heading}'")

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
        
        # DIAGNOSTICS: Detect which citations were actually used
        import re
        used_citations = re.findall(r'\[C\d+\]', answer_text)
        logger.info(f"📋 Citations used in answer: {used_citations}")
        
        # POST-GENERATION VALIDATION for list questions
        query_lower = query.lower()
        is_list_question = bool(
            re.search(r'\b(five|three|four|six|seven|eight|ten)\s+(rules?|steps?|requirements?|procedures?|instructions?)\b', query_lower) or
            re.search(r'\bwhat are the\s+\d*\s*(rules?|steps?|requirements?|procedures?|instructions?)\b', query_lower)
        )
        
        if is_list_question:
            # Check if multiple citations were used (indicates merging)
            unique_citations = set(used_citations)
            if len(unique_citations) > 1:
                logger.error(f"⚠️ VALIDATION FAILED: List question used multiple citations {unique_citations}. This indicates section merging!")
                logger.warning(f"   Answer may be mixing content from different sections.")
            else:
                logger.info(f"✅ VALIDATION PASSED: Single source citation {unique_citations}")
            
            # Check which chunk was cited (using chunks_in_prompt, not original chunks)
            if used_citations:
                cited_ref = used_citations[0]
                cited_chunk = next((c for c in chunks_in_prompt if c.citation_ref == cited_ref), None)
                if cited_chunk:
                    logger.info(f"✅ Answer sourced from: Section '{cited_chunk.section_heading}' (Page {cited_chunk.page_number})")
                else:
                    logger.error(f"❌ CRITICAL: Citation {cited_ref} not found in chunks_in_prompt!")
        
    except Exception as e:
        logger.error(f"Model inference error: {type(e).__name__}: {e}")
        answer_text = f"Error generating response: {str(e)}. The model may still be loading."

    # Map citation refs in the answer back to source metadata
    # CRITICAL: Use chunks_in_prompt (not original chunks) for correct mapping
    logger.info(f"🔧 CITATION MAPPING: Using {len(chunks_in_prompt)} chunks_in_prompt (NOT original {len(chunks)} chunks)")
    logger.info(f"🔧 CITATION MAPPING INPUT:")
    for c in chunks_in_prompt:
        logger.info(f"   {c.citation_ref} → Page {c.page_number}, Section '{c.section_heading}'")
    
    citations = map_citations(answer_text, chunks_in_prompt)
    
    logger.info(f"🔧 CITATION MAPPING OUTPUT:")
    for citation in citations:
        logger.info(f"   {citation.ref} → Page {citation.page_number}, Section '{citation.section_heading}'")
    
    # POST-MAPPING INTEGRITY CHECK
    logger.info(f"📋 CITATION INTEGRITY CHECK:")
    for citation in citations:
        logger.info(f"   {citation.ref} → Page {citation.page_number}, Section '{citation.section_heading}'")
    
    # Check if answer text mentions a section explicitly
    import re
    section_mentions = re.findall(r'[Ss]ection\s+([\d\.]+)\s+["\']?([^"\']+)["\']?', answer_text)
    if section_mentions and citations:
        for section_num, section_name in section_mentions:
            # Verify the citation matches the mentioned section
            citation_sections = [c.section_heading for c in citations]
            match_found = any(section_num in s or section_name.lower() in s.lower() for s in citation_sections)
            
            if match_found:
                logger.info(f"✅ INTEGRITY OK: Answer mentions 'Section {section_num} {section_name}' - citation matches")
            else:
                logger.error(f"❌ INTEGRITY VIOLATION: Answer mentions 'Section {section_num} {section_name}' "
                           f"but citations point to {citation_sections}")

    return AnswerResponse(
        answer=answer_text,
        citations=citations,
        retrieved_chunks=chunks_in_prompt,  # Return the chunks actually used
    ), metadata
