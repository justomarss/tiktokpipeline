"""
tts.py — Edge TTS ilə Azərbaycan dilində səs və altyazı fayli yaradır.
Səs: az-AZ-BabekNeural (kişi) və ya az-AZ-BanuNeural (qadın)
"""

import asyncio
import os

import edge_tts

VOICE = os.environ.get("TTS_VOICE", "az-AZ-BabekNeural")
OUTPUT_DIR = "output"


async def _generate_async(text: str, mp3_path: str, vtt_path: str) -> None:
    communicate = edge_tts.Communicate(text, VOICE)
    submaker = edge_tts.SubMaker()

    with open(mp3_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub(
                    (chunk["offset"], chunk["duration"]),
                    chunk["text"],
                )

    with open(vtt_path, "w", encoding="utf-8") as vtt_file:
        vtt_file.write(submaker.generate_subs())


def generate_audio(text: str) -> tuple[str, str]:
    """
    MP3 + VTT fayllarını yaradır.
    Returns: (mp3_path, vtt_path)
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    mp3_path = os.path.join(OUTPUT_DIR, "narration.mp3")
    vtt_path = os.path.join(OUTPUT_DIR, "narration.vtt")

    asyncio.run(_generate_async(text, mp3_path, vtt_path))

    print(f"   Səs: {mp3_path}")
    print(f"   Altyazı: {vtt_path}")
    return mp3_path, vtt_path
