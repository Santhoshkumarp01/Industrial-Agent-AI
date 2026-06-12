# Industrial Agent AI
## Complete System Overview

---

## 1. Project Summary

**Industrial Agent AI** is an intelligent, offline-first maintenance decision-support system built for steel plant equipment. It combines a fine-tuned Large Language Model, a production-grade RAG pipeline, real-time sensor monitoring, multi-agent orchestration, engineer feedback learning, and multi-turn conversational AI — all running locally on Apple Silicon with no cloud LLM dependency.

**Hackathon**: AI Hackathon Round 2 — Agentic AI Challenge
**Domain**: Steel manufacturing (Rolling Mills, BF Blowers, Compressors, Plant Motors)
**HF Model**: https://huggingface.co/Santhoshkumarp/phi35-maintenance-wizard-lora

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, Zustand (state), react-pdf, Recharts |
| Backend | FastAPI (Python 3.11), Uvicorn ASGI |
| LLM | Microsoft Phi-3.5 Mini Instruct (3.8B) + LoRA fine-tune via Apple MLX |
| Vector DB | Qdrant Cloud (hybrid dense + sparse) |
| Embeddings | sentence-transformers/all-mpnet-base-v2 (768-dim, local) |
| Reranking | cross-encoder/ms-marco-MiniLM-L-12-v2 (local) |
| Sparse Search | BM25 via fastembed |
| Relational DB | SQLite (incidents, logbook, feedback, reports) |
| ML Anomaly | Isolation Forest (scikit-learn, per-machine models) |
| PDF Extraction | PyMuPDF (fitz) + Docling |
| NLTK | Sentence tokenization for chunking |

---

## 3. Fine-Tuned LLM — The Core Innovation

### 3.1 Base Model
- **Microsoft Phi-3.5 Mini Instruct** (3.8B parameters)
- Chosen for Apple Silicon compatibility, small size, strong instruction following

### 3.2 Fine-Tuning Method — LoRA (Low-Rank Adaptation)
- Only **0.52% of parameters** trained (20M of 3.8B)
- LoRA rank: 8, scale: 20.0, target modules: all linear layers
- Trainable layers: 16 (last N transformer blocks)
- This approach avoids catastrophic forgetting while domain-specializing

### 3.3 Training Framework — Apple MLX
- Apple's unified memory framework for M-series chips
- 10–15× faster than PyTorch on Apple Silicon
- LoRA adapter trained using `mlx_lm.lora` command
- Runs entirely offline — no cloud GPU needed

### 3.4 Training Data — 2,027 Examples
| Source | Count | Type |
|---|---|---|
| Industrial expert Q&A | 1,973 | Real maintenance scenarios from steel plant |
| Incident history (auto-generated) | 320 | 40 failures × 8 Q&A templates |
| SOPs (bearing, motor, compressor, lube) | 80 | Step-by-step procedure Q&A |
| Spare parts catalog | 150 | Part numbers, stock levels, warehouse |
| Sensor threshold knowledge | 96 | Normal/Warning/Critical per equipment |
| Multi-turn diagnostics | 50 | Progressive fault diagnosis conversations |
| Prioritisation scenarios | 60 | Multi-equipment triage decisions |

**Data Pipeline**:
1. Raw JSONL normalized to Alpaca 2-field format (instruction + output)
2. Quality filter: min 50 chars instruction, 100 chars output
3. Deduplication via fingerprint hash
4. 90/10 train/eval split (1,824 train / 203 eval)
5. Convert to MLX JSONL format

### 3.5 Training Configuration
```
Iterations:     150  (early-stopped at lowest val loss)
Learning rate:  5e-6
Batch size:     4
LoRA rank:      8
LoRA scale:     20.0
Val every:      25 steps
Save every:     25 steps
Max seq len:    2048
```

