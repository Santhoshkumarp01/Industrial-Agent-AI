import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration loaded from environment variables."""
    
    # --- API Keys ---
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
    
    # --- Qdrant connection ---
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION = "maintenance_docs"

    # --- Vector dimensions ---
    DENSE_DIM = 768   # all-mpnet-base-v2 output dimension

    # --- Embedding models ---
    EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"  # Local embedding model (768-dim)
    SPARSE_MODEL = "Qdrant/bm25"                                  # sparse (BM25 via fastembed)

    # --- Retrieval ---
    TOP_K_RETRIEVAL = 20   # candidates before rerank
    TOP_K_FINAL = 8        # after rerank

    # --- Hybrid search weights ---
    DENSE_WEIGHT = 0.6     # semantic similarity weight
    SPARSE_WEIGHT = 0.4    # keyword match weight

    # --- Chunking (Semantic-based with Docling) ---
    CHUNK_SIZE_TOKENS = 450          # Target for paragraphs (350-500 range)
    CHUNK_MAX_TOKENS = 600           # Hard maximum for regular chunks
    LIST_MAX_TOKENS = 800            # Lists can be longer to avoid splits
    CHUNK_OVERLAP_SENTENCES = 1      # Sentence overlap for paragraphs
    MIN_CHUNK_TOKENS = 25            # Minimum to filter noise
    TABLE_ROW_TOKENS = 100           # Target tokens per table row group

    # --- Fine-tuned Local Model (Phi-3.5 Mini) ---
    USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"
    LOCAL_MODEL_BASE = os.getenv("LOCAL_MODEL_BASE", "ml/base_models/phi35_mini")
    LOCAL_MODEL_ADAPTER = os.getenv("LOCAL_MODEL_ADAPTER", "ml/saved_models/phi35_mlx_lora")

    # --- Paths ---
    UPLOAD_DIR = "./data/uploads"


# Create a singleton instance
config = Config()
