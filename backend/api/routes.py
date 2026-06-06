import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from config import config
from ingestion.ingestor import ingest_pdf
from retrieval.retriever import retrieve
from llm.answerer import generate_answer
from vectorstore.qdrant_store import delete_document, list_documents
from models.schemas import (
    IngestResult,
    ChatRequest,
    AnswerResponse,
    DocumentInfo,
    CitationRef,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Ensure upload directory exists
Path(config.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# In-memory citation cache: session_id → {ref_id: CitationRef}
# (Optional enhancement for GET /citation endpoint)
_citation_cache: dict[str, dict[str, CitationRef]] = {}


@router.post("/upload", response_model=IngestResult)
async def upload_document(
    file: UploadFile = File(...),
    equipment_tag: str = Form(...),
) -> IngestResult:
    """
    Accept a PDF upload, save it to disk, and run the ingestion pipeline.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    doc_id = str(uuid.uuid4())
    save_path = Path(config.UPLOAD_DIR) / f"{doc_id}.pdf"

    try:
        content = await file.read()
        save_path.write_bytes(content)
        logger.info(f"Saved uploaded file to {save_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    result = ingest_pdf(
        file_path=str(save_path),
        equipment_tag=equipment_tag,
        doc_name=file.filename,
        doc_id=doc_id,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error_message)

    return result


@router.post("/chat", response_model=AnswerResponse)
async def chat(request: ChatRequest) -> AnswerResponse:
    """
    Accept a natural language query and return a cited answer.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    chunks = retrieve(
        query=request.query,
        equipment_tag=request.equipment_tag,
    )
    answer_response = generate_answer(query=request.query, chunks=chunks)

    # Cache citations if session_id provided
    if request.session_id:
        _citation_cache[request.session_id] = {
            c.ref: c for c in answer_response.citations
        }

    return answer_response


@router.get("/documents", response_model=list[DocumentInfo])
async def get_documents() -> list[DocumentInfo]:
    """
    Return all ingested documents with metadata and chunk counts.
    """
    docs = list_documents()
    return [DocumentInfo(**d) for d in docs]


@router.delete("/documents/{doc_id}")
async def remove_document(doc_id: str) -> dict:
    """
    Delete all chunks for a given document from Qdrant.
    """
    try:
        delete_document(doc_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {e}")
    return {"success": True, "message": f"Document {doc_id} deleted."}


@router.get("/pdf/{doc_id}")
async def serve_pdf(doc_id: str):
    """
    Serve the raw PDF file so the frontend PDF viewer can render it.
    """
    pdf_path = Path(config.UPLOAD_DIR) / f"{doc_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF '{doc_id}' not found.")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={doc_id}.pdf"},
    )


@router.get("/citation/{session_id}/{ref_id}", response_model=CitationRef)
async def get_citation(session_id: str, ref_id: str) -> CitationRef:
    """
    Return the CitationRef for a given session and reference ID.
    Used by the frontend to draw highlight boxes on the PDF viewer.

    ref_id should be URL-encoded, e.g. 'C1' maps to '[C1]'.
    """
    ref_key = f"[{ref_id}]"
    session_citations = _citation_cache.get(session_id)
    if session_citations is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    citation = session_citations.get(ref_key)
    if citation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Citation '{ref_key}' not found in session '{session_id}'.",
        )
    return citation
