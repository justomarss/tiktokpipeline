"""
tiktok_uploader.py — TikTok Content Posting API ilə video yükləyir.

Tələblər:
  - TIKTOK_ACCESS_TOKEN: TikTok Developer Portal-dan alınmış OAuth token
    (bax: QURULUM.md → TikTok hissəsi)

Qeyd: İlk testdə privacy_level = "SELF_ONLY" saxlanır.
      Hər şey işlədikdən sonra "PUBLIC_TO_EVERYONE" edin.
"""

import os
import time

import requests

TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN", "")
BASE_URL = "https://open.tiktokapis.com/v2"

# Yükləmə zamanı gözləmə (saniyə)
_MAX_WAIT = 120
_POLL_INTERVAL = 6


def upload_video(
    video_path: str,
    caption: str,
    hashtags: list[str],
    privacy: str = "SELF_ONLY",
) -> str:
    """
    Videoyu TikTok-a yükləyir.
    Returns: publish_id
    """
    if not TIKTOK_ACCESS_TOKEN:
        raise EnvironmentError("TIKTOK_ACCESS_TOKEN mühit dəyişəni qeyd edilməyib.")

    # Caption + hashtags (maks. 2200 simvol)
    full_caption = caption.strip()
    tags_str = " ".join(hashtags)
    if len(full_caption) + len(tags_str) + 1 <= 2200:
        full_caption = f"{full_caption}\n\n{tags_str}"
    full_caption = full_caption[:2200]

    file_size = os.path.getsize(video_path)
    headers = {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    # ── Addım 1: Init ────────────────────────────────────────────────────────
    init_body = {
        "post_info": {
            "title": full_caption,
            "privacy_level": privacy,
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1000,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,
            "total_chunk_count": 1,
        },
    }

    resp = requests.post(f"{BASE_URL}/post/publish/video/init/", headers=headers, json=init_body, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    err = data.get("error", {})
    if err.get("code", "ok") != "ok":
        raise RuntimeError(f"TikTok init xətası: {err}")

    publish_id: str = data["data"]["publish_id"]
    upload_url: str = data["data"]["upload_url"]
    print(f"   Publish ID: {publish_id}")

    # ── Addım 2: Video yüklə ─────────────────────────────────────────────────
    with open(video_path, "rb") as f:
        video_bytes = f.read()

    upload_headers = {
        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
        "Content-Length": str(file_size),
        "Content-Type": "video/mp4",
    }
    up_resp = requests.put(upload_url, headers=upload_headers, data=video_bytes, timeout=300)
    up_resp.raise_for_status()

    # ── Addım 3: Status yoxla ────────────────────────────────────────────────
    status_headers = {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    elapsed = 0
    while elapsed < _MAX_WAIT:
        time.sleep(_POLL_INTERVAL)
        elapsed += _POLL_INTERVAL

        st_resp = requests.post(
            f"{BASE_URL}/post/publish/status/fetch/",
            headers=status_headers,
            json={"publish_id": publish_id},
            timeout=15,
        )
        st_data = st_resp.json()
        status = st_data.get("data", {}).get("status", "")
        print(f"   Status: {status} ({elapsed}s)")

        if status == "PUBLISH_COMPLETE":
            return publish_id
        if "FAIL" in status.upper():
            raise RuntimeError(f"TikTok yükləmə uğursuz: {st_data}")

    raise TimeoutError("TikTok yükləmə zamanı bitdi (120s).")
