"""
Compare base vs fine-tuned Phi-3.5 Mini using MLX.

Usage: python ml/test_mlx_phi35.py
"""

from mlx_lm import load, generate

# System message
SYSTEM_MESSAGE = """You are an expert AI maintenance engineer specializing in steel plant equipment including Rolling Mills, Blast Furnace Blowers, Compressors, and Conveyor Motors. You provide specific, actionable maintenance guidance with exact part numbers, torque specifications, safety procedures, and step-by-step repair instructions based on maintenance SOPs, historical incident records, and sensor data analysis."""

# Test cases
TEST_CASES = [
    {
        "title": "Compressor Cooling System Failure",
        "prompt": """Equipment alert: Compressor showing abnormal operation. Analyze the sensor data and provide maintenance diagnosis.

Equipment: Compressor | Type: L-grade
Sensors:
- Air Temperature: 29.2°C (baseline: 25°C)
- Process Temperature: 37.8°C (baseline: 35°C)
- Rotational Speed: 1377 RPM (baseline: 1500 RPM)
- Torque: 46.8 Nm (baseline: 40 Nm)
- Operating Time Since Maintenance: 166 minutes
Alert Code: HDF-091"""
    },
    {
        "title": "Predictive Maintenance - Air Compressor",
        "prompt": """Analyze equipment degradation pattern and predict maintenance requirements for Air Compressor Unit.

Equipment: Air Compressor Unit | ID: Air-Compressor-Unit-230
Operating Hours: 1,248 hours

Current Sensor Readings:
- Discharge Temperature: 104.5°C (baseline: 85.0°C, delta: +19.5°C)
- Discharge Pressure: 8.51 bar (baseline: 8.5 bar)
- Compressor Speed: 3200 RPM (rated: 3500 RPM)
- Vibration Level: 75.0 Hz (baseline: 80.0 Hz)
- Operating Efficiency: 109.68% (baseline: 100.0%)

Trend: Progressive degradation over past 30 days
Alert: Predictive maintenance recommended"""
    }
]

def format_prompt(user_message: str) -> str:
    """Format into Phi-3.5 chat template."""
    return (
        f"<|system|>\n{SYSTEM_MESSAGE}<|end|>\n"
        f"<|user|>\n{user_message}<|end|>\n"
        f"<|assistant|>\n"
    )

def run_comparison():
    """Compare base vs fine-tuned model responses."""
    
    print("=" * 80)
    print("PHI-3.5 MINI — BASE vs FINE-TUNED COMPARISON (MLX)")
    print("=" * 80)
    
    # Load base model
    print("\n→ Loading BASE model...")
    base_model, base_tokenizer = load("ml/base_models/phi35_mini")
    print("  ✓ Base model loaded")
    
    # Load fine-tuned model
    print("\n→ Loading FINE-TUNED model...")
    finetuned_model, finetuned_tokenizer = load(
        "ml/base_models/phi35_mini",
        adapter_path="ml/saved_models/phi35_mlx_lora"
    )
    print("  ✓ Fine-tuned model loaded (with LoRA adapter)")
    
    # Run test cases
    for i, test_case in enumerate(TEST_CASES, 1):
        print("\n" + "=" * 80)
        print(f"TEST CASE {i}: {test_case['title']}")
        print("=" * 80)
        
        prompt = format_prompt(test_case['prompt'])
        
        # Base model response
        print("\n--- BASE MODEL RESPONSE ---")
        response_base = generate(
            base_model,
            base_tokenizer,
            prompt=prompt,
            max_tokens=400,
            verbose=False
        )
        print(response_base)
        
        # Fine-tuned model response
        print("\n--- FINE-TUNED MODEL RESPONSE ---")
        response_finetuned = generate(
            finetuned_model,
            finetuned_tokenizer,
            prompt=prompt,
            max_tokens=400,
            verbose=False
        )
        print(response_finetuned)
        
        print("\n" + "-" * 80)
    
    print("\n" + "=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)
    print("""
Expected Results:
  - BASE model: Generic or vague maintenance advice
  - FINE-TUNED model: Specific diagnosis with risk levels, root cause analysis,
    confidence scores, immediate actions, spare parts, and manual references

If fine-tuned model shows significant improvement, enable in production:
  1. Set USE_LOCAL_MODEL=true in .env
  2. Restart backend
  3. Test via API
""")

if __name__ == "__main__":
    try:
        run_comparison()
    except FileNotFoundError as e:
        print("\n❌ ERROR: Fine-tuned model not found!")
        print(f"   {e}")
        print("\n   Run MLX fine-tuning first:")
        print("   python -m mlx_lm.lora --model ml/base_models/phi35_mini \\")
        print("     --train --data data/training/mlx \\")
        print("     --iters 600 --batch-size 4 --lora-layers 16 \\")
        print("     --adapter-path ml/saved_models/phi35_mlx_lora")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
