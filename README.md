# Industrial Agent AI

**AI-powered steel plant maintenance intelligence system** using fine-tuned LLM, RAG pipeline, and multi-agent orchestration.

🤖 **Fine-tuned Model**: [Santhoshkumarp/phi35-maintenance-wizard-lora](https://huggingface.co/Santhoshkumarp/phi35-maintenance-wizard-lora)

## 🌐 Live Demo

**🚀 Frontend**: https://industrial-agent-ai.vercel.app/  
**⚙️ Backend API**: https://Santhoshkumarp-industrial-agent-ai.hf.space  
**📖 API Docs**: https://Santhoshkumarp-industrial-agent-ai.hf.space/docs

**Quick Test:**
- Visit the live frontend
- Navigate to **Live Monitor Intelligence**
- Press `Ctrl+Shift+D` to trigger demo anomaly
- Watch AI analysis with PDF citations appear automatically

---

## 🚀 Local Setup

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env: Add your QDRANT_URL and QDRANT_API_KEY
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

**Access**: Open http://localhost:3000

---

## 🎯 Key Features

- ✅ **Fine-tuned Phi-3.5 Mini** (3.8B params) specialized for steel plant maintenance
- ✅ **Hybrid RAG** (dense + sparse search) with parent-child retrieval
- ✅ **3-Agent System** (Root Cause → Risk Assessment → Maintenance Planning)
- ✅ **Real-time Monitoring** with ML anomaly detection (Isolation Forest)
- ✅ **Multi-turn Chat** with conversation memory
- ✅ **PDF Citation System** with exact page highlighting
- ✅ **Feedback Learning Loop** (engineer corrections improve RAG)
- ✅ **Auto-Generated Reports** and operations logbook

---

## 📁 Project Structure

```
Industrial Agent/
├── backend/
│   ├── agents/           # Multi-agent orchestration
│   ├── api/              # FastAPI routes
│   ├── llm/              # Fine-tuned model inference
│   ├── retrieval/        # RAG pipeline (hybrid search + reranking)
│   ├── vectorstore/      # Qdrant integration
│   ├── ml/               # Anomaly detection models
│   ├── database/         # SQLite (logbook, feedback, reports)
│   └── data/
│       └── knowledge/    # Historical incidents, SOPs, spare parts
│
└── frontend/
    └── src/
        ├── components/
        │   ├── chat/         # Document Q&A interface
        │   ├── monitoring/   # Live equipment dashboard
        │   └── layout/       # Navigation and panels
        └── hooks/            # State management

```

---

## 🤖 Fine-Tuned Model

**Base**: `microsoft/Phi-3.5-mini-instruct` (3.8B parameters)  
**Method**: LoRA (Low-Rank Adaptation) - 0.52% parameters trained  
**Dataset**: 2,027 steel plant maintenance examples  
**Hosted**: [HuggingFace](https://huggingface.co/Santhoshkumarp/phi35-maintenance-wizard-lora)

Training data includes:
- 1,973 real maintenance scenarios from steel plant experts
- 320 incident Q&A pairs (programmatic generation)
- 80 SOP procedure extractions
- 150 spare parts catalog queries

---

## 🎮 Demo Flow

1. Open **Live Monitor Intelligence** panel
2. Press `Ctrl+Shift+D` to simulate vibration anomaly on Rolling Mill
3. Watch automatic AI analysis with PDF citations
4. Navigate to **Operations Logbook** to see auto-generated entry
5. Click **Analysis Reports** for structured incident report
6. Provide feedback to improve future predictions

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Phi-3.5 Mini + LoRA (fine-tuned) |
| Vector DB | Qdrant Cloud (hybrid search) |
| Embeddings | sentence-transformers (768-dim, local) |
| Reranking | cross-encoder (ms-marco-MiniLM) |
| Backend | FastAPI + Python 3.11 |
| Frontend | React 18 + Vite + Zustand |
| ML | Isolation Forest (scikit-learn) |
| Database | SQLite |

---

## 📊 System Architecture

```
User Query → RAG Pipeline → LLM Generation → Citations
                ↓
    [Qdrant Hybrid Search]
        ├── Dense (semantic)
        ├── Sparse (BM25 keywords)
        └── Cross-encoder reranking
                ↓
    [Parent-Child Retrieval]
        └── Fetch full sections for context
                ↓
    [Fine-tuned Phi-3.5 Mini]
        └── Domain-specialized answers
```

---

## 📝 Environment Setup

Create `backend/.env`:
```env
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
USE_LOCAL_MODEL=true
LOCAL_MODEL_BASE=microsoft/Phi-3.5-mini-instruct
LOCAL_MODEL_ADAPTER=Santhoshkumarp/phi35-maintenance-wizard-lora
```

---

---

## 🌐 Deployment Architecture

```
User Browser
    ↓
Vercel Frontend (React + Vite)
https://industrial-agent-ai.vercel.app/
    ↓ API calls
HF Spaces Backend (FastAPI + Python)
https://Santhoshkumarp-industrial-agent-ai.hf.space
    ↓
├── SQLite (ephemeral - logbook, reports, feedback)
└── Qdrant Cloud (persistent - vector DB with documents)
```

**Backend Features:**
- Dual LLM backend: MLX (Mac) + Transformers (Linux/Windows)
- Auto-downloads fine-tuned model from HuggingFace (~24 MB)
- Ephemeral SQLite for session-based data
- Persistent Qdrant for knowledge base

**Frontend Features:**
- Static deployment on Vercel
- Environment variable: `VITE_API_BASE_URL` points to HF backend
- Real-time monitoring with live API polling
- PDF citation viewer with exact page highlighting

---

## 📦 Deployment Files

**For HF Spaces:**
- `Dockerfile` - Container configuration
- `backend/app.py` - HF Spaces entry point (port 7860)
- `backend/requirements_spaces.txt` - Linux dependencies

**For Vercel:**
- `frontend/vercel.json` - Build configuration
- `frontend/.env` - API base URL configuration

**Required Secrets (HF Spaces):**
```env
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
LOCAL_MODEL_BASE=microsoft/Phi-3.5-mini-instruct
LOCAL_MODEL_ADAPTER=Santhoshkumarp/phi35-maintenance-wizard-lora
```

---

## 🏆 Built For

**AI Hackathon Round 2 — Agentic AI Challenge**  
**Domain**: Steel Manufacturing Plant Maintenance  
**GitHub**: https://github.com/Santhoshkumarp01/Industrial-Agent-AI  
**Live Demo**: https://industrial-agent-ai.vercel.app/  
**Backend**: https://Santhoshkumarp-industrial-agent-ai.hf.space
