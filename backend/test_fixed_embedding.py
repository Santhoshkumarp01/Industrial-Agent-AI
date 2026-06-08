"""Test embedding with correct model after SDK upgrade."""
import google.generativeai as genai
from config import config

genai.configure(api_key=config.GOOGLE_API_KEY)

# Test models that should work
models_to_test = [
    "models/embedding-001",           # v1beta model
    "models/text-embedding-004",      # v1 model (might need SDK update)
]

for model_name in models_to_test:
    try:
        print(f"\n🧪 Testing: {model_name}")
        result = genai.embed_content(
            model=model_name,
            content="test query"
        )
        dim = len(result['embedding'])
        print(f"✅ SUCCESS! Dimension: {dim}")
        print(f"✅ Use this model in config: {model_name}")
        
        if dim == 768:
            print(f"✅ Perfect! This is the 768-dim model we need!")
        break
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Failed: {error_msg[:200]}")
