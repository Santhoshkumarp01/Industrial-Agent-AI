import re
import logging
from typing import List

from models.schemas import RetrievedChunk, CitationRef

logger = logging.getLogger(__name__)

# Phase 3 Fix: accept both [C1] and (C1) bracket styles
_CITATION_PATTERN = re.compile(r"[\[\(]C(\d+)[\]\)]")


def map_citations(answer: str, chunks: List[RetrievedChunk]) -> List[CitationRef]:
    """
    Map [C1], [C2], ... (or (C1), (C2)...) references in the answer back to PDF page and bbox.

    Phase 3 Fix:
    - Regex now accepts both square brackets [C1] and parentheses (C1)
    - Warns when citation ref in answer has no matching chunk

    Args:
        answer: LLM-generated answer text containing [Cn] inline references.
        chunks: List of retrieved chunks with citation_ref already assigned.

    Returns:
        List of CitationRef objects for only the citations actually used in the answer.
    """
    # Build lookup: "[C1]" → RetrievedChunk (normalise to square brackets)
    ref_map = {}
    for chunk in chunks:
        # Normalise stored ref to [Cn] form
        norm = re.sub(r"[\(\)]", lambda m: "[" if m.group() == "(" else "]", chunk.citation_ref)
        ref_map[norm] = chunk

    # Find all unique [Cn]/(Cn) references in answer (in order of appearance)
    found_refs = []
    seen = set()
    for match in _CITATION_PATTERN.finditer(answer):
        # Always store as [Cn] normalised form
        ref = f"[C{match.group(1)}]"
        if ref not in seen:
            seen.add(ref)
            found_refs.append(ref)

    citations: List[CitationRef] = []
    for ref in found_refs:
        chunk = ref_map.get(ref)
        if chunk is None:
            logger.warning(f"Citation {ref} found in answer but not in retrieved chunks.")
            continue

        citations.append(CitationRef(
            ref=ref,
            doc_id=chunk.doc_id,
            doc_name=chunk.doc_name,
            page_number=chunk.page_number,
            bbox=chunk.bbox,
            section_heading=chunk.section_heading,
            snippet=chunk.text[:120],
        ))

    logger.debug(f"Resolved {len(citations)} citations from answer.")
    return citations
