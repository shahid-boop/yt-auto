"""End-to-end daily pipeline: topic -> script -> voice -> slides -> video -> upload.

Examples:
  python -m src.pipeline --topic "AI tips"          # local test, no upload
  python -m src.pipeline --offline                   # no OpenAI key needed
  python -m src.pipeline --upload                    # build + upload
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import build_video, script_generator, visuals, voiceover  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "out"
WORK = ROOT / "work"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def pick_topic(history: list[dict[str, Any]]) -> str:
    topics = load_json(DATA / "topics.json", [])
    if not topics:
        raise RuntimeError("data/topics.json khali hai.")
    recent = {h.get("topic") for h in history[-5:]}
    fresh = [t for t in topics if t not in recent]
    return random.choice(fresh or topics)


def run(args: argparse.Namespace) -> dict[str, Any]:
    cfg = load_yaml(Path(args.config).resolve() if args.config else ROOT / "config.yaml")
    history_path = DATA / "history.json"
    history = load_json(history_path, [])

    topic = args.topic or pick_topic(history)
    print(f"[1/6] Topic: {topic}")

    if args.offline:
        script = script_generator.generate_offline(topic, cfg)
    else:
        script = script_generator.generate(topic, cfg)
    print(f"[2/6] Title: {script['title']}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    work = WORK / f"run_{stamp}"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    lines = script["voiceover"]
    captions = script["slides"]
    print(f"[3/6] Voiceover ({len(lines)} lines)...")
    audios = voiceover.synthesize(lines, cfg, work)

    print("[4/6] Slides...")
    segments: list[dict[str, Any]] = []
    for i, audio in enumerate(audios):
        image = work / f"slide_{i:03d}.png"
        visuals.render_slide(captions[i], i, len(lines), cfg, image)
        segments.append(
            {
                "image": image,
                "audio": audio["path"],
                "duration": audio["duration"],
                "caption": captions[i],
            }
        )

    print("[5/6] Rendering video...")
    video = build_video.build(segments, cfg, OUT / f"video_{stamp}.mp4", work)
    size_mb = video.stat().st_size / (1024 * 1024)
    print(f"       {video} ({size_mb:.1f} MB)")

    result: dict[str, Any] = {
        "time": stamp,
        "topic": topic,
        "title": script["title"],
        "video": str(video),
        "size_mb": round(size_mb, 2),
        "uploaded": False,
    }

    if args.upload:
        from src import upload  # lazy: local offline test ke liye google libs zaroori nahi

        print("[6/6] Uploading to YouTube...")
        result["url"] = upload.upload(video, script, cfg)
        result["uploaded"] = True
        print(f"       {result['url']}")
    else:
        print("[6/6] Upload skip (--upload nahi diya).")

    history.append(result)
    history_path.write_text(
        json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if not args.keep_work:
        shutil.rmtree(work, ignore_errors=True)

    print("\n=== SUMMARY ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily YouTube video pipeline")
    parser.add_argument("--topic", help="Custom topic (warna auto pick)")
    parser.add_argument("--config", help="Custom config.yaml path")
    parser.add_argument("--offline", action="store_true", help="OpenAI API use na karein")
    parser.add_argument("--upload", action="store_true", help="YouTube pe upload karein")
    parser.add_argument("--keep-work", action="store_true", help="Intermediate files rakhein")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
