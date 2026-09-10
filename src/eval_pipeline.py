"""Product-level evaluation: run the FULL verdict logic (classifier + URL rules + urgency)
on every German test row and count green / yellow / red per true label.

The processed test.csv holds masked texts (<URL>), so the original texts are looked up
in data/raw/german_*.csv via the same masking; rows whose link was already masked at
collection time (*Link*) reach the URL layer without a real link – that is a known limit.

    python src/eval_pipeline.py                       # default config, with/without the trusted-link cap
    python src/eval_pipeline.py --yellow-p 0.22       # e.g. a threshold tuned by tune_threshold.py
    python src/eval_pipeline.py --probs results/distilbert_test_probs.csv   # scores from a CSV

--probs takes a CSV with the columns index,text,lang,label,p_phishing (one row per test
example, written by notebooks/03_transformer.ipynb). The classifier score is then read per
row instead of computed, so the traffic-light table can be recomputed for DistilBERT
WITHOUT the ~540 MB model. The URL rules and the urgency rules run unchanged.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline  # noqa: E402
from data_prep import GERMAN_FILES, LINK_PLACEHOLDER, SYNTHETIC_FILES  # noqa: E402
from url_check import URL_MASK, mask_urls  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ["green", "yellow", "red"]


def masked_to_raw() -> dict[str, str]:
    """Map the masked classifier text back to the originally collected text."""
    lookup: dict[str, str] = {}
    for path in list(GERMAN_FILES.values()) + list(SYNTHETIC_FILES.values()):
        if not path.exists():
            continue
        for raw in pd.read_csv(path, dtype=str, keep_default_na=False)["text"]:
            raw = raw.strip()
            lookup.setdefault(mask_urls(LINK_PLACEHOLDER.sub(URL_MASK, raw)), raw)
    return lookup


def verdict_table(rows: pd.DataFrame) -> pd.DataFrame:
    counts = pd.crosstab(rows["label"], rows["verdict"]).reindex(columns=LEVELS, fill_value=0)
    counts.index = [f"legit (label 0, n={int((rows.label == 0).sum())})",
                    f"phishing (label 1, n={int((rows.label == 1).sum())})"][: len(counts)]
    return counts


def load_probs(path: Path, rows: pd.DataFrame) -> pd.Series:
    """Read per-row phishing probabilities and check they really belong to these test rows."""
    df = pd.read_csv(path)
    missing = {"index", "text", "p_phishing"} - set(df.columns)
    if missing:
        raise SystemExit(f"{path}: Spalten fehlen: {sorted(missing)}")
    df = df.set_index("index")
    unknown = [i for i in rows.index if i not in df.index]
    if unknown:
        raise SystemExit(f"{path}: {len(unknown)} Testzeilen fehlen in der Datei (z. B. Index {unknown[:5]})")
    mismatch = [i for i in rows.index if str(df.loc[i, "text"]) != str(rows.loc[i, "text"])]
    if mismatch:
        raise SystemExit(f"{path}: Text passt bei {len(mismatch)} Zeilen nicht zu test.csv "
                         f"(z. B. Index {mismatch[:3]}) – stammt die Datei aus einem anderen Split?")
    return df.loc[rows.index, "p_phishing"].astype(float)


def run(rows: pd.DataFrame, cap: bool, probs: pd.Series | None = None) -> pd.DataFrame:
    """Full verdict logic per row. With `probs`, the classifier score is taken from the CSV."""
    pipeline.TRUSTED_LINK_CAP = cap
    out = rows.copy()
    clf = pipeline.get_classifier()
    original = clf._predict
    try:
        verdicts = []
        for idx, r in out.iterrows():
            if probs is not None:
                clf._predict = lambda _text, _p=float(probs.loc[idx]): _p
            verdicts.append(pipeline.analyze(r["text_raw"])["verdict"])
    finally:
        clf._predict = original
    out["verdict"] = verdicts
    return out


def main(yellow_p: float | None = None, red_p: float | None = None,
         probs_path: Path | None = None) -> None:
    if yellow_p is not None:
        pipeline.YELLOW_P = yellow_p
    if red_p is not None:
        pipeline.RED_P = red_p
    test = pd.read_csv(ROOT / "data" / "processed" / "test.csv")
    de = test[test.lang == "de"].copy()
    lookup = masked_to_raw()
    de["text_raw"] = de["text"].map(lookup)
    missing = int(de["text_raw"].isna().sum())
    de["text_raw"] = de["text_raw"].fillna(de["text"])
    n_placeholder = int(de["text_raw"].str.contains(r"\*Link\*", case=False).sum())
    # The collected texts write "*Link*" where the source had masked the link. data_prep turned
    # that into the <URL> token BEFORE training, so do the same here – otherwise the classifier
    # sees a token it never learned and this evaluation would not match metrics.json.
    # The URL layer is unaffected: neither "*Link*" nor "<URL>" is a real link.
    de["text_raw"] = de["text_raw"].map(lambda t: LINK_PLACEHOLDER.sub(URL_MASK, t))
    print(f"Deutsche Testzeilen: {len(de)} (Originaltext gefunden für {len(de) - missing}, "
          f"{n_placeholder} davon mit maskiertem Link *Link* – kein echter Link für die URL-Schicht)")
    probs = load_probs(probs_path, de) if probs_path else None
    source = (f"Wahrscheinlichkeiten aus {probs_path}" if probs is not None
              else f"Modell: {pipeline.get_classifier().name}")
    print(f"{source}  |  Schwellen: gelb ab p>={pipeline.YELLOW_P}, rot ab p>={pipeline.RED_P}\n")

    for cap in (False, True):
        res = run(de, cap, probs)
        tab = verdict_table(res)
        legit = res[res.label == 0]
        print(f"=== Ampel pro wahrem Label – {'MIT' if cap else 'OHNE'} Regel „vertrauenswürdiger Link“ ===")
        print(tab.to_string())
        print(f"Produkt-Fehlalarmrate (legit → gelb oder rot): {(legit.verdict != 'green').mean():.3f}  |  "
              f"legit → rot: {(legit.verdict == 'red').mean():.3f}  |  "
              f"Phishing erkannt (rot): {(res[res.label == 1].verdict == 'red').mean():.3f}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="product-level evaluation of the full verdict logic")
    ap.add_argument("--yellow-p", type=float, default=None, help="override pipeline.YELLOW_P")
    ap.add_argument("--red-p", type=float, default=None, help="override pipeline.RED_P")
    ap.add_argument("--probs", type=Path, default=None,
                    help="CSV with index,text,lang,label,p_phishing – use these scores instead of the model")
    a = ap.parse_args()
    main(yellow_p=a.yellow_p, red_p=a.red_p, probs_path=a.probs)
