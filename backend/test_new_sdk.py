"""Test with the new google.genai SDK."""
from google import genai
from google.genai import types
from config import config

# Initialize client
client = genai.Client(api_key=config.GOOGLE_API_KEY)

# Test different embedding model names
models_to_test = [
    "text-embedding-004",
    "gemini-embedding-001",
    "embedding-001",
]

for model_name in models_to_test:
    try:
        print(f"\n🧪 Testing: {model_name}")
        
        result = client.models.embed_content(
            model=model_name,
            contents="Hello world test query"
        )
        
        if hasattr(result, 'embeddings') and len(result.embeddings) > 0:
            dim = len(result.embeddings[0].values)
            print(f"✅ SUCCESS! Model: {model_name}")
            print(f"✅ Embedding dimension: {dim}")
            
            if dim == 768:
                print(f"✅ PERFECT! This is the 768-dim model we need!")
                print(f"✅ Update config to use: {model_name}")
            break
        else:
            print(f"❌ Unexpected response format")
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Failed: {error_msg[:250]}")
