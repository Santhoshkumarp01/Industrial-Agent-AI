# MLX Training Guide — Avoiding Overfitting

## The Problem: Overfitting

With **1,824 training examples**, your model can easily **memorize** the training data instead of learning generalizable maintenance patterns. This is called **overfitting**.

### Signs of Overfitting:
- ❌ Training loss goes below 0.1
- ❌ Training loss keeps decreasing but validation loss stops or increases
- ❌ Model gives perfect answers for training examples but fails on new questions
- ❌ Loss becomes unstable (bouncing up and down)

---

## Understanding Loss Values

### What Different Loss Values Mean:

| Loss Value | What It Means | Action |
|------------|---------------|--------|
| 2.0-3.0 | Random guessing | Keep training |
| 1.0-2.0 | Learning patterns | Keep training ✅ |
| 0.4-1.0 | Domain knowledge absorbed | Keep training ✅ |
| 0.2-0.4 | **IDEAL ZONE** | **Stop here!** ✅ |
| 0.1-0.2 | Acceptable but risky | Check validation loss ⚠️ |
| Below 0.1 | **Overfitting** | **Stop immediately!** ❌ |

### Healthy Training Example:
```
Iter 25:  Train 0.650, Val 0.720  ← val slightly higher = good
Iter 50:  Train 0.420, Val 0.480  ← still generalizing ✅
Iter 75:  Train 0.280, Val 0.350  ← IDEAL — stop around here
Iter 100: Train 0.220, Val 0.340  ← val stopped decreasing
Iter 125: Train 0.180, Val 0.360  ← val going up = overfitting ❌
```

**Best checkpoint**: Iteration 75 (lowest validation loss)

### Overfitting Example:
```
Iter 50:  Train 0.280, Val 0.350  ← good
Iter 75:  Train 0.120, Val 0.380  ← train too low, val rising ❌
Iter 100: Train 0.080, Val 0.420  ← memorizing! ❌
```

---

## Safe Training Settings

### Option 1: Let It Run and Pick Best Checkpoint

**Command:**
```bash
./START_MLX_TRAINING_SAFE.sh
```

This trains with **safe settings**:
- **150 iterations** (not 600)
- **5e-6 learning rate** (slower, more stable)
- **Validation every 25 steps**
- **Checkpoints every 25 steps**

**What to watch:**
1. Look for when validation loss stops decreasing
2. That iteration is your best model
3. Use that checkpoint for inference

**Example output:**
```
Iter 25:  Val loss 0.520  ← decreasing
Iter 50:  Val loss 0.380  ← decreasing
Iter 75:  Val loss 0.310  ← decreasing
Iter 100: Val loss 0.305  ← stopped decreasing ← USE THIS ONE
Iter 125: Val loss 0.320  ← going up = overfitting
```

**Best model**: `ml/saved_models/phi35_mlx_lora_safe/adapters-100.safetensors`

---

### Option 2: Manual Training (Full Control)

If you want to watch and stop manually:

```bash
cd "/Users/user1-ak/Documents/Industrial Agent AI/backend"
source .venv/bin/activate

python -m mlx_lm lora \
  --model ml/base_models/phi35_mini \
  --train \
  --data data/training/mlx \
  --iters 150 \
  --batch-size 4 \
  --num-layers 16 \
  --learning-rate 5e-6 \
  --steps-per-eval 25 \
  --steps-per-report 10 \
  --save-every 25 \
  --adapter-path ml/saved_models/phi35_mlx_lora_manual
```

**Press Ctrl+C** when you see validation loss stop decreasing or start increasing.

---

## After Training: Pick the Best Checkpoint

### Step 1: Find Available Checkpoints
```bash
ls -lh ml/saved_models/phi35_mlx_lora_safe/
```

You'll see:
```
adapters-25.safetensors
adapters-50.safetensors
adapters-75.safetensors
adapters-100.safetensors
adapters-125.safetensors
adapters-150.safetensors
```

### Step 2: Identify Best Iteration

Look at your training log and find the iteration with **lowest validation loss**.

Example:
```
Iter 25:  Val loss 0.520
Iter 50:  Val loss 0.380
Iter 75:  Val loss 0.310  ← LOWEST
Iter 100: Val loss 0.340
```

**Best checkpoint**: `adapters-75.safetensors`

### Step 3: Copy Best Checkpoint to Main Location

```bash
# Create final adapter directory
mkdir -p ml/saved_models/phi35_mlx_lora

# Copy the best checkpoint
cp ml/saved_models/phi35_mlx_lora_safe/adapters-75.safetensors \
   ml/saved_models/phi35_mlx_lora/adapters.safetensors

# Copy config files
cp ml/saved_models/phi35_mlx_lora_safe/adapter_config.json \
   ml/saved_models/phi35_mlx_lora/

cp ml/saved_models/phi35_mlx_lora_safe/adapter_model.safetensors \
   ml/saved_models/phi35_mlx_lora/
```

---

## Testing the Model

### Compare Base vs Fine-Tuned

Update `ml/test_mlx_phi35.py` to use your chosen checkpoint:

```python
# Load fine-tuned model
print("\n→ Loading FINE-TUNED model...")
finetuned_model, finetuned_tokenizer = load(
    "ml/base_models/phi35_mini",
    adapter_path="ml/saved_models/phi35_mlx_lora"  # Your best checkpoint
)
```

Run:
```bash
python ml/test_mlx_phi35.py
```

### What Good Fine-Tuning Looks Like:

**Base model:**
```
"Check the compressor for issues. Inspect components."
```

**Fine-tuned model:**
```
DIAGNOSIS: Cooling System Failure

ROOT CAUSE: Temperature differential of 8.6°C indicates cooling 
system degradation. Possible heat exchanger fouling.

RISK LEVEL: HIGH
CONFIDENCE: 0.90

IMMEDIATE ACTIONS:
1. Reduce equipment load by 30%
2. Inspect heat exchanger within 2 hours
3. Monitor temperature continuously

SPARE PARTS: Heat exchanger gasket kit, cooling fluid
MANUAL REFERENCE: Compressor Maintenance Manual Section 4.5
```

---

## Quick Reference: Training Commands

### SAFE (Recommended):
```bash
./START_MLX_TRAINING_SAFE.sh
```

### Manual with Monitoring:
```bash
python -m mlx_lm lora \
  --model ml/base_models/phi35_mini \
  --train \
  --data data/training/mlx \
  --iters 150 \
  --batch-size 4 \
  --num-layers 16 \
  --learning-rate 5e-6 \
  --steps-per-eval 25 \
  --save-every 25 \
  --adapter-path ml/saved_models/phi35_mlx_lora_v2
```

### If You Want More Training (Larger Dataset):
```bash
python -m mlx_lm lora \
  --model ml/base_models/phi35_mini \
  --train \
  --data data/training/mlx \
  --iters 300 \
  --batch-size 4 \
  --num-layers 16 \
  --learning-rate 3e-6 \
  --steps-per-eval 50 \
  --save-every 50 \
  --adapter-path ml/saved_models/phi35_mlx_lora_extended
```

---

## Summary: What You Should Do Now

1. **Stop current training** (Ctrl+C in terminal if still running)
2. **Run safe training**: `./START_MLX_TRAINING_SAFE.sh`
3. **Watch the validation loss** in the output
4. **Pick the checkpoint** with lowest validation loss
5. **Test the model**: `python ml/test_mlx_phi35.py`
6. **Enable in production**: Set `USE_LOCAL_MODEL=true` in `.env`

**Target**: Stop when validation loss is in the **0.2-0.4 range** and stops decreasing.
