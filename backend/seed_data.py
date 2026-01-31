import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone, timedelta
import uuid
import bcrypt
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def seed_database():
    print("Seeding database...")
    
    # Clear existing data
    await db.users.delete_many({})
    await db.claims.delete_many({})
    await db.annotations.delete_many({})
    await db.media.delete_many({})
    
    # Create users
    users = []
    user_data = [
        {"username": "dr_scientist", "email": "scientist@example.com", "reputation": 85.0},
        {"username": "fact_checker", "email": "checker@example.com", "reputation": 72.0},
        {"username": "researcher_jane", "email": "jane@example.com", "reputation": 65.0},
        {"username": "truth_seeker", "email": "seeker@example.com", "reputation": 45.0},
        {"username": "skeptic_bob", "email": "bob@example.com", "reputation": 38.0},
    ]
    
    for i, data in enumerate(user_data):
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "username": data["username"],
            "email": data["email"],
            "password": hash_password("password123"),
            "reputation_score": data["reputation"],
            "contribution_stats": {
                "claims_posted": 0,
                "annotations_added": 0,
                "helpful_votes_received": 0
            },
            "created_at": (datetime.now(timezone.utc) - timedelta(days=60-i*10)).isoformat()
        }
        await db.users.insert_one(user)
        users.append(user)
    
    print(f"Created {len(users)} users")
    
    # Create claims
    claims_data = [
        {
            "text": "Climate change is primarily caused by human activities according to scientific consensus, with 97% of climate scientists agreeing.",
            "domain": "Science",
            "confidence": 90,
            "days_ago": 5
        },
        {
            "text": "Regular exercise for 30 minutes a day can reduce the risk of heart disease by up to 50% according to multiple health studies.",
            "domain": "Health",
            "confidence": 85,
            "days_ago": 8
        },
        {
            "text": "The Great Wall of China is visible from space with the naked eye.",
            "domain": "History",
            "confidence": 40,
            "days_ago": 12
        },
        {
            "text": "Vaccines have eliminated smallpox globally and reduced polio cases by 99% since 1988.",
            "domain": "Health",
            "confidence": 95,
            "days_ago": 3
        },
        {
            "text": "Renewable energy sources now account for over 30% of global electricity generation capacity.",
            "domain": "Environment",
            "confidence": 80,
            "days_ago": 7
        },
        {
            "text": "The human brain uses only 10% of its capacity.",
            "domain": "Science",
            "confidence": 30,
            "days_ago": 15
        },
        {
            "text": "Drinking 8 glasses of water per day is necessary for optimal health.",
            "domain": "Health",
            "confidence": 50,
            "days_ago": 10
        },
        {
            "text": "Electric vehicles produce zero emissions during operation.",
            "domain": "Technology",
            "confidence": 85,
            "days_ago": 6
        },
        {
            "text": "Studies show that reading before bed improves sleep quality and cognitive function.",
            "domain": "Health",
            "confidence": 70,
            "days_ago": 9
        },
        {
            "text": "The global poverty rate has declined by more than half since 1990 according to World Bank data.",
            "domain": "Economics",
            "confidence": 88,
            "days_ago": 4
        }
    ]
    
    claims = []
    for i, claim_data in enumerate(claims_data):
        claim_id = str(uuid.uuid4())
        author = users[i % len(users)]
        
        claim = {
            "id": claim_id,
            "text": claim_data["text"],
            "domain": claim_data["domain"],
            "confidence_level": claim_data["confidence"],
            "author_id": author['id'],
            "media_ids": [],
            "truth_label": "Uncertain",
            "credibility_score": 0.0,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=claim_data["days_ago"])).isoformat()
        }
        await db.claims.insert_one(claim)
        claims.append(claim)
        
        # Update user stats
        await db.users.update_one(
            {"id": author['id']},
            {"$inc": {"contribution_stats.claims_posted": 1}}
        )
    
    print(f"Created {len(claims)} claims")
    
    # Create annotations for some claims
    annotations_count = 0
    
    # Add annotations to first few claims to create variety
    for i in range(5):
        claim = claims[i]
        num_annotations = (i % 3) + 2  # 2-4 annotations per claim
        
        for j in range(num_annotations):
            annotator = users[(i + j + 1) % len(users)]
            annotation_id = str(uuid.uuid4())
            
            annotation_types = ['support', 'contradict', 'context']
            ann_type = annotation_types[j % 3]
            
            annotation_texts = {
                'support': [
                    "Multiple peer-reviewed studies confirm this finding. See Nature Journal 2023.",
                    "This aligns with WHO guidelines and recommendations.",
                    "Independent research teams have replicated these results.",
                ],
                'contradict': [
                    "Recent studies suggest the numbers may be overstated.",
                    "This claim lacks sufficient evidence from credible sources.",
                    "Counter-evidence suggests a more nuanced interpretation.",
                ],
                'context': [
                    "It's important to note that results may vary based on individual circumstances.",
                    "This should be considered alongside other contributing factors.",
                    "The timeframe and methodology of the study are key to understanding this claim.",
                ]
            }
            
            annotation = {
                "id": annotation_id,
                "claim_id": claim['id'],
                "author_id": annotator['id'],
                "text": annotation_texts[ann_type][j % 3],
                "annotation_type": ann_type,
                "media_ids": [],
                "helpful_votes": 0,
                "not_helpful_votes": 0,
                "voted_by": [],
                "created_at": (datetime.now(timezone.utc) - timedelta(days=claim_data["days_ago"]-1, hours=j*6)).isoformat()
            }
            await db.annotations.insert_one(annotation)
            annotations_count += 1
            
            # Update user stats
            await db.users.update_one(
                {"id": annotator['id']},
                {"$inc": {"contribution_stats.annotations_added": 1}}
            )
    
    print(f"Created {annotations_count} annotations")
    
    # Recalculate credibility scores for claims with annotations
    for claim in claims[:5]:
        annotations = await db.annotations.find({"claim_id": claim['id']}, {"_id": 0}).to_list(length=1000)
        
        if len(annotations) >= 3:
            support_count = sum(1 for a in annotations if a['annotation_type'] == 'support')
            contradict_count = sum(1 for a in annotations if a['annotation_type'] == 'contradict')
            total = support_count + contradict_count
            
            if total > 0:
                support_ratio = support_count / total
                credibility = support_ratio * 100
                
                # Determine truth label
                if support_ratio >= 0.85:
                    label = "True"
                elif support_ratio >= 0.65:
                    label = "Likely True"
                elif support_ratio >= 0.45:
                    label = "Mixed Evidence"
                elif support_ratio >= 0.25:
                    label = "Likely False"
                else:
                    label = "False"
                
                await db.claims.update_one(
                    {"id": claim['id']},
                    {"$set": {"credibility_score": credibility, "truth_label": label}}
                )
    
    print("Database seeded successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
