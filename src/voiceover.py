"""Synthesize one MP3 per spoken line using edge-tts (free, no API key)."""
from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any

import edge_tts


def _duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    try:
        return max(0.5, float(out))
    except ValueError:
        return 2.0


def _tts_one(text: str, voice: str, rate: str, volume: str, out: Path) -> None:
    async def run() -> None:
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        await communicate.save(str(out))

    asyncio.run(run())


def synthesize(lines: list[str], cfg: dict[str, Any], work: Path) -> list[dict[str, Any]]:
    """Return [{path, text, duration}, ...] in the same order as lines."""
    work.mkdir(parents=True, exist_ok=True)
    tts = cfg["tts"]
    segments: list[dict[str, Any]] = []

    for i, line in enumerate(lines):
        path = work / f"voice_{i:03d}.mp3"
        if not path.exists() or path.stat().st_size == 0:
            _tts_one(line, tts["voice"], tts.get("rate", "+0%"), tts.get("volume", "+0%"), path)
        segments.append(
            {"path": path, "text": line, "duration": _duration(path)}
        )

    return segments
