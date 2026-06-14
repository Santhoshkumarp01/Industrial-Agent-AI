# Visible 3-Agent System with Real-Time Progress Updates

## Overview
Implement a transparent 3-agent diagnostic system that shows users exactly what each AI agent is doing in real-time, similar to how Kiro displays its thinking process. Users will see each agent's analysis phase, progress, and outputs as they happen.

## Business Goals
- Demonstrate true "Agentic AI" capability to hackathon judges
- Build user trust through transparency of AI decision-making process
- Meet hackathon requirement: "Multi-agent reasoning with distinct outputs"
- Improve user experience by showing progress instead of blank "Analyzing..." state

## User Stories

### US-1: See Agent Execution Progress
**As a** maintenance engineer  
**I want to** see which AI agent is currently analyzing the equipment issue  
**So that** I understand what the system is doing and how long it will take

**Acceptance Criteria**:
- When I click "Demo Anomaly" or "Run Analysis", I see a progressive display showing:
  - "🔍 Agent 1: Analyzing root cause..."
  - "⚡ Agent 2: Assessing risk level..."
  - "🔧 Agent 3: Planning maintenance actions..."
- Each agent shows a loading spinner while active
- Completed agents show a checkmark ✓
- If an agent fails, show error icon ❌

### US-2: See Distinct Agent Outputs
**As a** maintenance engineer  
**I want to** see clearly separated outputs from each agent  
**So that** I understand what each agent contributed to the diagnosis

**Acceptance Criteria**:
- Final analysis shows 3 distinct sections:
  - **Agent 1: Root Cause Analysis** (with icon 🔍)
    - Fault diagnosis
    - Why it happened (sensor trend analysis)
    - Manual citations
  - **Agent 2: Risk Assessment** (with icon ⚡)
    - Risk level badge (RED=CRITICAL, ORANGE=WARNING)
    - Urgency timeline (24h/72h)
    - Potential consequences
  - **Agent 3: Maintenance Plan** (with icon 🔧)
    - Immediate actions (numbered list)
    - Required spare parts
    - Long-term recommendations
- Each section has clear visual separation (border, background color)

### US-3: Agent Streaming Updates
**As a** maintenance engineer  
**I want to** see partial results as each agent completes  
**So that** I can start reading the analysis while other agents are still working

**Acceptance Criteria**:
- Agent 1 results appear immediately after Agent 1 completes
- Agent 2 results append below Agent 1 when ready
- Agent 3 results append below Agent 2 when ready
- Each agent's output fades in smoothly
- Total analysis time is displayed at the end

### US-4: Agent Reasoning Transparency
**As a** maintenance engineer  
**I want to** see what data each agent used  
**So that** I can verify the analysis is grounded in real information

**Acceptance Criteria**:
- Each agent section shows:
  - "Data sources: [Machine logs, General Industrial Motor Manual p.45-46]"
  - Confidence level (HIGH/MEDIUM/LOW)
  - Number of manual citations found
- Citations are clickable to open PDF at exact page

## Technical Requirements

### Backend Changes

#### TR-1: Refactor Agent Orchestrator
**File**: `backend/agents/orchestrator.py`
- Split monolithic `run_analysis()` into 3 distinct agent calls:
  - `agent_1_root_cause(logs, chunks, query)`
  - `agent_2_risk_assessment(agent1_output, logs, chunks)`
  - `agent_3_maintenance_plan(agent1_output, agent2_output, chunks, spare_parts)`
- Each agent function returns structured output:
  ```python
  {
    "agent_id": "agent_1",
    "agent_name": "Root Cause Analyzer",
    "status": "completed",  # or "running", "failed"
    "output": {...},
    "confidence": "HIGH",
    "sources_used": ["Machine logs", "Manual p.45-46"],
    "execution_time_ms": 2341
  }
  ```

