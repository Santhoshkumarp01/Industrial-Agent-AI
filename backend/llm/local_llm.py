"""
Maintenance Wizard Fine-tuned Model — MLX Inference.
Phi-3.5 Mini (3.8B) fine-tuned on 2,027 steel plant maintenance examples.
Runs entirely offline on Apple Silicon using MLX framework.

Loaded once as singleton — stays in memory for fast inference (~8-12s per call).
"""

import os
from mlx_lm import load, generate as mlx_generate

BASE_MODEL_PATH = os.getenv("LOCAL_MODEL_BASE", "ml/base_models/phi35_mini")
ADAPTER_PATH = os.getenv("LOCAL_MODEL_ADAPTER", "ml/saved_models/phi35_mlx_lora")

_model = None
_tokenizer = None


def _load():
    """Load fine-tuned model as singleton."""
    global _model, _tokenizer
    if _model is None:
        print("→ Loading Maintenance Wizard fine-tuned model...")
        _model, _tokenizer = load(
            BASE_MODEL_PATH,
            adapter_path=ADAPTER_PATH
        )
        print("✓ Phi-3.5 Maintenance Model ready")
    return _model, _tokenizer


def generate(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
    """
    Generate maintenance analysis using fine-tuned Phi-3.5 Mini.
    
    Args:
        system_prompt: Role and context instructions
        user_prompt: Specific query with sensor data
        max_tokens: Maximum response length
    
    Returns:
        Generated text response
    """
    try:
        model, tokenizer = _load()
        
        prompt = (
            f"<|system|>\n{system_prompt}<|end|>\n"
            f"<|user|>\n{user_prompt}<|end|>\n"
            f"<|assistant|>\n"
        )
        
        response = mlx_generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            verbose=False
        )
        
        # Clean up template tokens
        return response.replace("<|end|>", "").replace("<|assistant|>", "").strip()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"MLX generation error: {type(e).__name__}: {e}")
        logger.exception("MLX generation traceback:")
        raise RuntimeError(f"Model generation failed: {str(e)}")
