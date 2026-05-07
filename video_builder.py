"""
video_builder.py — Pexels arka planı + TTS audio + altyazı ilə TikTok videosu qurur.
Format: 1080x1920 (9:16), 30fps, H.264
"""

import os
import re
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
OUTPUT_DIR = "output"
VIDEO_W = 1080
VIDEO_H = 1920
FONT_SIZE = 54
SUBTITLE_Y_OFFSET = 380   # videounun altından px məsafəsi

# System font yolları (Ubuntu/GitHub Actions)
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",  # macOS
]


# ─────────────────────────── Pexels ─────────────────────────────────────────

def _download_pexels_video(keyword: str) -> str | None:
    """Pexels-dən portret formatında video yükləyir."""
    if not PEXELS_API_KEY:
        print("   ⚠️  PEXELS_API_KEY yoxdur — qaranlıq arxa fon istifadə olunur.")
        return None

    headers = {"Authorization": PEXELS_API_KEY}
    for orientation in ("portrait", "landscape"):
        params = {
            "query": keyword,
            "per_page": 5,
            "orientation": orientation,
            "size": "medium",
        }
        r = requests.get(
            "https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15
        )
        if r.status_code != 200:
            continue

        videos = r.json().get("videos", [])
        for video in videos:
            for vf in video.get("video_files", []):
                if vf.get("width", 0) >= 720:
                    url = vf["link"]
                    path = os.path.join(OUTPUT_DIR, "background.mp4")
                    print(f"   Pexels video yüklənir: {url[:60]}...")
                    with requests.get(url, stream=True, timeout=60) as resp:
                        with open(path, "wb") as f:
                            for chunk in resp.iter_content(chunk_size=65536):
                                f.write(chunk)
                    return path

    print(f"   ⚠️  '{keyword}' üçün Pexels videosu tapılmadı.")
    return None


# ─────────────────────────── VTT Parser ─────────────────────────────────────

def _vtt_time_to_sec(s: str) -> float:
    parts = s.split(":")
    h, m, sec = int(parts[0]), int(parts[1]), float(parts[2].replace(",", "."))
    return h * 3600 + m * 60 + sec


def _parse_vtt(vtt_path: str, words_per_chunk: int = 6) -> list[dict]:
    """VTT faylını oxuyur, sözləri qruplara bölür."""
    with open(vtt_path, encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*\n(.+?)(?=\n\n|\Z)",
        re.DOTALL,
    )
    words = []
    for m in pattern.finditer(content):
        words.append({
            "start": _vtt_time_to_sec(m.group(1)),
            "end": _vtt_time_to_sec(m.group(2)),
            "text": m.group(3).strip(),
        })

    if not words:
        return []

    chunks, buf, buf_start = [], [], None
    for w in words:
        if buf_start is None:
            buf_start = w["start"]
        buf.append(w["text"])
        if len(buf) >= words_per_chunk:
            chunks.append({"start": buf_start, "end": w["end"], "text": " ".join(buf)})
            buf, buf_start = [], None

    if buf and buf_start is not None:
        chunks.append({"start": buf_start, "end": words[-1]["end"], "text": " ".join(buf)})

    return chunks


# ─────────────────────────── Altyazı Klipi ──────────────────────────────────

def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(text: str, font, draw, max_width: int) -> list[str]:
    words = text.split()
    lines, line = [], []
    for word in words:
        test = " ".join(line + [word])
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] > max_width and line:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))
    return lines


def _make_subtitle_clip(text: str, start: float, end: float) -> ImageClip:
    duration = max(end - start, 0.1)
    pad = 60
    img = Image.new("RGBA", (VIDEO_W, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(FONT_SIZE)

    lines = _wrap_text(text, font, draw, VIDEO_W - pad * 2)
    line_h = FONT_SIZE + 10
    total_h = len(lines) * line_h
    y = (300 - total_h) // 2

    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        x = (VIDEO_W - (bb[2] - bb[0])) // 2
        # Kölgə
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 210))
        # Əsas mətn
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_h

    arr = np.array(img)
    clip = (
        ImageClip(arr, duration=duration)
        .set_start(start)
        .set_position(("center", VIDEO_H - SUBTITLE_Y_OFFSET))
    )
    return clip


# ─────────────────────────── Əsas Funksiya ──────────────────────────────────

def build_video(mp3_path: str, vtt_path: str, topic: dict) -> str:
    """
    TikTok üçün tam video qurur.
    Returns: output/tiktok.mp4 yolu
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "tiktok.mp4")

    # Audio
    audio = AudioFileClip(mp3_path)
    duration = audio.duration

    # Arxa plan
    keywords = topic.get("keywords", ["dark", "abstract"])
    bg_path = _download_pexels_video(keywords[0])

    if bg_path:
        raw_bg = VideoFileClip(bg_path).without_audio()

        # Lazım olduğu qədər uzat
        if raw_bg.duration < duration:
            loops = int(duration / raw_bg.duration) + 1
            raw_bg = concatenate_videoclips([raw_bg] * loops)
        raw_bg = raw_bg.subclip(0, duration)

        # 9:16 crop
        src_ratio = raw_bg.w / raw_bg.h
        tgt_ratio = VIDEO_W / VIDEO_H
        if src_ratio > tgt_ratio:
            new_w = int(raw_bg.h * tgt_ratio)
            raw_bg = raw_bg.crop(x_center=raw_bg.w / 2, width=new_w)
        else:
            new_h = int(raw_bg.w / tgt_ratio)
            raw_bg = raw_bg.crop(y_center=raw_bg.h / 2, height=new_h)

        bg = raw_bg.resize((VIDEO_W, VIDEO_H))
    else:
        # Qaranlıq arxa fon
        bg = ColorClip(size=(VIDEO_W, VIDEO_H), color=[10, 10, 10], duration=duration)

    # Altyazı
    chunks = _parse_vtt(vtt_path)
    subtitle_clips = [
        _make_subtitle_clip(c["text"], c["start"], c["end"])
        for c in chunks
        if c["end"] > c["start"]
    ]

    # Kompozit
    all_layers = [bg] + subtitle_clips
    final = (
        CompositeVideoClip(all_layers, size=(VIDEO_W, VIDEO_H))
        .set_audio(audio)
        .set_duration(duration)
    )

    print(f"   Video render edilir → {output_path}")
    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=os.path.join(OUTPUT_DIR, "temp_audio.m4a"),
        remove_temp=True,
        logger=None,
    )

    audio.close()
    bg.close()

    return output_path
