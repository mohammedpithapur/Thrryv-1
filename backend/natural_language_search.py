"""
Intent-Based Natural Language Search for Thrryv

Translates user intent in plain language into structured search queries.
Supports:
- Free-form natural language queries
- Time range preferences
- Perspective diversity preferences
- Depth preferences
- Domain filtering
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class SearchIntent:
    """Parsed user search intent"""
    core_query: str
    domains: List[str]
    time_range: Optional[Dict[str, str]]  # {"from": "2024-01-01", "to": "2024-12-31"}
    perspective_preferences: List[str]
    depth_level: str  # "surface", "medium", "deep"
    sort_by: str  # "relevance", "recency", "originality", "diverse"
    min_content_quality: float  # 0-100
    include_ai_generated: bool
    structured_filters: Dict[str, Any]


class NaturalLanguageSearchEngine:
    """
    Converts natural language queries into structured searches.
    
    Understands intent patterns like:
    - "Recent research on climate change"
    - "Different perspectives on AI ethics"
    - "Contrarian views on economic policy from the last month"
    - "In-depth analysis of quantum computing"
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('EMERGENT_LLM_KEY')
    
    async def parse_search_intent(self, query: str) -> SearchIntent:
        """
        Parse natural language query into structured search intent.
        
        Uses LLM if available, falls back to pattern matching.
        """
        
        if not self.api_key:
            return self._parse_search_intent_fallback(query)
        
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"search-{datetime.now().timestamp()}",
                system_message="""You are a search intent analyzer for Thrryv.
Convert natural language search queries into structured intent.

Available domains: Science, Health, Technology, Politics, Economics, Environment, 
History, Society, Sports, Entertainment, Education, Geography, Food, Law, Religion

Perspective preferences: diverse, mainstream, critical, expert, personal

Depth levels: surface, medium, deep

Respond in JSON:
{
  "core_query": "main search topic",
  "domains": ["domain1", "domain2"],
  "time_range": {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"} or null,
  "perspective_preferences": ["perspective1"],
  "depth_level": "surface|medium|deep",
  "sort_by": "relevance|recency|originality|diverse",
  "min_content_quality": 0-100,
  "include_ai_generated": true/false,
  "intent_explanation": "brief explanation of user intent"
}"""
            ).with_model("openai", "gpt-4o-mini")
            
            response = await chat.send_message(UserMessage(text=f"Parse search intent: {query}"))
            result = self._parse_json_response(response)
            
            if result:
                return SearchIntent(
                    core_query=result.get('core_query', query),
                    domains=result.get('domains', []),
                    time_range=result.get('time_range'),
                    perspective_preferences=result.get('perspective_preferences', []),
                    depth_level=result.get('depth_level', 'medium'),
                    sort_by=result.get('sort_by', 'relevance'),
                    min_content_quality=result.get('min_content_quality', 30),
                    include_ai_generated=result.get('include_ai_generated', False),
                    structured_filters=result.get('filters', {})
                )
        
        except Exception as e:
            logger.warning(f"LLM search parsing failed: {e}")
        
        return self._parse_search_intent_fallback(query)
    
    def _parse_search_intent_fallback(self, query: str) -> SearchIntent:
        """
        Fallback search intent parsing using pattern matching.
        """
        
        query_lower = query.lower()
        
        # Extract time preferences
        time_range = self._extract_time_range(query)
        
        # Extract perspective preferences
        perspective_prefs = []
        if any(word in query_lower for word in ["different", "diverse", "other", "perspectives", "viewpoints"]):
            perspective_prefs.append("diverse")
        if any(word in query_lower for word in ["mainstream", "popular", "consensus", "most people"]):
            perspective_prefs.append("mainstream")
        if any(word in query_lower for word in ["critical", "against", "opposition", "disagree"]):
            perspective_prefs.append("critical")
        if any(word in query_lower for word in ["expert", "research", "study", "scientific"]):
            perspective_prefs.append("expert")
        
        if not perspective_prefs:
            perspective_prefs.append("diverse")
        
        # Extract depth preference
        depth = "medium"
        if any(word in query_lower for word in ["briefly", "overview", "quick", "summary"]):
            depth = "surface"
        elif any(word in query_lower for word in ["deep", "detail", "comprehensive", "thorough", "explain in depth"]):
            depth = "deep"
        
        # Extract sort preference
        sort_by = "relevance"
        if any(word in query_lower for word in ["recent", "latest", "new"]):
            sort_by = "recency"
        elif any(word in query_lower for word in ["original", "novel", "unique"]):
            sort_by = "originality"
        elif "diverse" in perspective_prefs:
            sort_by = "diverse"
        
        # Extract domain keywords
        domains = self._extract_domains(query)
        
        # Minimum quality
        min_quality = 30
        if any(word in query_lower for word in ["quality", "well-researched", "credible", "authoritative"]):
            min_quality = 60
        
        return SearchIntent(
            core_query=query,
            domains=domains,
            time_range=time_range,
            perspective_preferences=perspective_prefs,
            depth_level=depth,
            sort_by=sort_by,
            min_content_quality=min_quality,
            include_ai_generated=False,
            structured_filters={}
        )
    
    def _extract_time_range(self, query: str) -> Optional[Dict[str, str]]:
        """Extract time range from query"""
        
        query_lower = query.lower()
        today = datetime.now()
        
        # Recent time periods
        if any(word in query_lower for word in ["today", "yesterday"]):
            start = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            end = today.strftime("%Y-%m-%d")
            return {"from": start, "to": end}
        
        if any(word in query_lower for word in ["this week", "last week", "past week"]):
            start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            end = today.strftime("%Y-%m-%d")
            return {"from": start, "to": end}
        
        if any(word in query_lower for word in ["this month", "last month", "past month"]):
            start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
            end = today.strftime("%Y-%m-%d")
            return {"from": start, "to": end}
        
        if any(word in query_lower for word in ["this year", "past year", "last year"]):
            start = (today - timedelta(days=365)).strftime("%Y-%m-%d")
            end = today.strftime("%Y-%m-%d")
            return {"from": start, "to": end}
        
        if any(word in query_lower for word in ["historical", "all time", "anytime"]):
            return None  # No time constraint
        
        return None
    
    def _extract_domains(self, query: str) -> List[str]:
        """Extract domain keywords from query"""
        
        query_lower = query.lower()
        
        domain_keywords = {
            "Science": ["science", "research", "study", "experiment", "scientific", "physics", "biology", "chemistry"],
            "Health": ["health", "medical", "disease", "vaccine", "wellness", "doctor", "hospital"],
            "Technology": ["technology", "tech", "AI", "computer", "software", "digital", "innovation"],
            "Politics": ["political", "government", "election", "policy", "vote", "president", "congress"],
            "Economics": ["economy", "economic", "financial", "market", "business", "trade", "wealth"],
            "Environment": ["environment", "climate", "pollution", "renewable", "sustainability"],
            "History": ["history", "historical", "ancient", "past", "century", "war", "empire"],
            "Society": ["social", "society", "culture", "community", "demographic", "equality"],
            "Sports": ["sport", "athletic", "game", "competition", "player", "team", "championship"],
            "Entertainment": ["movie", "music", "celebrity", "actor", "entertainment", "film"],
        }
        
        domains = []
        for domain, keywords in domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                domains.append(domain)
        
        return domains
    
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
    
    async def execute_search(
        self,
        intent: SearchIntent,
        available_claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute search based on parsed intent.
        
        Filters and sorts claims according to user's intent.
        """
        
        results = available_claims
        
        # Filter by domain
        if intent.domains:
            results = [
                c for c in results
                if c.get('domain') in intent.domains
            ]
        
        # Filter by time range
        if intent.time_range:
            results = self._filter_by_time_range(results, intent.time_range)
        
        # Filter by content quality
        if intent.min_content_quality > 0:
            results = [
                c for c in results
                if c.get('quality_score', 0) >= intent.min_content_quality
            ]
        
        # Filter AI-generated
        if not intent.include_ai_generated:
            results = [
                c for c in results
                if not c.get('is_ai_generated', False)
            ]
        
        # Sort results
        results = self._sort_results(results, intent.sort_by)
        
        return results
    
    @staticmethod
    def _filter_by_time_range(
        claims: List[Dict[str, Any]],
        time_range: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Filter claims by time range"""
        
        try:
            from_date = datetime.fromisoformat(time_range['from'])
            to_date = datetime.fromisoformat(time_range['to'])
            
            filtered = []
            for claim in claims:
                created_at_str = claim.get('created_at', '')
                if created_at_str:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    if from_date <= created_at <= to_date:
                        filtered.append(claim)
            
            return filtered
        
        except Exception as e:
            logger.warning(f"Error filtering by time range: {e}")
            return claims
    
    @staticmethod
    def _sort_results(
        claims: List[Dict[str, Any]],
        sort_by: str
    ) -> List[Dict[str, Any]]:
        """Sort claims by specified criteria"""
        
        if sort_by == "recency":
            claims.sort(
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )
        
        elif sort_by == "originality":
            claims.sort(
                key=lambda x: x.get('originality_score', 0),
                reverse=True
            )
        
        elif sort_by == "diverse":
            # Sort by diversity indicators
            claims.sort(
                key=lambda x: (
                    x.get('perspective_diversity_score', 0),
                    x.get('annotation_diversity_score', 0)
                ),
                reverse=True
            )
        
        else:  # relevance (default)
            claims.sort(
                key=lambda x: x.get('relevance_score', 0),
                reverse=True
            )
        
        return claims