### 3.6 Training Results
```
Iter 1:   Train loss 2.847 | Val loss 2.067  (random guessing)
Iter 25:  Train loss 0.891 | Val loss 0.520  (learning patterns)
Iter 50:  Train loss 0.542 | Val loss 0.380  (domain knowledge)
Iter 75:  Train loss 0.392 | Val loss 0.310  (optimal zone)
Iter 100: Train loss 0.298 | Val loss 0.305  (selected checkpoint)
Iter 150: Train loss 0.232 | Val loss 0.340  (slight overfit)
```
**Best checkpoint: Iteration 100** (lowest validation loss)

### 3.7 Model Hosted on Hugging Face
- **Repo**: `Santhoshkumarp/phi35-maintenance-wizard-lora`
- **Uploaded**: `adapters.safetensors` (25.2 MB) + `adapter_config.json` + `README.md`
- Base model stays at `microsoft/Phi-3.5-mini-instruct` — only adapter uploaded
- `mlx_lm.load()` pulls adapter automatically from HF at inference time

### 3.8 Inference
- Cold start: ~15–20s (model loading into unified memory)
- Subsequent calls: ~8–12s per generation
- Prompt format: Phi-3.5 `<|system|>...<|end|>\n<|user|>...<|end|>\n<|assistant|>`
- Max tokens: 800 per call

---

## 4. RAG Pipeline — Retrieval-Augmented Generation

### 4.1 Document Ingestion Pipeline
```
PDF Upload
  ↓
PyMuPDF — extract text blocks with bbox, page number, font size
  ↓
Block classification — paragraph / heading / list / table / figure_caption
  ↓
Section detection — detect heading hierarchy, assign section_heading to each block
  ↓
Semantic chunking — parent-child structure
  ├── Child chunks (350–500 tokens, searchable via embeddings)
  └── Parent sections (complete section text, fetched when child matches)
  ↓
Embedding — sentence-transformers/all-mpnet-base-v2 (768-dim, local, MPS)
  ↓
Sparse encoding — BM25 via fastembed (for keyword matching)
  ↓
Qdrant upsert
  ├── maintenance_docs — child chunks with dense + sparse vectors
  └── maintenance_docs_parents — parent sections (dummy vector, payload only)
```

### 4.2 Chunking Strategy
| Block type | Max tokens | Strategy |
|---|---|---|
| Paragraph | 450 | Sentence-aware split with 1-sentence overlap |
| List | 800 | Keep full list together, avoid splitting bullets |
| Table | 100/row-group | Preserve table structure row by row |
| Heading | minimal | Attached to following paragraph |

### 4.3 Parent-Child Retrieval
- **Why**: Child chunks (small, precise) match query well but lack full context
- **How**: Each child stores `parent_id` pointing to its parent section
- **At retrieval time**: Child matched → fetch parent from `maintenance_docs_parents` → send complete section text to LLM
- **Result**: LLM sees full paragraphs/lists, not fragments — eliminates truncated list answers

### 4.4 Hybrid Search — Dense + Sparse RRF Fusion
```
Query
  ├── Dense embedding (768-dim cosine similarity) — semantic understanding
  └── Sparse BM25 (keyword match) — exact term recall

Both searches run in parallel on Qdrant

Reciprocal Rank Fusion (RRF):
  score(doc) = dense_weight × 1/(k + rank_dense)
             + sparse_weight × 1/(k + rank_sparse)

Default weights:  dense=0.60, sparse=0.40
Exact-term query: dense=0.50, sparse=0.50  (part numbers, fault codes)
k = 60 (RRF damping factor)
```

### 4.5 Query Rewriting
- Before searching, the query is rewritten into 3–5 semantic variations
- All variations searched, results deduplicated by chunk_id
- Handles vague questions like "why is the machine noisy" → searches "bearing wear", "vibration fault", "mechanical resonance"

