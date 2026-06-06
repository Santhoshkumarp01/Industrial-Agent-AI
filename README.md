# Industrial Agent AI

AI-powered industrial maintenance decision-support system for steel manufacturing plants.

## Structure

```
Industrial Agent AI/
├── backend/       # RAG pipeline — FastAPI + ChromaDB + Anthropic
└── frontend/      # React dashboard — Control Room UI
```

## Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# API runs at http://localhost:8000
```

## Frontend

```bash
cd frontend
npm install
npm run dev
# UI runs at http://localhost:3000
```

## Demo

Press `Ctrl+Shift+D` in the UI to inject a vibration anomaly on Rolling Mill #3 and trigger the full alert → AI analysis flow.
