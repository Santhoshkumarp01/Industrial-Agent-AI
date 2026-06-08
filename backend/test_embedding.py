"""Quick test to find the correct Google embedding model name."""
import google.generativeai as genai
from config import config

genai.configure(api_key=config.GOOGLE_API_KEY)

# Test different model names
models_to_test = [
    "models/text-embedding-004",
    "models/embedding-001", 
    "text-embedding-004",
    "models/text-embedding-preview-0409",
]

for model_name in models_to_test:
    try:
        print(f"\n🧪 Testing: {model_name}")
        result = genai.embed_content(
            model=model_name,
            content="test query",
            task_type="retrieval_query"
        )
        print(f"✅ SUCCESS! Dimension: {len(result['embedding'])}")
        print(f"✅ Use this model: {model_name}")
        break
    except Exception as e:
        print(f"❌ Failed: {str(e)[:150]}")
