"""
Hierarchical AI-Powered Content Categorization System for Thrryv

This module provides intelligent, multi-level categorization for all content types
(text, images, videos, mixed media) using semantic and contextual analysis.

Key Features:
- Hierarchical taxonomy: Broad Domain → Category → Subcategory → Specific
- Multi-label support where appropriate
- No generic fallbacks like "General" or "Other"
- Handles informal content: memes, satire, cultural references
- Transparent categorization with reasoning
- Adaptable to emerging domains and formats
"""

import os
import base64
import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent


@dataclass
class CategoryPath:
    """Represents a single category path in the hierarchy"""
    path: List[str]  # e.g., ["Science", "Space Exploration", "Mars Missions", "Rover Data"]
    confidence: float
    reasoning: str
    
    @property
    def full_path(self) -> str:
        return " → ".join(self.path)
    
    @property
    def primary_domain(self) -> str:
        return self.path[0] if self.path else "Uncategorized"
    
    @property
    def depth(self) -> int:
        return len(self.path)


@dataclass
class ContentCategorizationResult:
    """Complete categorization result for a piece of content"""
    primary_category: CategoryPath
    secondary_categories: List[CategoryPath]  # Additional relevant categories
    content_type: str  # text, image, video, mixed
    content_format: str  # claim, meme, news, opinion, satire, documentary, etc.
    is_informal: bool  # memes, jokes, cultural references
    cultural_context: Optional[str]  # Additional context for cultural content
    taxonomy_version: str = "1.0"


