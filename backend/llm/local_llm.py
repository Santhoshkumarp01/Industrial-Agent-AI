"""
Industrial Agent AI — Fine-tuned LLM Inference.
Phi-3.5 Mini (3.8B) fine-tuned on 2,027 steel plant maintenance examples.

Supports two backends automatically:
  1. Apple MLX  — when running on Apple Silicon (local Mac)
  2. Transformers + PEFT — when running on Linux/HF Spaces (any GPU/CPU)

The generate() function signature is identical for both backends.
Nothing else in the codebase needs to change.
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

BASE_MODEL_PATH = os.getenv("LOCAL_MODEL_BASE", "microsoft/Phi-3.5-mini-instruct")
ADAPTER_PATH    = os.getenv("LOCAL_MODEL_ADAPTER", "Santhoshkumarp/phi35-maintenance-wizard-lora")

# ── Detect which backend to use ──────────────────────────────────────────────
def _is_apple_silicon() -> bool:
    """True if running on Apple Silicon Mac."""
    try:
        import platform
        return platform.system() == "Darwin" and platform.machine() == "arm64"
    except Exception:
        return False

USE_MLX = _is_apple_silicon() and os.getenv("FORCE_TRANSFORMERS", "").lower() != "true"
logger.info(f"[LLM] Backend: {'MLX (Apple Silicon)' if USE_MLX else 'Transformers + PEFT (Linux/HF)'}")

# ── Shared singleton state ────────────────────────────────────────────────────
_model     = None
_tokenizer = None


# ── MLX backend (Apple Silicon) ───────────────────────────────────────────────
def _load_mlx():
    global _model, _tokenizer
    if _model is None:
        from mlx_lm import load
        print("→ Loading Industrial Agent AI fine-tuned model (MLX)...")
        _model, _tokenizer = load(
            BASE_MODEL_PATH,
            adapter_path=ADAPTER_PATH,
        )
        print("✓ Phi-3.5 Industrial Agent model ready (MLX)")
    return _model, _tokenizer


def _generate_mlx(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    from mlx_lm import generate as mlx_generate
    model, tokenizer = _load_mlx()
    prompt = (
        f"<|system|>\n{system_prompt}<|end|>\n"
        f"<|user|>\n{user_prompt}<|end|>\n"
        f"<|assistant|>\n"
    )
    response = mlx_generate(
        model, tokenizer,
        prompt=prompt,
        max_tokens=max_tokens,
        verbose=False,
    )
    return response.replace("<|end|>", "").replace("<|assistant|>", "").strip()


# ── Transformers + PEFT backend (HF Spaces / Linux) ──────────────────────────
def _load_transformers():
    global _model, _tokenizer
    if _model is None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel

        print(f"→ Loading Industrial Agent AI fine-tuned model (Transformers)...")
        print(f"  Base model : {BASE_MODEL_PATH}")
        print(f"  Adapter    : {ADAPTER_PATH}")

        # Determine device + quantization
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"[LLM] Device: {device}")

        # Use 4-bit quantization on GPU to fit in 16 GB VRAM
        # On CPU: use float32 (slower but works)
        if device == "cuda":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            base = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL_PATH,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
        else:
            base = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL_PATH,
                torch_dtype=torch.float32,
                device_map="cpu",
                trust_remote_code=True,
            )

        # Load LoRA adapter on top of base model
        _model = PeftModel.from_pretrained(base, ADAPTER_PATH)
        _model.eval()

        _tokenizer = AutoTokenizer.from_pretrained(
            BASE_MODEL_PATH,
            trust_remote_code=True,
        )
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token

        print(f"✓ Phi-3.5 Industrial Agent model ready (Transformers, device={device})")
    return _model, _tokenizer


def _generate_transformers(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    import torch
    model, tokenizer = _load_transformers()

    prompt = (
        f"<|system|>\n{system_prompt}<|end|>\n"
        f"<|user|>\n{user_prompt}<|end|>\n"
        f"<|assistant|>\n"
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048,
    )

    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,          # greedy — deterministic, faster
            temperature=1.0,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # Decode only the newly generated tokens (not the prompt)
    generated = output_ids[0][inputs["input_ids"].shape[1]:]
    response  = tokenizer.decode(generated, skip_special_tokens=True)

    return response.replace("<|end|>", "").replace("<|assistant|>", "").strip()


# ── Public API — unchanged signature ─────────────────────────────────────────
def generate(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
    """
    Generate maintenance analysis using fine-tuned Phi-3.5 Mini.

    Automatically picks MLX (Apple Silicon) or Transformers (Linux/GPU).
    Called identically from answerer.py regardless of backend.

    Args:
        system_prompt: Role and context instructions
        user_prompt  : Query with sensor data + retrieved document chunks
        max_tokens   : Maximum response length (default 800)

    Returns:
        Generated text response string
    """
    try:
        if USE_MLX:
            return _generate_mlx(system_prompt, user_prompt, max_tokens)
        else:
            return _generate_transformers(system_prompt, user_prompt, max_tokens)
    except Exception as e:
        logger.error(f"LLM generation error ({('MLX' if USE_MLX else 'Transformers')}): {e}")
        logger.exception("Generation traceback:")
        raise RuntimeError(f"Model generation failed: {str(e)}")
