import time as _time

# Simple in-memory cache for suggestions and trending topics
_suggestion_cache = {}
_trending_cache = {}

def _cache_get(cache, key, max_age):
    entry = cache.get(key)
    if entry and (_time.time() - entry['time'] < max_age):
        return entry['value']
    return None

def _cache_set(cache, key, value):
    cache[key] = {'value': value, 'time': _time.time()}
from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status, Request, Header
from routes import uptime
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Load emergentintegrations stub if package unavailable
try:
    import emergentintegrations
except ImportError:
    import emergentintegrations_stub

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, RedirectResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import requests
import io
from enum import Enum
import asyncio
import tempfile
import boto3
import uvicorn
import re
import time

# Import AI Reputation Evaluator
from ai_reputation_evaluator import evaluate_claim_for_reputation, EvaluationResult

# Import Hierarchical Content Categorizer
from content_categorizer import categorize_claim_content, ContentCategorizationResult

# Import validators
from validators import InputValidator, validate_media_file

# Import media cleanup utilities
from media_cleanup import delete_media_files, cleanup_orphaned_media, get_storage_stats

# Import annotation classifier
from annotation_validator import classify_annotation_type

# Import new Thrryv v1 features
from content_discovery import ContentDiscoveryEngine, DiscoveryAlgorithm
from content_signals import ContentSignalGenerator
from user_standing import UserStandingSystem, StandingTier
from originality_detection import OriginalityDetector
from natural_language_search import NaturalLanguageSearchEngine
from interactive_challenges import InteractiveChallengeSystem, ChallengeStatus

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Setup logging
from logging_config import setup_logging
log_dir = ROOT_DIR / 'logs'
setup_logging(log_dir=log_dir, log_level=os.environ.get('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# MongoDB connection with retry logic
mongo_url = os.environ['MONGO_URL']
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

async def get_db_client():
    """Get MongoDB client with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                maxPoolSize=50,
                minPoolSize=10
            )
            # Test connection
            await client.admin.command('ping')
            logger.info(f"MongoDB connection established successfully")
            return client
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"MongoDB connection attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
            else:
                logger.error("Failed to connect to MongoDB after all retries")
                raise HTTPException(
                    status_code=503,
                    detail="Database connection unavailable. Please try again later."
                )

# Initialize client placeholder
client = None
db = None

# Environment: development or production
ENV = os.environ.get('ENV', 'development').lower()
if ENV not in ['development', 'production']:
    ENV = 'development'
    logger.warning("Invalid ENV value, defaulting to 'development'")

IS_PRODUCTION = ENV == 'production'

# JWT configuration - JWT_SECRET is required in production
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    if IS_PRODUCTION:
        raise ValueError("JWT_SECRET environment variable is required in production")
    else:
        # Development fallback
        JWT_SECRET = 'dev-secret-key-change-in-production'
        logger.warning("Using development JWT_SECRET. Set JWT_SECRET environment variable for production.")

JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7
ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY')
if not ADMIN_API_KEY:
    logger.warning("ADMIN_API_KEY not set. Admin endpoints may not work properly.")

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

# File upload directory
UPLOAD_DIR = ROOT_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

# AWS S3 Configuration
AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_S3_MEDIA_PREFIX = os.environ.get('AWS_S3_MEDIA_PREFIX', 'media/')
AWS_S3_PROFILE_PREFIX = os.environ.get('AWS_S3_PROFILE_PREFIX', 'profiles/')

# Validate AWS S3 settings
try:
    AWS_S3_PRESIGN_EXPIRES = int(os.environ.get('AWS_S3_PRESIGN_EXPIRES', '3600'))
    if AWS_S3_PRESIGN_EXPIRES < 60 or AWS_S3_PRESIGN_EXPIRES > 86400:
        AWS_S3_PRESIGN_EXPIRES = 3600
        logger.warning("AWS_S3_PRESIGN_EXPIRES out of range, using default 3600s")
except (ValueError, TypeError):
    AWS_S3_PRESIGN_EXPIRES = 3600
    logger.warning("Invalid AWS_S3_PRESIGN_EXPIRES value, using default 3600s")

def normalize_s3_prefix(prefix: str) -> str:
    if not prefix:
        return ''
    return prefix if prefix.endswith('/') else f"{prefix}/"

AWS_S3_MEDIA_PREFIX = normalize_s3_prefix(AWS_S3_MEDIA_PREFIX)
AWS_S3_PROFILE_PREFIX = normalize_s3_prefix(AWS_S3_PROFILE_PREFIX)

USE_S3 = bool(AWS_S3_BUCKET)

# Reputation bounds
MIN_REPUTATION = 0.0
MAX_REPUTATION = 1000.0

def clamp_reputation(score: float) -> float:
    """Ensure reputation score stays within bounds"""
    return max(MIN_REPUTATION, min(MAX_REPUTATION, score))

# Scoring constants - Post score calculation
ENGAGEMENT_BONUS_MAX = 5.0  # Maximum engagement bonus in post score
ENGAGEMENT_ANNOTATION_WEIGHT = 0.3  # Weight per annotation in engagement calculation
ENGAGEMENT_HELPFUL_VOTE_WEIGHT = 0.15  # Weight per helpful vote in engagement calculation
STANCE_ADJUSTMENT_MAX = 5.0  # Maximum stance adjustment range (-5 to +5)
STANCE_ADJUSTMENT_SCALE = 0.4  # Scale factor for stance adjustment calculation
STANCE_SUPPORT_SCALE = 1.0  # Positive multiplier for support annotations
STANCE_CONTRADICT_SCALE = 1.0  # Positive multiplier for contradict annotations

# Annotation weight calculation constants
ANNOTATION_WEIGHT_HELPFUL_VOTE_FACTOR = 0.2  # Weight increment per helpful vote
ANNOTATION_WEIGHT_NOT_HELPFUL_FACTOR = 0.1  # Weight decrement per not helpful vote
ANNOTATION_WEIGHT_MIN = 0.2  # Minimum annotation weight (floor)
ANNOTATION_WEIGHT_MAX = 2.0  # Maximum reputation factor multiplier
ANNOTATION_REPUTATION_FACTOR_BASE = 0.6  # Reputation factor minimum
ANNOTATION_REPUTATION_FACTOR_PER_REP = ANNOTATION_REPUTATION_FACTOR_BASE / 10.0  # Rep scaling
ANNOTATION_CONFIDENCE_FACTOR_BASE = 0.6  # Confidence factor baseline
ANNOTATION_CONFIDENCE_FACTOR_SCALE = 0.4  # Confidence factor scaling

# Evidence thresholds for annotations to influence score
ANNOTATION_WEAK_EVIDENCE_PENALTY = 0.25  # Multiplier for weak evidence annotations
ANNOTATION_HELPFUL_VOTES_THRESHOLD = 2  # Helpful votes needed for strong evidence
ANNOTATION_AUTHOR_REP_THRESHOLD = 15  # Author reputation for strong evidence
ANNOTATION_CONFIDENCE_THRESHOLD = 0.7  # Confidence level for strong evidence

# Voting and reputation constants
DEFAULT_AUTHOR_REPUTATION = 10.0  # Default reputation when not found
INITIAL_USER_REPUTATION = 10.0  # Initial reputation for newly registered users
VOTE_REPUTATION_GAIN_BASE = 1.0  # Base reputation gain from helpful vote
VOTE_TIME_BONUS_MAX = 2.0  # Maximum time bonus for aging well annotations
VOTE_TIME_BONUS_DAYS = 15.0  # Days to reach maximum time bonus (aging well)

def get_s3_client():
    if not USE_S3:
        return None
    return boto3.client('s3', region_name=AWS_REGION)

S3_CLIENT = get_s3_client()

def is_s3_uri(path_value: Optional[str]) -> bool:
    return isinstance(path_value, str) and path_value.startswith('s3://')

def parse_s3_uri(uri: str) -> tuple[str, str]:
    stripped = uri[5:]
    parts = stripped.split('/', 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError('Invalid S3 URI')
    return parts[0], parts[1]

async def s3_upload_file(file_path: str, key: str, content_type: str) -> str:
    if not S3_CLIENT or not AWS_S3_BUCKET:
        raise HTTPException(status_code=500, detail='S3 storage not configured')
    await asyncio.to_thread(
        S3_CLIENT.upload_file,
        file_path,
        AWS_S3_BUCKET,
        key,
        ExtraArgs={'ContentType': content_type}
    )
    return f"s3://{AWS_S3_BUCKET}/{key}"

async def s3_generate_presigned_url(bucket: str, key: str) -> str:
    if not S3_CLIENT:
        raise HTTPException(status_code=500, detail='S3 storage not configured')
    return await asyncio.to_thread(
        S3_CLIENT.generate_presigned_url,
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=AWS_S3_PRESIGN_EXPIRES
    )

async def s3_delete_object(bucket: str, key: str) -> bool:
    """Delete an object from S3 and return success status
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        True if deletion successful or S3 disabled, False if error occurs
    """
    if not S3_CLIENT:
        return True  # Consider success if S3 is not configured (no-op)
    try:
        response = await asyncio.to_thread(S3_CLIENT.delete_object, Bucket=bucket, Key=key)
        # Check for successful HTTP status code (204 No Content or 200 OK)
        status_code = response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)
        return status_code in (200, 204)
    except Exception as e:
        logger.error(f"Failed to delete S3 object {bucket}/{key}: {e}")
        return False

async def load_media_bytes(media: Dict[str, Any]) -> Optional[bytes]:
    file_path = media.get('file_path')
    if not file_path:
        return None
    if is_s3_uri(file_path):
        if not S3_CLIENT:
            return None
        try:
            bucket, key = parse_s3_uri(file_path)
            response = await asyncio.to_thread(S3_CLIENT.get_object, Bucket=bucket, Key=key)
            body = response.get('Body')
            if not body:
                return None
            return await asyncio.to_thread(body.read)
        except Exception as e:
            logging.warning(f"Could not read media from S3: {e}")
            return None
    try:
        path = Path(file_path)
        if path.exists():
            return path.read_bytes()
    except Exception as e:
        logging.warning(f"Could not read media from disk: {e}")
    return None

# API Response Wrapper Classes for standardized responses
class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses"""
    limit: int
    offset: int
    total: int
    has_more: bool

class ListResponse(BaseModel):
    """Standard response for list endpoints"""
    success: bool = True
    data: List[Dict[str, Any]] = Field(default_factory=list)
    pagination: Optional[PaginationMetadata] = None
    message: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class SingleResponse(BaseModel):
    """Standard response for single resource endpoints"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    status_code: int

def standardize_list_response(
    data: List[Dict[str, Any]],
    limit: int,
    offset: int,
    total: int,
    message: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized list response with pagination"""
    pagination = PaginationMetadata(
        limit=limit,
        offset=offset,
        total=total,
        has_more=offset + limit < total
    )
    response = ListResponse(
        data=data,
        pagination=pagination,
        message=message,
        extra=extra
    )
    return response.model_dump()

def standardize_single_response(
    data: Optional[Dict[str, Any]],
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Create a standardized single resource response"""
    response = SingleResponse(
        data=data,
        message=message
    )
    return response.model_dump()

def standardize_error_response(
    error: str,
    detail: Optional[str] = None,
    status_code: int = 400
) -> Dict[str, Any]:
    """Create a standardized error response"""
    response = ErrorResponse(
        error=error,
        detail=detail,
        status_code=status_code
    )
    return response.model_dump()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=standardize_error_response(
            error="http_error",
            detail=str(exc.detail),
            status_code=exc.status_code
        )
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=standardize_error_response(
            error="validation_error",
            detail=str(exc.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=standardize_error_response(
            error="server_error",
            detail="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    )

api_router = APIRouter(prefix="/api")

# Enums
class AnnotationType(str, Enum):
    SUPPORT = "support"
    CONTRADICT = "contradict"
    CONTEXT = "context"

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    reputation_score: float
    contribution_stats: Dict[str, int]
    created_at: str

class ClaimCreate(BaseModel):
    text: str
    confidence_level: int
    media_ids: Optional[List[str]] = []

class ClaimResponse(BaseModel):
    id: str
    text: str
    domain: str
    confidence_level: int
    author: Dict[str, str]
    media: List[Dict[str, Any]]
    post_score: float
    annotation_count: int
    created_at: str

class AnnotationCreate(BaseModel):
    text: str
    annotation_type: Optional[AnnotationType] = None
    media_ids: Optional[List[str]] = []

class UserSettingsUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

class AnnotationResponse(BaseModel):
    id: str
    claim_id: str
    author: Dict[str, str]
    text: str
    annotation_type: AnnotationType
    media: List[Dict[str, Any]]
    helpful_votes: int
    not_helpful_votes: int
    created_at: str

class MediaResponse(BaseModel):
    id: str
    file_path: str
    file_type: str
    is_ai_generated: bool
    ai_confidence: Optional[float] = None
    created_at: str

# New Thrryv v1 Models
class SearchQueryRequest(BaseModel):
    query: str
    algorithm: Optional[str] = "relevance"  # relevance, diversity, emergent, standing_aware
    diversity_preference: Optional[float] = 0.3
    limit: Optional[int] = 20

class FeedDiscoverRequest(BaseModel):
    limit: Optional[int] = 20
    diversity_preference: Optional[float] = 0.35

class ClientLogEntry(BaseModel):
    level: Optional[str] = "error"
    message: str
    source: Optional[str] = None
    url: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

class ContentFeedbackRequest(BaseModel):
    claim_id: str

class ChallengeCreateRequest(BaseModel):
    title: str
    description: str
    challenge_type: str  # yes_no, multiple_choice, prediction
    options: Optional[List[str]] = None
    duration_hours: Optional[int] = 24
    resolve_hours: Optional[int] = 48

class ChallengePredictionRequest(BaseModel):
    prediction: str
    confidence_level: Optional[float] = 50.0

# Auth utilities
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        'user_id': user_id,
        'exp': expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

RELATED_DOMAIN_MAP = {
    "Technology": ["Science", "Economics"],
    "Science": ["Health", "Technology"],
    "Health": ["Science", "Society"],
    "Politics": ["Economics", "Society"],
    "Economics": ["Politics", "Technology"],
    "Environment": ["Science", "Politics"],
    "Society": ["Politics", "Health"],
    "History": ["Politics", "Society"],
    "Entertainment": ["Society", "Technology"],
    "Sports": ["Health", "Society"],
    "Geography": ["History", "Environment"]
}

# Valid domain classifications for claims
VALID_DOMAINS = [
    "Science", "Health", "Technology", "Politics", "Economics",
    "Environment", "History", "Society", "Sports", "Entertainment",
    "Education", "Geography", "Food", "Law", "Religion", "General"
]

# Domain classification keywords for fallback method
DOMAIN_KEYWORDS = {
    "Science": ["scientific", "research", "study", "evidence", "experiment", "data", "scientists", "biology", "physics", "chemistry", "nasa", "rover", "mars", "space"],
    "Health": ["health", "medical", "disease", "vaccine", "treatment", "medicine", "exercise", "wellness", "mental", "physical", "doctor", "hospital"],
    "Technology": ["technology", "tech", "software", "digital", "computer", "internet", "AI", "electric", "innovation", "device", "app", "smartphone"],
    "Politics": ["political", "government", "election", "policy", "law", "president", "congress", "vote", "democracy", "parliament", "senator"],
    "Economics": ["economic", "economy", "financial", "market", "trade", "poverty", "wealth", "GDP", "inflation", "business", "stock", "investment"],
    "Environment": ["environment", "climate", "pollution", "renewable", "energy", "nature", "conservation", "sustainability", "carbon", "emissions"],
    "History": ["historical", "history", "ancient", "past", "century", "war", "empire", "civilization", "pyramids", "medieval", "dynasty"],
    "Society": ["social", "society", "culture", "community", "people", "demographic", "population", "equality", "rights"],
    "Sports": ["sport", "football", "basketball", "soccer", "olympics", "athlete", "team", "championship", "match", "player"],
    "Entertainment": ["movie", "film", "music", "celebrity", "actor", "singer", "concert", "album", "game", "netflix"],
    "Geography": ["country", "city", "continent", "river", "mountain", "ocean", "india", "china", "america", "europe", "kolkata", "delhi"]
}

def normalize_interest_domain(domain: Optional[str]) -> Optional[str]:
    if not domain:
        return None
    return domain.strip()

def extract_claim_domain(claim: Dict[str, Any]) -> Optional[str]:
    domain = claim.get('domain')
    if domain:
        return normalize_interest_domain(domain)
    category = claim.get('category') or {}
    primary_path = category.get('primary_path') if isinstance(category, dict) else None
    if primary_path and isinstance(primary_path, list) and primary_path:
        return normalize_interest_domain(primary_path[0])
    return None

async def update_user_interests(
    user_id: str,
    query: Optional[str],
    intent_domains: List[str],
    claim_domains: List[str],
    query_weight: int = 3,
    claim_weight: int = 1
):
    if not db:
        return
    now_iso = datetime.now(timezone.utc).isoformat()
    inc_ops: Dict[str, int] = {}

    for domain in intent_domains:
        normalized = normalize_interest_domain(domain)
        if not normalized:
            continue
        key = f"interests.{normalized}"
        inc_ops[key] = inc_ops.get(key, 0) + query_weight

    for domain in claim_domains:
        normalized = normalize_interest_domain(domain)
        if not normalized:
            continue
        key = f"interests.{normalized}"
        inc_ops[key] = inc_ops.get(key, 0) + claim_weight

    update_doc: Dict[str, Any] = {
        "$set": {"updated_at": now_iso},
        "$setOnInsert": {"user_id": user_id, "created_at": now_iso}
    }

    if inc_ops:
        update_doc["$inc"] = inc_ops

    if query:
        update_doc["$push"] = {
            "recent_queries": {
                "$each": [{"query": query, "created_at": now_iso}],
                "$slice": -20
            }
        }

    await db.user_interests.update_one({"user_id": user_id}, update_doc, upsert=True)

def build_interest_query(domains: List[str]) -> str:
    if not domains:
        return "Recent posts about varied topics"
    return f"Posts about {', '.join(domains)}"

async def enrich_claim_for_discovery(claim: Dict[str, Any]) -> Dict[str, Any]:
    author = await db.users.find_one({"id": claim['author_id']}, {"_id": 0, "password": 0})
    annotations = await db.annotations.find({"claim_id": claim['id']}, {"_id": 0}).to_list(length=1000)

    post_score = calculate_post_score(annotations, claim.get('baseline_evaluation'), claim.get('author_id'))
    impact_score = min(100, max(0, (post_score / 15.0) * 100))

    claim['impact_score'] = impact_score
    claim['author_reputation'] = author.get('reputation_score', DEFAULT_AUTHOR_REPUTATION) if author else DEFAULT_AUTHOR_REPUTATION
    claim['author_standing'] = author.get('user_standing_score', 1.0) if author else 1.0

    helpful_votes_total = sum(a.get('helpful_votes', 0) for a in annotations)
    controversial_votes_total = sum(a.get('not_helpful_votes', 0) for a in annotations)
    claim['helpful_votes_total'] = helpful_votes_total
    claim['controversial_votes_total'] = controversial_votes_total
    claim['annotation_count'] = len(annotations)

    return claim

def normalize_search_query(query: str) -> str:
    sanitized = InputValidator.sanitize_text(query, max_length=80)
    return sanitized.strip()

async def build_search_suggestions(query: str, limit: int) -> List[Dict[str, Any]]:
    normalized = normalize_search_query(query)
    if len(normalized) < 2:
        return []

    cache_key = f"{normalized}:{limit}"
    cached = _cache_get(_suggestion_cache, cache_key, max_age=60)  # 60s cache
    if cached is not None:
        return cached

    suggestions: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def add_suggestion(suggestion_type: str, text: str) -> None:
        key = text.lower()
        if key in seen:
            return
        seen.add(key)
        suggestions.append({"type": suggestion_type, "text": text})

    for domain in VALID_DOMAINS:
        if normalized.lower() in domain.lower():
            add_suggestion("domain", domain)

    if db:
        regex = re.escape(normalized)
        match = {"$regex": regex, "$options": "i"}
        claims = await db.claims.find(
            {
                "$or": [
                    {"text": match},
                    {"domain": match},
                    {"category.primary_path": {"$elemMatch": match}}
                ]
            },
            {"_id": 0, "domain": 1, "category": 1}
        ).limit(50).to_list(length=50)

        for claim in claims:
            domain = extract_claim_domain(claim)
            if domain:
                add_suggestion("topic", domain)
            if len(suggestions) >= limit:
                break

    if not suggestions:
        add_suggestion("query", normalized)

    result = suggestions[:limit]
    _cache_set(_suggestion_cache, cache_key, result)
    return result

async def build_trending_topics(days: int, limit: int) -> List[Dict[str, Any]]:
    if db is None:
        return []

    safe_days = max(1, min(days, 30))
    safe_limit = max(1, min(limit, 10))
    cache_key = f"{safe_days}:{safe_limit}"
    cached = _cache_get(_trending_cache, cache_key, max_age=60)  # 60s cache
    if cached is not None:
        return cached

    cutoff_iso = (datetime.now(timezone.utc) - timedelta(days=safe_days)).isoformat()

    claims = await db.claims.find(
        {"created_at": {"$gte": cutoff_iso}},
        {"_id": 0, "domain": 1, "category": 1}
    ).to_list(length=2000)

    if not claims:
        claims = await db.claims.find(
            {},
            {"_id": 0, "domain": 1, "category": 1}
        ).sort("created_at", -1).limit(2000).to_list(length=2000)

    counts: Dict[str, int] = {}
    for claim in claims:
        domain = extract_claim_domain(claim)
        if domain:
            counts[domain] = counts.get(domain, 0) + 1

    sorted_domains = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    trending = [
        {"topic": domain, "count": count}
        for domain, count in sorted_domains[:safe_limit]
    ]
    _cache_set(_trending_cache, cache_key, trending)
    return trending

def require_admin_key(x_admin_key: Optional[str] = Header(None)):
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=503, detail="Admin API key not configured")
    if not x_admin_key or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = decode_jwt_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional)):
    if not credentials or not credentials.credentials:
        return None
    user_id = decode_jwt_token(credentials.credentials)
    if not user_id:
        return None
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    return user

# AI Detection (Hive AI)
async def detect_ai_content(file_path: str, file_type: str) -> tuple[bool, float]:
    """Detect AI-generated content using Hive AI API"""
    hive_api_key = os.environ.get('HIVE_API_KEY')
    
    if not hive_api_key:
        # Return mock result if no API key
        return False, 0.0
    
    try:
        url = "https://api.hivemoderation.com/api/v1/functions/image_check"
        headers = {
            "authorization": f"token {hive_api_key}",
            "accept": "application/json"
        }
        
        with open(file_path, "rb") as f:
            files = {'image': (Path(file_path).name, f, file_type)}
            response = requests.post(url, files=files, headers=headers, timeout=30)
            response.raise_for_status()
        
        data = response.json()
        
        is_ai_generated = False
        confidence = 0.0
        
        if 'class_scores' in data:
            for detection in data['class_scores']:
                if detection.get('class') == 'ai_generated':
                    confidence = detection.get('score', 0)
                    is_ai_generated = confidence > 0.5
        
        return is_ai_generated, confidence
    
    except Exception as e:
        logging.error(f"AI detection error: {str(e)}")
        return False, 0.0

# Post score calculation (based on engagement and signals, not truth)
def calculate_post_score(annotations: List[Dict], baseline_eval: Optional[Dict[str, Any]] = None, claim_author_id: Optional[str] = None) -> float:
    """Calculate post score based on community engagement and content quality signals
    
    Args:
        annotations: List of annotations with author information
        baseline_eval: Baseline evaluation containing signal scores
        claim_author_id: ID of the claim author (to exclude self-annotations)
    
    Returns:
        Post score (0+ range, never negative)
    """
    # Start with baseline evaluation score if available
    base_score = 0.0
    if baseline_eval:
        clarity = baseline_eval.get('clarity_score', 0)
        originality = baseline_eval.get('originality_score', 0)
        relevance = baseline_eval.get('relevance_score', 0)
        effort = baseline_eval.get('effort_score', 0)
        evidentiary = baseline_eval.get('evidentiary_value_score', 0)
        
        # Average of signals (0-100) normalized to 0-10 range
        base_score = ((clarity + originality + relevance + effort + evidentiary) / 5) / 10
    
    # Add community engagement bonus
    engagement_score = 0.0
    valid_annotation_count = 0
    helpful_vote_total = 0

    support_weight = 0.0
    contradict_weight = 0.0

    for ann in annotations:
        # Skip self-annotations
        if claim_author_id and ann.get('author_id') == claim_author_id:
            continue

        valid_annotation_count += 1
        helpful_votes = ann.get('helpful_votes', 0)
        not_helpful_votes = ann.get('not_helpful_votes', 0)
        helpful_vote_total += helpful_votes

        # Weight by author reputation and classifier confidence (smart separation)
        author_rep = DEFAULT_AUTHOR_REPUTATION
        if ann.get('author') and isinstance(ann.get('author'), dict):
            author_rep = ann.get('author', {}).get('reputation_score', DEFAULT_AUTHOR_REPUTATION)
        else:
            author_rep = ann.get('author_reputation', DEFAULT_AUTHOR_REPUTATION)
        rep_factor = min(ANNOTATION_WEIGHT_MAX, max(ANNOTATION_REPUTATION_FACTOR_BASE, author_rep / 10.0))
        confidence = ann.get('classification_confidence', 0.5)
        confidence_factor = ANNOTATION_CONFIDENCE_FACTOR_BASE + (ANNOTATION_CONFIDENCE_FACTOR_SCALE * min(1.0, max(0.0, confidence)))

        weight = max(ANNOTATION_WEIGHT_MIN, (1.0 + (helpful_votes * ANNOTATION_WEIGHT_HELPFUL_VOTE_FACTOR) - (not_helpful_votes * ANNOTATION_WEIGHT_NOT_HELPFUL_FACTOR)) * rep_factor * confidence_factor)
        ann_type = ann.get('annotation_type')

        # Require evidence to influence score (avoid single weak "no")
        has_evidence = (helpful_votes >= ANNOTATION_HELPFUL_VOTES_THRESHOLD) or (author_rep >= ANNOTATION_AUTHOR_REP_THRESHOLD) or (confidence >= ANNOTATION_CONFIDENCE_THRESHOLD)
        if ann_type == 'support':
            support_weight += weight if has_evidence else (weight * ANNOTATION_WEAK_EVIDENCE_PENALTY)
        elif ann_type == 'contradict':
            contradict_weight += weight if has_evidence else (weight * ANNOTATION_WEAK_EVIDENCE_PENALTY)

    # Engagement bonus: annotations + helpful votes
    engagement_score = min(ENGAGEMENT_BONUS_MAX, (valid_annotation_count * ENGAGEMENT_ANNOTATION_WEIGHT) + (helpful_vote_total * ENGAGEMENT_HELPFUL_VOTE_WEIGHT))

    # Stance adjustment: support raises, contradict lowers
    stance_adjust = max(-STANCE_ADJUSTMENT_MAX, min(STANCE_ADJUSTMENT_MAX, (support_weight * STANCE_SUPPORT_SCALE - contradict_weight * STANCE_CONTRADICT_SCALE) * STANCE_ADJUSTMENT_SCALE))

    total_score = base_score + engagement_score + stance_adjust
    return max(0.0, total_score)
# Auth endpoints
@api_router.post("/auth/register")
@limiter.limit("5/hour")  # Limit registration attempts
async def register(request: Request, user_data: UserCreate, standard: bool = False):
    # Validate inputs
    email = InputValidator.validate_email(user_data.email)
    username = InputValidator.validate_username(user_data.username)
    password = InputValidator.validate_password(user_data.password)
    
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check username availability
    existing_username = await db.users.find_one({"username": username}, {"_id": 0})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(password)
    
    user = {
        "id": user_id,
        "username": username,
        "email": email,
        "password": hashed_pw,
        "reputation_score": INITIAL_USER_REPUTATION,
        "contribution_stats": {
            "claims_posted": 0,
            "annotations_added": 0,
            "helpful_votes_received": 0
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    
    token = create_jwt_token(user_id)
    
    response_data = {
        "token": token,
        "user": {
            "id": user_id,
            "username": username,
            "email": email,
            "reputation_score": INITIAL_USER_REPUTATION
        }
    }

    if standard:
        return standardize_single_response(response_data)

    return response_data

@api_router.post("/auth/login")
@limiter.limit("10/minute")  # Prevent brute force attacks
async def login(request: Request, credentials: UserLogin, standard: bool = False):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_jwt_token(user['id'])
    
    response_data = {
        "token": token,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "bio": user.get('bio', ''),
            "reputation_score": user['reputation_score'],
            "profile_picture": user.get('profile_picture')
        }
    }

    if standard:
        return standardize_single_response(response_data)

    return response_data

@api_router.get("/auth/me")
async def get_me(current_user = Depends(get_current_user), standard: bool = False):
    response_data = {
        "id": current_user['id'],
        "username": current_user['username'],
        "email": current_user['email'],  # Email only visible to the user themselves
        "bio": current_user.get('bio', ''),
        "reputation_score": current_user['reputation_score'],
        "contribution_stats": current_user['contribution_stats'],
        "profile_picture": current_user.get('profile_picture')
    }

    if standard:
        return standardize_single_response(response_data)

    return response_data

# Media upload
@api_router.post("/media/upload")
@limiter.limit("30/hour")  # Limit file uploads
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    standard: bool = False
):
    # Validate file
    contents = await file.read()
    validate_media_file(file.filename, file.content_type, len(contents))
    
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix.lower()
    s3_key = None
    
    # Sanitize extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.mp4', '.webm', '.ogg', '.mov']
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    
    temp_path = None
    if USE_S3:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(contents)
                temp_path = temp_file.name
            # Detect AI-generated content before upload
            is_ai, confidence = await detect_ai_content(temp_path, file.content_type)
            s3_key = f"{AWS_S3_MEDIA_PREFIX}{file_id}{file_ext}"
            file_path = await s3_upload_file(temp_path, s3_key, file.content_type)
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    logger.warning(f"Failed to remove temp file {temp_path}")
    else:
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
        # Save file
        with open(file_path, 'wb') as f:
            f.write(contents)
        # Detect AI-generated content
        is_ai, confidence = await detect_ai_content(str(file_path), file.content_type)
    
    media = {
        "id": file_id,
        "file_path": str(file_path),
        "file_name": file.filename,
        "file_type": file.content_type,
        "is_ai_generated": is_ai,
        "ai_confidence": confidence,
        "storage": "s3" if USE_S3 else "local",
        "s3_bucket": AWS_S3_BUCKET if USE_S3 else None,
        "s3_key": s3_key if USE_S3 else None,
        "s3_region": AWS_REGION if USE_S3 else None,
        "uploaded_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.media.insert_one(media)
    
    response_data = {
        "id": file_id,
        "file_name": file.filename,
        "file_type": file.content_type,
        "is_ai_generated": is_ai,
        "ai_confidence": confidence
    }

    if standard:
        return standardize_single_response(response_data)

    return response_data

# Media serving
@api_router.get("/media/{media_id}")
async def get_media(media_id: str):
    from fastapi.responses import FileResponse
    
    media = await db.media.find_one({"id": media_id}, {"_id": 0})
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    file_path = media['file_path']
    if is_s3_uri(file_path):
        bucket, key = parse_s3_uri(file_path)
        signed_url = await s3_generate_presigned_url(bucket, key)
        return RedirectResponse(signed_url, status_code=302)
    
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, media_type=media['file_type'])

# AI Domain Classification
async def classify_claim_domain(claim_text: str, media_files: list = None) -> str:
    """Use GPT-5.2 to intelligently classify the claim into a domain"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    import json
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    if not api_key:
        # Fallback to keyword-based if no API key
        return await classify_claim_domain_fallback(claim_text)
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"domain-{uuid.uuid4().hex[:8]}",
            system_message="""You are an expert content classifier for Thrryv, a fact-checking platform.
Your job is to analyze content (text and media) and classify it into the most appropriate domain.

Available domains:
- Science: Scientific research, discoveries, experiments, studies, natural phenomena
- Health: Medical topics, wellness, diseases, treatments, mental health, fitness
- Technology: Tech innovations, software, AI, gadgets, digital trends, computing
- Politics: Government, elections, policies, political figures, legislation
- Economics: Finance, markets, trade, business, economic trends, wealth
- Environment: Climate, ecology, conservation, sustainability, pollution
- History: Historical events, ancient civilizations, past figures, heritage
- Society: Social issues, culture, demographics, community topics
- Sports: Athletic events, sports figures, competitions, fitness activities
- Entertainment: Movies, music, celebrities, arts, media, gaming
- Education: Learning, schools, academic topics, research institutions
- Geography: Places, countries, cities, landmarks, travel
- Food: Cuisine, nutrition, cooking, restaurants, dietary topics
- Law: Legal matters, justice, crime, regulations, court cases
- Religion: Faith, spirituality, religious practices, theology

Analyze the content carefully. Consider:
1. The main subject matter
2. Key entities mentioned
3. The context and intent
4. Any media content that provides additional context

Respond ONLY with a JSON object:
{"domain": "<chosen domain>", "confidence": <0.0-1.0>, "reasoning": "<brief explanation>"}"""
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"Classify this content into the most appropriate domain:\n\nTEXT: {claim_text}"
        
        # Add media analysis if available
        message_content = UserMessage(text=prompt)
        if media_files and len(media_files) > 0:
            try:
                import base64
                first_media = media_files[0]
                media_base64 = base64.b64encode(first_media['data']).decode('utf-8')
                message_content = UserMessage(
                    text=prompt + "\n\n[An image/video is attached - analyze it for context]",
                    file_contents=[ImageContent(image_base64=media_base64)]
                )
            except Exception as e:
                logging.warning(f"Could not include media in classification: {e}")
        
        response = await chat.send_message(message_content)
        
        # Parse response
        response_text = response.strip()
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        
        result = json.loads(response_text)
        domain = result.get('domain', 'General')
        
        # Validate domain is in our list
        if domain not in VALID_DOMAINS:
            domain = "General"
            
        logging.info(f"AI Domain Classification: {domain} (confidence: {result.get('confidence', 'N/A')}, reason: {result.get('reasoning', 'N/A')})")
        return domain
        
    except Exception as e:
        logging.error(f"AI domain classification failed: {e}")
        return await classify_claim_domain_fallback(claim_text)


async def classify_claim_domain_fallback(claim_text: str) -> str:
    """Fallback keyword-based classification using predefined domain keywords"""
    claim_lower = claim_text.lower()
    domain_scores = {}
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in claim_lower)
        if score > 0:
            domain_scores[domain] = score
    
    if domain_scores:
        return max(domain_scores, key=domain_scores.get)
    
    return "General"

# Claims
@api_router.post("/claims")
@limiter.limit("20/hour")  # Prevent spam
async def create_claim(
    request: Request,
    claim_data: ClaimCreate,
    current_user = Depends(get_current_user),
    standard: bool = False
):
    # Validate and sanitize inputs
    claim_text = InputValidator.sanitize_text(claim_data.text, max_length=5000)
    InputValidator.validate_word_count(claim_text, max_words=250)
    confidence = InputValidator.validate_confidence_level(claim_data.confidence_level)
    
    claim_id = str(uuid.uuid4())
    
    # Get media objects and prepare for AI evaluation
    media_list = []
    media_files_for_eval = []
    
    if claim_data.media_ids:
        for media_id in claim_data.media_ids:
            media = await db.media.find_one({"id": media_id}, {"_id": 0})
            if media:
                # Validate that media belongs to current user (prevents accessing others' media)
                if media.get('user_id') != current_user['id']:
                    raise HTTPException(status_code=403, detail="You do not have permission to use this media")
                
                media_list.append(media)
                # Read media file for AI evaluation
                try:
                    media_data = await load_media_bytes(media)
                    if media_data:
                        media_files_for_eval.append({
                            'data': media_data,
                            'type': media.get('file_type', 'image/jpeg')
                        })
                except Exception as e:
                    logging.warning(f"Could not read media file for evaluation: {e}")
    
    # Hierarchical content categorization
    category_result = None
    try:
        cat_result = await categorize_claim_content(claim_data.text, media_files_for_eval)
        # Store only the primary tag for simplicity
        primary_tag = cat_result.primary_category.path[0] if cat_result.primary_category.path else "General"
        category_result = {
            "primary_path": [primary_tag],
            "primary_full": primary_tag,
            "primary_confidence": cat_result.primary_category.confidence,
            "primary_reasoning": cat_result.primary_category.reasoning,
            "content_format": cat_result.content_format,
            "is_informal": cat_result.is_informal
        }
        ai_domain = primary_tag
        primary_domain = primary_tag
        
        logging.info(f"Tag: {primary_tag}")
    except Exception as e:
        logging.error(f"Categorization failed: {e}")
        # Fallback to simple domain
        ai_domain = await classify_claim_domain(claim_data.text, media_files_for_eval)
        primary_domain = ai_domain
        category_result = {
            "primary_path": [ai_domain],
            "primary_full": ai_domain,
            "primary_confidence": 0.5,
            "primary_reasoning": "Fallback classification"
        }
    
    # Run AI Baseline Reputation Evaluation (for quality signals)
    reputation_boost = 0.0
    evaluation_result = None
    
    try:
        eval_result = await evaluate_claim_for_reputation(
            text=claim_data.text,
            domain=primary_domain if 'primary_domain' in dir() else ai_domain,
            media_files=media_files_for_eval
        )
        
        reputation_boost = eval_result.reputation_boost
        evaluation_result = {
            "reputation_boost": eval_result.reputation_boost,
            "qualifies_for_boost": eval_result.qualifies_for_boost,
            "clarity_score": eval_result.clarity_score,
            "originality_score": eval_result.originality_score,
            "relevance_score": eval_result.relevance_score,
            "effort_score": eval_result.effort_score,
            "evidentiary_value_score": eval_result.evidentiary_value_score,
            "media_value_score": eval_result.media_value_score,
            "content_type": eval_result.content_type.value,
            "evaluation_summary": eval_result.evaluation_summary
        }
        
        logging.info(f"AI Evaluation for claim {claim_id}: boost={reputation_boost}, qualifies={eval_result.qualifies_for_boost}")
    except Exception as e:
        logging.error(f"AI Reputation Evaluation failed: {e}")
        evaluation_result = {
            "reputation_boost": 0.0,
            "qualifies_for_boost": False,
            "evaluation_summary": "Evaluation temporarily unavailable"
        }
    
    # Calculate initial post score based on baseline evaluation
    initial_post_score = 0.0
    if evaluation_result:
        clarity = evaluation_result.get('clarity_score', 0)
        originality = evaluation_result.get('originality_score', 0)
        relevance = evaluation_result.get('relevance_score', 0)
        effort = evaluation_result.get('effort_score', 0)
        evidentiary = evaluation_result.get('evidentiary_value_score', 0)
        
        # Average of signals (0-100) normalized to 0-10 range
        initial_post_score = ((clarity + originality + relevance + effort + evidentiary) / 5) / 10
        initial_post_score = min(15.0, max(0.0, initial_post_score))
        # Bucket initial score into 2-5 or 6-15 bands
        if initial_post_score < 2.0:
            initial_post_score = 2.0
        elif initial_post_score <= 5.0:
            initial_post_score = initial_post_score
        elif initial_post_score < 6.0:
            initial_post_score = 6.0
        elif initial_post_score > 15.0:
            initial_post_score = 15.0
    
    claim = {
        "id": claim_id,
        "text": claim_text,
        "domain": ai_domain,  # Full hierarchical path
        "category": category_result,  # Full category information
        "confidence_level": confidence,
        "author_id": current_user['id'],
        "media_ids": claim_data.media_ids or [],
        "post_score": initial_post_score,  # Signal-based score (0-15 range)
        "baseline_evaluation": evaluation_result,  # Store AI evaluation
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.claims.insert_one(claim)
    
    # Update user stats and apply reputation boost with bounds
    new_reputation = current_user['reputation_score']
    if reputation_boost > 0:
        new_reputation = clamp_reputation(current_user['reputation_score'] + reputation_boost)
    
    await db.users.update_one(
        {"id": current_user['id']},
        {"$inc": {"contribution_stats.claims_posted": 1}, "$set": {"reputation_score": new_reputation}}
    )
    
    response_data = {
        "id": claim_id,
        "text": claim_text,
        "domain": ai_domain,
        "category": category_result,
        "author": {
            "id": current_user['id'],
            "username": current_user['username'],
            "reputation_score": new_reputation
        },
        "media": media_list,
        "post_score": initial_post_score,
        "baseline_evaluation": evaluation_result
    }

    if standard:
        return standardize_single_response(response_data)

    return response_data

async def build_claim_feed_item(claim: Dict[str, Any]) -> Dict[str, Any]:
    author = await db.users.find_one({"id": claim['author_id']}, {"_id": 0, "password": 0})
    annotations = await db.annotations.find({"claim_id": claim['id']}, {"_id": 0}).to_list(length=1000)

    # Bulk fetch media instead of one by one (fixes N+1 query)
    media_ids = claim.get('media_ids', [])
    media_list = []
    if media_ids:
        media_docs = await db.media.find({"id": {"$in": media_ids}}, {"_id": 0}).to_list(length=len(media_ids))
        # Keep original order from media_ids
        media_by_id = {m['id']: m for m in media_docs}
        media_list = [media_by_id[mid] for mid in media_ids if mid in media_by_id]

    # Use stored post_score from claim to avoid redundant calculation
    post_score = claim.get('post_score', 0.0)

    top_annotations = sorted(
        annotations,
        key=lambda a: (a.get('helpful_votes', 0), a.get('created_at', '')),
        reverse=True
    )[:2]
    
    # Bulk fetch annotation authors (fixes N+1 query)
    annotation_author_ids = [ann['author_id'] for ann in top_annotations]
    annotation_authors = {}
    if annotation_author_ids:
        author_docs = await db.users.find(
            {"id": {"$in": annotation_author_ids}},
            {"_id": 0, "password": 0}
        ).to_list(length=len(annotation_author_ids))
        annotation_authors = {u['id']: u for u in author_docs}
    
    top_annotation_cards = []
    for ann in top_annotations:
        ann_author = annotation_authors.get(ann['author_id'])
        top_annotation_cards.append({
            "id": ann['id'],
            "text": ann['text'],
            "annotation_type": ann.get('annotation_type', 'context'),
            "helpful_votes": ann.get('helpful_votes', 0),
            "author": {
                "id": ann_author['id'] if ann_author else ann['author_id'],
                "username": ann_author.get('username') if ann_author else 'Unknown'
            }
        })

    return {
        "id": claim['id'],
        "text": claim['text'],
        "domain": claim['domain'],
        "confidence_level": claim['confidence_level'],
        "author": {
            "id": author.get('id') if author else claim.get('author_id', 'Unknown'),
            "username": author.get('username') if author else 'Unknown',
            "reputation_score": author.get('reputation_score', 0) if author else 0
        },
        "media": media_list,
        "post_score": post_score,
        "credibility_score": post_score,
        "top_annotations": top_annotation_cards,
        "baseline_evaluation": claim.get('baseline_evaluation'),
        "category": claim.get('category'),
        "annotation_count": len(annotations),
        "created_at": claim['created_at']
    }

@api_router.get("/claims")
async def get_claims(limit: int = 20, offset: int = 0, standard: bool = False):
    """Get paginated list of claims"""
    claims = await db.claims.find({}, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
    
    result = []
    for claim in claims:
        result.append(await build_claim_feed_item(claim))
    
    if standard:
        total = await db.claims.count_documents({})
        return standardize_list_response(result, limit, offset, total)
    
    return result

@api_router.get("/claims/{claim_id}")
async def get_claim(claim_id: str, standard: bool = False):
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    author = await db.users.find_one({"id": claim['author_id']}, {"_id": 0, "password": 0})
    annotations = await db.annotations.find({"claim_id": claim_id}, {"_id": 0}).to_list(length=1000)
    
    # Bulk load media (avoids N+1 queries)
    media_ids = claim.get('media_ids', [])
    media_list = []
    if media_ids:
        media_docs = await db.media.find({"id": {"$in": media_ids}}, {"_id": 0}).to_list(length=len(media_ids))
        media_by_id = {m['id']: m for m in media_docs}
        media_list = [media_by_id[mid] for mid in media_ids if mid in media_by_id]
    
    # Use stored post_score to avoid redundant calculation
    post_score = claim.get('post_score', 0.0)
    
    response_data = {
        "id": claim['id'],
        "text": claim['text'],
        "domain": claim['domain'],
        "category": claim.get('category'),
        "confidence_level": claim['confidence_level'],
        "author": {
            "id": author.get('id') if author else claim.get('author_id', 'Unknown'),
            "username": author.get('username') if author else 'Unknown',
            "reputation_score": author.get('reputation_score', 0) if author else 0
        },
        "media": media_list,
        "post_score": post_score,
        "credibility_score": post_score,  # Kept for backwards compatibility
        "baseline_evaluation": claim.get('baseline_evaluation'),
        "annotation_count": len(annotations),
        "created_at": claim['created_at']
    }

    if standard:
        return standardize_single_response(response_data)
    
    return response_data

# Annotations
@api_router.post("/claims/{claim_id}/annotations")
@limiter.limit("30/hour")  # Prevent annotation spam
async def create_annotation(
    request: Request,
    claim_id: str,
    annotation_data: AnnotationCreate,
    current_user = Depends(get_current_user)
):
    # Validate inputs
    claim_id = InputValidator.validate_uuid(claim_id)
    annotation_text = InputValidator.sanitize_text(annotation_data.text, max_length=2000)
    
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Auto-classify annotation type with AI
    classification = await classify_annotation_type(
        claim_text=claim['text'],
        annotation_text=annotation_text
    )
    
    classified_type = classification.get('annotation_type', 'context')
    classification_confidence = float(classification.get('confidence', 0.5) or 0.5)
    
    annotation_id = str(uuid.uuid4())
    
    media_list = []
    if annotation_data.media_ids:
        for media_id in annotation_data.media_ids:
            media = await db.media.find_one({"id": media_id}, {"_id": 0})
            if media:
                media_list.append(media)
    
    annotation = {
        "id": annotation_id,
        "claim_id": claim_id,
        "author_id": current_user['id'],
        "author_reputation": current_user.get('reputation_score', DEFAULT_AUTHOR_REPUTATION),
        "text": annotation_text,
        "annotation_type": classified_type,
        "classification_confidence": classification_confidence,
        "media_ids": annotation_data.media_ids or [],
        "helpful_votes": 0,
        "not_helpful_votes": 0,
        "voted_by": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.annotations.insert_one(annotation)
    
    # Update user stats
    await db.users.update_one(
        {"id": current_user['id']},
        {"$inc": {"contribution_stats.annotations_added": 1}}
    )
    
    # Create notification for claim owner (if not self)
    if claim['author_id'] != current_user['id']:
        notification_type_map = {
            'support': 'supported',
            'contradict': 'contradicted',
            'context': 'added context to'
        }
        action_text = notification_type_map.get(classified_type, 'annotated')
        
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": claim['author_id'],
            "type": "annotation",
            "annotation_type": classified_type,
            "claim_id": claim_id,
            "claim_preview": claim['text'][:80] + "..." if len(claim['text']) > 80 else claim['text'],
            "from_user_id": current_user['id'],
            "from_username": current_user['username'],
            "message": f"{current_user['username']} {action_text} your claim",
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification)
    
    # Recalculate post score based on new annotations
    all_annotations = await db.annotations.find({"claim_id": claim_id}, {"_id": 0}).to_list(length=1000)
    
    # Bulk fetch annotation authors instead of one by one (fixes N+1 query)
    annotation_author_ids = [ann['author_id'] for ann in all_annotations]
    annotation_authors = {}
    if annotation_author_ids:
        author_docs = await db.users.find(
            {"id": {"$in": annotation_author_ids}},
            {"_id": 0}
        ).to_list(length=len(annotation_author_ids))
        annotation_authors = {u['id']: u for u in author_docs}
    
    # Enrich annotations with author data
    enriched_annotations = []
    for ann in all_annotations:
        author = annotation_authors.get(ann['author_id'])
        enriched_annotations.append({
            **ann,
            "author": author
        })
    
    # Calculate new post score
    post_score = calculate_post_score(enriched_annotations, claim.get('baseline_evaluation'), claim.get('author_id'))
    
    await db.claims.update_one(
        {"id": claim_id},
        {"$set": {"post_score": post_score}}
    )
    
    response_data = {
        "id": annotation_id,
        "claim_id": claim_id,
        "author": {
            "id": current_user['id'],
            "username": current_user['username'],
            "reputation_score": current_user['reputation_score']
        },
        "text": annotation_data.text,
        "annotation_type": classified_type,
        "media": media_list,
        "helpful_votes": 0,
        "not_helpful_votes": 0
    }
    
    return response_data

@api_router.get("/claims/{claim_id}/annotations")
async def get_annotations(claim_id: str, skip: int = 0, limit: int = 1000, standard: bool = False):
    annotations = await db.annotations.find({"claim_id": claim_id}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    result = []
    for ann in annotations:
        author = await db.users.find_one({"id": ann['author_id']}, {"_id": 0, "password": 0})
        
        media_list = []
        for media_id in ann.get('media_ids', []):
            media = await db.media.find_one({"id": media_id}, {"_id": 0})
            if media:
                media_list.append(media)
        
        result.append({
            "id": ann['id'],
            "claim_id": ann['claim_id'],
            "author": {
                "id": author['id'],
                "username": author['username'],
                "reputation_score": author['reputation_score']
            },
            "text": ann['text'],
            "annotation_type": ann['annotation_type'],
            "media": media_list,
            "helpful_votes": ann['helpful_votes'],
            "not_helpful_votes": ann['not_helpful_votes'],
            "created_at": ann['created_at']
        })

    if standard:
        total = await db.annotations.count_documents({"claim_id": claim_id})
        return standardize_list_response(result, limit, skip, total)
    
    return result

# Vote on annotations
@api_router.post("/annotations/{annotation_id}/vote")
@limiter.limit("100/hour")  # Prevent vote spam
async def vote_annotation(
    annotation_id: str,
    helpful: bool,
    request: Request,
    current_user = Depends(get_current_user)
):
    annotation = await db.annotations.find_one({"id": annotation_id}, {"_id": 0})
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    # Check if user already voted
    voted_by = annotation.get('voted_by', [])
    if current_user['id'] in voted_by:
        raise HTTPException(status_code=400, detail="You have already voted on this annotation")
    
    # Update vote count
    if helpful:
        await db.annotations.update_one(
            {"id": annotation_id},
            {"$inc": {"helpful_votes": 1}, "$push": {"voted_by": current_user['id']}}
        )
        
        # Update annotation author's reputation with time-based bonus
        author_id = annotation['author_id']
        annotation_created = datetime.fromisoformat(annotation['created_at'])
        days_old = (datetime.now(timezone.utc) - annotation_created).days
        
        # Aging well bonus: older annotations that get helpful votes get more reputation
        # Base reputation gain + up to bonus points for aging well (maxes at specified days)
        time_bonus = min(VOTE_TIME_BONUS_MAX, days_old / VOTE_TIME_BONUS_DAYS)
        reputation_gain = VOTE_REPUTATION_GAIN_BASE + time_bonus
        
        # Get current reputation and apply bounds
        author = await db.users.find_one({"id": author_id}, {"_id": 0, "reputation_score": 1})
        current_rep = author.get('reputation_score', DEFAULT_AUTHOR_REPUTATION) if author else DEFAULT_AUTHOR_REPUTATION
        new_rep = clamp_reputation(current_rep + reputation_gain)
        
        await db.users.update_one(
            {"id": author_id},
            {"$set": {"reputation_score": new_rep}, "$inc": {"contribution_stats.helpful_votes_received": 1}}
        )
    else:
        await db.annotations.update_one(
            {"id": annotation_id},
            {"$inc": {"not_helpful_votes": 1}, "$push": {"voted_by": current_user['id']}}
        )
    
    # Recalculate claim credibility
    claim_id = annotation['claim_id']
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        # Claim was deleted - skip recalculation
        return {"message": "Vote recorded successfully"}
    
    all_annotations = await db.annotations.find({"claim_id": claim_id}, {"_id": 0}).to_list(length=1000)
    
    # Bulk fetch all annotation authors
    annotation_author_ids = [ann['author_id'] for ann in all_annotations]
    annotation_authors = {}
    if annotation_author_ids:
        author_docs = await db.users.find(
            {"id": {"$in": annotation_author_ids}},
            {"_id": 0}
        ).to_list(length=len(annotation_author_ids))
        annotation_authors = {u['id']: u for u in author_docs}
    
    enriched_annotations = []
    for ann in all_annotations:
        author = annotation_authors.get(ann['author_id'])
        enriched_annotations.append({
            **ann,
            "author": author
        })
    
    # Recalculate post score
    post_score = calculate_post_score(enriched_annotations, claim.get('baseline_evaluation'), claim.get('author_id'))
    
    await db.claims.update_one(
        {"id": claim_id},
        {"$set": {"post_score": post_score}}
    )
    
    return {"message": "Vote recorded successfully"}

# Profile picture upload
@api_router.post("/users/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    contents = await file.read()
    temp_path = None
    if USE_S3:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(contents)
                temp_path = temp_file.name
            s3_key = f"{AWS_S3_PROFILE_PREFIX}profile_{file_id}{file_ext}"
            file_path = await s3_upload_file(temp_path, s3_key, file.content_type)
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    logger.warning(f"Failed to remove temp file {temp_path}")
    else:
        file_path = UPLOAD_DIR / f"profile_{file_id}{file_ext}"
        # Save file
        with open(file_path, 'wb') as f:
            f.write(contents)
    
    # Update user's profile picture
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"profile_picture": str(file_path)}}
    )
    
    return {"profile_picture": file_id, "message": "Profile picture updated"}

# Serve profile pictures
@api_router.get("/users/profile-picture/{user_id}")
async def get_profile_picture(user_id: str):
    from fastapi.responses import FileResponse, JSONResponse
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user or not user.get('profile_picture'):
        # Return empty response - frontend will show default avatar
        return JSONResponse(status_code=204, content=None)
    
    file_path = user['profile_picture']
    if is_s3_uri(file_path):
        bucket, key = parse_s3_uri(file_path)
        signed_url = await s3_generate_presigned_url(bucket, key)
        return RedirectResponse(signed_url, status_code=302)
    
    if not Path(file_path).exists():
        # File referenced but doesn't exist - clear the reference and return 204
        await db.users.update_one(
            {"id": user_id},
            {"$unset": {"profile_picture": ""}}
        )
        return JSONResponse(status_code=204, content=None)
    
    return FileResponse(file_path)

# Update user settings
@api_router.patch("/users/settings")
@limiter.limit("30/hour")  # Prevent setting spam
async def update_user_settings(
    request: Request,
    settings: UserSettingsUpdate,
    current_user = Depends(get_current_user),
    standard: bool = False
):
    updates = {}
    username = settings.username
    bio = settings.bio
    current_password = settings.current_password
    new_password = settings.new_password
    
    # Update username
    if username and username != current_user['username']:
        username = InputValidator.validate_username(username)
        # Check if username is already taken
        existing = await db.users.find_one({"username": username, "id": {"$ne": current_user['id']}}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        updates["username"] = username
    
    # Update bio (max 60 characters)
    if bio is not None:
        bio = InputValidator.sanitize_text(bio, max_length=60)
        updates["bio"] = bio
    
    # Update password
    if current_password and new_password:
        if not verify_password(current_password, current_user['password']):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        new_password = InputValidator.validate_password(new_password)
        updates["password"] = hash_password(new_password)
    
    if updates:
        await db.users.update_one(
            {"id": current_user['id']},
            {"$set": updates}
        )
        
        # Return updated user data
        updated_user = await db.users.find_one({"id": current_user['id']}, {"_id": 0, "password": 0})
        response_data = {
            "message": "Settings updated successfully",
            "user": {
                "id": updated_user['id'],
                "username": updated_user['username'],
                "email": updated_user['email'],
                "bio": updated_user.get('bio', ''),
                "reputation_score": updated_user['reputation_score']
            }
        }
        if standard:
            return standardize_single_response(response_data, message="Settings updated successfully")
        return response_data
    
    if standard:
        return standardize_single_response({"message": "No changes made"}, message="No changes made")
    return {"message": "No changes made"}

# Check username availability and get suggestions
@api_router.get("/users/check-username/{username}")
async def check_username_availability(username: str, current_user = Depends(get_current_user)):
    # Check if username is same as current user's
    if username.lower() == current_user['username'].lower():
        return {"available": True, "suggestions": []}
    
    # Check if username is taken
    existing = await db.users.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}}, {"_id": 0})
    
    if not existing:
        return {"available": True, "suggestions": []}
    
    # Generate intelligent suggestions
    suggestions = []
    base_username = username.lower()
    
    # Add numbers
    for i in range(1, 100):
        suggestion = f"{base_username}{i}"
        exists = await db.users.find_one({"username": {"$regex": f"^{suggestion}$", "$options": "i"}}, {"_id": 0})
        if not exists:
            suggestions.append(suggestion)
            if len(suggestions) >= 3:
                break
    
    # Add underscores
    if len(suggestions) < 5:
        for suffix in ['_', '__', '_x', '_v2', '_real']:
            suggestion = f"{base_username}{suffix}"
            exists = await db.users.find_one({"username": {"$regex": f"^{suggestion}$", "$options": "i"}}, {"_id": 0})
            if not exists:
                suggestions.append(suggestion)
                if len(suggestions) >= 5:
                    break
    
    return {"available": False, "suggestions": suggestions[:5]}

# User profile (public view - no email)
@api_router.get("/users/{user_id}")
async def get_user_profile(user_id: str):
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's claims and annotations
    claims = await db.claims.find({"author_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(length=5)
    annotations = await db.annotations.find({"author_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(length=5)
    
    # Return public profile - NO email
    return {
        "id": user['id'],
        "username": user['username'],
        "bio": user.get('bio', ''),
        "reputation_score": user['reputation_score'],
        "contribution_stats": user['contribution_stats'],
        "created_at": user['created_at'],
        "profile_picture": user.get('profile_picture'),
        "recent_claims": claims,
        "recent_annotations": annotations
    }

# Get all user claims
@api_router.get("/users/{user_id}/claims")
async def get_user_claims(user_id: str, skip: int = 0, limit: int = 50, standard: bool = False):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    claims = await db.claims.find({"author_id": user_id}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    # Bulk fetch all media and annotations needed (fixes N+1 queries)
    all_media_ids = []
    claim_ids = []
    for claim in claims:
        all_media_ids.extend(claim.get('media_ids', []))
        claim_ids.append(claim['id'])
    
    # Fetch all media at once
    media_map = {}
    if all_media_ids:
        all_media = await db.media.find({"id": {"$in": all_media_ids}}, {"_id": 0}).to_list(length=len(set(all_media_ids)))
        media_map = {m['id']: m for m in all_media}
    
    # Fetch all annotations at once
    annotations_by_claim = {}
    if claim_ids:
        all_annotations = await db.annotations.find(
            {"claim_id": {"$in": claim_ids}},
            {"_id": 0}
        ).to_list(length=10000)
        for ann in all_annotations:
            cid = ann['claim_id']
            if cid not in annotations_by_claim:
                annotations_by_claim[cid] = []
            annotations_by_claim[cid].append(ann)
    
    result = []
    for claim in claims:
        media_list = []
        for media_id in claim.get('media_ids', []):
            if media_id in media_map:
                media_list.append(media_map[media_id])
        
        # Use stored post_score to avoid redundant calculation
        post_score = claim.get('post_score', 0.0)
        
        result.append({
            "id": claim['id'],
            "text": claim['text'],
            "domain": claim['domain'],
            "post_score": post_score,
            "credibility_score": post_score,  # Kept for backwards compatibility
            "media": media_list,
            "baseline_evaluation": claim.get('baseline_evaluation'),
            "created_at": claim['created_at']
        })

    if standard:
        total = await db.claims.count_documents({"author_id": user_id})
        return standardize_list_response(result, limit, skip, total)
    
    return result

# Get all user annotations
@api_router.get("/users/{user_id}/annotations")
async def get_user_annotations(user_id: str, skip: int = 0, limit: int = 50, standard: bool = False):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    annotations = await db.annotations.find({"author_id": user_id}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    result = []
    for ann in annotations:
        # Get claim info
        claim = await db.claims.find_one({"id": ann['claim_id']}, {"_id": 0, "text": 1, "id": 1})
        result.append({
            "id": ann['id'],
            "claim_id": ann['claim_id'],
            "claim_preview": claim['text'][:100] + "..." if claim and len(claim.get('text', '')) > 100 else claim.get('text', '') if claim else '',
            "text": ann['text'],
            "annotation_type": ann['annotation_type'],
            "helpful_votes": ann['helpful_votes'],
            "not_helpful_votes": ann['not_helpful_votes'],
            "created_at": ann['created_at']
        })
    
    if standard:
        total = await db.annotations.count_documents({"author_id": user_id})
        return standardize_list_response(result, limit, skip, total)
    
    return result

# Delete claim (hard delete with reputation reversal)
@api_router.delete("/claims/{claim_id}")
@limiter.limit("20/hour")  # Prevent deletion spam
async def delete_claim(
    request: Request,
    claim_id: str,
    current_user = Depends(get_current_user),
    standard: bool = False
):
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Check ownership
    if claim['author_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="You can only delete your own claims")
    
    # Delete associated media files
    if claim.get('media_ids'):
        media_deleted = await delete_media_files(
            claim['media_ids'],
            db,
            UPLOAD_DIR,
            s3_client=S3_CLIENT,
            s3_bucket=AWS_S3_BUCKET
        )
        logger.info(f"Deleted {media_deleted} media files for claim {claim_id}")
    
    # Reverse reputation boost if any
    baseline_eval = claim.get('baseline_evaluation', {})
    reputation_boost = baseline_eval.get('reputation_boost', 0)
    
    if reputation_boost > 0:
        await db.users.update_one(
            {"id": current_user['id']},
            {"$inc": {"reputation_score": -reputation_boost}}
        )
    
    # Delete associated annotations and their media
    annotations = await db.annotations.find({"claim_id": claim_id}, {"_id": 0}).to_list(length=1000)
    for ann in annotations:
        if ann.get('media_ids'):
            await delete_media_files(
                ann['media_ids'],
                db,
                UPLOAD_DIR,
                s3_client=S3_CLIENT,
                s3_bucket=AWS_S3_BUCKET
            )
    
    await db.annotations.delete_many({"claim_id": claim_id})
    
    # Delete associated notifications
    await db.notifications.delete_many({"claim_id": claim_id})
    
    # Delete the claim
    await db.claims.delete_one({"id": claim_id})
    
    # Update user stats
    await db.users.update_one(
        {"id": current_user['id']},
        {"$inc": {"contribution_stats.claims_posted": -1}}
    )
    
    logger.info(f"Claim {claim_id} deleted by user {current_user['id']}")
    
    response_data = {"message": "Claim deleted successfully", "reputation_reversed": reputation_boost}
    if standard:
        return standardize_single_response(response_data, message="Claim deleted successfully")
    return response_data

# Delete user account (hard delete)
@api_router.delete("/users/account")
@limiter.limit("5/hour")  # Prevent account deletion spam
async def delete_user_account(
    request: Request,
    confirmation: str,
    current_user = Depends(get_current_user),
    standard: bool = False
):
    if confirmation != "Delete Account":
        raise HTTPException(status_code=400, detail="Please type 'Delete Account' to confirm deletion")
    
    user_id = current_user['id']
    
    # Get all user's claims to reverse reputation
    claims = await db.claims.find({"author_id": user_id}, {"_id": 0}).to_list(length=10000)
    media_ids_to_delete = set()
    
    total_reputation_reversed = 0
    for claim in claims:
        baseline_eval = claim.get('baseline_evaluation', {})
        reputation_boost = baseline_eval.get('reputation_boost', 0)
        total_reputation_reversed += reputation_boost
        media_ids_to_delete.update(claim.get('media_ids', []))
        
        # Delete annotations on this claim
        claim_annotations = await db.annotations.find({"claim_id": claim['id']}, {"_id": 0, "media_ids": 1}).to_list(length=10000)
        for ann in claim_annotations:
            media_ids_to_delete.update(ann.get('media_ids', []))
        await db.annotations.delete_many({"claim_id": claim['id']})
    
    # Delete user's annotation media on other claims
    user_annotations = await db.annotations.find({"author_id": user_id}, {"_id": 0, "media_ids": 1}).to_list(length=10000)
    for ann in user_annotations:
        media_ids_to_delete.update(ann.get('media_ids', []))
    
    if media_ids_to_delete:
        media_deleted = await delete_media_files(
            list(media_ids_to_delete),
            db,
            UPLOAD_DIR,
            s3_client=S3_CLIENT,
            s3_bucket=AWS_S3_BUCKET
        )
        logger.info(f"Deleted {media_deleted} media files for user {user_id}")
    
    # Delete profile picture file if present
    profile_picture = current_user.get('profile_picture')
    if profile_picture:
        try:
            if is_s3_uri(profile_picture):
                bucket, key = parse_s3_uri(profile_picture)
                deleted = await s3_delete_object(bucket, key)
                if deleted:
                    logger.info(f"Deleted profile picture for user {user_id} from S3")
                else:
                    logger.warning(f"Failed to delete profile picture for user {user_id} from S3")
            else:
                profile_path = Path(profile_picture)
                if profile_path.exists():
                    profile_path.unlink()
                    logger.info(f"Deleted profile picture for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to delete profile picture for user {user_id}: {e}")
    
    # Delete all user's claims
    await db.claims.delete_many({"author_id": user_id})
    
    # Delete all user's annotations
    await db.annotations.delete_many({"author_id": user_id})
    
    # Delete all user's notifications
    await db.notifications.delete_many({"user_id": user_id})
    
    # Delete the user
    await db.users.delete_one({"id": user_id})
    
    response_data = {"message": "Account deleted successfully"}
    if standard:
        return standardize_single_response(response_data, message="Account deleted successfully")
    return response_data

# Admin media maintenance
@api_router.post("/admin/media/cleanup")
async def admin_cleanup_media(
    admin_key: str = Depends(require_admin_key),
    standard: bool = False
):
    result = await cleanup_orphaned_media(
        db,
        UPLOAD_DIR,
        s3_client=S3_CLIENT,
        s3_bucket=AWS_S3_BUCKET
    )
    response_data = {"message": "Cleanup completed", "result": result}
    if standard:
        return standardize_single_response(response_data, message="Cleanup completed")
    return response_data

@api_router.get("/admin/media/stats")
async def admin_media_stats(
    admin_key: str = Depends(require_admin_key),
    standard: bool = False
):
    stats = await get_storage_stats(
        db,
        UPLOAD_DIR,
        s3_client=S3_CLIENT,
        s3_bucket=AWS_S3_BUCKET,
        s3_prefix=AWS_S3_MEDIA_PREFIX
    )
    response_data = {"stats": stats}
    if standard:
        return standardize_single_response(response_data)
    return response_data

@api_router.get("/admin/logs/client")
async def admin_client_logs(
    admin_key: str = Depends(require_admin_key),
    skip: int = 0,
    limit: int = 50,
    level: Optional[str] = None,
    standard: bool = False
):
    query: Dict[str, Any] = {}
    if level:
        query["level"] = level.lower()

    logs = await db.client_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    total = await db.client_logs.count_documents(query)

    if standard:
        return standardize_list_response(logs, limit, skip, total)

    return {"logs": logs, "total": total}

@api_router.delete("/admin/logs/client")
async def admin_client_logs_cleanup(
    admin_key: str = Depends(require_admin_key),
    days: int = 30,
    standard: bool = False
):
    safe_days = max(1, min(days, 365))
    cutoff_iso = (datetime.now(timezone.utc) - timedelta(days=safe_days)).isoformat()
    result = await db.client_logs.delete_many({"created_at": {"$lt": cutoff_iso}})

    response_data = {"deleted": result.deleted_count, "older_than_days": safe_days}
    if standard:
        return standardize_single_response(response_data, message="Client logs cleaned")
    return response_data

# Notifications
@api_router.get("/notifications")
async def get_notifications(
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
    standard: bool = False
):
    notifications = await db.notifications.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    # Get unread count
    unread_count = await db.notifications.count_documents({
        "user_id": current_user['id'],
        "read": False
    })
    
    if standard:
        total = await db.notifications.count_documents({"user_id": current_user['id']})
        return standardize_list_response(
            notifications,
            limit,
            skip,
            total,
            extra={"unread_count": unread_count}
        )
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }

# Mark notification as read
@api_router.patch("/notifications/{notification_id}/read")
@limiter.limit("60/hour")  # Allow frequent notification updates
async def mark_notification_read(
    request: Request,
    notification_id: str,
    current_user = Depends(get_current_user),
    standard: bool = False
):
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user['id']},
        {"$set": {"read": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    response_data = {"message": "Notification marked as read"}
    if standard:
        return standardize_single_response(response_data, message="Notification marked as read")
    return response_data

# Mark all notifications as read
@api_router.patch("/notifications/read-all")
@limiter.limit("30/hour")  # Prevent notification spam
async def mark_all_notifications_read(
    request: Request,
    current_user = Depends(get_current_user),
    standard: bool = False
):
    await db.notifications.update_many(
        {"user_id": current_user['id'], "read": False},
        {"$set": {"read": True}}
    )
    
    response_data = {"message": "All notifications marked as read"}
    if standard:
        return standardize_single_response(response_data, message="All notifications marked as read")
    return response_data

# Get unread notification count
@api_router.get("/notifications/unread-count")
async def get_unread_notification_count(
    current_user = Depends(get_current_user),
    standard: bool = False
):
    count = await db.notifications.count_documents({
        "user_id": current_user['id'],
        "read": False
    })
    
    response_data = {"unread_count": count}
    if standard:
        return standardize_single_response(response_data)
    return response_data

# CORS configuration - restrict to specific origins

# Add your production frontend domain to allowed origins
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:3001,https://getthrryv.com')
if CORS_ORIGINS == '*':
    logger.warning("CORS_ORIGINS set to '*' - this is not recommended for production. Use specific origins instead.")
    allowed_origins = ['*']
else:
    allowed_origins = [origin.strip() for origin in CORS_ORIGINS.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        return response

app.add_middleware(SecurityHeadersMiddleware)

class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('x-request-id') or uuid.uuid4().hex
        request.state.request_id = request_id
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Response-Time-ms'] = f"{duration_ms:.2f}"
        return response


# --- FastAPI lifespan event handler for startup/shutdown ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    global client, db
    # Startup logic
    try:
        client = await get_db_client()
        db = client[os.environ['DB_NAME']]
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        db = None
    # Initialize additional collections for Thrryv v1 features
    if db is not None:
        try:
            # Challenges collection
            if 'challenges' not in await db.list_collection_names():
                await db.create_collection('challenges')
            await db.challenges.create_index([("claim_id", 1)])
            await db.challenges.create_index([("creator_id", 1)])
            await db.challenges.create_index([("status", 1)])

            # Predictions collection
            if 'predictions' not in await db.list_collection_names():
                await db.create_collection('predictions')
            await db.predictions.create_index([("challenge_id", 1)])
            await db.predictions.create_index([("user_id", 1)])
            await db.predictions.create_index([("challenge_id", 1), ("user_id", 1)])

            # Content signals collection (for caching feedback)
            if 'content_signals' not in await db.list_collection_names():
                await db.create_collection('content_signals')
            await db.content_signals.create_index([("claim_id", 1)])

            # User standing records collection
            if 'user_standing_records' not in await db.list_collection_names():
                await db.create_collection('user_standing_records')
            await db.user_standing_records.create_index([("user_id", 1)])
            await db.user_standing_records.create_index([("updated_at", -1)])

            # User interest profiles collection
            if 'user_interests' not in await db.list_collection_names():
                await db.create_collection('user_interests')
            await db.user_interests.create_index([("user_id", 1)], unique=True)
            await db.user_interests.create_index([("updated_at", -1)])

            # Client logs collection
            if 'client_logs' not in await db.list_collection_names():
                await db.create_collection('client_logs')
            await db.client_logs.create_index([("created_at", -1)])
            await db.client_logs.create_index([("level", 1)])

            # --- Added recommended indexes for speed ---
            # Claims collection
            await db.claims.create_index([("created_at", -1)])
            await db.claims.create_index([("domain", 1)])
            await db.claims.create_index([("category.primary_path", 1)])
            # Users collection
            await db.users.create_index([("id", 1)], unique=True)
            await db.users.create_index([("email", 1)], unique=True)
            await db.users.create_index([("username", 1)], unique=True)
            # Annotations collection
            await db.annotations.create_index([("claim_id", 1)])
            await db.annotations.create_index([("author_id", 1)])

            logger.info("Thrryv v1 collections and indexes initialized successfully")
        except Exception as e:
            logger.warning(f"Collection initialization note: {e}")
    yield
    # Shutdown logic
    if client:
        client.close()
        logger.info("Database connection closed")

import logging
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = _time.time()
        response = await call_next(request)
        duration = (_time.time() - start) * 1000
        logging.info(f"{request.method} {request.url.path} took {duration:.2f}ms")
        response.headers['X-Endpoint-Timing-ms'] = f"{duration:.2f}"
        return response

app.add_middleware(TimingMiddleware)
app.add_middleware(RequestMetricsMiddleware)
app.router.lifespan_context = lifespan

# Thrryv v1 Features

# Search suggestions and trending topics

@api_router.get("/search/suggestions")
@limiter.limit("120/hour")
async def get_search_suggestions(
    request: Request,
    q: str,
    limit: int = 5,
    standard: bool = False
):
    safe_limit = max(1, min(limit, 10))
    suggestions = await build_search_suggestions(q, safe_limit)

    if standard:
        return standardize_list_response(suggestions, safe_limit, 0, len(suggestions))

    return suggestions

@api_router.get("/search/trending")
@limiter.limit("60/hour")
async def get_trending_topics(
    request: Request,
    limit: int = 5,
    days: int = 7,
    standard: bool = False
):
    try:
        trending = await build_trending_topics(days, limit)
        if standard:
            return standardize_list_response(trending, min(max(1, limit), 10), 0, len(trending))
        return [item["topic"] for item in trending]
    except Exception as e:
        import logging
        logging.error(f"Trending endpoint error: {e}", exc_info=True)
        return {"success": False, "error": "server_error", "detail": str(e), "status_code": 500}

# Client error logging
@api_router.post("/logs/client")
@limiter.limit("120/hour")
async def log_client_error(
    request: Request,
    entry: ClientLogEntry,
    current_user = Depends(get_current_user_optional),
    standard: bool = False
):
    message = InputValidator.sanitize_text(entry.message, max_length=1000)
    level = (entry.level or "error").lower()
    created_at = entry.created_at or datetime.now(timezone.utc).isoformat()
    context = entry.context if isinstance(entry.context, dict) else None

    record = {
        "id": str(uuid.uuid4()),
        "level": level,
        "message": message,
        "source": entry.source,
        "url": entry.url,
        "context": context,
        "created_at": created_at,
        "user_id": current_user.get("id") if current_user else None,
        "request_id": getattr(request.state, "request_id", None),
        "user_agent": request.headers.get("user-agent"),
        "ip": request.client.host if request.client else None
    }

    if db:
        await db.client_logs.insert_one(record)
    else:
        logger.warning(f"Client log (no db): {record}")

    response_data = {"message": "Log recorded"}
    if standard:
        return standardize_single_response(response_data, message="Log recorded")
    return response_data

# AI-Powered Content Discovery
@api_router.post("/discover")
async def discover_content(
    search_request: SearchQueryRequest,
    current_user = Depends(get_current_user),
    standard: bool = False
):
    """
    AI-powered content discovery based on user intent.
    
    Uses natural language search and intelligent ranking
    considering relevance, perspective diversity, originality, and user standing.
    """
    
    try:
        # Parse search intent
        search_engine = NaturalLanguageSearchEngine()
        search_intent = await search_engine.parse_search_intent(search_request.query)
        
        # Get all claims (in real implementation, would be paginated efficiently)
        all_claims = await db.claims.find({}, {"_id": 0}).to_list(length=10000)
        
        # Execute search with intent
        search_results = await search_engine.execute_search(
            intent=search_intent,
            available_claims=all_claims
        )

        enriched_results = []
        for claim in search_results:
            enriched_results.append(await enrich_claim_for_discovery(claim))
        
        # Initialize discovery engine
        discovery = ContentDiscoveryEngine()
        user_standing = current_user.get('user_standing_score', 1.0)
        
        algorithm = DiscoveryAlgorithm(search_request.algorithm) if search_request.algorithm else DiscoveryAlgorithm.RELEVANCE
        
        # Discover content
        discovered = await discovery.discover_content(
            user_query=search_request.query,
            available_claims=enriched_results,
            user_standing=user_standing,
            algorithm=algorithm,
            limit=search_request.limit,
            diversity_preference=search_request.diversity_preference
        )

        discovered_ids = [item.claim_id for item in discovered]
        claims_by_id: Dict[str, Dict[str, Any]] = {}
        if discovered_ids:
            discovered_claims = await db.claims.find(
                {"id": {"$in": discovered_ids}},
                {"_id": 0}
            ).to_list(length=len(discovered_ids))
            claims_by_id = {claim['id']: claim for claim in discovered_claims}

        claim_feed_items = []
        for item in discovered:
            claim = claims_by_id.get(item.claim_id)
            if claim:
                claim_feed_items.append(await build_claim_feed_item(claim))

        try:
            intent_domains = search_intent.domains or []
            claim_domains = [
                extract_claim_domain(claim)
                for claim in claims_by_id.values()
            ]
            claim_domains = [domain for domain in claim_domains if domain]
            await update_user_interests(
                user_id=current_user['id'],
                query=search_request.query,
                intent_domains=intent_domains,
                claim_domains=claim_domains
            )
        except Exception as e:
            logger.warning(f"Failed to update user interests: {e}")
        
        # Format results
        results = []
        for item in discovered:
            claim = await db.claims.find_one({"id": item.claim_id}, {"_id": 0})
            author = await db.users.find_one({"id": item.author_id}, {"_id": 0, "password": 0})
            
            results.append({
                "claim_id": item.claim_id,
                "title": item.title,
                "author": {
                    "id": item.author_id,
                    "username": author.get('username', ''),
                    "standing": item.author_standing
                },
                "composite_score": round(item.composite_score, 2),
                "relevance_match": item.relevance_match_explanation,
                "perspective_type": item.perspective_type,
                "diversity_indicators": item.diversity_indicators,
                "signals": {
                    "relevance": round(item.signals.relevance_score, 1),
                    "diversity": round(item.signals.diversity_score, 1),
                    "originality": round(item.signals.originality_score, 1),
                    "engagement_quality": round(item.signals.engagement_quality, 1),
                    "clarity": round(item.signals.clarity_signal, 1),
                    "impact": round(item.signals.impact_score, 1),
                    "author_reputation": round(item.signals.author_reputation, 1)
                }
            })
        
        response_data = {
            "search_intent": {
                "query": search_intent.core_query,
                "domains": search_intent.domains,
                "perspective_preferences": search_intent.perspective_preferences,
                "sort_by": search_intent.sort_by
            },
            "results": results,
            "claims": claim_feed_items,
            "note": "Discovery uses AI signals, not truth labels. Explore different perspectives."
        }

        if standard:
            return standardize_single_response(response_data)
        
        return response_data
    
    except Exception as e:
        logger.error(f"Discovery error: {e}")
        raise HTTPException(status_code=500, detail="Discovery service temporarily unavailable")

@api_router.post("/discover/feed")
async def discover_feed(
    request: FeedDiscoverRequest,
    current_user = Depends(get_current_user),
    standard: bool = False
):
    """
    Personalized feed discovery using stored user interests.
    """
    async def build_top_claims(limit: int) -> List[Dict[str, Any]]:
        all_items = await db.claims.find({}, {"_id": 0}).to_list(length=10000)
        sorted_items = sorted(
            all_items,
            key=lambda claim: (
                claim.get('impact_score') or 0,
                claim.get('post_score') or claim.get('credibility_score') or 0,
                claim.get('created_at') or ''
            ),
            reverse=True
        )
        top_items = sorted_items[:max(1, limit)]
        return [await build_claim_feed_item(claim) for claim in top_items]

    try:
        interest_doc = await db.user_interests.find_one({"user_id": current_user['id']}, {"_id": 0})
        interests = interest_doc.get('interests', {}) if interest_doc else {}

        top_domains = [
            domain for domain, _score in sorted(
                interests.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ][:3]

        expanded_domains = list(top_domains)
        for domain in top_domains:
            for related in RELATED_DOMAIN_MAP.get(domain, []):
                if related not in expanded_domains:
                    expanded_domains.append(related)
                if len(expanded_domains) >= 5:
                    break
            if len(expanded_domains) >= 5:
                break

        if not expanded_domains:
            response_data = {
                "query": "top",
                "interests": [],
                "claims": await build_top_claims(request.limit),
                "note": "Top posts shown while interests are still learning."
            }
            if standard:
                return standardize_single_response(response_data)
            return response_data

        query = build_interest_query(expanded_domains)

        search_engine = NaturalLanguageSearchEngine()
        search_intent = await search_engine.parse_search_intent(query)

        all_claims = await db.claims.find({}, {"_id": 0}).to_list(length=10000)
        search_results = await search_engine.execute_search(
            intent=search_intent,
            available_claims=all_claims
        )

        enriched_results = []
        for claim in search_results:
            enriched_results.append(await enrich_claim_for_discovery(claim))

        discovery = ContentDiscoveryEngine()
        user_standing = current_user.get('user_standing_score', 1.0)

        discovered = await discovery.discover_content(
            user_query=query,
            available_claims=enriched_results,
            user_standing=user_standing,
            algorithm=DiscoveryAlgorithm.RELEVANCE,
            limit=request.limit,
            diversity_preference=request.diversity_preference
        )

        if not discovered:
            response_data = {
                "query": query,
                "interests": expanded_domains,
                "claims": await build_top_claims(request.limit),
                "note": "Top posts shown while personalized feed warms up."
            }
            if standard:
                return standardize_single_response(response_data)
            return response_data

        discovered = discovery._apply_diversity_ranking(discovered, request.diversity_preference)
        discovered = discovery._apply_emergent_ranking(discovered)
        discovered = discovery._apply_standing_aware_ranking(discovered)

        discovered_ids = [item.claim_id for item in discovered]
        claims_by_id: Dict[str, Dict[str, Any]] = {}
        if discovered_ids:
            discovered_claims = await db.claims.find(
                {"id": {"$in": discovered_ids}},
                {"_id": 0}
            ).to_list(length=len(discovered_ids))
            claims_by_id = {claim['id']: claim for claim in discovered_claims}

        claim_feed_items = []
        for item in discovered:
            claim = claims_by_id.get(item.claim_id)
            if claim:
                claim_feed_items.append(await build_claim_feed_item(claim))

        try:
            claim_domains = [
                extract_claim_domain(claim)
                for claim in claims_by_id.values()
            ]
            claim_domains = [domain for domain in claim_domains if domain]
            await update_user_interests(
                user_id=current_user['id'],
                query=query,
                intent_domains=expanded_domains,
                claim_domains=claim_domains,
                query_weight=2,
                claim_weight=1
            )
        except Exception as e:
            logger.warning(f"Failed to update user interests for feed: {e}")

        response_data = {
            "query": query,
            "interests": expanded_domains,
            "claims": claim_feed_items,
            "note": "Feed is personalized using your interests with light topic expansion."
        }

        if standard:
            return standardize_single_response(response_data)

        return response_data

    except Exception as e:
        logger.error(f"Feed discovery error: {e}")
        raise HTTPException(status_code=500, detail="Feed discovery temporarily unavailable")

# Content Signals & Improvement Feedback
@api_router.get("/claims/{claim_id}/signals")
async def get_content_signals(
    claim_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get AI-generated content signals and improvement feedback.
    
    Does NOT label content as true/false.
    Provides feedback on clarity, context, and supporting signals.
    """
    
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Get annotations
    annotations = await db.annotations.find({"claim_id": claim_id}, {"_id": 0}).to_list(length=1000)
    
    # Get sources if available
    sources = claim.get('sources', [])
    
    try:
        signal_generator = ContentSignalGenerator()
        feedback = await signal_generator.generate_feedback(
            claim=claim,
            annotations=annotations,
            sources=sources
        )
        
        return {
            "claim_id": claim_id,
            "clarity": {
                "score": round(feedback.clarity_signal.score, 1),
                "strengths": feedback.clarity_signal.strengths,
                "areas_for_improvement": feedback.clarity_signal.areas_for_improvement,
                "suggestions": feedback.clarity_signal.actionable_suggestions
            },
            "context": {
                "score": round(feedback.context_signal.score, 1),
                "has_timeframe": feedback.context_signal.has_timeframe,
                "has_location": feedback.context_signal.has_location,
                "has_sources": feedback.context_signal.has_sources,
                "has_definitions": feedback.context_signal.has_definitions,
                "has_data": feedback.context_signal.has_data,
                "improvements": feedback.context_signal.improvement_suggestions
            },
            "evidence": {
                "score": round(feedback.evidence_signal.score, 1),
                "has_citations": feedback.evidence_signal.has_citations,
                "citation_count": feedback.evidence_signal.citation_count,
                "has_media": feedback.evidence_signal.has_supporting_media,
                "media_count": feedback.evidence_signal.media_count,
                "has_statistics": feedback.evidence_signal.has_statistics,
                "evidence_types": feedback.evidence_signal.evidence_types,
                "improvements": feedback.evidence_signal.improvement_suggestions
            },
            "overall_quality": round(feedback.overall_quality_score, 1),
            "standing_impact": feedback.creator_standing_impact,
            "improvement_roadmap": feedback.improvement_roadmap,
            "positive_aspects": feedback.positive_aspects,
            "note": "Feedback focuses on improvement, not judgment. Higher quality helps with discovery and creator standing."
        }
    
    except Exception as e:
        logger.error(f"Signal generation error: {e}")
        raise HTTPException(status_code=500, detail="Signal generation temporarily unavailable")

# User Standing Profile
@api_router.get("/users/{user_id}/standing")
async def get_user_standing(user_id: str):
    """
    Get user's standing signal (replaces reputation score).
    
    Shows standing tier, metrics, and next milestone requirements.
    NOT a ranking, but descriptive level based on consistency and quality.
    """
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user statistics
    user_claims = await db.claims.find({"author_id": user_id}, {"_id": 0}).to_list(length=10000)
    user_annotations = await db.annotations.find({"author_id": user_id}, {"_id": 0}).to_list(length=10000)
    
    # Calculate average content quality
    quality_scores = [c.get('baseline_evaluation', {}).get('clarity_score', 50) for c in user_claims]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 50
    
    user_stats = {
        "claims_posted": len(user_claims),
        "annotations_added": len(user_annotations),
        "helpful_votes_received": user.get('contribution_stats', {}).get('helpful_votes_received', 0),
        "original_claims": sum(1 for c in user_claims if c.get('originality_boosted', False))
    }
    
    try:
        standing_system = UserStandingSystem()
        standing_signal = await standing_system.calculate_standing(
            user=user,
            user_stats=user_stats,
            content_quality_avg=avg_quality,
            annotations=user_annotations
        )
        
        standing_display = standing_system.format_standing_for_profile(standing_signal)
        
        return {
            "user_id": user_id,
            "username": user.get('username', ''),
            "standing": standing_display,
            "note": "Standing reflects consistency, effort, and quality - not ranking against other users."
        }
    
    except Exception as e:
        logger.error(f"Standing calculation error: {e}")
        raise HTTPException(status_code=500, detail="Standing calculation temporarily unavailable")

# Originality Recognition
@api_router.get("/claims/{claim_id}/originality")
async def get_originality_analysis(claim_id: str):
    """
    Get originality analysis for a claim.
    
    Shows how original/novel the content is compared to platform content.
    Originality reflects novelty, not accuracy.
    """
    
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Get all existing claims
    all_claims = await db.claims.find({}, {"_id": 0}).to_list(length=10000)
    
    try:
        detector = OriginalityDetector()
        analysis = await detector.analyze_originality(
            claim=claim,
            existing_claims=[c for c in all_claims if c.get('id') != claim_id]
        )
        
        return {
            "claim_id": claim_id,
            "originality_score": round(analysis.originality_score, 1),
            "novelty_level": analysis.novelty_level,
            "is_boosted": analysis.boost_eligible,
            "similar_content": [
                {
                    "claim_id": m.get('claim_id'),
                    "similarity": round(m.get('similarity', 0), 2),
                    "preview": m.get('text_preview', ''),
                    "created_at": m.get('created_at')
                }
                for m in analysis.similarity_matches[:3]
            ],
            "note": "Originality reflects how novel your content is. Original contributions get discovery boosts."
        }
    
    except Exception as e:
        logger.error(f"Originality analysis error: {e}")
        raise HTTPException(status_code=500, detail="Originality analysis temporarily unavailable")

# Interactive Challenges
@api_router.post("/claims/{claim_id}/challenges")
async def create_challenge(
    claim_id: str,
    challenge_data: ChallengeCreateRequest,
    current_user = Depends(get_current_user)
):
    """
    Create an interactive challenge for viewers to make predictions.
    
    Low-stakes engagement that only affects viewer's standing.
    Creator gets no punishment or reward from challenge results.
    """
    
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if claim['author_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Only claim creator can create challenges")
    
    try:
        challenge_system = InteractiveChallengeSystem()
        challenge = await challenge_system.create_challenge(
            claim_id=claim_id,
            creator_id=current_user['id'],
            challenge_data=challenge_data.dict()
        )
        
        # Store challenge
        challenge_doc = {
            **challenge.__dict__,
            "status": challenge.status.value
        }
        await db.challenges.insert_one(challenge_doc)
        
        return {
            "challenge_id": challenge.id,
            "status": "created",
            "title": challenge.title,
            "closes_at": challenge.closes_at,
            "note": "Predictions are fun, low-stakes engagement. No impact on your content quality."
        }
    
    except Exception as e:
        logger.error(f"Challenge creation error: {e}")
        raise HTTPException(status_code=500, detail="Challenge creation failed")

@api_router.post("/challenges/{challenge_id}/predictions")
async def make_prediction(
    challenge_id: str,
    prediction_data: ChallengePredictionRequest,
    current_user = Depends(get_current_user)
):
    """
    Make a prediction on an interactive challenge.
    
    Only affects your engagement standing, not the content or creator.
    """
    
    challenge = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge.get('status') != 'active':
        raise HTTPException(status_code=400, detail="Challenge is not active")
    
    try:
        challenge_system = InteractiveChallengeSystem()
        prediction = await challenge_system.make_prediction(
            challenge_id=challenge_id,
            user_id=current_user['id'],
            prediction=prediction_data.prediction,
            confidence_level=prediction_data.confidence_level or 50.0
        )
        
        # Store prediction
        prediction_doc = prediction.__dict__
        await db.predictions.insert_one(prediction_doc)
        
        # Update challenge prediction count
        await db.challenges.update_one(
            {"id": challenge_id},
            {"$inc": {"prediction_count": 1, "participant_count": 1}}
        )
        
        return {
            "prediction_id": prediction.id,
            "status": "recorded",
            "message": "Your prediction has been recorded!",
            "standing_note": "Your engagement with this prediction will affect your standing."
        }
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Prediction recording failed")

@api_router.get("/challenges/{challenge_id}")
async def get_challenge(challenge_id: str, current_user = Depends(get_current_user)):
    """Get challenge details with user's prediction if any"""
    
    challenge = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Get user's prediction if any
    user_prediction = await db.predictions.find_one({
        "challenge_id": challenge_id,
        "user_id": current_user['id']
    }, {"_id": 0})
    
    try:
        challenge_system = InteractiveChallengeSystem()
        # Find actual Challenge object structure
        challenge_obj_data = {k: v for k, v in challenge.items() if k != '_id'}
        # Convert status if string
        if isinstance(challenge_obj_data.get('status'), str):
            challenge_obj_data['status'] = ChallengeStatus(challenge_obj_data['status'])
        
        display = challenge_system.format_challenge_for_display(
            challenge={
                **challenge_obj_data,
                **{'id': challenge_id}
            },
            user_prediction=user_prediction
        )
        
        return display
    
    except Exception as e:
        logger.error(f"Challenge retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Challenge retrieval failed")

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """Check application health and database connectivity"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }
    
    # Check database
    try:
        if db is not None:
            await db.command('ping')
            health_status["services"]["database"] = "connected"
        else:
            health_status["services"]["database"] = "not_initialized"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check AI services
    ai_key = os.environ.get('EMERGENT_LLM_KEY')
    health_status["services"]["ai_evaluation"] = "configured" if ai_key else "not_configured"
    
    # Check file storage
    health_status["services"]["file_storage"] = "accessible" if UPLOAD_DIR.exists() else "error"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return health_status

app.include_router(api_router)
app.include_router(uptime.router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)