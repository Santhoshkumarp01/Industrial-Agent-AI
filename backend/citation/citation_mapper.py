import re
import logging
from typing import List

from models.schemas import RetrievedChunk, CitationRef

logger = logging.getLogger(__name__)

_CITATION_PATTERN = re.compile(r"\[C(\d+)\]")


def map_citations(answer: str, chunks: List[RetrievedChunk]) -> List[CitationRef]:
    """
    Map [C1], [C2], ... references in the answer back to PDF page and bbox.

    Args:
        answer: LLM-generated answer text containing [Cn] inline references.
        chunks: List of retrieved chunks with citation_ref already assigned.

    Returns:
        List of CitationRef objects for only the citations actually used in the answer.
    """
    # Build lookup: "[C1]" → RetrievedChunk
    ref_map = {chunk.citation_ref: chunk for chunk in chunks}

    # Find all unique [Cn] references used in the answer (in order of appearance)
    found_refs = []
    seen = set()
    for match in _CITATION_PATTERN.finditer(answer):
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
            doc_id=chunk.doc_id,         # ← Populate from chunk
            doc_name=chunk.doc_name,
            page_number=chunk.page_number,
            bbox=chunk.bbox,
            section_heading=chunk.section_heading,
            snippet=chunk.text[:120],
        ))

    logger.debug(f"Resolved {len(citations)} citations from answer.")
    return citations
