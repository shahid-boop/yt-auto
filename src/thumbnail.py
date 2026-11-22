"""Create a 1280x720 YouTube thumbnail and embed it as MP4 cover art."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .visuals import find_font


def _wrap(text: str, max_chars: int = 22, max_lines: int = 3) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) <= max_chars or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:max_lines]


def make_thumbnail(title: str, cfg: dict[str, Any], out_path: Path) -> Path:
    font = find_font(cfg)
    w, h = 1280, 720
    textfile = out_path.with_suffix(".txt")
    lines = _wrap(title)
    textfile.write_text("\n".join(lines), encoding="utf-8")

    filters = [
        f"drawbox=x={w - 170}:y=0:w=170:h={h}:color=0x38bdf8@0.12:t=fill",
        "drawbox=x=72:y=62:w=8:h=96:color=0x38bdf8:t=fill",
        f"drawtext=fontfile={font}:text='MIND SECRETS URDU':fontsize=28:"
        "fontcolor=0x38bdf8:x=104:y=68",
        f"drawtext=fontfile={font}:textfile={textfile}:fontsize=62:"
        "fontcolor=white:x=88:y=(h-text_h)/2-10:line_spacing=16",
        f"drawtext=fontfile={font}:text='FULL VIDEO':fontsize=26:"
        "fontcolor=0x38bdf8:x=88:y=h-80",
        f"drawtext=fontfile={font}:text='WATCH NOW  >>':fontsize=26:"
        f"fontcolor=white:x={w - 300}:y=h-80",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=0x0b1020:s={w}x{h}",
        "-frames:v", "1",
        "-vf", ",".join(filters),
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("Thumbnail render fail:\n" + r.stderr[-1500:])
    return out_path


def embed_cover(video: Path, thumb: Path) -> Path:
    """Add the thumbnail as attached-picture metadata (used by YouTube/players)."""
    tmp = video.with_name(video.stem + "_cover.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video), "-i", str(thumb),
        "-map", "0", "-map", "1",
        "-c", "copy",
        "-disposition:v:1", "attached_pic",
        "-movflags", "+faststart",
        str(tmp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("Cover embed fail:\n" + r.stderr[-1500:])
    tmp.replace(video)
    return video
