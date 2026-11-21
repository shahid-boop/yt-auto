"""Render slide images with ffmpeg drawtext — no Pillow needed."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def find_font(cfg: dict[str, Any]) -> str:
    for candidate in cfg["visual"].get("font_candidates", []):
        if Path(candidate).exists():
            return candidate
    raise RuntimeError("Koi font nahi mila. config.yaml me font_candidates check karein.")


def _color(value: str) -> str:
    return "0x" + value.lstrip("#").upper()


def _wrap(text: str, max_chars: int = 26) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        if len(current) + len(word) + 1 <= max_chars or not current:
            current = f"{current} {word}".strip()
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:4]


def _textfile(work: Path, name: str, text: str) -> str:
    path = work / f"tf_{name}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def render_slide(
    text: str,
    index: int,
    total: int,
    cfg: dict[str, Any],
    out_path: Path,
) -> None:
    v = cfg["visual"]
    w, h = int(v["width"]), int(v["height"])
    margin = 84
    font = find_font(cfg)
    accent = _color(v.get("accent", "#38bdf8"))
    bg = _color(v.get("background", ["#0f172a"])[0])
    work = out_path.parent

    lines = _wrap(text)
    main_file = _textfile(work, f"main_{index:03d}", "\n".join(lines))
    kicker_file = _textfile(work, "kicker", str(v.get("kicker", "DAILY LEARNING")))
    channel_file = _textfile(work, "channel", cfg["channel"]["name"])
    counter_file = _textfile(work, f"count_{index:03d}", f"{index + 1:02d} / {total:02d}")

    def dt(textfile: str, size: int, color: str, x: str, y: str, extra: str = "") -> str:
        return (
            f"drawtext=fontfile={font}:textfile={textfile}:fontsize={size}:"
            f"fontcolor={color}:x={x}:y={y}{extra}"
        )

    frac = (index + 1) / max(1, total)
    filters = [
        f"drawbox=x={margin}:y=66:w=64:h=8:color={accent}:t=fill",
        dt(kicker_file, 26, accent, str(margin + 84), "52"),
        dt(main_file, 60, _color(v.get("text_color", "#ffffff")),
           "(w-text_w)/2", "(h-text_h)/2", ":line_spacing=18"),
        dt(channel_file, 24, "0xC8D2E6", str(margin), str(h - 70)),
        dt(counter_file, 24, "0xC8D2E6", "w-text_w-84", str(h - 70)),
        f"drawbox=x={margin}:y={h - 30}:w={w - margin * 2}:h=6:color=0x3C4A69:t=fill",
        f"drawbox=x={margin}:y={h - 30}:w=(iw-{margin * 2})*{frac:.5f}:h=6:color={accent}:t=fill",
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={bg}:s={w}x{h}",
        "-frames:v", "1",
        "-vf", ",".join(filters),
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("ffmpeg slide render fail:\n" + result.stderr[-2000:])