class HierarchicalCategorizer:
    """
    AI-powered content categorizer that assigns precise, hierarchical categories
    to any content type using semantic and contextual analysis.
    """
    
    TAXONOMY_VERSION = "1.0"
    
    # Master taxonomy - broad domains with example subcategories
    TAXONOMY = {
        "Science & Technology": {
            "subcategories": [
                "Space Exploration", "Climate Science", "Biology & Medicine", 
                "Physics & Chemistry", "Artificial Intelligence", "Computing",
                "Engineering", "Mathematics", "Environmental Science",
                "Neuroscience", "Genetics", "Quantum Physics"
            ]
        },
        "Politics & Government": {
            "subcategories": [
                "Elections", "Policy & Legislation", "International Relations",
                "Political Figures", "Democracy & Governance", "Political Movements",
                "Human Rights", "Military & Defense", "Political Satire"
            ]
        },
        "Economics & Business": {
            "subcategories": [
                "Markets & Finance", "Cryptocurrency", "Startups & Entrepreneurship",
                "Corporate News", "Trade & Commerce", "Economic Policy",
                "Personal Finance", "Real Estate", "Employment"
            ]
        },
        "Health & Wellness": {
            "subcategories": [
                "Medical Research", "Mental Health", "Nutrition & Diet",
                "Fitness & Exercise", "Public Health", "Diseases & Conditions",
                "Healthcare Systems", "Alternative Medicine", "Pharmaceuticals"
            ]
        },
        "Society & Culture": {
            "subcategories": [
                "Social Issues", "Demographics", "Religion & Spirituality",
                "Education", "Family & Relationships", "LGBTQ+ Issues",
                "Racial & Ethnic Topics", "Gender Issues", "Generational Topics"
            ]
        },
        "Entertainment & Media": {
            "subcategories": [
                "Film & Television", "Music", "Gaming", "Streaming Platforms",
                "Celebrity News", "Award Shows", "Theater & Performing Arts",
                "Books & Literature", "Podcasts"
            ]
        },
        "Sports & Athletics": {
            "subcategories": [
                "Football/Soccer", "American Football", "Basketball", "Cricket",
                "Tennis", "Olympics", "Combat Sports", "Motorsports",
                "Esports", "Team Rivalries", "Sports Records"
            ]
        },
        "Internet Culture": {
            "subcategories": [
                "Memes & Viral Content", "Social Media Trends", "Online Communities",
                "Influencer Culture", "Digital Art & NFTs", "Internet History",
                "Platform-Specific Culture", "Copypasta & Jokes", "Reaction Images"
            ]
        },
        "History & Heritage": {
            "subcategories": [
                "Ancient History", "Medieval Period", "Modern History",
                "World Wars", "Cultural Heritage", "Archaeological Discoveries",
                "Historical Figures", "Historical Myths & Facts"
            ]
        },
        "Geography & Travel": {
            "subcategories": [
                "Countries & Regions", "Cities & Urban Life", "Natural Landmarks",
                "Travel & Tourism", "Maps & Cartography", "Geopolitics",
                "Local Culture", "Migration & Diaspora"
            ]
        },
        "Food & Cuisine": {
            "subcategories": [
                "Recipes & Cooking", "Restaurant Industry", "Food Science",
                "Regional Cuisines", "Food History", "Dietary Movements",
                "Food Safety", "Beverages", "Food Culture"
            ]
        },
        "Environment & Nature": {
            "subcategories": [
                "Climate Change", "Wildlife & Conservation", "Sustainability",
                "Natural Disasters", "Renewable Energy", "Pollution",
                "Ecosystems", "Environmental Policy"
            ]
        },
        "Law & Justice": {
            "subcategories": [
                "Court Cases", "Criminal Justice", "Civil Rights",
                "International Law", "Legal Precedents", "Law Enforcement",
                "Corporate Law", "Privacy & Data Rights"
            ]
        },
        "Pop Culture": {
            "subcategories": [
                "Fan Communities", "Merchandise & Collectibles", "Cosplay",
                "Fan Theories", "Nostalgia", "Pop Culture References",
                "Crossover Content", "Parodies & Tributes"
            ]
        }
    }
    
    # Content format identifiers
    CONTENT_FORMATS = [
        "factual_claim", "news_report", "opinion_piece", "analysis",
        "meme", "satire", "parody", "joke", "screenshot", "quote",
        "documentary_evidence", "personal_story", "announcement",
        "question", "debate_point", "correction", "update"
    ]
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment")
    
    def _get_categorization_chat(self, session_id: str) -> LlmChat:
        """Get a chat instance configured for hierarchical categorization"""
        return LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=self._get_system_prompt()
        ).with_model("openai", "gpt-5.2")
    
    def _get_system_prompt(self) -> str:
        taxonomy_summary = "\n".join([
            f"• {domain}: {', '.join(info['subcategories'][:5])}..."
            for domain, info in self.TAXONOMY.items()
        ])
        
        return f"""You are an expert content categorization AI for Thrryv, a fact-checking platform.
Your task is to analyze content (text, images, videos) and assign PRECISE, HIERARCHICAL categories.

## TAXONOMY STRUCTURE
Categories follow a hierarchy: Domain → Category → Subcategory → Specific Topic
Example: "Science & Technology → Space Exploration → Mars Missions → Perseverance Rover"

## AVAILABLE DOMAINS
{taxonomy_summary}

## CRITICAL RULES
1. NEVER use generic labels like "General", "Other", "Miscellaneous", or "Various"
2. ALWAYS provide the most specific categorization possible
3. For informal content (memes, satire, jokes), still categorize precisely:
   - Meme about politics: "Internet Culture → Memes & Viral Content → Political Memes → Election Humor"
   - Sports joke: "Sports & Athletics → [Sport] → Fan Culture → Matchday Humor"
4. Multi-label is allowed - content can belong to multiple categories
5. Identify the CONTENT FORMAT (meme, satire, factual claim, news, etc.)
6. Note if content has cultural/contextual significance

## CONTENT FORMATS
- factual_claim: A statement presented as fact
- news_report: Reporting on events
- opinion_piece: Subjective viewpoint
- meme: Image/video with humorous intent
- satire: Ironic or exaggerated content
- screenshot: Captured content from elsewhere
- documentary_evidence: Supporting visual evidence
- personal_story: Individual experience
- analysis: In-depth examination

## OUTPUT FORMAT
Respond ONLY with this JSON structure:
{{
  "primary_category": {{
    "path": ["Domain", "Category", "Subcategory", "Specific"],
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation"
  }},
  "secondary_categories": [
    {{
      "path": ["Domain", "Category", "Subcategory"],
      "confidence": 0.0-1.0,
      "reasoning": "Why this also applies"
    }}
  ],
  "content_format": "one of the formats listed",
  "is_informal": true/false,
  "cultural_context": "Any relevant cultural context or null"
}}

Be thorough, precise, and never default to vague categorizations."""

    async def categorize_content(
        self,
        text: str,
        media_files: List[Dict[str, Any]] = None,
        existing_domain: str = None
    ) -> ContentCategorizationResult:
        """
        Categorize content using hierarchical taxonomy.
        
        Args:
            text: The content text
            media_files: List of media files with 'data' (bytes) and 'type' (mime type)
            existing_domain: Optional hint from previous classification
        
        Returns:
            ContentCategorizationResult with full hierarchical categorization
        """
        media_files = media_files or []
        session_id = f"categorize-{uuid.uuid4().hex[:8]}"
        
        chat = self._get_categorization_chat(session_id)
        
        # Determine content type
        has_media = len(media_files) > 0
        has_video = any('video' in m.get('type', '') for m in media_files)
        
        if has_video:
            content_type = "video"
        elif has_media:
            content_type = "mixed" if text.strip() else "image"
        else:
            content_type = "text"
        
        # Build prompt
        prompt = f"""Analyze and categorize this content:

CONTENT TYPE: {content_type}
TEXT: {text}
"""
        
        if existing_domain and existing_domain not in ["Other", "General"]:
            prompt += f"\nPREVIOUS HINT: Content may relate to {existing_domain}"
        
        # Prepare message with media if available
        try:
            if media_files and len(media_files) > 0:
                first_media = media_files[0]
                media_base64 = base64.b64encode(first_media['data']).decode('utf-8')
                message = UserMessage(
                    text=prompt + "\n\n[Media attached - analyze visual content for categorization]",
                    file_contents=[ImageContent(image_base64=media_base64)]
                )
            else:
                message = UserMessage(text=prompt)
            
            response = await chat.send_message(message)
            result = self._parse_response(response, content_type)
            
            logging.info(f"Hierarchical Categorization: {result.primary_category.full_path} "
                        f"(confidence: {result.primary_category.confidence:.2f}, "
                        f"format: {result.content_format})")
            
            return result
            
        except Exception as e:
            logging.error(f"Categorization failed: {e}")
            return self._fallback_categorization(text, content_type)
    
    def _parse_response(self, response: str, content_type: str) -> ContentCategorizationResult:
        """Parse the AI response into a structured result"""
        try:
            response_text = response.strip()
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
            
            data = json.loads(response_text)
            
            primary = data.get('primary_category', {})
            primary_path = primary.get('path', ['Uncategorized'])
            
            # Ensure we have at least 2 levels
            if len(primary_path) < 2:
                primary_path.append("General Topic")
            
            primary_category = CategoryPath(
                path=primary_path,
                confidence=primary.get('confidence', 0.8),
                reasoning=primary.get('reasoning', '')
            )
            
            secondary_categories = []
            for sec in data.get('secondary_categories', []):
                if sec.get('path'):
                    secondary_categories.append(CategoryPath(
                        path=sec['path'],
                        confidence=sec.get('confidence', 0.5),
                        reasoning=sec.get('reasoning', '')
                    ))
            
            return ContentCategorizationResult(
                primary_category=primary_category,
                secondary_categories=secondary_categories,
                content_type=content_type,
                content_format=data.get('content_format', 'factual_claim'),
                is_informal=data.get('is_informal', False),
                cultural_context=data.get('cultural_context')
            )
            
        except Exception as e:
            logging.error(f"Failed to parse categorization response: {e}")
            return self._fallback_categorization("", content_type)
    
    def _fallback_categorization(self, text: str, content_type: str) -> ContentCategorizationResult:
        """Intelligent fallback using keyword analysis - never returns 'General'"""
        text_lower = text.lower()
        
        # Keyword-based domain detection
        domain_keywords = {
            "Science & Technology": ["research", "study", "scientist", "technology", "ai", "space", "nasa", "experiment", "data"],
            "Politics & Government": ["government", "election", "president", "policy", "political", "congress", "vote", "law"],
            "Sports & Athletics": ["game", "match", "player", "team", "championship", "score", "win", "league", "sport"],
            "Entertainment & Media": ["movie", "film", "music", "album", "actor", "celebrity", "show", "netflix", "streaming"],
            "Health & Wellness": ["health", "medical", "disease", "treatment", "doctor", "hospital", "mental", "fitness"],
            "Economics & Business": ["market", "stock", "business", "economy", "company", "financial", "trade", "investment"],
            "Internet Culture": ["meme", "viral", "trend", "social media", "internet", "online", "twitter", "reddit"],
            "History & Heritage": ["history", "historical", "ancient", "century", "war", "civilization", "heritage"],
            "Society & Culture": ["society", "culture", "social", "community", "people", "tradition"],
            "Food & Cuisine": ["food", "recipe", "restaurant", "cooking", "cuisine", "dish", "chef"],
            "Environment & Nature": ["climate", "environment", "nature", "wildlife", "pollution", "sustainability"],
            "Geography & Travel": ["country", "city", "travel", "location", "region", "tourism"]
        }
        
        best_domain = "Society & Culture"  # Default to something meaningful
        best_score = 0
        
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_domain = domain
        
        # Create a reasonable subcategory
        subcategory = "Contemporary Topics" if best_score == 0 else "Related Discussion"
        
        return ContentCategorizationResult(
            primary_category=CategoryPath(
                path=[best_domain, subcategory],
                confidence=0.6,
                reasoning="Categorized using keyword analysis"
            ),
            secondary_categories=[],
            content_type=content_type,
            content_format="factual_claim",
            is_informal=False,
            cultural_context=None
        )


# Singleton instance
_categorizer_instance = None

def get_categorizer() -> HierarchicalCategorizer:
    """Get or create the singleton categorizer instance"""
    global _categorizer_instance
    if _categorizer_instance is None:
        _categorizer_instance = HierarchicalCategorizer()
    return _categorizer_instance


async def categorize_claim_content(
    text: str,
    media_files: List[Dict[str, Any]] = None
) -> ContentCategorizationResult:
    """
    Main entry point for content categorization.
    Returns a full hierarchical categorization result.
    """
    categorizer = get_categorizer()
    return await categorizer.categorize_content(text, media_files)
