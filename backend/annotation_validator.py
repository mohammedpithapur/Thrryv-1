"""
Annotation Type Validator

Validates if annotation text matches the declared annotation type using AI.
"""

import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


async def classify_annotation_type(
    claim_text: str,
    annotation_text: str
) -> dict:
    """
    Classify annotation type using AI (support/contradict/context).

    Returns:
        dict with 'annotation_type' (str), 'confidence' (float), 'reasoning' (str|None)
    """
    groq_api_key = os.environ.get('GROQ_API_KEY')

    if not annotation_text or len(annotation_text) < 10:
        return {"annotation_type": "context", "confidence": 0.4, "reasoning": "Too short to classify"}

    if not groq_api_key:
        text = annotation_text.lower()
        contradict_markers = ["not", "false", "wrong", "debunk", "no evidence", "misleading", "incorrect", "myth"]
        support_markers = ["evidence", "study", "research", "confirms", "supports", "shows", "data", "according to"]

        if any(m in text for m in contradict_markers):
            return {"annotation_type": "contradict", "confidence": 0.6, "reasoning": "Heuristic contradict markers"}
        if any(m in text for m in support_markers):
            return {"annotation_type": "support", "confidence": 0.6, "reasoning": "Heuristic support markers"}

        return {"annotation_type": "context", "confidence": 0.5, "reasoning": "Heuristic default"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_api_key}"},
                json={
                    "model": os.environ.get('GROQ_MODEL', 'llama-3.1-8b-instant'),
                    "messages": [
                        {
                            "role": "system",
                            "content": """Classify the annotation as one of: support, contradict, context.

Definitions:
- support: Agrees with or validates the claim; adds supporting evidence
- contradict: Challenges or disputes the claim; adds counter-evidence
- context: Neutral info, clarification, or background without taking a stance

Respond ONLY with JSON:
{"annotation_type": "support|contradict|context", "confidence": 0.0-1.0, "reasoning": "brief"}
"""
                        },
                        {
                            "role": "user",
                            "content": f"Claim: \"{claim_text}\"\nAnnotation: \"{annotation_text}\""
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 120
                }
            )

            if response.status_code == 200:
                result = response.json()["choices"][0]["message"]["content"].strip()
                import json
                try:
                    data = json.loads(result)
                    ann_type = data.get("annotation_type", "context")
                    if ann_type not in ["support", "contradict", "context"]:
                        ann_type = "context"
                    return {
                        "annotation_type": ann_type,
                        "confidence": float(data.get("confidence", 0.5)),
                        "reasoning": data.get("reasoning")
                    }
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse AI response: {result}")
    except Exception as e:
        logger.warning(f"Annotation classification failed: {e}")

    return {"annotation_type": "context", "confidence": 0.5, "reasoning": None}


async def validate_annotation_type(
    claim_text: str, 
    annotation_text: str, 
    annotation_type: str
) -> dict:
    """
    Validate if annotation text matches its declared type.
    
    Returns:
        dict with 'is_valid' (bool), 'confidence' (float), 'warning' (str|None)
    """
    groq_api_key = os.environ.get('GROQ_API_KEY')
    
    if not groq_api_key:
        return {"is_valid": True, "confidence": 1.0, "warning": None}
    
    if len(annotation_text) < 20:
        return {"is_valid": True, "confidence": 1.0, "warning": None}
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_api_key}"},
                json={
                    "model": os.environ.get('GROQ_MODEL', 'llama-3.1-8b-instant'),
                    "messages": [
                        {
                            "role": "system",
                            "content": """Analyze if annotation text matches its declared type. Consider the semantic meaning, not just keywords.

Types explained:
- support: Agrees with/validates the claim, provides supporting evidence or reasoning
- contradict: Disagrees with/challenges the claim, provides counter-evidence or opposing reasoning
- context: Neutral additional information, clarifications, or related facts without taking a stance

Respond with ONLY a JSON object:
{"match": "yes/no/unclear", "confidence": 0.0-1.0, "reasoning": "brief explanation"}

Examples:
Claim: "Earth is flat"
Annotation (type=contradict): "NASA has photos showing Earth is round" → {"match": "yes", "confidence": 0.95, "reasoning": "Provides counter-evidence"}
Annotation (type=support): "NASA photos show Earth is round" → {"match": "no", "confidence": 0.9, "reasoning": "Text contradicts rather than supports"}
"""
                        },
                        {
                            "role": "user",
                            "content": f"""Claim: "{claim_text}"

Declared type: {annotation_type}

Annotation text: "{annotation_text}"

Analyze if the annotation text matches the declared type."""
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 150
                }
            )
            
            if response.status_code == 200:
                result = response.json()["choices"][0]["message"]["content"].strip()
                
                # Parse JSON response
                import json
                try:
                    data = json.loads(result)
                    match_status = data.get("match", "unclear").lower()
                    confidence = float(data.get("confidence", 0.5))
                    reasoning = data.get("reasoning", "")
                    
                    if match_status == "no" and confidence > 0.7:
                        opposite_type = {
                            'support': 'contradict',
                            'contradict': 'support',
                            'context': 'support or contradict'
                        }.get(annotation_type, 'different')
                        
                        warning = f"⚠️ Your comment seems to {opposite_type} the claim, but you selected '{annotation_type}'. {reasoning}"
                        return {
                            "is_valid": False,
                            "confidence": confidence,
                            "warning": warning
                        }
                    
                    return {"is_valid": True, "confidence": confidence, "warning": None}
                    
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse AI response: {result}")
                    return {"is_valid": True, "confidence": 0.5, "warning": None}
            
    except Exception as e:
        logger.warning(f"Annotation validation failed: {e}")
    
    return {"is_valid": True, "confidence": 0.5, "warning": None}
