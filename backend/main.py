import nltk
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.sensor_routes import router as sensor_router
from api.agent_routes import router as agent_router
from api.machine_analysis_routes import router as machine_analysis_router
from vectorstore.qdrant_store import ensure_collection
from database.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Industrial Agent AI — RAG API",
    description=(
        "Industrial AI system for steel plant maintenance. "
        "Upload equipment manuals and SOPs, monitor live sensor streams, "
        "detect anomalies, diagnose faults, and get cited answers from "
        "a fine-tuned LLM grounded in equipment documentation."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(sensor_router)
app.include_router(agent_router)
app.include_router(machine_analysis_router)


@app.on_event("startup")
async def startup():
    """Initialize all components on server startup."""
    print("🚀 Starting Industrial Agent AI backend...")
    
    # 1. Download NLTK data
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
    
    # 2. Initialize database
    init_db()
    print("✓ SQLite database initialized")
    
    # 3. Ensure Qdrant collection exists
    ensure_collection()
    print("✓ Qdrant collection ready")

    # 4. Index historical incidents.json if not already indexed
    _index_incidents_if_needed()
    
    # 5. Preload models for fast first request
    print("⏳ Preloading models...")
    try:
        from embeddings.embedder import _get_local_model
        _get_local_model()
        print("  ✓ Embedding model loaded (sentence-transformers)")
        
        from retrieval.reranker import _get_cross_encoder
        _get_cross_encoder()
        print("  ✓ Cross-encoder loaded (reranking)")
        
        print("✓ All models preloaded - first request will be fast!")
    except Exception as e:
        print(f"⚠️  Model preloading failed: {e}")
        print("   Models will load on first request instead.")
    
    print("\n" + "="*60)
    print("✅ Industrial Agent AI API ready")
    print("   Backend: http://localhost:8000")
    print("   Fine-tuned model: Will load on first agent call (~15-20s)")
    print("="*60 + "\n")


def _index_incidents_if_needed():
    """
    Index incidents.json into Qdrant as historical knowledge if not already done.
    Each incident becomes a searchable chunk tagged as 'historical_incident'.
    Guards against re-indexing on every restart by checking for existing entries.
    """
    import json
    from pathlib import Path
    from vectorstore.qdrant_store import list_documents

    incidents_path = Path("data/knowledge/incidents.json")
    if not incidents_path.exists():
        print("⚠️  incidents.json not found, skipping historical indexing")
        return

    # Check if already indexed (doc_name contains "incidents")
    existing = list_documents()
    already_indexed = any("incident" in d.get("doc_name", "").lower() for d in existing)
    if already_indexed:
        print("✓ Historical incidents already indexed in Qdrant")
        return

    try:
        from ingestion.ingestor import ingest_text_chunk
        incidents = json.loads(incidents_path.read_text())

        # Map old short IDs to the correct machine tag slugs used in the system
        EQUIPMENT_ID_MAP = {
            "RM1":    "rolling-mill-main-drive-motor",
            "RM3":    "rolling-mill-main-drive-motor",
            "BF1":    "blower-large-motor-reference",
            "COMP_A": "industrial-induction-compressor-motor",
            "GM1":    "general-plant-motor",
        }

        count = 0
        for inc in incidents:
            raw_equip_id = inc.get("equipment_id", "General")
            equip_tag = EQUIPMENT_ID_MAP.get(raw_equip_id, "general-plant-motor")

            # Format each incident as a readable text chunk
            text = (
                f"Historical Incident {inc.get('incident_id','?')} ({inc.get('date','?')})\n"
                f"Equipment: {inc.get('equipment_name','?')} ({raw_equip_id})\n"
                f"Symptoms: {inc.get('initial_observation','')}\n"
                f"Root Cause: {inc.get('root_cause','')}\n"
                f"Contributing Factors: {'; '.join(inc.get('contributing_factors', []))}\n"
                f"Action Taken: {inc.get('action_taken','')}\n"
                f"Parts Used: {', '.join(inc.get('parts_used', []))}\n"
                f"Downtime: {inc.get('downtime_hours', 0)}h\n"
                f"Outcome: {inc.get('outcome','')}\n"
                f"Recurrence Prevention: {inc.get('recurrence_prevention','')}"
            )
            ingest_text_chunk(
                text=text,
                doc_name="Steel Plant Historical Incidents",
                equipment_tag=equip_tag,
                block_type="historical_incident",
                source="incidents_knowledge_base",
            )
            count += 1
        print(f"✓ Indexed {count} historical incidents into Qdrant with correct equipment tags")
    except Exception as e:
        print(f"⚠️  Failed to index incidents: {e}")


@app.get("/")
async def root() -> dict:
    """Root endpoint - API info."""
    return {
        "name": "Industrial Agent AI API",
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
