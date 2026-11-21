"""Exchange a one-time Google authorization code for a permanent refresh token.

  python exchange_code.py --code "4/0..." --client-id "..." --client-secret "..."

Saves the refresh token to secrets/.env and prints it.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / "secrets" / ".env"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "https://developers.google.com/oauthplayground"


def save(token: str) -> None:
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    text = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
    line = f"GOOGLE_REFRESH_TOKEN={token}"
    if re.search(r"^GOOGLE_REFRESH_TOKEN=.*$", text, re.M):
        text = re.sub(r"^GOOGLE_REFRESH_TOKEN=.*$", line, text, flags=re.M)
    else:
        text = text.rstrip() + "\n" + line + "\n"
    ENV_FILE.write_text(text, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True)
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret", required=True)
    args = ap.parse_args()

    r = requests.post(
        TOKEN_URL,
        data={
            "code": args.code,
            "client_id": args.client_id,
            "client_secret": args.client_secret,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=60,
    )
    if r.status_code != 200:
        raise SystemExit(f"Exchange fail HTTP {r.status_code}: {r.text[:500]}")
    data = r.json()
    token = data.get("refresh_token")
    if not token:
        raise SystemExit(f"Refresh token nahi mila: {str(data)[:500]}")
    save(token)
    print("\n✅ Refresh token .env me save ho gaya:\n" + token)
    print("\nAb chalayein: python set_secrets.py")


if __name__ == "__main__":
    main()