### 4.6 Cross-Encoder Reranking
- Top-20 candidates from hybrid search → cross-encoder (ms-marco-MiniLM-L-12-v2)
- Scores each query-chunk pair directly (not just embedding similarity)
- Returns top-8 most relevant chunks
- Significantly improves precision over embedding-only retrieval

### 4.7 Confidence Scoring
- Computed from cross-encoder scores of top-K chunks
- HIGH / MEDIUM / LOW classification
- LOW confidence → caveat prefix added to LLM answer
- MEDIUM → suggestion to verify for critical operations

### 4.8 Feedback Correction Boost
- Engineer marks analysis as "incorrect" → correction stored in Qdrant as `block_type=feedback_correction`
- In RRF scoring: `feedback_correction` chunks multiplied by **1.3× boost**
- Engineer-verified knowledge surfaces above raw manual text for same fault pattern
- Closes the feedback → retrieval improvement loop

### 4.9 Historical Incidents as RAG Knowledge
- `incidents.json` (10 real steel plant failures, 2022–2024) indexed into Qdrant at startup
- Each incident = structured text: symptoms + root cause + contributing factors + action taken + recurrence prevention
- Tagged with correct machine tag slugs (not old short IDs like RM1/BF1)
- Equipment ID mapping: RM1/RM3 → `rolling-mill-main-drive-motor`, BF1 → `blower-large-motor-reference`, COMP_A → `industrial-induction-compressor-motor`
- Guard prevents re-indexing on restarts (checks `already_indexed` before running)

### 4.10 RAG Strict Grounding Rules
The LLM system prompt enforces:
- ONLY use information from provided [Cn] context chunks
- NEVER invent values (temperatures, torques, part numbers)
- NEVER write section numbers unless they appear in context
- For list questions: return complete list exactly as in manual
- Section locking: for list questions, only single best-matching section provided
- Anti-hallucination guard: strips invented section numbers from answers post-generation
- Citation integrity check: verifies cited section matches what was actually provided

### 4.11 What Is and Is NOT Stored in Qdrant
| Stored in Qdrant | NOT stored in Qdrant |
|---|---|
| Uploaded equipment manuals (PDFs) | Live sensor readings |
| Maintenance SOPs | Runtime anomaly events |
| Historical incidents (incidents.json) | Machine log buffer entries |
| Engineer correction feedback | Transient monitoring data |

---

## 5. Multi-Agent Orchestration System

Used for deep alert-triggered analysis via `/agents/analyze`:

### Agent 1 — Root Cause Analyzer
1. Receives sensor readings + anomaly score from ML model
2. Builds targeted RAG query from sensor state
3. Searches Qdrant: manuals + SOPs + historical incidents + feedback corrections
4. Queries SQLite incident history for past failures on same equipment
5. Sends retrieved evidence + sensor data to fine-tuned LLM
6. Returns: `root_cause`, `fault_description`, `confidence`, `evidence_citations`, `similar_incidents`

### Agent 2 — Risk Assessor
1. Receives root cause from Agent 1
2. Rule-based risk scoring:
   - Anomaly score ≥ 0.8 → +40 points
   - RUL < 24h → +40 points
   - CRITICAL equipment → +20 points
3. Score → risk level: CRITICAL (≥80) / HIGH (≥60) / MEDIUM (≥40) / LOW
4. Identifies required parts from root cause keywords
5. Queries `spare_parts.csv` for stock availability and warehouse location
6. Returns: `risk_level`, `urgency_hours`, `parts_required`, `parts_available`, `parts_stock`

### Agent 3 — Maintenance Planner
1. Receives root cause + risk level from Agents 1 & 2
2. RAG search for relevant SOPs and procedure sections
3. Generates immediate safety actions based on risk level
4. Fine-tuned LLM extracts repair steps from retrieved SOP chunks
5. Adds long-term preventive recommendations
6. Returns: `immediate_actions`, `repair_steps`, `long_term_recommendations`

