"""API Gateway configuration."""

from shared.config import get_settings

settings = get_settings()

JWT_SECRET: str = settings.secret_key
AUTH_LOGIN_URL: str = "/auth/login"
RATE_LIMIT_PER_MINUTE: int = 100
