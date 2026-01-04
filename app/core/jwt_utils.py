"""JWT Token Management Module.

This module provides utilities for creating and verifying JWT access tokens
used for user authentication. Tokens include expiration times and are signed
using configured secret key and algorithm.
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from app.core.config import settings


SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with expiration.
    
    Generates signed JWT token containing user data and expiration time.
    Used for authenticating API requests.
    
    Args:
        data: Payload to encode in token (typically {"sub": user_id}).
        expires_delta: Optional custom expiration time; defaults to ACCESS_TOKEN_EXPIRE_MINUTES.
        
    Returns:
        str: Encoded JWT token string.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_access_token(token: str) -> Optional[dict]:
    """Verify and decode JWT access token.
    
    Validates token signature and expiration, returning decoded payload
    if valid.
    
    Args:
        token: JWT token string to verify.
        
    Returns:
        dict: Decoded token payload if valid.
        None: If token is invalid, expired, or verification fails.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None
