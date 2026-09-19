"""Tests for src/pipeline.py (text path) and src/ocr.py (skipped if easyocr is unavailable)."""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pipeline  # noqa: E402
from make_samples import SAMPLES_TEXT  # noqa: E402

SAMPLES = ROOT / "data" / "samples"
DHL_TEXT = SAMPLES_TEXT["dhl_phishing.png"][2]
BANK_TEXT = SAMPLES_TEXT["bank_phishing.png"][2]
FAMILY_TEXT = SAMPLES_TEXT["family_ok.png"][2]


def _check_shape(result: dict) -> None:
    assert set(result) == {"verdict", "score", "reason_de", "urls", "mixed_script", "signale", "model"}
    assert result["verdict"] in ("red", "yellow", "green")
    assert 0.0 <= result["score"] <= 1.0
    assert 0 < len(result["reason_de"]) <= 120
    assert "%" not in result["reason_de"]
    assert result["model"] in ("baseline_tfidf_logreg", "distilbert_multilingual")
    assert isinstance(result["mixed_script"], list)


def test_red_dhl_phishing_with_fake_link():
    r = pipeline.analyze(DHL_TEXT)
    _check_shape(r)
    assert r["verdict"] == "red"
    assert r["urls"][0]["level"] == "red"
    assert "DHL" in r["reason_de"]


def test_red_bank_phishing():
    r = pipeline.analyze(BANK_TEXT)
    _check_shape(r)
    assert r["verdict"] == "red"
    assert "Sparkasse" in r["reason_de"]


def test_green_family_message():
    r = pipeline.analyze(FAMILY_TEXT)
    _check_shape(r)
    assert r["verdict"] == "green"
    assert r["urls"] == []
    assert r["score"] < 0.5


def test_yellow_from_urgency_phrase_only():
    r = pipeline.analyze("Bitte rufen Sie uns dringend zurück, es geht um Ihren Termin.")
    _check_shape(r)
    assert r["verdict"] == "yellow"
    assert r["score"] < 0.8
    assert "Druck" in r["reason_de"]


def _fix_score(monkeypatch, p: float) -> None:
    """Pin the classifier score so the verdict RULES are tested independently of the model."""
    monkeypatch.setattr(pipeline.get_classifier(), "_predict", lambda text: p)


def test_yellow_from_suspicious_link(monkeypatch):
    _fix_score(monkeypatch, 0.1)
    r = pipeline.analyze("Schau mal hier: https://bit.ly/3xYzAbc")
    _check_shape(r)
    assert r["urls"][0]["level"] == "yellow"
    assert r["verdict"] == "yellow"
    assert "Link" in r["reason_de"]


def test_yellow_from_probability_band(monkeypatch):
    _fix_score(monkeypatch, 0.65)
    r = pipeline.analyze("Guten Tag, wir melden uns wegen Ihrer Anfrage.")
    _check_shape(r)
    assert r["verdict"] == "yellow" and r["urls"] == []


OFFICIAL_LINK_TEXT = "DHL: Ihre Sendung kommt heute. Details: https://www.dhl.de/de/privatkunden/verfolgen.html"


def test_trusted_link_caps_red_at_yellow(monkeypatch):
    _fix_score(monkeypatch, 0.85)
    r = pipeline.analyze(OFFICIAL_LINK_TEXT)
    _check_shape(r)
    assert r["urls"][0]["trusted"] is True
    assert r["verdict"] == "yellow"
    assert "bekannten Seite" in r["reason_de"]


def test_trusted_link_cap_not_applied_above_090(monkeypatch):
    _fix_score(monkeypatch, 0.95)
    assert pipeline.analyze(OFFICIAL_LINK_TEXT)["verdict"] == "red"


def test_trusted_link_cap_not_applied_with_urgency(monkeypatch):
    _fix_score(monkeypatch, 0.85)
    assert pipeline.analyze(OFFICIAL_LINK_TEXT + " Bitte sofort bestätigen.")["verdict"] == "red"


def test_trusted_link_cap_not_applied_for_untrusted_link(monkeypatch):
    _fix_score(monkeypatch, 0.85)
    assert pipeline.analyze("Ihre Sendung: https://paket-info-service.de/track")["verdict"] == "red"


def test_red_from_probability_threshold(monkeypatch):
    _fix_score(monkeypatch, 0.8)
    assert pipeline.analyze("Guten Tag, wir melden uns wegen Ihrer Anfrage.")["verdict"] == "red"


