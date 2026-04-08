"""Optional Nextcloud integration.

Requirements: 6.1-6.5
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NextcloudConfig:
    enabled: bool = False
    data_dir: str = "/srv/nextcloud/data"
    admin_user: str = "admin"


class NextcloudManager:
    """Manages optional local Nextcloud instance."""

    def __init__(self, config: NextcloudConfig) -> None:
        self.config = config

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    def deploy_command(self) -> str | None:
        if not self.enabled:
            return None
        return f"nextcloud.occ maintenance:install --data-dir {self.config.data_dir}"
