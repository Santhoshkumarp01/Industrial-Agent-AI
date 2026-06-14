from typing import Optional
from pydantic import BaseModel


class ExtractedBlock(BaseModel):
    doc_id: str
    doc_name: str
    equipment_tag: str
    block_type: str  # paragraph | heading | list | table | figure_caption
    text: str
    page_number: int
    bbox: tuple  # (x0, y0, x1, y1)
    font_size: float
    is_bold: bool
    section_heading: str


class ParentSection(BaseModel):
    """A parent section containing multiple child chunks for parent-child retrieval."""
    parent_id: str                   # Unique ID for the parent section
    doc_id: str
    doc_name: str
    equipment_tag: str
    section_heading: str
    full_text: str                   # Complete section text (sent to LLM)
    page_number: int
    bbox: tuple                      # Bounding box of entire section
    block_types: list[str]          # Types of blocks in this section
    token_count: int
    child_chunk_ids: list[str]      # IDs of child chunks that belong to this parent


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    doc_name: str
    equipment_tag: str
    block_type: str
    text: str
    page_number: int
    bbox: tuple  # (x0, y0, x1, y1)
    section_heading: str
    chunk_index: int
    token_count: int
    parent_id: Optional[str] = None  # NEW: Link to parent section


class RetrievedChunk(BaseModel):
    chunk_id: str
    doc_id: str            # ← Added for PDF serving
    doc_name: str
    equipment_tag: str
    block_type: str        # ← ADDED: paragraph | heading | list | table | figure_caption
    text: str
    page_number: int
    bbox: tuple
    section_heading: str
    relevance_score: float
    citation_ref: str  # [C1], [C2], etc.
    parent_id: Optional[str] = None  # ← ADDED: Link to parent section for parent-child retrieval


class CitationRef(BaseModel):
    ref: str  # "[C1]"
    doc_id: str            # ← Added to fetch PDF from /pdf/{doc_id}
    doc_name: str
    page_number: int
    bbox: tuple  # (x0, y0, x1, y1)
    section_heading: str
    snippet: str  # First 120 chars of chunk text


class AnswerResponse(BaseModel):
    answer: str
    citations: list[CitationRef]
    retrieved_chunks: list[RetrievedChunk]


class ChatRequest(BaseModel):
    query: str
    equipment_tag: Optional[str] = None
    session_id: Optional[str] = None


class IngestResult(BaseModel):
    doc_id: str
    doc_name: str
    chunk_count: int
    page_count: int
    success: bool = True
    error_message: Optional[str] = None


class DocumentInfo(BaseModel):
    doc_id: str
    doc_name: str
    equipment_tag: str
    chunk_count: int


class SensorReading(BaseModel):
    equipment_id: str           # "RM1", "RM3", "BF1", "COMP_A"
    vibration: float            # mm/s
    temperature: float          # °C
    current: float              # Amperes
    pressure: float             # bar
    timestamp: str              # ISO format datetime string


class PredictionResult(BaseModel):
    equipment_id: str
    is_anomaly: bool
    anomaly_score: float        # 0.0 (normal) to 1.0 (very anomalous)
    risk_level: str             # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    timestamp: str


class SensorAlert(BaseModel):
    alert_id: str
    equipment_id: str
    equipment_name: str
    sensor_key: str             # which sensor triggered: "vibration" etc.
    sensor_value: float         # the anomalous reading value
    anomaly_score: float
    risk_level: str
    rul_hours: Optional[float]  # estimated hours to failure, None if unknown
    timestamp: str
    acknowledged: bool
    auto_chat_message: str      # pre-built message for frontend to send to chat


# ========== AGENT SYSTEM SCHEMAS ==========

class AgentInput(BaseModel):
    equipment_id: str
    equipment_name: str
    alert_description: str
    sensor_data: dict           # Current sensor readings
    anomaly_score: float
    risk_level: str
    rul_hours: Optional[float] = None
    triggered_by: str = "alert"  # "alert" or "chat"
    alert_id: Optional[str] = None
    session_id: Optional[str] = None


class RootCauseResult(BaseModel):
    root_cause: str
    fault_description: str
    confidence: float
    evidence: list[str]         # Citation refs like "[C1]", "[C2]"
    similar_incidents: list[dict]


class RiskResult(BaseModel):
    risk_level: str             # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    urgency_hours: float
    parts_required: list[str]
    parts_available: bool
    parts_stock: dict           # {part_name: quantity}


class MaintenancePlanResult(BaseModel):
    immediate_actions: list[str]
    repair_steps: list[str]
    long_term_recommendations: list[str]


class AnalysisResult(BaseModel):
    incident_id: str
    logbook_entry_id: str
    equipment_id: str
    equipment_name: str
    timestamp: str
    triggered_by: str
    
    # Root cause
    fault_description: str
    root_cause: str
    confidence_score: float
    evidence_sources: list[str]
    similar_incidents: list[dict]
    
    # Risk assessment
    risk_level: str
    urgency_hours: float
    parts_required: list[str]
    parts_available: bool
    parts_stock: dict
    
    # Maintenance plan
    immediate_actions: list[str]
    repair_steps: list[str]
    long_term_recommendations: list[str]
    
    # Context
    rul_hours: Optional[float]
    sensor_data: dict
    anomaly_score: float


class AnalyzeRequest(BaseModel):
    equipment_id: str
    equipment_name: str
    alert_description: str
    sensor_data: dict
    anomaly_score: float
    risk_level: str
    rul_hours: Optional[float] = None
    triggered_by: str = "alert"
    alert_id: Optional[str] = None
    session_id: Optional[str] = None


class FeedbackCreate(BaseModel):
    logbook_entry_id: str
    engineer_name: Optional[str] = "Unknown"
    verdict: str                # "confirmed" | "incorrect" | "partial"
    actual_root_cause: Optional[str] = None
    actual_action_taken: Optional[str] = None
    outcome: Optional[str] = None  # "resolved" | "escalated" | "pending"
    downtime_hours: Optional[float] = None


class LogbookEntryCreate(BaseModel):
    incident_id: str
    equipment_id: str
    equipment_name: str
    fault_description: str
    root_cause: str
    risk_level: str
    urgency_hours: float
    immediate_actions: list[str]
    repair_steps: list[str]
    long_term_recommendations: list[str]
    parts_required: list[str]
    parts_available: bool
    rul_hours: Optional[float]
    confidence_score: float
    evidence_sources: list[str]
    report_id: str
    fault_code: Optional[str] = None  # PDF-grounded fault code


class IncidentCreate(BaseModel):
    equipment_id: str
    equipment_name: str
    triggered_by: str
    alert_id: Optional[str] = None
    session_id: Optional[str] = None
    sensor_readings: dict
