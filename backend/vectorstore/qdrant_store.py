"""
Qdrant vector store — hybrid dense + sparse search.

Local:  http://localhost:6333 (Docker or in-memory fallback)
Cloud:  set QDRANT_URL and QDRANT_API_KEY env vars — no code changes needed.
"""

import re
import json
import uuid
import logging
from typing import List, Optional

from qdrant_client import QdrantClient, models
from qdrant_client.models import (
    VectorParams,
    Distance,
    SparseVectorParams,
    SparseIndexParams,
    PointStruct,
    NamedVector,
    NamedSparseVector,
    SparseVector,
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector,
    OptimizersConfigDiff,
)
from fastembed import SparseTextEmbedding

import config
from models.schemas import Chunk, RetrievedChunk

logger = logging.getLogger(__name__)

_client: Optional[QdrantClient] = None
_sparse_model: Optional[SparseTextEmbedding] = None


# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------

def get_client() -> QdrantClient:
    """Return singleton Qdrant client. Falls back to in-memory if Docker unreachable."""
    global _client
    if _client is None:
        if config.QDRANT_API_KEY:
            # Cloud mode
            logger.info(f"Connecting to Qdrant Cloud: {config.QDRANT_URL}")
            _client = QdrantClient(
                url=config.QDRANT_URL,
                api_key=config.QDRANT_API_KEY,
            )
        else:
            # Local mode — try Docker first, fall back to in-memory
            try:
                _client = QdrantClient(url=config.QDRANT_URL)
                _client.get_collections()   # test connection
                logger.info(f"Connected to local Qdrant at {config.QDRANT_URL}")
            except Exception:
                print("⚠  Qdrant not reachable at localhost:6333, using in-memory mode")
                logger.warning("Falling back to in-memory Qdrant (data will not persist).")
                _client = QdrantClient(":memory:")
    return _client


def get_sparse_model() -> SparseTextEmbedding:
    """Return singleton BM25 sparse embedding model."""
    global _sparse_model
    if _sparse_model is None:
        logger.info(f"Loading sparse model: {config.SPARSE_MODEL}")
        _sparse_model = SparseTextEmbedding(model_name=config.SPARSE_MODEL)
        logger.info("Sparse model loaded.")
    return _sparse_model


# ---------------------------------------------------------------------------
# Collection management
# ---------------------------------------------------------------------------

def ensure_collection() -> None:
    """Create the Qdrant collection with dense + sparse vectors if it doesn't exist."""
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]

    if config.QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=config.QDRANT_COLLECTION,
            vectors_config={
                "dense": VectorParams(
                    size=config.DENSE_DIM,
                    distance=Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            },
        )
        print(f"✓ Created Qdrant collection: {config.QDRANT_COLLECTION}")
        logger.info(f"Created Qdrant collection: {config.QDRANT_COLLECTION}")
    else:
        print(f"✓ Qdrant collection exists: {config.QDRANT_COLLECTION}")
        logger.info(f"Qdrant collection already exists: {config.QDRANT_COLLECTION}")


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

def upsert_chunks(chunks: List[Chunk], dense_embeddings: List[List[float]]) -> None:
    """
    Upsert chunks with both dense and sparse vectors into Qdrant.

    Args:
        chunks: List of Chunk objects.
        dense_embeddings: Corresponding dense embedding vectors.
    """
    client = get_client()
    sparse_model = get_sparse_model()

    # Generate sparse vectors for all chunk texts in one batch
    sparse_results = list(sparse_model.embed([c.text for c in chunks]))

    points: List[PointStruct] = []
    for chunk, dense_vec, sparse_result in zip(chunks, dense_embeddings, sparse_results):
        sparse_vec = SparseVector(
            indices=sparse_result.indices.tolist(),
            values=sparse_result.values.tolist(),
        )

        payload = {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "doc_name": chunk.doc_name,
            "equipment_tag": chunk.equipment_tag,
            "block_type": chunk.block_type,
            "text": chunk.text,
            "page_number": chunk.page_number,
            "bbox": json.dumps(list(chunk.bbox)) if chunk.bbox else "[]",
            "section_heading": chunk.section_heading,
            "chunk_index": chunk.chunk_index,
            "token_count": chunk.token_count,
        }

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "dense": dense_vec,
                    "sparse": sparse_vec,
                },
                payload=payload,
            )
        )

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(
            collection_name=config.QDRANT_COLLECTION,
            points=batch,
        )

    print(f"✓ Upserted {len(points)} chunks into Qdrant")
    logger.info(f"Upserted {len(points)} chunks into Qdrant.")


# ---------------------------------------------------------------------------
# Hybrid search
# ---------------------------------------------------------------------------

