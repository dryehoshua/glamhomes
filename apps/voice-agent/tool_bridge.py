#!/usr/bin/env python3
"""Shared Realtime tool bridge helpers for GLAM HOMES Concierge.

The web demo and the Twilio Media Streams process both use this bridge layer so
tool calls stay consistent across channels.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


TOOL_BRIDGE_GROUPS = {
    "guesty_read": {
        "guesty_status",
        "guesty_search_reservation",
        "guesty_confirm_reservation",
        "guesty_get_reservation",
        "guesty_list_listings",
        "guesty_available_listings",
        "guesty_listing_calendar",
    },
    "property_links": {
        "glam_search_public_property_links",
    },
    "twilio_sms": {
        "twilio_send_property_link_sms",
        "twilio_send_human_handoff_sms",
    },
}


def tool_bridge_name(tool_name: str) -> str:
    for bridge_name, tool_names in TOOL_BRIDGE_GROUPS.items():
        if tool_name in tool_names:
            return bridge_name
    return "unknown"


def apply_tool_context(tool_name: str, arguments: dict[str, Any] | None, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Merge channel context into tool arguments without mutating caller data."""

    merged = deepcopy(arguments or {})
    context = context or {}
    if tool_name in {"twilio_send_property_link_sms", "twilio_send_human_handoff_sms"}:
        if not merged.get("phone_number") and context.get("caller"):
            merged["phone_number"] = context["caller"]
        if not merged.get("call_sid") and context.get("call_sid"):
            merged["call_sid"] = context["call_sid"]
        if not merged.get("called_number") and context.get("called"):
            merged["called_number"] = context["called"]
    return merged
