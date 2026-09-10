"""Experiments on the EXISTING splits: decision-threshold tuning and a simple ensemble.

For every available model:
  1. sweep the decision threshold on the VALIDATION set and pick the threshold with the
     highest recall subject to FPR <= MAX_FPR,
  2. evaluate once on the test set at that threshold (overall and German-only).
Then combine the models: phishing if ANY model scores above its own tuned threshold.

Results are APPENDED to results/metrics.json and results/experiments.csv.

    python src/tune_threshold.py

NOTE: val.csv contains English rows only (see data_prep.py), so the thresholds are tuned
on English data and then applied to the German test slice. That is a real limitation and
is reported in results/ and CLAUDE.md.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_baseline import (EXPERIMENTS_PATH, METRICS_PATH, PROCESSED, SEED,  # noqa: E402
                            log, metrics, strip_url_token)

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
DISTILBERT_DIR = MODELS / "distilbert"

THRESHOLDS = np.round(np.arange(0.10, 0.901, 0.01), 2)
MAX_FPR = 0.02


# ---------------------------------------------------------------------------
# Models: name -> callable(texts) -> phishing probability per row
# ---------------------------------------------------------------------------
def load_models() -> dict[str, callable]:
    """Every model that is available locally. DistilBERT joins automatically once present."""
    models: dict[str, callable] = {}
    p = MODELS / "baseline.joblib"
    if p.exists():
        pipe = joblib.load(p)
        models["baseline_tfidf_logreg"] = lambda t, _p=pipe: _p.predict_proba(t)[:, 1]
    p = MODELS / "baseline_nourl.joblib"
    if p.exists():
        pipe = joblib.load(p)
        models["baseline_tfidf_logreg_nourl"] = lambda t, _p=pipe: _p.predict_proba(strip_url_token(t))[:, 1]
    if (DISTILBERT_DIR / "config.json").exists():
        from transformers import pipeline as hf_pipeline
        clf = hf_pipeline("text-classification", model=str(DISTILBERT_DIR), tokenizer=str(DISTILBERT_DIR),
                          device=-1, truncation=True, max_length=128)

        def predict(texts, _clf=clf):
            out = []
            for row in _clf(list(texts), top_k=None):
                scores = {d["label"]: d["score"] for d in row}
                out.append(float(scores.get("LABEL_1", scores.get("1", 0.0))))
            return np.array(out)
        models["distilbert_multilingual"] = predict
    else:
        log("[info] models/distilbert/ nicht vorhanden – DistilBERT ist NICHT Teil dieser Experimente")
    return models


# ---------------------------------------------------------------------------
def tune(probs: np.ndarray, labels: np.ndarray) -> tuple[float, dict]:
    """Highest recall among thresholds whose FPR <= MAX_FPR; fallback: lowest FPR."""
    rows = []
    for t in THRESHOLDS:
        m = metrics(labels, (probs >= t).astype(int))
        rows.append((float(t), m))
    ok = [r for r in rows if r[1]["fpr"] is not None and r[1]["fpr"] <= MAX_FPR]
    if ok:
        best = max(ok, key=lambda r: (r[1]["recall"], -r[0]))
    else:
        best = min(rows, key=lambda r: r[1]["fpr"])
        log(f"[warn] kein Schwellenwert mit FPR <= {MAX_FPR} – nehme kleinste FPR")
    return best


def evaluate(probs_test: np.ndarray, test: pd.DataFrame, thr: float) -> tuple[dict, dict | None]:
    pred = (probs_test >= thr).astype(int)
    m_test = metrics(test["label"].to_numpy(), pred)
    de = (test["lang"] == "de").to_numpy()
    m_de = metrics(test.loc[de, "label"].to_numpy(), pred[de]) if de.any() else None
    return m_test, m_de


def append_entry(key: str, entry: dict) -> None:
    all_metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8")) if METRICS_PATH.exists() else {}
    all_metrics[key] = entry
    METRICS_PATH.write_text(json.dumps(all_metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    exp = EXPERIMENTS_PATH
    new = not exp.exists()
    with exp.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "model", "params", "seed", "train_acc", "test_acc", "f1", "fpr"])
        w.writerow([entry["date"], key, json.dumps(entry["params"], ensure_ascii=False), SEED,
                    entry["train"]["accuracy"], entry["test"]["accuracy"], entry["test"]["f1"], entry["test"]["fpr"]])


def row(name: str, thr: float, m_test: dict, m_de: dict | None) -> str:
    de = (f"{m_de['accuracy']:7.4f} {m_de['f1']:7.4f} {m_de['recall']:7.4f} {m_de['fpr']:7.4f}"
          f" {str(m_de['fp']) + '/' + str(m_de['fp'] + m_de['tn']):>10}" if m_de
          else f"{'–':>7} {'–':>7} {'–':>7} {'–':>7} {'–':>10}")
    return (f"{name:34} {thr:5.2f} {m_test['accuracy']:8.4f} {m_test['f1']:8.4f} {m_test['fpr']:8.4f} | {de}")


HEADER = (f"{'Modell':34} {'thr':>5} {'test_acc':>8} {'test_f1':>8} {'test_fpr':>8} | "
          f"{'de_acc':>7} {'de_f1':>7} {'de_rec':>7} {'de_fpr':>7} {'de_fp/leg':>10}")


def main() -> None:
    train = pd.read_csv(PROCESSED / "train.csv")
    val = pd.read_csv(PROCESSED / "val.csv")
    test = pd.read_csv(PROCESSED / "test.csv")
    log(f"train={len(train)}  val={len(val)} (nur {sorted(val.lang.unique())})  test={len(test)}"
        f" (davon de: {int((test.lang == 'de').sum())})")
    log(f"Schwellenwert-Suche: {THRESHOLDS[0]}–{THRESHOLDS[-1]} (Schritt 0.01), Kriterium: max recall bei FPR <= {MAX_FPR}\n")

    models = load_models()
    if not models:
        raise SystemExit("Keine Modelle in models/ gefunden")

    probs = {name: {"train": fn(train["text"]), "val": fn(val["text"]), "test": fn(test["text"])}
             for name, fn in models.items()}

    log(HEADER)
    # reference: the default 0.50 boundary these models were reported with (already in experiments.csv)
    for name, pr in probs.items():
        m_test, m_de = evaluate(pr["test"], test, 0.50)
        log(row(name + " @0.50 (Referenz)", 0.50, m_test, m_de))
    log("")

    chosen: dict[str, float] = {}
    for name, pr in probs.items():
        thr, m_val = tune(pr["val"], val["label"].to_numpy())
        chosen[name] = thr
        m_test, m_de = evaluate(pr["test"], test, thr)
        m_train = metrics(train["label"].to_numpy(), (pr["train"] >= thr).astype(int))
        log(row(name + " @tuned", thr, m_test, m_de))
        append_entry(f"{name}_thr{thr:.2f}", {
            "date": date.today().isoformat(), "seed": SEED,
            "params": {"base_model": name, "threshold": thr, "tuned_on": "val (English only)",
                       "criterion": f"max recall s.t. FPR <= {MAX_FPR}",
                       "val_at_threshold": {k: m_val[k] for k in ("recall", "fpr", "f1")}},
            "train": m_train, "test": m_test, "test_de": m_de})

    # --- ensemble: phishing if ANY model is above its own tuned threshold ---
    if len(models) > 1:
        def any_above(split: str) -> np.ndarray:
            return np.any([probs[n][split] >= chosen[n] for n in models], axis=0).astype(int)

        m_train = metrics(train["label"].to_numpy(), any_above("train"))
        pred_test = any_above("test")
        m_test = metrics(test["label"].to_numpy(), pred_test)
        de = (test["lang"] == "de").to_numpy()
        m_de = metrics(test.loc[de, "label"].to_numpy(), pred_test[de]) if de.any() else None
        log(row("ensemble_or @tuned", float("nan"), m_test, m_de))
        append_entry("ensemble_or_tuned", {
            "date": date.today().isoformat(), "seed": SEED,
            "params": {"rule": "phishing if ANY model >= its tuned threshold",
                       "members": {n: chosen[n] for n in models}, "tuned_on": "val (English only)"},
            "train": m_train, "test": m_test, "test_de": m_de})

    log("\nGewählte Schwellenwerte: " + ", ".join(f"{n}={t:.2f}" for n, t in chosen.items()))
    log(f"[out] {METRICS_PATH.relative_to(ROOT)}, {EXPERIMENTS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
