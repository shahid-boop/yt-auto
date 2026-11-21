"""Upload a rendered MP4 to YouTube with the Data API v3 (OAuth refresh token)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from .env_loader import load_env

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _credentials() -> Credentials:
    load_env()
    required = {
        "GOOGLE_CLIENT_ID": os.environ.get("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "GOOGLE_REFRESH_TOKEN": os.environ.get("GOOGLE_REFRESH_TOKEN"),
    }
    missing = [k for k, value in required.items() if not value]
    if missing:
        raise RuntimeError("Missing env vars: " + ", ".join(missing))

    creds = Credentials(
        token=None,
        refresh_token=required["GOOGLE_REFRESH_TOKEN"],
        client_id=required["GOOGLE_CLIENT_ID"],
        client_secret=required["GOOGLE_CLIENT_SECRET"],
        token_uri=TOKEN_URI,
        scopes=SCOPES,
    )
    try:
        creds.refresh(Request())
    except Exception as exc:  # google.auth.exceptions.RefreshError
        raise RuntimeError(
            "Refresh token expire ya revoke ho gaya. Google Cloud console me "
            "OAuth consent screen ko 'In Production' par publish karein, phir "
            "python -m src.auth_setup se naya token lein. "
            f"Original error: {exc}"
        ) from exc
    return creds


def upload(path: Path, script: dict[str, Any], cfg: dict[str, Any]) -> str:
    youtube = build("youtube", "v3", credentials=_credentials(), cache_discovery=False)
    channel = cfg["channel"]
    tags = list(script.get("tags", [])) + channel.get("default_tags", [])
    tags = list(dict.fromkeys(tags))[:20]

    body = {
        "snippet": {
            "title": script["title"][:100],
            "description": script["description"],
            "tags": tags,
            "categoryId": str(channel.get("category_id", "22")),
            "defaultLanguage": channel.get("default_language", "en-US"),
        },
        "status": {
            "privacyStatus": channel.get("privacy_status", "public"),
            "madeForKids": bool(channel.get("made_for_kids", False)),
            "selfDeclaredMadeForKids": bool(channel.get("made_for_kids", False)),
        },
    }

    media = MediaFileUpload(str(path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media=media)
    response = request.execute()
    video_id = response.get("id", "")
    return f"https://www.youtube.com/watch?v={video_id}" if video_id else str(response)
