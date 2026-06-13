import logging
import uuid
import os
from pathlib import Path
from collections import defaultdict

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

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
from utils.cloudinary_storage import upload_pdf, delete_pdf, get_pdf_url

logger = logging.getLogger(__name__)

router = APIRouter()

Path(config.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# ── In-memory citation cache: session_id → {ref_id: CitationRef}
_citation_cache: dict[str, dict[str, CitationRef]] = {}

# ── In-memory conversation history: session_id → list of {role, content}
# Keeps last 6 turns (3 user + 3 assistant) per session as a sliding window
_session_history: dict[str, list[dict]] = defaultdict(list)
MAX_HISTORY_TURNS = 6  # total messages (user + assistant) to retain


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

    # Step 1 — Generate doc_id here (not inside ingestor)
    doc_id = str(uuid.uuid4())

    # Step 2 — Save PDF to disk BEFORE ingestion
    upload_dir = Path(config.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = upload_dir / f"{doc_id}.pdf"

    try:
        content = await file.read()
        pdf_path.write_bytes(content)
        logger.info(f"Saved uploaded file to {pdf_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Step 3 — Ingest from saved path, pass same doc_id
    try:
        result = ingest_pdf(
            file_path=str(pdf_path),
            equipment_tag=equipment_tag,
            doc_name=file.filename,
            doc_id=doc_id,
        )
    except Exception as e:
        # If ingestion fails, delete the saved PDF to avoid orphaned files
        pdf_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))

    if not result.success:
        # Also clean up PDF on ingestion failure
        pdf_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=result.error_message)

    # Step 4 — Upload PDF to Cloudinary for persistent storage
    cloudinary_success = False
    try:
        pdf_url = upload_pdf(str(pdf_path), doc_id)
        logger.info(f"✅ PDF stored in Cloudinary: {pdf_url}")
        cloudinary_success = True
    except Exception as e:
        logger.error(f"❌ Cloudinary upload failed: {type(e).__name__}: {str(e)}")
        logger.error(f"Cloudinary config check - Cloud Name: {os.getenv('CLOUDINARY_CLOUD_NAME', 'NOT_SET')}")
        # Don't fail the whole request if Cloudinary fails

    # Add warning to result if Cloudinary failed
    if not cloudinary_success:
        result.message += " (Warning: PDF not stored persistently - will be lost on restart)"

    return result


@router.post("/chat", response_model=AnswerResponse)
async def chat(request: ChatRequest) -> AnswerResponse:
    """
    Accept a natural language query and return a cited answer with confidence scoring.
    Supports multi-turn context-aware conversations via session_id.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        logger.info(f"[CHAT] Processing query: {request.query[:100]}")

        # ── Build conversation history context ───────────────────────────────
        # Prepend last N turns to the query so the LLM understands follow-ups
        history_context = ""
        if request.session_id and _session_history[request.session_id]:
            history_lines = []
            for turn in _session_history[request.session_id]:
                role_label = "Engineer" if turn["role"] == "user" else "Assistant"
                # Truncate long assistant answers to 300 chars to save tokens
                content = turn["content"]
                if turn["role"] == "assistant" and len(content) > 300:
                    content = content[:300] + "..."
                history_lines.append(f"{role_label}: {content}")
            history_context = "=== PREVIOUS CONVERSATION ===\n" + "\n".join(history_lines) + "\n=== END PREVIOUS CONVERSATION ===\n\n"
            logger.info(f"[CHAT] Injecting {len(_session_history[request.session_id])} history turns")

        # Compose the enriched query: history + current question
        enriched_query = history_context + request.query if history_context else request.query

        # ── Retrieval ────────────────────────────────────────────────────────
        try:
            chunks, retrieval_metadata = retrieve(
                query=request.query,  # retrieve on original query, not history-padded
                equipment_tag=request.equipment_tag,
                use_query_rewriting=True,
                use_parent_retrieval=True,
            )
            logger.info(f"[CHAT] Retrieval successful: {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"[CHAT] Retrieval failed: {type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")

        confidence_score = retrieval_metadata.get("confidence_score", 0.0)
        if not isinstance(confidence_score, (int, float)) or confidence_score != confidence_score:
            confidence_score = 0.1
            retrieval_metadata["confidence_score"] = 0.1
            retrieval_metadata["confidence_level"] = "LOW"

        # ── Answer generation (with history injected into prompt) ────────────
        try:
            answer_response, answer_metadata = generate_answer(
                query=enriched_query,
                chunks=chunks,
                confidence_score=confidence_score,
                confidence_level=retrieval_metadata.get("confidence_level"),
                confidence_details=retrieval_metadata.get("confidence_details"),
            )
            logger.info(f"[CHAT] Answer generation successful")
        except Exception as e:
            logger.error(f"[CHAT] Answer generation failed: {type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail=f"Answer generation error: {str(e)}")

        # ── Update session history (sliding window) ──────────────────────────
        if request.session_id:
            history = _session_history[request.session_id]
            history.append({"role": "user",      "content": request.query})
            history.append({"role": "assistant",  "content": answer_response.answer})
            # Keep only last MAX_HISTORY_TURNS messages
            if len(history) > MAX_HISTORY_TURNS:
                _session_history[request.session_id] = history[-MAX_HISTORY_TURNS:]

            # Cache citations
            _citation_cache[request.session_id] = {
                c.ref: c for c in answer_response.citations
            }

        logger.info(f"[CHAT] Request completed successfully")
        return answer_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CHAT] Unexpected error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


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
    Serve PDF from Cloudinary storage (persistent across HF Spaces restarts).
    Falls back to local storage if available.
    """
    # Try local file first (for immediate uploads)
    pdf_path = Path(config.UPLOAD_DIR) / f"{doc_id}.pdf"
    if pdf_path.exists():
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={doc_id}.pdf",
                "Access-Control-Allow-Origin": "*"
            },
        )
    
    # Redirect to Cloudinary URL
    try:
        cloudinary_url = get_pdf_url(doc_id)
        return RedirectResponse(url=cloudinary_url)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"PDF not found. Please re-upload the document."
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
