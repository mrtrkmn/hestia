"""MQTT broker management and topic matching.

Requirements: 10.2, 10.3, 10.6, 11.1
"""

from __future__ import annotations

import re


def mqtt_topic_matches(pattern: str, topic: str) -> bool:
    """Check if an MQTT topic matches a subscription pattern.

    Supports '+' (single level) and '#' (multi level) wildcards.
    """
    pat_parts = pattern.split("/")
    top_parts = topic.split("/")

    i = 0
    for i, pp in enumerate(pat_parts):
        if pp == "#":
            return True  # matches everything from here
        if i >= len(top_parts):
            return False
        if pp != "+" and pp != top_parts[i]:
            return False

    return len(top_parts) == len(pat_parts)
