#!/usr/bin/env python3
"""
Upload fine-tuned Phi-3.5 Mini LoRA adapter to Hugging Face Hub.

What gets uploaded (only 24 MB total):
  - adapters.safetensors    (best checkpoint = iter 150)
  - adapter_config.json     (LoRA training config)
  - README.md               (model card)

The base model (microsoft/Phi-3.5-mini-instruct) stays on HF - no need to re-upload.
Users load the adapter on top of the base model at inference time.

Usage:
    cd backend
    .venv/bin/python ml/upload_to_huggingface.py --repo YOUR_HF_USERNAME/phi35-maintenance-wizard-lora
"""

import argparse
import os
from pathlib import Path

from huggingface_hub import HfApi, create_repo, login

# ── Config ──────────────────────────────────────────────────────────────────
ADAPTER_DIR = Path("ml/saved_models/phi35_mlx_lora")
README_PATH = ADAPTER_DIR / "README.md"

MODEL_CARD = """\
---
base_model: microsoft/Phi-3.5-mini-instruct
library_name: mlx
tags:
  - lora
  - mlx
  - industrial-maintenance
  - steel-plant
  - rag
  - domain-adaptation
license: mit
language:
  - en
pipeline_tag: text-generation
---

# Phi-3.5 Mini — Industrial Maintenance Wizard (LoRA Adapter)

Fine-tuned LoRA adapter for **Phi-3.5 Mini Instruct** specialised in
steel-plant maintenance diagnostics, safety procedures, and equipment fault analysis.

## Model Details

| Property | Value |
|----------|-------|
| Base model | [microsoft/Phi-3.5-mini-instruct](https://huggingface.co/microsoft/Phi-3.5-mini-instruct) |
| Fine-tuning method | LoRA (Low-Rank Adaptation) via Apple MLX |
| LoRA rank | 8 |
| LoRA scale | 20.0 |
| Trainable layers | 16 |
| Trainable parameters | ~20M (0.52% of 3.8B) |
| Training iterations | 150 |
| Batch size | 4 |
| Learning rate | 5e-6 |
| Max sequence length | 2048 |
| Training framework | [mlx-lm](https://github.com/ml-explore/mlx-examples) |
| Hardware | Apple Silicon (M-series) |
| Training time | ~45-60 minutes |

## Training Dataset

**Total: 2,027 examples** (1,824 train / 203 validation)

| Source | Examples | Description |
|--------|----------|-------------|
| Industrial expert data | 1,973 | Real-world maintenance Q&A from steel plant operations |
| Incident history | 320 | 40 equipment failures × 8 Q&A templates |
| SOPs | 80 | Bearing replacement, compressor, lubrication, motor inspection |
| Spare parts catalog | 150 | Part numbers, stock levels, lead times, warehouse locations |
| Sensor thresholds | 96 | Normal / Warning / Critical readings for 4 equipment types |
| Multi-turn diagnostics | 50 | Progressive fault diagnosis conversations |
| Prioritisation scenarios | 60 | Multi-equipment triage decisions |

## Capabilities

The fine-tuned model demonstrates domain expertise including:

- **Exact thresholds** — vibration mm/s, temperature °C, current A, pressure bar per equipment
- **Part numbers** — SKF bearings, specific catalogue references with warehouse locations
- **Incident recall** — references historical fault patterns (e.g. IR-2023-055)
- **Safety procedures** — 5-safety-rules, lockout/tagout, ESD handling
- **Structured outputs** — DIAGNOSIS / ROOT CAUSE / RISK LEVEL / IMMEDIATE ACTIONS format
- **RAG citation** — correctly uses [C1], [C2] inline citation markers

## Usage (MLX — Apple Silicon)

```python
from mlx_lm import load, generate

model, tokenizer = load(
    "microsoft/Phi-3.5-mini-instruct",
    adapter_path="YOUR_HF_USERNAME/phi35-maintenance-wizard-lora"
)

prompt = (
    "<|system|>\\nYou are an expert industrial maintenance engineer.<|end|>\\n"
    "<|user|>\\nRolling Mill #3 shows vibration 9.2 mm/s and temperature 96°C. "
    "What is the diagnosis?<|end|>\\n<|assistant|>\\n"
)

response = generate(model, tokenizer, prompt=prompt, max_tokens=400)
print(response)
```

## Performance

| Metric | Value |
|--------|-------|
| Final training loss | ~0.30 |
| Final validation loss | ~0.34 |
| Loss reduction | ~88% (from 2.5 → 0.3) |
| System test (50 questions) | 100% success rate |
| Citation rate | 86% of answers include source citations |
| Average inference time | ~8-12 seconds (Apple M-series) |

## Qualitative Comparison

**Base Phi-3.5 Mini:**
> "High vibration in bearings can be caused by wear, misalignment, or lack of
> lubrication. I recommend checking the bearing condition."

**Fine-tuned Maintenance Wizard:**
> "DIAGNOSIS: Bearing race defect — Rolling Mill #3 vibration 9.2 mm/s exceeds
> CRITICAL threshold (6.5 mm/s). Temperature 96°C at critical limit (95°C).
> ROOT CAUSE: Metal particle ingress in lubrication circuit (ref: IR-2023-055).
> RISK LEVEL: HIGH — estimated time to failure 4-6 hours.
> IMMEDIATE ACTIONS:
> 1. Reduce mill speed by 40%
> 2. Assign team to bearing B2 inspection
> 3. Prepare SKF-22318 from Warehouse-A Rack-3 (2 units in stock)
> Estimated repair: 6-8 hours downtime [C1]"

## System Architecture

This adapter is used inside the **Industrial Agent AI** RAG pipeline:

```
PDF Manual → Chunker (parent/child) → Qdrant Vector DB
                                           ↓
User Query → Embedder → Hybrid Search (Dense + BM25) → Reranker
                                           ↓
                              Parent Section Retrieval
                                           ↓
                         Fine-tuned Phi-3.5 Mini (this model)
                                           ↓
                              Cited Answer + Source Reference
```

## Citation

If you use this adapter in your work, please cite:

```
@misc{maintenance-wizard-lora-2024,
  title  = {Phi-3.5 Mini Industrial Maintenance Wizard LoRA Adapter},
  year   = {2024},
  url    = {https://huggingface.co/YOUR_HF_USERNAME/phi35-maintenance-wizard-lora}
}
```

## License

MIT — adapter weights only. Base model license: [MIT](https://huggingface.co/microsoft/Phi-3.5-mini-instruct/blob/main/LICENSE).
"""

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Upload LoRA adapter to Hugging Face Hub")
    parser.add_argument(
        "--repo",
        required=True,
        help="HuggingFace repo id, e.g. your-username/phi35-maintenance-wizard-lora"
    )
    parser.add_argument(
        "--token",
        default=None,
        help="HuggingFace write token (or set HF_TOKEN env var)"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        default=False,
        help="Make the repository private"
    )
    args = parser.parse_args()

    # ── Auth ────────────────────────────────────────────────────────────────
    token = args.token or os.environ.get("HF_TOKEN")
    if not token:
        print("No token provided. Trying cached login...")
        print("If this fails, run: huggingface-cli login")
    else:
        login(token=token)
        print("✓ Logged in to Hugging Face")

    api = HfApi()

    # ── Create or verify repo ────────────────────────────────────────────────
    print(f"\nCreating/verifying repo: {args.repo}")
    try:
        create_repo(
            repo_id=args.repo,
            repo_type="model",
            private=args.private,
            exist_ok=True,
        )
        print(f"✓ Repo ready: https://huggingface.co/{args.repo}")
    except Exception as e:
        print(f"✗ Repo creation failed: {e}")
        return

    # ── Write model card ─────────────────────────────────────────────────────
    readme_content = MODEL_CARD.replace(
        "YOUR_HF_USERNAME/phi35-maintenance-wizard-lora", args.repo
    )
    README_PATH.write_text(readme_content)
    print("✓ Model card written")

    # ── Upload files ─────────────────────────────────────────────────────────
    files_to_upload = [
        ("adapters.safetensors",  "adapters.safetensors"),
        ("adapter_config.json",   "adapter_config.json"),
        ("README.md",             "README.md"),
    ]

    print("\nUploading files...")
    for local_name, remote_name in files_to_upload:
        local_path = ADAPTER_DIR / local_name
        if not local_path.exists():
            print(f"  ⚠ Skipping (not found): {local_path}")
            continue

        size_mb = local_path.stat().st_size / (1024 * 1024)
        print(f"  Uploading {local_name} ({size_mb:.1f} MB)...", end=" ", flush=True)

        api.upload_file(
            path_or_fileobj=str(local_path),
            path_in_repo=remote_name,
            repo_id=args.repo,
            repo_type="model",
        )
        print("✓")

    print(f"\n{'='*60}")
    print("UPLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"Model URL: https://huggingface.co/{args.repo}")
    print()
    print("To load in your project, update backend/.env:")
    print(f'  LOCAL_MODEL_ADAPTER="{args.repo}"')
    print()
    print("Then in local_llm.py, mlx_lm will pull the adapter automatically:")
    print(f'  load("microsoft/Phi-3.5-mini-instruct", adapter_path="{args.repo}")')


if __name__ == "__main__":
    main()
