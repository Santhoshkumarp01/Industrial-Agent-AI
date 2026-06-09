"""
Query Rewriter — improves retrieval quality by rewriting vague queries.

Strategies:
1. Expand abbreviations (RM → Rolling Mill, VFD → Variable Frequency Drive)
2. Add technical context
3. Generate rule-based query variations for better coverage
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


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

# Domain-specific synonym map for better retrieval
SYNONYMS = {
    "safety levels": ["safety rules", "safety procedures", "five safety rules", "safety steps", "isolation safety"],
    "safety level": ["safety rule", "safety procedure", "safety step"],
    "maintenance steps": ["maintenance procedure", "service instructions", "maintenance instructions"],
    "fault": ["error", "defect", "failure", "malfunction", "problem"],
    "bearing": ["rolling contact bearing", "bearing assembly", "bearing replacement"],
    "shutdown": ["isolate", "deactivate", "power off", "switch off", "de-energize"],
    "vibration": ["oscillation", "vibration level", "mechanical vibration"],
    "temperature": ["thermal", "heat", "temperature level", "operating temperature"],
    "pressure": ["hydraulic pressure", "pneumatic pressure", "pressure level"],
    "lubrication": ["lubricant", "grease", "oil", "lubrication system"],
}


def _expand_abbreviations(query: str) -> str:
    """Expand known abbreviations in query."""
    query_lower = query.lower()
    expanded = query
    
    for abbr, full in ABBREVIATION_MAP.items():
        # Match whole words only
        pattern = r'\b' + re.escape(abbr) + r'\b'
        if re.search(pattern, query_lower):
            expanded = re.sub(pattern, f"{abbr} ({full})", expanded, flags=re.IGNORECASE)
            logger.info(f"Expanded abbreviation: {abbr} → {full}")
    
    return expanded


def _expand_with_synonyms(query: str) -> List[str]:
    """Expand query with domain-specific synonyms."""
    query_lower = query.lower()
    variations = []
    
    for key, synonyms in SYNONYMS.items():
        if key in query_lower:
            # Replace key phrase with each synonym
            for synonym in synonyms:
                variation = query_lower.replace(key, synonym)
                if variation != query_lower:
                    variations.append(variation)
    
    return variations[:3]  # Limit to top 3 synonym variations


def _generate_query_variations(query: str) -> List[str]:
    """
    Generate rule-based query variations for better coverage.
    CRITICAL: Always return at least 3 variations (never empty).
    
    Example:
    Input: "How to fix vibration issue?"
    Output: [
        "vibration troubleshooting diagnosis",
        "high vibration causes solutions",
        "vibration problem corrective action"
    ]
    """
    variations = []
    
    # Extract key technical terms
    query_lower = query.lower()
    
    # Common patterns for maintenance queries
    if "how to fix" in query_lower or "repair" in query_lower:
        # Diagnostic angle
        term = query_lower.replace("how to fix", "").replace("repair", "").strip()
        variations.append(f"{term} troubleshooting diagnosis")
        variations.append(f"{term} causes solutions")
        variations.append(f"{term} repair procedure")
    
    if "what are" in query_lower or "what is" in query_lower:
        # Definition/list angle
        term = query_lower.replace("what are", "").replace("what is", "").replace("the", "").strip()
        variations.append(f"{term} list")
        variations.append(f"{term} description")
        variations.append(f"{term} definition")
    
    if "vibration" in query_lower:
        variations.append("vibration analysis bearing alignment")
        variations.append("excessive vibration motor equipment")
    
    if "temperature" in query_lower or "overheat" in query_lower:
        variations.append("temperature monitoring cooling lubrication")
        variations.append("thermal failure overheating causes")
    
    if "pressure" in query_lower:
        variations.append("pressure system leak valve")
        variations.append("pressure abnormal hydraulic pneumatic")
    
    if "noise" in query_lower or "sound" in query_lower:
        variations.append("abnormal noise bearing gearbox")
        variations.append("acoustic signature mechanical fault")
    
    if "bearing" in query_lower:
        variations.append("bearing failure wear diagnosis")
        variations.append("bearing replacement lubrication procedure")
    
    if "motor" in query_lower:
        variations.append("motor fault electrical winding")
        variations.append("motor failure troubleshooting")
    
    if "safety" in query_lower:
        variations.append("safety procedure steps")
        variations.append("safety rules requirements")
        variations.append("safety instructions guidelines")
    
    # Remove duplicates and limit
    variations = list(dict.fromkeys(variations))[:5]
    
    # CRITICAL FIX: Never return empty - always provide at least basic variations
    if not variations:
        # Generic fallback variations
        words = query_lower.split()
        if len(words) > 2:
            variations = [
                " ".join(words[:3]),  # First 3 words
                " ".join(words[-3:]),  # Last 3 words
                query_lower  # Original as fallback
            ]
        else:
            variations = [query_lower]  # At minimum, original query
    
    logger.info(f"Generated {len(variations)} query variations")
    return variations


def rewrite_query(query: str, use_variations: bool = True) -> List[str]:
    """
    Rewrite user query for better retrieval.
    CRITICAL: Always returns at least the original query (never empty list).
    
    Args:
        query: Original user query
        use_variations: If True, generate multiple variations
    
    Returns:
        List of rewritten queries (original + expanded + synonym variations + rule-based)
    """
    queries = []
    
    # 1. Original query (always include)
    queries.append(query)
    
    # 2. Expanded abbreviations
    expanded = _expand_abbreviations(query)
    if expanded != query:
        queries.append(expanded)
    
    # 3. Synonym expansion
    synonym_variations = _expand_with_synonyms(query)
    queries.extend(synonym_variations)
    
    # 4. Rule-based variations (optional)
    if use_variations:
        variations = _generate_query_variations(query)
        queries.extend(variations)
    
    # Deduplicate while preserving order
    queries = list(dict.fromkeys(queries))
    
    # CRITICAL FIX: Ensure we never return empty
    if not queries:
        queries = [query]  # Minimum fallback
    
    logger.info(f"Query rewriter produced {len(queries)} queries (from: '{query}')")
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
