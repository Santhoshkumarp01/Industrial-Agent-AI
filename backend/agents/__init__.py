"""
Multi-agent orchestrator for industrial maintenance decision support.

Three specialized agents:
1. Root Cause Agent — searches RAG + incident history → diagnosis
2. Risk Agent — scores urgency + checks spare parts availability
3. Maintenance Agent — generates step-by-step work order

Coordinated by orchestrator that routes input → calls agents → combines output.
"""