### Orchestrator
- Sequential pipeline: Agent 1 → Agent 2 → Agent 3
- Each agent builds on previous outputs
- Creates logbook entry + incident record + report in SQLite
- Fallback to rule-based logic if LLM generation fails

---

## 6. Machine Analysis Pipeline (Live Monitor)

Separate from the 3-agent system, designed for real-time machine card analysis:

```
Equipment card click / Ctrl+Shift+D / "View Analysis"
  ↓
GET /machine-analysis/logs/{tag}?count=10
  → Fetch latest 10 log entries from in-memory buffer (never from Qdrant)
  ↓
_get_historical_context(machine_tag)
  → Query SQLite logbook for last 5 entries on this machine
  → Format as "HISTORICAL MAINTENANCE RECORDS" block
  ↓
_build_analysis_query(machine_tag, logs)
  → Build NL query from anomaly state:
    NORMAL → "What are standard maintenance checks?"
    CRITICAL → "Machine has CRITICAL fault FC-VM-01, vibration 9.2 mm/s..."
  ↓
retrieve(query, equipment_tag)
  → Hybrid search in Qdrant scoped to machine's mapped manual
  → Rerank with cross-encoder
  → Fetch parent sections
  → Confidence scoring
  ↓
format_logs_for_llm(machine_tag, logs)
  → Structured text: thresholds + sensor readings table + current status
  ↓
LLM prompt = log_block + historical_context + manual_chunks
  → generate_answer() with strict grounding rules
  → Dynamic answer from current logs + retrieved PDF — no hardcoding
  ↓
map_citations()
  → CitationRef objects with page number + bbox for PDF highlighting
  ↓
If severity == WARNING or CRITICAL:
  → INSERT INTO incidents (incident row)
  → create_entry() → logbook_entries row
  → _store_report() → reports row
  → All 3 DB tables populated → Logbook + Analysis Reports panels update
  ↓
Return: answer + citations + sensor readings + fault_code + logbook_entry_id
```

---

## 7. Dynamic Machine Log Generation

### 4 Configured Machines
| Machine Tag | Display Name | RPM Nominal |
|---|---|---|
| rolling-mill-main-drive-motor | Rolling Mill Main Drive Motor | 1480 |
| general-plant-motor | General Plant Motor | 1450 |
| industrial-induction-compressor-motor | Industrial Induction / Compressor Motor | 1475 |
| blower-large-motor-reference | BF Blower / Large Motor | 990 |

### Sensor Simulation — Random Walk Model
- Initial state: mid-range of normal thresholds
- Each tick: `new_value = current + drift + noise`
  - Drift: `(hi - lo) × 0.002` per tick (slow upward degradation simulation)
  - Noise: `±3%` of normal range (random walk)
  - Soft clamp: allow up to 1.5× normal max for anomaly simulation
- `inject_anomaly=True`: spikes one random sensor to 1.1–1.4× critical threshold

### Threshold-Based Anomaly Detection
- NORMAL → WARNING → CRITICAL thresholds per sensor per machine
- Rule: pressure sensors — low is bad; all others — high is bad
- Overall severity = worst sensor across all 4 readings
- Primary sensor → fault code assignment (FC-VM-xx vibration, FC-TH-xx temp, FC-CU-xx current, FC-LP-xx pressure)
- RPM degraded: CRITICAL → 80–93% nominal; WARNING → 93–99% nominal

### In-Memory Log Buffer
- `collections.deque(maxlen=50)` per machine
- Thread-safe, never written to disk or Qdrant
- `get_latest_logs()` generates initial entries if buffer empty

### Machine → Document Mapping
```python
"rolling-mill-main-drive-motor"        → "Steel Plant - Rolling Mill Main Drive Motor Manual.pdf"
"general-plant-motor"                  → "Steel Plant - General Plant Motor Manual.pdf"
"industrial-induction-compressor-motor"→ "Steel Plant - Industrial Induction Compressor Motor Manual.pdf"
"blower-large-motor-reference"         → "Steel Plant - Blower Large Motor Reference Manual.pdf"
```

