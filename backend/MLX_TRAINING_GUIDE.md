# MLX Fine-Tuning Guide — 10-15× Faster than PyTorch

**STATUS**: PyTorch training is TOO SLOW (~7-8 min/step = 80 hours total)  
**SOLUTION**: Use Apple's MLX framework (45-60 minutes total)

---

## Why MLX?

- **PyTorch MPS**: ~7-8 minutes per step → **80 hours total** for 684 steps
- **MLX**: ~5-10 seconds per step → **45-60 minutes total** for 600 iterations
- **10-15× faster** on Apple Silicon

---

## Step 1: Stop PyTorch Training

If PyTorch training is still running in terminal:

```bash
# Press Ctrl+C in the terminal running finetune_phi35.py
```

---

## Step 2: Convert Data to MLX Format

```bash
cd "/Users/user1-ak/Documents/Industrial Agent AI/backend"
source .venv/bin/activate
python ml/convert_to_mlx.py
```

**Output**:
- `data/training/mlx/train.jsonl` (1,824 examples)
- `data/training/mlx/valid.jsonl` (203 examples)

---

## Step 3: Run MLX Fine-Tuning

```bash
python -m mlx_lm.lora \
  --model ml/base_models/phi35_mini \
  --train \
  --data data/training/mlx \
  --iters 600 \
  --batch-size 4 \
  --lora-layers 16 \
  --learning-rate 1e-5 \
  --save-every 100 \
  --adapter-path ml/saved_models/phi35_mlx_lora
```

**Training Time**: 45-60 minutes (vs 80 hours PyTorch)

**Parameters Explained**:
- `--iters 600`: Training iterations (comparable to ~3 epochs)
- `--batch-size 4`: Samples per batch (MLX handles memory efficiently)
- `--lora-layers 16`: LoRA rank (matches PyTorch config)
- `--learning-rate 1e-5`: Conservative learning rate for stability

---

## Step 4: Test the Fine-Tuned Model

Create `ml/test_mlx_phi35.py`:

```python
from mlx_lm import load, generate

# Load base model
print("→ Loading BASE model...")
base_model, base_tokenizer = load("ml/base_models/phi35_mini")

# Load fine-tuned model
print("→ Loading FINE-TUNED model...")
finetuned_model, finetuned_tokenizer = load(
    "ml/base_models/phi35_mini",
    adapter_path="ml/saved_models/phi35_mlx_lora"
)

# Test prompt
prompt = """<|system|>
You are an expert AI maintenance engineer specializing in steel plant equipment.<|end|>
<|user|>
Equipment alert: Compressor showing abnormal operation. Temperature: 45°C (baseline: 35°C), Torque: 55 Nm (baseline: 40 Nm). Provide diagnosis.<|end|>
<|assistant|>
"""

print("\n" + "="*60)
print("BASE MODEL RESPONSE:")
print("="*60)
response_base = generate(base_model, base_tokenizer, prompt=prompt, max_tokens=300)
print(response_base)

print("\n" + "="*60)
print("FINE-TUNED MODEL RESPONSE:")
print("="*60)
response_finetuned = generate(finetuned_model, finetuned_tokenizer, prompt=prompt, max_tokens=300)
print(response_finetuned)
```

Run comparison:
```bash
python ml/test_mlx_phi35.py
```

---

## Step 5: Update Inference Code for MLX

Update `llm/local_llm.py`:

```python
from mlx_lm import load, generate

class LocalLLM:
    def __init__(self, use_finetuned: bool = True):
        model_path = "ml/base_models/phi35_mini"
        adapter_path = "ml/saved_models/phi35_mlx_lora" if use_finetuned else None
        
        print(f"→ Loading {'fine-tuned' if adapter_path else 'base'} Phi-3.5 Mini (MLX)...")
        self.model, self.tokenizer = load(model_path, adapter_path=adapter_path)
    
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        return generate(self.model, self.tokenizer, prompt=prompt, max_tokens=max_tokens)
```

---

## Step 6: Enable in Production

Update `.env`:
```bash
USE_LOCAL_MODEL=true
```

Restart backend:
```bash
source .venv/bin/activate
uvicorn main:app --reload
```

---

## Monitoring Training Progress

MLX will show:
```
Iter 10: Train loss 2.345, Val loss 2.401, Tokens/sec 1234
Iter 20: Train loss 2.123, Val loss 2.234, Tokens/sec 1250
...
Iter 600: Train loss 0.891, Val loss 0.945, Tokens/sec 1280
```

**Good training**: Loss should steadily decrease from ~2.5 → ~0.9

---

## File Sizes

- Base model: ~7.6 GB
- MLX LoRA adapter: ~100-200 MB (lightweight!)
- Total: Still ~7.7 GB (adapter merges at inference)

---

## Comparison Summary

| Aspect | PyTorch MPS | MLX |
|--------|-------------|-----|
| Training time | 80 hours | 45-60 min |
| Memory usage | ~14 GB | ~12 GB |
| Speed per step | 7-8 min | 5-10 sec |
| Setup complexity | Medium | Easy |
| Apple Silicon optimized | Partial | Full |

---

## Troubleshooting

**Error: "module 'mlx_lm' has no attribute 'lora'"**
```bash
pip install --upgrade mlx-lm
```

**Error: "Model not found"**
Check that `ml/base_models/phi35_mini/` contains `config.json` and model files.

**MLX training crashes**
Reduce `--batch-size` from 4 to 2 or 1.

---

**Ready to start?** Run Step 2 (convert data) then Step 3 (MLX training)!
