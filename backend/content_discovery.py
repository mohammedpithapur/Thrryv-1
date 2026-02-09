"""
AI-Powered Content Discovery Engine for Thrryv

This module handles intelligent content discovery based on:
- User intent
- Perspective diversity
- Content relevance
- User engagement standing
- Originality signals
- Domain expertise indicators
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class DiscoveryAlgorithm(str, Enum):
    """Discovery algorithm options"""
    RELEVANCE = "relevance"
    DIVERSITY = "diversity"
    EMERGENT = "emergent"  # New emerging content
    STANDING_AWARE = "standing_aware"  # Boosted by user standing


@dataclass
class DiscoverySignals:
    """Signals used for content discovery"""
    relevance_score: float  # 0-100: How relevant to query
    diversity_score: float  # 0-100: Diverse perspective indicator
    originality_score: float  # 0-100: How original/novel
    engagement_quality: float  # 0-100: Quality of engagement signals
    author_standing: float  # User standing score
    recency_weight: float  # Recent content boost
    clarity_signal: float  # Content clarity indicator


@dataclass
class DiscoveryResult:
    """Result of content discovery"""
    claim_id: str
    author_id: str
    author_standing: float
    title: str
    signals: DiscoverySignals
    composite_score: float
    relevance_match_explanation: str
    diversity_indicators: List[str]
    perspective_type: str


class ContentDiscoveryEngine:
    """
    AI-powered content discovery engine for Thrryv.
    
    Key principles:
    - Prioritizes relevance over viral metrics
    - Encourages perspective diversity
    - Respects user intent
    - Rewards original thinking
    - Supports discoverer standing over pure popularity
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('EMERGENT_LLM_KEY')
        self.session = None
    
    async def discover_content(
        self,
        user_query: str,
        available_claims: List[Dict[str, Any]],
        user_standing: float = 1.0,
        algorithm: DiscoveryAlgorithm = DiscoveryAlgorithm.RELEVANCE,
        limit: int = 20,
        diversity_preference: float = 0.3,  # 0-1 scale
    ) -> List[DiscoveryResult]:
        """
        Discover relevant content based on user intent and signals.
        
        Args:
            user_query: User's intent in natural language
            available_claims: List of claims to rank
            user_standing: User's standing score
            algorithm: Which discovery algorithm to use
            limit: Max results to return
            diversity_preference: How much to prioritize perspective diversity (0-1)
        
        Returns:
            List of discovery results ranked by composite score
        """
        
        # Extract user intent and preferences
        intent = await self._analyze_user_intent(user_query)
        
        # Score each claim
        results = []
        for claim in available_claims:
            signals = await self._calculate_discovery_signals(
                claim=claim,
                user_intent=intent,
                user_standing=user_standing,
                diversity_preference=diversity_preference
            )
            
            # Calculate composite score based on algorithm
            composite_score = self._calculate_composite_score(
                signals=signals,
                algorithm=algorithm,
                diversity_preference=diversity_preference
            )
            
            result = DiscoveryResult(
                claim_id=claim['id'],
                author_id=claim['author_id'],
                author_standing=claim.get('author_standing', 1.0),
                title=claim['text'][:100],
                signals=signals,
                composite_score=composite_score,
                relevance_match_explanation=intent.get('query_analysis', ''),
                diversity_indicators=self._extract_diversity_indicators(claim),
                perspective_type=claim.get('perspective_type', 'neutral')
            )
            results.append(result)
        
        # Sort by composite score (descending)
        results.sort(key=lambda x: x.composite_score, reverse=True)
        
        # Apply algorithm-specific ranking adjustments
        if algorithm == DiscoveryAlgorithm.STANDING_AWARE:
            results = self._apply_standing_aware_ranking(results)
        elif algorithm == DiscoveryAlgorithm.DIVERSITY:
            results = self._apply_diversity_ranking(results, diversity_preference)
        elif algorithm == DiscoveryAlgorithm.EMERGENT:
            results = self._apply_emergent_ranking(results)
        
        return results[:limit]
    
    async def _analyze_user_intent(self, query: str) -> Dict[str, Any]:
        """
        Analyze user query to extract intent, preferences, and constraints.
        
        Extracts:
        - Core topic/question
        - Time preferences (recent, historical, any)
        - Perspective preferences (diverse, mainstream, critical, etc.)
        - Depth preferences (shallow, medium, deep)
        - Domain preferences
        """
        
        if not self.api_key:
            return self._analyze_user_intent_fallback(query)
        
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"intent-{datetime.now().timestamp()}",
                system_message="""You are an expert query analyzer for Thrryv's content discovery engine.
Analyze user queries to extract:
1. Core topic/question they're asking about
2. Time preferences (recent/historical/anytime)
3. Perspective preferences (diverse/mainstream/critical/expert/personal)
4. Depth preferences (surface/medium/deep)
5. Related domains or contexts
6. Key entities or keywords

Respond in JSON format:
{
  "core_topic": "main topic",
  "time_preference": "recent|historical|anytime",
  "perspective_preference": ["diverse", "mainstream", "critical", "expert", "personal"],
  "depth_preference": "surface|medium|deep",
  "related_domains": ["domain1", "domain2"],
  "key_entities": ["entity1", "entity2"],
  "keywords": ["keyword1", "keyword2"],
  "query_analysis": "brief explanation of what user is looking for"
}"""
            ).with_model("openai", "gpt-4o-mini")
            
            response = await chat.send_message(UserMessage(text=f"Query: {query}"))
            
            # Parse JSON response
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Try to extract JSON from response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    result = json.loads(response[start:end])
                    return result
                return self._analyze_user_intent_fallback(query)
        
        except Exception as e:
            logger.error(f"Error analyzing user intent: {e}")
            return self._analyze_user_intent_fallback(query)
    
    def _analyze_user_intent_fallback(self, query: str) -> Dict[str, Any]:
        """Fallback intent analysis using keyword matching"""
        
        query_lower = query.lower()
        
        # Time preferences
        time_pref = "anytime"
        if any(word in query_lower for word in ["recent", "lately", "today", "this week", "new"]):
            time_pref = "recent"
        elif any(word in query_lower for word in ["historical", "history", "past", "old", "ancient", "during"]):
            time_pref = "historical"
        
        # Perspective preferences
        perspective_prefs = []
        if any(word in query_lower for word in ["different", "diverse", "other", "various", "perspectives", "viewpoints"]):
            perspective_prefs.append("diverse")
        if any(word in query_lower for word in ["mainstream", "popular", "common", "consensus"]):
            perspective_prefs.append("mainstream")
        if any(word in query_lower for word in ["critical", "against", "opposition", "disagree"]):
            perspective_prefs.append("critical")
        if any(word in query_lower for word in ["expert", "research", "study", "scientific", "evidence"]):
            perspective_prefs.append("expert")
        
        if not perspective_prefs:
            perspective_prefs = ["diverse", "mainstream"]
        
        # Depth preferences
        depth_pref = "medium"
        if any(word in query_lower for word in ["briefly", "quick", "simple", "basics", "overview"]):
            depth_pref = "surface"
        elif any(word in query_lower for word in ["deep", "detail", "comprehensive", "thorough", "explain"]):
            depth_pref = "deep"
        
        return {
            "core_topic": query,
            "time_preference": time_pref,
            "perspective_preference": perspective_prefs,
            "depth_preference": depth_pref,
            "related_domains": [],
            "key_entities": [],
            "keywords": query.split(),
            "query_analysis": "Analyzed with fallback keyword matching"
        }
    
    async def _calculate_discovery_signals(
        self,
        claim: Dict[str, Any],
        user_intent: Dict[str, Any],
        user_standing: float,
        diversity_preference: float
    ) -> DiscoverySignals:
        """
        Calculate discovery signals for a single claim.
        
        Signals include:
        - Relevance to user query
        - Perspective diversity score
        - Originality indicator
        - Engagement quality
        - Author standing impact
        - Recency weight
        - Clarity signals
        """
        
        # Relevance score (0-100)
        relevance = await self._calculate_relevance(claim, user_intent)
        
        # Diversity score (0-100)
        diversity = self._calculate_diversity_score(claim, user_intent)
        
        # Originality score (0-100)
        originality = claim.get('originality_score', 50.0)
        
        # Engagement quality (based on quality of annotations, not just count)
        engagement_quality = self._calculate_engagement_quality(claim)
        
        # Author standing (normalized to 0-100)
        author_standing = min(100, claim.get('author_standing', 1.0) * 20)
        
        # Recency weight
        created_at = claim.get('created_at')
        recency = self._calculate_recency_weight(created_at, user_intent)
        
        # Clarity signal
        clarity = claim.get('clarity_score', 50.0)
        
        return DiscoverySignals(
            relevance_score=relevance,
            diversity_score=diversity,
            originality_score=originality,
            engagement_quality=engagement_quality,
            author_standing=author_standing,
            recency_weight=recency,
            clarity_signal=clarity
        )
    
    async def _calculate_relevance(
        self,
        claim: Dict[str, Any],
        user_intent: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score (0-100).
        
        Considers:
        - Keyword match
        - Domain match
        - Entity match
        - Semantic similarity
        """
        
        keywords = set(user_intent.get('keywords', []))
        claim_text_lower = claim['text'].lower()
        
        # Simple keyword matching
        keyword_matches = sum(1 for kw in keywords if kw.lower() in claim_text_lower)
        keyword_score = min(100, (keyword_matches / max(len(keywords), 1)) * 100)
        
        # Domain match
        domain_match_score = 70.0
        if user_intent.get('related_domains'):
            claim_domain = claim.get('domain', '')
            if claim_domain in user_intent.get('related_domains', []):
                domain_match_score = 100.0
            else:
                domain_match_score = 40.0
        
        # Entity match
        entity_match_score = 50.0
        claim_text_words = set(claim_text_lower.split())
        entity_matches = sum(
            1 for entity in user_intent.get('key_entities', [])
            if entity.lower() in claim_text_words
        )
        if user_intent.get('key_entities'):
            entity_match_score = min(100, (entity_matches / len(user_intent['key_entities'])) * 100)
        
        # Composite relevance
        relevance = (keyword_score * 0.4) + (domain_match_score * 0.35) + (entity_match_score * 0.25)
        return min(100, max(0, relevance))
    
    def _calculate_diversity_score(
        self,
        claim: Dict[str, Any],
        user_intent: Dict[str, Any]
    ) -> float:
        """
        Calculate diversity score (0-100).
        
        Scores perspectives that differ from mainstream consensus.
        """
        
        perspective_prefs = user_intent.get('perspective_preference', [])
        claim_perspective = claim.get('perspective_type', 'neutral')
        
        # Base score
        base_score = 50.0
        
        # Boost for diverse perspectives if requested
        if 'diverse' in perspective_prefs:
            if claim_perspective not in ['mainstream', 'consensus']:
                base_score = 80.0
        
        # Boost for expert perspectives if requested
        if 'expert' in perspective_prefs:
            if claim.get('has_citations', False) or claim.get('sources', []):
                base_score = min(100, base_score + 20)
        
        # Consider annotation patterns (diverse views)
        annotation_diversity = claim.get('annotation_diversity_score', 50.0)
        
        return (base_score * 0.6) + (annotation_diversity * 0.4)
    
    def _calculate_engagement_quality(self, claim: Dict[str, Any]) -> float:
        """
        Calculate engagement quality score (0-100).
        
        Based on:
        - Ratio of quality annotations
        - Citation/source presence
        - Helpful votes vs controversial votes
        """
        
        annotation_count = claim.get('annotation_count', 0)
        helpful_votes = claim.get('helpful_votes_total', 0)
        controversial_votes = claim.get('controversial_votes_total', 0)
        has_sources = len(claim.get('sources', [])) > 0
        
        if annotation_count == 0:
            # New content - low engagement quality by default
            return 40.0 if not has_sources else 55.0
        
        # Quality ratio
        quality_ratio = helpful_votes / max(annotation_count, 1)
        
        # Source presence boost
        source_boost = 15.0 if has_sources else 0.0
        
        # Controversial metric (reduces quality)
        controversy_penalty = min(30, controversial_votes * 2)
        
        score = (quality_ratio * 70) + source_boost - controversy_penalty
        return min(100, max(0, score))
    
    def _calculate_recency_weight(
        self,
        created_at: Optional[str],
        user_intent: Dict[str, Any]
    ) -> float:
        """
        Calculate recency weight (0-100).
        
        Time preferences affect weighting.
        """
        
        time_pref = user_intent.get('time_preference', 'anytime')
        
        if not created_at:
            return 50.0
        
        try:
            from datetime import datetime, timezone
            
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            age_hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600
            
            if time_pref == 'recent':
                # Heavily favor recent content
                if age_hours < 24:
                    return 100.0
                elif age_hours < 168:  # 1 week
                    return 80.0 - (age_hours / 168 * 20)
                else:
                    return 40.0
            elif time_pref == 'historical':
                # Prefer older, established content
                if age_hours > 30 * 24:  # 30 days
                    return 100.0 - min(50, age_hours / (365 * 24) * 50)
                else:
                    return 50.0
            else:
                # 'anytime' - slight recency boost
                return 100.0 - min(50, age_hours / (365 * 24) * 50)
        
        except Exception as e:
            logger.warning(f"Error calculating recency: {e}")
            return 50.0
    
    def _calculate_composite_score(
        self,
        signals: DiscoverySignals,
        algorithm: DiscoveryAlgorithm,
        diversity_preference: float
    ) -> float:
        """
        Calculate composite discovery score based on signals and algorithm.
        
        Different algorithms weight signals differently.
        """
        
        if algorithm == DiscoveryAlgorithm.RELEVANCE:
            # Heavy emphasis on relevance
            return (
                signals.relevance_score * 0.5 +
                signals.engagement_quality * 0.2 +
                signals.clarity_signal * 0.15 +
                signals.originality_score * 0.1 +
                signals.recency_weight * 0.05
            )
        
        elif algorithm == DiscoveryAlgorithm.DIVERSITY:
            # Emphasize diverse perspectives
            return (
                signals.diversity_score * 0.4 +
                signals.relevance_score * 0.35 +
                signals.engagement_quality * 0.15 +
                signals.originality_score * 0.1
            )
        
        elif algorithm == DiscoveryAlgorithm.EMERGENT:
            # Favor new, original content
            return (
                signals.originality_score * 0.4 +
                signals.recency_weight * 0.25 +
                signals.relevance_score * 0.2 +
                signals.clarity_signal * 0.15
            )
        
        elif algorithm == DiscoveryAlgorithm.STANDING_AWARE:
            # Boost by author standing
            return (
                signals.relevance_score * 0.35 +
                signals.author_standing * 0.3 +
                signals.engagement_quality * 0.2 +
                signals.originality_score * 0.1 +
                signals.diversity_score * 0.05
            )
        
        return signals.relevance_score
    
    def _apply_standing_aware_ranking(self, results: List[DiscoveryResult]) -> List[DiscoveryResult]:
        """Apply standing-aware ranking adjustments"""
        
        # Probabilistically boost high-standing authors
        for result in results:
            # Soft boost - don't completely override relevance
            standing_boost = (result.author_standing / 100) * 15
            result.composite_score += standing_boost
        
        results.sort(key=lambda x: x.composite_score, reverse=True)
        return results
    
    def _apply_diversity_ranking(
        self,
        results: List[DiscoveryResult],
        diversity_preference: float
    ) -> List[DiscoveryResult]:
        """Apply diversity-aware ranking"""
        
        # Spread out similar perspectives
        perspective_counts = {}
        for result in results:
            ptype = result.perspective_type
            perspective_counts[ptype] = perspective_counts.get(ptype, 0) + 1
        
        # Reduce score for overrepresented perspectives
        for result in results:
            penalty = (perspective_counts[result.perspective_type] - 1) * 5 * diversity_preference
            result.composite_score -= penalty
        
        results.sort(key=lambda x: x.composite_score, reverse=True)
        return results
    
    def _apply_emergent_ranking(self, results: List[DiscoveryResult]) -> List[DiscoveryResult]:
        """Apply emergent content ranking"""
        
        # Further boost novelty
        for result in results:
            novelty_boost = (result.signals.originality_score / 100) * 20
            result.composite_score += novelty_boost
        
        results.sort(key=lambda x: x.composite_score, reverse=True)
        return results
    
    def _extract_diversity_indicators(self, claim: Dict[str, Any]) -> List[str]:
        """Extract diversity indicators from claim"""
        
        indicators = []
        
        if claim.get('perspective_type') == 'contrarian':
            indicators.append("contrarian_view")
        
        if claim.get('perspective_type') == 'emerging':
            indicators.append("emerging_perspective")
        
        if claim.get('has_citations', False):
            indicators.append("evidence_based")
        
        if claim.get('annotation_diversity_score', 0) > 70:
            indicators.append("diverse_discussion")
        
        return indicators
