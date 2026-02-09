from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status, Request, Header
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
from starlette.responses import Response
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

JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7
ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY')

security = HTTPBearer()

# File upload directory
UPLOAD_DIR = ROOT_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    
    # Add community engagement bonus (up to +5.0)
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
        author_rep = 10.0
        if ann.get('author') and isinstance(ann.get('author'), dict):
            author_rep = ann.get('author', {}).get('reputation_score', 10.0)
        else:
            author_rep = ann.get('author_reputation', 10.0)
        rep_factor = min(2.0, max(0.6, author_rep / 10.0))
        confidence = ann.get('classification_confidence', 0.5)
        confidence_factor = 0.6 + (0.4 * min(1.0, max(0.0, confidence)))

        weight = max(0.2, (1.0 + (helpful_votes * 0.2) - (not_helpful_votes * 0.1)) * rep_factor * confidence_factor)
        ann_type = ann.get('annotation_type')

        # Require evidence to influence score (avoid single weak "no")
        has_evidence = (helpful_votes >= 2) or (author_rep >= 15) or (confidence >= 0.7)
        if ann_type == 'support':
            support_weight += weight if has_evidence else (weight * 0.25)
        elif ann_type == 'contradict':
            contradict_weight += weight if has_evidence else (weight * 0.25)

    # Engagement bonus: annotations + helpful votes
    engagement_score = min(5.0, (valid_annotation_count * 0.3) + (helpful_vote_total * 0.15))

    # Stance adjustment: support raises, contradict lowers (range -5 to +5)
    stance_adjust = max(-5.0, min(5.0, (support_weight - contradict_weight) * 0.4))

    total_score = base_score + engagement_score + stance_adjust
    return max(0.0, total_score)
# Auth endpoints
@api_router.post("/auth/register")
@limiter.limit("5/hour")  # Limit registration attempts
async def register(request: Request, user_data: UserCreate):
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
        "reputation_score": 10.0,
        "contribution_stats": {
            "claims_posted": 0,
            "annotations_added": 0,
            "helpful_votes_received": 0
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    
    token = create_jwt_token(user_id)
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "username": username,
            "email": email,
            "reputation_score": 10.0
        }
    }