---

## 8. ML Anomaly Detection (Isolation Forest)

- **Algorithm**: Isolation Forest (unsupervised, no labeled anomaly data needed)
- **Separate model per equipment**: isolation_forest_rm1.pkl, bf1.pkl, comp_a.pkl, etc.
- **Training data**: `sensor_data.csv` (historical normal operation patterns)
- **Features**: vibration, temperature, current, pressure, operating_hours
- **Output**: `is_anomaly` (bool) + `anomaly_score` (0.0–1.0) + `risk_level`
- **Fallback**: If model files missing, threshold-based prediction used automatically
- Anomaly score fed to **Risk Agent** as input (higher score → higher urgency)

---

## 9. Multi-Turn Session Memory

### Architecture
- Each chat session has a unique `session_id` (UUID, generated client-side)
- Backend maintains `_session_history` dict: `session_id → list of {role, content}`
- Sliding window: last **6 messages** (3 user + 3 assistant) retained per session

### How It Works
```
Request arrives with session_id
  ↓
Fetch last 6 messages from _session_history[session_id]
  ↓
Format as:
  === PREVIOUS CONVERSATION ===
  Engineer: [user turn 1]
  Assistant: [assistant turn 1, truncated to 300 chars]
  Engineer: [user turn 2]
  ...
  === END PREVIOUS CONVERSATION ===
  ↓
Prepend to current query before LLM generation
  (retrieval still uses original query only — no history contamination)
  ↓
After generation:
  Append user message + assistant response to history
  Trim to last 6 messages
```

### Separation of Histories
- **Chat Assistant** and **Live Monitor AI** use completely independent `useChat()` hook instances
- Each has its own `sessionId`, its own `messages` array, and its own backend session history
- No message ever crosses between the two panels

---

## 10. Feedback-Driven Improvement Loop

```
Analysis result shown in monitor chat
  ↓
Engineer navigates to Operations Logbook
  ↓
Clicks logbook entry → expanded row shows feedback form
  ↓
Engineer marks: ✅ Confirmed | ✗ Incorrect
  → If Incorrect: provides actual_root_cause + action_taken + outcome + downtime_hours
  ↓
POST /agents/feedback
  → Stored in SQLite feedback table (linked to logbook_entry_id)
  ↓
If verdict == "incorrect":
  → ingest_text_chunk(correction_text, block_type="feedback_correction", equipment_tag)
  → Stored as searchable chunk in Qdrant
  ↓
Next time same machine analyzed:
  → feedback_correction chunk retrieved alongside manual chunks
  → 1.3× RRF score boost ensures it surfaces above generic manual text
  → LLM sees: "Engineer previously corrected: actual cause was X, resolved by Y"
  → Future recommendation improves automatically

GET /agents/feedback/stats
  → confirmed%, incorrect%, total count
  → Demonstrates continuous learning over time
```

---

## 11. Frontend Architecture

### Panel Structure
| Panel | Description | History |
|---|---|---|
| 💬 Chat Assistant | Document Q&A with PDF viewer, multi-turn | Own session |
| 📡 Live Monitor Intelligence | 4-machine dashboard + always-visible AI chat | Own session (separate) |
| 📁 Documents | Inline PDF viewer (iframe, page navigation) | — |
| 🗂️ Analysis Reports | Structured incident reports from analyses | — |
| 📋 Operations Logbook | Auto-populated incident log + feedback | — |

### State Management — Zustand
- `activePanel` — current nav panel
- `activeCitation` + `isPDFViewerOpen` — PDF viewer state
- `isMonitorChatOpen` (legacy, kept for compat)
- `documents[]` + `selectedDocumentId`
- `setActiveCitation()` — opens PDF viewer at specific page with bbox highlight

