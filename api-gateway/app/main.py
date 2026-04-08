"""API Gateway — FastAPI entry point.

Central HTTP gateway that routes authenticated API requests to
the appropriate microservice.

Requirements: 9.4, 15.7, 15.8, 17.1, 17.2, 17.4
"""

from fastapi import FastAPI

from app.config import JWT_SECRET, AUTH_LOGIN_URL, RATE_LIMIT_PER_MINUTE
from app.middleware.jwt_auth import JWTMiddleware
from app.middleware.validation import SanitizationMiddleware, RateLimitMiddleware
from app.routes import files, jobs, pipelines, storage, iot, admin

app = FastAPI(
    title="Hestia API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/openapi.json",
)

# Middleware order: outermost first in add_middleware = applied last
app.add_middleware(JWTMiddleware, secret=JWT_SECRET, login_url=AUTH_LOGIN_URL)
app.add_middleware(SanitizationMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=RATE_LIMIT_PER_MINUTE)

# Register route modules
app.include_router(files.router)
app.include_router(jobs.router)
app.include_router(pipelines.router)
app.include_router(storage.router)
app.include_router(iot.router)
app.include_router(admin.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
