"""List available models from Google AI."""
import requests
from config import config

api_key = config.GOOGLE_API_KEY
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

print("Fetching available models from Google AI API...")
response = requests.get(url, timeout=30)

if response.status_code == 200:
    data = response.json()
    models = data.get('models', [])
    
    print(f"\n✅ Found {len(models)} models\n")
    print("=" * 80)
    print("EMBEDDING MODELS:")
    print("=" * 80)
    
    for model in models:
        name = model.get('name', '')
        if 'embed' in name.lower():
            methods = model.get('supportedGenerationMethods', [])
            print(f"\n📦 {name}")
            print(f"   Methods: {', '.join(methods)}")
            print(f"   Description: {model.get('description', 'N/A')[:100]}")
    
    print("\n" + "=" * 80)
    print("ALL GEMINI MODELS:")
    print("=" * 80)
    
    for model in models:
        name = model.get('name', '')
        if 'gemini' in name.lower():
            methods = model.get('supportedGenerationMethods', [])
            print(f"\n📦 {name}")
            print(f"   Methods: {', '.join(methods)}")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text[:500])
