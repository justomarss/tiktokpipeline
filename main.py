"""
main.py — Psixologiya/Fəlsəfə TikTok Pipeline orkestratörü.

İstifadə:
  python main.py                     # Normal işləmə
  python main.py --dry-run           # TikTok-a yükləmədən test
  python main.py --topic "Nietzsche" # Mövzu adını override et
"""

import argparse
import json
import os
import sys
import traceback
from datetime import datetime

from topic_selector import pick_topic, mark_used
from script_gen import generate_script, save_script
from tts import generate_audio
from video_builder import build_video
from tiktok_uploader import upload_video
from notifier import send_success, send_error

OUTPUT_DIR = "output"


def _banner() -> None:
    print("=" * 55)
    print("  🧠 Psixologiya/Fəlsəfə TikTok Pipeline")
    print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)


def run(dry_run: bool = False, topic_override: str | None = None) -> None:
    _banner()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    step = "topic"
    topic = None

    try:
        # ── 1. Mövzu ─────────────────────────────────────────────────────────
        print("\n[1/5] 📌 Mövzu seçilir...")
        topic = pick_topic()
        if topic_override:
            topic["title"] = topic_override
        print(f"      → {topic['title']}")

        # ── 2. Ssenari ────────────────────────────────────────────────────────
        step = "script"
        print("\n[2/5] ✍️  Ssenari yazılır (Claude AI)...")
        script = generate_script(topic)
        save_script(script)
        print(f"      Hook: {script['hook'][:70]}...")

        # ── 3. Səs ────────────────────────────────────────────────────────────
        step = "tts"
        print("\n[3/5] 🎙️  Səs yaradılır (Edge TTS — az-AZ-BabekNeural)...")
        mp3_path, vtt_path = generate_audio(script["full_text"])

        # ── 4. Video ──────────────────────────────────────────────────────────
        step = "video"
        print("\n[4/5] 🎬 Video qurulur (1080×1920)...")
        video_path = build_video(mp3_path, vtt_path, topic)
        print(f"      → {video_path}")

        # ── 5. Yüklə ─────────────────────────────────────────────────────────
        step = "upload"
        if dry_run:
            print("\n[5/5] ⏭️  DRY-RUN — TikTok-a yüklənmir.")
            publish_id = "dry-run-00000"
        else:
            print("\n[5/5] 📤 TikTok-a yüklənir...")
            publish_id = upload_video(
                video_path=video_path,
                caption=script["hook"],
                hashtags=script.get("hashtags", ["#psixologiya", "#fəlsəfə", "#azerbaycan"]),
                privacy="SELF_ONLY",   # ← hazır olduqda PUBLIC_TO_EVERYONE edin
            )

        # ── Tamamla ──────────────────────────────────────────────────────────
        mark_used(topic)
        send_success(topic["title"], script["hook"], publish_id)

        # Son hesabat
        summary = {
            "date": datetime.now().isoformat(),
            "topic": topic["title"],
            "hook": script["hook"],
            "publish_id": publish_id,
            "video_path": video_path,
        }
        with open(os.path.join(OUTPUT_DIR, "last_run.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 55)
        print("  ✅ Pipeline uğurla tamamlandı!")
        print("=" * 55)

    except Exception as exc:
        print(f"\n❌ XƏTA ({step}): {exc}")
        traceback.print_exc()
        if topic:
            send_error(step, str(exc))
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Psixologiya TikTok Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="TikTok-a yükləmədən test")
    parser.add_argument("--topic", type=str, default=None, help="Mövzu adını override et")
    args = parser.parse_args()

    run(dry_run=args.dry_run, topic_override=args.topic)
