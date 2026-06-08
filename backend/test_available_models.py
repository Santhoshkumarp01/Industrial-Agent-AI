"""Check what Gemini models are available."""
import google.generativeai as genai
from config import config

genai.configure(api_key=config.GOOGLE_API_KEY)

# Try the embedContent method with known Gemini model
print("Testing with models/gemini-pro...")
try:
    result = genai.embed_content(
        model="models/gemini-pro",
        content="test"
    )
    print(f"✅ gemini-pro works for embeddings! Dim: {len(result['embedding'])}")
except Exception as e:
    print(f"❌ gemini-pro failed: {str(e)[:200]}")

# Try text-embedding-004 without task_type
print("\nTesting models/text-embedding-004 without task_type...")
try:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content="test"
    )
    print(f"✅ text-embedding-004 works! Dim: {len(result['embedding'])}")
except Exception as e:
    print(f"❌ Failed: {str(e)[:200]}")

# Check installed version
import google.generativeai
print(f"\nInstalled google-generativeai version: {google.generativeai.__version__}")
