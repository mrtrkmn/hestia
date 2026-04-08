"""Shared configuration module for Hestia.

Reads settings from environment variables (HUB_ prefix) with fallback
to config files in /etc/hestia/.
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


_CONFIG_DIR = Path("/etc/hestia")


class HubSettings(BaseSettings):
    """Central configuration for all Hestia services."""

    model_config = SettingsConfigDict(
        env_prefix="HUB_",
        env_file=str(_CONFIG_DIR / ".env") if _CONFIG_DIR.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Service ports ---
    api_gateway_port: int = Field(default=8000, description="API Gateway listen port")
    file_processor_port: int = Field(default=8001, description="File Processor listen port")
    storage_service_port: int = Field(default=8002, description="Storage Service listen port")
    iot_bridge_port: int = Field(default=8003, description="IoT Bridge listen port")
    job_queue_port: int = Field(default=8004, description="Job Queue API listen port")

    # --- Domain / hostname ---
    domain: str = Field(default="localhost", description="Public domain or hostname for the Hub")

    # --- Redis ---
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # --- Service URLs (inter-service communication) ---
    file_processor_url: str = Field(default="http://localhost:8001", description="File Processor base URL")
    storage_service_url: str = Field(default="http://localhost:8002", description="Storage Service base URL")
    iot_bridge_url: str = Field(default="http://localhost:8003", description="IoT Bridge base URL")
    job_queue_url: str = Field(default="http://localhost:8004", description="Job Queue base URL")

    # --- Security ---
    secret_key: str = Field(default="change-me-in-production", description="Secret key for JWT signing")

    # --- Feature flags ---
    enable_nextcloud: bool = Field(default=False, description="Enable optional Nextcloud integration")
    enable_nfs: bool = Field(default=False, description="Enable NFS exports")
    enable_zfs: bool = Field(default=False, description="Enable ZFS dataset management")
    enable_tailscale: bool = Field(default=False, description="Enable Tailscale mesh VPN")

    # --- Logging ---
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")


def get_settings(**overrides: object) -> HubSettings:
    """Create a HubSettings instance, optionally overriding values.

    Useful in tests or when a service needs to tweak defaults.
    """
    return HubSettings(**overrides)  # type: ignore[arg-type]
