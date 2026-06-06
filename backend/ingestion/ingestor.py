import logging
import uuid
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF — used only for page count

from ingestion.extractor import extract_blocks
from ingestion.chunker import chunk_blocks
from embeddings.embedder import encode_texts
from vectorstore.qdrant_store import upsert_chunks, delete_document
from models.schemas import IngestResult

logger = logging.getLogger(__name__)


def ingest_pdf(
    file_path: str,
    equipment_tag: str,
    doc_name: str,
    doc_id: Optional[str] = None,
) -> IngestResult:
    """
    Full ingestion pipeline: extract → chunk → embed → store.

    Args:
        file_path: Absolute path to the saved PDF.
        equipment_tag: Equipment identifier string.
        doc_name: Original PDF filename.
        doc_id: Optional pre-generated UUID. One is created if not provided.

    Returns:
        IngestResult with success/failure status and counts.
    """
    if doc_id is None:
        doc_id = str(uuid.uuid4())

    page_count = 0

    try:
        # Step 1: Get page count
        pdf = fitz.open(file_path)
        page_count = len(pdf)
        pdf.close()
        logger.info(f"[{doc_name}] PDF opened — {page_count} pages.")

        # Step 2: Extract blocks
        logger.info(f"[{doc_name}] Extracting blocks...")
        blocks = extract_blocks(file_path, doc_id, doc_name, equipment_tag)
        logger.info(f"[{doc_name}] Extracted {len(blocks)} blocks.")

        # Step 3: Chunk
        logger.info(f"[{doc_name}] Chunking blocks...")
        chunks = chunk_blocks(blocks)
        logger.info(f"[{doc_name}] Produced {len(chunks)} chunks.")

        if not chunks:
            logger.warning(f"[{doc_name}] No chunks produced — document may be empty or image-only.")
            return IngestResult(
                doc_id=doc_id,
                doc_name=doc_name,
                chunk_count=0,
                page_count=page_count,
                success=False,
                error_message="No chunks produced from document.",
            )

        # Step 4: Embed (dense vectors)
        logger.info(f"[{doc_name}] Encoding {len(chunks)} chunks...")
        texts = [c.text for c in chunks]
        embeddings = encode_texts(texts)
        logger.info(f"[{doc_name}] Dense embeddings generated.")

        # Step 5: Store (Qdrant generates sparse BM25 vectors internally)
        logger.info(f"[{doc_name}] Upserting to Qdrant...")
        upsert_chunks(chunks, embeddings)
        logger.info(f"[{doc_name}] Ingestion complete — {len(chunks)} chunks stored.")

        return IngestResult(
            doc_id=doc_id,
            doc_name=doc_name,
            chunk_count=len(chunks),
            page_count=page_count,
            success=True,
        )

    except Exception as e:
        logger.error(f"[{doc_name}] Ingestion failed: {e}")
        # Best-effort cleanup: remove any partially stored chunks
        try:
            delete_document(doc_id)
            logger.info(f"[{doc_name}] Partial data cleaned up from Qdrant.")
        except Exception as cleanup_err:
            logger.warning(f"[{doc_name}] Cleanup failed: {cleanup_err}")

        return IngestResult(
            doc_id=doc_id,
            doc_name=doc_name,
            chunk_count=0,
            page_count=page_count,
            success=False,
            error_message=str(e),
        )
