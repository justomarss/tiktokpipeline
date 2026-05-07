"""
script_gen.py — Claude API ilə Azərbaycan dilindəpsixologiya/fəlsəfə ssenarisiyazar.
"""

import json
import os
import re

import anthropic

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


SYSTEM_PROMPT = """Sən Azərbaycan dilindəpsixologiya və fəlsəfə mövzularında viral TikTok videoları üçün ssenari yazan mütəxəssissiniz.

Stilin:
- Güclü, şok edici açılış
- Sadə, axıcı Azərbaycan ədəbi dili (lakin quru akademik deyil)
- Real həyatdan konkret nümunələr
- Bir psixoloji/fəlsəfi termin — izah edilmiş şəkildə
- İzləyicini düşündürən son sual

Format: YALNIZ JSON cavab ver. Heç bir izahat, Markdown, kod blokundan kənar mətn olmayacaq."""


def generate_script(topic: dict) -> dict:
    """Verilən mövzu üçün TikTok ssenarisini yaradır."""

    user_prompt = f"""Mövzu: {topic['title']}
Qeyd: {topic['description']}

60 saniyelik TikTok ssenarisini aşağıdakı JSON formatında yaz:

{{
  "hook": "İlk 6-8 saniyə. Provokativ sual və ya şok faktı. Maksimum 2 cümlə.",
  "content": "8-50 saniyə. Əsas konsept — sadə dildə, bir nümunə ilə. Psixoloji/fəlsəfi termini izah et.",
  "cta": "50-60 saniyə. İzləyicini şərh yazmağa sövq edən sual.",
  "full_text": "Hook + Content + CTA — aralarında natural keçişlə tam mətni. TTS üçün istifadə olunacaq.",
  "hashtags": ["#psixologiya", "#fəlsəfə", "#azərbaycan", "mövzuya uyğun 4-5 əlavə hashtag"]
}}

Tələblər:
- Maksimum 140-160 söz (full_text üçün)
- Hook şok edici olsun
- Azərbaycan izləyicisini cəlb etsin
- Heç bir Markdown, yalnız JSON"""

    resp = _get_client().messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = resp.content[0].text.strip()

    # JSON-u çıxar
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"JSON tapılmadı. Model cavabı:\n{raw}")

    return json.loads(match.group())


def save_script(script: dict, path: str = "output/script.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
