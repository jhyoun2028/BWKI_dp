"""Schritt 2: Baseline – TF-IDF (Wort- + Zeichen-n-Gramme) + logistische Regression.

Training auf train.csv, Wahl von C über F1 auf val.csv, GENAU EINE Auswertung
auf test.csv. Schreibt results/metrics.json, results/experiments.csv,
results/confusion_matrix_baseline.png und models/baseline.joblib.

Aufruf:  python src/train_baseline.py
"""
from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.pipeline import FeatureUnion, Pipeline

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
MODELS = ROOT / "models"

SEED = 42
MODEL_NAME = "baseline_tfidf_logreg"
C_GRID = [0.3, 1, 3]


def log(msg: str = "") -> None:
    print(msg, flush=True)


def build_pipeline(C: float) -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2))),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))),
    ])
    clf = LogisticRegression(C=C, class_weight="balanced", max_iter=1000, random_state=SEED)
    return Pipeline([("features", features), ("clf", clf)])


def metrics(y_true, y_pred) -> dict:
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = (int(v) for v in cm.ravel())
    return {
        "n": int(len(y_true)),
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "fpr": round(fp / (fp + tn), 4) if (fp + tn) else None,
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
    }


def print_metrics(title: str, m: dict) -> None:
    log(f"{title} (n={m['n']}): acc={m['accuracy']:.4f} prec={m['precision']:.4f} "
        f"rec={m['recall']:.4f} f1={m['f1']:.4f} fpr={m['fpr']}  "
        f"[tn={m['tn']} fp={m['fp']} fn={m['fn']} tp={m['tp']}]")


def top_features(pipe: Pipeline, k: int = 10) -> dict[str, list[tuple[str, float]]]:
    names = pipe.named_steps["features"].get_feature_names_out()
    coef = pipe.named_steps["clf"].coef_[0]
    order = np.argsort(coef)
    spam = [(str(names[i]), round(float(coef[i]), 3)) for i in order[::-1][:k]]
    ham = [(str(names[i]), round(float(coef[i]), 3)) for i in order[:k]]
    return {"spam (label 1)": spam, "ham (label 0)": ham}


def save_confusion_matrix(y_true, y_pred, path: Path) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    fig, ax = plt.subplots(figsize=(4.2, 3.8))
    # eine Farbe, hell→dunkel (sequentiell); Zahlen in Textfarbe, nicht in Serienfarbe
    im = ax.imshow(cm, cmap="Blues", vmin=0)
    for (i, j), v in np.ndenumerate(cm):
        ink = "white" if v > cm.max() * 0.6 else "#1f2933"
        ax.text(j, i, f"{v:,}", ha="center", va="center", color=ink, fontsize=12)
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["ham (0)", "phishing (1)"]); ax.set_yticklabels(["ham (0)", "phishing (1)"])
    ax.set_xlabel("vorhergesagt"); ax.set_ylabel("tatsächlich")
    ax.set_title("Baseline TF-IDF + LogReg – Testdaten", fontsize=11)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)

    train = pd.read_csv(PROCESSED / "train.csv")
    val = pd.read_csv(PROCESSED / "val.csv")
    test = pd.read_csv(PROCESSED / "test.csv")
    log(f"train={len(train)}  val={len(val)}  test={len(test)}")

    # --- Modellwahl: C über F1 auf val -------------------------------------
    best_C, best_f1, best_pipe = None, -1.0, None
    for C in C_GRID:
        pipe = build_pipeline(C).fit(train["text"], train["label"])
        f1 = f1_score(val["label"], pipe.predict(val["text"]))
        log(f"[val] C={C}: F1={f1:.4f}")
        if f1 > best_f1:
            best_C, best_f1, best_pipe = C, f1, pipe
    log(f"[val] gewählt: C={best_C} (F1={best_f1:.4f})")
    pipe = best_pipe

    # --- Auswertung: train und GENAU EINMAL test ----------------------------
    m_train = metrics(train["label"], pipe.predict(train["text"]))
    y_test_pred = pipe.predict(test["text"])
    m_test = metrics(test["label"], y_test_pred)
    log()
    print_metrics("TRAIN", m_train)
    print_metrics("TEST ", m_test)

    m_test_de = None
    de = test["lang"] == "de"
    if de.any():
        m_test_de = metrics(test.loc[de, "label"], y_test_pred[de.to_numpy()])
        print_metrics("TEST (nur Deutsch)", m_test_de)
    else:
        log("TEST (nur Deutsch): keine deutschen Zeilen im Testset")

    # --- Top-Merkmale ------------------------------------------------------
    feats = top_features(pipe)
    log()
    for cls, items in feats.items():
        log(f"Top-10 Merkmale für {cls}:")
        for name, w in items:
            log(f"  {w:+.3f}  {name}")

    # --- Speichern ---------------------------------------------------------
    params = {"features": "tfidf word(1,2) + tfidf char_wb(3,5)",
              "clf": "LogisticRegression", "C": best_C,
              "class_weight": "balanced", "max_iter": 1000, "C_grid": C_GRID,
              "data": f"train={len(train)} val={len(val)} test={len(test)} "
                      f"de_train={int((train.lang == 'de').sum())} de_test={int(de.sum())}"}
    entry = {"date": date.today().isoformat(), "seed": SEED, "params": params,
             "val_f1_best": round(best_f1, 4), "train": m_train, "test": m_test,
             "test_de": m_test_de, "top_features": feats}
    metrics_path = RESULTS / "metrics.json"
    all_metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}
    all_metrics[MODEL_NAME] = entry
    metrics_path.write_text(json.dumps(all_metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    exp_path = RESULTS / "experiments.csv"
    new_file = not exp_path.exists()
    with exp_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["date", "model", "params", "seed", "train_acc", "test_acc", "f1", "fpr"])
        w.writerow([entry["date"], MODEL_NAME, json.dumps(params, ensure_ascii=False), SEED,
                    m_train["accuracy"], m_test["accuracy"], m_test["f1"], m_test["fpr"]])

    cm_path = RESULTS / "confusion_matrix_baseline.png"
    save_confusion_matrix(test["label"], y_test_pred, cm_path)

    model_path = MODELS / "baseline.joblib"
    joblib.dump(pipe, model_path)

    log()
    for p in (metrics_path, exp_path, cm_path, model_path):
        log(f"[out] {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