def test_red_from_high_probability_english_spam():
    text = ("WINNER!! You have been selected to receive a £900 prize reward! "
            "To claim call 09061701461. Claim code KL341. Valid 12 hours only.")
    r = pipeline.analyze(text)
    _check_shape(r)
    assert r["score"] >= 0.8
    assert r["verdict"] == "red"


def test_find_urgency_is_case_insensitive():
    assert "konto gesperrt" in pipeline.find_urgency("Achtung: KONTO GESPERRT!")
    assert pipeline.find_urgency("Bis morgen!") == []


def test_worst_level():
    assert pipeline.worst_level([]) == "green"
    assert pipeline.worst_level(["green", "yellow"]) == "yellow"
    assert pipeline.worst_level(["yellow", "red", "green"]) == "red"


def test_empty_text_is_green():
    r = pipeline.analyze("")
    assert r["verdict"] == "green" and r["urls"] == []


def test_model_fallback_is_baseline_without_distilbert():
    if (ROOT / "models" / "distilbert" / "config.json").exists():
        pytest.skip("local distilbert present")
    assert pipeline.get_classifier().name == "baseline_tfidf_logreg"


# --- OCR ---------------------------------------------------------------------
ocr = pytest.importorskip("ocr")
_OCR_OK = ocr.ocr_available()
needs_ocr = pytest.mark.skipif(not _OCR_OK, reason="easyocr or its weights unavailable")


@needs_ocr
def test_ocr_reads_dhl_screenshot():
    text = ocr.extract_text(SAMPLES / "dhl_phishing.png")
    assert "dhl" in text.lower()
    assert "paket" in text.lower()


@needs_ocr
def test_ocr_screenshot_to_red_verdict():
    r = pipeline.analyze(ocr.extract_text(SAMPLES / "dhl_phishing.png"))
    assert r["verdict"] == "red", r


@needs_ocr
def test_ocr_family_screenshot_to_green_verdict():
    text = ocr.extract_text(SAMPLES / "family_ok.png")
    assert "kaffee" in text.lower()
    assert pipeline.analyze(text)["verdict"] == "green"


# --- explainability: the "signale" field -------------------------------------
SPAM_EN = ("WINNER!! You have been selected to receive a £900 prize reward! "
           "To claim call 09061701461 now.")
PHISH_DE = ("DHL: Ihr Paket konnte nicht zugestellt werden. Bitte bestätigen Sie "
            "Ihre Adresse: http://dhl-paket-service.top/track")


def _baseline_active() -> bool:
    return pipeline.get_classifier().name == "baseline_tfidf_logreg"


def test_signale_field_is_always_present():
    assert isinstance(pipeline.analyze("Hallo")["signale"], list)


def test_signals_are_words_from_the_message():
    if not _baseline_active():
        pytest.skip("signals are only produced by the TF-IDF baseline")
    signals = pipeline.analyze(PHISH_DE)["signale"]
    assert signals, "a clear phishing text must yield signals"
    low = PHISH_DE.lower()
    for s in signals:
        assert s.lower() in low, f"{s!r} is not part of the message"


def test_signals_respect_the_limit_and_the_filters():
    if not _baseline_active():
        pytest.skip("signals are only produced by the TF-IDF baseline")
    for text in (SPAM_EN, PHISH_DE):
        signals = pipeline.analyze(text)["signale"]
        assert len(signals) <= pipeline.MAX_SIGNALS
        assert all(s.lower() != "url" for s in signals), signals      # the <URL> token is hidden
        for s in signals:
            assert max(len(t) for t in s.split()) >= pipeline.MIN_SIGNAL_LEN, s
        assert len(signals) == len({s.lower() for s in signals}), "no duplicates"


def test_signals_do_not_repeat_the_same_word():
    if not _baseline_active():
        pytest.skip("signals are only produced by the TF-IDF baseline")
    signals = pipeline.analyze(PHISH_DE)["signale"]
    words = [w.lower() for s in signals for w in s.split()]
    assert len(words) == len(set(words)), signals


def test_no_signals_without_text():
    assert pipeline.analyze("")["signale"] == []


def test_masked_link_does_not_become_a_signal():
    if not _baseline_active():
        pytest.skip("signals are only produced by the TF-IDF baseline")
    signals = pipeline.analyze("Jetzt hier klicken: https://dhl-paket-service.top/track")["signale"]
    assert all("url" != s.lower() for s in signals), signals
