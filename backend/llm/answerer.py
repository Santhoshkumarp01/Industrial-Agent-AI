import logging
from typing import List, Tuple

from config import config
from models.schemas import RetrievedChunk, AnswerResponse
from citation.citation_mapper import map_citations
from retrieval.confidence_scorer import generate_confidence_message
from llm.local_llm import generate as llm_generate

logger = logging.getLogger(__name__)

# VERSION MARKER - Check this appears in logs to confirm code is loaded
ANSWERER_VERSION = "PHASE3_CITATION_GROUNDING_v6"
logger.info(f"🔧 ANSWERER MODULE LOADED: {ANSWERER_VERSION}")

_SYSTEM_PROMPT = """You are a helpful maintenance QA assistant for industrial motor manuals.

TASK:
Answer the user's question using the provided context documents below.
Each context document is labelled [C1], [C2], etc. with its page and section.

OUTPUT RULES (CRITICAL - NEVER VIOLATE):
- Output ONLY the final answer. NO internal reasoning, thinking process, or analysis steps.
- DO NOT output any text like "Let me analyze", "Looking at", "Decision:", "Wait,", "Constraint Check:", etc.
- DO NOT show your reasoning process, decision-making, or how you arrived at the answer.
- Start directly with the answer text.
- Your entire response should be the answer the user will read - nothing else.

STRICT GROUNDING RULES (HIGHEST PRIORITY — NEVER VIOLATE):
1. ONLY use information from the [Cn] context documents provided. No outside knowledge.
2. NEVER invent, guess, or assume values (temperatures, torques, speeds, weights, part numbers).
3. NEVER write a section number (e.g. "Section 3.3.2") unless that exact section number appears in the [Cn] context provided to you. If the context shows [C1] is "Section 7.1.3", do NOT say "Section 3.3.2".
4. For safety questions, use exact manual wording. Do not paraphrase safety instructions.
5. Never answer with assumptions or general engineering knowledge.

HANDLING VAGUE OR INCOMPLETE QUESTIONS:
6. If the question is clearly OUT OF SCOPE (asking about locations, people, colleges, dates, non-technical topics), immediately respond: "This question is outside the scope of the equipment maintenance manual. Please ask about equipment specifications, maintenance procedures, safety instructions, or troubleshooting."
7. If the question is vague or incomplete but RELATED to equipment/maintenance (e.g., "What does the manual say about"), provide a helpful summary of the key topics found in the retrieved context.
8. Structure the response as: "The manual sections retrieved cover the following topics: [summarize main topics from context]"
9. If the context is completely unrelated to the question, ONLY THEN say: "This information could not be confirmed from the retrieved manual sections."

CRITICAL LIST RULES (NEVER VIOLATE):
9. If the user asks for a numbered list (e.g., "what are the safety rules/steps/requirements"), return the COMPLETE list exactly as stated in the manual.
10. **IGNORE THE SPECIFIC NUMBER** mentioned in the question (five, three, four, etc.). Return ALL items found in the manual section.
11. If user asks "What are the five safety rules?" but manual has 4 rules, return all 4 rules and note: "The manual lists 4 safety rules:"
12. If user asks "What are the three steps?" but manual has 6 steps, return all 6 steps and note: "The manual provides 6 steps:"
13. NEVER truncate, shorten, or summarize lists.
14. NEVER paraphrase list items. Use the exact wording from the context.
15. NEVER add generic advice unless the manual explicitly includes it.
16. Preserve the exact numbering, order, and formatting from the source.

CRITICAL SECTION LOCK RULES (NEVER VIOLATE):
13. If you see "CRITICAL SECTION LOCK" in the context, use ONLY the specified section.
14. NEVER merge information from other sections.
15. NEVER cite a different section than the one you used.
16. If the locked section is incomplete, say so — do NOT fill gaps from memory.

CITATION RULES (MANDATORY):
- Every factual claim MUST have a [Cn] citation. This is NOT optional.
- Use ONLY the [Cn] labels provided in the context (e.g. [C1], [C2]).
- NEVER write (C1) with parentheses — always use square brackets [C1].
- NEVER write a section number in your answer unless it exactly matches the section shown in the [Cn] context.
  CORRECT: "According to [C1], the five safety rules are..."
  WRONG: "According to Section 1.1 [C1], ..." (unless the context for [C1] explicitly says "Section 1.1")
- If you have no [Cn] citation for a claim, do not make the claim.
- ALWAYS include at least one [Cn] citation in every factual answer.

FORMATTING RULES (CRITICAL - NEVER VIOLATE):
- Write in PLAIN TEXT ONLY. NO markdown formatting.
- DO NOT use **bold**, *italic*, or any markdown syntax.
- DO NOT use asterisks (*) for emphasis or lists.
- Use simple bullet points with dash (-) or numbers (1., 2., 3.) only.
- Example CORRECT format:
  "The manual specifies the following safety notices [C1]:
  - DANGER indicates death or severe injury risk
  - WARNING indicates death or serious injury risk if precautions not taken
  - CAUTION indicates minor injury risk"
- Example WRONG format:
  "**Graded Safety Notices:** The manual uses **DANGER** and **WARNING**"

ANSWER FORMAT:
- For list questions: Complete list with single [C1] citation at start, use simple dashes or numbers.
- For factual questions: 1-2 sentences with [Cn] citation in plain text.
- For not-found: "This information could not be confirmed from the retrieved manual sections."
- Do NOT add "Please verify with supervisor" or confidence caveats — that is handled separately.
- Write naturally like a technical manual excerpt, not like formatted markdown.

EXAMPLES OF CORRECT OUTPUT:

User: What are the five safety rules listed in the manual?
CORRECT: According to [C1], the manual lists 5 safety rules:
1. Isolate.
2. Protect against reconnection.
3. Verify that the equipment is not live.
4. Ground and short circuit.
5. Cover or enclose adjacent components that are still live.

User: What are the three safety steps?
CORRECT (if manual has 4 steps): According to [C1], the manual provides 4 safety steps:
1. Switch off the power supply.
2. Secure against reconnection.
3. Verify voltage-free state.
4. Apply grounding equipment.

Note: The user asked for three steps, but the manual contains four. Always return the complete list from the manual.

User: What safety instructions are mentioned in the manual?
CORRECT: According to [C1], the manual describes the following safety-related elements:
- Safety symbols and instructions on the machine and its packaging
- Covers and protective insulation for noise reduction
- Hearing protection measures
- Secured free shaft extensions and rotating parts to prevent contact
- Warning notice system with DANGER, WARNING, CAUTION, and NOTICE levels

The manual also lists items to observe to prevent accidents, including awareness of live parts, rotating parts, hot surfaces, hazardous substances, flammable substances, and noise emissions [C1].

User: What is the maximum operating speed for IM B5 flange-mounted motors?
CORRECT: This information could not be confirmed from the retrieved manual sections."""


