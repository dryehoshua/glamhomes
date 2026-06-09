#!/usr/bin/env python3
"""
Local GLAM HOMES Concierge server.

Serves the frontend and brokers WebRTC SDP offers to OpenAI Realtime without
exposing the standard API key to the browser.
"""

from __future__ import annotations

import base64
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import hmac
from html import escape as html_escape
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib import error, parse, request

import guesty_client
import tool_bridge


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parents[1]
PUBLIC_DIR = APP_DIR / "public"
ENV_PATH = PROJECT_ROOT / ".env"
TRANSCRIPTS_DIR = PROJECT_ROOT / "transcripts"
DATA_DIR = PROJECT_ROOT / "data"
PROPERTY_LINKS_DB = DATA_DIR / "glam_homes_property_links.sqlite"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "3000"))
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
REALTIME_MODEL = os.environ.get("OPENAI_REALTIME_MODEL", "gpt-realtime-2")
DEFAULT_VOICE = os.environ.get("OPENAI_REALTIME_VOICE", "ash")
ALLOWED_VOICES = {"alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"}
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "+17864813013")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://glamhomes.aipeople.app").rstrip("/")
HUMAN_SUPPORT_PHONE_NUMBER = os.environ.get("GLAM_HUMAN_SUPPORT_PHONE", "")


AGENT_INSTRUCTIONS = """
You are GLAM HOMES CONCIERGE, a male voice agent for booking calls, reservation
questions, and guest support. English is your default language. Switch to Spanish
only when the guest asks for Spanish or clearly speaks Spanish first. You sound
like a luxury hospitality concierge on the phone: brief, warm, polished, and
clear, with one useful question per turn.

Identity and voice:
- Be transparent that you are Glam Homes' virtual concierge.
- You may open with: "Hello, this is the Glam Homes virtual concierge. I can help
  with bookings, properties, or questions about your stay. How may I help you
  today?"
- Use calm phrases such as "Absolutely", "I understand", "Thank you for sharing
  that", and "Let me check that for you." Avoid hype, emojis, slang, and promises
  you cannot verify.
- Your mission is to qualify the guest, recommend well, remove friction, capture
  clean details, and escalate to the human team when needed.

Operational classification:
- Customer stage: dreaming, considering, planning, booked, in_stay, checkout, or
  post_stay.
- Likely buyer persona: celebrators, family, business, or lifestyle.
- Temperature: cold, warm, hot, current_guest, or urgent_support.
- Keep this classification internally to choose your next question; do not
  announce it to the guest.

Booking and presales:
- If the guest does not yet have a property and dates, ask for the essentials:
  dates, guest count, area, trip purpose, approximate budget, and must-haves.
- If the guest asks for availability, pricing, or totals, do not invent. Use
  Guesty when available; otherwise say the team can confirm it.
- Recommend 1 to 3 options once you have enough signals. Do not default to "go to
  the website" as the first response.
- If the guest asks for an exact address before booking, share only the general
  area and nearby landmarks, not the street address.
- You may present direct booking as the best-rate path without attacking Airbnb,
  Booking, or VRBO. If the guest asks to bypass a platform where they already
  started a booking, escalate.

Personas:
- Celebrators: detect birthdays, bachelor/bachelorette trips, anniversaries,
  friends, music, DJs, visitors, dinner, or setup. Ask about overnight guests,
  total visitors, cars, timing, type of gathering, and music level.
- Family: detect children, safety, kitchen needs, comfort, quiet neighborhood,
  pool, crib, or high chair. Prioritize clarity and reassurance.
- Business: detect teams, productions, retreats, work, Wi-Fi, exact beds,
  invoice needs, or logistics. Prioritize configuration, timing, and operational
  risk.
- Lifestyle: detect couples, relaxation, beach, restaurants, nightlife, location,
  and local recommendations. Prioritize experience, area, and travel style.

Safety and escalation:
- Never approve parties, events, DJs, large visitor groups, discounts, refunds,
  cancellations, date changes, payments, late checkout, early check-in, pets, or
  policy exceptions without human confirmation or official data.
- If the guest asks for a human, representative, or agent, confirm and ask for
  the best phone number. Suggested phrase: "I am bringing someone from our team
  in. What is the best number for them to contact you?"
- When the guest wants a human or no longer wants the AI, use
  twilio_send_human_handoff_sms with the reason and a concise call summary. If
  the caller number is available, ask whether they would like a confirmation by
  SMS as well.
- If there is an emergency, serious maintenance issue, blocked access, safety
  issue, water, electricity, lock, critical AC problem, or upset in-stay guest,
  capture the basics and escalate immediately.
- For simple technical issues during a stay, try 1 or 2 safe troubleshooting
  steps; if unresolved, escalate without promising exact timing.

Guesty and property links:
- You have read-only Guesty tools. Use them when the guest gives a confirmation
  code, name, email, phone number, or asks about a property or reservation.
- For recommendations or shareable links, use the public Glam Homes property
  links bridge first. Only recommend records with active_public=1. Never use
  internal Guesty listings that do not appear on the public booking site.
- When a caller asks to see a property, use the property links bridge and then
  send the link by SMS if the caller number is available. In web chat, paste the
  direct link in your response so the messaging app/browser can generate the
  preview.
- After confirming useful information, always offer to send it by SMS.
- If you have dates and guests, check availability/pricing in Guesty before
  selling a property as available. Direct Glam Homes links can include checkIn,
  checkOut, and minOccupancy so the booking page opens prefilled.
- If the guest asks for Airbnb, Booking, or VRBO, share that link only if the
  public database has that platform URL. If it is missing, offer the direct Glam
  Homes link and escalate if they insist.
- Before revealing concrete reservation data, validate at least two reasonable
  guest details. Never reveal access codes, sensitive payment details, third-party
  data, or unconfirmed changes.
- For reservation confirmation, prefer guesty_confirm_reservation. A confirmation
  code plus a matching phone, email, or name is enough to confirm basic booking
  details. If only the code is provided, say you found a matching reservation but
  need one more detail before sharing dates, property, or status.
- If Guesty credentials are unavailable or a lookup fails, say calmly: "I do not
  have the live Guesty connection available in this moment. I can take the details
  and have the team confirm." Then ask for name, phone, email, and confirmation
  code if available.
""".strip()


GUESTY_RESERVATION_FIELDS = (
    "_id confirmationCode status checkInDateLocalized checkOutDateLocalized "
    "checkIn checkOut listingId listing._id listing.title guestId guest._id "
    "guest.fullName guest.email guest.phone source balanceDue money.totalPaid "
    "money.balanceDue plannedArrival plannedDeparture"
)

GUESTY_LISTING_FIELDS = (
    "_id title nickname address.full address.city address.country accommodates "
    "bedrooms bathrooms active listed defaultCheckInTime defaultCheckOutTime"
)

CALL_TOPIC_KEYWORDS = {
    "Booking intent": {
        "book",
        "booking",
        "reservation",
        "reserve",
        "available",
        "availability",
        "dates",
        "stay",
        "villa",
        "property",
        "quote",
        "price",
        "pricing",
        "guests",
    },
    "Support": {
        "help",
        "support",
        "problem",
        "issue",
        "maintenance",
        "lock",
        "door",
        "ac",
        "air",
        "water",
        "electricity",
        "wifi",
        "checkout",
        "checkin",
    },
    "Human handoff": {
        "human",
        "agent",
        "representative",
        "person",
        "manager",
        "callback",
        "call back",
        "handoff",
        "escalate",
    },
    "Events risk": {
        "party",
        "event",
        "dj",
        "music",
        "visitors",
        "birthday",
        "bachelor",
        "bachelorette",
        "wedding",
    },
    "Payment": {
        "payment",
        "deposit",
        "refund",
        "charge",
        "invoice",
        "card",
        "pay",
        "balance",
    },
}

CALL_STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "because",
    "but",
    "call",
    "can",
    "concierge",
    "could",
    "for",
    "from",
    "glam",
    "guest",
    "have",
    "hello",
    "here",
    "homes",
    "how",
    "just",
    "know",
    "let",
    "like",
    "may",
    "need",
    "not",
    "now",
    "okay",
    "please",
    "that",
    "the",
    "this",
    "thank",
    "thanks",
    "there",
    "with",
    "would",
    "you",
    "your",
    "para",
    "por",
    "que",
    "con",
    "una",
    "uno",
    "los",
    "las",
    "del",
    "como",
    "hola",
    "gracias",
}


