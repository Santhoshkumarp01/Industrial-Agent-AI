import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration loaded from environment variables."""
    
    # --- API Keys ---
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", None))
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
    
    # --- Qdrant connection ---
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION = "maintenance_docs"

    # --- Vector dimensions ---
    DENSE_DIM = 768   # text-embedding-004 output dimension

    # --- Embedding models ---
    EMBEDDING_MODEL = "gemini-embedding-001"         # Google embedding model (768-dim with output_dimensionality)
    SPARSE_MODEL = "Qdrant/bm25"                     # sparse (BM25 via fastembed)

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

    # --- LLM ---
    LLM_MODEL = "gemini-2.5-flash"  # Latest Gemini Flash model (verified working with v1beta API)
    LLM_MAX_TOKENS = 2048
    LLM_TEMPERATURE = 0.1

    # --- Paths ---
    UPLOAD_DIR = "./data/uploads"


# Create a singleton instance
config = Config()
