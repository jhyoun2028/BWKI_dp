"""Merge Colab exports from results/colab/ into results/metrics.json and results/experiments.csv.

APPEND ONLY: an existing metrics key is never overwritten and an existing CSV row is never
duplicated or changed. Run after downloading metrics.json / experiments.csv from a Colab run:

    python src/merge_colab_results.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_baseline import (EXPERIMENTS_PATH, METRICS_PATH, RESULTS,  # noqa: E402
                            log, save_confusion_matrix)

ROOT = Path(__file__).resolve().parents[1]
COLAB = RESULTS / "colab"


def merge_metrics() -> list[str]:
    """Add unknown model keys; report keys that already exist (kept as they are)."""
    src = COLAB / "metrics.json"
    if not src.exists():
        log(f"[metrics] {src.relative_to(ROOT)} nicht vorhanden – übersprungen")
        return []
    incoming = json.loads(src.read_text(encoding="utf-8"))
    current = json.loads(METRICS_PATH.read_text(encoding="utf-8")) if METRICS_PATH.exists() else {}
    added = []
    for key, entry in incoming.items():
        if key in current:
            log(f"[metrics] '{key}' existiert bereits – NICHT überschrieben")
        else:
            current[key] = entry
            added.append(key)
            log(f"[metrics] '{key}' hinzugefügt")
            write_confusion_matrix(key, entry)
    if added:
        METRICS_PATH.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
    return added


TITLES = {"distilbert_multilingual": "DistilBERT multilingual – Testdaten"}


def write_confusion_matrix(key: str, entry: dict) -> None:
    """Rebuild results/confusion_matrix_<key>.png from the merged tn/fp/fn/tp, if missing.

    Colab writes this PNG itself; this is the fallback when the exported file is missing
    or empty. The counts come from the executed Colab run, nothing is invented.
    """
    short = key.split("_")[0]
    path = RESULTS / f"confusion_matrix_{short}.png"
    if path.exists() and path.stat().st_size > 0:
        return
    t = entry.get("test", {})
    if not all(k in t for k in ("tn", "fp", "fn", "tp")):
        return
    y_true = [0] * (t["tn"] + t["fp"]) + [1] * (t["fn"] + t["tp"])
    y_pred = [0] * t["tn"] + [1] * t["fp"] + [0] * t["fn"] + [1] * t["tp"]
    save_confusion_matrix(y_true, y_pred, path, title=TITLES.get(key, f"{key} – Testdaten"))
    log(f"[plot] {path.relative_to(ROOT)} aus den Zahlen des Colab-Laufs erzeugt "
        f"(tn={t['tn']} fp={t['fp']} fn={t['fn']} tp={t['tp']})")


def merge_experiments() -> int:
    """Append rows that are not already present (compared as whole rows)."""
    src = COLAB / "experiments.csv"
    if not src.exists():
        log(f"[experiments] {src.relative_to(ROOT)} nicht vorhanden – übersprungen")
        return 0
    with src.open(encoding="utf-8", newline="") as f:
        incoming = list(csv.reader(f))
    header, rows = incoming[0], incoming[1:]

    existing: list[list[str]] = []
    if EXPERIMENTS_PATH.exists():
        with EXPERIMENTS_PATH.open(encoding="utf-8", newline="") as f:
            existing = list(csv.reader(f))
        if existing and existing[0] != header:
            raise ValueError(f"Spalten passen nicht: {existing[0]} vs {header}")
    known = {tuple(r) for r in existing[1:]}

    new_rows = [r for r in rows if tuple(r) not in known]
    with EXPERIMENTS_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not existing:
            w.writerow(header)
        for r in new_rows:
            w.writerow(r)
            log(f"[experiments] Zeile angehängt: {r[0]} {r[1]}")
    log(f"[experiments] {len(rows) - len(new_rows)} Zeile(n) waren schon vorhanden")
    return len(new_rows)


def main() -> None:
    if not COLAB.exists():
        raise SystemExit(f"{COLAB.relative_to(ROOT)} fehlt – Colab-Dateien dorthin legen")
    added = merge_metrics()
    n = merge_experiments()
    log(f"\nErgebnis: {len(added)} neue Modelle in metrics.json, {n} neue Zeile(n) in experiments.csv")


if __name__ == "__main__":
    main()
