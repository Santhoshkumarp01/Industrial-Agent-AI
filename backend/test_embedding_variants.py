"""Test embedding variants with task_type and output_dimensionality."""
from google import genai
from google.genai import types
from config import config

client = genai.Client(api_key=config.GOOGLE_API_KEY)

# Test with output_dimensionality parameter to reduce dimensions
print("Testing gemini-embedding-001 with output_dimensionality=768...\n")
try:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents="Hello world test query",
        config=types.EmbedContentConfig(
            output_dimensionality=768,
            task_type="RETRIEVAL_QUERY"
        )
    )
    
    if hasattr(result, 'embeddings') and len(result.embeddings) > 0:
        dim = len(result.embeddings[0].values)
        print(f"✅ SUCCESS!")
        print(f"✅ Model: gemini-embedding-001")
        print(f"✅ Embedding dimension: {dim}")
        print(f"✅ This is PERFECT for our use case!")
        print(f"\n📝 Config to use:")
        print(f"   EMBEDDING_MODEL = 'gemini-embedding-001'")
        print(f"   output_dimensionality = 768")
    else:
        print(f"❌ Unexpected response")
        
except Exception as e:
    print(f"❌ Failed: {e}")
