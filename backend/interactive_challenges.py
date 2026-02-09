"""
Interactive Challenge Predictions for Thrryv

Enables creators to introduce time-bound challenges within content.
Viewers can make quick predictions that:
- Create engaging interactive experiences
- Affect only viewer's engagement standing (not creator)
- Don't label content as true/false
- Build community participation
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import uuid
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ChallengeStatus(str, Enum):
    """Status of a challenge"""
    ACTIVE = "active"
    CLOSED = "closed"
    RESOLVED = "resolved"
    EXPIRED = "expired"


@dataclass
class ChallengePrediction:
    """A single prediction on a challenge"""
    id: str
    challenge_id: str
    user_id: str
    prediction: str  # "yes", "no", "unsure"
    confidence_level: float  # 0-100
    made_at: str
    points_earned: Optional[float] = None
    feedback: Optional[str] = None


@dataclass
class ChallengeResolution:
    """Resolution of a challenge after it closes"""
    challenge_id: str
    actual_outcome: str
    resolution_timestamp: str
    resolution_explanation: str
    community_accuracy: float  # What % predicted correctly
    engagement_metrics: Dict[str, Any]


@dataclass
class Challenge:
    """Interactive challenge within content"""
    id: str
    claim_id: str
    creator_id: str
    title: str
    description: str
    challenge_type: str  # "yes_no", "multiple_choice", "prediction"
    options: List[str]  # For multiple choice
    created_at: str
    closes_at: str
    resolve_at: str
    status: ChallengeStatus
    prediction_count: int
    participant_count: int
    points_per_prediction: float


class InteractiveChallengeSystem:
    """
    Manages interactive challenge predictions.
    
    Key features:
    - Time-bound challenges
    - Low-stakes predictions
    - Standing impact only for viewers
    - Community engagement boost
    - No content labeling
    """
    
    def __init__(self):
        self.default_duration_hours = 24
        self.default_resolve_hours = 48
        self.points_correct = 5.0
        self.points_close = 2.5
        self.points_attempt = 1.0
    
    async def create_challenge(
        self,
        claim_id: str,
        creator_id: str,
        challenge_data: Dict[str, Any]
    ) -> Challenge:
        """
        Create a new interactive challenge.
        
        Args:
            claim_id: Associated claim
            creator_id: Creator of challenge
            challenge_data: {
                "title": "Can I achieve X by [date]?",
                "description": "Detailed explanation",
                "challenge_type": "yes_no|multiple_choice|prediction",
                "options": ["option1", "option2"],  # For multiple choice
                "duration_hours": 24,  # How long prediction is open
                "resolve_hours": 48  # When to resolve challenge
            }
        
        Returns:
            Created challenge
        """
        
        challenge_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        duration = challenge_data.get('duration_hours', self.default_duration_hours)
        resolve = challenge_data.get('resolve_hours', self.default_resolve_hours)
        
        challenge = Challenge(
            id=challenge_id,
            claim_id=claim_id,
            creator_id=creator_id,
            title=challenge_data.get('title', ''),
            description=challenge_data.get('description', ''),
            challenge_type=challenge_data.get('challenge_type', 'yes_no'),
            options=challenge_data.get('options', ['Yes', 'No', 'Unsure']),
            created_at=now.isoformat(),
            closes_at=(now + timedelta(hours=duration)).isoformat(),
            resolve_at=(now + timedelta(hours=resolve)).isoformat(),
            status=ChallengeStatus.ACTIVE,
            prediction_count=0,
            participant_count=0,
            points_per_prediction=self.points_attempt
        )
        
        return challenge
    
    async def make_prediction(
        self,
        challenge_id: str,
        user_id: str,
        prediction: str,
        confidence_level: float = 50.0
    ) -> ChallengePrediction:
        """
        Record a user's prediction on a challenge.
        
        Args:
            challenge_id: Challenge being predicted on
            user_id: User making prediction
            prediction: The prediction ("yes", "no", "unsure", or option)
            confidence_level: User's confidence (0-100)
        
        Returns:
            Created prediction
        """
        
        # Validate confidence
        confidence_level = min(100, max(0, confidence_level))
        
        prediction_record = ChallengePrediction(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            user_id=user_id,
            prediction=prediction,
            confidence_level=confidence_level,
            made_at=datetime.now(timezone.utc).isoformat()
        )
        
        return prediction_record
    
    async def resolve_challenge(
        self,
        challenge_id: str,
        actual_outcome: str,
        resolution_explanation: str = ""
    ) -> ChallengeResolution:
        """
        Resolve a challenge after it closes.
        
        Does NOT label the original content.
        Only updates engagement standing for participants.
        
        Args:
            challenge_id: Challenge to resolve
            actual_outcome: The actual result
            resolution_explanation: Explanation of resolution
        
        Returns:
            Challenge resolution record
        """
        
        resolution = ChallengeResolution(
            challenge_id=challenge_id,
            actual_outcome=actual_outcome,
            resolution_timestamp=datetime.now(timezone.utc).isoformat(),
            resolution_explanation=resolution_explanation,
            community_accuracy=0.0,  # Calculate from predictions
            engagement_metrics={
                "total_predictions": 0,
                "unique_participants": 0,
                "accuracy_rate": 0.0,
                "engagement_score": 0.0
            }
        )
        
        return resolution
    
    def calculate_prediction_score(
        self,
        prediction: ChallengePrediction,
        actual_outcome: str,
        challenge: Challenge
    ) -> float:
        """
        Calculate standing points earned from prediction.
        
        Only affects viewer's standing, not content or creator.
        """
        
        # Check if prediction was correct
        is_correct = prediction.prediction == actual_outcome
        
        # Base points for attempting
        points = self.points_attempt
        
        if is_correct:
            # Bonus for correct prediction
            points += self.points_correct
            
            # Confidence bonus (up to 5x multiplier for high confidence)
            confidence_multiplier = 1.0 + (prediction.confidence_level / 100) * 1.0
            points *= confidence_multiplier
        
        else:
            # Close prediction (within category)
            if self._is_close_prediction(prediction.prediction, actual_outcome):
                points += self.points_close
        
        return min(50, points)  # Cap maximum points per prediction
    
    def _is_close_prediction(self, prediction: str, outcome: str) -> bool:
        """
        Check if prediction was close to actual outcome.
        
        For scoring partial credit.
        """
        
        # Simple similarity check
        if len(prediction) > 3 and len(outcome) > 3:
            common_words = set(prediction.lower().split()) & set(outcome.lower().split())
            return len(common_words) > 0
        
        return False
    
    def update_viewer_standing(
        self,
        user_stats: Dict[str, Any],
        points_earned: float
    ) -> Dict[str, Any]:
        """
        Update viewer's standing based on prediction performance.
        
        Note: Creator is NOT affected.
        """
        
        # Add to engagement metric
        user_stats['challenge_predictions'] = user_stats.get('challenge_predictions', 0) + 1
        user_stats['challenge_points_earned'] = user_stats.get('challenge_points_earned', 0) + points_earned
        
        # Calculate engagement consistency (predictions count)
        user_stats['engagement_score'] = user_stats.get('engagement_score', 0) + (points_earned / 50)
        
        return user_stats
    
    def get_leaderboard_metrics(
        self,
        prediction_records: List[ChallengePrediction],
        resolutions: List[ChallengeResolution]
    ) -> Dict[str, Any]:
        """
        Calculate leaderboard metrics for challenge.
        
        Shows engagement without ranking.
        """
        
        # Calculate accuracy
        correct_predictions = 0
        for pred in prediction_records:
            for res in resolutions:
                if pred.challenge_id == res.challenge_id:
                    if pred.prediction == res.actual_outcome:
                        correct_predictions += 1
        
        accuracy_rate = (correct_predictions / len(prediction_records)) if prediction_records else 0
        
        # Top predictors (by confidence and correctness)
        predictor_scores = {}
        for pred in prediction_records:
            if pred.user_id not in predictor_scores:
                predictor_scores[pred.user_id] = {
                    'count': 0,
                    'confidence_avg': 0,
                    'correct': 0
                }
            
            predictor_scores[pred.user_id]['count'] += 1
            predictor_scores[pred.user_id]['confidence_avg'] += pred.confidence_level
            
            for res in resolutions:
                if pred.challenge_id == res.challenge_id and pred.prediction == res.actual_outcome:
                    predictor_scores[pred.user_id]['correct'] += 1
        
        # Calculate confidence averages
        for user_id in predictor_scores:
            count = predictor_scores[user_id]['count']
            predictor_scores[user_id]['confidence_avg'] /= count
        
        return {
            "total_predictions": len(prediction_records),
            "unique_participants": len(predictor_scores),
            "accuracy_rate": accuracy_rate,
            "average_confidence": sum(p.confidence_level for p in prediction_records) / len(prediction_records) if prediction_records else 0,
            "top_predictors": sorted(
                predictor_scores.items(),
                key=lambda x: (x[1]['correct'], x[1]['confidence_avg']),
                reverse=True
            )[:10]
        }
    
    def format_challenge_for_display(
        self,
        challenge: Challenge,
        user_prediction: Optional[ChallengePrediction] = None
    ) -> Dict[str, Any]:
        """
        Format challenge for frontend display.
        """
        
        now = datetime.now(timezone.utc)
        closes_at = datetime.fromisoformat(challenge.closes_at)
        
        time_remaining = closes_at - now
        is_open = time_remaining.total_seconds() > 0
        
        return {
            "id": challenge.id,
            "title": challenge.title,
            "description": challenge.description,
            "type": challenge.challenge_type,
            "options": challenge.options,
            "status": challenge.status.value,
            "is_open": is_open,
            "time_remaining_seconds": max(0, int(time_remaining.total_seconds())),
            "participation_stats": {
                "predictions": challenge.prediction_count,
                "participants": challenge.participant_count
            },
            "your_prediction": {
                "prediction": user_prediction.prediction if user_prediction else None,
                "confidence": user_prediction.confidence_level if user_prediction else None,
                "made_at": user_prediction.made_at if user_prediction else None
            } if user_prediction else None,
            "engagement_note": "Make a quick prediction to engage with this content. Your engagement only affects your standing, not this content."
        }
    
    async def auto_resolve_expired_challenges(
        self,
        challenges: List[Challenge]
    ) -> List[ChallengeResolution]:
        """
        Auto-resolve challenges that have expired without manual resolution.
        
        Marks as "not resolved" to preserve integrity.
        """
        
        now = datetime.now(timezone.utc)
        resolutions = []
        
        for challenge in challenges:
            resolve_at = datetime.fromisoformat(challenge.resolve_at)
            
            if now > resolve_at and challenge.status == ChallengeStatus.CLOSED:
                # Auto-expire without resolution
                resolution = ChallengeResolution(
                    challenge_id=challenge.id,
                    actual_outcome="not_resolved",
                    resolution_timestamp=now.isoformat(),
                    resolution_explanation="Challenge expired without manual resolution",
                    community_accuracy=0.0,
                    engagement_metrics={
                        "status": "expired",
                        "note": "Predictions do not affect standing when unresolved"
                    }
                )
                resolutions.append(resolution)
        
        return resolutions
