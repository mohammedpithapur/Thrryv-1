from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7

security = HTTPBearer()

# File upload directory
UPLOAD_DIR = ROOT_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Enums
class TruthLabel(str, Enum):
    TRUE = "True"
    LIKELY_TRUE = "Likely True"
    MIXED = "Mixed Evidence"
    UNCERTAIN = "Uncertain"
    LIKELY_FALSE = "Likely False"
    FALSE = "False"

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
    domain: str
    confidence_level: int
    media_ids: Optional[List[str]] = []

class ClaimResponse(BaseModel):
    id: str
    text: str
    domain: str
    confidence_level: int
    author: Dict[str, str]
    media: List[Dict[str, Any]]
    truth_label: TruthLabel
    credibility_score: float
    annotation_count: int
    created_at: str

class AnnotationCreate(BaseModel):
    text: str
    annotation_type: AnnotationType
    media_ids: Optional[List[str]] = []

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

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
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

# Credibility calculation
def calculate_credibility_and_label(annotations: List[Dict]) -> tuple[float, TruthLabel]:
    """Calculate credibility score and truth label based on annotations"""
    if not annotations:
        return 0.0, TruthLabel.UNCERTAIN
    
    support_weight = 0
    contradict_weight = 0
    
    for ann in annotations:
        # Weight by author reputation and helpful votes
        author_rep = ann.get('author', {}).get('reputation_score', 1.0)
        helpful_votes = ann.get('helpful_votes', 0)
        weight = (author_rep * 0.7) + (helpful_votes * 0.3)
        
        if ann['annotation_type'] == 'support':
            support_weight += weight
        elif ann['annotation_type'] == 'contradict':
            contradict_weight += weight
    
    total_weight = support_weight + contradict_weight
    
    if total_weight == 0:
        return 0.0, TruthLabel.UNCERTAIN
    
    support_ratio = support_weight / total_weight
    credibility = support_ratio * 100
    
    # Determine truth label
    if support_ratio >= 0.85:
        label = TruthLabel.TRUE
    elif support_ratio >= 0.65:
        label = TruthLabel.LIKELY_TRUE
    elif support_ratio >= 0.45:
        label = TruthLabel.MIXED
    elif support_ratio >= 0.25:
        label = TruthLabel.LIKELY_FALSE
    else:
        label = TruthLabel.FALSE
    
    # If few annotations, mark as uncertain
    if len(annotations) < 3:
        label = TruthLabel.UNCERTAIN
    
    return credibility, label

# Auth endpoints
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user_data.password)
    
    user = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
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
            "username": user_data.username,
            "email": user_data.email,
            "reputation_score": 10.0
        }
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
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
            "reputation_score": user['reputation_score']
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user = Depends(get_current_user)):
    return {
        "id": current_user['id'],
        "username": current_user['username'],
        "email": current_user['email'],
        "reputation_score": current_user['reputation_score'],
        "contribution_stats": current_user['contribution_stats']
    }

# Media upload
@api_router.post("/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
    
    # Save file
    contents = await file.read()
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

# Claims
@api_router.post("/claims")
async def create_claim(
    claim_data: ClaimCreate,
    current_user = Depends(get_current_user)
):
    claim_id = str(uuid.uuid4())
    
    # Get media objects
    media_list = []
    if claim_data.media_ids:
        for media_id in claim_data.media_ids:
            media = await db.media.find_one({"id": media_id}, {"_id": 0})
            if media:
                media_list.append(media)
    
    claim = {
        "id": claim_id,
        "text": claim_data.text,
        "domain": claim_data.domain,
        "confidence_level": claim_data.confidence_level,
        "author_id": current_user['id'],
        "media_ids": claim_data.media_ids or [],
        "truth_label": TruthLabel.UNCERTAIN.value,
        "credibility_score": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.claims.insert_one(claim)
    
    # Update user stats
    await db.users.update_one(
        {"id": current_user['id']},
        {"$inc": {"contribution_stats.claims_posted": 1}}
    )
    
    return {
        "id": claim_id,
        "text": claim_data.text,
        "domain": claim_data.domain,
        "author": {
            "id": current_user['id'],
            "username": current_user['username'],
            "reputation_score": current_user['reputation_score']
        },
        "media": media_list,
        "truth_label": TruthLabel.UNCERTAIN.value,
        "credibility_score": 0.0
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
            "truth_label": claim['truth_label'],
            "credibility_score": claim['credibility_score'],
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
    
    return {
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
        "truth_label": claim['truth_label'],
        "credibility_score": claim['credibility_score'],
        "annotation_count": len(annotations),
        "created_at": claim['created_at']
    }

# Annotations
@api_router.post("/claims/{claim_id}/annotations")
async def create_annotation(
    claim_id: str,
    annotation_data: AnnotationCreate,
    current_user = Depends(get_current_user)
):
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
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
        "text": annotation_data.text,
        "annotation_type": annotation_data.annotation_type.value,
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
    
    # Recalculate claim credibility
    all_annotations = await db.annotations.find({"claim_id": claim_id}, {"_id": 0}).to_list(length=1000)
    
    # Enrich annotations with author data
    enriched_annotations = []
    for ann in all_annotations:
        author = await db.users.find_one({"id": ann['author_id']}, {"_id": 0})
        enriched_annotations.append({
            **ann,
            "author": author
        })
    
    credibility, truth_label = calculate_credibility_and_label(enriched_annotations)
    
    await db.claims.update_one(
        {"id": claim_id},
        {"$set": {"credibility_score": credibility, "truth_label": truth_label.value}}
    )
    
    return {
        "id": annotation_id,
        "claim_id": claim_id,
        "author": {
            "id": current_user['id'],
            "username": current_user['username'],
            "reputation_score": current_user['reputation_score']
        },
        "text": annotation_data.text,
        "annotation_type": annotation_data.annotation_type.value,
        "media": media_list,
        "helpful_votes": 0,
        "not_helpful_votes": 0
    }

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
        
        # Update annotation author's reputation
        author_id = annotation['author_id']
        await db.users.update_one(
            {"id": author_id},
            {"$inc": {"reputation_score": 1.0, "contribution_stats.helpful_votes_received": 1}}
        )
    else:
        await db.annotations.update_one(
            {"id": annotation_id},
            {"$inc": {"not_helpful_votes": 1}, "$push": {"voted_by": current_user['id']}}
        )
    
    # Recalculate claim credibility
    claim_id = annotation['claim_id']
    all_annotations = await db.annotations.find({"claim_id": claim_id}, {"_id": 0}).to_list(length=1000)
    
    enriched_annotations = []
    for ann in all_annotations:
        author = await db.users.find_one({"id": ann['author_id']}, {"_id": 0})
        enriched_annotations.append({
            **ann,
            "author": author
        })
    
    credibility, truth_label = calculate_credibility_and_label(enriched_annotations)
    
    await db.claims.update_one(
        {"id": claim_id},
        {"$set": {"credibility_score": credibility, "truth_label": truth_label.value}}
    )
    
    return {"message": "Vote recorded successfully"}

# User profile
@api_router.get("/users/{user_id}")
async def get_user_profile(user_id: str):
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's claims and annotations
    claims = await db.claims.find({"author_id": user_id}, {"_id": 0}).to_list(length=100)
    annotations = await db.annotations.find({"author_id": user_id}, {"_id": 0}).to_list(length=100)
    
    return {
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "reputation_score": user['reputation_score'],
        "contribution_stats": user['contribution_stats'],
        "created_at": user['created_at'],
        "recent_claims": claims[:5],
        "recent_annotations": annotations[:5]
    }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()