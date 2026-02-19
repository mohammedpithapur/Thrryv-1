# MongoDB Index Migration Script for Thrryv
# Run this script once to create all recommended indexes outside of app startup.

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

async def create_indexes():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    print('Creating indexes...')
    # Claims
    await db.claims.create_index([('created_at', -1)])
    await db.claims.create_index([('domain', 1)])
    await db.claims.create_index([('category.primary_path', 1)])
    # Users
    await db.users.create_index([('id', 1)], unique=True)
    await db.users.create_index([('email', 1)], unique=True)
    await db.users.create_index([('username', 1)], unique=True)
    # Annotations
    await db.annotations.create_index([('claim_id', 1)])
    await db.annotations.create_index([('author_id', 1)])
    print('Indexes created.')
    client.close()

if __name__ == '__main__':
    asyncio.run(create_indexes())
