# 🧠 Psixologiya/Fəlsəfə TikTok Pipeline — Qurulum Bələdçisi

> Azərbaycan dilində psixologiya/fəlsəfə mövzularında hər gün avtomatik TikTok videosu yayımlayan sistem.

---

## İçindəkilər

1. [Sistem nə edir?](#1-sistem-nə-edir)
2. [Nə lazımdır?](#2-nə-lazımdır)
3. [Lokal Test (İlk Addım)](#3-lokal-test-ilk-addım)
4. [API Açarlarını Almaq](#4-api-açarlarını-almaq)
5. [GitHub Actions Kurulumu (Avtomatik)](#5-github-actions-kurulumu-avtomatik)
6. [TikTok Token Alma](#6-tiktok-token-alma)
7. [Faylların İzahı](#7-faylların-izahı)
8. [Tənzimləmələr](#8-tənzimləmələr)
9. [Xəta Giderme](#9-xəta-giderme)

---

## 1. Sistem nə edir?

Hər gün avtomatik olaraq:

1. `topic_pool.json`-dan yeni psixologiya/fəlsəfə mövzusu seçir
2. **Claude AI** ilə Azərbaycan dilində 60 saniyelik ssenari yazır
3. **Edge TTS** ilə `az-AZ-BabekNeural` səsi ilə MP3 yaradır
4. **Pexels**-dən uyğun arxa fon videosu yükləyir
5. **MoviePy** ilə altyazılı 1080×1920 TikTok videosu qurur
6. **TikTok API** ilə yükləyir
7. **Telegram**-a bildiriş göndərir

**Xərc:** Yalnız Claude API (aylıq ~2-5$). Qalanı tamamilə pulsuzdur.

---

## 2. Nə lazımdır?

| Şey | Haradan alınır | Ödənişli? |
|---|---|---|
| Anthropic API açarı | platform.anthropic.com | Pulsuz kreditlə başlayır |
| Pexels API açarı | pexels.com/api | Tamamilə pulsuz |
| TikTok Developer hesabı | developers.tiktok.com | Pulsuz |
| Telegram bot (bildiriş) | @BotFather | Pulsuz |
| GitHub hesabı | github.com | Pulsuz |
| Python 3.10+ | python.org | Pulsuz |
| FFmpeg | ffmpeg.org | Pulsuz |

---

## 3. Lokal Test (İlk Addım)

**ÖNƏMLİ:** Əvvəlcə öz kompüterinizdə test edin, sonra GitHub Actions-a keçin.

### 3.1 Repo-nu yükləyin

```bash
git clone https://github.com/SİZİN-USERNAME/psych-tiktok-pipeline.git
cd psych-tiktok-pipeline
```

### 3.2 Asılılıqları quraşdırın

```bash
# FFmpeg (əgər yoxdursa)
# Ubuntu/Debian:
sudo apt install ffmpeg fonts-dejavu

# macOS:
brew install ffmpeg

# Python paketlərini yüklə
pip install -r requirements.txt
```

### 3.3 Mühit dəyişənlərini qeyd edin

`.env` faylı yaradın (git-ə push ETMƏYIN):

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...
PEXELS_API_KEY=...
TIKTOK_ACCESS_TOKEN=...     # İlk testdə boş buraxın
TELEGRAM_BOT_TOKEN=...      # İlk testdə boş buraxın
TELEGRAM_CHAT_ID=...        # İlk testdə boş buraxın
```

Dəyişənləri export edin:

```bash
# Linux/macOS
export $(cat .env | xargs)

# Windows PowerShell
Get-Content .env | ForEach-Object {
    $k, $v = $_ -split '=', 2
    [Environment]::SetEnvironmentVariable($k, $v, 'Process')
}
```

### 3.4 Dry-run testi

```bash
python main.py --dry-run
```

Bu addım TikTok-a yükləmədən hər şeyi test edir. `output/tiktok.mp4` faylı yaranmalıdır.

---

## 4. API Açarlarını Almaq

### 4.1 Anthropic (Claude) API

1. [platform.anthropic.com](https://platform.anthropic.com) → Qeydiyyat
2. "API Keys" → "Create Key"
3. Açarı kopyalayın: `sk-ant-api03-...`

### 4.2 Pexels API

1. [pexels.com/api](https://www.pexels.com/api) → "Get Started"
2. Qeydiyyatdan sonra API açarınız dərhal verilir
3. Aylıq 200 video yükləmə pulsuz

### 4.3 Telegram Bot

1. Telegram-da `@BotFather`-ə yazın
2. `/newbot` → Ad verin → Token alın
3. Botunuza bir mesaj göndərin
4. `https://api.telegram.org/bot{TOKEN}/getUpdates` → `chat.id` tapın

---

## 5. GitHub Actions Kurulumu (Avtomatik)

### 5.1 Repo yaradın

GitHub-da yeni private repo yaradın, faylları push edin:

```bash
git init
git add .
git commit -m "ilk commit"
git remote add origin https://github.com/USERNAME/REPO-ADI.git
git push -u origin main
```

### 5.2 Secrets əlavə edin

`GitHub Repo → Settings → Secrets and variables → Actions → New repository secret`

| Secret Adı | Dəyər |
|---|---|
| `ANTHROPIC_API_KEY` | sk-ant-api03-... |
| `PEXELS_API_KEY` | Pexels açarınız |
| `TIKTOK_ACCESS_TOKEN` | TikTok token (aşağıda) |
| `TELEGRAM_BOT_TOKEN` | Bot token |
| `TELEGRAM_CHAT_ID` | Chat ID |

### 5.3 İlk manual işlətmə

`Actions → Daily TikTok Pipeline → Run workflow → dry_run: true → Run`

Nəticəni `Artifacts`-dən yükləyib videonu yoxlayın.

---

## 6. TikTok Token Alma

Bu addım bir az texniki, amma bir dəfədir.

### 6.1 TikTok Developer App yaradın

1. [developers.tiktok.com](https://developers.tiktok.com) → Login
2. "Manage apps" → "Create app"
3. App adı, açıqlama daxil edin
4. "Products" → "Content Posting API" əlavə edin
5. Redirect URI: `https://localhost`
6. **Client Key** və **Client Secret** alın

### 6.2 OAuth URL yaradın

Brauzerdə açın (CLIENT_KEY-i əvəz edin):

```
https://www.tiktok.com/v2/auth/authorize/?client_key=CLIENT_KEY&scope=video.publish,video.upload&response_type=code&redirect_uri=https://localhost&state=random123
```

TikTok hesabınıza icazə verin → `localhost`-a redirect olunacaq.
URL-dən `code=` parametrini kopyalayın.

### 6.3 Access Token alın

```bash
curl -X POST "https://open.tiktokapis.com/v2/oauth/token/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_key=CLIENT_KEY&client_secret=CLIENT_SECRET&code=CODE&grant_type=authorization_code&redirect_uri=https://localhost"
```

Cavabdan `access_token` dəyərini `TIKTOK_ACCESS_TOKEN` kimi saxlayın.

**Qeyd:** Token 24 saatda bir yenilənir. Uzunmüddətli istifadə üçün `refresh_token` ilə avtomatik yeniləmə əlavə edilə bilər.

---

## 7. Faylların İzahı

```
psych-pipeline/
├── main.py               ← Əsas orkestrator
├── topic_selector.py     ← Mövzu seçimi
├── script_gen.py         ← Claude AI ssenari yazır
├── tts.py                ← Edge TTS audio yaradır
├── video_builder.py      ← Pexels + MoviePy video
├── tiktok_uploader.py    ← TikTok API yükləmə
├── notifier.py           ← Telegram bildirişlər
├── topic_pool.json       ← 50+ mövzu bazası
├── used_topics.json      ← İşlənmiş mövzular (auto)
├── requirements.txt      ← Python asılılıqlar
└── .github/
    └── workflows/
        └── daily.yml     ← GitHub Actions (hər gün 08:00 UTC)
```

---

## 8. Tənzimləmələr

### Səs dəyişdirmək

`tts.py`-da və ya mühit dəyişənlə:

```bash
export TTS_VOICE=az-AZ-BanuNeural   # Qadın səsi
export TTS_VOICE=az-AZ-BabekNeural  # Kişi səsi (default)
```

### Yayım vaxtı dəyişdirmək

`.github/workflows/daily.yml`-da:

```yaml
- cron: "0 8 * * *"   # 08:00 UTC = 12:00 Bakı
- cron: "0 6 * * *"   # 06:00 UTC = 10:00 Bakı
```

### TikTok gizliliyi

`main.py`-da (`privacy` parametri):

```python
privacy="SELF_ONLY"        # Yalnız sən görürsən (test)
privacy="PUBLIC_TO_EVERYONE"  # Hamı görür (aktiv kanal)
```

### Yeni mövzular əlavə etmək

`topic_pool.json`-a əlavə edin:

```json
{
  "id": "unikal_id",
  "title": "Mövzunun başlığı",
  "description": "Qısa izah",
  "keywords": ["pexels üçün axtarış sözləri"],
  "category": "psychology"
}
```

---

## 9. Xəta Giderme

### `az-AZ-BabekNeural` səsi işləmir

```bash
edge-tts --list-voices | grep az
```

Azərbaycan dili görünmürsə Edge TTS-i yeniləyin:
```bash
pip install --upgrade edge-tts
```

### MoviePy xətası

FFmpeg quraşdırılıb-quraşdırılmadığını yoxlayın:
```bash
ffmpeg -version
```

### Pexels videosu tapılmır

`topic_pool.json`-da `keywords`-ü daha sadə İngilis sözlərə dəyişin:
```json
"keywords": ["dark", "nature", "abstract", "forest"]
```

### TikTok `401 Unauthorized`

Token vaxtı bitib. Yenidən [6. TikTok Token Alma](#6-tiktok-token-alma) addımından keçin.

---

## Uğurlar! 🚀

Suallar üçün: pipeline loqlarını `output/last_run.json`-dan yoxlayın.
