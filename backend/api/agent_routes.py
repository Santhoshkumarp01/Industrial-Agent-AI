"""
Agent API routes:

  POST /analyze              — Run multi-agent analysis on equipment anomaly
  POST /feedback             — Submit engineer feedback on analysis
  GET  /logbook              — Get maintenance logbook entries
  GET  /logbook/{entry_id}   — Get specific logbook entry
  GET  /reports              — Get all analysis reports
  GET  /reports/{report_id}  — Get specific report
  GET  /feedback/stats       — Get feedback accuracy statistics
"""

from fastapi import APIRouter, HTTPException
from models.schemas import (
    AnalyzeRequest, AnalysisResult, FeedbackCreate,
    LogbookEntryCreate
)
from agents.orchestrator import run_analysis
from database.logbook import get_all_entries, get_entry, mark_resolved
from database.feedback import store_feedback, get_feedback_for_entry, get_feedback_stats
from reports.report_generator import generate_report, get_report, get_all_reports

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_equipment(request: AnalyzeRequest):
    """
    Run multi-agent analysis on equipment anomaly.
    
    Triggers the orchestrator which coordinates:
    1. Root Cause Agent - diagnosis
    2. Risk Agent - urgency assessment  
    3. Maintenance Agent - work order generation
    
    Returns complete analysis with logbook entry ID.
    """
    try:
        result = run_analysis(
            equipment_id=request.equipment_id,
            equipment_name=request.equipment_name,
            alert_description=request.alert_description,
            sensor_data=request.sensor_data,
            anomaly_score=request.anomaly_score,
            risk_level_raw=request.risk_level,
            rul_hours=request.rul_hours,
            triggered_by=request.triggered_by,
            alert_id=request.alert_id,
            session_id=request.session_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/feedback")
async def submit_feedback(feedback: FeedbackCreate):
    """
    Submit engineer feedback on an analysis.
    
    If verdict is "incorrect", the correction is stored back into Qdrant
    for continuous learning.
    """
    try:
        feedback_id = store_feedback(feedback)
        return {
            "success": True,
            "feedback_id": feedback_id,
            "message": "Feedback stored successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store feedback: {str(e)}")


@router.get("/logbook")
async def get_logbook(equipment_id: str = None, limit: int = 50):
    """
    Get maintenance logbook entries.
    
    Optional filters:
    - equipment_id: Filter by specific equipment
    - limit: Maximum number of entries (default 50)
    """
    try:
        entries = get_all_entries(equipment_id=equipment_id, limit=limit)
        return {"entries": entries, "count": len(entries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logbook: {str(e)}")


@router.get("/logbook/{entry_id}")
async def get_logbook_entry(entry_id: str):
    """Get a specific logbook entry by ID."""
    try:
        entry = get_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Logbook entry not found")
        
        # Include feedback if any
        feedback_list = get_feedback_for_entry(entry_id)
        entry["feedback"] = feedback_list
        
        return entry
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve entry: {str(e)}")


@router.post("/logbook/{entry_id}/resolve")
async def resolve_entry(entry_id: str, technician: str = "Unknown"):
    """Mark a logbook entry as resolved."""
    try:
        mark_resolved(entry_id, technician)
        return {"success": True, "entry_id": entry_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark resolved: {str(e)}")


@router.get("/reports")
async def get_reports(equipment_id: str = None, limit: int = 50):
    """
    Get all analysis reports.
    
    Optional filters:
    - equipment_id: Filter by specific equipment
    - limit: Maximum number of reports (default 50)
    """
    try:
        reports = get_all_reports(equipment_id=equipment_id, limit=limit)
        return {"reports": reports, "count": len(reports)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reports: {str(e)}")


@router.get("/reports/{report_id}")
async def get_report_by_id(report_id: str):
    """Get a specific report by ID."""
    try:
        report = get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {str(e)}")


@router.post("/reports/generate/{incident_id}")
async def generate_report_for_incident(incident_id: str, logbook_entry_id: str):
    """Generate a formal report from an incident and logbook entry."""
    try:
        report = generate_report(incident_id, logbook_entry_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/feedback/stats")
async def get_stats():
    """Get overall feedback statistics (accuracy metrics)."""
    try:
        stats = get_feedback_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")