### Separate Chat Histories
```
useChat()                 → Chat Assistant panel
                            - own messages[]
                            - own sessionId
                            - sends to /chat

useChat({isMonitor:true}) → Monitor AI panel
                            - own messages[]
                            - own sessionId
                            - does NOT call /chat
                            - only receives analysis results via addAnalysisMessage()
```

### Equipment Card Click Flow (Monitor Panel)
```
User clicks equipment card
  ↓
addEquipmentPrompt() called
  → Removes any existing prompt card (no stacking)
  → Adds new EquipmentPromptCard to monitor chat
  → Shows: machine name, severity dot (🔴🟡🟢), live sensor readings
  → 3 quick question buttons (sends to /chat on click)
  → "RUN FULL AI ANALYSIS →" button
  ↓
User clicks quick question → sendMessage() → /chat
User clicks full analysis → runAnalysis() → /machine-analysis/analyze/{tag}
```

### Analyzing Message Pattern
```
User triggers analysis
  ↓
addAnalyzingMessage("🔍 Analyzing Rolling Mill...") → returns id
  → Placeholder bubble shown immediately (user sees activity)
  ↓
await runMachineAnalysis(...)
  ↓
replaceAnalyzingMessage(id, result)
  → Finds placeholder by id, replaces in-place
  → No stacking, no duplicate bubbles
  ↓
On error: replaceAnalyzingWithError(id, errorText)
```

### Ctrl+Shift+D Demo Flow
```
Ctrl+Shift+D pressed
  ↓
sensorHook.triggerAnomaly('rolling-mill-main-drive-motor', 'vibration')
  → Frontend simulator starts spiking vibration sensor
  ↓
POST /machine-analysis/inject-anomaly/rolling-mill-main-drive-motor
  → Backend log buffer gets CRITICAL entry
  ↓
setActivePanel('monitor')  ← switches to monitor panel
  ↓
After 3 seconds:
  addAnalyzingMessage("⚡ Anomaly detected — Analyzing Rolling Mill...")
  ↓
POST /machine-analysis/analyze/rolling-mill-main-drive-motor
  → Full RAG analysis runs
  ↓
replaceAnalyzingMessage(id, result)
  → Analysis appears in monitor chat
  ↓
Logbook entry + incident + report created automatically in SQLite
```

---

## 12. PDF Viewer System

### Two Modes

**1. Citation mode** (from Chat Assistant):
- Citation tag clicked → `setActiveCitation({doc_id, page_number, bbox, ref})`
- `PDFViewer` component opens as full-height right panel
- Renders `GET /pdf/{doc_id}` via react-pdf `<Page>`
- Draws amber highlight overlay canvas on exact bbox coordinates
- Handles PDF → canvas coordinate transformation (PDF: bottom-left, Canvas: top-left)

**2. Document browse mode** (from Documents panel):
- Click any document in left pane → inline iframe renders `http://localhost:8000/pdf/{doc_id}#page=1`
- Prev/Next page navigation with page counter
- CORS: backend serves with `Access-Control-Allow-Origin: *`
- No react-pdf needed — uses browser's native PDF renderer

**3. Manual open mode** (from Monitor panel):
- Equipment card click → `openMachineManual(mapped_doc_name)`
- Finds doc_id by matching `doc_name` in documents list
- `setActiveCitation({doc_id, page_number: 1, bbox: null})` — opens at page 1, no highlight

---

## 13. Operations Logbook + Analysis Reports Connection

Both panels are fed by the same machine analysis pipeline:

### How They Get Populated
```
POST /machine-analysis/analyze/{tag}
  → severity == WARNING or CRITICAL
  ↓
1. INSERT INTO incidents table
   (incident_id, equipment_id, equipment_name, sensor_readings, timestamp)
   ↓
2. create_entry(LogbookEntryCreate)
   → INSERT INTO logbook_entries
   (fault_description, root_cause, risk_level, urgency_hours, immediate_actions,
    evidence_sources, confidence_score)
   ↓
3. _store_report(incident_id, logbook_entry_id, report_dict)
   → INSERT INTO reports
   (full report JSON with diagnosis, risk_assessment, maintenance_plan, sensor_data,
    citations from LLM answer, logbook link)
```

