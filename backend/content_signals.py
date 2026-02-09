"""
Content Signals & Improvement Feedback System for Thrryv

This module generates AI-powered feedback on content quality, clarity, and signals
WITHOUT labeling content as true/false. Instead, it highlights:
- Clarity of expression
- Presence (or absence) of context
- Strength of supporting signals
- Potential improvements
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class ClaritySignal:
    """Signal about content clarity"""
    score: float  # 0-100
    strengths: List[str]
    areas_for_improvement: List[str]
    actionable_suggestions: List[str]


@dataclass
class ContextSignal:
    """Signal about context presence"""
    score: float  # 0-100
    has_timeframe: bool
    has_location: bool
    has_sources: bool
    has_definitions: bool
    has_data: bool
    improvement_suggestions: List[str]


@dataclass
class EvidenceSignal:
    """Signal about supporting evidence/signals"""
    score: float  # 0-100
    has_citations: bool
    citation_count: int
    has_supporting_media: bool
    media_count: int
    has_statistics: bool
    statistic_count: int
    evidence_types: List[str]
    improvement_suggestions: List[str]


@dataclass
class ContentFeedback:
    """Complete AI-generated feedback for content"""
    claim_id: str
    clarity_signal: ClaritySignal
    context_signal: ContextSignal
    evidence_signal: EvidenceSignal
    overall_quality_score: float  # 0-100
    creator_standing_impact: str  # How this affects standing
    improvement_roadmap: List[str]
    positive_aspects: List[str]
    timestamp: str


class ContentSignalGenerator:
    """
    Generates AI-powered content signals and improvement feedback.
    
    Does NOT judge truth/falsehood.
    Focuses on:
    - Clarity of expression
    - Presence of context
    - Strength of supporting signals
    - How content can be improved
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('EMERGENT_LLM_KEY')
    
    async def generate_feedback(
        self,
        claim: Dict[str, Any],
        annotations: List[Dict[str, Any]] = None,
        sources: List[Dict[str, Any]] = None
    ) -> ContentFeedback:
        """
        Generate comprehensive feedback for a piece of content.
        
        Args:
            claim: The claim/content being analyzed
            annotations: Related annotations/discussion
            sources: Referenced sources or citations
        
        Returns:
            Complete feedback package for creator
        """
        
        # Generate individual signals
        clarity = await self._analyze_clarity(claim)
        context = self._analyze_context(claim, sources)
        evidence = self._analyze_evidence(claim, sources, annotations)
        
        # Calculate overall quality
        overall_score = (clarity.score * 0.35 + context.score * 0.3 + evidence.score * 0.35)
        
        # Determine standing impact
        standing_impact = self._determine_standing_impact(overall_score, clarity, evidence)
        
        # Create improvement roadmap
        roadmap = self._create_improvement_roadmap(clarity, context, evidence)
        
        # Extract positive aspects
        positives = self._extract_positive_aspects(clarity, context, evidence)
        
        return ContentFeedback(
            claim_id=claim.get('id', ''),
            clarity_signal=clarity,
            context_signal=context,
            evidence_signal=evidence,
            overall_quality_score=overall_score,
            creator_standing_impact=standing_impact,
            improvement_roadmap=roadmap,
            positive_aspects=positives,
            timestamp=datetime.now().isoformat()
        )
    
    async def _analyze_clarity(self, claim: Dict[str, Any]) -> ClaritySignal:
        """
        Analyze clarity of expression.
        
        Evaluates:
        - Sentence structure and readability
        - Vocabulary complexity
        - Logical flow
        - Specificity vs vagueness
        - Presence of unclear pronouns or references
        """
        
        if not self.api_key:
            return self._analyze_clarity_fallback(claim)
        
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"clarity-{datetime.now().timestamp()}",
                system_message="""You are an expert content clarity analyst for Thrryv.
Analyze the clarity of the provided content. DO NOT judge if it's true or false.

Evaluate:
1. Sentence structure and readability (0-100)
2. Vocabulary complexity and appropriateness (0-100)
3. Logical flow and organization (0-100)
4. Specificity of claims (vague vs specific) (0-100)
5. Clarity of pronouns and references (0-100)

Provide:
- 2-3 specific strengths
- 2-3 areas that could be clearer
- 3-5 actionable suggestions for improvement

Respond in JSON:
{
  "score": <average of above scores>,
  "strengths": ["strength1", "strength2"],
  "areas_for_improvement": ["area1", "area2"],
  "actionable_suggestions": ["suggestion1", "suggestion2", "suggestion3"]
}"""
            ).with_model("openai", "gpt-4o-mini")
            
            claim_text = claim.get('text', '')
            response = await chat.send_message(UserMessage(text=f"Analyze clarity: {claim_text}"))
            
            result = self._parse_json_response(response)
            if result:
                return ClaritySignal(
                    score=min(100, max(0, result.get('score', 50))),
                    strengths=result.get('strengths', []),
                    areas_for_improvement=result.get('areas_for_improvement', []),
                    actionable_suggestions=result.get('actionable_suggestions', [])
                )
        
        except Exception as e:
            logger.error(f"Error analyzing clarity: {e}")
        
        return self._analyze_clarity_fallback(claim)
    
    def _analyze_clarity_fallback(self, claim: Dict[str, Any]) -> ClaritySignal:
        """Fallback clarity analysis"""
        
        text = claim.get('text', '').strip()
        
        # Simple heuristics
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        words = text.split()
        
        # Sentence length average
        avg_sentence_length = len(words) / max(len(sentences), 1)
        
        # Clarity heuristics
        strengths = []
        areas = []
        suggestions = []
        
        # Positive signals
        if len(words) > 20:
            strengths.append("Sufficient detail provided")
        
        if any(word in text.lower() for word in ["specifically", "exactly", "precisely", "clearly"]):
            strengths.append("Uses specific language")
        
        # Areas for improvement
        if avg_sentence_length > 25:
            areas.append("Some sentences are quite long")
            suggestions.append("Consider breaking longer sentences into shorter, more focused statements")
        
        if text.count('?') > 3:
            areas.append("Many questions may reduce clarity")
        
        if len(words) < 15:
            areas.append("Content is quite brief")
            suggestions.append("Add more detail and specific examples")
        
        # Fallback suggestions
        if not suggestions:
            suggestions.append("Review for unclear pronouns or references")
            suggestions.append("Consider adding examples to support main points")
        
        score = 60.0
        if len(strengths) > 0:
            score += 10
        if len(areas) == 0:
            score += 10
        
        return ClaritySignal(
            score=min(100, score),
            strengths=strengths or ["Content is understandable"],
            areas_for_improvement=areas or ["No major clarity issues detected"],
            actionable_suggestions=suggestions
        )
    
    def _analyze_context(
        self,
        claim: Dict[str, Any],
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> ContextSignal:
        """
        Analyze presence of context in content.
        
        Checks for:
        - Timeframe/when
        - Location/where
        - Sources/references
        - Definitions of key terms
        - Data/numbers
        """
        
        text = claim.get('text', '').lower()
        
        # Detect context elements
        has_timeframe = any(
            word in text for word in [
                'in 20', 'during', 'when', 'after', 'before', 'recent', 'historical',
                'yesterday', 'today', 'tomorrow', 'year', 'month', 'week', 'day'
            ]
        )
        
        has_location = any(
            word in text for word in [
                'in ', 'at ', 'from ', 'near ', 'city', 'country', 'region', 'state',
                'place', 'location', 'area', 'zone'
            ]
        )
        
        has_sources = len(sources or []) > 0 or any(
            word in text for word in ['source', 'research', 'study', 'report', 'said', 'according']
        )
        
        has_definitions = any(
            word in text for word in ['means', 'is', 'defined as', 'definition', 'refers to']
        )
        
        has_statistics = any(
            char in text for char in ['%', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        )
        
        suggestions = []
        
        if not has_timeframe:
            suggestions.append("Specify when this applies or occurred")
        
        if not has_location:
            suggestions.append("Mention geographic scope or specific location")
        
        if not has_sources:
            suggestions.append("Reference sources or cite supporting information")
        
        if not has_definitions:
            suggestions.append("Define key terms for clarity")
        
        if not has_statistics and "claim" in text:
            suggestions.append("Include relevant data or statistics where applicable")
        
        # Calculate context score
        context_elements = sum([has_timeframe, has_location, has_sources, has_definitions, has_statistics])
        score = (context_elements / 5) * 100
        
        return ContextSignal(
            score=score,
            has_timeframe=has_timeframe,
            has_location=has_location,
            has_sources=has_sources,
            has_definitions=has_definitions,
            has_data=has_statistics,
            improvement_suggestions=suggestions
        )
    
    def _analyze_evidence(
        self,
        claim: Dict[str, Any],
        sources: Optional[List[Dict[str, Any]]] = None,
        annotations: Optional[List[Dict[str, Any]]] = None
    ) -> EvidenceSignal:
        """
        Analyze strength of supporting signals.
        
        Evaluates:
        - Citation presence and count
        - Supporting media
        - Statistics/data
        - Type of evidence
        """
        
        sources = sources or []
        annotations = annotations or []
        
        # Count citation indicators in text
        text = claim.get('text', '').lower()
        citations_mentioned = text.count('source') + text.count('study') + text.count('research')
        
        # Detect media
        media = claim.get('media', [])
        
        # Detect statistics
        stats_count = text.count('%') + text.count('million') + text.count('billion')
        
        # Evidence types
        evidence_types = []
        if sources:
            evidence_types.append("cited_sources")
        if media:
            evidence_types.append("supporting_media")
        if stats_count > 0:
            evidence_types.append("statistical_data")
        if annotations and any(a.get('annotation_type') == 'support' for a in annotations):
            evidence_types.append("community_support")
        
        # Calculate score
        has_citations = len(sources) > 0
        has_media = len(media) > 0
        has_stats = stats_count > 0
        
        evidence_score = 0
        if has_citations:
            evidence_score += 40
        if has_media:
            evidence_score += 30
        if has_stats:
            evidence_score += 30
        
        suggestions = []
        if not has_citations:
            suggestions.append("Add citations or references to support claims")
        if not has_media:
            suggestions.append("Consider adding supporting images or videos")
        if not has_stats:
            suggestions.append("Include relevant statistics or data")
        
        return EvidenceSignal(
            score=min(100, evidence_score),
            has_citations=has_citations,
            citation_count=len(sources),
            has_supporting_media=has_media,
            media_count=len(media),
            has_statistics=has_stats,
            statistic_count=stats_count,
            evidence_types=evidence_types,
            improvement_suggestions=suggestions
        )
    
    def _determine_standing_impact(
        self,
        quality_score: float,
        clarity: ClaritySignal,
        evidence: EvidenceSignal
    ) -> str:
        """
        Determine how content quality affects creator standing.
        
        Returns descriptive impact message.
        """
        
        if quality_score >= 80:
            return "High-quality contribution: Standing boost earned for clear, well-sourced content"
        elif quality_score >= 60:
            return "Good quality: Standing improvement expected as community engages with content"
        elif quality_score >= 40:
            return "Fair quality: Neutral standing impact; improvements could increase visibility"
        else:
            return "Low quality: No standing adjustment; focus on clarity and sources to improve"
    
    def _create_improvement_roadmap(
        self,
        clarity: ClaritySignal,
        context: ContextSignal,
        evidence: EvidenceSignal
    ) -> List[str]:
        """Create actionable improvement steps"""
        
        roadmap = []
        
        # Priority 1: Add evidence
        if evidence.score < 60:
            roadmap.append("Priority 1: Strengthen evidence - add citations, data, or supporting media")
        
        # Priority 2: Improve clarity
        if clarity.score < 70:
            roadmap.append("Priority 2: Enhance clarity - simplify language and improve sentence structure")
        
        # Priority 3: Add context
        if context.score < 70:
            roadmap.append("Priority 3: Add context - specify time, place, and relevant definitions")
        
        # General improvements
        if not roadmap:
            roadmap.append("Content quality is good - minor refinements could increase engagement")
        
        roadmap.append("Monitor annotations - respond to questions and engage with community discussion")
        roadmap.append("Update if new information becomes available")
        
        return roadmap
    
    def _extract_positive_aspects(
        self,
        clarity: ClaritySignal,
        context: ContextSignal,
        evidence: EvidenceSignal
    ) -> List[str]:
        """Extract positive aspects of content"""
        
        positives = []
        
        if clarity.score >= 75:
            positives.append("Well-expressed and easy to understand")
        
        if context.score >= 75:
            positives.append("Good contextual information provided")
        
        if evidence.score >= 75:
            positives.append("Strong supporting evidence and sources")
        
        positives.extend([
            s for s in clarity.strengths if s
        ][:2])
        
        if not positives:
            positives.append("Content contributes to community discussion")
        
        return positives
    
    @staticmethod
    def _parse_json_response(response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response"""
        
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
