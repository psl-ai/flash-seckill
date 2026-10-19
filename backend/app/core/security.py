from datetime import datetime, timedelta, timezone
from jose import jwt
import bcrypt
import os

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-change-me')
ALGORITHM = 'HS256'
def hash_password(password: str) -> str: return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
def verify_password(password: str, hashed: str) -> bool: return bcrypt.checkpw(password.encode(), hashed.encode())
def create_access_token(data: dict, expires_minutes: int = 30) -> str:
    payload = data.copy(); payload['exp'] = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
def decode_token(token: str) -> dict: return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
