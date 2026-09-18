"""Tests for src/script_check.py and its effect on the verdict."""
from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pipeline  # noqa: E402
from script_check import (CONFUSABLES, MIXED_SCRIPT_REASON, find_mixed_script_words,  # noqa: E402
                          has_mixed_script)


def real_vzhh_row() -> str:
    """The genuine Verbraucherzentrale Hamburg smishing text from our collected data."""
    df = pd.read_csv(ROOT / "data" / "raw" / "german_phishing.csv", dtype=str, keep_default_na=False)
    hits = df[df.source_url.str.contains("vzhh.de", na=False) & df.text.str.contains(r"[Ѐ-ӿ]")]
    if hits.empty:
        pytest.skip("no mixed-script row in german_phishing.csv")
    return hits.iloc[0].text


# --- detection ---------------------------------------------------------------
def test_real_verbraucherzentrale_example_is_detected():
    text = real_vzhh_row()
    found = find_mixed_script_words(text)
    assert found, "the real smishing text must be flagged"
    words = {m.word for m in found}
    assert any(m.normalised == "Hallo" for m in found), words
    assert any(m.normalised.lower().startswith("dass") or m.normalised == "nicht" for m in found), words


def test_cyrillic_lookalikes_flagged():
    found = find_mixed_script_words("Ihr Pakеt wartet")      # Cyrillic е
    assert [m.word for m in found] == ["Pakеt"]
    assert found[0].normalised == "Paket"
    assert found[0].chars == ("е",)


def test_greek_lookalikes_flagged():
    assert has_mixed_script("Bitte bestätigen Sie Ihr Κοnto")   # Greek Ο and ο


@pytest.mark.parametrize("word", ["Hаllo", "niсht", "Kоnto", "рaypal", "Steuеr"])
def test_single_confusable_is_enough(word):
    assert has_mixed_script(f"Guten Tag {word} bitte")


# --- no false alarms ---------------------------------------------------------
@pytest.mark.parametrize("text", [
    "Hallo Oma, ich komme am Sonntag zum Kaffee.",
    "Grüße von der Straße – schöne Füße, 30 % Rabatt!",
    "DHL: Ihre Sendung wird heute zugestellt. https://www.dhl.de/verfolgen",
    "Sparkasse: Ihr Kontoauszug steht bereit.",
    "",
])
def test_plain_german_is_clean(text):
    assert not has_mixed_script(text)


def test_pure_cyrillic_word_is_not_mixed():
    # a genuinely Russian word has no Latin letters, so nothing is being disguised
    assert not has_mixed_script("Привет, как дела?")


def test_confusable_table_maps_to_latin():
    assert all(v.isascii() and v.isalpha() for v in CONFUSABLES.values())


# --- effect on the verdict ---------------------------------------------------
def _fix_score(monkeypatch, p: float) -> None:
    monkeypatch.setattr(pipeline.get_classifier(), "_predict", lambda text: p)


def test_mixed_script_lifts_green_to_yellow(monkeypatch):
    _fix_score(monkeypatch, 0.05)
    r = pipeline.analyze("Guten Tag, Ihr Pakеt ist unterwegs.")
    assert r["verdict"] == "yellow"
    assert r["reason_de"] == MIXED_SCRIPT_REASON
    assert r["mixed_script"] == ["Pakеt"]


def test_same_text_without_homoglyph_stays_green(monkeypatch):
    _fix_score(monkeypatch, 0.05)
    r = pipeline.analyze("Guten Tag, Ihr Paket ist unterwegs.")
    assert r["verdict"] == "green"
    assert r["mixed_script"] == []


def test_red_verdict_keeps_its_stronger_reason(monkeypatch):
    _fix_score(monkeypatch, 0.05)
    r = pipeline.analyze("Ihr Pakеt: https://dhl-paket-service.top/track")
    assert r["verdict"] == "red"
    assert "DHL" in r["reason_de"]
    assert r["mixed_script"] == ["Pakеt"]          # still reported to the UI


def test_trusted_link_cap_does_not_swallow_mixed_script(monkeypatch):
    _fix_score(monkeypatch, 0.85)
    r = pipeline.analyze("Ihr Pakеt: https://www.dhl.de/de/privatkunden/verfolgen.html")
    assert r["verdict"] == "red", "the cap must not downgrade a homoglyph message"


def test_reason_fits_the_budget():
    assert len(MIXED_SCRIPT_REASON) <= 120
