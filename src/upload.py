"""Upload video to YouTube using only `requests` (no Google client library).

OAuth refresh -> access token, then a resumable upload to the Data API v3.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests

from .env_loader import load_env

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} set nahi hai. secrets/.env ya GitHub Secrets me daalein."
        )
    return value


def access_token() -> str:
    load_env()
    payload = {
        "client_id": _required("GOOGLE_CLIENT_ID"),
        "client_secret": _required("GOOGLE_CLIENT_SECRET"),
        "refresh_token": _required("GOOGLE_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }
    r = requests.post(TOKEN_URL, data=payload, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(
            "Refresh token fail (expired/revoke ya galat credentials). "
            f"Production publishing check karein. HTTP {r.status_code}: {r.text[:400]}"
        )
    token = r.json().get("access_token")
    if not token:
        raise RuntimeError(f"Access token nahi mila: {r.text[:400]}")
    return token


def upload(path: Path, script: dict[str, Any], cfg: dict[str, Any]) -> str:
    token = access_token()
    channel = cfg["channel"]
    tags = list(script.get("tags", [])) + channel.get("default_tags", [])
    tags = list(dict.fromkeys(tags))[:20]

    metadata = {
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

    size = path.stat().st_size
    init_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": "video/mp4",
        "X-Upload-Content-Length": str(size),
    }
    init = requests.post(
        UPLOAD_URL,
        params={"part": "snippet,status", "uploadType": "resumable"},
        headers=init_headers,
        data=json.dumps(metadata),
        timeout=60,
    )
    if init.status_code not in (200, 201) or "Location" not in init.headers:
        raise RuntimeError(
            f"Resumable session fail HTTP {init.status_code}: {init.text[:600]}"
        )

    with path.open("rb") as fh:
        result = requests.put(
            init.headers["Location"],
            headers={"Content-Type": "video/mp4", "Content-Length": str(size)},
            data=fh,
            timeout=600,
        )
    if result.status_code not in (200, 201):
        raise RuntimeError(f"Video upload fail HTTP {result.status_code}: {result.text[:600]}")

    video_id = result.json().get("id", "")
    return f"https://www.youtube.com/watch?v={video_id}" if video_id else str(result.json())
