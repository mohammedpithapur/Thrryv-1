"""
Input validation and sanitization utilities for Thrryv API
Prevents XSS, SQL injection, and other security vulnerabilities
"""
import re
import html
from typing import Optional, Any
from fastapi import HTTPException


class InputValidator:
    """Validates and sanitizes user inputs"""
    
    # Regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    
    # Dangerous patterns
    XSS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),  # onclick, onerror, etc.
        re.compile(r'<iframe', re.IGNORECASE),
        re.compile(r'<object', re.IGNORECASE),
        re.compile(r'<embed', re.IGNORECASE),
    ]
    
    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None, allow_html: bool = False) -> str:
        """
        Sanitize text input to prevent XSS attacks
        
        Args:
            text: The text to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow basic HTML tags (still sanitized)
        
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            raise HTTPException(status_code=400, detail="Text must be a string")
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Check length
        if max_length and len(text) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"Text exceeds maximum length of {max_length} characters"
            )
        
        # Check for XSS patterns
        for pattern in InputValidator.XSS_PATTERNS:
            if pattern.search(text):
                raise HTTPException(
                    status_code=400,
                    detail="Input contains potentially dangerous content"
                )
        
        # HTML escape if not allowing HTML
        if not allow_html:
            text = html.escape(text)
        
        return text
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email address"""
        if not isinstance(email, str):
            raise HTTPException(status_code=400, detail="Email must be a string")
        
        email = email.strip().lower()
        
        if not InputValidator.EMAIL_PATTERN.match(email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        if len(email) > 254:  # RFC 5321
            raise HTTPException(status_code=400, detail="Email too long")
        
        return email
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate and sanitize username"""
        if not isinstance(username, str):
            raise HTTPException(status_code=400, detail="Username must be a string")
        
        username = username.strip()
        
        if not InputValidator.USERNAME_PATTERN.match(username):
            raise HTTPException(
                status_code=400,
                detail="Username must be 3-30 characters and contain only letters, numbers, underscores, and hyphens"
            )
        
        # Check for reserved usernames
        reserved = ['admin', 'root', 'system', 'api', 'thrryv', 'moderator']
        if username.lower() in reserved:
            raise HTTPException(status_code=400, detail="Username is reserved")
        
        return username
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password strength"""
        if not isinstance(password, str):
            raise HTTPException(status_code=400, detail="Password must be a string")
        
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        if len(password) > 128:
            raise HTTPException(status_code=400, detail="Password too long")
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', password) or not re.search(r'[0-9]', password):
            raise HTTPException(
                status_code=400,
                detail="Password must contain at least one letter and one number"
            )
        
        return password
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> str:
        """Validate UUID format"""
        if not isinstance(uuid_str, str):
            raise HTTPException(status_code=400, detail="UUID must be a string")
        
        uuid_str = uuid_str.strip().lower()
        
        if not InputValidator.UUID_PATTERN.match(uuid_str):
            raise HTTPException(status_code=400, detail="Invalid UUID format")
        
        return uuid_str
    
    @staticmethod
    def validate_confidence_level(level: int) -> int:
        """Validate confidence level (0-100)"""
        if not isinstance(level, int):
            raise HTTPException(status_code=400, detail="Confidence level must be an integer")
        
        if level < 0 or level > 100:
            raise HTTPException(status_code=400, detail="Confidence level must be between 0 and 100")
        
        return level
    
    @staticmethod
    def validate_word_count(text: str, max_words: int = 250) -> bool:
        """Validate word count"""
        words = text.split()
        word_count = len([w for w in words if w.strip()])
        
        if word_count > max_words:
            raise HTTPException(
                status_code=400,
                detail=f"Text exceeds maximum word count of {max_words} words"
            )
        
        return True
    
    @staticmethod
    def sanitize_dict(data: dict, allowed_keys: list) -> dict:
        """Remove unexpected keys from dictionary"""
        return {k: v for k, v in data.items() if k in allowed_keys}


def validate_media_file(filename: str, content_type: str, size: int) -> None:
    """
    Validate uploaded media files
    
    Args:
        filename: Original filename
        content_type: MIME type
        size: File size in bytes
    """
    # Check file size (50MB max)
    MAX_SIZE = 50 * 1024 * 1024
    if size > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    # Validate content type
    allowed_types = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/avif',
        'video/mp4', 'video/webm', 'video/ogg', 'video/quicktime'
    ]
    
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: images (JPEG, PNG, GIF, WebP, AVIF) and videos (MP4, WebM, OGG, MOV)"
        )
    
    # Validate filename
    filename_lower = filename.lower()
    dangerous_extensions = ['.exe', '.sh', '.bat', '.cmd', '.com', '.js', '.php', '.py']
    
    if any(filename_lower.endswith(ext) for ext in dangerous_extensions):
        raise HTTPException(status_code=400, detail="Dangerous file extension detected")
    
    # Check for path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
