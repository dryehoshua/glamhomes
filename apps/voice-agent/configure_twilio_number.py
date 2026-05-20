#!/usr/bin/env python3
"""Configure the GLAM HOMES Twilio number webhooks safely.

The script only updates the exact TWILIO_PHONE_NUMBER in .env. It refuses to
touch numbers ending in 7532 because that belongs to Kim Live.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from urllib import error, parse, request

import server as glam


TWILIO_API = "https://api.twilio.com/2010-04-01"
KIM_PROTECTED_SUFFIX = "7532"


def env_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta {name} en .env.")
    return value


def auth_header(account_sid: str, auth_token: str) -> str:
    raw = f"{account_sid}:{auth_token}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def twilio_request(account_sid: str, auth_token: str, url: str, data: dict[str, str] | None = None) -> dict:
    encoded = parse.urlencode(data).encode("utf-8") if data is not None else None
    req = request.Request(
        url,
        data=encoded,
        headers={
            "Authorization": auth_header(account_sid, auth_token),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST" if data is not None else "GET",
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Twilio HTTP {exc.code}: {body}") from exc


def find_number(account_sid: str, auth_token: str, phone_number: str) -> dict:
    query = parse.urlencode({"PhoneNumber": phone_number})
    payload = twilio_request(account_sid, auth_token, f"{TWILIO_API}/Accounts/{account_sid}/IncomingPhoneNumbers.json?{query}")
    numbers = payload.get("incoming_phone_numbers") or []
    if not numbers:
        raise RuntimeError(f"No encontre el numero {phone_number} en esta cuenta Twilio.")
    return numbers[0]


def configure_number(dry_run: bool) -> dict:
    account_sid = env_required("TWILIO_ACCOUNT_SID")
    auth_token = env_required("TWILIO_AUTH_TOKEN")
    phone_number = env_required("TWILIO_PHONE_NUMBER")
    public_base_url = env_required("PUBLIC_BASE_URL").rstrip("/")

    if phone_number.endswith(KIM_PROTECTED_SUFFIX):
        raise RuntimeError("Proteccion activa: este numero parece ser Kim Live y no se tocara.")

    incoming_number = find_number(account_sid, auth_token, phone_number)
    update_url = f"{TWILIO_API}/Accounts/{account_sid}/IncomingPhoneNumbers/{incoming_number['sid']}.json"
    webhooks = {
        "VoiceUrl": f"{public_base_url}/twilio/voice",
        "VoiceMethod": "POST",
        "StatusCallback": f"{public_base_url}/twilio/status",
        "StatusCallbackMethod": "POST",
        "SmsUrl": f"{public_base_url}/twilio/sms",
        "SmsMethod": "POST",
    }
    if dry_run:
        return {"ok": True, "dry_run": True, "phone_number": phone_number, "webhooks": webhooks}
    updated = twilio_request(account_sid, auth_token, update_url, webhooks)
    return {
        "ok": True,
        "dry_run": False,
        "phone_number": updated.get("phone_number"),
        "voice_url": updated.get("voice_url"),
        "sms_url": updated.get("sms_url"),
        "status_callback": updated.get("status_callback"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure GLAM HOMES Twilio webhooks")
    parser.add_argument("--apply", action="store_true", help="Apply the webhook update. Default is dry-run.")
    args = parser.parse_args()
    glam.load_dotenv()
    result = configure_number(dry_run=not args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
