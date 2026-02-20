from cryptography.fernet import Fernet
from app.config import settings
import json
import base64


def _cipher():
    if not settings.ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY not set in environment")
    
    # Validate key format
    try:
        key = settings.ENCRYPTION_KEY.encode()
        # Test if it's a valid Fernet key
        base64.urlsafe_b64decode(key)
        if len(base64.urlsafe_b64decode(key)) != 32:
            raise ValueError("Encryption key must be 32 bytes (44 chars base64)")
        return Fernet(key)
    except Exception as e:
        raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}. Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'") from e


def encrypt_data(data: dict) -> str:
    """Encrypt sensitive data"""
    return _cipher().encrypt(json.dumps(data).encode()).decode()


def decrypt_data(encrypted: str) -> dict:
    """Decrypt sensitive data"""
    return json.loads(_cipher().decrypt(encrypted.encode()).decode())
