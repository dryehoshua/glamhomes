#!/usr/bin/env python3
"""
Interactive Guesty credential setup.

Prompts for OAuth client credentials and writes them to the project .env file
with private file permissions. Do not paste account passwords here.
"""

from __future__ import annotations

from getpass import getpass
from pathlib import Path
import stat


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

DEFAULTS = {
    "GUESTY_API_BASE_URL": "https://open-api.guesty.com/v1",
    "GUESTY_TOKEN_URL": "https://open-api.guesty.com/oauth2/token",
}


def read_existing_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_PATH.exists():
        return values
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def write_env(values: dict[str, str]) -> None:
    ordered_keys = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_API_KEY",
        "TWILIO_API_SECRET",
        "TWILIO_PHONE_NUMBER",
        "GUESTY_API_BASE_URL",
        "GUESTY_TOKEN_URL",
        "GUESTY_CLIENT_ID",
        "GUESTY_CLIENT_SECRET",
        "OPENAI_API_KEY",
        "VOICE_AGENT_MODEL",
        "PUBLIC_BASE_URL",
        "PORT",
    ]
    lines = []
    for key in ordered_keys:
        if key in values:
            lines.append(f"{key}={values[key]}")
    for key in sorted(set(values) - set(ordered_keys)):
        lines.append(f"{key}={values[key]}")
    ENV_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    ENV_PATH.chmod(stat.S_IRUSR | stat.S_IWUSR)


def main() -> int:
    values = read_existing_env()
    values.update(DEFAULTS)
    values.setdefault("TWILIO_PHONE_NUMBER", "+17864813013")
    values.setdefault("PORT", "3000")

    print("Guesty OAuth setup for GLAM HOMES")
    print("Use the Client ID and Client Secret from Guesty OAuth applications.")
    print("Do not enter your Guesty/Gmail account password here.\n")

    try:
        client_id = input("GUESTY_CLIENT_ID: ").strip()
        client_secret = getpass("GUESTY_CLIENT_SECRET: ").strip()
    except EOFError:
        print("Canceled: run this script in an interactive terminal.")
        return 1

    if not client_id or not client_secret:
        print("Canceled: both Client ID and Client Secret are required.")
        return 1

    values["GUESTY_CLIENT_ID"] = client_id
    values["GUESTY_CLIENT_SECRET"] = client_secret
    write_env(values)
    print(f"Wrote {ENV_PATH} with private permissions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
