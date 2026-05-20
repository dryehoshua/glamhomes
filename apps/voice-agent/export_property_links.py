#!/usr/bin/env python3
"""Export public Glam Homes booking links from the Guesty booking engine.

This reads the public Guesty booking site inventory, not the full internal
Guesty PMS listing table. That distinction matters: the concierge should share
only URLs that are visible on the public booking engine.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import json
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import guesty_client


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
SQLITE_PATH = DATA_DIR / "glam_homes_property_links.sqlite"
BOOKING_BASE_URL = "https://theglamhomes.guestybookings.com"
API_URL = "https://app.guesty.com/api/pm-websites-backend/listings"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)

# Public key embedded in the Guesty booking-engine frontend bundle. It is not a
# Glam Homes credential; Guesty can change it when they update the booking UI.
REQUEST_CONTEXT_KEY = "D/H\\9e$>^wpKGVH>S~:.rI<Ax\"4Br/[>c6m'b"
PUBLIC_FIELDS = (
    "_id title roomType beds timezone publicDescription picture address "
    "accommodates bedrooms bathrooms propertyType prices reviews nightlyRates "
    "totalPrice isRecommended"
)

CHANNEL_COLUMNS = {
    "airbnb2": "airbnb_url",
    "bookingCom": "booking_url",
    "homeaway2": "vrbo_url",
    "expedia": "expedia_url",
    "homesVillasByMarriott": "marriott_url",
    "googleVacationRentals": "google_vacation_rentals_url",
}


def request_context(user_agent: str) -> str:
    """Build the X-Request-Context header expected by Guesty's public engine."""

    user_hash = hashlib.sha256(user_agent.encode("utf-8")).hexdigest()[:8]
    window = int(time.time() // 900)
    session_id = "glamlinks"
    message = f"{window}:{session_id}:{user_hash}".encode("utf-8")
    digest = hmac.new(
        REQUEST_CONTEXT_KEY.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()[:32]
    payload = {"v": 1, "w": window, "s": session_id, "u": user_hash, "h": digest}
    return base64.b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()


def fetch_page(cursor: str | None = None) -> dict[str, Any]:
    params = {
        "minOccupancy": "1",
        "fields": PUBLIC_FIELDS,
    }
    if cursor:
        params["cursor"] = cursor

    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Origin": BOOKING_BASE_URL,
            "Referer": f"{BOOKING_BASE_URL}/en/properties?minOccupancy=1",
            "User-Agent": USER_AGENT,
            "X-Request-Context": request_context(USER_AGENT),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def first_picture(listing: dict[str, Any]) -> str:
    picture = listing.get("picture")
    if isinstance(picture, dict):
        return picture.get("thumbnail") or picture.get("regular") or picture.get("original") or ""
    return ""


def review_summary(reviews: Any) -> tuple[str, str]:
    if not isinstance(reviews, dict):
        return "", ""
    rating = reviews.get("avg") or reviews.get("average") or reviews.get("rating") or ""
    count = reviews.get("count") or reviews.get("total") or ""
    return str(rating) if rating != "" else "", str(count) if count != "" else ""


def nightly_price(listing: dict[str, Any]) -> str:
    total_price = listing.get("totalPrice")
    if isinstance(total_price, dict):
        amount = total_price.get("amount") or total_price.get("value")
        currency = total_price.get("currency") or "USD"
        if amount:
            return f"{amount} {currency}"

    prices = listing.get("prices")
    if isinstance(prices, dict):
        base = prices.get("basePrice") or prices.get("base")
        currency = prices.get("currency") or "USD"
        if base:
            return f"{base} {currency}"

    return ""


def normalize(listing: dict[str, Any]) -> dict[str, Any]:
    listing_id = str(listing.get("_id") or "")
    address = listing.get("address") if isinstance(listing.get("address"), dict) else {}
    rating, review_count = review_summary(listing.get("reviews"))
    title = str(listing.get("title") or "").strip()
    public_url_en = f"{BOOKING_BASE_URL}/en/properties/{listing_id}?minOccupancy=1"
    public_url_es = f"{BOOKING_BASE_URL}/es/properties/{listing_id}?minOccupancy=1"

    return {
        "listing_id": listing_id,
        "title": title,
        "city": address.get("city") or "",
        "state": address.get("state") or "",
        "country": address.get("country") or "",
        "accommodates": listing.get("accommodates") or "",
        "bedrooms": listing.get("bedrooms") or "",
        "bathrooms": listing.get("bathrooms") or "",
        "beds": listing.get("beds") or "",
        "property_type": listing.get("propertyType") or listing.get("roomType") or "",
        "starting_price": nightly_price(listing),
        "rating": rating,
        "review_count": review_count,
        "image_url": first_picture(listing),
        "public_url_en": public_url_en,
        "public_url_es": public_url_es,
        "airbnb_url": "",
        "booking_url": "",
        "vrbo_url": "",
        "expedia_url": "",
        "marriott_url": "",
        "google_vacation_rentals_url": "",
        "channel_links_json": "{}",
        "channel_status_json": "{}",
        "active_public": 1,
        "sms_text_es": f"Glam Homes: te comparto la propiedad {title}: {public_url_en}",
    }


def channel_status(integration: dict[str, Any], platform: str) -> str:
    platform_payload = integration.get(platform)
    if isinstance(platform_payload, dict):
        return str(platform_payload.get("status") or "")
    return str(integration.get("status") or "")


def enrich_channel_links(rows: list[dict[str, Any]]) -> None:
    """Add OTA links from Guesty listing integrations when available."""

    guesty_client.load_dotenv()
    if not guesty_client.required_env("GUESTY_CLIENT_ID") or not guesty_client.required_env("GUESTY_CLIENT_SECRET"):
        return

    for index, row in enumerate(rows, start=1):
        listing_id = row["listing_id"]
        try:
            listing = guesty_client.guesty_get(f"/listings/{urllib.parse.quote(listing_id)}")
        except Exception as exc:
            row["channel_status_json"] = json.dumps({"guesty_detail_error": str(exc)}, ensure_ascii=False)
            continue

        links: dict[str, str] = {}
        statuses: dict[str, str] = {}
        integrations = listing.get("integrations") if isinstance(listing.get("integrations"), list) else []
        for integration in integrations:
            if not isinstance(integration, dict):
                continue
            platform = str(integration.get("platform") or "")
            if not platform:
                continue
            status = channel_status(integration, platform)
            if status:
                statuses[platform] = status
            external_url = str(integration.get("externalUrl") or "").strip()
            column = CHANNEL_COLUMNS.get(platform)
            if external_url and column:
                row[column] = external_url
                links[platform] = external_url
            elif external_url:
                links[platform] = external_url

        row["channel_links_json"] = json.dumps(links, ensure_ascii=False, sort_keys=True)
        row["channel_status_json"] = json.dumps(statuses, ensure_ascii=False, sort_keys=True)
        print(f"enriched {index}/{len(rows)} {listing_id}", file=sys.stderr)


def export_rows(rows: list[dict[str, Any]], generated_at: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DATA_DIR / "guesty-property-links.json"
    csv_path = DATA_DIR / "guesty-property-links.csv"
    md_path = DATA_DIR / "guesty-property-links.md"

    payload = {
        "generated_at": generated_at,
        "source": f"{BOOKING_BASE_URL}/en/properties?minOccupancy=1",
        "public_listing_count": len(rows),
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fieldnames = list(rows[0].keys()) if rows else []
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Glam Homes public property links",
        "",
        f"- Generated at: `{generated_at}`",
        f"- Source: {BOOKING_BASE_URL}/en/properties?minOccupancy=1",
        f"- Public listings: {len(rows)}",
        "",
        "| # | Property | City | Guests | Link |",
        "|---:|---|---|---:|---|",
    ]
    for index, row in enumerate(rows, start=1):
        title = row["title"].replace("|", "\\|")
        city = str(row["city"]).replace("|", "\\|")
        guests = row["accommodates"]
        lines.append(f"| {index} | {title} | {city} | {guests} | {row['public_url_en']} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    export_sqlite(rows, generated_at, payload["source"])


def export_sqlite(rows: list[dict[str, Any]], generated_at: str, source: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(SQLITE_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS public_properties")
        conn.execute("DROP TABLE IF EXISTS property_channel_links")
        conn.execute(
            """
            CREATE TABLE public_properties (
                listing_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                city TEXT,
                state TEXT,
                country TEXT,
                accommodates INTEGER,
                bedrooms TEXT,
                bathrooms TEXT,
                beds TEXT,
                property_type TEXT,
                starting_price TEXT,
                rating TEXT,
                review_count TEXT,
                image_url TEXT,
                public_url_en TEXT NOT NULL,
                public_url_es TEXT,
                airbnb_url TEXT,
                booking_url TEXT,
                vrbo_url TEXT,
                expedia_url TEXT,
                marriott_url TEXT,
                google_vacation_rentals_url TEXT,
                channel_links_json TEXT,
                channel_status_json TEXT,
                sms_text_es TEXT,
                active_public INTEGER NOT NULL,
                generated_at TEXT NOT NULL,
                source TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE property_channel_links (
                listing_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                url TEXT NOT NULL,
                status TEXT,
                generated_at TEXT NOT NULL,
                PRIMARY KEY (listing_id, platform),
                FOREIGN KEY (listing_id) REFERENCES public_properties(listing_id)
            )
            """
        )
        for row in rows:
            conn.execute(
                """
                INSERT INTO public_properties VALUES (
                    :listing_id, :title, :city, :state, :country, :accommodates,
                    :bedrooms, :bathrooms, :beds, :property_type, :starting_price,
                    :rating, :review_count, :image_url, :public_url_en, :public_url_es,
                    :airbnb_url, :booking_url, :vrbo_url, :expedia_url, :marriott_url,
                    :google_vacation_rentals_url, :channel_links_json,
                    :channel_status_json, :sms_text_es, :active_public,
                    :generated_at, :source
                )
                """,
                {**row, "generated_at": generated_at, "source": source},
            )
            links = json.loads(row.get("channel_links_json") or "{}")
            statuses = json.loads(row.get("channel_status_json") or "{}")
            for platform, url in links.items():
                conn.execute(
                    """
                    INSERT INTO property_channel_links VALUES (?, ?, ?, ?, ?)
                    """,
                    (row["listing_id"], platform, url, statuses.get(platform, ""), generated_at),
                )
        conn.execute("CREATE INDEX idx_public_properties_title ON public_properties(title)")
        conn.execute("CREATE INDEX idx_public_properties_city ON public_properties(city)")
        conn.execute("CREATE INDEX idx_channel_links_platform ON property_channel_links(platform)")


def main() -> int:
    cursor: str | None = None
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    expected_total: int | None = None

    for _ in range(10):
        page = fetch_page(cursor)
        expected_total = page.get("pagination", {}).get("total") or expected_total
        for listing in page.get("results", []):
            listing_id = str(listing.get("_id") or "")
            if listing_id and listing_id not in seen:
                seen.add(listing_id)
                rows.append(normalize(listing))

        cursor = page.get("pagination", {}).get("cursor", {}).get("next")
        if not cursor or (expected_total and len(rows) >= expected_total):
            break

    rows.sort(key=lambda item: item["title"].lower())
    try:
        enrich_channel_links(rows)
    except Exception as exc:
        print(f"warning: channel link enrichment skipped: {exc}", file=sys.stderr)
    generated_at = datetime.now(timezone.utc).isoformat()
    export_rows(rows, generated_at)

    print(
        json.dumps(
            {
                "public_listing_count": len(rows),
                "expected_total": expected_total,
                "outputs": [
                    str(DATA_DIR / "guesty-property-links.json"),
                    str(DATA_DIR / "guesty-property-links.csv"),
                    str(DATA_DIR / "guesty-property-links.md"),
                    str(SQLITE_PATH),
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
