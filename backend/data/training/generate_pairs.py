"""
Generate training Q&A pairs from local knowledge sources.

Strategies:
1. Incidents.json → 8 pairs per incident (320 total)
2. SOPs → 15-20 pairs per SOP (80 total)
3. Spare parts CSV → 5 pairs per part (150 total)
4. Sensor thresholds → 96 pairs (programmatic)
5. Multi-turn diagnostics → 50 pairs (Gemini-assisted)
6. Prioritization scenarios → 60 pairs (Gemini-assisted)

Total target: ~750 pairs
"""

import json
import csv
import os
import time
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment")

client = genai.Client(api_key=GOOGLE_API_KEY)

OUTPUT_PATH = Path("data/training/raw/generated_pairs.json")
all_pairs = []

print("=" * 60)
print("GENERATING TRAINING PAIRS FROM LOCAL SOURCES")
print("=" * 60)


# ============================================================================
# STRATEGY 1: FROM INCIDENTS.JSON (320 PAIRS)
# ============================================================================
print("\n→ Strategy 1: Generating from incidents.json...")

INCIDENT_TEMPLATES = [
    ("What caused the {equipment} failure recorded in incident {incident_id}?",
     "Incident {incident_id} ({date}) on {equipment} was caused by {root_cause}. {details}"),
    
    ("What were the sensor symptoms before the {equipment} failure in {incident_id}?",
     "Before the {equipment} failure in {incident_id}, sensors showed: vibration {vibration} mm/s, temperature {temperature}°C. {details}"),
    
    ("What immediate actions were taken for incident {incident_id} on {equipment}?",
     "For incident {incident_id}, immediate actions included: {action_taken}. Downtime: {downtime} hours."),
    
    ("How long was the downtime for {equipment} in incident {incident_id} and why?",
     "{equipment} in incident {incident_id} had {downtime} hours downtime due to {root_cause}. Production loss: {production_loss} tonnes."),
    
    ("What spare parts were used to fix {equipment} in incident {incident_id}?",
     "Incident {incident_id} on {equipment} required: {parts_used}. Root cause: {root_cause}."),
    
    ("What preventive measures were recommended after incident {incident_id}?",
     "After incident {incident_id}, preventive measures recommended: {recurrence_prevention}"),
    
    ("If {equipment} shows vibration {vibration} mm/s and temperature {temperature}°C, what does this indicate?",
     "Vibration {vibration} mm/s and temperature {temperature}°C on {equipment} indicates potential {root_cause}, as seen in incident {incident_id}. Monitor closely and {action_taken}."),
    
    ("What is the estimated production loss from a {downtime}-hour downtime on {equipment}?",
     "A {downtime}-hour downtime on {equipment} results in approximately {production_loss} tonnes production loss, as documented in incident {incident_id}."),
]

try:
    with open("data/knowledge/incidents.json", "r") as f:
        incidents = json.load(f)
    
    for incident in incidents:
        for q_template, a_template in INCIDENT_TEMPLATES:
            question = q_template.format(**incident)
            answer = a_template.format(**incident)
            all_pairs.append({
                "instruction": question,
                "response": answer
            })
    
    print(f"  ✓ Generated {len(INCIDENT_TEMPLATES) * len(incidents)} incident pairs")
except Exception as e:
    print(f"  ✗ Error loading incidents: {e}")


# ============================================================================
# STRATEGY 2: FROM SOPs (80 PAIRS)
# ============================================================================
print("\n→ Strategy 2: Generating from SOPs...")

SOP_DIR = Path("data/knowledge/sops")
sop_files = list(SOP_DIR.glob("*.txt"))

