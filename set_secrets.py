"""Push secrets from secrets/.env to GitHub Actions Secrets (REST + NaCl).

Usage:
  python set_secrets.py                 # all non-empty values
  python set_secrets.py --name OPENAI_API_KEY
"""
from __future__ import annotations

import argparse
import base64
import re
import subprocess
from pathlib import Path

import requests
from nacl.public import PublicKey, SealedBox

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / "secrets" / ".env"
REPO = "shahid-boop/yt-auto"
API = "https://api.github.com"


def github_token() -> str:
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    match = re.search(r"^password=(.+)$", out, re.M)
    if not match:
        raise SystemExit("Git credential store me GitHub token nahi mila.")
    return match.group(1).strip()


def read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_FILE.exists():
        raise SystemExit(f"{ENV_FILE} nahi mila.")
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", help="sirf ye secret set karein")
    args = ap.parse_args()

    token = github_token()
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    key_resp = requests.get(
        f"{API}/repos/{REPO}/actions/secrets/public-key",
        headers=headers,
        timeout=30,
    )
    if key_resp.status_code != 200:
        raise SystemExit(
            f"Public key nahi mila: {key_resp.status_code} {key_resp.text[:400]}"
        )
    key_data = key_resp.json()
    public_key = PublicKey(base64.b64decode(key_data["key"]))
    box = SealedBox(public_key)

    wanted = {"OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_CLIENT_ID",
              "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"}
    if args.name:
        wanted = {args.name}

    for name in sorted(wanted):
        value = read_env().get(name, "")
        if not value:
            print(f"[SKIP] {name} — .env me khali hai")
            continue
        encrypted = base64.b64encode(box.encrypt(value.encode())).decode()
        r = requests.put(
            f"{API}/repos/{REPO}/actions/secrets/{name}",
            headers=headers,
            json={"encrypted_value": encrypted, "key_id": key_data["key_id"]},
            timeout=30,
        )
        state = "OK" if r.status_code in (201, 204) else f"FAIL {r.status_code}: {r.text[:200]}"
        print(f"[{state}] {name}")


if __name__ == "__main__":
    main()
