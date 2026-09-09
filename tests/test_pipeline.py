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
    assert set(result) == {"verdict", "score", "reason_de", "urls", "model"}
    assert result["verdict"] in ("red", "yellow", "green")
    assert 0.0 <= result["score"] <= 1.0
    assert 0 < len(result["reason_de"]) <= 120
    assert "%" not in result["reason_de"]
    assert result["model"] in ("baseline_tfidf_logreg", "distilbert_multilingual")


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
