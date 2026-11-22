"""Generate video script + upload metadata from Gemini (free) or OpenAI."""
from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

from .env_loader import load_env

SYSTEM_PROMPT = """You are a viral faceless YouTube Shorts writer for an Urdu-speaking audience.
You specialise in psychology / human-behaviour shorts with very high retention.
Rules you never break:
- Line 1 must be a curiosity-gap hook that works in the first 2 seconds.
- Every line is 1-2 short sentences. No long explanations.
- Insert a twist ('lekin...', 'asli baat yeh hai...', 'sabse ajeeb baat...') every 2-3 lines.
- End with a question-based CTA to drive comments.
- Simple, correct, non-controversial claims only. No medical/legal/financial advice.
- Return STRICT JSON only — no markdown, no commentary, no emoji."""


def _clean_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def _build_prompt(topic: str, cfg: dict[str, Any], n: int) -> str:
    content = cfg["content"]
    return f"""Channel niche: {content['niche']}
Audience: {content['audience']}
Tone: {content['tone']}
Video length: about {content['video_seconds']} seconds
Topic: {topic}

Write one complete short video. Return ONLY this JSON shape:
{{
  "title": "catchy title under 60 characters",
  "description": "2-3 short lines describing the video",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "voiceover": ["line 1", "line 2", ... exactly {n} lines],
  "slides": ["on-screen line 1", ... exactly {n} lines]
}}

STRICT RULES:
- "voiceover" lines MUST be in Pakistani Urdu, written in Urdu script, with everyday Pakistani vocabulary (جیسے: بالکل، زیادہ، پرسکون، ضرور، سمجھیں، بس، مگر). Avoid formal Hindi/Indian words. Natural conversational spoken style.
- "slides" lines MUST be in {content['slide_text_language']}, maximum 8 words each.
- Exactly {n} voiceover lines and exactly {n} slides, in the same order.
- Line 1 = curiosity-gap hook like "Kya aap ne kabhi notice kiya..." or "Log yeh baat aapko kabhi nahi batayenge...".
- Line 3 or 4 must be a twist starting with "Lekin..." or "Asli baat yeh hai...".
- Last line = question + call to action: {content['cta']}
- Each spoken line should be 1-2 sentences, roughly {max(5, int(content['video_seconds'] / n))} seconds when spoken.
- No emojis, no markdown, no "Here is your script" style preamble.
- Do not repeat the same idea in two lines.
- No false facts, no medical/legal/financial claims."""


def _call_openai(prompt: str, cfg: dict[str, Any]) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY set nahi hai (secrets/.env dekhein).")
    base = cfg["openai"]["base_url"].rstrip("/")
    payload: dict[str, Any] = {
        "model": cfg["openai"]["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.85,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = base + "/chat/completions"
    try:
        r = requests.post(
            url,
            headers=headers,
            json={**payload, "response_format": {"type": "json_object"}},
            timeout=120,
        )
        if r.status_code == 400:
            raise ValueError("response_format unsupported")
        r.raise_for_status()
    except (ValueError, requests.RequestException):
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _call_gemini(prompt: str, cfg: dict[str, Any]) -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY set nahi hai (secrets/.env dekhein).")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={key}"
    )
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.85,
            "responseMimeType": "application/json",
        },
    }
    r = requests.post(url, json=body, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini API error {r.status_code}: {r.text[:500]}")
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Gemini response unexpected: {str(data)[:500]}") from exc


def generate(topic: str, cfg: dict[str, Any]) -> dict[str, Any]:
    """Call configured LLM and return a validated script dict."""
    load_env()
    content = cfg["content"]
    n = max(5, min(9, int(content.get("line_count", 7))))
    prompt = _build_prompt(topic, cfg, n)
    provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    try:
        raw = _call_gemini(prompt, cfg) if provider == "gemini" else _call_openai(prompt, cfg)
        return _validate(_clean_json(raw), n, topic)
    except Exception as exc:  # quota, network, bad JSON — system must still produce a video
        print(f"[warn] LLM generation fail ({str(exc)[:160]}). Offline template use ho raha hai.")
        return generate_offline(topic, cfg)


def generate_offline(topic: str, cfg: dict[str, Any]) -> dict[str, Any]:
    """No-API fallback. Useful for a first local test."""
    n = max(5, min(9, int(cfg["content"].get("line_count", 7))))
    # Urdu script me — Urdu TTS voice ko yahi natural lagta hai.
    hooks = [
        "کیا آپ نے کبھی محسوس کیا کہ کوئی آپ کی بات کاٹ کر بول اٹھتا ہے؟",
        "آج ہم بالکل سادہ طریقے سے یہ سمجھیں گے۔",
        "سب سے پہلے یہ جان لیں کہ یہ کوئی بے ادبی نہیں، بس ایک عادت ہے۔",
        "لیکن اصل بات یہ ہے کہ ایسے لوگ اپنی بات کو زیادہ اہم سمجھتے ہیں۔",
        "آپ کو بس پرسکون رہ کر اپنی بات مکمل کرنی ہے۔",
        "یہ ایک چھوٹا سا قدم ہے، مگر اثر بڑا ہوتا ہے۔",
        "اگلے ویڈیو کے لیے ضرور سبسکرائب کر دیں۔",
    ]
    slides = [
        "Kya aap ne socha?",
        "Aaj samajhte hain",
        "Ye koi badtameezi nahi",
        "Asli baat ye hai",
        "Perskoun rahein",
        "Ek chhota qadam",
        "Subscribe karein",
    ]
    while len(hooks) < n:
        hooks.insert(-1, "یہ بات آپ کے کام کی ضرور ثابت ہوگی۔")
        slides.insert(-1, "Ek aur tip")
    return {
        "title": f"{topic[:52]} | Shorts",
        "description": f"Is short me {topic} ke baare me simple tips.\n{cfg['content']['cta']}",
        "tags": cfg["channel"].get("default_tags", [])[:5],
        "voiceover": hooks[:n],
        "slides": slides[:n],
    }


def _validate(data: dict[str, Any], n: int, topic: str) -> dict[str, Any]:
    for key in ("title", "description", "voiceover", "slides"):
        if key not in data:
            raise ValueError(f"LLM response me '{key}' missing hai: {data}")

    voice = [str(x).strip() for x in data["voiceover"] if str(x).strip()]
    slides = [str(x).strip() for x in data["slides"] if str(x).strip()]
    if len(voice) < 3 or len(slides) < 3:
        raise ValueError("Bahut kam lines mili hain.")

    def fit(items: list[str]) -> list[str]:
        if len(items) > n:
            items = items[: n - 1] + [items[-1]]
        while len(items) < n:
            items.append(items[-1])
        return items

    tags = [str(t).strip() for t in data.get("tags", []) if str(t).strip()][:10]
    return {
        "title": str(data["title"]).strip()[:100] or topic[:100],
        "description": str(data["description"]).strip(),
        "tags": tags or ["shorts", "facts", "tips"],
        "voiceover": fit(voice),
        "slides": fit(slides),
    }
