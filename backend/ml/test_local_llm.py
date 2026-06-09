"""
Test local fine-tuned Phi-3.5 Mini model.
Verifies the model works standalone before integrating with agents.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.local_llm import generate

# Test prompt - maintenance scenario
response = generate(
    system_prompt="You are an expert maintenance engineer for steel plant equipment.",
    user_prompt="""Equipment alert: Rolling Mill #3 showing abnormal operation.

Equipment: Rolling Mill #3
Sensors:
- Vibration: 9.2 mm/s (baseline: 4.5 mm/s)
- Temperature: 96°C (baseline: 75°C)
- Current: 58A (baseline: 45A)  
- Pressure: 3.1 bar (baseline: 3.5 bar)

Diagnose the fault and provide immediate actions.""",
    max_tokens=800
)

print("=" * 80)
print("FINE-TUNED MODEL RESPONSE")
print("=" * 80)
print(response)
print("=" * 80)