for sop_file in sop_files:
    try:
        with open(sop_file, "r") as f:
            sop_content = f.read()
        
        # Extract procedure name from filename
        procedure_name = sop_file.stem.replace("_", " ").title()
        
        # Use Gemini to extract Q&A pairs from SOP
        prompt = f"""Extract 15 specific Q&A pairs from this maintenance SOP. Focus on:
- Required tools and equipment
- Safety precautions
- Step-by-step procedures
- Torque specifications
- Acceptance criteria
- Troubleshooting steps

SOP: {procedure_name}
Content:
{sop_content[:2000]}

Output ONLY a JSON array with 'instruction' and 'response' fields. Make responses detailed and specific."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=2048,
                temperature=0.3,
            )
        )
        
        # Parse JSON response
        text = response.text.strip()
        # Remove markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        sop_pairs = json.loads(text)
        all_pairs.extend(sop_pairs[:15])  # Limit to 15 per SOP
        print(f"  ✓ {sop_file.name}: {len(sop_pairs[:15])} pairs")
        
        time.sleep(1)  # Rate limit
        
    except Exception as e:
        print(f"  ✗ Error processing {sop_file.name}: {e}")


# ============================================================================
# STRATEGY 3: FROM SPARE PARTS CSV (150 PAIRS)
# ============================================================================
print("\n→ Strategy 3: Generating from spare_parts.csv...")

PARTS_TEMPLATES = [
    ("What bearing is used on {compatible_equipment}?",
     "The {description} (part number {part_number}) is used on {compatible_equipment}. Currently {quantity_in_stock} units in stock at {location}."),
    
    ("What is the procurement lead time for {part_number}?",
     "{part_number} ({description}) has a lead time of {lead_time_days} days. Current stock: {quantity_in_stock} units. Supplier: {supplier}."),
    
    ("Is {part_number} available in stock?",
     "{part_number} ({description}): Stock level {quantity_in_stock} units at {location}. Lead time if ordering: {lead_time_days} days from {supplier}."),
    
    ("What is the cost of {description}?",
     "The {description} (part number {part_number}) costs ₹{cost_per_unit} per unit. Supplier: {supplier}. Lead time: {lead_time_days} days."),
    
    ("Where is {part_number} stored in the warehouse?",
     "{part_number} ({description}) is stored at {location}. Current stock: {quantity_in_stock} units. Used for: {compatible_equipment}."),
]

try:
    with open("data/knowledge/spare_parts.csv", "r") as f:
        reader = csv.DictReader(f)
        parts = list(reader)
    
    for part in parts:
        for q_template, a_template in PARTS_TEMPLATES:
            question = q_template.format(**part)
            answer = a_template.format(**part)
            all_pairs.append({
                "instruction": question,
                "response": answer
            })
    
    print(f"  ✓ Generated {len(PARTS_TEMPLATES) * len(parts)} parts pairs")
except Exception as e:
    print(f"  ✗ Error loading spare parts: {e}")


# ============================================================================
# STRATEGY 4: SENSOR THRESHOLDS (96 PAIRS)
# ============================================================================
print("\n→ Strategy 4: Generating sensor threshold pairs...")

EQUIPMENT_THRESHOLDS = {
    "Rolling Mill #1": {
        "vibration":   {"normal": (1.5, 3.0),  "warning": (3.0, 6.0),  "critical": (6.0, 10.0), "unit": "mm/s"},
        "temperature": {"normal": (65, 78),     "warning": (78, 90),    "critical": (90, 110),    "unit": "°C"},
        "current":     {"normal": (38, 46),     "warning": (46, 55),    "critical": (55, 70),     "unit": "A"},
        "pressure":    {"normal": (4.2, 5.1),   "warning": (3.0, 4.2),  "critical": (1.0, 3.0),   "unit": "bar"},
    },
    "Rolling Mill #3": {
        "vibration":   {"normal": (1.8, 3.2),  "warning": (3.2, 6.5),  "critical": (6.5, 10.0), "unit": "mm/s"},
        "temperature": {"normal": (68, 80),     "warning": (80, 95),    "critical": (95, 115),    "unit": "°C"},
        "current":     {"normal": (40, 48),     "warning": (48, 58),    "critical": (58, 72),     "unit": "A"},
        "pressure":    {"normal": (4.0, 5.0),   "warning": (3.0, 4.0),  "critical": (1.0, 3.0),   "unit": "bar"},
    },
    "BF Blower #1": {
        "vibration":   {"normal": (0.8, 2.0),  "warning": (2.0, 4.5),  "critical": (4.5, 8.0),  "unit": "mm/s"},
        "temperature": {"normal": (55, 70),     "warning": (70, 85),    "critical": (85, 100),    "unit": "°C"},
        "current":     {"normal": (52, 62),     "warning": (62, 72),    "critical": (72, 85),     "unit": "A"},
        "pressure":    {"normal": (6.1, 7.4),   "warning": (4.5, 6.1),  "critical": (2.0, 4.5),   "unit": "bar"},
    },
    "Compressor A": {
        "vibration":   {"normal": (1.2, 2.8),  "warning": (2.8, 5.5),  "critical": (5.5, 9.5),  "unit": "mm/s"},
        "temperature": {"normal": (72, 88),     "warning": (88, 105),   "critical": (105, 125),   "unit": "°C"},
        "current":     {"normal": (28, 36),     "warning": (36, 44),    "critical": (44, 55),     "unit": "A"},
        "pressure":    {"normal": (8.5, 10.2),  "warning": (6.0, 8.5),  "critical": (3.0, 6.0),   "unit": "bar"},
    },
}

threshold_count = 0
for equipment, sensors in EQUIPMENT_THRESHOLDS.items():
    for sensor, thresholds in sensors.items():
        unit = thresholds["unit"]
        
        # Generate pairs for each threshold level
        for level in ["normal", "warning", "critical"]:
            low, high = thresholds[level]
            value = (low + high) / 2  # midpoint
            
            # Question 1: What does this reading mean?
            all_pairs.append({
                "instruction": f"What does {sensor} reading of {value} {unit} mean on {equipment}?",
                "response": f"{sensor.title()} reading of {value} {unit} on {equipment} is in the {level.upper()} range ({low}-{high} {unit}). {'Normal operation.' if level == 'normal' else 'WARNING: Monitor closely and plan intervention.' if level == 'warning' else 'CRITICAL: Immediate action required to prevent failure.'}"
            })
            
            # Question 2: What action should be taken?
            action_map = {
                "normal": "Continue normal operation. Monitor trends.",
                "warning": "Increase monitoring frequency. Plan maintenance intervention within 24-48 hours. Reduce load if possible.",
                "critical": "IMMEDIATE ACTION: Reduce equipment speed by 40%. Initiate emergency maintenance protocol. Prepare for controlled shutdown."
            }
            
            all_pairs.append({
                "instruction": f"What action should be taken when {equipment} {sensor} reaches {value} {unit}?",
                "response": f"{equipment} {sensor} at {value} {unit} is {level.upper()} (threshold: {low}-{high} {unit}). Action: {action_map[level]}"
            })
            
            threshold_count += 2

print(f"  ✓ Generated {threshold_count} threshold pairs")


# ============================================================================
# STRATEGY 5: MULTI-TURN DIAGNOSTICS (50 PAIRS)
# ============================================================================
print("\n→ Strategy 5: Generating multi-turn diagnostic conversations...")

MULTITURN_PROMPT = """Generate 10 realistic multi-turn maintenance diagnostic conversations for a steel plant.

