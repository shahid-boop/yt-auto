"""Assemble slide images + per-line audio into one MP4 with ffmpeg."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "ffmpeg failed:\n" + (result.stderr or "")[-3000:]
        )


def build(
    segments: list[dict[str, Any]],
    cfg: dict[str, Any],
    out_path: Path,
    work: Path,
) -> Path:
    """segments = [{image: Path, audio: Path, duration: float, caption: str}, ...]"""
    work.mkdir(parents=True, exist_ok=True)
    v = cfg["visual"]
    w, h = int(v["width"]), int(v["height"])
    fps = int(v.get("fps", 24))
    rendered: list[Path] = []

    for i, seg in enumerate(segments):
        audio: Path = seg["audio"]
        image: Path = seg["image"]
        pad = 0.35

        target = work / f"segment_{i:03d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", str(fps), "-i", str(image),
            "-i", str(audio),
            "-af", f"apad=pad_dur={pad}",
            "-vf", f"scale={w}:{h}",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest", str(target),
        ]
        _run(cmd)
        rendered.append(target)

    list_file = work / "concat.txt"
    list_file.write_text(
        "".join(f"file '{p.resolve()}'\n" for p in rendered), encoding="utf-8"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file), "-c", "copy", str(out_path),
        ]
    )
    return out_path
