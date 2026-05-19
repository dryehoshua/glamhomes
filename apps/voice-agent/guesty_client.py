#!/usr/bin/env python3
"""
Small Guesty Open API client for Glam Homes.

Uses OAuth client_credentials and caches the access token locally because Guesty
limits token generation per client in a 24-hour window.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import time
from typing import Any
from urllib import error, parse, request


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
CACHE_DIR = PROJECT_ROOT / ".cache"
TOKEN_CACHE = CACHE_DIR / "guesty_token.json"

DEFAULT_API_BASE = "https://open-api.guesty.com/v1"
DEFAULT_TOKEN_URL = "https://open-api.guesty.com/oauth2/token"

RESERVATION_FIELDS = (
    "_id confirmationCode status checkInDateLocalized checkOutDateLocalized "
    "listing._id listing.title guest._id guest.fullName guest.email guest.phone "
    "source balanceDue money.totalPaid money.balanceDue plannedArrival plannedDeparture"
)
LISTING_FIELDS = (
    "_id title nickname address.full address.city address.country accommodates "
    "bedrooms bathrooms amenities pictures active listed"
)
LISTING_SEARCH_FIELDS = "_id title nickname active listed address.city accommodates bedrooms bathrooms"
GUEST_FIELDS = "fullName guestEmail guestPhone address id"


class GuestyError(RuntimeError):
    pass


def load_dotenv(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise GuestyError(f"Missing required environment variable: {name}")
    return value


def json_request(url: str, *, method: str = "GET", headers: dict[str, str] | None = None, data: bytes | None = None) -> dict[str, Any]:
    request_headers = {"Accept": "application/json", **(headers or {})}
    req = request.Request(url, method=method, headers=request_headers, data=data)
    try:
        with request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GuestyError(f"Guesty HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise GuestyError(f"Guesty connection error: {exc.reason}") from exc


def read_cached_token() -> str | None:
    try:
        payload = json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
    expires_at = float(payload.get("expires_at") or 0)
    token = str(payload.get("access_token") or "")
    if token and expires_at - time.time() > 300:
        return token
    return None


def write_cached_token(token_payload: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    expires_in = int(token_payload.get("expires_in") or 86400)
    payload = {
        "access_token": token_payload["access_token"],
        "token_type": token_payload.get("token_type", "Bearer"),
        "scope": token_payload.get("scope", "open-api"),
        "expires_at": time.time() + expires_in,
    }
    TOKEN_CACHE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    TOKEN_CACHE.chmod(stat.S_IRUSR | stat.S_IWUSR)


def fetch_token() -> str:
    token_url = os.environ.get("GUESTY_TOKEN_URL", DEFAULT_TOKEN_URL).strip() or DEFAULT_TOKEN_URL
    body = parse.urlencode(
        {
            "grant_type": "client_credentials",
            "scope": "open-api",
            "client_id": required_env("GUESTY_CLIENT_ID"),
            "client_secret": required_env("GUESTY_CLIENT_SECRET"),
        }
    ).encode("utf-8")
    payload = json_request(
        token_url,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=body,
    )
    if not payload.get("access_token"):
        raise GuestyError("Token response did not include access_token.")
    write_cached_token(payload)
    return str(payload["access_token"])


def get_token(force_refresh: bool = False) -> str:
    if not force_refresh:
        cached = read_cached_token()
        if cached:
            return cached
    return fetch_token()


def api_url(path: str, params: dict[str, Any] | None = None) -> str:
    base = os.environ.get("GUESTY_API_BASE_URL", DEFAULT_API_BASE).strip().rstrip("/") or DEFAULT_API_BASE
    clean_path = "/" + path.lstrip("/")
    query = parse.urlencode(params or {}, doseq=False)
    return f"{base}{clean_path}" + (f"?{query}" if query else "")


def guesty_get(path: str, params: dict[str, Any] | None = None, *, force_refresh: bool = False) -> dict[str, Any]:
    token = get_token(force_refresh=force_refresh)
    return json_request(api_url(path, params), headers={"Authorization": f"Bearer {token}"})


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def auth_check(args: argparse.Namespace) -> None:
    token = get_token(force_refresh=args.refresh)
    print_json({"ok": True, "token_cached": TOKEN_CACHE.exists(), "token_preview": token[:12] + "...", "cache": str(TOKEN_CACHE)})


def list_listings(args: argparse.Namespace) -> None:
    params = {
        "limit": min(max(args.limit, 1), 100),
        "skip": max(args.skip, 0),
        "fields": args.fields or LISTING_FIELDS,
        "sort": args.sort,
    }
    print_json(guesty_get("/listings", params))


def available_listings(args: argparse.Namespace) -> None:
    params = {
        "limit": min(max(args.limit, 1), 100),
        "skip": max(args.skip, 0),
        "fields": args.fields or LISTING_SEARCH_FIELDS,
        "sort": args.sort,
        "available": json.dumps(
            {"checkIn": args.check_in, "checkOut": args.check_out, "minOccupancy": args.guests},
            separators=(",", ":"),
        ),
    }
    if args.city:
        params["filters"] = json.dumps([{"operator": "$contains", "field": "address.city", "value": args.city}], separators=(",", ":"))
    print_json(guesty_get("/listings", params))


def calendar_minified(args: argparse.Namespace) -> None:
    print_json(
        guesty_get(
            f"/availability-pricing/api/calendar/listings/minified/{parse.quote(args.listing_id)}",
            {"startDate": args.start_date, "endDate": args.end_date},
        )
    )


def list_reservations(args: argparse.Namespace) -> None:
    params = {
        "limit": min(max(args.limit, 1), 100),
        "skip": max(args.skip, 0),
        "fields": args.fields or RESERVATION_FIELDS,
        "sort": args.sort,
    }
    if args.filters:
        params["filters"] = args.filters
    print_json(guesty_get("/reservations", params))


def get_reservation(args: argparse.Namespace) -> None:
    params = {"fields": args.fields or RESERVATION_FIELDS}
    print_json(guesty_get(f"/reservations/{parse.quote(args.reservation_id)}", params))


def reservation_by_code(args: argparse.Namespace) -> None:
    filters = [{"operator": "$in", "field": "confirmationCode", "value": [args.confirmation_code]}]
    params = {
        "filters": json.dumps(filters, separators=(",", ":")),
        "fields": args.fields or RESERVATION_FIELDS,
        "sort": "_id",
        "limit": 10,
        "skip": 0,
    }
    print_json(guesty_get("/reservations", params))


def list_guests(args: argparse.Namespace) -> None:
    params = {
        "columns": args.columns or GUEST_FIELDS,
        "limit": min(max(args.limit, 1), 100),
        "skip": max(args.skip, 0),
    }
    if args.filters:
        params["filters"] = args.filters
    print_json(guesty_get("/guests-crud", params))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Glam Homes Guesty Open API client")
    sub = parser.add_subparsers(dest="command", required=True)

    auth = sub.add_parser("auth-check", help="Get/cache an OAuth token and show a safe preview")
    auth.add_argument("--refresh", action="store_true", help="Force token refresh")
    auth.set_defaults(func=auth_check)

    listings = sub.add_parser("listings", help="List Guesty listings")
    listings.add_argument("--limit", type=int, default=5)
    listings.add_argument("--skip", type=int, default=0)
    listings.add_argument("--sort", default="-createdAt")
    listings.add_argument("--fields", default="")
    listings.set_defaults(func=list_listings)

    available = sub.add_parser("available-listings", help="Find listings available for dates and guest count")
    available.add_argument("--check-in", required=True, help="YYYY-MM-DD")
    available.add_argument("--check-out", required=True, help="YYYY-MM-DD")
    available.add_argument("--guests", type=int, required=True)
    available.add_argument("--limit", type=int, default=5)
    available.add_argument("--skip", type=int, default=0)
    available.add_argument("--city", default="")
    available.add_argument("--sort", default="title")
    available.add_argument("--fields", default="")
    available.set_defaults(func=available_listings)

    calendar = sub.add_parser("calendar-minified", help="Get minified availability/pricing calendar for one listing")
    calendar.add_argument("listing_id")
    calendar.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    calendar.add_argument("--end-date", required=True, help="YYYY-MM-DD")
    calendar.set_defaults(func=calendar_minified)

    reservations = sub.add_parser("reservations", help="List or filter reservations")
    reservations.add_argument("--limit", type=int, default=5)
    reservations.add_argument("--skip", type=int, default=0)
    reservations.add_argument("--sort", default="-createdAt")
    reservations.add_argument("--fields", default="")
    reservations.add_argument("--filters", default="", help="Guesty filters JSON string")
    reservations.set_defaults(func=list_reservations)

    reservation = sub.add_parser("reservation", help="Retrieve one reservation by Guesty ID")
    reservation.add_argument("reservation_id")
    reservation.add_argument("--fields", default="")
    reservation.set_defaults(func=get_reservation)

    by_code = sub.add_parser("reservation-by-code", help="Find reservation by confirmation code")
    by_code.add_argument("confirmation_code")
    by_code.add_argument("--fields", default="")
    by_code.set_defaults(func=reservation_by_code)

    guests = sub.add_parser("guests", help="List or filter guests")
    guests.add_argument("--limit", type=int, default=5)
    guests.add_argument("--skip", type=int, default=0)
    guests.add_argument("--columns", default="")
    guests.add_argument("--filters", default="")
    guests.set_defaults(func=list_guests)

    return parser


def main() -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except GuestyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