Format: Each conversation shows an engineer describing symptoms over 2-3 exchanges, and the AI providing increasingly refined diagnosis.

Combine into single Q&A pairs where:
- instruction = the full conversation history as context + final question
- response = the final comprehensive diagnosis with specific actions

Equipment: Rolling Mill #1, Rolling Mill #3, BF Blower #1, Compressor A
Include: realistic sensor readings, part numbers (SKF bearings, etc.), specific torque values, warehouse locations

Output ONLY valid JSON array with 'instruction' and 'response' fields."""

multiturn_count = 0
for batch in range(5):  # 5 batches × 10 = 50 pairs
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=MULTITURN_PROMPT,
            config=types.GenerateContentConfig(
                max_output_tokens=3000,
                temperature=0.8,
            )
        )
        
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        pairs = json.loads(text)
        all_pairs.extend(pairs[:10])
        multiturn_count += len(pairs[:10])
        print(f"  Batch {batch + 1}: {len(pairs[:10])} pairs")
        
        time.sleep(2)  # Rate limit
        
    except Exception as e:
        print(f"  ✗ Batch {batch + 1} failed: {e}")

print(f"  ✓ Generated {multiturn_count} multi-turn pairs")


# ============================================================================
# STRATEGY 6: PRIORITIZATION SCENARIOS (60 PAIRS)
# ============================================================================
print("\n→ Strategy 6: Generating prioritization scenarios...")

PRIORITY_PROMPT = """Generate 10 Q&A pairs about maintenance prioritization in a steel plant.

Scenario: Multiple equipment have issues simultaneously. Engineer must prioritize based on:
- Production criticality (which equipment failure stops production?)
- Anomaly severity (CRITICAL > HIGH > MEDIUM)
- Spare parts availability
- Estimated time to failure
- Safety risk

Include realistic sensor readings, specific equipment names, risk levels, and detailed justification for prioritization.

Output ONLY valid JSON array with 'instruction' and 'response' fields."""

priority_count = 0
for batch in range(6):  # 6 batches × 10 = 60 pairs
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=PRIORITY_PROMPT,
            config=types.GenerateContentConfig(
                max_output_tokens=2048,
                temperature=0.7,
            )
        )
        
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        pairs = json.loads(text)
        all_pairs.extend(pairs[:10])
        priority_count += len(pairs[:10])
        print(f"  Batch {batch + 1}: {len(pairs[:10])} pairs")
        
        time.sleep(2)  # Rate limit
        
    except Exception as e:
        print(f"  ✗ Batch {batch + 1} failed: {e}")

print(f"  ✓ Generated {priority_count} prioritization pairs")


# ============================================================================
# SAVE OUTPUT
# ============================================================================
print(f"\n{'=' * 60}")
print(f"GENERATION COMPLETE")
print(f"{'=' * 60}")
print(f"Total pairs generated: {len(all_pairs)}")
print(f"Saving to: {OUTPUT_PATH}")

with open(OUTPUT_PATH, "w") as f:
    json.dump(all_pairs, f, indent=2)

print(f"\n✓ Saved {len(all_pairs)} training pairs")
print(f"✓ Next step: python ml/prepare_data.py")
