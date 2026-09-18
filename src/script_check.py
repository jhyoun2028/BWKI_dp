"""Detect homoglyph evasion: words that mix Latin letters with Cyrillic or Greek look-alikes.

Spam filters match on words like "Paket". Writing it as "Pakеt" with a Cyrillic "е"
defeats a literal match while looking identical to a human reader. A word is only
flagged when it MIXES scripts – a genuinely Cyrillic or Greek word stays untouched.

    find_mixed_script_words(text) -> list[MixedWord]
    has_mixed_script(text) -> bool
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Confusable characters that look like a Latin letter but are not one.
# The Cyrillic "ѕ" (DZE) is included on top of the obvious set because it appears in
# our own collected Verbraucherzentrale sample ("daѕs", "verlaѕѕen").
CONFUSABLES: dict[str, str] = {
    # Cyrillic
    "а": "a", "е": "e", "о": "o", "с": "c", "р": "p", "і": "i", "х": "x", "ѕ": "s",
    "А": "A", "Е": "E", "О": "O", "С": "C", "Р": "P", "І": "I", "Х": "X",
    # Greek
    "ο": "o", "ε": "e", "α": "a", "Ο": "O", "Α": "A", "Ε": "E",
}

# Shown to the user (German, no jargon), fits the <= 120 character budget of reason_de.
MIXED_SCRIPT_REASON = (
    "Der Text enthält versteckte fremde Schriftzeichen – ein typischer Trick, "
    "um Spamfilter zu umgehen."
)

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
# Invisible characters are a second evasion trick and also split words apart, so that
# "P\u200d\u200dak\u0435t" would otherwise be reported as "ak\u0435t". Drop them before tokenising.
_ZERO_WIDTH = re.compile("[\u200b\u200c\u200d\u2060\ufeff\u00ad]")


@dataclass(frozen=True)
class MixedWord:
    """One suspicious word plus the confusable characters found in it."""
    word: str
    chars: tuple[str, ...]

    @property
    def normalised(self) -> str:
        """The word as it was probably meant to be read ("Pakеt" -> "Paket")."""
        return "".join(CONFUSABLES.get(c, c) for c in self.word)


def _is_latin(ch: str) -> bool:
    try:
        return unicodedata.name(ch).startswith("LATIN")
    except ValueError:
        return False


def find_mixed_script_words(text: str) -> list[MixedWord]:
    """Words containing at least one Latin letter AND at least one confusable character."""
    found: list[MixedWord] = []
    for word in _WORD.findall(_ZERO_WIDTH.sub("", text or "")):
        chars = tuple(dict.fromkeys(c for c in word if c in CONFUSABLES))
        if chars and any(_is_latin(c) for c in word):
            found.append(MixedWord(word, chars))
    return found


def has_mixed_script(text: str) -> bool:
    return bool(find_mixed_script_words(text))


if __name__ == "__main__":  # quick manual check
    import sys
    sample = " ".join(sys.argv[1:]) or "Hаllo, Ihr Pakеt konnte niсht zugestellt werden."
    for m in find_mixed_script_words(sample):
        print(f"{m.word!r} -> gemeint: {m.normalised!r}  (Zeichen: {' '.join(m.chars)})")
