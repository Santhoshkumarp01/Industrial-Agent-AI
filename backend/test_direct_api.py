"""Test direct REST API call to Google embeddings."""
import requests
from config import config

api_key = config.GOOGLE_API_KEY
model = "text-embedding-004"

# Direct REST API call
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"

payload = {
    "model": f"models/{model}",
    "content": {
        "parts": [{
            "text": "Hello world"
        }]
    }
}

print(f"Testing direct API call to {model}...")
response = requests.post(url, json=payload, timeout=30)

if response.status_code == 200:
    data = response.json()
    if 'embedding' in data:
        print(f"✅ SUCCESS! Embedding dimension: {len(data['embedding']['values'])}")
        print(f"✅ Model works: models/{model}")
    else:
        print(f"✅ Response received but unexpected format:")
        print(data)
else:
    print(f"❌ Failed with status {response.status_code}")
    print(response.text[:500])
