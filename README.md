# Industrial Agent AI

AI-powered industrial maintenance decision-support system for steel manufacturing plants using fine-tuned Phi-3.5 Mini model.

## Structure

```
Industrial Agent AI/
├── backend/       # RAG pipeline — FastAPI + Qdrant + Fine-tuned Phi-3.5 Mini
└── frontend/      # React dashboard — Control Room UI
```

## Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# API runs at http://localhost:8000
```

**Note**: The system uses a fine-tuned Phi-3.5 Mini model via MLX. No external API keys required for inference.

## Frontend

```bash
cd frontend
npm install
npm run dev
# UI runs at http://localhost:3000
```

## Demo

Press `Ctrl+Shift+D` in the UI to inject a vibration anomaly on Rolling Mill #3 and trigger the full alert → AI analysis flow.
