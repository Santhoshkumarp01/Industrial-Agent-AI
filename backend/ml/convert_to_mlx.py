"""
Convert processed training data to MLX format.

MLX fine-tuning expects:
- data/training/mlx/train.jsonl (JSONL with "text" field)
- data/training/mlx/valid.jsonl (JSONL with "text" field)

Each line should be a single JSON object with the formatted prompt.
"""

import json
from pathlib import Path

# Paths
TRAIN_INPUT = "data/training/processed/train_split.json"
EVAL_INPUT = "data/training/processed/eval_split.json"
OUTPUT_DIR = Path("data/training/mlx")
TRAIN_OUTPUT = OUTPUT_DIR / "train.jsonl"
VALID_OUTPUT = OUTPUT_DIR / "valid.jsonl"

# System message for Phi-3.5
SYSTEM_MESSAGE = """You are an expert AI maintenance engineer specializing in steel plant equipment including Rolling Mills, Blast Furnace Blowers, Compressors, and Conveyor Motors. You provide specific, actionable maintenance guidance with exact part numbers, torque specifications, safety procedures, and step-by-step repair instructions based on maintenance SOPs, historical incident records, and sensor data analysis."""

def format_for_phi35(instruction: str, response: str) -> str:
    """Format instruction-response pair into Phi-3.5 chat template."""
    return (
        f"<|system|>\n{SYSTEM_MESSAGE}<|end|>\n"
        f"<|user|>\n{instruction}<|end|>\n"
        f"<|assistant|>\n{response}<|end|>"
    )

def convert_to_mlx_jsonl(input_path: str, output_path: Path):
    """Convert JSON array to JSONL with formatted text."""
    with open(input_path) as f:
        data = json.load(f)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        for example in data:
            formatted = {
                "text": format_for_phi35(
                    example["instruction"],
                    example["response"]
                )
            }
            f.write(json.dumps(formatted) + "\n")
    
    return len(data)

if __name__ == "__main__":
    print("=" * 60)
    print("Converting Training Data to MLX Format")
    print("=" * 60)
    
    print(f"\n→ Converting training data...")
    train_count = convert_to_mlx_jsonl(TRAIN_INPUT, TRAIN_OUTPUT)
    print(f"  ✓ {train_count} examples → {TRAIN_OUTPUT}")
    
    print(f"\n→ Converting validation data...")
    valid_count = convert_to_mlx_jsonl(EVAL_INPUT, VALID_OUTPUT)
    print(f"  ✓ {valid_count} examples → {VALID_OUTPUT}")
    
    print(f"\n✓ MLX data ready!")
    print(f"\nNext: Run MLX fine-tuning:")
    print(f"  cd /Users/user1-ak/Documents/Industrial\\ Agent\\ AI/backend")
    print(f"  python -m mlx_lm.lora \\")
    print(f"    --model ml/base_models/phi35_mini \\")
    print(f"    --train \\")
    print(f"    --data data/training/mlx \\")
    print(f"    --iters 600 \\")
    print(f"    --batch-size 4 \\")
    print(f"    --lora-layers 16 \\")
    print(f"    --save-every 100 \\")
    print(f"    --adapter-path ml/saved_models/phi35_mlx_lora")
    print("=" * 60)
