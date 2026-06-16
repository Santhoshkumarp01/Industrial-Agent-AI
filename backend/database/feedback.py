"""
Engineer feedback storage.

When engineer marks a recommendation as confirmed/incorrect, that feedback
is stored and used to improve future retrieval.
"""

import uuid
from datetime import datetime
from database.db import get_connection
from models.schemas import FeedbackCreate


def store_feedback(feedback: FeedbackCreate) -> str:
    """Store engineer feedback on a logbook entry."""
    feedback_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO feedback (
                id, logbook_entry_id, engineer_name, verdict,
                actual_root_cause, actual_action_taken,
                outcome, downtime_hours, feedback_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback_id,
            feedback.logbook_entry_id,
            feedback.engineer_name,
            feedback.verdict,
            feedback.actual_root_cause,
            feedback.actual_action_taken,
            feedback.outcome,
            feedback.downtime_hours,
            now
        ))

    # If verdict is 'incorrect', store the correction as a new knowledge entry
    # This goes back into Qdrant so future retrievals improve
    if feedback.verdict == "incorrect" and feedback.actual_root_cause:
        _store_correction_as_knowledge(feedback, feedback_id)

    return feedback_id


def _store_correction_as_knowledge(feedback: FeedbackCreate, feedback_id: str):
    """
    When engineer corrects the AI, store the correction as a new
    incident record in Qdrant so future similar queries find it.
    This is the feedback-driven improvement loop.
    """
    from ingestion.ingestor import ingest_text_chunk
    correction_text = (
        f"Engineer Correction (Feedback ID: {feedback_id}): "
        f"AI recommendation was incorrect. "
        f"Actual root cause: {feedback.actual_root_cause}. "
        f"Actual action taken: {feedback.actual_action_taken}. "
        f"Outcome: {feedback.outcome}."
    )
    # Store this correction text as a new chunk in Qdrant
    # Tagged as 'feedback_correction' block type
    try:
        ingest_text_chunk(
            text=correction_text,
            doc_name=f"Engineer Correction {feedback_id[:8]}",
            equipment_tag="General",
            block_type="feedback_correction",
            source="engineer_feedback"
        )
        print(f"✓ Correction stored in Qdrant for future learning")
    except Exception as e:
        print(f"⚠ Could not store correction in Qdrant: {e}")


def get_feedback_for_entry(logbook_entry_id: str) -> list[dict]:
    """Get all feedback for a specific logbook entry."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM feedback
            WHERE logbook_entry_id = ?
            ORDER BY feedback_timestamp DESC
        """, (logbook_entry_id,)).fetchall()
    return [dict(row) for row in rows]


def get_feedback_stats() -> dict:
    """Overall accuracy stats — what % of recommendations were confirmed."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        confirmed = conn.execute(
            "SELECT COUNT(*) FROM feedback WHERE verdict = 'confirmed'"
        ).fetchone()[0]
        incorrect = conn.execute(
            "SELECT COUNT(*) FROM feedback WHERE verdict = 'incorrect'"
        ).fetchone()[0]

    return {
        "total_feedback": total,
        "confirmed": confirmed,
        "incorrect": incorrect,
        "accuracy_percent": round((confirmed / total * 100) if total > 0 else 0, 1)
    }


def store_chat_feedback(
    session_id: str,
    message_id: str,
    query: str,
    answer: str,
    verdict: str,  # "positive" or "negative"
) -> str:
    """
    Store engineer feedback on chat assistant answers.
    
    Args:
        session_id: Chat session identifier
        message_id: Unique message identifier (timestamp-based)
        query: Engineer's question
        answer: AI's answer that was rated
        verdict: "positive" or "negative"
    
    Returns:
        feedback_id: UUID of stored feedback
    """
    feedback_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    with get_connection() as conn:
        # Create chat_feedback table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_feedback (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                query TEXT NOT NULL,
                answer TEXT NOT NULL,
                verdict TEXT NOT NULL,
                feedback_timestamp TEXT NOT NULL
            )
        """)
        
        conn.execute("""
            INSERT INTO chat_feedback (
                id, session_id, message_id, query, answer, verdict, feedback_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback_id,
            session_id,
            message_id,
            query,
            answer,
            verdict,
            now
        ))

    # TODO: For negative feedback, could reinject corrected answers into Qdrant
    # Similar to _store_correction_as_knowledge() but for chat Q&A
    
    return feedback_id
