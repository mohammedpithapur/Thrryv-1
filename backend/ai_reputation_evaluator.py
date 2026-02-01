"""
AI Baseline Reputation Evaluator for Thrryv

This module evaluates user-generated content at publish time and assigns
a conservative, non-punitive baseline reputation boost based on the
informational value of the content.

Key Principles:
- ONLY awards positive reputation boosts (+5.0 to +15.0)
- NEVER decreases reputation for low-value or neutral content
- Does NOT determine truth or correctness
- Does NOT predict long-term accuracy
- Separate from community-driven annotation system
"""

import os
import base64
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent, FileContentWithMimeType


class ContentType(Enum):
    TEXT_ONLY = "text_only"
    IMAGE = "image"
    VIDEO = "video"
    MIXED = "mixed"


@dataclass
class EvaluationResult:
    """Result of the AI baseline reputation evaluation"""
    reputation_boost: float  # 0.0 (no boost) to 15.0 (max boost)
    clarity_score: float  # 0-100
    originality_score: float  # 0-100
    relevance_score: float  # 0-100
    effort_score: float  # 0-100
    evidentiary_value_score: float  # 0-100
    media_value_score: Optional[float]  # 0-100, only for media posts
    evaluation_summary: str  # Human-readable summary
    content_type: ContentType
    qualifies_for_boost: bool  # Whether content meets threshold


