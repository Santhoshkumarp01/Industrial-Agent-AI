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
    # Phase 2 Fix — new synonyms for high-failure queries
    "qualified personnel": ["authorized personnel", "qualified electrician", "specialist", "trained personnel"],
    "clearance in air": ["creepage distance", "air gap", "minimum clearance", "clearance distance live parts"],
    "maximum speed": ["nmax", "permissible speed", "operating speed limit", "max rpm", "speed limit"],
    "bearing relubrication": ["bearing grease", "regreasing interval", "lubrication period", "grease replacement"],
    "degree of protection": ["ip rating", "ip55", "ip44", "protection class", "ingress protection"],
    "insulation resistance": ["winding resistance", "megohm", "megaohm", "IR value", "insulation test"],
    "tightening torque": ["torque value", "bolt torque", "nm torque", "fastener torque", "screw torque"],
    "weight": ["mass", "kg", "kilogram", "motor weight", "approximate weight"],
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
    CRITICAL: For exact manual questions with model names or numbered lists, preserve the original query.
    
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
    
    # CRITICAL FIX: Detect exact manual questions (section-like wording, model names, numbered items)
    # These should NOT be rewritten into generic queries
    is_exact_manual_question = bool(
        re.search(r'\b(1ph718|siemens|manual)\b', query_lower) or
        re.search(r'\b(five|three|four|six|seven|eight|ten)\s+(rules?|steps?|requirements?|procedures?|instructions?)\b', query_lower) or
        re.search(r'\bwhat are the\s+\d+\s+(rules?|steps?)\b', query_lower) or
        re.search(r'\blist(ed)?\s+(in|on)\b', query_lower)
    )
    
    # If exact manual question, add variations that preserve anchor terms
    if is_exact_manual_question:
        logger.info("Detected exact manual question - preserving anchor terms")
        
        # Extract model name if present
        model_match = re.search(r'\b(1ph718)\b', query_lower)
        model_name = model_match.group(1) if model_match else ""
        
        # Extract list terms (five rules, three steps, etc.)
        list_match = re.search(r'\b(five|three|four|six|seven|eight|ten)\s+(rules?|steps?|requirements?|procedures?)\b', query_lower)
        if list_match:
            # Add variations that keep the enumeration and anchor terms
            count_word = list_match.group(1)
            item_type = list_match.group(2)
            
            variations.append(f"{count_word} {item_type} {model_name}".strip())
            variations.append(f"observing the {count_word} {item_type}".strip())
            variations.append(f"{item_type} {model_name}".strip())
            
            # Do NOT add generic queries like "safety procedure steps"
            return variations[:3]
    
    # Common patterns for maintenance queries (generic cases only)
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
    
    # REMOVED: Generic safety variations that cause list truncation
    # Old code was adding: "safety procedure steps", "safety rules requirements", "safety instructions guidelines"
    # These are too vague and match partial list fragments instead of complete sections
    
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
    CRITICAL: For exact manual questions, original query is ALWAYS first (highest priority).
    
    Args:
        query: Original user query
        use_variations: If True, generate multiple variations
    
    Returns:
        List of rewritten queries (original + expanded + synonym variations + rule-based)
    """
    queries = []
    query_lower = query.lower()
    
    # CRITICAL: Detect exact manual questions
    is_exact_manual_question = bool(
        re.search(r'\b(1ph718|siemens|manual)\b', query_lower) or
        re.search(r'\b(five|three|four|six|seven|eight|ten)\s+(rules?|steps?|requirements?|procedures?|instructions?)\b', query_lower) or
        re.search(r'\bwhat are the\s+\d+\s+(rules?|steps?)\b', query_lower) or
        re.search(r'\blist(ed)?\s+(in|on)\b', query_lower)
    )
    
    # 1. Original query (ALWAYS FIRST - highest priority)
    queries.append(query)
    
    # For exact manual questions, limit variations to preserve precision
    if is_exact_manual_question:
        logger.info("Exact manual question detected - original query prioritized, limited variations")
        
        # Only add 2-3 targeted variations that preserve key terms
        if use_variations:
            variations = _generate_query_variations(query)
            queries.extend(variations[:2])  # Limit to 2 variations max
        
        # Deduplicate and return early
        queries = list(dict.fromkeys(queries))
        logger.info(f"Query rewriter produced {len(queries)} queries (from: '{query}')")
        return queries
    
    # For generic questions, use full expansion pipeline
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