#### TR-2: Streaming Agent Updates API
**File**: `backend/api/machine_analysis_routes.py`
- Add new endpoint: `POST /machine-analysis/analyze-streaming/{machine_tag}`
- Return Server-Sent Events (SSE) stream with progress updates:
  ```json
  {"event": "agent_start", "data": {"agent_id": "agent_1", "name": "Root Cause Analyzer"}}
  {"event": "agent_progress", "data": {"agent_id": "agent_1", "status": "Retrieving manual sections..."}}
  {"event": "agent_complete", "data": {"agent_id": "agent_1", "output": {...}}}
  {"event": "agent_start", "data": {"agent_id": "agent_2", "name": "Risk Assessor"}}
  ...
  {"event": "analysis_complete", "data": {"total_time_ms": 8234}}
  ```
- Keep existing `/analyze/{machine_tag}` endpoint for backward compatibility

#### TR-3: Agent-Specific Prompts
**File**: `backend/agents/prompts.py` (new file)
- Create specialized prompts for each agent:
  - `ROOT_CAUSE_PROMPT`: Focus on fault diagnosis and sensor trend analysis
  - `RISK_ASSESSMENT_PROMPT`: Focus on consequence analysis and urgency
  - `MAINTENANCE_PLAN_PROMPT`: Focus on actionable repair steps
- Each prompt should enforce structured output format

#### TR-4: Spare Parts Integration
**File**: `backend/agents/spare_parts_checker.py` (new file)
- Parse `backend/data/knowledge/spare_parts.csv`
- Function: `check_spare_availability(part_name) -> dict`:
  ```python
  {
    "part_name": "SKF 6308 Bearing",
    "available": True,
    "quantity": 12,
    "procurement_lead_time_days": 3,
    "location": "Warehouse A-23"
  }
  ```
- Integrate into Agent 3 (Maintenance Plan)

### Frontend Changes

#### TR-5: Agent Progress Component
**File**: `frontend/src/components/monitoring/AgentProgressTracker.jsx` (new file)
- Display 3 agent cards with status:
  - Icon (🔍/⚡/🔧)
  - Agent name
  - Status indicator (spinner/checkmark/error)
  - Progress message
  - Execution time
- Example layout:
  ```
  ┌─────────────────────────────────────┐
  │ 🔍 Agent 1: Root Cause Analysis  ✓ │
  │    Completed in 2.3s                │
  ├─────────────────────────────────────┤
  │ ⚡ Agent 2: Risk Assessment       ⏳│
  │    Analyzing failure consequences...│
  ├─────────────────────────────────────┤
  │ 🔧 Agent 3: Maintenance Plan      ⏸ │
  │    Waiting for Agent 2...           │
  └─────────────────────────────────────┘
  ```

#### TR-6: Structured Agent Output Display
**File**: `frontend/src/components/monitoring/AgentOutputCard.jsx` (new file)
- Component props: `{ agentId, agentName, icon, output, confidence, sources, time }`
- Visual design:
  - Colored left border (blue for Agent 1, orange for Agent 2, green for Agent 3)
  - Agent name + icon header
  - Collapsible sections
  - Citation badges
  - Confidence indicator
- Show outputs in accordion-style expandable cards

#### TR-7: SSE Integration in MonitorChatPanel
**File**: `frontend/src/components/monitoring/MonitorChatPanel.jsx`
- Replace `runMachineAnalysis()` with `runMachineAnalysisStreaming()`
- Listen to SSE events and update UI in real-time:
  - `agent_start` → Show agent card with spinner
  - `agent_progress` → Update progress message
  - `agent_complete` → Show checkmark, append output card
  - `analysis_complete` → Show final summary

#### TR-8: API Service for SSE
**File**: `frontend/src/services/api.js`
- Add `runMachineAnalysisStreaming(machineTag, onEvent)`:
  ```javascript
  export const runMachineAnalysisStreaming = async (machineTag, onEvent) => {
    const eventSource = new EventSource(`${BASE}/machine-analysis/analyze-streaming/${machineTag}`)
    
    eventSource.addEventListener('agent_start', (e) => {
      onEvent('agent_start', JSON.parse(e.data))
    })
    
    eventSource.addEventListener('agent_complete', (e) => {
      onEvent('agent_complete', JSON.parse(e.data))
    })
    
    // ... other events
  }
  ```

## Data Models

