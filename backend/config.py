import os


# --- Qdrant connection ---
# Local by default; switch to cloud by setting env vars
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)   # None = no auth (local)
QDRANT_COLLECTION = "maintenance_docs"

# --- Vector dimensions ---
DENSE_DIM = 384   # all-MiniLM-L6-v2 output dimension

# --- Embedding models ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"    # dense
SPARSE_MODEL = "Qdrant/bm25"             # sparse (BM25 via fastembed)

# --- Retrieval ---
TOP_K_RETRIEVAL = 15   # candidates before rerank (higher because hybrid finds more)
TOP_K_FINAL = 5        # after rerank

# --- Hybrid search weights ---
DENSE_WEIGHT = 0.6     # semantic similarity weight
SPARSE_WEIGHT = 0.4    # keyword match weight

# --- Chunking (unchanged) ---
CHUNK_SIZE_TOKENS = 400
CHUNK_OVERLAP_SENTENCES = 1
MIN_CHUNK_TOKENS = 10

# --- LLM (unchanged) ---
LLM_MODEL = "claude-haiku-4-5-20251001"
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.1

# --- Paths (unchanged) ---
UPLOAD_DIR = "./data/uploads"
