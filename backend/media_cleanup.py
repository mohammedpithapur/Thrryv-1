"""
Media file cleanup utilities for Thrryv
Handles orphaned files and cleanup when claims/users are deleted
"""
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Set
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


async def cleanup_orphaned_media(db, upload_dir: Path) -> dict:
    """
    Find and delete media files that are not referenced by any claim or user
    
    Args:
        db: MongoDB database instance
        upload_dir: Directory where media files are stored
    
    Returns:
        dict with cleanup statistics
    """
    logger.info("Starting orphaned media cleanup")
    
    # Get all referenced media IDs from database
    referenced_media_ids: Set[str] = set()
    
    # Get media from claims
    claims = await db.claims.find({}, {"_id": 0, "media_ids": 1}).to_list(length=100000)
    for claim in claims:
        referenced_media_ids.update(claim.get('media_ids', []))
    
    # Get media from users (profile pictures)
    users = await db.users.find({}, {"_id": 0, "profile_picture": 1}).to_list(length=100000)
    for user in users:
        if user.get('profile_picture'):
            # Extract ID from file path
            profile_pic_path = Path(user['profile_picture'])
            media_id = profile_pic_path.stem.replace('profile_', '')
            referenced_media_ids.add(media_id)
    
    # Get all media records from database
    all_media = await db.media.find({}, {"_id": 0, "id": 1, "file_path": 1}).to_list(length=100000)
    db_media_ids = {m['id'] for m in all_media}
    media_file_paths = {m['id']: m['file_path'] for m in all_media}
    
    # Find orphaned media in database
    orphaned_db_media = db_media_ids - referenced_media_ids
    
    # Find orphaned files in filesystem
    orphaned_files: List[Path] = []
    deleted_files = 0
    deleted_db_records = 0
    
    # Check filesystem for unreferenced files
    if upload_dir.exists():
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                # Extract media ID from filename
                stem = file_path.stem
                if stem.startswith('profile_'):
                    media_id = stem.replace('profile_', '')
                else:
                    media_id = stem
                
                # Check if this file is referenced
                if media_id not in referenced_media_ids:
                    orphaned_files.append(file_path)
    
    # Delete orphaned database records
    if orphaned_db_media:
        result = await db.media.delete_many({"id": {"$in": list(orphaned_db_media)}})
        deleted_db_records = result.deleted_count
        logger.info(f"Deleted {deleted_db_records} orphaned media records from database")
    
    # Delete orphaned files
    for file_path in orphaned_files:
        try:
            file_path.unlink()
            deleted_files += 1
            logger.debug(f"Deleted orphaned file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
    
    logger.info(f"Cleanup complete: {deleted_files} files and {deleted_db_records} DB records deleted")
    
    return {
        "deleted_files": deleted_files,
        "deleted_db_records": deleted_db_records,
        "total_media_in_db": len(db_media_ids),
        "referenced_media": len(referenced_media_ids),
        "orphaned_found": len(orphaned_db_media) + len(orphaned_files)
    }


async def delete_media_files(media_ids: List[str], db, upload_dir: Path) -> int:
    """
    Delete specific media files and their database records
    
    Args:
        media_ids: List of media IDs to delete
        db: MongoDB database instance
        upload_dir: Directory where media files are stored
    
    Returns:
        Number of files successfully deleted
    """
    deleted_count = 0
    
    for media_id in media_ids:
        try:
            # Get media record
            media = await db.media.find_one({"id": media_id}, {"_id": 0})
            if not media:
                continue
            
            # Delete file from filesystem
            file_path = Path(media['file_path'])
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted media file: {file_path}")
            
            # Delete database record
            await db.media.delete_one({"id": media_id})
            deleted_count += 1
            
        except Exception as e:
            logger.error(f"Failed to delete media {media_id}: {e}")
    
    return deleted_count


async def cleanup_old_media(db, upload_dir: Path, days_old: int = 90) -> dict:
    """
    Delete media files older than specified days that are not referenced
    
    Args:
        db: MongoDB database instance
        upload_dir: Directory where media files are stored
        days_old: Age threshold in days
    
    Returns:
        dict with cleanup statistics
    """
    logger.info(f"Starting cleanup of media older than {days_old} days")
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    # Find old media records
    old_media = await db.media.find({
        "created_at": {"$lt": cutoff_date.isoformat()}
    }, {"_id": 0, "id": 1}).to_list(length=100000)
    
    old_media_ids = [m['id'] for m in old_media]
    
    # Check which ones are still referenced
    referenced = set()
    
    claims = await db.claims.find({
        "media_ids": {"$in": old_media_ids}
    }, {"_id": 0, "media_ids": 1}).to_list(length=100000)
    
    for claim in claims:
        referenced.update(claim.get('media_ids', []))
    
    # Delete unreferenced old media
    unreferenced_old = [mid for mid in old_media_ids if mid not in referenced]
    deleted = await delete_media_files(unreferenced_old, db, upload_dir)
    
    logger.info(f"Deleted {deleted} old unreferenced media files")
    
    return {
        "total_old_media": len(old_media_ids),
        "still_referenced": len(referenced),
        "deleted": deleted
    }


async def get_storage_stats(db, upload_dir: Path) -> dict:
    """
    Get statistics about media storage
    
    Returns:
        dict with storage statistics
    """
    total_files = 0
    total_size = 0
    
    if upload_dir.exists():
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
    
    media_count = await db.media.count_documents({})
    
    return {
        "total_files_on_disk": total_files,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "media_records_in_db": media_count,
        "upload_directory": str(upload_dir)
    }
