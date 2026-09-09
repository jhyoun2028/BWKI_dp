"""Render 3 phone-like sample screenshots (PNG) into data/samples/ with PIL.

    python src/make_samples.py
"""
from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "samples"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

SAMPLES_TEXT = {
    "dhl_phishing.png": (
        "DHL", "+49 1573 9921xxx",
        "DHL: Ihr Paket konnte nicht zugestellt werden. Bitte bestätigen Sie Ihre Adresse "
        "innerhalb von 24 Stunden: http://dhl-paket-service.top/track"),
    "bank_phishing.png": (
        "Sparkasse", "+49 176 4471xxx",
        "Sparkasse: Ihr Konto wurde eingeschränkt. Verifizieren Sie sich sofort unter "
        "https://sparkasse-sicherheit.de/verify sonst wird Ihr Konto gesperrt."),
    "family_ok.png": (
        "Lena", "Enkelin",
        "Hallo Oma, ich komme am Sonntag um 15 Uhr zum Kaffee. Soll ich Kuchen mitbringen? "
        "Liebe Grüße, Lena"),
}


def render(sender: str, sub: str, text: str, path: Path, size=(1080, 1920)) -> None:
    img = Image.new("RGB", size, "#f2f2f7")
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(FONT, 54)
    small = ImageFont.truetype(FONT, 36)
    body = ImageFont.truetype(FONT, 46)
    d.rectangle([0, 0, size[0], 220], fill="#ffffff")
    d.text((50, 60), sender, font=big, fill="#111111")
    d.text((50, 140), sub, font=small, fill="#777777")
    # URLs must stay on one line (no breaks at hyphens / inside words)
    lines = textwrap.wrap(text, width=36, break_on_hyphens=False, break_long_words=False)
    line_h = 64
    box_h = line_h * len(lines) + 60
    d.rounded_rectangle([40, 320, size[0] - 40, 320 + box_h], radius=36, fill="#ffffff")
    y = 350
    for line in lines:
        d.text((80, y), line, font=body, fill="#111111")
        y += line_h
    d.text((50, 340 + box_h + 24), "Heute 09:41", font=small, fill="#999999")
    img.save(path)


def main() -> None:
    SAMPLES.mkdir(parents=True, exist_ok=True)
    for name, (sender, sub, text) in SAMPLES_TEXT.items():
        render(sender, sub, text, SAMPLES / name)
        print(f"[samples] {SAMPLES.relative_to(ROOT) / name}")


if __name__ == "__main__":
    main()
