"""One-time OAuth helper (stdlib + requests, no Google client library).

  python -m src.auth_setup

Prints an authorization URL. Open it, approve, and the refresh token is saved
into secrets/.env automatically.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests

from .env_loader import load_env

ROOT = Path(__file__).resolve().parent.parent
SECRET_FILE = ROOT / "secrets" / "client_secret.json"
ENV_FILE = ROOT / "secrets" / ".env"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
REDIRECT_URI = "http://localhost:8080"
TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


class _Handler(BaseHTTPRequestHandler):
    code: str = ""

    def do_GET(self) -> None:  # noqa: N802
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _Handler.code = query.get("code", [""])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            "<h3>Authorization complete. You can close this tab.</h3>".encode()
        )

    def log_message(self, *_: object) -> None:
        pass


def _save_refresh_token(token: str) -> None:
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    text = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
    line = f"GOOGLE_REFRESH_TOKEN={token}"
    if re.search(r"^GOOGLE_REFRESH_TOKEN=.*$", text, re.M):
        text = re.sub(r"^GOOGLE_REFRESH_TOKEN=.*$", line, text, flags=re.M)
    else:
        text = text.rstrip() + "\n" + line + "\n"
    ENV_FILE.write_text(text, encoding="utf-8")


def main() -> None:
    load_env()
    if not SECRET_FILE.exists():
        raise SystemExit(
            f"Pehle {SECRET_FILE} me client_secret.json save karein."
        )

    config = json.loads(SECRET_FILE.read_text(encoding="utf-8"))
    oauth = config.get("web") or config.get("installed") or config
    client_id = oauth["client_id"]
    client_secret = oauth["client_secret"]

    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print("\nYe URL browser me kholein:\n" + url + "\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

    server = HTTPServer(("127.0.0.1", 8080), _Handler)
    server.timeout = 300
    print("Approve hone ka intezaar ho raha hai (max 5 min)...")
    server.handle_request()
    server.server_close()

    if not _Handler.code:
        raise SystemExit("Authorization code nahi mila. Dobara try karein.")

    r = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": _Handler.code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        timeout=60,
    )
    if r.status_code != 200:
        raise SystemExit(f"Token exchange fail: {r.status_code} {r.text[:500]}")
    token = r.json().get("refresh_token")
    if not token:
        raise SystemExit(f"Refresh token nahi mila: {r.text[:500]}")

    _save_refresh_token(token)
    print("\n✅ Refresh token secrets/.env me save ho gaya.")
    print("GitHub Secret GOOGLE_REFRESH_TOKEN me bhi yehi value daalein:")
    print(token)


if __name__ == "__main__":
    main()
