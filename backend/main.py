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
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
    init_db()         # Initialize SQLite database
    ensure_collection()   # creates Qdrant collection with dense + sparse vectors
    print("✓ Industrial Agent AI API ready")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