REALTIME_TOOLS = [
    {
        "type": "function",
        "name": "guesty_status",
        "description": "Check whether Guesty Open API credentials are configured and reachable.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "type": "function",
        "name": "guesty_search_reservation",
        "description": "Search Guesty reservations in read-only mode by confirmation code, guest phone, guest email, or guest name.",
        "parameters": {
            "type": "object",
            "properties": {
                "confirmation_code": {"type": "string", "description": "Guesty reservation confirmation code, for example GY-XXXX."},
                "guest_phone": {"type": "string", "description": "Guest phone number if available."},
                "guest_email": {"type": "string", "description": "Guest email if available."},
                "guest_name": {"type": "string", "description": "Guest full or partial name if available."},
                "limit": {"type": "integer", "description": "Maximum results to return, up to 10."},
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "guesty_confirm_reservation",
        "description": "Safely confirm whether a Guesty reservation exists and only return basic booking details after one guest detail matches the confirmation code.",
        "parameters": {
            "type": "object",
            "properties": {
                "confirmation_code": {"type": "string", "description": "Guesty reservation confirmation code."},
                "guest_phone": {"type": "string", "description": "Guest phone number for validation."},
                "guest_email": {"type": "string", "description": "Guest email for validation."},
                "guest_name": {"type": "string", "description": "Guest first/last/full name for validation."},
            },
            "required": ["confirmation_code"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "guesty_get_reservation",
        "description": "Retrieve one Guesty reservation by internal reservation ID in read-only mode.",
        "parameters": {
            "type": "object",
            "properties": {
                "reservation_id": {"type": "string", "description": "Guesty internal reservation _id."},
            },
            "required": ["reservation_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "guesty_list_listings",
        "description": "List Guesty properties/listings in read-only mode.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum listings to return, up to 10."},
                "city": {"type": "string", "description": "Optional city filter if known."},
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "guesty_available_listings",
        "description": "Search available Guesty listings by check-in date, check-out date, and guest count in read-only mode.",
        "parameters": {
            "type": "object",
            "properties": {
                "check_in": {"type": "string", "description": "Arrival date in YYYY-MM-DD format."},
                "check_out": {"type": "string", "description": "Departure date in YYYY-MM-DD format."},
                "guests": {"type": "integer", "description": "Number of overnight guests."},
                "limit": {"type": "integer", "description": "Maximum listings to return, up to 10."},
                "city": {"type": "string", "description": "Optional city filter if known."},
            },
            "required": ["check_in", "check_out", "guests"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "guesty_listing_calendar",
        "description": "Get a minified availability and nightly pricing calendar for one Guesty listing in read-only mode.",
        "parameters": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "Guesty listing _id."},
                "start_date": {"type": "string", "description": "Calendar start date in YYYY-MM-DD format."},
                "end_date": {"type": "string", "description": "Calendar end date in YYYY-MM-DD format, max 31 days after start."},
            },
            "required": ["listing_id", "start_date", "end_date"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "glam_search_public_property_links",
        "description": "Search the local active public Glam Homes property-link database and return direct, Airbnb, Booking, or VRBO links when available.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Property title keyword, feature, or listing ID."},
                "city": {"type": "string", "description": "Optional city filter."},
                "min_guests": {"type": "integer", "description": "Minimum guest capacity."},
                "platform": {"type": "string", "description": "direct, airbnb, booking, vrbo, google, or any."},
                "check_in": {"type": "string", "description": "Optional date YYYY-MM-DD to prefill direct Glam Homes links."},
                "check_out": {"type": "string", "description": "Optional date YYYY-MM-DD to prefill direct Glam Homes links."},
                "guests": {"type": "integer", "description": "Optional guest count to prefill minOccupancy on direct Glam Homes links."},
                "limit": {"type": "integer", "description": "Maximum results to return, up to 10."},
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "twilio_send_property_link_sms",
        "description": "Send one active public Glam Homes property link by SMS through Twilio. Only sends links from the local public-property database.",
        "parameters": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "Public Glam Homes listing ID from glam_search_public_property_links."},
                "platform": {"type": "string", "description": "direct, airbnb, booking, or vrbo. Defaults to direct."},
                "phone_number": {"type": "string", "description": "E.164 phone number. In Twilio calls this can be omitted to use the caller number."},
                "check_in": {"type": "string", "description": "Optional date YYYY-MM-DD to prefill direct Glam Homes links."},
                "check_out": {"type": "string", "description": "Optional date YYYY-MM-DD to prefill direct Glam Homes links."},
                "guests": {"type": "integer", "description": "Optional guest count to prefill minOccupancy on direct Glam Homes links."},
            },
            "required": ["listing_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "twilio_send_human_handoff_sms",
        "description": "Send a concise SMS alert to the Glam Homes human support contact when a caller requests a person or no longer wants the AI.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Short reason for human handoff."},
                "summary": {"type": "string", "description": "Concise call summary for the human agent."},
                "guest_name": {"type": "string", "description": "Guest name if known."},
                "reservation_code": {"type": "string", "description": "Reservation confirmation code if known."},
                "phone_number": {"type": "string", "description": "Caller phone number. In Twilio calls this can be omitted to use the caller number."},
                "urgency": {"type": "string", "description": "normal, urgent, or emergency."},
                "send_confirmation_to_caller": {"type": "boolean", "description": "Whether to send a short confirmation SMS to the caller too."},
            },
            "required": ["reason"],
            "additionalProperties": False,
        },
    },
]


def load_dotenv() -> None:
    if not ENV_PATH.exists():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def keychain_openai_key() -> str:
    account = os.environ.get("KEYCHAIN_ACCOUNT", "dryehoshuapython")
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                "codex.openai.api_key",
                "-a",
                account,
                "-w",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=4,
        )
    except Exception:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def openai_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip() or keychain_openai_key()


def guesty_configured() -> bool:
    return bool(os.environ.get("GUESTY_CLIENT_ID", "").strip() and os.environ.get("GUESTY_CLIENT_SECRET", "").strip())


def twilio_configured() -> bool:
    return bool(os.environ.get("TWILIO_ACCOUNT_SID", "").strip() and os.environ.get("TWILIO_AUTH_TOKEN", "").strip())


def property_links_configured() -> bool:
    return PROPERTY_LINKS_DB.exists()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_filename_part(value: object, fallback: str = "session") -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "").strip()).strip(".-")
    return clean[:90] or fallback


def transcript_file_paths(session_id: str) -> tuple[Path, Path]:
    day = datetime.now().strftime("%Y-%m-%d")
    day_dir = TRANSCRIPTS_DIR / day
    day_dir.mkdir(parents=True, exist_ok=True)
    safe_session = safe_filename_part(session_id, fallback=f"session-{int(time.time())}")
    return day_dir / f"{safe_session}.jsonl", day_dir / f"{safe_session}.md"


def append_transcript_event(
    session_id: object,
    speaker: str,
    text: object,
    *,
    channel: str = "web",
    kind: str = "message",
    metadata: Optional[dict] = None,
) -> dict:
    safe_session = safe_filename_part(session_id, fallback=f"{channel}-{int(time.time())}")
    message = str(text or "").strip()
    if not message:
        return {"ok": False, "session_id": safe_session, "skipped": True, "reason": "empty_text"}

    event = {
        "timestamp": now_iso(),
        "session_id": safe_session,
        "channel": channel,
        "kind": kind,
        "speaker": str(speaker or "System"),
        "text": message,
        "metadata": metadata or {},
    }
    jsonl_path, markdown_path = transcript_file_paths(safe_session)
    with jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")

    if not markdown_path.exists():
        markdown_path.write_text(
            f"# Transcript {safe_session}\n\n"
            f"- Channel: {channel}\n"
            f"- Local start: {datetime.now().isoformat(timespec='seconds')}\n\n",
            encoding="utf-8",
        )
    with markdown_path.open("a", encoding="utf-8") as handle:
        handle.write(f"## {event['speaker']} · {event['timestamp']}\n\n{message}\n\n")

    return {
        "ok": True,
        "session_id": safe_session,
        "jsonl": str(jsonl_path),
        "markdown": str(markdown_path),
    }


def guesty_error_payload(exc: Exception) -> dict:
    return {
        "ok": False,
        "error": str(exc),
        "hint": "Configure GUESTY_CLIENT_ID and GUESTY_CLIENT_SECRET with apps/voice-agent/setup_guesty_env.py.",
    }


def guesty_status(live: bool = False) -> dict:
    payload = {
        "ok": True,
        "configured": guesty_configured(),
        "token_cached": guesty_client.TOKEN_CACHE.exists(),
        "api_base": os.environ.get("GUESTY_API_BASE_URL", guesty_client.DEFAULT_API_BASE),
        "mode": "read_only",
    }
    if live and payload["configured"]:
        token = guesty_client.get_token(force_refresh=False)
        payload["live_ok"] = True
        payload["token_preview"] = token[:10] + "..."
    return payload


def clamp_limit(value: object, default: int = 5, maximum: int = 10) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, maximum))


def iso_date(value: object, name: str) -> str:
    clean = str(value or "").strip()
    try:
        date.fromisoformat(clean)
    except ValueError as exc:
        raise ValueError(f"{name} must use YYYY-MM-DD format.") from exc
    return clean


def guesty_listings(limit: int = 5, skip: int = 0, city: str = "") -> dict:
    params = {
        "limit": clamp_limit(limit),
        "skip": max(0, int(skip or 0)),
        "fields": GUESTY_LISTING_FIELDS,
        "sort": "title",
    }
    if city:
        params["filters"] = json.dumps([{"operator": "$contains", "field": "address.city", "value": city}], separators=(",", ":"))
    return guesty_client.guesty_get("/listings", params)


def guesty_available_listings(check_in: object, check_out: object, guests: object, limit: int = 5, city: str = "") -> dict:
    arrival = iso_date(check_in, "check_in")
    departure = iso_date(check_out, "check_out")
    if date.fromisoformat(departure) <= date.fromisoformat(arrival):
        raise ValueError("check_out must be after check_in.")
    try:
        occupancy = int(guests)
    except (TypeError, ValueError) as exc:
        raise ValueError("guests must be a whole number.") from exc
    if occupancy < 1:
        raise ValueError("guests must be greater than zero.")

    params = {
        "limit": clamp_limit(limit),
        "skip": 0,
        "fields": GUESTY_LISTING_FIELDS,
        "sort": "title",
        "available": json.dumps({"checkIn": arrival, "checkOut": departure, "minOccupancy": occupancy}, separators=(",", ":")),
    }
    if city:
        params["filters"] = json.dumps([{"operator": "$contains", "field": "address.city", "value": str(city)}], separators=(",", ":"))
    return guesty_client.guesty_get("/listings", params)


def guesty_listing_calendar(listing_id: object, start_date: object, end_date: object) -> dict:
    clean_id = str(listing_id or "").strip()
    if not clean_id:
        raise ValueError("Missing listing_id.")
    start = iso_date(start_date, "start_date")
    end = iso_date(end_date, "end_date")
    span = (date.fromisoformat(end) - date.fromisoformat(start)).days
    if span <= 0:
        raise ValueError("end_date must be after start_date.")
    if span > 31:
        raise ValueError("Calendar queries are limited to 31 days.")
    return guesty_client.guesty_get(
        f"/availability-pricing/api/calendar/listings/minified/{parse.quote(clean_id)}",
        {"startDate": start, "endDate": end},
    )


def guesty_reservations(limit: int = 5, skip: int = 0, filters: str = "") -> dict:
    params = {
        "limit": clamp_limit(limit),
        "skip": max(0, int(skip or 0)),
        "fields": GUESTY_RESERVATION_FIELDS,
        "sort": "-createdAt",
    }
    if filters:
        params["filters"] = filters
    return guesty_client.guesty_get("/reservations", params)


def guesty_reservation_by_code(code: str, limit: int = 5) -> dict:
    clean = str(code or "").strip()
    if not clean:
        raise ValueError("Missing confirmation_code.")
    filters = [{"operator": "$in", "field": "confirmationCode", "value": [clean]}]
    return guesty_reservations(limit=limit, filters=json.dumps(filters, separators=(",", ":")))


