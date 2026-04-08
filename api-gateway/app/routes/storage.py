"""Storage routes.

Requirements: 5.1-5.6
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/storage", tags=["storage"])


class ShareRequest(BaseModel):
    name: str
    path: str
    protocols: list[str] = ["smb"]
    allowed_users: list[str] = []
    read_only: bool = False


@router.get("/shares")
async def list_shares():
    return {"shares": []}


@router.post("/shares")
async def create_share(req: ShareRequest):
    return {"share_id": "pending", "status": "created"}


@router.put("/shares/{share_id}")
async def update_share(share_id: str, req: ShareRequest):
    return {"share_id": share_id, "status": "updated"}


@router.delete("/shares/{share_id}")
async def delete_share(share_id: str):
    return {"share_id": share_id, "status": "deleted"}


@router.post("/snapshots")
async def create_snapshot(dataset: str = ""):
    return {"snapshot_id": "pending"}


@router.post("/snapshots/{snapshot_id}/restore")
async def restore_snapshot(snapshot_id: str):
    return {"snapshot_id": snapshot_id, "status": "restoring"}
