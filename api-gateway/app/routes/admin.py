"""Admin and health routes.

Requirements: 9.7, 12.2, 12.7
"""

from fastapi import APIRouter, Request, HTTPException

from shared.auth import check_rbac

router = APIRouter(tags=["admin"])


def _require_admin(request: Request) -> None:
    role = getattr(request.state, "role", None)
    if not role or not check_rbac(role, request.url.path, request.method):
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/api/v1/admin/users")
async def list_users(request: Request):
    _require_admin(request)
    return {"users": []}


@router.post("/api/v1/admin/users")
async def create_user(request: Request):
    _require_admin(request)
    return {"user_id": "pending", "status": "created"}


@router.put("/api/v1/admin/users/{user_id}")
async def update_user(request: Request, user_id: str):
    _require_admin(request)
    return {"user_id": user_id, "status": "updated"}


@router.delete("/api/v1/admin/users/{user_id}")
async def delete_user(request: Request, user_id: str):
    _require_admin(request)
    return {"user_id": user_id, "status": "deleted"}


@router.get("/api/v1/admin/logs")
async def get_logs(request: Request):
    _require_admin(request)
    return {"logs": []}


@router.get("/api/v1/services/health")
async def service_health():
    return {"services": []}
