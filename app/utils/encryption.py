from cryptography.fernet import Fernet
from app.config import settings
import json


def _cipher():
    if not settings.ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY not set in environment")
    key = settings.ENCRYPTION_KEY.encode()
    return Fernet(key)


def encrypt_data(data: dict) -> str:
    """Encrypt sensitive data"""
    return _cipher().encrypt(json.dumps(data).encode()).decode()


def decrypt_data(encrypted: str) -> dict:
    """Decrypt sensitive data"""
    return json.loads(_cipher().decrypt(encrypted.encode()).decode())
