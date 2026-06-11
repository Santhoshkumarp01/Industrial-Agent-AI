"""Utilities for working with LLM responses."""
import json
import logging

logger = logging.getLogger(__name__)


def parse_llm_json(raw_text: str) -> dict:
    """
    Robustly parse JSON from LLM response.
    
    Handles:
    - Markdown code fences (```)
    - 'json' language tag
    - Leading/trailing whitespace
    - Extra text before/after JSON block
    
    Args:
        raw_text: Raw response text from LLM
        
    Returns:
        Parsed JSON as dict
        
    Raises:
        ValueError: If JSON cannot be parsed after all attempts
    """
    text = raw_text.strip()
    
    # Remove markdown code fences
    if "```" in text:
        # Extract content between first ``` and last ```
        parts = text.split("```")
        # Find the part that looks like JSON (starts with { or [)
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{") or part.startswith("["):
                text = part
                break
    
    # Find JSON object boundaries as last resort
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}")
        logger.error(f"Raw text (first 500 chars): {raw_text[:500]}")
        raise ValueError(
            f"Could not parse LLM JSON response: {e}\n"
            f"Raw text preview: {raw_text[:200]}..."
        )
