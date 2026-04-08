"""Home Assistant integration.

Requirements: 10.1, 10.4, 10.5
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HAEntity:
    entity_id: str
    state: str
    attributes: dict


class HomeAssistantClient:
    """Client for Home Assistant REST API."""

    def __init__(self, url: str = "http://localhost:8123", token: str = "") -> None:
        self.url = url
        self.token = token

    def get_entity(self, entity_id: str) -> HAEntity | None:
        # Stub — would call HA API
        return None

    def list_entities(self) -> list[HAEntity]:
        return []
