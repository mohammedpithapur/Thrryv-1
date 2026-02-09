"""
User Standing System for Thrryv

Replaces traditional "reputation scores" with user-friendly standing signals
that evolve over time based on:
- Behavior consistency
- Contribution quality
- Engagement patterns
- Community feedback
- Content signals
- Originality of contributions

Standing is NOT a rank against other users, but a reflection of
consistency, effort, and contribution quality over time.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class StandingTier(str, Enum):
    """User standing tiers (not rankings, but descriptive levels)"""
    EMERGING = "emerging"  # New contributors
    CONSISTENT = "consistent"  # Regular, consistent contributors
    ESTABLISHED = "established"  # Proven track record
    EXPERT = "expert"  # High-quality consistent contributions
    TRUSTED = "trusted"  # Long-term, highly consistent excellence


@dataclass
class StandingMetric:
    """Individual standing metric component"""
    name: str
    current_value: float  # 0-100
    weight: float  # How much this contributes to overall
    trend: str  # "improving", "stable", "declining"
    contribution: float  # Amount contributed to total score


@dataclass
class StandingSignal:
    """User-friendly standing signal"""
    user_id: str
    tier: StandingTier
    overall_score: float  # 0-100
    metrics: List[StandingMetric]
    tenure_months: int
    content_quality_avg: float  # Average quality of user's content
    engagement_consistency: float  # How consistent their engagement
    originality_index: float  # How original their contributions
    community_feedback_score: float  # How positively community responds
    last_updated: str
    next_tier_requirements: Optional[Dict[str, Any]]


class UserStandingSystem:
    """
    Manages user standing signals based on contribution quality and behavior.
    
    Key principles:
    - NOT a ranking system
    - Reflects consistency and effort
    - Based on multiple signals
    - Transparent about what contributes to standing
    - Gradual changes (doesn't punish single mistakes)
    """
    
    def __init__(self):
        self.metric_weights = {
            "content_quality": 0.35,
            "engagement_consistency": 0.25,
            "originality": 0.15,
            "community_feedback": 0.15,
            "tenure_factor": 0.10
        }
    
    async def calculate_standing(
        self,
        user: Dict[str, Any],
        user_stats: Dict[str, Any],
        content_quality_avg: float,
        annotations: List[Dict[str, Any]]
    ) -> StandingSignal:
        """
        Calculate comprehensive standing signal for user.
        
        Args:
            user: User document
            user_stats: User statistics (claims, annotations, etc.)
            content_quality_avg: Average quality score of user's content
            annotations: User's annotations for feedback analysis
        
        Returns:
            Complete standing signal
        """
        
        # Calculate individual metrics
        content_quality = self._evaluate_content_quality(content_quality_avg)
        engagement = self._evaluate_engagement_consistency(user_stats, user)
        originality = self._evaluate_originality(user_stats)
        feedback = self._evaluate_community_feedback(annotations, user_stats)
        tenure_factor = self._evaluate_tenure(user)
        
        # Create metric objects
        metrics = [
            StandingMetric(
                name="Content Quality",
                current_value=content_quality,
                weight=self.metric_weights["content_quality"],
                trend=self._determine_trend(user_stats, "quality"),
                contribution=content_quality * self.metric_weights["content_quality"]
            ),
            StandingMetric(
                name="Engagement Consistency",
                current_value=engagement,
                weight=self.metric_weights["engagement_consistency"],
                trend=self._determine_trend(user_stats, "engagement"),
                contribution=engagement * self.metric_weights["engagement_consistency"]
            ),
            StandingMetric(
                name="Originality",
                current_value=originality,
                weight=self.metric_weights["originality"],
                trend="stable",
                contribution=originality * self.metric_weights["originality"]
            ),
            StandingMetric(
                name="Community Feedback",
                current_value=feedback,
                weight=self.metric_weights["community_feedback"],
                trend=self._determine_trend(user_stats, "feedback"),
                contribution=feedback * self.metric_weights["community_feedback"]
            ),
            StandingMetric(
                name="Tenure",
                current_value=tenure_factor,
                weight=self.metric_weights["tenure_factor"],
                trend="stable",
                contribution=tenure_factor * self.metric_weights["tenure_factor"]
            )
        ]
        
        # Calculate overall score
        overall_score = sum(m.contribution for m in metrics)
        
        # Determine tier
        tier = self._determine_tier(overall_score, user)
        
        # Calculate tenure in months
        created_at = datetime.fromisoformat(user.get('created_at', datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00'))
        tenure = (datetime.now(timezone.utc) - created_at).days // 30
        
        # Get next tier requirements
        next_tier_reqs = self._get_next_tier_requirements(tier, overall_score, metrics)
        
        return StandingSignal(
            user_id=user['id'],
            tier=tier,
            overall_score=overall_score,
            metrics=metrics,
            tenure_months=max(0, tenure),
            content_quality_avg=content_quality,
            engagement_consistency=engagement,
            originality_index=originality,
            community_feedback_score=feedback,
            last_updated=datetime.now(timezone.utc).isoformat(),
            next_tier_requirements=next_tier_reqs
        )
    
    def _evaluate_content_quality(self, avg_quality: float) -> float:
        """
        Evaluate content quality score (0-100).
        
        Converted from content signal scores.
        """
        return min(100, max(0, avg_quality * 1.2))  # Slight boost for existing scores
    
    def _evaluate_engagement_consistency(
        self,
        user_stats: Dict[str, Any],
        user: Dict[str, Any]
    ) -> float:
        """
        Evaluate engagement consistency (0-100).
        
        Based on:
        - Regular contribution patterns
        - Participation frequency
        - Response rate to discussions
        """
        
        claims_posted = user_stats.get('claims_posted', 0)
        annotations_added = user_stats.get('annotations_added', 0)
        
        # Calculate engagement rate
        total_contributions = claims_posted + annotations_added
        
        if total_contributions == 0:
            return 30.0  # Very low for non-contributors
        
        # Points for consistent participation
        score = 0.0
        
        if total_contributions >= 50:
            score += 40.0
        elif total_contributions >= 20:
            score += 30.0
        elif total_contributions >= 10:
            score += 20.0
        elif total_contributions >= 5:
            score += 15.0
        else:
            score += 5.0
        
        # Balance between claims and annotations (encourage both)
        if claims_posted > 0 and annotations_added > 0:
            score += 30.0
        elif annotations_added > 0:
            score += 15.0  # Encourage annotations
        
        # Diversity of contribution (not just one type)
        if claims_posted > 0 and annotations_added > 0:
            ratio = min(claims_posted, annotations_added) / max(claims_posted, annotations_added)
            score += ratio * 20
        
        return min(100, score)
    
    def _evaluate_originality(self, user_stats: Dict[str, Any]) -> float:
        """
        Evaluate originality of contributions (0-100).
        
        Based on:
        - Original claims vs duplicates
        - Novel perspectives
        - Unique annotation perspectives
        """
        
        original_claims = user_stats.get('original_claims', user_stats.get('claims_posted', 0))
        total_claims = user_stats.get('claims_posted', 0)
        
        # Score for having original content
        if total_claims == 0:
            return 50.0  # Neutral for new users
        
        originality_ratio = original_claims / total_claims
        
        score = originality_ratio * 80  # Base score from originality ratio
        
        # Bonus for high originality
        if originality_ratio > 0.8:
            score += 15.0
        elif originality_ratio > 0.6:
            score += 10.0
        
        return min(100, score)
    
    def _evaluate_community_feedback(
        self,
        annotations: List[Dict[str, Any]],
        user_stats: Dict[str, Any]
    ) -> float:
        """
        Evaluate community feedback score (0-100).
        
        Based on:
        - Helpful votes received
        - Quality of engagement
        - Constructive contributions
        """
        
        helpful_votes = user_stats.get('helpful_votes_received', 0)
        unhelpful_votes = user_stats.get('unhelpful_votes_received', 0)
        annotations_count = user_stats.get('annotations_added', 0)
        
        if annotations_count == 0:
            return 50.0  # Neutral
        
        # Calculate helpful ratio
        total_votes = helpful_votes + unhelpful_votes
        
        if total_votes == 0:
            return 50.0  # No votes yet
        
        helpful_ratio = helpful_votes / total_votes
        
        # Score based on ratio
        score = helpful_ratio * 100
        
        # Bonus for having significant engagement
        if total_votes >= 50:
            score = min(100, score + 10)
        elif total_votes >= 20:
            score = min(100, score + 5)
        
        return score
    
    def _evaluate_tenure(self, user: Dict[str, Any]) -> float:
        """
        Evaluate tenure factor (0-100).
        
        Newer users get lower scores, but score increases with time.
        """
        
        created_at = datetime.fromisoformat(
            user.get('created_at', datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00')
        )
        age_days = (datetime.now(timezone.utc) - created_at).days
        
        # Tenure scoring
        if age_days < 7:
            return 20.0
        elif age_days < 30:
            return 30.0
        elif age_days < 90:
            return 50.0
        elif age_days < 180:
            return 70.0
        elif age_days < 365:
            return 85.0
        else:
            return 95.0 + min(5, age_days / 365)  # Cap at 100
    
    def _determine_tier(self, score: float, user: Dict[str, Any]) -> StandingTier:
        """
        Determine user's standing tier.
        
        Not a ranking, but a descriptive level.
        """
        
        created_at = datetime.fromisoformat(
            user.get('created_at', datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00')
        )
        age_days = (datetime.now(timezone.utc) - created_at).days
        
        # New users are "emerging" regardless of score
        if age_days < 7:
            return StandingTier.EMERGING
        
        # Tier based on score
        if score >= 85:
            if age_days >= 365:  # 1 year consistent excellence
                return StandingTier.TRUSTED
            else:
                return StandingTier.EXPERT
        elif score >= 70:
            return StandingTier.ESTABLISHED
        elif score >= 50:
            return StandingTier.CONSISTENT
        else:
            return StandingTier.EMERGING
    
    def _determine_trend(self, user_stats: Dict[str, Any], metric_type: str) -> str:
        """
        Determine if metric is improving, stable, or declining.
        
        Based on historical data if available.
        """
        
        # Simple implementation - would be enhanced with historical tracking
        trend_data = user_stats.get('trend_data', {})
        
        if metric_type in trend_data:
            trend_value = trend_data[metric_type]
            if trend_value > 0.1:
                return "improving"
            elif trend_value < -0.1:
                return "declining"
        
        return "stable"
    
    def _get_next_tier_requirements(
        self,
        current_tier: StandingTier,
        current_score: float,
        metrics: List[StandingMetric]
    ) -> Optional[Dict[str, Any]]:
        """
        Get requirements for next tier.
        
        Returns None if user is already at highest tier.
        """
        
        tier_thresholds = {
            StandingTier.EMERGING: 50,
            StandingTier.CONSISTENT: 70,
            StandingTier.ESTABLISHED: 80,
            StandingTier.EXPERT: 90,
            StandingTier.TRUSTED: None  # Highest tier
        }
        
        tier_order = [
            StandingTier.EMERGING,
            StandingTier.CONSISTENT,
            StandingTier.ESTABLISHED,
            StandingTier.EXPERT,
            StandingTier.TRUSTED
        ]
        
        if current_tier == StandingTier.TRUSTED:
            return None
        
        # Find next tier
        next_index = tier_order.index(current_tier) + 1
        if next_index >= len(tier_order):
            return None
        
        next_tier = tier_order[next_index]
        threshold = tier_thresholds[next_tier]
        
        # Calculate requirements
        gap = threshold - current_score
        
        # Find which metrics need improvement
        weak_metrics = [m for m in metrics if m.current_value < 70]
        
        return {
            "next_tier": next_tier.value,
            "score_needed": max(0, gap),
            "current_score": current_score,
            "focus_areas": [m.name for m in weak_metrics],
            "estimate_weeks": max(1, int(gap / 10)) if gap > 0 else 0
        }
    
    def get_standing_impact_on_reach(self, standing_signal: StandingSignal) -> float:
        """
        Determine how standing affects content reach probability.
        
        Returns multiplier (1.0 = baseline, < 1.0 = less reach, > 1.0 = more reach).
        
        This is PROBABILISTIC and SOFT - not a hard rank.
        """
        
        tier_multipliers = {
            StandingTier.EMERGING: 0.8,
            StandingTier.CONSISTENT: 0.95,
            StandingTier.ESTABLISHED: 1.1,
            StandingTier.EXPERT: 1.25,
            StandingTier.TRUSTED: 1.4
        }
        
        base_multiplier = tier_multipliers.get(standing_signal.tier, 1.0)
        
        # Slight boost based on overall score
        score_boost = (standing_signal.overall_score / 100) * 0.2
        
        return base_multiplier + score_boost
    
    def format_standing_for_profile(self, standing_signal: StandingSignal) -> Dict[str, Any]:
        """
        Format standing signal for public profile display.
        
        Shows user-friendly information without ranking.
        """
        
        tier_descriptions = {
            StandingTier.EMERGING: "New contributor - building their track record",
            StandingTier.CONSISTENT: "Regular contributor with consistent participation",
            StandingTier.ESTABLISHED: "Proven contributor with established track record",
            StandingTier.EXPERT: "Highly respected for quality contributions",
            StandingTier.TRUSTED: "Long-term trusted member of community"
        }
        
        # Sort metrics by contribution
        sorted_metrics = sorted(standing_signal.metrics, key=lambda m: m.contribution, reverse=True)
        
        return {
            "standing_tier": standing_signal.tier.value,
            "tier_description": tier_descriptions[standing_signal.tier],
            "overall_score": round(standing_signal.overall_score, 1),
            "tenure_months": standing_signal.tenure_months,
            "strength_areas": [m.name for m in sorted_metrics[:2] if m.current_value >= 70],
            "growth_areas": [m.name for m in sorted_metrics if m.current_value < 60],
            "key_metrics": [
                {
                    "name": m.name,
                    "score": round(m.current_value, 1),
                    "trend": m.trend
                }
                for m in sorted_metrics[:3]
            ],
            "next_milestone": standing_signal.next_tier_requirements
        }
