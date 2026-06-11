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
from config import config
from models.schemas import Chunk, RetrievedChunk, ParentSection

logger = logging.getLogger(__name__)

try:
    from fastembed import SparseTextEmbedding
    SPARSE_AVAILABLE = True
except Exception as e:
    logger.warning(f"Sparse embeddings (BM25) unavailable: {e}. Using dense-only search.")
    SPARSE_AVAILABLE = False
    SparseTextEmbedding = None

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
            # Cloud mode with increased timeout
            logger.info(f"Connecting to Qdrant Cloud: {config.QDRANT_URL}")
            _client = QdrantClient(
                url=config.QDRANT_URL,
                api_key=config.QDRANT_API_KEY,
                timeout=60,  # Increased timeout for large uploads
            )
        else:
            # Local mode — try Docker first, fall back to in-memory
            try:
                _client = QdrantClient(url=config.QDRANT_URL, timeout=60)
                _client.get_collections()   # test connection
                logger.info(f"Connected to local Qdrant at {config.QDRANT_URL}")
            except Exception:
                print("⚠  Qdrant not reachable at localhost:6333, using in-memory mode")
                logger.warning("Falling back to in-memory Qdrant (data will not persist).")
                _client = QdrantClient(":memory:")
    return _client


def get_sparse_model():
    """Return singleton BM25 sparse embedding model."""
    global _sparse_model
    if not SPARSE_AVAILABLE:
        return None
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

    # Child chunks collection (embedded, searchable)
    if config.QDRANT_COLLECTION not in existing:
        vectors_config = {
            "dense": VectorParams(
                size=config.DENSE_DIM,
                distance=Distance.COSINE,
            )
        }
        
        sparse_config = None
        if SPARSE_AVAILABLE:
            sparse_config = {
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            }
        
        client.create_collection(
            collection_name=config.QDRANT_COLLECTION,
            vectors_config=vectors_config,
            sparse_vectors_config=sparse_config,
        )
        
        # Create payload indexes for filtering
        client.create_payload_index(
            collection_name=config.QDRANT_COLLECTION,
            field_name="doc_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        
        client.create_payload_index(
            collection_name=config.QDRANT_COLLECTION,
            field_name="equipment_tag",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        
        client.create_payload_index(
            collection_name=config.QDRANT_COLLECTION,
            field_name="parent_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        
        print(f"✓ Created Qdrant collection: {config.QDRANT_COLLECTION}")
        logger.info(f"Created Qdrant collection: {config.QDRANT_COLLECTION}")
    else:
        print(f"✓ Qdrant collection exists: {config.QDRANT_COLLECTION}")
        logger.info(f"Qdrant collection already exists: {config.QDRANT_COLLECTION}")
    
    # Parent sections collection (not embedded, just stored for retrieval)
    parent_collection = f"{config.QDRANT_COLLECTION}_parents"
    if parent_collection not in existing:
        # Parents don't need vectors, just payload storage
        client.create_collection(
            collection_name=parent_collection,
            vectors_config={
                "dummy": VectorParams(size=1, distance=Distance.COSINE)
            }
        )
        
        client.create_payload_index(
            collection_name=parent_collection,
            field_name="parent_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        
        print(f"✓ Created parent sections collection: {parent_collection}")
        logger.info(f"Created parent sections collection: {parent_collection}")
    else:
        # Collection exists - ensure parent_id index exists
        try:
            # Try to create index if it doesn't exist (idempotent operation)
            client.create_payload_index(
                collection_name=parent_collection,
                field_name="parent_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            logger.info(f"✓ Ensured parent_id index exists on {parent_collection}")
        except Exception as e:
            # Index might already exist - that's fine
            logger.info(f"Parent collection index check: {e}")


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

def upsert_chunks_with_parents(
    chunks: List[Chunk], 
    dense_embeddings: List[List[float]],
    parents: List[ParentSection]
) -> None:
    """
    Upsert child chunks (with embeddings) and parent sections (full context).
    
    Child chunks are searchable via embeddings.
    Parent sections are retrieved when child matches.
    """
    client = get_client()
    sparse_model = get_sparse_model()

    # 1. Upsert child chunks with embeddings
    sparse_results = None
    if sparse_model and SPARSE_AVAILABLE:
        sparse_results = list(sparse_model.embed([c.text for c in chunks]))

    child_points: List[PointStruct] = []
    for i, (chunk, dense_vec) in enumerate(zip(chunks, dense_embeddings)):
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
            "parent_id": chunk.parent_id or "",  # Link to parent
        }

        vector_dict = {"dense": dense_vec}
        if sparse_results:
            sparse_vec = SparseVector(
                indices=sparse_results[i].indices.tolist(),
                values=sparse_results[i].values.tolist(),
            )
            vector_dict["sparse"] = sparse_vec

        child_points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector_dict,
                payload=payload,
            )
        )

    # Upsert children in batches
    batch_size = 50
    for i in range(0, len(child_points), batch_size):
        batch = child_points[i : i + batch_size]
        client.upsert(
            collection_name=config.QDRANT_COLLECTION,
            points=batch,
            wait=True,
        )
        logger.info(f"Upserted child batch {i//batch_size + 1}/{(len(child_points)-1)//batch_size + 1}")

    # 2. Upsert parent sections (no embeddings, just payload storage)
    parent_collection = f"{config.QDRANT_COLLECTION}_parents"
    parent_points: List[PointStruct] = []
    
    for parent in parents:
        payload = {
            "parent_id": parent.parent_id,
            "doc_id": parent.doc_id,
            "doc_name": parent.doc_name,
            "equipment_tag": parent.equipment_tag,
            "section_heading": parent.section_heading,
            "full_text": parent.full_text,  # Complete section text
            "page_number": parent.page_number,
            "bbox": json.dumps(list(parent.bbox)),
            "block_types": json.dumps(parent.block_types),
            "token_count": parent.token_count,
            "child_chunk_ids": json.dumps(parent.child_chunk_ids),
        }
        
        parent_points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector={"dummy": [0.0]},  # Dummy vector (not used for search)
                payload=payload,
            )
        )
    
    # Upsert parents
    for i in range(0, len(parent_points), batch_size):
        batch = parent_points[i : i + batch_size]
        client.upsert(
            collection_name=parent_collection,
            points=batch,
            wait=True,
        )
    
    print(f"✓ Upserted {len(child_points)} child chunks + {len(parent_points)} parent sections")
    logger.info(f"Upserted {len(child_points)} children + {len(parent_points)} parents")