@api_router.post("/auth/login")
@limiter.limit("10/minute")  # Prevent brute force attacks
async def login(request: Request, credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_jwt_token(user['id'])
    
    return {
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

@api_router.get("/auth/me")
async def get_me(current_user = Depends(get_current_user)):
    return {
        "id": current_user['id'],
        "username": current_user['username'],
        "email": current_user['email'],  # Email only visible to the user themselves
        "bio": current_user.get('bio', ''),
        "reputation_score": current_user['reputation_score'],
        "contribution_stats": current_user['contribution_stats'],
        "profile_picture": current_user.get('profile_picture')
    }

# Media upload
@api_router.post("/media/upload")
@limiter.limit("30/hour")  # Limit file uploads
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    # Validate file
    contents = await file.read()
    validate_media_file(file.filename, file.content_type, len(contents))
    
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix.lower()
    
    # Sanitize extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.mp4', '.webm', '.ogg', '.mov']
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    
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
        "uploaded_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.media.insert_one(media)
    
    return {
        "id": file_id,
        "file_name": file.filename,
        "file_type": file.content_type,
        "is_ai_generated": is_ai,
        "ai_confidence": confidence
    }

# Media serving
@api_router.get("/media/{media_id}")
async def get_media(media_id: str):
    from fastapi.responses import FileResponse
    
    media = await db.media.find_one({"id": media_id}, {"_id": 0})
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    file_path = media['file_path']
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
        valid_domains = ["Science", "Health", "Technology", "Politics", "Economics", 
                        "Environment", "History", "Society", "Sports", "Entertainment",
                        "Education", "Geography", "Food", "Law", "Religion", "General"]
        
        if domain not in valid_domains:
            domain = "General"
            
        logging.info(f"AI Domain Classification: {domain} (confidence: {result.get('confidence', 'N/A')}, reason: {result.get('reasoning', 'N/A')})")
        return domain
        
    except Exception as e:
        logging.error(f"AI domain classification failed: {e}")
        return await classify_claim_domain_fallback(claim_text)


async def classify_claim_domain_fallback(claim_text: str) -> str:
    """Fallback keyword-based classification"""
    domains_keywords = {
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
    
    claim_lower = claim_text.lower()
    domain_scores = {}
    
    for domain, keywords in domains_keywords.items():
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
    current_user = Depends(get_current_user)
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
                media_list.append(media)
                # Read media file for AI evaluation
                try:
                    file_path = media.get('file_path')
                    if file_path and Path(file_path).exists():
                        with open(file_path, 'rb') as f:
                            media_data = f.read()
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
    
    # Update user stats and apply reputation boost
    update_ops = {"$inc": {"contribution_stats.claims_posted": 1}}
    
    if reputation_boost > 0:
        update_ops["$inc"]["reputation_score"] = reputation_boost
    
    await db.users.update_one(
        {"id": current_user['id']},
        update_ops
    )
    
    # Get updated user reputation
    updated_user = await db.users.find_one({"id": current_user['id']}, {"_id": 0, "reputation_score": 1})
    new_reputation = updated_user.get('reputation_score', current_user['reputation_score'])
    
    return {
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

@api_router.get("/claims")
async def get_claims(limit: int = 20, offset: int = 0):
    claims = await db.claims.find({}, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
    
    result = []
    for claim in claims:
        author = await db.users.find_one({"id": claim['author_id']}, {"_id": 0, "password": 0})
        annotations = await db.annotations.find({"claim_id": claim['id']}, {"_id": 0}).to_list(length=1000)
        
        media_list = []
        for media_id in claim.get('media_ids', []):
            media = await db.media.find_one({"id": media_id}, {"_id": 0})
            if media:
                media_list.append(media)
        
        # Calculate current post score
        post_score = calculate_post_score(annotations, claim.get('baseline_evaluation'), claim.get('author_id'))

        # Top annotations (for feed preview)
        top_annotations = sorted(
            annotations,
            key=lambda a: (a.get('helpful_votes', 0), a.get('created_at', '')),
            reverse=True
        )[:2]
        top_annotation_cards = []
        for ann in top_annotations:
            ann_author = await db.users.find_one({"id": ann['author_id']}, {"_id": 0, "password": 0})
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

        result.append({
            "id": claim['id'],
            "text": claim['text'],
            "domain": claim['domain'],
            "confidence_level": claim['confidence_level'],
            "author": {
                "id": author['id'],
                "username": author['username'],
                "reputation_score": author['reputation_score']
            },
            "media": media_list,
            "post_score": post_score,
            "credibility_score": post_score,  # Kept for backwards compatibility
            "top_annotations": top_annotation_cards,
            "baseline_evaluation": claim.get('baseline_evaluation'),
            "category": claim.get('category'),
            "annotation_count": len(annotations),
            "created_at": claim['created_at']
        })
    
    return result

@api_router.get("/claims/{claim_id}")
async def get_claim(claim_id: str):
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    author = await db.users.find_one({"id": claim['author_id']}, {"_id": 0, "password": 0})
    annotations = await db.annotations.find({"claim_id": claim_id}, {"_id": 0}).to_list(length=1000)
    
    media_list = []
    for media_id in claim.get('media_ids', []):
        media = await db.media.find_one({"id": media_id}, {"_id": 0})
        if media:
            media_list.append(media)
    
    # Calculate current post score
    post_score = calculate_post_score(annotations, claim.get('baseline_evaluation'), claim.get('author_id'))
    
    return {
        "id": claim['id'],
        "text": claim['text'],
        "domain": claim['domain'],
        "category": claim.get('category'),
        "confidence_level": claim['confidence_level'],
        "author": {
            "id": author['id'],
            "username": author['username'],
            "reputation_score": author['reputation_score']
        },
        "media": media_list,
        "post_score": post_score,
        "credibility_score": post_score,  # Kept for backwards compatibility
        "baseline_evaluation": claim.get('baseline_evaluation'),
        "annotation_count": len(annotations),
        "created_at": claim['created_at']
    }

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
        "author_reputation": current_user.get('reputation_score', 10.0),
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
    
    # Enrich annotations with author data
    enriched_annotations = []
    for ann in all_annotations:
        author = await db.users.find_one({"id": ann['author_id']}, {"_id": 0})
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
async def get_annotations(claim_id: str):
    annotations = await db.annotations.find({"claim_id": claim_id}, {"_id": 0}).to_list(length=1000)
    
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
    
    return result

# Vote on annotations
@api_router.post("/annotations/{annotation_id}/vote")
async def vote_annotation(
    annotation_id: str,
    helpful: bool,
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
        # 1 point base + up to 2 bonus points for aging well (maxes at 30 days)
        time_bonus = min(2.0, days_old / 15.0)
        reputation_gain = 1.0 + time_bonus
        
        await db.users.update_one(
            {"id": author_id},
            {"$inc": {"reputation_score": reputation_gain, "contribution_stats.helpful_votes_received": 1}}
        )
    else:
        await db.annotations.update_one(
            {"id": annotation_id},
            {"$inc": {"not_helpful_votes": 1}, "$push": {"voted_by": current_user['id']}}
        )
    
    # Recalculate claim credibility
    claim_id = annotation['claim_id']
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    all_annotations = await db.annotations.find({"claim_id": claim_id}, {"_id": 0}).to_list(length=1000)
    
    enriched_annotations = []
    for ann in all_annotations:
        author = await db.users.find_one({"id": ann['author_id']}, {"_id": 0})
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
    file_path = UPLOAD_DIR / f"profile_{file_id}{file_ext}"
    
    # Save file
    contents = await file.read()
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
async def update_user_settings(
    settings: UserSettingsUpdate,
    current_user = Depends(get_current_user)
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
        return {
            "message": "Settings updated successfully",
            "user": {
                "id": updated_user['id'],
                "username": updated_user['username'],
                "email": updated_user['email'],
                "bio": updated_user.get('bio', ''),
                "reputation_score": updated_user['reputation_score']
            }
        }
    
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
async def get_user_claims(user_id: str, skip: int = 0, limit: int = 50):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    claims = await db.claims.find({"author_id": user_id}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    result = []
    for claim in claims:
        media_list = []
        for media_id in claim.get('media_ids', []):
            media = await db.media.find_one({"id": media_id}, {"_id": 0})
            if media:
                media_list.append(media)
        
        # Get annotations for post score calculation
        annotations = await db.annotations.find({"claim_id": claim['id']}, {"_id": 0}).to_list(length=1000)
        post_score = calculate_post_score(annotations, claim.get('baseline_evaluation'), claim.get('author_id'))
        
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
    
    return result

# Get all user annotations
@api_router.get("/users/{user_id}/annotations")
async def get_user_annotations(user_id: str, skip: int = 0, limit: int = 50):
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
    
    return result

# Delete claim (hard delete with reputation reversal)
@api_router.delete("/claims/{claim_id}")
async def delete_claim(
    claim_id: str,
    current_user = Depends(get_current_user)
):
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Check ownership
    if claim['author_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="You can only delete your own claims")
    
    # Delete associated media files
    if claim.get('media_ids'):
        media_deleted = await delete_media_files(claim['media_ids'], db, UPLOAD_DIR)
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
            await delete_media_files(ann['media_ids'], db, UPLOAD_DIR)
    
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
    
    return {"message": "Claim deleted successfully", "reputation_reversed": reputation_boost}

# Delete user account (hard delete)
@api_router.delete("/users/account")
async def delete_user_account(
    confirmation: str,
    current_user = Depends(get_current_user)
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
        media_deleted = await delete_media_files(list(media_ids_to_delete), db, UPLOAD_DIR)
        logger.info(f"Deleted {media_deleted} media files for user {user_id}")
    
    # Delete profile picture file if present
    profile_picture = current_user.get('profile_picture')
    if profile_picture:
        try:
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
    
    return {"message": "Account deleted successfully"}

# Admin media maintenance
@api_router.post("/admin/media/cleanup")
async def admin_cleanup_media(
    admin_key: str = Depends(require_admin_key)
):
    result = await cleanup_orphaned_media(db, UPLOAD_DIR)
    return {"message": "Cleanup completed", "result": result}

@api_router.get("/admin/media/stats")
async def admin_media_stats(
    admin_key: str = Depends(require_admin_key)
):
    stats = await get_storage_stats(db, UPLOAD_DIR)
    return {"stats": stats}

# Notifications
@api_router.get("/notifications")
async def get_notifications(
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
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
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }

# Mark notification as read
@api_router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user = Depends(get_current_user)
):
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user['id']},
        {"$set": {"read": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

# Mark all notifications as read
@api_router.patch("/notifications/read-all")
async def mark_all_notifications_read(
    current_user = Depends(get_current_user)
):
    await db.notifications.update_many(
        {"user_id": current_user['id'], "read": False},
        {"$set": {"read": True}}
    )
    
    return {"message": "All notifications marked as read"}

# Get unread notification count
@api_router.get("/notifications/unread-count")
async def get_unread_notification_count(
    current_user = Depends(get_current_user)
):
    count = await db.notifications.count_documents({
        "user_id": current_user['id'],
        "read": False
    })
    
    return {"unread_count": count}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.on_event("startup")
async def startup_db_client():
    """Initialize database connection on startup"""
    global client, db
    try:
        client = await get_db_client()
        db = client[os.environ['DB_NAME']]
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Allow app to start but log error
        # Individual endpoints will handle connection errors

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection on shutdown"""
    global client
    if client:
        client.close()
        logger.info("Database connection closed")

# Initialize additional collections for Thrryv v1 features
@app.on_event("startup")
async def initialize_new_collections():
    """Initialize collections for new Thrryv v1 features"""
    global db
    
    if db is not None:
        # Create indexes for performance
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
            
            logger.info("Thrryv v1 collections initialized successfully")
        
        except Exception as e:
            logger.warning(f"Collection initialization note: {e}")

# Thrryv v1 Features

# AI-Powered Content Discovery
@api_router.post("/discover")
async def discover_content(
    search_request: SearchQueryRequest,
    current_user = Depends(get_current_user)
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
        
        # Initialize discovery engine
        discovery = ContentDiscoveryEngine()
        user_standing = current_user.get('user_standing_score', 1.0)
        
        algorithm = DiscoveryAlgorithm(search_request.algorithm) if search_request.algorithm else DiscoveryAlgorithm.RELEVANCE
        
        # Discover content
        discovered = await discovery.discover_content(
            user_query=search_request.query,
            available_claims=search_results,
            user_standing=user_standing,
            algorithm=algorithm,
            limit=search_request.limit,
            diversity_preference=search_request.diversity_preference
        )
        
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
                    "clarity": round(item.signals.clarity_signal, 1)
                }
            })
        
        return {
            "search_intent": {
                "query": search_intent.core_query,
                "domains": search_intent.domains,
                "perspective_preferences": search_intent.perspective_preferences,
                "sort_by": search_intent.sort_by
            },
            "results": results,
            "note": "Discovery uses AI signals, not truth labels. Explore different perspectives."
        }
    
    except Exception as e:
        logger.error(f"Discovery error: {e}")
        raise HTTPException(status_code=500, detail="Discovery service temporarily unavailable")

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