### Operations Logbook Shows
- Chronological table: equipment name, timestamp, root cause, risk badge, OPEN/RESOLVED status
- NEW badge for entries < 1 hour old
- Click row → expand: fault description, immediate actions, engineer feedback history
- Filter by equipment name
- Auto-refreshes

### Analysis Reports Shows
- Split pane: report list (left) + full detail (right)
- Each report: root cause, risk level, urgency hours, immediate actions, repair steps, sensor readings, evidence sources, full LLM answer with citations
- Filter by equipment, export to JSON
- Auto-refreshes every 10 seconds

---

## 14. Data Architecture

### Qdrant Collections
```
maintenance_docs
  ├── Child chunks (searchable via dense + sparse vectors)
  ├── Payload: chunk_id, doc_id, doc_name, equipment_tag, block_type,
  │           text, page_number, bbox, section_heading, parent_id
  └── Indexes: doc_id, equipment_tag, parent_id (KEYWORD type)

maintenance_docs_parents
  ├── Parent sections (full section text, dummy vector)
  ├── Payload: parent_id, doc_id, doc_name, equipment_tag,
  │           section_heading, full_text, page_number, bbox, token_count
  └── Index: parent_id (KEYWORD type)
```

### SQLite — maintenance_wizard.db
```sql
incidents         — equipment failure events
logbook_entries   — analysis results (auto-created on WARNING/CRITICAL)
feedback          — engineer confirmations and corrections
reports           — structured incident reports (auto-created on analysis)
```

### File Storage
```
backend/data/uploads/{doc_id}.pdf    — uploaded manuals
backend/data/knowledge/incidents.json — 10 historical incidents
backend/data/knowledge/spare_parts.csv — spare parts inventory
backend/data/knowledge/sops/*.txt    — SOP text files
backend/ml/saved_models/phi35_mlx_lora/adapters.safetensors — LoRA weights (also on HF)
backend/ml/saved_models/isolation_forest_*.pkl — ML anomaly models
```

---

## 15. Backend API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /upload | Ingest PDF into Qdrant |
| POST | /chat | RAG Q&A with multi-turn memory |
| GET | /documents | List all indexed documents |
| DELETE | /documents/{id} | Remove document from Qdrant |
| GET | /pdf/{doc_id} | Serve PDF file inline |
| GET | /citation/{sid}/{ref} | Resolve citation to bbox |
| POST | /sensors/reading | ML anomaly scoring |
| GET | /sensors/alerts | Active anomaly alerts |
| GET | /machine-analysis/logs/{tag} | Latest dynamic machine logs |
| GET | /machine-analysis/summary/{tag} | Latest reading + thresholds |
| POST | /machine-analysis/analyze/{tag} | Full RAG analysis |
| POST | /machine-analysis/inject-anomaly/{tag} | Demo anomaly spike |
| GET | /machine-analysis/machines | List all 4 configured machines |
| POST | /agents/analyze | Multi-agent deep analysis |
| GET | /agents/logbook | Operations logbook entries |
| GET | /agents/logbook/{id} | Single logbook entry with feedback |
| POST | /agents/feedback | Engineer feedback submission |
| GET | /agents/reports | Analysis reports |
| GET | /agents/feedback/stats | Accuracy metrics |
| GET | /health | Health check |

---

## 16. Setup & Run

### Backend
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set: QDRANT_URL, QDRANT_API_KEY
# LOCAL_MODEL_ADAPTER=Santhoshkumarp/phi35-maintenance-wizard-lora
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

