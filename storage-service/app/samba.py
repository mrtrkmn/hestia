"""Samba share management.

Requirements: 5.1, 5.4, 5.5
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SambaShare:
    name: str
    path: str
    allowed_users: list[str] = field(default_factory=list)
    read_only: bool = False


class SambaManager:
    """Manages SMB shares (in-memory for now, generates smb.conf snippets)."""

    def __init__(self) -> None:
        self._shares: dict[str, SambaShare] = {}

    def create_share(self, share: SambaShare) -> None:
        self._shares[share.name] = share

    def delete_share(self, name: str) -> bool:
        return self._shares.pop(name, None) is not None

    def get_share(self, name: str) -> SambaShare | None:
        return self._shares.get(name)

    def list_shares(self) -> list[SambaShare]:
        return list(self._shares.values())

    def check_access(self, share_name: str, user_id: str, user_role: str = "user") -> bool:
        """Return True iff user has access to the share."""
        if user_role == "admin":
            return True
        share = self._shares.get(share_name)
        if share is None:
            return False
        return user_id in share.allowed_users

    def generate_conf_section(self, share: SambaShare) -> str:
        lines = [
            f"[{share.name}]",
            f"   path = {share.path}",
            f"   read only = {'yes' if share.read_only else 'no'}",
            f"   valid users = {' '.join(share.allowed_users)}",
            "   browseable = yes",
        ]
        return "\n".join(lines)