def _detect_out_of_scope_query(query: str) -> bool:
    """
    Detect if a query is completely out of scope for industrial equipment manuals.
    
    Out-of-scope patterns:
    - Geographic/location questions (distance, location, address)
    - Personal/people questions (who, names of people)
    - Current events, news, politics
    - Non-technical topics (recipes, entertainment, sports)
    
    IMPORTANT: Machine diagnostic reports and maintenance queries are IN SCOPE!
    
    Returns:
        True if query is out of scope, False if potentially relevant
    """
    import re
    query_lower = query.lower()
    
    # Skip if this is a machine diagnostic report (in-scope)
    if "machine diagnostic report" in query_lower or "equipment" in query_lower:
        return False
    
    # Out-of-scope keywords
    out_of_scope_patterns = [
        # Geographic
        r'\b(distance|location|address|where is|how far|city|town|college|university|school)\b',
        # People
        r'\b(who is|person|people|name of.*person|celebrity)\b',
        # Current events
        r'\b(news|latest|today|yesterday|current|election|politics)\b',
        # Non-technical
        r'\b(recipe|cook|food|movie|film|sport|game|music|song)\b',
        # Non-equipment
        r'\b(weather|climate|animal|plant|tree|flower)\b',
    ]
    
    for pattern in out_of_scope_patterns:
        if re.search(pattern, query_lower):
            logger.warning(f"⚠️ OUT-OF-SCOPE QUERY DETECTED: {query[:80]}")
            return True
    
    return False


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
    
    # Extract list type (rules, steps, levels, features, etc.)
    type_match = re.search(r'\b(rules?|levels?|features?|steps?|requirements?|procedures?|instructions?)\b', query_lower)
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


