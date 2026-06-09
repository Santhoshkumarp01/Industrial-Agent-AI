"""
Prepare training data for Phi-3.5 Mini fine-tuning.

Steps:
1. Load friend's data (JSONL format with 3 fields: instruction + input + output)
2. Load generated data (JSON format with 2 fields: instruction + response)
3. Normalize all to common format
4. Quality filter
5. Deduplicate
6. Split 90/10 train/eval
7. Save processed datasets
"""

import json
import random
from pathlib import Path

print("=" * 60)
print("PREPARING TRAINING DATA")
print("=" * 60)

# ============================================================================
# LOAD DATA
# ============================================================================
print("\n→ Loading friend's data...")
friend_data = []
try:
    with open("data/training/raw/friend_data.jsonl", "r") as f:
        for line in f:
            if line.strip():
                friend_data.append(json.loads(line))
    print(f"  ✓ Loaded {len(friend_data)} examples from friend's dataset")
except Exception as e:
    print(f"  ✗ Error loading friend's data: {e}")
    friend_data = []

print("\n→ Loading generated data...")
try:
    with open("data/training/raw/generated_pairs.json", "r") as f:
        generated_data = json.load(f)
    print(f"  ✓ Loaded {len(generated_data)} examples from generated dataset")
except Exception as e:
    print(f"  ✗ Error loading generated data: {e}")
    generated_data = []

total_before = len(friend_data) + len(generated_data)
print(f"\nTotal examples before processing: {total_before}")


# ============================================================================
# NORMALIZE FORMAT
# ============================================================================
print("\n→ Normalizing formats...")

def normalize(example):
    """
    Normalize different data formats to common structure.
    
    Handles:
    - 3-field format: instruction + input + output (friend's data)
    - 2-field format: instruction + response (generated data)
    - Alternative key names: question, prompt, answer, completion
    """
    # Handle 3-field format (instruction + input + output)
    if "input" in example and example.get("input"):
        # Combine instruction + input into single instruction
        instruction = f"{example.get('instruction', '')}\n\n{example['input']}"
        response = example.get("output", "")
    else:
        # Handle 2-field format
        instruction = (
            example.get("instruction") or
            example.get("question") or
            example.get("prompt") or ""
        )
        response = (
            example.get("response") or
            example.get("answer") or
            example.get("output") or
            example.get("completion") or ""
        )
    
    return {
        "instruction": instruction.strip(),
        "response": response.strip()
    }

all_data = [normalize(e) for e in friend_data + generated_data]
print(f"  ✓ Normalized {len(all_data)} examples")


# ============================================================================
# QUALITY FILTERING
# ============================================================================
print("\n→ Applying quality filters...")

def is_good_quality(example):
    """
    Filter out low-quality examples.
    
    Criteria:
    - Both fields must be non-empty
    - Instruction must have at least 5 words
    - Response must have at least 10 words
    - Combined length must not exceed 600 words (context window limit)
    - Response must not be weak/uncertain
    """
    instruction = example["instruction"]
    response = example["response"]
    
    # Remove empty
    if not instruction or not response:
        return False
    
    # Remove too short
    if len(instruction.split()) < 5:
        return False
    if len(response.split()) < 10:
        return False
    
    # Remove too long (will exceed context window)
    if len(instruction.split()) + len(response.split()) > 600:
        return False
    
    # Remove weak responses
    weak_responses = [
        "i don't know",
        "i cannot",
        "i am unable",
        "not sure",
        "i'm not sure",
        "cannot provide",
        "unable to"
    ]
    response_lower = response.lower()
    if any(w in response_lower for w in weak_responses):
        return False
    
    return True

filtered = [e for e in all_data if is_good_quality(e)]
print(f"  ✓ Quality filter: {len(all_data)} → {len(filtered)} examples")
print(f"    Removed: {len(all_data) - len(filtered)} low-quality examples")


# ============================================================================
# DEDUPLICATION
# ============================================================================
print("\n→ Deduplicating...")

seen_instructions = set()
deduplicated = []

for example in filtered:
    # Use full instruction + first 50 chars of response as fingerprint
    # This prevents over-aggressive deduplication when instructions have same prefix
    key = (example["instruction"] + " ||| " + example["response"][:50]).lower().strip()
    
    if key not in seen_instructions:
        seen_instructions.add(key)
        deduplicated.append(example)

print(f"  ✓ Deduplication: {len(filtered)} → {len(deduplicated)} examples")
print(f"    Removed: {len(filtered) - len(deduplicated)} duplicates")


# ============================================================================
# SHUFFLE AND SPLIT
# ============================================================================
print("\n→ Splitting train/eval...")

random.seed(42)  # Reproducible splits
random.shuffle(deduplicated)

split_idx = int(len(deduplicated) * 0.9)
train_data = deduplicated[:split_idx]
eval_data = deduplicated[split_idx:]

print(f"  ✓ Train: {len(train_data)} examples (90%)")
print(f"  ✓ Eval:  {len(eval_data)} examples (10%)")


# ============================================================================
# SAVE PROCESSED DATA
# ============================================================================
print("\n→ Saving processed datasets...")

output_dir = Path("data/training/processed")
output_dir.mkdir(parents=True, exist_ok=True)

# Save combined dataset
with open(output_dir / "combined_dataset.json", "w") as f:
    json.dump(deduplicated, f, indent=2)

# Save train split
with open(output_dir / "train_split.json", "w") as f:
    json.dump(train_data, f, indent=2)

# Save eval split
with open(output_dir / "eval_split.json", "w") as f:
    json.dump(eval_data, f, indent=2)

print(f"  ✓ Saved to data/training/processed/")


# ============================================================================
# SUMMARY
# ============================================================================
print(f"\n{'=' * 60}")
print(f"DATA PREPARATION COMPLETE")
print(f"{'=' * 60}")
print(f"\nDataset Statistics:")
print(f"  Original:     {total_before:,} examples")
print(f"  After filter: {len(filtered):,} examples")
print(f"  Final:        {len(deduplicated):,} examples")
print(f"  Train split:  {len(train_data):,} examples")
print(f"  Eval split:   {len(eval_data):,} examples")
print(f"\nQuality metrics:")
print(f"  Retention rate: {len(deduplicated) / total_before * 100:.1f}%")
print(f"  Avg instruction length: {sum(len(e['instruction'].split()) for e in deduplicated) / len(deduplicated):.1f} words")
print(f"  Avg response length: {sum(len(e['response'].split()) for e in deduplicated) / len(deduplicated):.1f} words")

print(f"\n✓ Ready for fine-tuning!")
print(f"✓ Next step: python ml/finetune_phi35.py")