### Agent Output Schema
```python
class AgentOutput(BaseModel):
    agent_id: str  # "agent_1", "agent_2", "agent_3"
    agent_name: str  # "Root Cause Analyzer", etc.
    status: str  # "running", "completed", "failed"
    output: dict  # Agent-specific output structure
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    sources_used: List[str]  # ["Machine logs", "Manual p.45"]
    citations: List[Citation]  # PDF citations
    execution_time_ms: int
    error: Optional[str]  # If failed
```

### Agent 1 Output Structure
```python
{
  "fault_diagnosis": "Bearing temperature exceeded alarm threshold (112.5°C > 110°C)",
  "root_cause": "Insufficient lubrication or bearing wear",
  "sensor_trend_analysis": "Temperature increased 15°C over past 2 hours",
  "manual_references": ["Section 8.9.3: Bearing overheats", "Table 5-2: Lubrication intervals"],
  "citations": [...]
}
```

### Agent 2 Output Structure
```python
{
  "risk_level": "CRITICAL",  # or "HIGH", "MEDIUM", "LOW"
  "urgency_hours": 24,
  "potential_consequences": [
    "Bearing seizure leading to motor shutdown",
    "Damage to shaft and housing",
    "Production line stoppage"
  ],
  "criticality_score": 0.85,
  "similar_past_incidents": 3
}
```

### Agent 3 Output Structure
```python
{
  "immediate_actions": [
    "Stop motor immediately to prevent catastrophic failure",
    "Inspect bearing for signs of wear or contamination",
    "Check lubrication system pressure and flow rate"
  ],
  "required_spare_parts": [
    {
      "part_name": "SKF 6308 Deep Groove Ball Bearing",
      "quantity": 2,
      "available": True,
      "procurement_lead_time_days": 3
    }
  ],
  "repair_steps": [...],
  "long_term_recommendations": [
    "Implement vibration monitoring for early bearing fault detection",
    "Review lubrication maintenance schedule"
  ],
  "estimated_repair_time_hours": 4
}
```

## UI/UX Design

### Visual Design Mockup
```
┌────────────────────────────────────────────────────────────┐
│  ANALYSIS IN PROGRESS                                      │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 🔍 Agent 1: Root Cause Analysis             ✓   │    │
│  │ Completed in 2.3s                                │    │
│  │                                                  │    │
│  │ Fault Diagnosis:                                 │    │
│  │ Bearing temperature exceeded alarm threshold... │    │
│  │                                                  │    │
│  │ 📊 Confidence: HIGH | 📚 Sources: Machine logs, │    │
│  │    General Industrial Motor Manual p.85-87      │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ ⚡ Agent 2: Risk Assessment                  ✓   │    │
│  │ Completed in 1.8s                                │    │
│  │                                                  │    │
│  │ Risk Level: 🔴 CRITICAL                         │    │
│  │ Urgency: Intervention required within 24 hours  │    │
│  │                                                  │    │
│  │ Potential Consequences:                          │    │
│  │ • Bearing seizure → motor shutdown               │    │
│  │ • Damage to shaft and housing                    │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 🔧 Agent 3: Maintenance Plan                 ⏳  │    │
│  │ Generating repair procedures...                  │    │
│  └──────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
```

## Success Metrics
- Agent execution phases are visible in UI within 100ms of starting
- Each agent completes analysis within 3 seconds
- Users can clearly identify which agent provided each recommendation
- 95%+ of agent outputs include at least 1 manual citation
- Total analysis time is reduced by streaming partial results

## Out of Scope (Future Work)
- Agent self-correction/retry logic
- Parallel agent execution (keep sequential for now)
- Agent memory/learning between sessions
- Custom agent configuration by users

## Dependencies
- Existing RAG pipeline must continue working
- No breaking changes to current `/analyze` endpoint
- SSE support in Uvicorn (already available)

## Testing Requirements
- Unit tests for each agent function
- Integration test for full 3-agent pipeline
- Frontend test for SSE event handling
- Manual QA: Run demo anomaly and verify all 3 agents show progress

## Timeline Estimate
- Backend agent refactoring: 3-4 hours
- SSE streaming implementation: 2-3 hours
- Frontend components: 3-4 hours
- Integration + testing: 2 hours
- **Total: 10-13 hours**