def _sanitize_text(text: str) -> str:
    """
    Sanitize text to prevent Gemini API crashes from malformed characters.
    
    - Remove control characters and non-printable characters
    - Replace problematic unicode with safe alternatives
    - Truncate extremely long chunks
    """
    if not text:
        return ""
    
    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    # Remove null bytes and replacement characters
    sanitized = sanitized.replace('\x00', '')
    sanitized = sanitized.replace('\ufffd', '')
    
    # Normalize excessive whitespace
    import re
    sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)  # Max 2 consecutive newlines
    sanitized = re.sub(r' {2,}', ' ', sanitized)  # Max 1 space
    
    # Truncate to prevent massive chunks that break API
    MAX_CHUNK_CHARS = 3500
    if len(sanitized) > MAX_CHUNK_CHARS:
        sanitized = sanitized[:MAX_CHUNK_CHARS] + "\n[... content truncated for length ...]"
    
    return sanitized.strip()


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
        # Match list questions regardless of specific count
        re.search(r'\b(five|three|four|six|seven|eight|ten|two|one|all|any)\b.*\b(rules?|levels?|features?|steps?|requirements?|procedures?|instructions?)\b', query_lower) or
        re.search(r'\bwhat are (the\s+)?\d*\s*(rules?|levels?|features?|steps?|requirements?|procedures?|instructions?)\b', query_lower) or
        re.search(r'\b(list|enumerate)\b', query_lower) or
        # NEW: Match questions asking for safety/maintenance items without specific count
        re.search(r'\bwhat.*\b(safety|maintenance|operational)\b.*(rules?|levels?|features?|steps?|procedures?|instructions?|requirements?)\b', query_lower)
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
                sanitized_text = _sanitize_text(chunk.text)
                context_parts.append(
                    f"{chunk.citation_ref} (Page {chunk.page_number}, {chunk.doc_name}, "
                    f"Section: {chunk.section_heading})\n{sanitized_text}"
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
        sanitized_text = _sanitize_text(chunk.text)
        context_parts.append(
            f"{chunk.citation_ref} (Page {chunk.page_number}, {chunk.doc_name}, "
            f"Section: {chunk.section_heading})\n{sanitized_text}"
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
    
    # Check if query is completely out of scope BEFORE processing
    if _detect_out_of_scope_query(query):
        logger.warning(f"🚫 OUT-OF-SCOPE QUERY REJECTED: {query[:80]}")
        metadata["confidence_message"] = "Question is outside the scope of equipment manuals"
        return AnswerResponse(
            answer="This question is outside the scope of the equipment maintenance manual. Please ask about equipment specifications, maintenance procedures, safety instructions, or troubleshooting.",
            citations=[],
            retrieved_chunks=[],
        ), metadata
    
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
    
    # Log prompt size for debugging
    prompt_size = len(_SYSTEM_PROMPT) + len(user_message)
    logger.info(f"📊 Total prompt size: {prompt_size} chars (system: {len(_SYSTEM_PROMPT)}, user: {len(user_message)})")

    logger.info(f"Calling fine-tuned model with {confidence_level} confidence...")

    try:
        # Use fine-tuned model for RAG answer generation
        answer_text = llm_generate(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_message,
            max_tokens=800
        )
        
        # SAFETY CHECK: If model refuses with generic message but we have context, provide summary
        refusal_phrases = [
            "could not be confirmed",
            "not available in the uploaded documents",
            "I could not confirm this"
        ]
        
        if any(phrase in answer_text.lower() for phrase in refusal_phrases):
            # Check if we actually have valid context
            if chunks_in_prompt and len(chunks_in_prompt) > 0:
                total_context_chars = sum(len(c.text) for c in chunks_in_prompt)
                if total_context_chars > 200:  # We have substantial context
                    logger.warning(f"Model refused to answer despite having {total_context_chars} chars of context. Generating summary...")
                    
                    # Generate a helpful summary instead
                    summary_parts = []
                    for chunk in chunks_in_prompt[:3]:  # Top 3 chunks
                        summary_parts.append(f"- {chunk.section_heading} (Page {chunk.page_number}) {chunk.citation_ref}")
                    
                    answer_text = (
                        f"The retrieved manual sections cover the following topics:\n" +
                        "\n".join(summary_parts) +
                        f"\n\nPlease ask a more specific question about any of these topics for detailed information."
                    )
                    logger.info("Generated fallback summary response")
        
        # Prepend confidence message to answer (only for LOW/MEDIUM)
        if metadata["confidence_message"] and confidence_level != "HIGH":
            answer_text = f"{metadata['confidence_message']}\n\n{answer_text}"
        
        logger.info(f"Model response received ({len(answer_text)} chars).")
        
        # DIAGNOSTICS: Detect which citations were actually used
        import re
        used_citations = re.findall(r'\[C\d+\]', answer_text)
        logger.info(f"📋 Citations used in answer: {used_citations}")

        # Phase 3 Fix: Section-number hallucination guard
        # If model wrote "Section X.Y" but [Cn] context doesn't have that section,
        # strip the section number to prevent misleading references.
        section_refs_in_answer = re.findall(r'[Ss]ection\s+([\d\.]+)', answer_text)
        available_sections = " ".join(c.section_heading for c in chunks_in_prompt)
        for sec_num in section_refs_in_answer:
            if sec_num not in available_sections:
                logger.warning(f"🔧 HALLUCINATED SECTION: '{sec_num}' not in context — stripping from answer")
                # Replace "Section X.Y" or "Section X.Y.Z" with just the citation marker
                answer_text = re.sub(
                    rf'[Ss]ection\s+{re.escape(sec_num)}\s*',
                    '',
                    answer_text
                )
        
        # POST-GENERATION VALIDATION for list questions
        query_lower = query.lower()
        is_list_question = bool(
            re.search(r'\b(five|three|four|six|seven|eight|ten)\s+(rules?|levels?|features?|steps?|requirements?|procedures?|instructions?)\b', query_lower) or
            re.search(r'\bwhat are the\s+\d*\s*(rules?|levels?|features?|steps?|requirements?|procedures?|instructions?)\b', query_lower)
        )
        
        if is_list_question:
            unique_citations = set(used_citations)
            if len(unique_citations) > 1:
                logger.error(f"⚠️ VALIDATION FAILED: List question used multiple citations {unique_citations}.")
            else:
                logger.info(f"✅ VALIDATION PASSED: Single source citation {unique_citations}")
            
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