class AIReputationEvaluator:
    """
    AI-powered content evaluator that assesses the informational value
    of posts at publish time and awards baseline reputation boosts.
    """
    
    MIN_BOOST = 5.0
    MAX_BOOST = 15.0
    BOOST_THRESHOLD = 50.0  # Minimum average score to qualify for boost
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment")
    
    def _get_text_chat(self, session_id: str) -> LlmChat:
        """Get a chat instance for text analysis using GPT-5.2"""
        return LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=self._get_text_system_prompt()
        ).with_model("openai", "gpt-5.2")
    
    def _get_vision_chat(self, session_id: str) -> LlmChat:
        """Get a chat instance for image/video analysis using GPT-5.2 vision"""
        return LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=self._get_media_system_prompt()
        ).with_model("openai", "gpt-5.2")
    
    def _get_gemini_chat(self, session_id: str) -> LlmChat:
        """Get a Gemini chat instance for additional media analysis"""
        return LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=self._get_media_system_prompt()
        ).with_model("gemini", "gemini-2.5-flash")
    
    def _get_text_system_prompt(self) -> str:
        return """You are an AI content evaluator for Thrryv, a fact-checking platform. 
Your role is to assess the INFORMATIONAL VALUE of user posts at publish time.

IMPORTANT RULES:
1. You do NOT determine truth or correctness of claims
2. You do NOT predict whether claims will be proven true/false later
3. You ONLY evaluate the quality and value of the content contribution
4. You are generous but fair - reward genuine effort and value

Evaluate content on these criteria (score 0-100 each):

1. CLARITY (0-100): How clearly is the claim/information presented?
   - Well-structured sentences
   - Unambiguous language
   - Easy to understand

2. ORIGINALITY (0-100): Does this add new information or perspective?
   - Novel claims or insights
   - Unique angles on topics
   - Not just repeating common knowledge

3. RELEVANCE (0-100): Is the content meaningful and topical?
   - Addresses real-world topics
   - Has potential impact
   - Timely or evergreen importance

4. EFFORT (0-100): Does the post show thoughtful effort?
   - Detailed explanation
   - Proper context provided
   - Shows research or thought

5. EVIDENTIARY VALUE (0-100): Does content provide verifiable information?
   - Specific facts that can be checked
   - References to sources (even if not linked)
   - Concrete details rather than vague claims

Respond ONLY in this JSON format:
{
  "clarity_score": <0-100>,
  "originality_score": <0-100>,
  "relevance_score": <0-100>,
  "effort_score": <0-100>,
  "evidentiary_value_score": <0-100>,
  "summary": "<1-2 sentence summary of evaluation>"
}"""

    def _get_media_system_prompt(self) -> str:
        return """You are an AI media evaluator for Thrryv, a fact-checking platform.
Your role is to assess whether images or videos ADD MEANINGFUL VALUE to a claim.

IMPORTANT RULES:
1. You do NOT determine if the media proves anything true/false
2. You ONLY evaluate if the media meaningfully supports understanding
3. Distinguish between informative media vs decoration/engagement bait

Evaluate media on INFORMATIONAL VALUE (score 0-100):

HIGH VALUE (70-100):
- Screenshots of primary sources
- Documentary evidence
- Data visualizations
- Relevant photographs that illustrate the claim
- Video evidence of events being discussed

MEDIUM VALUE (40-69):
- Contextual images that help understanding
- Relevant stock photos that illustrate concepts
- Diagrams or explanatory visuals

LOW VALUE (0-39):
- Generic stock photos unrelated to claim
- Memes or engagement bait
- Decorative images with no informational purpose
- Blurry or unclear media
- Irrelevant content

Respond ONLY in this JSON format:
{
  "media_value_score": <0-100>,
  "media_type": "<screenshot|document|photo|video|diagram|stock|meme|other>",
  "adds_information": <true|false>,
  "summary": "<1 sentence description of media value>"
}"""

    async def evaluate_text_content(self, text: str, domain: str = "") -> Dict[str, Any]:
        """Evaluate text-only content"""
        import uuid
        session_id = f"eval-text-{uuid.uuid4().hex[:8]}"
        
        chat = self._get_text_chat(session_id)
        
        prompt = f"""Evaluate this claim/post for informational value:

DOMAIN: {domain if domain else "General"}
CONTENT: {text}

Remember: Do NOT judge truth/correctness. Only assess content quality and value."""

        try:
            response = await chat.send_message(UserMessage(text=prompt))
            return self._parse_text_response(response)
        except Exception as e:
            print(f"Text evaluation error: {e}")
            return self._default_text_scores()
    
    async def evaluate_media_content(
        self, 
        media_data: bytes, 
        media_type: str,
        claim_text: str = ""
    ) -> Dict[str, Any]:
        """Evaluate image or video frame content"""
        import uuid
        session_id = f"eval-media-{uuid.uuid4().hex[:8]}"
        
        # Use GPT-5.2 vision for primary analysis
        chat = self._get_vision_chat(session_id)
        
        # Convert to base64
        media_base64 = base64.b64encode(media_data).decode('utf-8')
        
        prompt = f"""Evaluate this media for informational value in the context of a fact-checking post.

CLAIM CONTEXT: {claim_text if claim_text else "No text provided"}

Does this media add meaningful information or is it just decoration?"""

        try:
            image_content = ImageContent(image_base64=media_base64)
            response = await chat.send_message(UserMessage(
                text=prompt,
                file_contents=[image_content]
            ))
            return self._parse_media_response(response)
        except Exception as e:
            print(f"Media evaluation error with OpenAI: {e}")
            # Fallback to Gemini
            try:
                gemini_chat = self._get_gemini_chat(f"eval-media-gemini-{uuid.uuid4().hex[:8]}")
                image_content = ImageContent(image_base64=media_base64)
                response = await gemini_chat.send_message(UserMessage(
                    text=prompt,
                    file_contents=[image_content]
                ))
                return self._parse_media_response(response)
            except Exception as e2:
                print(f"Media evaluation error with Gemini fallback: {e2}")
                return self._default_media_scores()
    
    async def evaluate_post(
        self,
        text: str,
        domain: str = "",
        media_files: List[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Main evaluation method - evaluates a complete post with text and optional media.
        
        Args:
            text: The claim/post text
            domain: The topic domain (e.g., "Science", "Politics")
            media_files: List of dicts with 'data' (bytes) and 'type' (mime type)
        
        Returns:
            EvaluationResult with scores and reputation boost
        """
        media_files = media_files or []
        
        # Determine content type
        has_media = len(media_files) > 0
        has_video = any('video' in m.get('type', '') for m in media_files)
        
        if not has_media:
            content_type = ContentType.TEXT_ONLY
        elif has_video:
            content_type = ContentType.VIDEO
        elif len(media_files) > 0 and text.strip():
            content_type = ContentType.MIXED
        else:
            content_type = ContentType.IMAGE
        
        # Evaluate text content
        text_scores = await self.evaluate_text_content(text, domain)
        
        # Evaluate media if present
        media_score = None
        if has_media:
            # Evaluate first media file (primary evidence)
            first_media = media_files[0]
            media_result = await self.evaluate_media_content(
                first_media['data'],
                first_media['type'],
                text
            )
            media_score = media_result.get('media_value_score', 0)
        
        # Calculate overall scores
        clarity = text_scores.get('clarity_score', 50)
        originality = text_scores.get('originality_score', 50)
        relevance = text_scores.get('relevance_score', 50)
        effort = text_scores.get('effort_score', 50)
        evidentiary = text_scores.get('evidentiary_value_score', 50)
        
        # Calculate average score
        if media_score is not None:
            all_scores = [clarity, originality, relevance, effort, evidentiary, media_score]
        else:
            all_scores = [clarity, originality, relevance, effort, evidentiary]
        
        avg_score = sum(all_scores) / len(all_scores)
        
        # Determine if content qualifies for boost
        qualifies = avg_score >= self.BOOST_THRESHOLD
        
        # Calculate reputation boost (0 if doesn't qualify, scaled 5-15 if does)
        if qualifies:
            # Scale from BOOST_THRESHOLD-100 to MIN_BOOST-MAX_BOOST
            score_range = 100 - self.BOOST_THRESHOLD
            boost_range = self.MAX_BOOST - self.MIN_BOOST
            normalized = (avg_score - self.BOOST_THRESHOLD) / score_range
            reputation_boost = self.MIN_BOOST + (normalized * boost_range)
            reputation_boost = min(max(reputation_boost, self.MIN_BOOST), self.MAX_BOOST)
        else:
            reputation_boost = 0.0
        
        # Generate summary
        summary = self._generate_summary(
            qualifies, reputation_boost, avg_score, 
            text_scores.get('summary', ''), 
            content_type, media_score
        )
        
        return EvaluationResult(
            reputation_boost=round(reputation_boost, 2),
            clarity_score=clarity,
            originality_score=originality,
            relevance_score=relevance,
            effort_score=effort,
            evidentiary_value_score=evidentiary,
            media_value_score=media_score,
            evaluation_summary=summary,
            content_type=content_type,
            qualifies_for_boost=qualifies
        )
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """Parse the JSON response from text evaluation"""
        import json
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith('```'):
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]
            return json.loads(response)
        except:
            return self._default_text_scores()
    
    def _parse_media_response(self, response: str) -> Dict[str, Any]:
        """Parse the JSON response from media evaluation"""
        import json
        try:
            response = response.strip()
            if response.startswith('```'):
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]
            return json.loads(response)
        except:
            return self._default_media_scores()
    
    def _default_text_scores(self) -> Dict[str, Any]:
        """Return neutral default scores when evaluation fails"""
        return {
            'clarity_score': 50,
            'originality_score': 50,
            'relevance_score': 50,
            'effort_score': 50,
            'evidentiary_value_score': 50,
            'summary': 'Automated evaluation unavailable'
        }
    
    def _default_media_scores(self) -> Dict[str, Any]:
        """Return neutral default scores for media when evaluation fails"""
        return {
            'media_value_score': 50,
            'media_type': 'unknown',
            'adds_information': True,
            'summary': 'Media evaluation unavailable'
        }
    
    def _generate_summary(
        self, 
        qualifies: bool, 
        boost: float, 
        avg_score: float,
        text_summary: str,
        content_type: ContentType,
        media_score: Optional[float]
    ) -> str:
        """Generate a human-readable evaluation summary"""
        if not qualifies:
            return f"Content evaluated (avg score: {avg_score:.1f}/100). No baseline boost applied - content meets platform standards but doesn't exceed value threshold for reputation reward."
        
        boost_level = "modest" if boost < 8 else "good" if boost < 12 else "excellent"
        media_note = ""
        if media_score is not None:
            media_quality = "high" if media_score >= 70 else "moderate" if media_score >= 40 else "limited"
            media_note = f" Media provides {media_quality} informational value."
        
        return f"Content adds clear value to the platform. {boost_level.capitalize()} baseline reputation boost of +{boost:.1f} awarded.{media_note} {text_summary}"


# Singleton instance for use in the application
_evaluator_instance = None

def get_evaluator() -> AIReputationEvaluator:
    """Get or create the singleton evaluator instance"""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = AIReputationEvaluator()
    return _evaluator_instance


async def evaluate_claim_for_reputation(
    text: str,
    domain: str = "",
    media_files: List[Dict[str, Any]] = None
) -> EvaluationResult:
    """
    Convenience function to evaluate a claim and get reputation boost.
    
    This is the main entry point for the claim creation flow.
    """
    evaluator = get_evaluator()
    return await evaluator.evaluate_post(text, domain, media_files)
