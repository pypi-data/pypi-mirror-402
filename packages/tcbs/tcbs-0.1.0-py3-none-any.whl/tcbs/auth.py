"""Token management and persistence"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict


class TokenManager:
    """Manages JWT token persistence and validation"""
    
    TOKEN_FILE = Path.home() / ".tcbs_token.json"
    TOKEN_LIFETIME_HOURS = 8
    
    @classmethod
    def save_token(cls, token: str, expires_in: int = None) -> None:
        """Save token with expiry timestamp to local file"""
        if expires_in is None:
            expires_in = cls.TOKEN_LIFETIME_HOURS * 3600
        
        expiry = datetime.now() + timedelta(seconds=expires_in)
        
        data = {
            "token": token,
            "expiry": expiry.isoformat()
        }
        
        cls.TOKEN_FILE.write_text(json.dumps(data))
        cls.TOKEN_FILE.chmod(0o600)  # Secure file permissions
    
    @classmethod
    def load_token(cls) -> Optional[str]:
        """Load token if exists and not expired"""
        if not cls.TOKEN_FILE.exists():
            return None
        
        try:
            data = json.loads(cls.TOKEN_FILE.read_text())
            expiry = datetime.fromisoformat(data["expiry"])
            
            if datetime.now() < expiry:
                return data["token"]
            else:
                cls.clear_token()
                return None
        except (json.JSONDecodeError, KeyError, ValueError):
            cls.clear_token()
            return None
    
    @classmethod
    def clear_token(cls) -> None:
        """Remove token file"""
        if cls.TOKEN_FILE.exists():
            cls.TOKEN_FILE.unlink()
    
    @classmethod
    def is_valid(cls) -> bool:
        """Check if token exists and is valid"""
        return cls.load_token() is not None
