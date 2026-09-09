"""End-to-end verdict: text -> classifier probability + URL check + urgency -> traffic light.

    analyze(text) -> {"verdict", "score", "reason_de", "urls", "model"}

Model fallback: models/distilbert/ if present locally, else models/baseline.joblib.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from url_check import check_url, extract_urls  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DISTILBERT_DIR = ROOT / "models" / "distilbert"
BASELINE_PATH = ROOT / "models" / "baseline.joblib"

RED_P, YELLOW_P = 0.80, 0.50
URGENCY_DE = ["sofort", "innerhalb von 24 stunden", "konto gesperrt", "konto wird gesperrt",
              "eingeschränkt", "verifizieren", "zustellung fehlgeschlagen",
              "konnte nicht zugestellt werden", "zollgebühr", "gewinn", "letzte mahnung", "dringend"]
URGENCY_EN = ["urgent", "verify your account", "suspended", "claim", "prize"]
MAX_REASON_LEN = 120
_LEVEL_RANK = {"green": 0, "yellow": 1, "red": 2}


# ---------------------------------------------------------------------------
# Classifier with fallback
# ---------------------------------------------------------------------------
class Classifier:
    """Wraps either the fine-tuned DistilBERT or the TF-IDF baseline."""

    def __init__(self):
        self.name, self._predict = self._load()
        print(f"[pipeline] aktives Modell: {self.name}", flush=True)

    def _load(self):
        if (DISTILBERT_DIR / "config.json").exists():
            try:
                from transformers import pipeline as hf_pipeline
                clf = hf_pipeline("text-classification", model=str(DISTILBERT_DIR),
                                  tokenizer=str(DISTILBERT_DIR), device=-1, truncation=True, max_length=128)

                def predict(text: str) -> float:
                    scores = {d["label"]: d["score"] for d in clf(text, top_k=None)}
                    return float(scores.get("LABEL_1", scores.get("1", 0.0)))
                return "distilbert_multilingual", predict
            except Exception as e:
                print(f"[pipeline] DistilBERT nicht ladbar ({type(e).__name__}: {e}) – Fallback Baseline")
        if not BASELINE_PATH.exists():
            raise FileNotFoundError(f"{BASELINE_PATH} fehlt – bitte zuerst src/train_baseline.py ausführen")
        pipe = joblib.load(BASELINE_PATH)
        return "baseline_tfidf_logreg", lambda text: float(pipe.predict_proba([text])[0][1])

    def phishing_probability(self, text: str) -> float:
        return self._predict(text)


_classifier: Classifier | None = None


def get_classifier() -> Classifier:
    global _classifier
    if _classifier is None:
        _classifier = Classifier()
    return _classifier


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def find_urgency(text: str) -> list[str]:
    low = text.lower()
    return [p for p in URGENCY_DE + URGENCY_EN if p in low]


def worst_level(levels: list[str]) -> str:
    return max(levels, key=_LEVEL_RANK.get) if levels else "green"


def _brand_from_reasons(url_results: list[dict]) -> str | None:
    for r in url_results:
        for reason in r["reasons"]:
            m = re.search(r"als (.+?) aus|wie (.+?), ist|Namen von (.+?) \(", reason)
            if m:
                return next(g for g in m.groups() if g)
    return None


def _fit(sentence: str) -> str:
    if len(sentence) <= MAX_REASON_LEN:
        return sentence
    return sentence[: MAX_REASON_LEN - 1].rstrip(" ,;–-") + "."


def build_reason(verdict: str, p: float, url_results: list[dict], urgency: list[str]) -> str:
    """One plain-German sentence (<= 120 chars), no jargon, no percentages."""
    url_level = worst_level([r["level"] for r in url_results])
    brand = _brand_from_reasons(url_results)
    blocklisted = any("Phishing-Liste" in x for r in url_results for x in r["reasons"])
    if verdict == "red":
        if brand:
            return _fit(f"Vorsicht – diese Nachricht gibt sich als {brand} aus und der Link führt zu einer unbekannten Seite.")
        if blocklisted:
            return "Vorsicht – der Link in dieser Nachricht ist als Betrugsseite bekannt. Nicht antippen."
        if url_level == "red":
            return "Vorsicht – der Link in dieser Nachricht führt zu einer gefälschten Seite. Nicht antippen."
        return "Vorsicht – diese Nachricht sieht stark nach Betrug aus. Nichts antippen, nichts eingeben."
    if verdict == "yellow":
        if url_level == "yellow":
            return "Achtung – der Link in dieser Nachricht ist ungewöhnlich. Lieber nicht antippen."
        if urgency:
            return _fit(f"Achtung – die Nachricht macht Druck („{urgency[0]}“). Echte Firmen drängen so nicht.")
        return "Achtung – diese Nachricht könnte Betrug sein. Im Zweifel direkt bei der Firma nachfragen."
    return "Sieht unbedenklich aus. Bleiben Sie trotzdem aufmerksam bei Links und Zahlungen."


def analyze(text: str) -> dict:
    """Full verdict for one message text."""
    text = (text or "").strip()
    clf = get_classifier()
    urls = extract_urls(text)
    url_results = [{"url": u, **check_url(u)} for u in urls]
    url_level = worst_level([r["level"] for r in url_results])
    urgency = find_urgency(text)
    p = clf.phishing_probability(text) if text else 0.0

    if p >= RED_P or url_level == "red":
        verdict = "red"
    elif p >= YELLOW_P or url_level == "yellow" or urgency:
        verdict = "yellow"
    else:
        verdict = "green"

    return {
        "verdict": verdict,
        "score": round(p, 4),
        "reason_de": build_reason(verdict, p, url_results, urgency),
        "urls": url_results,
        "model": clf.name,
    }


if __name__ == "__main__":
    import json
    msg = " ".join(sys.argv[1:]) or "DHL: Ihr Paket wartet. Adresse bestätigen: http://dhl-paket-service.top/track"
    print(json.dumps(analyze(msg), ensure_ascii=False, indent=2))
