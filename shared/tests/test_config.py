"""Tests for shared.config module."""

import os
from unittest.mock import patch

from shared.config import HubSettings, get_settings


class TestHubSettingsDefaults:
    """Verify default values are sensible."""

    def test_default_ports(self) -> None:
        s = get_settings()
        assert s.api_gateway_port == 8000
        assert s.file_processor_port == 8001
        assert s.storage_service_port == 8002
        assert s.iot_bridge_port == 8003
        assert s.job_queue_port == 8004

    def test_default_domain(self) -> None:
        assert get_settings().domain == "localhost"

    def test_default_redis_url(self) -> None:
        assert get_settings().redis_url == "redis://localhost:6379/0"

    def test_default_service_urls(self) -> None:
        s = get_settings()
        assert s.file_processor_url == "http://localhost:8001"
        assert s.storage_service_url == "http://localhost:8002"
        assert s.iot_bridge_url == "http://localhost:8003"
        assert s.job_queue_url == "http://localhost:8004"

    def test_default_feature_flags_off(self) -> None:
        s = get_settings()
        assert s.enable_nextcloud is False
        assert s.enable_nfs is False
        assert s.enable_zfs is False
        assert s.enable_tailscale is False

    def test_default_log_level(self) -> None:
        assert get_settings().log_level == "INFO"

    def test_default_secret_key(self) -> None:
        assert get_settings().secret_key == "change-me-in-production"


class TestHubSettingsEnvOverride:
    """Verify HUB_ prefixed env vars override defaults."""

    def test_env_overrides_port(self) -> None:
        with patch.dict(os.environ, {"HUB_API_GATEWAY_PORT": "9999"}):
            assert HubSettings().api_gateway_port == 9999

    def test_env_overrides_domain(self) -> None:
        with patch.dict(os.environ, {"HUB_DOMAIN": "hub.example.com"}):
            assert HubSettings().domain == "hub.example.com"

    def test_env_overrides_feature_flag(self) -> None:
        with patch.dict(os.environ, {"HUB_ENABLE_ZFS": "true"}):
            assert HubSettings().enable_zfs is True

    def test_env_overrides_redis_url(self) -> None:
        with patch.dict(os.environ, {"HUB_REDIS_URL": "redis://redis:6380/1"}):
            assert HubSettings().redis_url == "redis://redis:6380/1"

    def test_env_overrides_secret_key(self) -> None:
        with patch.dict(os.environ, {"HUB_SECRET_KEY": "super-secret"}):
            assert HubSettings().secret_key == "super-secret"

    def test_env_overrides_log_level(self) -> None:
        with patch.dict(os.environ, {"HUB_LOG_LEVEL": "DEBUG"}):
            assert HubSettings().log_level == "DEBUG"


class TestGetSettingsOverrides:
    """Verify get_settings() keyword overrides work."""

    def test_override_port(self) -> None:
        s = get_settings(api_gateway_port=7777)
        assert s.api_gateway_port == 7777

    def test_override_domain(self) -> None:
        s = get_settings(domain="custom.local")
        assert s.domain == "custom.local"

    def test_override_feature_flag(self) -> None:
        s = get_settings(enable_tailscale=True)
        assert s.enable_tailscale is True
