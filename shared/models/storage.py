"""Storage share data models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ShareProtocol(str, Enum):
    SMB = "smb"
    NFS = "nfs"


class StorageShare(BaseModel):
    id: str
    name: str
    path: str
    protocols: list[ShareProtocol]
    zfs_dataset: str | None
    allowed_users: list[str]
    read_only: bool
    created_at: datetime
