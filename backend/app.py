"""
Hugging Face Spaces entry point for Industrial Agent AI.

This file starts the FastAPI backend on HF Spaces.
HF Spaces expects the app to run on port 7860.

Set these Secrets in your HF Space settings:
  QDRANT_URL       = your Qdrant Cloud URL
  QDRANT_API_KEY   = your Qdrant API key
  LOCAL_MODEL_BASE = microsoft/Phi-3.5-mini-instruct
  LOCAL_MODEL_ADAPTER = Santhoshkumarp/phi35-maintenance-wizard-lora
"""

import os
import uvicorn

# HF Spaces requires port 7860
PORT = int(os.getenv("PORT", 7860))

if __name__ == "__main__":
    from main import app
    
    # Run with reduced logging for HF Spaces (suppress high-frequency sensor logs)
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=PORT,
        log_level="warning",  # Only show warnings and errors, not INFO
        access_log=False  # Disable access logs completely to prevent log spam
    )
