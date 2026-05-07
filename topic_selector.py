"""
topic_selector.py — Mövzu seçimi.
İstifadə edilməmiş mövzuları izləyir, növbətiyi seçir.
"""

import json
import os
import random
from datetime import date

TOPIC_POOL_PATH = "topic_pool.json"
USED_TOPICS_PATH = "used_topics.json"


def _load_pool() -> list[dict]:
    with open(TOPIC_POOL_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_used() -> list[dict]:
    if not os.path.exists(USED_TOPICS_PATH):
        return []
    with open(USED_TOPICS_PATH, encoding="utf-8") as f:
        return json.load(f)


def mark_used(topic: dict) -> None:
    used = _load_used()
    used.append({
        "id": topic["id"],
        "title": topic["title"],
        "date": str(date.today()),
    })
    with open(USED_TOPICS_PATH, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def pick_topic() -> dict:
    pool = _load_pool()
    used_ids = {u["id"] for u in _load_used()}
    available = [t for t in pool if t["id"] not in used_ids]

    if not available:
        print("⚠️  Bütün mövzular istifadə edilib — sıfırlanır.")
        with open(USED_TOPICS_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        available = pool

    return random.choice(available)
