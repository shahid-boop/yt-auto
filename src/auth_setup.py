"""One-time OAuth helper: produce a refresh token for the upload scope.

Usage:
  python -m src.auth_setup
It prints a URL. Open it, approve access, and the token is saved to
secrets/token.json. Copy the printed refresh token into GitHub Secrets.
"""
from __future__ import annotations

import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from .env_loader import load_env
from .upload import SCOPES

SECRET_FILE = Path(__file__).resolve().parent.parent / "secrets" / "client_secret.json"
TOKEN_FILE = Path(__file__).resolve().parent.parent / "secrets" / "token.json"


def main() -> None:
    load_env()
    if not SECRET_FILE.exists():
        raise SystemExit(
            f"Pehle {SECRET_FILE} me OAuth client_secret.json rakhein."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(SECRET_FILE), SCOPES)
    creds = flow.run_local_server(
        port=8080,
        open_browser=False,
        prompt="consent",
        access_type="offline",
    )

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(
        json.dumps(
            {
                "refresh_token": creds.refresh_token,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "token_uri": "https://oauth2.googleapis.com/token",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("\n=== DONE ===")
    print("Refresh token (GitHub Secret GOOGLE_REFRESH_TOKEN me daalein):")
    print(creds.refresh_token)
    print(f"\nFull token backup: {TOKEN_FILE}")


if __name__ == "__main__":
    main()
