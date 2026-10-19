import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./miaoqiang.db')
    redis_url: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    secret_key: str = os.getenv('SECRET_KEY', 'dev-only-change-me')
    access_token_minutes: int = int(os.getenv('ACCESS_TOKEN_MINUTES', '30'))
    reservation_ttl: int = int(os.getenv('RESERVATION_TTL_SECONDS', '300'))
settings = Settings()
