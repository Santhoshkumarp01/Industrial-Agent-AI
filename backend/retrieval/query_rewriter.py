"""
Query Rewriter — improves retrieval quality by rewriting vague queries.

Strategies:
1. Expand abbreviations (RM → Rolling Mill, VFD → Variable Frequency Drive)
2. Add technical context
3. Rephrase ambiguous questions
4. Generate multiple query variations for better coverage
"""

import logging
from google import genai
from google.genai import types
from typing import List
from config import config

logger = logging.getLogger(__name__)

# Initialize client
_client = None

def _get_client():
    """Get or create singleton client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GOOGLE_API_KEY)
    return _client


# Common industrial abbreviations
ABBREVIATION_MAP = {
    "rm": "rolling mill",
    "bf": "blast furnace", 
    "vfd": "variable frequency drive",
    "rtu": "remote terminal unit",
    "plc": "programmable logic controller",
    "scada": "supervisory control and data acquisition",
    "hmi": "human machine interface",
    "oee": "overall equipment effectiveness",
    "mtbf": "mean time between failures",
    "mttr": "mean time to repair",
    "cmms": "computerized maintenance management system",
    "ppm": "planned preventive maintenance",
    "rul": "remaining useful life",
}


def _expand_abbreviations(query: str) -> str:
    """Expand known abbreviations in query."""
    query_lower = query.lower()
    expanded = query
    
    for abbr, full in ABBREVIATION_MAP.items():
        # Match whole words only
        import re
        pattern = r'\b' + re.escape(abbr) + r'\b'
        if re.search(pattern, query_lower):
            expanded = re.sub(pattern, f"{abbr} ({full})", expanded, flags=re.IGNORECASE)
            logger.info(f"Expanded abbreviation: {abbr} → {full}")
    
    return expanded


def _generate_query_variations(query: str) -> List[str]:
    """
    Use Gemini to generate multiple query variations for better coverage.
    
    Example:
    Input: "How to fix vibration issue?"
    Output: [
        "How to troubleshoot high vibration in rotating equipment?",
        "What causes excessive vibration in motors?",
        "Vibration diagnostic procedures and corrective actions"
    ]
    """
    try:
        client = _get_client()
        
        prompt = f"""You are an industrial maintenance expert. Rewrite this user query into 3 precise technical variations that would retrieve relevant information from a maintenance manual.

Original Query: "{query}"

Requirements:
1. Use proper technical terminology
2. Make implicit context explicit
3. Include diagnostic and corrective action angles
4. Keep each variation concise (under 20 words)

Output format (one per line):
1. [First variation]
2. [Second variation]
3. [Third variation]"""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=200,
                temperature=0.7,  # Some creativity for variations
            )
        )
        
        text = response.text.strip()
        
        # Parse numbered list
        variations = []
        for line in text.split('\n'):
            line = line.strip()
            if line and any(line.startswith(f"{i}.") for i in range(1, 10)):
                # Remove number prefix
                cleaned = line.split('.', 1)[1].strip() if '.' in line else line
                variations.append(cleaned)
        
        logger.info(f"Generated {len(variations)} query variations")
        return variations[:3]  # Max 3 variations
        
    except Exception as e:
        logger.error(f"Query variation generation failed: {e}")
        return []


def rewrite_query(query: str, use_variations: bool = True) -> List[str]:
    """
    Rewrite user query for better retrieval.
    
    Args:
        query: Original user query
        use_variations: If True, generate multiple variations
    
    Returns:
        List of rewritten queries (original + expanded + variations)
    """
    queries = []
    
    # 1. Original query
    queries.append(query)
    
    # 2. Expanded abbreviations
    expanded = _expand_abbreviations(query)
    if expanded != query:
        queries.append(expanded)
    
    # 3. AI-generated variations (optional)
    if use_variations:
        variations = _generate_query_variations(query)
        queries.extend(variations)
    
    # Deduplicate
    queries = list(dict.fromkeys(queries))  # Preserves order
    
    logger.info(f"Query rewriter produced {len(queries)} queries")
    return queries


def get_best_query(query: str) -> str:
    """
    Get single best rewritten query (for simple cases).
    
    Returns the first variation or expanded query.
    """
    queries = rewrite_query(query, use_variations=True)
    
    # Prefer variations over original
    if len(queries) > 1:
        return queries[1]  # First rewrite
    return queries[0]
