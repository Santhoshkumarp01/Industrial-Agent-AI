import nltk
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.sensor_routes import router as sensor_router
from api.agent_routes import router as agent_router
from vectorstore.qdrant_store import ensure_collection
from database.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Industrial Agent AI — RAG API",
    description=(
        "RAG pipeline for industrial maintenance decision support. "
        "Upload equipment manuals and SOPs, then ask natural language questions "
        "with exact source citations and PDF highlight coordinates."
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
    
    # 4. Preload models for fast first request
    print("⏳ Preloading models...")
    try:
        # Preload embedding model
        from embeddings.embedder import _get_local_model
        _get_local_model()
        print("  ✓ Embedding model loaded (sentence-transformers)")
        
        # Preload cross-encoder for reranking
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


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
