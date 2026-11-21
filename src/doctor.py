"""Pre-flight check: python -m src.doctor"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import yaml

from .visuals import find_font

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    problems: list[str] = []

    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool):
            print(f"[OK]   {tool}")
        else:
            problems.append(f"{tool} missing")
            print(f"[FAIL] {tool} missing")

    if shutil.which("ffmpeg"):
        out = subprocess.run(
            ["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True
        ).stdout
        for needed in ("drawtext",):
            if needed in out:
                print(f"[OK]   ffmpeg {needed} filter")
            else:
                problems.append(f"ffmpeg {needed} filter missing")
                print(f"[FAIL] ffmpeg {needed} filter missing")

    try:
        print(f"[OK]   font: {find_font(cfg)}")
    except Exception as exc:  # noqa: BLE001
        problems.append(f"font: {exc}")
        print(f"[FAIL] font: {exc}")

    print(f"[OK]   config.yaml — niche: {cfg['content']['niche']}")

    env = {
        "OPENAI_API_KEY": "script generation",
        "GOOGLE_CLIENT_ID": "OAuth",
        "GOOGLE_CLIENT_SECRET": "OAuth",
        "GOOGLE_REFRESH_TOKEN": "upload",
    }
    for key, purpose in env.items():
        state = "OK" if os.environ.get(key) else "MISSING"
        print(f"[{state}]  {key} ({purpose})")

    if problems:
        print("\nProblems: " + ", ".join(problems))
    else:
        print("\nDoctor: PASS (local build ke liye taiyaar)")


if __name__ == "__main__":
    main()
