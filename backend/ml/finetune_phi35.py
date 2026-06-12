"""
Fine-tune Phi-3.5 Mini Instruct on maintenance Q&A data using LoRA.

Model: microsoft/Phi-3.5-mini-instruct (3.8B parameters)
Technique: LoRA (Low-Rank Adaptation) - trains only ~0.52% of parameters
Data: data/training/processed/train_split.json
Output: ml/saved_models/phi35_maintenance_lora/

Run: python ml/finetune_phi35.py
Time: 1-2 hours on MacBook Pro M-series
RAM: ~14GB during training
"""

import torch
import json
from pathlib import Path
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer, SFTConfig

print("=" * 60)
print("INDUSTRIAL AGENT AI — Phi-3.5 Mini Fine-tuning")
print("=" * 60)

# ============================================================================
# PATHS
# ============================================================================
BASE_MODEL_PATH = "ml/base_models/phi35_mini"
OUTPUT_DIR = "ml/saved_models/phi35_maintenance_lora"
TRAIN_DATA_PATH = "data/training/processed/train_split.json"
EVAL_DATA_PATH = "data/training/processed/eval_split.json"

# ============================================================================
# LOAD DATA
# ============================================================================
print("\n→ Loading training data...")
with open(TRAIN_DATA_PATH) as f:
    train_pairs = json.load(f)
with open(EVAL_DATA_PATH) as f:
    eval_pairs = json.load(f)

print(f"  Train: {len(train_pairs)} examples")
print(f"  Eval:  {len(eval_pairs)} examples")

# ============================================================================
# FORMAT FOR PHI-3.5 CHAT TEMPLATE
# ============================================================================
SYSTEM_MESSAGE = """You are an expert AI maintenance engineer specializing in steel plant equipment including Rolling Mills, Blast Furnace Blowers, Compressors, and Conveyor Motors. You provide specific, actionable maintenance guidance with exact part numbers, torque specifications, safety procedures, and step-by-step repair instructions based on maintenance SOPs, historical incident records, and sensor data analysis."""

def format_for_phi35(example):
    """Format Q&A pair into Phi-3.5 chat template."""
    text = (
        f"<|system|>\n{SYSTEM_MESSAGE}<|end|>\n"
        f"<|user|>\n{example['instruction']}<|end|>\n"
        f"<|assistant|>\n{example['response']}<|end|>"
    )
    return {"text": text}

print("\n→ Formatting for Phi-3.5 chat template...")
train_dataset = Dataset.from_list(train_pairs).map(format_for_phi35)
eval_dataset = Dataset.from_list(eval_pairs).map(format_for_phi35)
print(f"  ✓ Formatted {len(train_dataset)} train examples")
print(f"  ✓ Formatted {len(eval_dataset)} eval examples")

# ============================================================================
# LOAD TOKENIZER
# ============================================================================
print(f"\n→ Loading tokenizer from {BASE_MODEL_PATH}...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"
print(f"  ✓ Tokenizer loaded")

# ============================================================================
# LOAD MODEL — MPS COMPATIBLE
# ============================================================================
print(f"\n→ Loading Phi-3.5 Mini on Apple MPS...")

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_PATH,
    torch_dtype=torch.float32,       # float32, NOT float16 (MPS incompatible)
    device_map={"": "mps"},          # explicit MPS, not "auto"
    trust_remote_code=True,
    attn_implementation="eager"      # required for MPS
)

print(f"  ✓ Model loaded on: {next(model.parameters()).device}")

# ============================================================================
# APPLY LORA — PHI-3.5 VERIFIED LAYER NAMES
# ============================================================================
print("\n→ Applying LoRA adapters...")

lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=[
        "qkv_proj",      # Phi-3.5 uses combined QKV projection
        "o_proj",
        "gate_up_proj",  # Phi-3.5 MLP gate+up projection
        "down_proj",     # Phi-3.5 MLP down projection
    ],
    bias="none",
)

model = get_peft_model(model, lora_config)
print(f"\n  LoRA Configuration:")
print(f"    Rank: {lora_config.r}")
print(f"    Alpha: {lora_config.lora_alpha}")
print(f"    Dropout: {lora_config.lora_dropout}")
print(f"    Target modules: {', '.join(lora_config.target_modules)}")

model.print_trainable_parameters()

# ============================================================================
# SFTCONFIG — REPLACES TRAININGARGUMENTS IN TRL >= 0.9
# ============================================================================
print("\n→ Setting up training...")

training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    fp16=False,                      # DISABLED — MPS crashes with fp16
    bf16=False,                      # DISABLED — not supported on MPS
    logging_steps=10,
    eval_steps=100,
    save_steps=100,
    save_total_limit=2,
    eval_strategy="steps",           # "evaluation_strategy" is deprecated
    load_best_model_at_end=True,
    warmup_ratio=0.05,
    lr_scheduler_type="cosine",
    optim="adamw_torch",
    report_to="none",
    dataloader_pin_memory=False,     # required for MPS
    dataset_text_field="text",       # moved into SFTConfig (not SFTTrainer)
    max_seq_length=512,              # moved into SFTConfig
)

print(f"  Epochs: {training_args.num_train_epochs}")
print(f"  Batch size: {training_args.per_device_train_batch_size}")
print(f"  Gradient accumulation: {training_args.gradient_accumulation_steps}")
print(f"  Effective batch size: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps}")
print(f"  Learning rate: {training_args.learning_rate}")

# ============================================================================
# TRAINER
# ============================================================================
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    processing_class=tokenizer,      # "tokenizer=" deprecated, use this
)

# ============================================================================
# TRAIN
# ============================================================================
print("\n→ Starting training...")
print(f"  Total steps: {len(train_dataset) // (training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps) * training_args.num_train_epochs}")
print(f"  Estimated time: 1-2 hours")
print(f"  Watch: loss should decrease each 10 steps\n")
print("=" * 60)

trainer.train()

# ============================================================================
# SAVE
# ============================================================================
print("\n" + "=" * 60)
print("→ Saving fine-tuned LoRA adapter...")
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

# Save training summary
summary = {
    "model": "microsoft/Phi-3.5-mini-instruct",
    "technique": "LoRA",
    "lora_rank": 16,
    "lora_alpha": 32,
    "lora_target_modules": ["qkv_proj", "o_proj", "gate_up_proj", "down_proj"],
    "epochs": 3,
    "train_examples": len(train_pairs),
    "eval_examples": len(eval_pairs),
    "friend_data_format": "JSONL Alpaca (instruction + input + output)",
    "domain": "Steel plant industrial maintenance",
    "output_path": OUTPUT_DIR
}
with open(f"{OUTPUT_DIR}/training_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"✓ LoRA adapter saved to: {OUTPUT_DIR}")
print(f"✓ Training summary saved")
print("=" * 60)
print("""
FINE-TUNING COMPLETE!

Next steps:
  1. python ml/test_phi35.py   → compare base vs fine-tuned
  2. Set USE_LOCAL_MODEL=true in .env to use in agents
  3. Restart backend and test
""")