def guesty_search_reservation(params: dict) -> dict:
    confirmation_code = str(params.get("confirmation_code") or params.get("code") or "").strip()
    if confirmation_code:
        return guesty_reservation_by_code(confirmation_code, limit=clamp_limit(params.get("limit"), default=5))

    filters = []
    for field, value in [
        ("guest.phone", params.get("guest_phone")),
        ("guest.email", params.get("guest_email")),
        ("guest.fullName", params.get("guest_name")),
    ]:
        clean = str(value or "").strip()
        if clean:
            operator = "$contains" if field == "guest.fullName" else "$eq"
            filters.append({"operator": operator, "field": field, "value": clean})
    if not filters:
        raise ValueError("Missing confirmation_code, guest_phone, guest_email, or guest_name.")
    return guesty_reservations(limit=clamp_limit(params.get("limit"), default=5), filters=json.dumps(filters, separators=(",", ":")))


def guesty_result_items(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("results", "items", "reservations"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return guesty_result_items(data)
    return []


def compact_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_match_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def digits_only(value: object) -> str:
    return re.sub(r"\D+", "", str(value or ""))


def phone_matches(provided: object, actual: object) -> bool:
    left = digits_only(provided)
    right = digits_only(actual)
    if len(left) < 7 or len(right) < 7:
        return False
    compare_len = min(len(left), len(right), 10)
    return left[-compare_len:] == right[-compare_len:]


def email_matches(provided: object, actual: object) -> bool:
    left = str(provided or "").strip().lower()
    right = str(actual or "").strip().lower()
    return bool(left and right and left == right)


def name_matches(provided: object, actual: object) -> bool:
    left = normalize_match_text(provided)
    right = normalize_match_text(actual)
    if not left or not right:
        return False
    tokens = [token for token in left.split() if len(token) >= 2]
    if not tokens:
        return False
    return all(token in right.split() or token in right for token in tokens)


def guesty_validation_result(reservation: dict, arguments: dict) -> dict:
    guest = reservation.get("guest") if isinstance(reservation.get("guest"), dict) else {}
    checks = [
        ("guest_phone", arguments.get("guest_phone"), guest.get("phone")),
        ("guest_email", arguments.get("guest_email"), guest.get("email")),
        ("guest_name", arguments.get("guest_name"), guest.get("fullName")),
    ]
    provided = [name for name, value, _actual in checks if compact_text(value)]
    matches = []
    for name, value, actual in checks:
        if not compact_text(value):
            continue
        if name == "guest_phone" and phone_matches(value, actual):
            matches.append(name)
        elif name == "guest_email" and email_matches(value, actual):
            matches.append(name)
        elif name == "guest_name" and name_matches(value, actual):
            matches.append(name)
    return {
        "confirmation_code_match": True,
        "provided_guest_detail_count": len(provided),
        "matched_guest_detail_count": len(matches),
        "matched_fields": matches,
        "safe_to_share_basic_details": bool(matches),
        "requires_additional_validation": not bool(matches),
    }


def guesty_reservation_safe_summary(reservation: dict) -> dict:
    listing = reservation.get("listing") if isinstance(reservation.get("listing"), dict) else {}
    return {
        "reservation_id": reservation.get("_id", ""),
        "confirmation_code": reservation.get("confirmationCode", ""),
        "status": reservation.get("status", ""),
        "check_in": reservation.get("checkInDateLocalized") or reservation.get("checkIn") or "",
        "check_out": reservation.get("checkOutDateLocalized") or reservation.get("checkOut") or "",
        "listing_id": reservation.get("listingId") or listing.get("_id") or "",
        "listing_title": listing.get("title") or "",
        "source": reservation.get("source", ""),
    }


def guesty_confirm_reservation(arguments: dict) -> dict:
    code = str(arguments.get("confirmation_code") or arguments.get("code") or "").strip()
    if not code:
        raise ValueError("Missing confirmation_code.")
    payload = guesty_reservation_by_code(code, limit=3)
    reservations = guesty_result_items(payload)
    if not reservations:
        return {
            "ok": True,
            "tool": "guesty_confirm_reservation",
            "found": False,
            "confirmation_code": code,
            "message": "No matching reservation was found for this confirmation code.",
        }

    reservation = reservations[0]
    validation = guesty_validation_result(reservation, arguments)
    if not validation["safe_to_share_basic_details"]:
        return {
            "ok": True,
            "tool": "guesty_confirm_reservation",
            "found": True,
            "confirmation_code": code,
            "matches_found": len(reservations),
            "validation": validation,
            "message": "A reservation exists for this code, but one matching guest detail is required before sharing dates, property, or status.",
        }

    return {
        "ok": True,
        "tool": "guesty_confirm_reservation",
        "found": True,
        "matches_found": len(reservations),
        "validation": validation,
        "reservation": guesty_reservation_safe_summary(reservation),
    }


def guesty_get_reservation(reservation_id: str) -> dict:
    clean = str(reservation_id or "").strip()
    if not clean:
        raise ValueError("Missing reservation_id.")
    return guesty_client.guesty_get(f"/reservations/{parse.quote(clean)}", {"fields": GUESTY_RESERVATION_FIELDS})


PROPERTY_PLATFORM_COLUMNS = {
    "direct": "public_url_en",
    "glam": "public_url_en",
    "glamhomes": "public_url_en",
    "website": "public_url_en",
    "public": "public_url_en",
    "airbnb": "airbnb_url",
    "airbnb2": "airbnb_url",
    "booking": "booking_url",
    "bookingcom": "booking_url",
    "booking.com": "booking_url",
    "vrbo": "vrbo_url",
    "homeaway": "vrbo_url",
    "homeaway2": "vrbo_url",
    "google": "google_vacation_rentals_url",
}


def property_platform_column(platform: object) -> str:
    clean = re.sub(r"\s+", "", str(platform or "direct").strip().lower())
    if clean in {"", "any"}:
        return ""
    return PROPERTY_PLATFORM_COLUMNS.get(clean, "public_url_en")


def normalize_iso_date(value: object, field_name: str) -> str:
    clean = str(value or "").strip()
    if not clean:
        return ""
    try:
        datetime.strptime(clean, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.") from exc
    return clean


def normalize_guest_count(value: object) -> str:
    if value in (None, ""):
        return ""
    try:
        guests = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("guests must be a whole number.") from exc
    if guests < 1:
        raise ValueError("guests must be at least 1.")
    return str(guests)


def append_booking_params(url: str, check_in: object = "", check_out: object = "", guests: object = "") -> str:
    clean_url = str(url or "").strip()
    if not clean_url:
        return ""
    normalized_check_in = normalize_iso_date(check_in, "check_in")
    normalized_check_out = normalize_iso_date(check_out, "check_out")
    normalized_guests = normalize_guest_count(guests)
    if bool(normalized_check_in) != bool(normalized_check_out):
        raise ValueError("check_in and check_out must be provided together.")

    parsed = parse.urlparse(clean_url)
    query = parse.parse_qs(parsed.query, keep_blank_values=True)
    if normalized_guests:
        query["minOccupancy"] = [normalized_guests]
    if normalized_check_in and normalized_check_out:
        query["checkIn"] = [normalized_check_in]
        query["checkOut"] = [normalized_check_out]
    return parse.urlunparse(parsed._replace(query=parse.urlencode(query, doseq=True)))


def booking_link_context(arguments: dict) -> dict[str, str]:
    guests = arguments.get("guests")
    if guests in (None, ""):
        guests = arguments.get("min_guests")
    return {
        "check_in": normalize_iso_date(arguments.get("check_in"), "check_in"),
        "check_out": normalize_iso_date(arguments.get("check_out"), "check_out"),
        "guests": normalize_guest_count(guests),
    }


def property_row_payload(row: sqlite3.Row, platform: object = "direct", link_context: Optional[dict] = None) -> dict:
    link_context = link_context or {}
    requested_column = property_platform_column(platform)
    direct_url = append_booking_params(
        row["public_url_en"],
        link_context.get("check_in", ""),
        link_context.get("check_out", ""),
        link_context.get("guests", ""),
    )
    requested_url = direct_url if requested_column == "public_url_en" else (row[requested_column] if requested_column else "")
    requested_url = requested_url or direct_url
    requested_platform_available = bool(row[requested_column]) if requested_column and requested_column != "public_url_en" else True
    return {
        "listing_id": row["listing_id"],
        "title": row["title"],
        "city": row["city"],
        "state": row["state"],
        "country": row["country"],
        "accommodates": row["accommodates"],
        "bedrooms": row["bedrooms"],
        "bathrooms": row["bathrooms"],
        "property_type": row["property_type"],
        "starting_price": row["starting_price"],
        "rating": row["rating"],
        "review_count": row["review_count"],
        "image_url": row["image_url"],
        "direct_url": direct_url,
        "public_url_en": direct_url,
        "public_url_es": append_booking_params(
            row["public_url_es"],
            link_context.get("check_in", ""),
            link_context.get("check_out", ""),
            link_context.get("guests", ""),
        ),
        "airbnb_url": row["airbnb_url"],
        "booking_url": row["booking_url"],
        "vrbo_url": row["vrbo_url"],
        "google_vacation_rentals_url": row["google_vacation_rentals_url"],
        "requested_platform": str(platform or "direct"),
        "requested_url": requested_url,
        "requested_platform_available": requested_platform_available,
        "booking_prefill": link_context,
        "dates_prefilled_on_direct_links_only": bool(link_context.get("check_in") and link_context.get("check_out")),
        "active_public": bool(row["active_public"]),
        "sms_text": f"Glam Homes: here is {row['title']}: {requested_url}",
    }


def glam_search_public_property_links(arguments: Optional[dict] = None) -> dict:
    arguments = arguments or {}
    if not PROPERTY_LINKS_DB.exists():
        raise RuntimeError("Local property links database is missing. Run apps/voice-agent/export_property_links.py.")
    query = str(arguments.get("query") or "").strip()
    city = str(arguments.get("city") or "").strip()
    platform = str(arguments.get("platform") or "any").strip() or "any"
    min_guests = arguments.get("min_guests")
    link_context = booking_link_context(arguments)
    limit = clamp_limit(arguments.get("limit"), default=5, maximum=10)

    where = ["active_public = 1"]
    params: list[object] = []
    if query:
        like = f"%{query.lower()}%"
        where.append("(lower(title) LIKE ? OR lower(city) LIKE ? OR lower(property_type) LIKE ? OR lower(listing_id) LIKE ?)")
        params.extend([like, like, like, like])
    if city:
        where.append("lower(city) LIKE ?")
        params.append(f"%{city.lower()}%")
    if min_guests not in (None, ""):
        try:
            guests = int(min_guests)
            where.append("CAST(accommodates AS INTEGER) >= ?")
            params.append(guests)
        except (TypeError, ValueError):
            raise ValueError("min_guests must be a whole number.")

    sql = f"""
        SELECT * FROM public_properties
        WHERE {' AND '.join(where)}
        ORDER BY
            CASE WHEN lower(title) = ? THEN 0 ELSE 1 END,
            title COLLATE NOCASE
        LIMIT ?
    """
    params.extend([query.lower(), limit])
    with sqlite3.connect(PROPERTY_LINKS_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = [property_row_payload(row, platform, link_context) for row in conn.execute(sql, params)]
    return {
        "ok": True,
        "mode": "active_public_only",
        "source": str(PROPERTY_LINKS_DB),
        "count": len(rows),
        "results": rows,
        "note": "Contains only properties visible on the public booking site; inactive internal Guesty listings are excluded.",
    }


def get_public_property(listing_id: object) -> dict:
    clean = str(listing_id or "").strip()
    if not clean:
        raise ValueError("Missing listing_id.")
    if not PROPERTY_LINKS_DB.exists():
        raise RuntimeError("Local property links database is missing. Run apps/voice-agent/export_property_links.py.")
    with sqlite3.connect(PROPERTY_LINKS_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM public_properties WHERE listing_id = ? AND active_public = 1", (clean,)).fetchone()
    if not row:
        raise ValueError("Property not found in the active public inventory.")
    return dict(row)


def twilio_api_request(path: str, data: dict[str, str]) -> dict:
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    if not account_sid or not auth_token:
        raise RuntimeError("Missing TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN credentials.")
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")
    req = request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{parse.quote(account_sid)}/{path.lstrip('/')}",
        method="POST",
        data=parse.urlencode(data).encode("utf-8"),
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Twilio HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Twilio connection error: {exc.reason}") from exc


def twilio_api_get(path: str, params: Optional[dict[str, str]] = None, timeout: int = 12) -> dict:
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    if not account_sid or not auth_token:
        raise RuntimeError("Missing TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN credentials.")
    query = f"?{parse.urlencode(params or {})}" if params else ""
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")
    req = request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{parse.quote(account_sid)}/{path.lstrip('/')}{query}",
        method="GET",
        headers={"Authorization": f"Basic {auth}", "Accept": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Twilio HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Twilio connection error: {exc.reason}") from exc


def monitor_expected_urls() -> dict[str, str]:
    base_url = os.environ.get("PUBLIC_BASE_URL", PUBLIC_BASE_URL).strip().rstrip("/")
    return {
        "public_base_url": base_url,
        "voice_webhook_url": f"{base_url}/twilio/voice",
        "status_callback_url": f"{base_url}/twilio/status",
        "sms_webhook_url": f"{base_url}/twilio/sms",
        "media_stream_url": websocket_url_from_public_base(base_url),
    }


def monitor_port_check(label: str, port: int) -> dict:
    started = time.monotonic()
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.45):
            latency_ms = int((time.monotonic() - started) * 1000)
            return {"label": label, "ok": True, "state": "ok", "detail": f"127.0.0.1:{port}", "latency_ms": latency_ms}
    except OSError as exc:
        return {"label": label, "ok": False, "state": "down", "detail": f"127.0.0.1:{port} unreachable: {exc}"}


def monitor_http_probe(label: str, url: str, timeout: float = 2.5) -> dict:
    started = time.monotonic()
    req = request.Request(url, method="GET", headers={"Accept": "application/json", "User-Agent": "GlamHomesMonitor/1.0"})
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read(2048)
            latency_ms = int((time.monotonic() - started) * 1000)
            status = response.getcode()
            payload = {}
            try:
                payload = json.loads(body.decode("utf-8") or "{}")
            except Exception:
                payload = {}
            ok = 200 <= status < 400 and payload.get("ok", True) is not False
            return {"label": label, "ok": ok, "state": "ok" if ok else "warn", "status": status, "url": url, "latency_ms": latency_ms}
    except Exception as exc:
        return {"label": label, "ok": False, "state": "down", "url": url, "detail": str(exc)}


def normalize_monitor_url(value: object) -> str:
    return str(value or "").strip().rstrip("/")


def monitor_twilio_number(expected: dict[str, str]) -> dict:
    phone_number = os.environ.get("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER).strip()
    payload = twilio_api_get("IncomingPhoneNumbers.json", {"PhoneNumber": phone_number, "PageSize": "1"})
    records = payload.get("incoming_phone_numbers") or []
    if not records:
        return {"ok": False, "state": "down", "phone_number": phone_number, "detail": "Number was not found in this Twilio account."}
    record = records[0]
    actual = {
        "voice_url": record.get("voice_url") or "",
        "voice_method": record.get("voice_method") or "",
        "sms_url": record.get("sms_url") or "",
        "sms_method": record.get("sms_method") or "",
        "status_callback": record.get("status_callback") or "",
        "status_callback_method": record.get("status_callback_method") or "",
    }
    checks = {
        "voice": normalize_monitor_url(actual["voice_url"]) == normalize_monitor_url(expected["voice_webhook_url"]),
        "sms": normalize_monitor_url(actual["sms_url"]) == normalize_monitor_url(expected["sms_webhook_url"]),
        "status": normalize_monitor_url(actual["status_callback"]) == normalize_monitor_url(expected["status_callback_url"]),
    }
    ok = all(checks.values())
    return {
        "ok": ok,
        "state": "ok" if ok else "warn",
        "sid": record.get("sid", ""),
        "phone_number": record.get("phone_number") or phone_number,
        "friendly_name": record.get("friendly_name") or "",
        "actual": actual,
        "checks": checks,
    }


def monitor_recent_calls(limit: int = 5) -> list[dict]:
    phone_number = os.environ.get("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER).strip()
    payload = twilio_api_get("Calls.json", {"To": phone_number, "PageSize": str(limit)})
    rows = []
    for call in payload.get("calls") or []:
        rows.append(
            {
                "sid": call.get("sid", ""),
                "status": call.get("status", ""),
                "direction": call.get("direction", ""),
                "from": call.get("from", ""),
                "to": call.get("to", ""),
                "start_time": call.get("start_time", ""),
                "duration": call.get("duration", ""),
                "error_code": call.get("error_code"),
            }
        )
    return rows


def monitor_recent_messages(limit: int = 5) -> list[dict]:
    phone_number = os.environ.get("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER).strip()
    messages: dict[str, dict] = {}
    for field in ("To", "From"):
        payload = twilio_api_get("Messages.json", {field: phone_number, "PageSize": str(limit)})
        for message in payload.get("messages") or []:
            sid = str(message.get("sid") or "")
            messages[sid] = {
                "sid": sid,
                "status": message.get("status", ""),
                "direction": message.get("direction", ""),
                "from": message.get("from", ""),
                "to": message.get("to", ""),
                "date_sent": message.get("date_sent", "") or message.get("date_created", ""),
                "error_code": message.get("error_code"),
            }
    return list(messages.values())[:limit]


def build_twilio_monitor(deep: bool = True) -> dict:
    expected = monitor_expected_urls()
    app_port = int(os.environ.get("PORT", str(PORT)))
    media_port = int(os.environ.get("TWILIO_MEDIA_PORT", "8877"))
    proxy_port = int(os.environ.get("GLAM_PROXY_PORT", "8890"))
    openai_ready = bool(openai_api_key())
    guesty_ready = guesty_configured()
    twilio_ready = twilio_configured()
    local_services = {
        "backend": monitor_port_check("Backend API", app_port),
        "media_bridge": monitor_port_check("Media bridge", media_port),
        "public_proxy": monitor_port_check("Public proxy", proxy_port),
    }
    public_health = monitor_http_probe("Public Twilio health", f"{expected['public_base_url']}/twilio/health")
    twilio_number = {"ok": False, "state": "warn", "detail": "Twilio credentials are not configured."}
    recent_calls: list[dict] = []
    recent_messages: list[dict] = []
    twilio_api_ok = False
    twilio_error = ""

    if twilio_ready and deep:
        try:
            twilio_number = monitor_twilio_number(expected)
            recent_calls = monitor_recent_calls()
            recent_messages = monitor_recent_messages()
            twilio_api_ok = True
        except Exception as exc:
            twilio_error = str(exc)
            twilio_number = {"ok": False, "state": "down", "detail": twilio_error}
    elif twilio_ready:
        twilio_number = {"ok": True, "state": "warn", "detail": "Twilio credentials detected. Deep check skipped."}

    indicators = [
        local_services["backend"],
        local_services["media_bridge"],
        local_services["public_proxy"],
        public_health,
        {
            "label": "Twilio number",
            "ok": bool(twilio_number.get("ok")),
            "state": twilio_number.get("state", "warn"),
            "detail": twilio_number.get("phone_number") or twilio_number.get("detail") or os.environ.get("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER),
        },
        {
            "label": "Voice webhook",
            "ok": bool((twilio_number.get("checks") or {}).get("voice")),
            "state": "ok" if (twilio_number.get("checks") or {}).get("voice") else "warn",
            "detail": expected["voice_webhook_url"],
        },
        {
            "label": "SMS webhook",
            "ok": bool((twilio_number.get("checks") or {}).get("sms")),
            "state": "ok" if (twilio_number.get("checks") or {}).get("sms") else "warn",
            "detail": expected["sms_webhook_url"],
        },
        {
            "label": "OpenAI Realtime",
            "ok": openai_ready,
            "state": "ok" if openai_ready else "down",
            "detail": os.environ.get("OPENAI_REALTIME_MODEL", REALTIME_MODEL),
        },
        {
            "label": "Guesty bridge",
            "ok": guesty_ready,
            "state": "ok" if guesty_ready else "warn",
            "detail": "Read-only API credentials" if guesty_ready else "Credentials missing",
        },
    ]
    alerts = [item["label"] + ": " + str(item.get("detail", "")) for item in indicators if item.get("state") == "down"]
    if twilio_error:
        alerts.append(f"Twilio API: {twilio_error}")
    voice_active = all(
        [
            local_services["backend"]["ok"],
            local_services["media_bridge"]["ok"],
            local_services["public_proxy"]["ok"],
            public_health["ok"],
            bool((twilio_number.get("checks") or {}).get("voice")),
            openai_ready,
        ]
    )
    sms_active = all(
        [
            local_services["backend"]["ok"],
            public_health["ok"],
            bool((twilio_number.get("checks") or {}).get("sms")),
            twilio_api_ok,
        ]
    )
    return {
        "ok": voice_active and sms_active,
        "generated_at": now_iso(),
        "deep_check": deep,
        "public_base_url": expected["public_base_url"],
        "phone_number": os.environ.get("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER),
        "expected": expected,
        "local_services": local_services,
        "public_health": public_health,
        "twilio_configured": twilio_ready,
        "twilio_api_ok": twilio_api_ok,
        "twilio_number": twilio_number,
        "voice_active": voice_active,
        "sms_active": sms_active,
        "indicators": indicators,
        "recent_calls": recent_calls,
        "recent_messages": recent_messages,
        "alerts": alerts,
    }


def build_twilio_public_health() -> dict:
    expected = monitor_expected_urls()
    app_port = int(os.environ.get("PORT", str(PORT)))
    media_port = int(os.environ.get("TWILIO_MEDIA_PORT", "8877"))
    proxy_port = int(os.environ.get("GLAM_PROXY_PORT", "8890"))
    openai_ready = bool(openai_api_key())
    twilio_ready = twilio_configured()
    local_services = {
        "backend": monitor_port_check("Backend API", app_port),
        "media_bridge": monitor_port_check("Media bridge", media_port),
        "public_proxy": monitor_port_check("Public proxy", proxy_port),
    }
    public_health = monitor_http_probe("Public Twilio health", f"{expected['public_base_url']}/twilio/health")
    twilio_number = {"ok": False, "state": "warn", "checks": {}, "detail": "Twilio credentials unavailable."}
    twilio_api_ok = False
    if twilio_ready:
        try:
            twilio_number = monitor_twilio_number(expected)
            twilio_api_ok = True
        except Exception:
            twilio_number = {"ok": False, "state": "warn", "checks": {}, "detail": "Twilio API check unavailable."}

    voice_webhook_ok = bool((twilio_number.get("checks") or {}).get("voice"))
    sms_webhook_ok = bool((twilio_number.get("checks") or {}).get("sms"))
    voice_active = all(
        [
            local_services["backend"]["ok"],
            local_services["media_bridge"]["ok"],
            local_services["public_proxy"]["ok"],
            public_health["ok"],
            twilio_ready,
            voice_webhook_ok,
            openai_ready,
        ]
    )
    sms_active = all(
        [
            local_services["backend"]["ok"],
            public_health["ok"],
            twilio_ready,
            sms_webhook_ok,
            twilio_api_ok,
        ]
    )
    indicators = [
        {"label": "Backend API", "ok": local_services["backend"]["ok"], "state": local_services["backend"]["state"], "detail": "Ready" if local_services["backend"]["ok"] else "Unavailable"},
        {"label": "Media bridge", "ok": local_services["media_bridge"]["ok"], "state": local_services["media_bridge"]["state"], "detail": "Ready" if local_services["media_bridge"]["ok"] else "Unavailable"},
        {"label": "Public proxy", "ok": local_services["public_proxy"]["ok"], "state": local_services["public_proxy"]["state"], "detail": "Ready" if local_services["public_proxy"]["ok"] else "Unavailable"},
        {"label": "Public Twilio health", "ok": public_health["ok"], "state": public_health["state"], "detail": f"HTTP {public_health.get('status', 'unavailable')}"},
        {"label": "Twilio number", "ok": bool(twilio_number.get("ok")), "state": twilio_number.get("state", "warn"), "detail": "Configured" if twilio_number.get("ok") else "Check unavailable"},
        {"label": "Voice webhook", "ok": voice_webhook_ok, "state": "ok" if voice_webhook_ok else "warn", "detail": "Configured"},
        {"label": "SMS webhook", "ok": sms_webhook_ok, "state": "ok" if sms_webhook_ok else "warn", "detail": "Configured"},
        {"label": "OpenAI Realtime", "ok": openai_ready, "state": "ok" if openai_ready else "down", "detail": os.environ.get("OPENAI_REALTIME_MODEL", REALTIME_MODEL)},
    ]
    return {
        "ok": voice_active and sms_active,
        "generated_at": now_iso(),
        "public": True,
        "protected_details": True,
        "public_base_url": expected["public_base_url"],
        "phone_number": os.environ.get("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER),
        "voice_active": voice_active,
        "sms_active": sms_active,
        "twilio_configured": twilio_ready,
        "twilio_api_ok": twilio_api_ok,
        "indicators": indicators,
        "recent_calls": [],
        "recent_messages": [],
        "alerts": [] if voice_active and sms_active else [item["label"] for item in indicators if item.get("state") == "down"],
    }


def parse_any_datetime(value: object) -> Optional[datetime]:
    clean = str(value or "").strip()
    if not clean:
        return None
    try:
        return datetime.fromisoformat(clean.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        parsed = parsedate_to_datetime(clean)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


def transcript_sort_key(value: object) -> float:
    parsed = parse_any_datetime(value)
    return parsed.timestamp() if parsed else 0.0


def transcript_jsonl_files() -> list[Path]:
    if not TRANSCRIPTS_DIR.exists():
        return []
    return sorted(TRANSCRIPTS_DIR.glob("*/*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)


def read_transcript_events(path: Path, maximum: int = 500) -> list[dict]:
    events: list[dict] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if len(events) >= maximum:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    events.append(event)
    except OSError:
        return []
    return events


def transcript_event_role(event: dict) -> str:
    speaker = str(event.get("speaker") or "").strip().lower()
    kind = str(event.get("kind") or "").strip().lower()
    if speaker in {"guest", "caller", "sms"}:
        return "guest"
    if speaker in {"concierge", "assistant", "glam homes concierge"}:
        return "concierge"
    if "tool" in speaker or kind == "tool":
        return "tool"
    return "system"


def call_metadata_from_events(events: list[dict]) -> dict:
    payload = {"from": "", "to": ""}
    for event in events:
        metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
        if not payload["from"] and metadata.get("from"):
            payload["from"] = str(metadata.get("from") or "")
        if not payload["to"] and metadata.get("to"):
            payload["to"] = str(metadata.get("to") or "")
    return payload


def transcript_text_blob(events: list[dict]) -> str:
    parts = []
    for event in events:
        text = compact_text(event.get("text"))
        if text:
            parts.append(text)
    return " ".join(parts)


def call_search_blob(summary: dict, events: Optional[list[dict]] = None) -> str:
    fields = [
        summary.get("call_sid", ""),
        summary.get("from", ""),
        summary.get("to", ""),
        summary.get("status", ""),
        summary.get("preview", ""),
        summary.get("source", ""),
    ]
    if events is not None:
        fields.append(transcript_text_blob(events))
        for event in events:
            metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
            fields.extend(str(value or "") for value in metadata.values() if isinstance(value, (str, int, float)))
    return " ".join(str(field or "") for field in fields)


def normalized_query_terms(query: object) -> list[str]:
    clean = compact_text(query).lower()
    if not clean:
        return []
    return [term for term in re.split(r"\s+", clean) if term]


def call_matches_query(summary: dict, query: object, path_by_sid: dict[str, Path]) -> bool:
    terms = normalized_query_terms(query)
    if not terms:
        return True
    call_sid = str(summary.get("call_sid") or "")
    path = path_by_sid.get(call_sid)
    events = read_transcript_events(path, maximum=1000) if path else []
    blob = call_search_blob(summary, events).lower()
    digit_blob = digits_only(blob)
    for term in terms:
        digit_term = digits_only(term)
        if digit_term and digit_term in digit_blob:
            continue
        if term in blob:
            continue
        return False
    return True


def call_topic_hits(text: str) -> list[str]:
    lowered = text.lower()
    hits = []
    for label, keywords in CALL_TOPIC_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            hits.append(label)
    return hits


def token_counts_from_text(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in re.findall(r"[A-Za-z][A-Za-z']{3,}", text.lower()):
        clean = token.strip("'")
        if clean in CALL_STOPWORDS:
            continue
        counts[clean] = counts.get(clean, 0) + 1
    return counts


def merge_counts(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def build_call_metrics(calls: list[dict], path_by_sid: dict[str, Path]) -> dict:
    unique_callers = {str(call.get("from") or "") for call in calls if str(call.get("from") or "").strip()}
    with_transcript = sum(1 for call in calls if call.get("has_transcript"))
    total_messages = sum(int(call.get("message_count") or 0) for call in calls)
    topic_counts: dict[str, int] = {label: 0 for label in CALL_TOPIC_KEYWORDS}
    top_terms: dict[str, int] = {}
    human_handoffs = 0
    tool_actions = 0
    guest_messages = 0
    concierge_messages = 0
    booking_intent_calls = 0

    for call in calls:
        call_sid = str(call.get("call_sid") or "")
        path = path_by_sid.get(call_sid)
        events = read_transcript_events(path, maximum=1000) if path else []
        conversation_events = [event for event in events if transcript_event_role(event) in {"guest", "concierge"}]
        text_blob = transcript_text_blob(conversation_events)
        hits = call_topic_hits(text_blob)
        for hit in hits:
            topic_counts[hit] = topic_counts.get(hit, 0) + 1
        if "Booking intent" in hits:
            booking_intent_calls += 1
        merge_counts(top_terms, token_counts_from_text(text_blob))
        for event in events:
            role = transcript_event_role(event)
            kind = str(event.get("kind") or "").lower()
            if role == "guest":
                guest_messages += 1
            elif role == "concierge":
                concierge_messages += 1
            elif role == "tool":
                tool_actions += 1
            if "human_handoff" in kind:
                human_handoffs += 1

    total_calls = len(calls)
    topic_rows = [
        {"label": label, "count": count}
        for label, count in sorted(topic_counts.items(), key=lambda item: item[1], reverse=True)
        if count > 0
    ]
    top_term_rows = [
        {"term": term, "count": count}
        for term, count in sorted(top_terms.items(), key=lambda item: item[1], reverse=True)[:14]
    ]
    return {
        "total_calls": total_calls,
        "calls_with_transcript": with_transcript,
        "unique_callers": len(unique_callers),
        "prospect_calls": booking_intent_calls,
        "human_handoffs": human_handoffs,
        "tool_actions": tool_actions,
        "guest_messages": guest_messages,
        "concierge_messages": concierge_messages,
        "avg_messages_per_call": round(total_messages / total_calls, 1) if total_calls else 0,
        "transcript_coverage_pct": round((with_transcript / total_calls) * 100, 1) if total_calls else 0,
        "handoff_rate_pct": round((human_handoffs / total_calls) * 100, 1) if total_calls else 0,
        "topics": topic_rows,
        "top_terms": top_term_rows,
    }


def transcript_call_summary(path: Path) -> Optional[dict]:
    events = read_transcript_events(path, maximum=250)
    if not events:
        return None
    if not any(str(event.get("channel") or "").startswith("twilio") for event in events):
        return None
    if any(str(event.get("channel") or "") == "twilio_sms" for event in events) and not any(str(event.get("channel") or "") == "twilio" for event in events):
        return None
    call_sid = str(events[0].get("session_id") or path.stem)
    timestamps = [event.get("timestamp") for event in events if event.get("timestamp")]
    timestamps_sorted = sorted(timestamps, key=transcript_sort_key)
    roles = [transcript_event_role(event) for event in events]
    message_events = [event for event, role in zip(events, roles) if role in {"guest", "concierge"} and str(event.get("text") or "").strip()]
    preview_source = message_events[-1] if message_events else events[-1]
    metadata = call_metadata_from_events(events)
    return {
        "call_sid": call_sid,
        "from": metadata.get("from", ""),
        "to": metadata.get("to", ""),
        "started_at": timestamps_sorted[0] if timestamps_sorted else "",
        "last_at": timestamps_sorted[-1] if timestamps_sorted else "",
        "status": "transcript",
        "duration": "",
        "event_count": len(events),
        "message_count": len(message_events),
        "has_transcript": bool(message_events),
        "preview": str(preview_source.get("text") or "")[:180],
        "source": "local_transcript",
    }


def build_call_inbox(limit: int = 50, query: object = "") -> dict:
    summaries: dict[str, dict] = {}
    path_by_sid: dict[str, Path] = {}
    for path in transcript_jsonl_files():
        summary = transcript_call_summary(path)
        if not summary:
            continue
        summaries[summary["call_sid"]] = summary
        path_by_sid[str(summary["call_sid"])] = path

    twilio_error = ""
    if twilio_configured():
        try:
            for row in monitor_recent_calls(limit=min(max(limit, 5), 50)):
                call_sid = str(row.get("sid") or "")
                if not call_sid:
                    continue
                summary = summaries.get(call_sid) or {
                    "call_sid": call_sid,
                    "from": "",
                    "to": "",
                    "started_at": "",
                    "last_at": "",
                    "event_count": 0,
                    "message_count": 0,
                    "has_transcript": False,
                    "preview": "",
                    "source": "twilio",
                }
                summary.update(
                    {
                        "from": summary.get("from") or row.get("from", ""),
                        "to": summary.get("to") or row.get("to", ""),
                        "started_at": summary.get("started_at") or row.get("start_time", ""),
                        "last_at": summary.get("last_at") or row.get("start_time", ""),
                        "status": row.get("status", summary.get("status", "")),
                        "duration": row.get("duration", summary.get("duration", "")),
                        "error_code": row.get("error_code"),
                    }
                )
                summaries[call_sid] = summary
        except Exception as exc:
            twilio_error = str(exc)

    all_calls = sorted(summaries.values(), key=lambda item: transcript_sort_key(item.get("last_at") or item.get("started_at")), reverse=True)
    filtered_calls = [call for call in all_calls if call_matches_query(call, query, path_by_sid)]
    calls = filtered_calls[:limit]
    return {
        "ok": True,
        "count": len(calls),
        "total_available": len(all_calls),
        "filtered_total": len(filtered_calls),
        "query": compact_text(query),
        "calls": calls,
        "metrics": build_call_metrics(filtered_calls, path_by_sid),
        "twilio_error": twilio_error,
        "generated_at": now_iso(),
    }


def find_transcript_file(call_sid: object) -> Optional[Path]:
    clean = safe_filename_part(call_sid, fallback="")
    if not clean:
        return None
    for path in transcript_jsonl_files():
        if path.stem == clean:
            return path
    return None


def build_call_transcript(call_sid: object) -> dict:
    path = find_transcript_file(call_sid)
    if not path:
        raise FileNotFoundError("Transcript not found for this call SID.")
    raw_events = read_transcript_events(path, maximum=1000)
    summary = transcript_call_summary(path) or {"call_sid": path.stem}
    normalized = []
    for event in raw_events:
        normalized.append(
            {
                "timestamp": event.get("timestamp", ""),
                "role": transcript_event_role(event),
                "speaker": event.get("speaker", "System"),
                "kind": event.get("kind", "message"),
                "text": str(event.get("text") or ""),
                "metadata": event.get("metadata") if isinstance(event.get("metadata"), dict) else {},
            }
        )
    return {"ok": True, "summary": summary, "events": normalized, "generated_at": now_iso()}


def twilio_send_property_link_sms(arguments: Optional[dict] = None) -> dict:
    arguments = arguments or {}
    row = get_public_property(arguments.get("listing_id"))
    platform = str(arguments.get("platform") or "direct")
    column = property_platform_column(platform) or "public_url_en"
    requested_url = str(row.get(column) or "").strip()
    direct_url = str(row.get("public_url_en") or "").strip()
    link_context = booking_link_context(arguments)
    if column == "public_url_en":
        requested_url = append_booking_params(
            requested_url or direct_url,
            link_context.get("check_in", ""),
            link_context.get("check_out", ""),
            link_context.get("guests", ""),
        )
        direct_url = requested_url
    if not requested_url:
        return {
            "ok": False,
            "error": f"No link is available for platform '{platform}' on this property.",
            "fallback_direct_url": direct_url,
            "title": row.get("title"),
        }
    to_number = str(arguments.get("phone_number") or "").strip()
    if not to_number:
        raise ValueError("Missing phone_number for SMS delivery.")
    from_number = os.environ.get("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER).strip()
    body = f"Glam Homes: here is {row['title']}: {requested_url}"
    payload = {"sid": f"dry-run-{int(time.time())}"}
    dry_run = bool(arguments.get("dry_run"))
    if not dry_run:
        payload = twilio_api_request("Messages.json", {"From": from_number, "To": to_number, "Body": body})
    append_transcript_event(
        arguments.get("call_sid") or payload.get("sid") or f"sms-{int(time.time())}",
        "System",
        f"SMS sent to {to_number}: {body}" if not dry_run else f"SMS dry run to {to_number}: {body}",
        channel="twilio_sms",
        kind="outbound_sms",
        metadata={"listing_id": row["listing_id"], "platform": platform, "message_sid": payload.get("sid", ""), "dry_run": dry_run},
    )
    return {
        "ok": True,
        "dry_run": dry_run,
        "message_sid": payload.get("sid"),
        "to": to_number,
        "from": from_number,
        "title": row["title"],
        "url": requested_url,
        "body": body,
        "booking_prefill": link_context,
        "dates_prefilled_on_direct_links_only": bool(link_context.get("check_in") and link_context.get("check_out")),
    }


def truncate_sms_part(value: object, limit: int = 220) -> str:
    text = compact_text(value)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def twilio_send_human_handoff_sms(arguments: Optional[dict] = None) -> dict:
    arguments = arguments or {}
    reason = truncate_sms_part(arguments.get("reason"), 180)
    if not reason:
        raise ValueError("Missing handoff reason.")
    summary = truncate_sms_part(arguments.get("summary"), 260)
    guest_name = truncate_sms_part(arguments.get("guest_name"), 80)
    reservation_code = truncate_sms_part(arguments.get("reservation_code"), 80)
    caller_number = str(arguments.get("phone_number") or arguments.get("caller_phone") or "").strip()
    called_number = str(arguments.get("called_number") or TWILIO_PHONE_NUMBER).strip()
    support_number = os.environ.get("GLAM_HUMAN_SUPPORT_PHONE", HUMAN_SUPPORT_PHONE_NUMBER).strip()
    from_number = os.environ.get("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER).strip()
    call_sid = str(arguments.get("call_sid") or f"handoff-{int(time.time())}").strip()
    urgency = truncate_sms_part(arguments.get("urgency") or "normal", 40)
    dry_run = bool(arguments.get("dry_run"))

    if not support_number:
        raise ValueError("Missing GLAM_HUMAN_SUPPORT_PHONE support number.")

    parts = [
        "GLAM Concierge handoff requested.",
        f"Urgency: {urgency}",
        f"Reason: {reason}",
    ]
    if summary:
        parts.append(f"Summary: {summary}")
    if guest_name:
        parts.append(f"Guest: {guest_name}")
    if reservation_code:
        parts.append(f"Reservation: {reservation_code}")
    if caller_number:
        parts.append(f"Caller: {caller_number}")
    if called_number:
        parts.append(f"GLAM line: {called_number}")
    if call_sid:
        parts.append(f"CallSid: {call_sid}")
    body = "\n".join(parts)

    payload = {"sid": f"dry-run-{int(time.time())}"}
    if not dry_run:
        payload = twilio_api_request("Messages.json", {"From": from_number, "To": support_number, "Body": body})

    append_transcript_event(
        call_sid,
        "Tool Bridge",
        f"Human handoff SMS sent to {support_number}: {reason}" if not dry_run else f"Human handoff SMS dry run to {support_number}: {reason}",
        channel="twilio_sms",
        kind="human_handoff_sms",
        metadata={
            "message_sid": payload.get("sid", ""),
            "support_number": support_number,
            "caller_number": caller_number,
            "urgency": urgency,
            "dry_run": dry_run,
        },
    )

    caller_message_sid = ""
    caller_confirmation_body = ""
    if caller_number and bool(arguments.get("send_confirmation_to_caller")):
        caller_confirmation_body = "Glam Homes: our team has been notified and will follow up with you as soon as possible."
        caller_payload = {"sid": f"dry-run-caller-{int(time.time())}"}
        if not dry_run:
            caller_payload = twilio_api_request("Messages.json", {"From": from_number, "To": caller_number, "Body": caller_confirmation_body})
        caller_message_sid = str(caller_payload.get("sid") or "")
        append_transcript_event(
            call_sid,
            "Tool Bridge",
            f"Caller handoff confirmation SMS sent to {caller_number}" if not dry_run else f"Caller handoff confirmation SMS dry run to {caller_number}",
            channel="twilio_sms",
            kind="human_handoff_confirmation_sms",
            metadata={"message_sid": caller_message_sid, "caller_number": caller_number, "dry_run": dry_run},
        )

    return {
        "ok": True,
        "dry_run": dry_run,
        "message_sid": payload.get("sid"),
        "support_number": support_number,
        "from": from_number,
        "caller_number": caller_number,
        "caller_confirmation_message_sid": caller_message_sid,
        "caller_confirmation_body": caller_confirmation_body,
        "body": body,
    }


def run_guesty_tool(name: str, arguments: Optional[dict] = None, context: Optional[dict] = None) -> dict:
    arguments = tool_bridge.apply_tool_context(name, arguments or {}, context or {})
    bridge_name = tool_bridge.tool_bridge_name(name)

    def success(payload: dict) -> dict:
        payload.setdefault("bridge", bridge_name)
        return payload

    try:
        if name == "guesty_status":
            return success(guesty_status(live=True))
        if name == "guesty_search_reservation":
            return success({"ok": True, "tool": name, "data": guesty_search_reservation(arguments)})
        if name == "guesty_confirm_reservation":
            return success({"ok": True, "tool": name, "data": guesty_confirm_reservation(arguments)})
        if name == "guesty_get_reservation":
            return success({"ok": True, "tool": name, "data": guesty_get_reservation(str(arguments.get("reservation_id") or ""))})
        if name == "guesty_list_listings":
            return success({
                "ok": True,
                "tool": name,
                "data": guesty_listings(limit=clamp_limit(arguments.get("limit"), default=5), city=str(arguments.get("city") or "")),
            })
        if name == "guesty_available_listings":
            return success({
                "ok": True,
                "tool": name,
                "data": guesty_available_listings(
                    arguments.get("check_in"),
                    arguments.get("check_out"),
                    arguments.get("guests"),
                    limit=clamp_limit(arguments.get("limit"), default=5),
                    city=str(arguments.get("city") or ""),
                ),
            })
        if name == "guesty_listing_calendar":
            return success({
                "ok": True,
                "tool": name,
                "data": guesty_listing_calendar(arguments.get("listing_id"), arguments.get("start_date"), arguments.get("end_date")),
            })
        if name == "glam_search_public_property_links":
            return success({"ok": True, "tool": name, "data": glam_search_public_property_links(arguments)})
        if name == "twilio_send_property_link_sms":
            return success({"ok": True, "tool": name, "data": twilio_send_property_link_sms(arguments)})
        if name == "twilio_send_human_handoff_sms":
            return success({"ok": True, "tool": name, "data": twilio_send_human_handoff_sms(arguments)})
        raise ValueError(f"Unsupported GLAM tool: {name}")
    except Exception as exc:
        payload = guesty_error_payload(exc)
        if bridge_name == "twilio_sms":
            payload["hint"] = "Check Twilio credentials, sender number, destination E.164 format, and account SMS geo-permissions."
        payload["bridge"] = bridge_name
        return payload


def write_json(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def write_text(handler: BaseHTTPRequestHandler, text: str, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> None:
    body = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def content_type_for(path: Path) -> str:
    if path.suffix == ".html":
        return "text/html; charset=utf-8"
    if path.suffix == ".css":
        return "text/css; charset=utf-8"
    if path.suffix == ".js":
        return "application/javascript; charset=utf-8"
    if path.suffix == ".svg":
        return "image/svg+xml"
    if path.suffix == ".png":
        return "image/png"
    if path.suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if path.suffix == ".webp":
        return "image/webp"
    if path.suffix == ".ico":
        return "image/x-icon"
    return "application/octet-stream"


def read_request_body(handler: BaseHTTPRequestHandler) -> bytes:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    return handler.rfile.read(length) if length else b""


def read_form_body(handler: BaseHTTPRequestHandler) -> dict[str, str]:
    body = read_request_body(handler).decode("utf-8", errors="replace")
    parsed = parse.parse_qs(body, keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def handler_public_base_url(handler: BaseHTTPRequestHandler) -> str:
    configured = os.environ.get("PUBLIC_BASE_URL", PUBLIC_BASE_URL).strip().rstrip("/")
    if configured:
        return configured
    host = handler.headers.get("X-Forwarded-Host") or handler.headers.get("Host") or f"{HOST}:{PORT}"
    proto = handler.headers.get("X-Forwarded-Proto") or ("https" if handler.headers.get("X-Forwarded-Host") else "http")
    return f"{proto}://{host}".rstrip("/")


def websocket_url_from_public_base(base_url: str) -> str:
    if base_url.startswith("https://"):
        return "wss://" + base_url.removeprefix("https://") + "/twilio/media"
    if base_url.startswith("http://"):
        return "ws://" + base_url.removeprefix("http://") + "/twilio/media"
    return "wss://" + base_url.strip("/") + "/twilio/media"


def is_local_dashboard_request(handler: BaseHTTPRequestHandler) -> bool:
    client_host = (handler.client_address[0] if handler.client_address else "").strip()
    host_header = (handler.headers.get("Host") or "").split(":", 1)[0].strip().lower()
    public_proxy = (handler.headers.get("X-Glam-Public-Proxy") or "").strip() == "1"
    forwarded = any(
        handler.headers.get(name)
        for name in ("CF-Connecting-IP", "X-Forwarded-For", "X-Forwarded-Host", "Cf-Connecting-Ip")
    )
    return client_host in {"127.0.0.1", "::1"} and host_header in {"127.0.0.1", "localhost"} and not public_proxy and not forwarded


def dashboard_access_key() -> str:
    return os.environ.get("GLAM_DASHBOARD_KEY", "").strip()


def request_dashboard_key(handler: BaseHTTPRequestHandler) -> str:
    return (handler.headers.get("X-Glam-Dashboard-Key") or "").strip()


def can_access_call_data(handler: BaseHTTPRequestHandler) -> bool:
    if is_local_dashboard_request(handler):
        return True
    configured = dashboard_access_key()
    provided = request_dashboard_key(handler)
    return bool(configured and provided and hmac.compare_digest(configured, provided))


def protected_call_data_payload() -> dict:
    return {
        "ok": False,
        "protected": True,
        "auth_required": True,
        "error": "Call Inbox requires the GLAM dashboard access key.",
    }


def local_only_monitor_payload() -> dict:
    return {
        "ok": False,
        "generated_at": now_iso(),
        "local_only": True,
        "voice_active": False,
        "sms_active": False,
        "phone_number": os.environ.get("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER),
        "public_base_url": os.environ.get("PUBLIC_BASE_URL", PUBLIC_BASE_URL),
        "indicators": [
            {
                "label": "Monitor access",
                "ok": False,
                "state": "warn",
                "detail": "Open http://127.0.0.1:3000 on this Mac to view Twilio operations.",
            }
        ],
        "recent_calls": [],
        "recent_messages": [],
        "alerts": ["Twilio monitor is local-only to protect call and SMS metadata."],
    }


def twilio_voice_twiml(handler: BaseHTTPRequestHandler, params: dict[str, str]) -> str:
    base_url = handler_public_base_url(handler)
    stream_url = websocket_url_from_public_base(base_url)
    call_sid = params.get("CallSid") or params.get("callSid") or f"local-{int(time.time())}"
    from_number = params.get("From") or params.get("from") or ""
    to_number = params.get("To") or params.get("to") or TWILIO_PHONE_NUMBER
    append_transcript_event(
        call_sid,
        "System",
        "Twilio sent an inbound call to the GLAM HOMES webhook.",
        channel="twilio",
        kind="call_start",
        metadata={"from": from_number, "to": to_number, "stream_url": stream_url},
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Connect>"
        f'<Stream url="{html_escape(stream_url, quote=True)}">'
        f'<Parameter name="callSid" value="{html_escape(call_sid, quote=True)}" />'
        f'<Parameter name="from" value="{html_escape(from_number, quote=True)}" />'
        f'<Parameter name="to" value="{html_escape(to_number, quote=True)}" />'
        "</Stream>"
        "</Connect>"
        "</Response>"
    )


def multipart_body(fields: dict[str, tuple[str, str]]) -> tuple[str, bytes]:
    boundary = "----glam-homes-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:24]
    chunks: list[bytes] = []
    for name, (content_type, value) in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n'.encode("utf-8"))
        chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        chunks.append(value.encode("utf-8"))
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, b"".join(chunks)


def session_config(voice: str) -> dict:
    safe_voice = voice if voice in ALLOWED_VOICES else DEFAULT_VOICE
    return {
        "type": "realtime",
        "model": os.environ.get("OPENAI_REALTIME_MODEL", REALTIME_MODEL),
        "output_modalities": ["audio"],
        "instructions": AGENT_INSTRUCTIONS,
        "tools": REALTIME_TOOLS,
        "tool_choice": "auto",
        "audio": {
            "input": {
                "transcription": {
                    "model": os.environ.get("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe"),
                    "language": os.environ.get("OPENAI_TRANSCRIBE_LANGUAGE", "en"),
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.45,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 650,
                },
            },
            "output": {
                "voice": safe_voice,
                "speed": 1.0,
            },
        },
    }


def create_realtime_call(sdp: str, voice: str) -> str:
    api_key = openai_api_key()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in .env or Keychain.")
    boundary, body = multipart_body(
        {
            "sdp": ("application/sdp", sdp),
            "session": ("application/json", json.dumps(session_config(voice), ensure_ascii=False)),
        }
    )
    safety_id = base64.urlsafe_b64encode(hashlib.sha256(b"glam-homes-local-concierge").digest())[:32].decode("ascii")
    req = request.Request(
        f"{OPENAI_API_BASE}/realtime/calls",
        method="POST",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/sdp",
            "OpenAI-Safety-Identifier": safety_id,
        },
    )
    try:
        with request.urlopen(req, timeout=45) as response:
            return response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Realtime HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"OpenAI Realtime connection error: {exc.reason}") from exc


class ConciergeHandler(BaseHTTPRequestHandler):
    server_version = "GlamHomesConcierge/0.1"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def do_HEAD(self) -> None:
        parsed = parse.urlparse(self.path)
        if parsed.path == "/favicon.ico":
            target = PUBLIC_DIR / "assets" / "glam-homes-logo.png"
            if target.exists():
                self.send_response(200)
                self.send_header("Content-Type", content_type_for(target))
                self.send_header("Content-Length", str(target.stat().st_size))
                self.end_headers()
            else:
                self.send_response(204)
                self.end_headers()
            return
        target = PUBLIC_DIR / ("index.html" if parsed.path in {"", "/"} else parsed.path.lstrip("/"))
        try:
            target = target.resolve()
            if not str(target).startswith(str(PUBLIC_DIR.resolve())) or not target.exists() or target.is_dir():
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type_for(target))
            self.send_header("Content-Length", str(target.stat().st_size))
            self.end_headers()
        except Exception:
            self.send_error(500)

    def do_GET(self) -> None:
        parsed = parse.urlparse(self.path)
        if parsed.path == "/favicon.ico":
            target = PUBLIC_DIR / "assets" / "glam-homes-logo.png"
            if target.exists():
                body = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", content_type_for(target))
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(204)
                self.end_headers()
            return
        if parsed.path == "/api/status":
            write_json(
                self,
                {
                    "ok": True,
                    "app": "GLAM HOMES CONCIERGE",
                    "openai_configured": bool(openai_api_key()),
                    "guesty_configured": guesty_configured(),
                    "twilio_configured": twilio_configured(),
                    "property_links_configured": property_links_configured(),
                    "property_links_db": str(PROPERTY_LINKS_DB),
                    "twilio_phone_number": os.environ.get("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER),
                    "public_base_url": os.environ.get("PUBLIC_BASE_URL", PUBLIC_BASE_URL),
                    "transcripts_enabled": True,
                    "transcripts_dir": str(TRANSCRIPTS_DIR),
                    "realtime_model": os.environ.get("OPENAI_REALTIME_MODEL", REALTIME_MODEL),
                    "default_voice": os.environ.get("OPENAI_REALTIME_VOICE", DEFAULT_VOICE),
                },
            )
            return
        if parsed.path == "/api/twilio/monitor":
            if not is_local_dashboard_request(self):
                write_json(self, local_only_monitor_payload(), status=403)
                return
            params = parse.parse_qs(parsed.query)
            deep = (params.get("deep") or ["1"])[0].lower() not in {"0", "false", "no"}
            try:
                write_json(self, build_twilio_monitor(deep=deep))
            except Exception as exc:
                write_json(self, {"ok": False, "generated_at": now_iso(), "error": str(exc)}, status=500)
            return
        if parsed.path == "/api/twilio/public-health":
            try:
                write_json(self, build_twilio_public_health())
            except Exception as exc:
                write_json(self, {"ok": False, "generated_at": now_iso(), "error": str(exc)}, status=500)
            return
        if parsed.path == "/api/calls/inbox":
            if not can_access_call_data(self):
                write_json(self, protected_call_data_payload(), status=403)
                return
            params = parse.parse_qs(parsed.query)
            try:
                write_json(
                    self,
                    build_call_inbox(
                        limit=clamp_limit((params.get("limit") or ["50"])[0], default=50, maximum=100),
                        query=(params.get("q") or [""])[0],
                    ),
                )
            except Exception as exc:
                write_json(self, {"ok": False, "error": str(exc)}, status=500)
            return
        if parsed.path == "/api/calls/transcript":
            if not can_access_call_data(self):
                write_json(self, protected_call_data_payload(), status=403)
                return
            params = parse.parse_qs(parsed.query)
            call_sid = (params.get("call_sid") or params.get("sid") or [""])[0]
            try:
                write_json(self, build_call_transcript(call_sid))
            except FileNotFoundError as exc:
                write_json(self, {"ok": False, "error": str(exc)}, status=404)
            except Exception as exc:
                write_json(self, {"ok": False, "error": str(exc)}, status=500)
            return
        if parsed.path == "/twilio/health":
            base_url = handler_public_base_url(self)
            write_json(
                self,
                {
                    "ok": True,
                    "service": "glam-homes-twilio",
                    "phone_number": os.environ.get("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER),
                    "twilio_configured": twilio_configured(),
                    "media_stream_url": websocket_url_from_public_base(base_url),
                    "transcripts_dir": str(TRANSCRIPTS_DIR),
                },
            )
            return
        if parsed.path == "/twilio/voice":
            params = {key: values[-1] for key, values in parse.parse_qs(parsed.query, keep_blank_values=True).items()}
            write_text(self, twilio_voice_twiml(self, params), content_type="text/xml; charset=utf-8")
            return
        if parsed.path == "/api/guesty/status":
            params = parse.parse_qs(parsed.query)
            try:
                write_json(self, guesty_status(live=(params.get("live") or ["0"])[0] in {"1", "true", "yes"}))
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/properties/search":
            params = parse.parse_qs(parsed.query)
            try:
                write_json(
                    self,
                    glam_search_public_property_links(
                        {
                            "query": (params.get("query") or [""])[0],
                            "city": (params.get("city") or [""])[0],
                            "platform": (params.get("platform") or ["any"])[0],
                            "min_guests": (params.get("min_guests") or [""])[0],
                            "check_in": (params.get("check_in") or [""])[0],
                            "check_out": (params.get("check_out") or [""])[0],
                            "guests": (params.get("guests") or [""])[0],
                            "limit": (params.get("limit") or ["5"])[0],
                        }
                    ),
                )
            except Exception as exc:
                write_json(self, {"ok": False, "error": str(exc)}, status=500)
            return
        if parsed.path == "/api/guesty/listings":
            params = parse.parse_qs(parsed.query)
            try:
                write_json(
                    self,
                    {"ok": True, "data": guesty_listings(limit=clamp_limit((params.get("limit") or ["5"])[0]), city=(params.get("city") or [""])[0])},
                )
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/guesty/available-listings":
            params = parse.parse_qs(parsed.query)
            try:
                write_json(
                    self,
                    {
                        "ok": True,
                        "data": guesty_available_listings(
                            (params.get("check_in") or [""])[0],
                            (params.get("check_out") or [""])[0],
                            (params.get("guests") or [""])[0],
                            limit=clamp_limit((params.get("limit") or ["5"])[0]),
                            city=(params.get("city") or [""])[0],
                        ),
                    },
                )
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/guesty/listing-calendar":
            params = parse.parse_qs(parsed.query)
            try:
                write_json(
                    self,
                    {
                        "ok": True,
                        "data": guesty_listing_calendar(
                            (params.get("listing_id") or [""])[0],
                            (params.get("start_date") or [""])[0],
                            (params.get("end_date") or [""])[0],
                        ),
                    },
                )
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/guesty/reservations":
            params = parse.parse_qs(parsed.query)
            try:
                write_json(
                    self,
                    {
                        "ok": True,
                        "data": guesty_reservations(
                            limit=clamp_limit((params.get("limit") or ["5"])[0]),
                            skip=int((params.get("skip") or ["0"])[0] or 0),
                            filters=(params.get("filters") or [""])[0],
                        ),
                    },
                )
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/guesty/reservation-by-code":
            params = parse.parse_qs(parsed.query)
            code = (params.get("code") or params.get("confirmation_code") or [""])[0]
            try:
                write_json(self, {"ok": True, "data": guesty_reservation_by_code(code)})
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/guesty/reservation":
            params = parse.parse_qs(parsed.query)
            reservation_id = (params.get("id") or params.get("reservation_id") or [""])[0]
            try:
                write_json(self, {"ok": True, "data": guesty_get_reservation(reservation_id)})
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        target = PUBLIC_DIR / ("index.html" if parsed.path in {"", "/"} else parsed.path.lstrip("/"))
        try:
            target = target.resolve()
            if not str(target).startswith(str(PUBLIC_DIR.resolve())) or not target.exists() or target.is_dir():
                self.send_error(404)
                return
            body = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type_for(target))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            write_text(self, f"Server error: {exc}", status=500)

    def do_POST(self) -> None:
        parsed = parse.urlparse(self.path)
        if parsed.path == "/api/transcripts/log":
            try:
                body = json.loads(read_request_body(self).decode("utf-8") or "{}")
                write_json(
                    self,
                    append_transcript_event(
                        body.get("session_id"),
                        str(body.get("speaker") or "System"),
                        body.get("text"),
                        channel=str(body.get("channel") or "web"),
                        kind=str(body.get("kind") or "message"),
                        metadata=body.get("metadata") if isinstance(body.get("metadata"), dict) else {},
                    ),
                )
            except Exception as exc:
                write_json(self, {"ok": False, "error": str(exc)}, status=500)
            return
        if parsed.path == "/twilio/voice":
            try:
                params = read_form_body(self)
                write_text(self, twilio_voice_twiml(self, params), content_type="text/xml; charset=utf-8")
            except Exception as exc:
                write_text(self, f'<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service unavailable.</Say></Response>', status=500, content_type="text/xml; charset=utf-8")
                self.log_message("Twilio voice webhook error: %s", exc)
            return
        if parsed.path == "/twilio/status":
            params = read_form_body(self)
            call_sid = params.get("CallSid") or params.get("callSid") or f"status-{int(time.time())}"
            status = params.get("CallStatus") or params.get("CallStatusCallbackEvent") or params.get("CallStatusCallback") or "unknown"
            append_transcript_event(
                call_sid,
                "System",
                f"Twilio status callback: {status}",
                channel="twilio",
                kind="status",
                metadata=params,
            )
            write_json(self, {"ok": True})
            return
        if parsed.path == "/twilio/sms":
            params = read_form_body(self)
            message_sid = params.get("MessageSid") or f"sms-{int(time.time())}"
            append_transcript_event(
                message_sid,
                "SMS",
                params.get("Body") or "(sin texto)",
                channel="twilio_sms",
                kind="inbound_sms",
                metadata={"from": params.get("From", ""), "to": params.get("To", ""), "message_sid": message_sid},
            )
            write_text(self, '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', content_type="text/xml; charset=utf-8")
            return
        if parsed.path == "/api/guesty/tool":
            try:
                body = json.loads(read_request_body(self).decode("utf-8") or "{}")
                write_json(self, run_guesty_tool(str(body.get("name") or ""), body.get("arguments") or {}))
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path != "/api/realtime-call":
            self.send_error(404)
            return
        params = parse.parse_qs(parsed.query)
        voice = (params.get("voice") or [DEFAULT_VOICE])[0]
        try:
            sdp = read_request_body(self).decode("utf-8", errors="replace")
            if not sdp.strip():
                write_text(self, "Missing SDP offer.", status=400)
                return
            answer = create_realtime_call(sdp, voice)
            write_text(self, answer, status=201, content_type="application/sdp")
        except Exception as exc:
            write_text(self, str(exc), status=500)


def main() -> int:
    load_dotenv()
    port = int(os.environ.get("PORT", str(PORT)))
    server = ThreadingHTTPServer((HOST, port), ConciergeHandler)
    print(f"GLAM HOMES CONCIERGE running at http://{HOST}:{port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