# Keep old function for compatibility
def upsert_chunks(chunks: List[Chunk], dense_embeddings: List[List[float]]) -> None:
    """
    Upsert chunks with both dense and sparse vectors into Qdrant.

    Args:
        chunks: List of Chunk objects.
        dense_embeddings: Corresponding dense embedding vectors.
    """
    client = get_client()
    sparse_model = get_sparse_model()

    # Generate sparse vectors if available
    sparse_results = None
    if sparse_model and SPARSE_AVAILABLE:
        sparse_results = list(sparse_model.embed([c.text for c in chunks]))

    points: List[PointStruct] = []
    for i, (chunk, dense_vec) in enumerate(zip(chunks, dense_embeddings)):
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

        # Build vector dict
        vector_dict = {"dense": dense_vec}
        if sparse_results:
            sparse_vec = SparseVector(
                indices=sparse_results[i].indices.tolist(),
                values=sparse_results[i].values.tolist(),
            )
            vector_dict["sparse"] = sparse_vec

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector_dict,
                payload=payload,
            )
        )

    # Upsert in smaller batches for better reliability
    batch_size = 50
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(
            collection_name=config.QDRANT_COLLECTION,
            points=batch,
            wait=True,  # Wait for confirmation
        )
        logger.info(f"Upserted batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")

    print(f"✓ Upserted {len(points)} chunks into Qdrant")
    logger.info(f"Upserted {len(points)} chunks into Qdrant.")