def query(
    query_dense: List[float],
    query_text: str,
    top_k: int = config.TOP_K_RETRIEVAL,
    equipment_tag: Optional[str] = None,
) -> List[RetrievedChunk]:
    """
    Hybrid search: dense (semantic) + sparse (BM25 keyword) with RRF fusion.

    Args:
        query_dense: Pre-encoded dense query vector.
        query_text: Raw query string (used to encode sparse BM25 vector).
        top_k: Number of candidates to return.
        equipment_tag: Optional filter to scope results.

    Returns:
        List of RetrievedChunk objects fused and ranked by RRF score.
    """
    client = get_client()
    sparse_model = get_sparse_model()

    # Encode query as sparse BM25 vector
    sparse_result = list(sparse_model.embed([query_text]))[0]
    query_sparse = SparseVector(
        indices=sparse_result.indices.tolist(),
        values=sparse_result.values.tolist(),
    )

    # Build optional equipment_tag filter
    qdrant_filter = None
    if equipment_tag:
        qdrant_filter = Filter(
            must=[
                FieldCondition(
                    key="equipment_tag",
                    match=MatchValue(value=equipment_tag),
                )
            ]
        )

    # Dynamic weight: boost sparse for exact-term queries (part numbers, fault codes)
    has_exact_terms = bool(
        re.search(r"\b([A-Z]{2,}-\d{3,}|[A-Z]+\d+[A-Z]*|\d{4,})\b", query_text)
    )
    dense_w = 0.5 if has_exact_terms else config.DENSE_WEIGHT
    sparse_w = 0.5 if has_exact_terms else config.SPARSE_WEIGHT

    logger.debug(
        f"Hybrid search — dense_w={dense_w}, sparse_w={sparse_w}, "
        f"exact_terms={has_exact_terms}"
    )

    # Run dense and sparse searches in a single batch call
    results = client.search_batch(
        collection_name=config.QDRANT_COLLECTION,
        requests=[
            models.SearchRequest(
                vector=models.NamedVector(name="dense", vector=query_dense),
                filter=qdrant_filter,
                limit=top_k,
                with_payload=True,
            ),
            models.SearchRequest(
                vector=models.NamedSparseVector(
                    name="sparse",
                    vector=query_sparse,
                ),
                filter=qdrant_filter,
                limit=top_k,
                with_payload=True,
            ),
        ],
    )

    dense_hits, sparse_hits = results[0], results[1]

    return _reciprocal_rank_fusion(
        dense_hits=dense_hits,
        sparse_hits=sparse_hits,
        dense_weight=dense_w,
        sparse_weight=sparse_w,
        top_k=top_k,
    )


def _reciprocal_rank_fusion(
    dense_hits: list,
    sparse_hits: list,
    dense_weight: float,
    sparse_weight: float,
    top_k: int,
    k: int = 60,
) -> List[RetrievedChunk]:
    """
    Reciprocal Rank Fusion:
        score(d) = dense_weight  * 1 / (k + rank_dense)
                 + sparse_weight * 1 / (k + rank_sparse)
    """
    scores: dict = {}
    payloads: dict = {}

    for rank, hit in enumerate(dense_hits):
        cid = hit.payload["chunk_id"]
        scores[cid] = scores.get(cid, 0.0) + dense_weight * (1.0 / (k + rank + 1))
        payloads[cid] = hit.payload

    for rank, hit in enumerate(sparse_hits):
        cid = hit.payload["chunk_id"]
        scores[cid] = scores.get(cid, 0.0) + sparse_weight * (1.0 / (k + rank + 1))
        payloads[cid] = hit.payload

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    retrieved: List[RetrievedChunk] = []
    for cid in sorted_ids[:top_k]:
        p = payloads[cid]
        bbox_raw = json.loads(p.get("bbox", "[]"))
        bbox = tuple(float(v) for v in bbox_raw) if bbox_raw else (0.0, 0.0, 0.0, 0.0)

        retrieved.append(
            RetrievedChunk(
                chunk_id=cid,
                doc_name=p["doc_name"],
                equipment_tag=p.get("equipment_tag", ""),
                text=p["text"],
                page_number=int(p["page_number"]),
                bbox=bbox,
                section_heading=p.get("section_heading", ""),
                relevance_score=scores[cid],
                citation_ref="",   # assigned by retriever.py
            )
        )

    return retrieved


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def delete_document(doc_id: str) -> None:
    """Delete all chunks belonging to a document."""
    client = get_client()
    client.delete(
        collection_name=config.QDRANT_COLLECTION,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
                ]
            )
        ),
    )
    logger.info(f"Deleted all chunks for doc_id: {doc_id}")
    print(f"✓ Deleted all chunks for doc_id: {doc_id}")


# ---------------------------------------------------------------------------
# List documents
# ---------------------------------------------------------------------------

def list_documents() -> List[dict]:
    """Return unique documents stored in the collection with chunk counts."""
    client = get_client()

    # Scroll all points — only fetch lightweight payload fields
    results, _ = client.scroll(
        collection_name=config.QDRANT_COLLECTION,
        limit=1000,
        with_payload=["doc_id", "doc_name", "equipment_tag"],
        with_vectors=False,
    )

    seen: dict = {}
    for point in results:
        doc_id = point.payload["doc_id"]
        if doc_id not in seen:
            seen[doc_id] = {
                "doc_id": doc_id,
                "doc_name": point.payload["doc_name"],
                "equipment_tag": point.payload.get("equipment_tag", ""),
            }

    # Count chunks per document
    for doc_id in seen:
        count_result = client.count(
            collection_name=config.QDRANT_COLLECTION,
            count_filter=Filter(
                must=[
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
                ]
            ),
        )
        seen[doc_id]["chunk_count"] = count_result.count

    return list(seen.values())
