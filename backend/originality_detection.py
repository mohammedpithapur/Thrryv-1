"""
Originality Detection & Recognition System for Thrryv

This module detects and recognizes posts that show high originality
(novel content that doesn't closely resemble existing content on the platform).

Key features:
- Semantic similarity detection
- Pattern matching
- Plagiarism detection
- Novelty scoring
- Recognition and boosting of original content
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class OriginalityAnalysis:
    """Analysis of content originality"""
    claim_id: str
    originality_score: float  # 0-100
    novelty_level: str  # "highly_original", "original", "semi_original", "derivative", "duplicate"
    similarity_matches: List[Dict[str, Any]]  # Similar content found
    is_flagged_for_manual_review: bool
    boost_eligible: bool
    analysis_timestamp: str


class OriginalityDetector:
    """
    Detects and analyzes originality of content.
    
    Principles:
    - Focuses on novelty, not accuracy
    - Clearly communicates originality vs. accuracy
    - Boosts discovery for original content
    - Detects plagiarism/duplication
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('EMERGENT_LLM_KEY')
        self.similarity_threshold = 0.75  # 75% similarity = likely duplicate
        self.moderate_similarity = 0.55  # 55% similarity = moderate match
    
    async def analyze_originality(
        self,
        claim: Dict[str, Any],
        existing_claims: List[Dict[str, Any]]
    ) -> OriginalityAnalysis:
        """
        Analyze originality of a claim against existing platform content.
        
        Args:
            claim: New claim to analyze
            existing_claims: All existing claims in database
        
        Returns:
            Detailed originality analysis
        """
        
        claim_text = claim.get('text', '')
        claim_id = claim.get('id', '')
        
        # Get similarity matches
        similarity_matches = await self._find_similar_content(
            claim_text,
            existing_claims
        )
        
        # Calculate originality score
        originality_score = self._calculate_originality_score(similarity_matches)
        
        # Determine novelty level
        novelty_level = self._determine_novelty_level(
            originality_score,
            similarity_matches
        )
        
        # Check if flagged for review
        is_flagged = (
            originality_score < 30 or  # Very low originality
            len([m for m in similarity_matches if m['similarity'] > self.similarity_threshold]) > 0
        )
        
        # Determine if eligible for originality boost
        boost_eligible = (
            originality_score >= 75 and
            novelty_level in ["highly_original", "original"]
        )
        
        return OriginalityAnalysis(
            claim_id=claim_id,
            originality_score=originality_score,
            novelty_level=novelty_level,
            similarity_matches=similarity_matches[:5],  # Top 5 matches
            is_flagged_for_manual_review=is_flagged,
            boost_eligible=boost_eligible,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    async def _find_similar_content(
        self,
        claim_text: str,
        existing_claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find similar content in existing claims.
        
        Uses both semantic and textual similarity.
        """
        
        similar_matches = []
        
        for existing_claim in existing_claims:
            existing_text = existing_claim.get('text', '')
            
            # Calculate similarity
            similarity = await self._calculate_similarity(claim_text, existing_text)
            
            if similarity >= self.moderate_similarity:
                similar_matches.append({
                    'claim_id': existing_claim.get('id', ''),
                    'author_id': existing_claim.get('author_id', ''),
                    'text_preview': existing_text[:150],
                    'similarity': similarity,
                    'created_at': existing_claim.get('created_at', ''),
                    'annotation_count': existing_claim.get('annotation_count', 0)
                })
        
        # Sort by similarity (highest first)
        similar_matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similar_matches
    
    async def _calculate_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate similarity between two texts.
        
        Uses multiple methods for robust comparison.
        """
        
        # Method 1: Token overlap (simple but fast)
        tokens1 = set(self._tokenize(text1))
        tokens2 = set(self._tokenize(text2))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        token_similarity = intersection / union if union > 0 else 0.0
        
        # Method 2: Semantic similarity (using LLM if available)
        semantic_similarity = await self._calculate_semantic_similarity(text1, text2)
        
        # Combine scores (60% semantic, 40% token)
        combined_similarity = (semantic_similarity * 0.6) + (token_similarity * 0.4)
        
        return min(1.0, max(0.0, combined_similarity))
    
    async def _calculate_semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate semantic similarity using LLM.
        
        Falls back to simple heuristics if LLM unavailable.
        """
        
        if not self.api_key:
            return self._calculate_semantic_similarity_fallback(text1, text2)
        
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import json
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"similarity-{datetime.now().timestamp()}",
                system_message="""You are a semantic similarity analyzer.
Compare two text snippets and determine how similar they are semantically (0-1 scale).
Consider:
- Same topic/subject
- Same perspective or viewpoint
- Similar claims or arguments
- Paraphrasing vs original

Respond ONLY with JSON:
{"similarity": <0.0-1.0>, "reasoning": "brief explanation"}"""
            ).with_model("openai", "gpt-4o-mini")
            
            prompt = f"Text 1: {text1[:200]}\n\nText 2: {text2[:200]}"
            response = await chat.send_message(UserMessage(text=prompt))
            
            result = self._parse_json_response(response)
            if result:
                return min(1.0, max(0.0, result.get('similarity', 0.5)))
        
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
        
        return self._calculate_semantic_similarity_fallback(text1, text2)
    
    def _calculate_semantic_similarity_fallback(self, text1: str, text2: str) -> float:
        """
        Fallback semantic similarity using keyword analysis.
        """
        
        # Extract keywords
        keywords1 = set(self._tokenize(text1))
        keywords2 = set(self._tokenize(text2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Remove common words
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'that', 'this', 'it', 'to', 'for', 'of', 'in',
            'on', 'at', 'by', 'with', 'from', 'as', 'about', 'into', 'through',
            'during', 'can', 'could', 'would', 'should', 'may', 'might', 'must'
        }
        
        keywords1 = keywords1 - common_words
        keywords2 = keywords2 - common_words
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Calculate overlap
        overlap = len(keywords1.intersection(keywords2))
        max_keywords = max(len(keywords1), len(keywords2))
        
        return overlap / max_keywords
    
    def _calculate_originality_score(
        self,
        similarity_matches: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate originality score (0-100).
        
        Based on similarity to existing content.
        """
        
        if not similarity_matches:
            return 100.0  # No similar content = fully original
        
        # Get highest similarity
        highest_similarity = similarity_matches[0]['similarity']
        
        # Convert similarity to originality (inverse)
        originality = 100 - (highest_similarity * 100)
        
        return max(0.0, min(100.0, originality))
    
    def _determine_novelty_level(
        self,
        originality_score: float,
        similarity_matches: List[Dict[str, Any]]
    ) -> str:
        """
        Determine novelty level (0-100 -> descriptive level).
        """
        
        has_duplicate = any(m['similarity'] > self.similarity_threshold for m in similarity_matches)
        
        if has_duplicate:
            return "duplicate"
        
        has_high_similarity = any(m['similarity'] > 0.70 for m in similarity_matches)
        
        if originality_score >= 85:
            return "highly_original"
        elif originality_score >= 70 and not has_high_similarity:
            return "original"
        elif originality_score >= 50 and not has_high_similarity:
            return "semi_original"
        elif has_high_similarity:
            return "derivative"
        else:
            return "original"
    
    def boost_original_content(
        self,
        claim: Dict[str, Any],
        originality_analysis: OriginalityAnalysis
    ) -> Dict[str, Any]:
        """
        Apply originality boost to content.
        
        Enhances discoverability of original content.
        """
        
        if not originality_analysis.boost_eligible:
            return claim
        
        # Add originality signals
        claim['originality_boosted'] = True
        claim['originality_score'] = originality_analysis.originality_score
        claim['novelty_level'] = originality_analysis.novelty_level
        
        # Add discovery boost (used in ranking)
        # This is a soft boost - not a hard rank
        originality_boost = (originality_analysis.originality_score / 100) * 25
        claim['discovery_boost_originality'] = originality_boost
        
        logger.info(f"Original content boost applied to {claim.get('id')}: "
                   f"score={originality_analysis.originality_score}, "
                   f"boost={originality_boost}")
        
        return claim
    
    def flag_for_review(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Flag content for potential plagiarism review."""
        
        claim['originality_flagged'] = True
        claim['originality_review_needed'] = True
        
        return claim
    
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        Simple tokenization.
        
        Splits text into words, lowercases, removes punctuation.
        """
        
        import string
        
        text = text.lower()
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Split into words
        tokens = text.split()
        
        return tokens
    
    @staticmethod
    def _parse_json_response(response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response"""
        
        import json
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(response[start:end])
                except:
                    pass
        
        return None
    
    async def calculate_bulk_originality(
        self,
        new_claims: List[Dict[str, Any]],
        existing_claims: List[Dict[str, Any]]
    ) -> List[OriginalityAnalysis]:
        """
        Calculate originality for multiple claims efficiently.
        """
        
        results = []
        
        for claim in new_claims:
            analysis = await self.analyze_originality(claim, existing_claims)
            results.append(analysis)
        
        return results
