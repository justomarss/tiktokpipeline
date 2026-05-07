"""
notifier.py — Telegram bildirişləri.
TELEGRAM_BOT_TOKEN və TELEGRAM_CHAT_ID mühit dəyişənləri lazımdır.
"""

import os
import requests

_BOT = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
_API = f"https://api.telegram.org/bot{_BOT}"


def _send(text: str) -> None:
    if not _BOT or not _CHAT:
        print("   ℹ️  Telegram konfiqurasiya edilməyib, bildiriş atlanır.")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{_BOT}/sendMessage",
            json={"chat_id": _CHAT, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception as e:
        print(f"   ⚠️  Telegram bildirişi göndərilmədi: {e}")


def send_success(topic_title: str, hook: str, publish_id: str) -> None:
    _send(
        f"✅ *Yeni TikTok videosu!*\n\n"
        f"📌 *Mövzu:* {topic_title}\n"
        f"🎣 *Hook:* {hook}\n"
        f"🔗 Publish ID: `{publish_id}`\n\n"
        f"#psixologiya #fəlsəfə #azerbaycan"
    )


def send_error(step: str, error: str) -> None:
    _send(
        f"❌ *Pipeline xətası!*\n\n"
        f"📍 *Addım:* `{step}`\n"
        f"💬 *Xəta:* {str(error)[:400]}"
    )