def get_parent_sections(parent_ids: List[str]) -> dict[str, dict]:
    """
    Retrieve parent sections by their IDs.
    
    Args:
        parent_ids: List of parent_id strings
    
    Returns:
        Dict mapping parent_id -> parent section data
    """
    if not parent_ids:
        return {}
    
    client = get_client()
    parent_collection = f"{config.QDRANT_COLLECTION}_parents"
    
    parents_map = {}
    parent_ids_set = set(parent_ids)
    
    try:
        # Method 1: Try with filter (requires index)
        try:
            results, _ = client.scroll(
                collection_name=parent_collection,
                scroll_filter=Filter(
                    should=[
                        FieldCondition(
                            key="parent_id",
                            match=MatchValue(value=pid)
                        )
                        for pid in parent_ids
                    ]
                ),
                limit=len(parent_ids) * 2,  # Margin for safety
                with_payload=True,
                with_vectors=False,
            )
            
            for point in results:
                p = point.payload
                if p.get("parent_id") in parent_ids_set:
                    parents_map[p["parent_id"]] = {
                        "parent_id": p["parent_id"],
                        "doc_id": p["doc_id"],
                        "doc_name": p["doc_name"],
                        "equipment_tag": p.get("equipment_tag", ""),
                        "section_heading": p.get("section_heading", ""),
                        "full_text": p["full_text"],
                        "page_number": int(p["page_number"]),
                        "bbox": json.loads(p.get("bbox", "[]")),
                        "token_count": int(p.get("token_count", 0)),
                    }
            
            logger.info(f"✓ Retrieved {len(parents_map)}/{len(parent_ids)} parent sections via filter")
            return parents_map
            
        except Exception as filter_error:
            logger.warning(f"Filter-based parent fetch failed: {filter_error}. Trying fallback method...")
            
            # Method 2: Scroll all and filter in code (no index required)
            results, _ = client.scroll(
                collection_name=parent_collection,
                limit=1000,  # Get all parents (typically <100)
                with_payload=True,
                with_vectors=False,
            )
            
            for point in results:
                p = point.payload
                if p.get("parent_id") in parent_ids_set:
                    parents_map[p["parent_id"]] = {
                        "parent_id": p["parent_id"],
                        "doc_id": p["doc_id"],
                        "doc_name": p["doc_name"],
                        "equipment_tag": p.get("equipment_tag", ""),
                        "section_heading": p.get("section_heading", ""),
                        "full_text": p["full_text"],
                        "page_number": int(p["page_number"]),
                        "bbox": json.loads(p.get("bbox", "[]")),
                        "token_count": int(p.get("token_count", 0)),
                    }
            
            logger.info(f"✓ Retrieved {len(parents_map)}/{len(parent_ids)} parent sections via scroll fallback")
            return parents_map
            
    except Exception as e:
        logger.error(f"⚠️ CRITICAL: Failed to retrieve parent sections: {type(e).__name__}: {e}")
        logger.exception("Parent fetch traceback:")
    
    return parents_map


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

    # Encode query as sparse BM25 vector if available
    query_sparse = None
    if sparse_model and SPARSE_AVAILABLE:
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

    # Run searches - hybrid if sparse available, dense-only otherwise
    if query_sparse and SPARSE_AVAILABLE:
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
    else:
        # Dense-only search
        logger.info("Using dense-only search (sparse unavailable)")
        dense_hits = client.search(
            collection_name=config.QDRANT_COLLECTION,
            query_vector=models.NamedVector(name="dense", vector=query_dense),
            query_filter=qdrant_filter,
            limit=top_k,
            with_payload=True,
        )
        sparse_hits = []

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

        # ── Feedback correction boost ────────────────────────────────────────
        # Engineer-verified corrections are more trustworthy than raw manual text.
        # Boost their RRF score by 30% so they surface above generic manual chunks
        # when a similar fault pattern recurs on the same equipment.
        block_type = p.get("block_type", "paragraph")
        rrf_score = scores[cid]
        if block_type == "feedback_correction":
            rrf_score *= 1.3
            logger.debug(f"[RRF] Boosted feedback_correction chunk {cid}: {scores[cid]:.4f} → {rrf_score:.4f}")

        retrieved.append(
            RetrievedChunk(
                chunk_id=cid,
                doc_id=p["doc_id"],
                doc_name=p["doc_name"],
                equipment_tag=p.get("equipment_tag", ""),
                block_type=block_type,
                text=p["text"],
                page_number=int(p["page_number"]),
                bbox=bbox,
                section_heading=p.get("section_heading", ""),
                relevance_score=rrf_score,
                citation_ref="",
                parent_id=p.get("parent_id") or None,
            )
        )

    # Re-sort after boost so corrections surface to top
    retrieved.sort(key=lambda c: c.relevance_score, reverse=True)
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
