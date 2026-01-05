"""
JWT Service

Handles JWT token generation, verification, and refresh.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from server.config import config


# JWT configuration
JWT_SECRET_KEY = getattr(config, "JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_EXPIRE_MINUTES = getattr(config, "JWT_ACCESS_EXPIRE_MINUTES", 15)
JWT_REFRESH_EXPIRE_DAYS = getattr(config, "JWT_REFRESH_EXPIRE_DAYS", 7)


def generate_access_token(person_id: str, role: Optional[str] = None) -> str:
    """
    Generate JWT access token.
    
    Payload: {sub: person_id, role: role, exp: now + 15min, type: "access"}
    Returns JWT string.
    """
    payload = {
        "sub": person_id,
        "role": role,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=JWT_ACCESS_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def generate_refresh_token(person_id: str) -> str:
    """
    Generate JWT refresh token.
    
    Payload: {sub: person_id, exp: now + 7days, type: "refresh"}
    Returns JWT string.
    """
    payload = {
        "sub": person_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str, token_type: str = "access") -> Dict:
    """
    Verify and decode JWT token.
    
    Checks expiration and type.
    Returns payload or raises exception.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            raise ValueError(f"Invalid token type. Expected {token_type}")
        
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")


def decode_token(token: str) -> Dict:
    """
    Decode JWT token without verification (for debugging).
    
    Returns payload dictionary.
    """
    return jwt.decode(token, options={"verify_signature": False})

