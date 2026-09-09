"""OCR for screenshots: easyocr, languages de+en, CPU only, reader loaded lazily.

    extract_text(image) -> str      image = path, PIL.Image or numpy array
    ocr_available() -> bool         False if easyocr or its weights are unavailable
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image

from url_check import UNCOMMON_TLDS

LANGS = ["de", "en"]
_reader = None


def get_reader():
    """Create the easyocr reader once (downloads weights on first use)."""
    global _reader
    if _reader is None:
        import easyocr  # imported lazily: heavy (torch) and optional in the sandbox
        _reader = easyocr.Reader(LANGS, gpu=False, verbose=False)
    return _reader


def ocr_available() -> bool:
    try:
        get_reader()
        return True
    except Exception as e:  # missing package, blocked weight download ...
        print(f"[ocr] nicht verfügbar: {type(e).__name__}: {e}")
        return False


def _to_array(image) -> np.ndarray:
    if isinstance(image, (str, Path)):
        image = Image.open(image)
    if isinstance(image, Image.Image):
        return np.array(image.convert("RGB"))
    return np.asarray(image)


_COMMON_TLDS = {"de", "com", "net", "org", "eu", "at", "ch", "info", "io", "me", "app", "shop"}
_TLD_ALT = "|".join(sorted(_COMMON_TLDS | UNCOMMON_TLDS, key=len, reverse=True))
_SCHEME_FIX = re.compile(r"\b(https?)\s*[:;]\s*[/l|I1]{2}(?=\S)", re.I)
_DOT_FIX = re.compile(r"(https?://[a-z0-9\-]+(?:\.[a-z0-9\-]+)*) +(?=(?:" + _TLD_ALT + r")(?:[/lI|][a-z0-9]|\b))", re.I)
_SLASH_FIX = re.compile(r"(https?://[a-z0-9.\-]+\.(?:" + _TLD_ALT + r"))[lI|](?=[a-z0-9])", re.I)


def fix_ocr_urls(text: str) -> str:
    """Repair three classic OCR confusions, only inside links (after http/https):
    1. 'http:ll'  -> 'http://'
    2. a dropped dot before a known domain ending: 'service top' -> 'service.top'
    3. a '/' read as 'l' right after the domain ending: 'service.topltrack' -> 'service.top/track'
    """
    text = _SCHEME_FIX.sub(lambda m: m.group(1).lower() + "://", text)
    text = _DOT_FIX.sub(r"\1.", text)
    return _SLASH_FIX.sub(r"\1/", text)


def extract_text(image) -> str:
    """Return the recognized text, one detected line per row."""
    lines = get_reader().readtext(_to_array(image), detail=0, paragraph=False)
    return fix_ocr_urls("\n".join(l.strip() for l in lines if l.strip()))


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        print(f"--- {p}\n{extract_text(p)}")