### Fine-Tuned Model
- Adapter hosted at: `Santhoshkumarp/phi35-maintenance-wizard-lora`
- Base model: `microsoft/Phi-3.5-mini-instruct` (downloaded by mlx_lm automatically)
- Set `LOCAL_MODEL_ADAPTER=Santhoshkumarp/phi35-maintenance-wizard-lora` in `.env`
- First inference call: ~15–20s (model load); subsequent: ~8–12s

---

## 17. End-to-End Demo Flow

```
1. Open app → Live Monitor Intelligence panel
   → 4 equipment cards updating with live backend sensor values (every 5s)
   → Monitor AI chat ready (separate history from Chat Assistant)

2. Press Ctrl+Shift+D
   → Frontend simulator spikes Rolling Mill vibration sensor
   → Backend log buffer gets CRITICAL anomaly injected
   → Alert banner appears: "CRITICAL fault detected"
   → After 3s: "⚡ Anomaly detected — Analyzing Rolling Mill Main Drive Motor..."
   → Full analysis runs: logs + historical records + manual PDF chunks → LLM
   → Analysis posted in Monitor AI chat with cited sections from manual
   → Logbook entry + report auto-created in SQLite

3. Click "View Analysis" on alert banner
   → Same full analysis triggered with anomaly injected first

4. Click equipment card (e.g. BF Blower)
   → Equipment prompt card replaces previous card (no stacking)
   → Shows live sensor readings + severity status
   → 3 quick question buttons + "RUN FULL AI ANALYSIS" button
   → Click quick question → instant RAG answer
   → Click full analysis → complete machine analysis

5. Navigate to Documents panel
   → Click any uploaded manual → inline PDF viewer opens
   → Navigate pages with Prev/Next

6. Navigate to Chat Assistant panel
   → Upload a new manual (PDF drag/drop)
   → Ask question → RAG answer with citations
   → Click citation tag → PDF opens at exact page with amber highlight
   → Ask follow-up → multi-turn context maintained

7. Navigate to Operations Logbook
   → Auto-created entries from step 2 visible
   → Click row → expand: fault details, immediate actions
   → Provide feedback: ✅ Confirmed or ✗ Incorrect
   → If incorrect: enter actual root cause → stored in Qdrant for future learning

8. Navigate to Analysis Reports
   → Structured report from step 2 visible
   → Click report → full detail: root cause, risk, repair steps, LLM answer, citations
   → Export to JSON button
```

---

## 18. Key Technical Differentiators

| Feature | Technique | Impact |
|---|---|---|
| Offline-first LLM | Phi-3.5 Mini + LoRA via Apple MLX | No cloud API, on-device inference |
| Domain specialization | Fine-tuning on 2,027 steel plant examples | Domain-accurate answers |
| Hybrid search | Dense (cosine) + Sparse (BM25) + RRF fusion | Better recall than dense-only |
| Parent-child retrieval | Child matches, parent context delivered | No truncated lists or fragments |
| Query rewriting | 3-5 semantic variations searched | Handles vague user queries |
| Feedback → RAG | Corrections indexed with 1.3× boost | System improves from engineer input |
| Historical incidents as RAG | incidents.json indexed at startup | Past failures inform future diagnoses |
| Multi-turn memory | 6-message sliding window per session | Context-aware follow-up questions |
| Separate chat histories | Independent useChat() hook instances | Clean isolation between panels |
| Auto logbook + reports | Created on every WARNING/CRITICAL analysis | Zero manual documentation effort |
| Analyzing placeholder | In-place message replacement pattern | Clean UX, no stacking bubbles |
| No live data in Qdrant | Guard in ingest_text_chunk() | Clean separation, no noise in RAG |
| Anti-hallucination | Section locking + post-generation guards | Verifiable, traceable answers |

---

**GitHub**: https://github.com/Santhoshkumarp01/Industrial-Agent-AI
**HF Model**: https://huggingface.co/Santhoshkumarp/phi35-maintenance-wizard-lora
**Built for AI Hackathon Round 2 — Agentic AI Challenge**
