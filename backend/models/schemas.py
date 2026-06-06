from typing import Optional
from pydantic import BaseModel


class ExtractedBlock(BaseModel):
    doc_id: str
    doc_name: str
    equipment_tag: str
    block_type: str  # paragraph | heading | list | table | figure_caption
    text: str
    page_number: int
    bbox: tuple  # (x0, y0, x1, y1)
    font_size: float
    is_bold: bool
    section_heading: str


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    doc_name: str
    equipment_tag: str
    block_type: str
    text: str
    page_number: int
    bbox: tuple  # (x0, y0, x1, y1)
    section_heading: str
    chunk_index: int
    token_count: int


class RetrievedChunk(BaseModel):
    chunk_id: str
    doc_name: str
    equipment_tag: str
    text: str
    page_number: int
    bbox: tuple
    section_heading: str
    relevance_score: float
    citation_ref: str  # [C1], [C2], etc.


class CitationRef(BaseModel):
    ref: str  # "[C1]"
    doc_name: str
    page_number: int
    bbox: tuple  # (x0, y0, x1, y1)
    section_heading: str
    snippet: str  # First 120 chars of chunk text


class AnswerResponse(BaseModel):
    answer: str
    citations: list[CitationRef]
    retrieved_chunks: list[RetrievedChunk]


class ChatRequest(BaseModel):
    query: str
    equipment_tag: Optional[str] = None
    session_id: Optional[str] = None


class IngestResult(BaseModel):
    doc_id: str
    doc_name: str
    chunk_count: int
    page_count: int
    success: bool = True
    error_message: Optional[str] = None


class DocumentInfo(BaseModel):
    doc_id: str
    doc_name: str
    equipment_tag: str
    chunk_count: int
