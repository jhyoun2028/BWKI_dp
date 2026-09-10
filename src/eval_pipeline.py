"""Product-level evaluation: run the FULL verdict logic (classifier + URL rules + urgency)
on every German test row and count green / yellow / red per true label.

The processed test.csv holds masked texts (<URL>), so the original texts are looked up
in data/raw/german_*.csv via the same masking; rows whose link was already masked at
collection time (*Link*) reach the URL layer without a real link – that is a known limit.

    python src/eval_pipeline.py                       # default config, with/without the trusted-link cap
    python src/eval_pipeline.py --yellow-p 0.22       # e.g. a threshold tuned by tune_threshold.py
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


def run(rows: pd.DataFrame, cap: bool) -> pd.DataFrame:
    pipeline.TRUSTED_LINK_CAP = cap
    out = rows.copy()
    out["verdict"] = [pipeline.analyze(t)["verdict"] for t in out["text_raw"]]
    return out


def main(yellow_p: float | None = None, red_p: float | None = None) -> None:
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
    print(f"Deutsche Testzeilen: {len(de)} (Originaltext gefunden für {len(de) - missing}, "
          f"{n_placeholder} davon mit maskiertem Link *Link* – kein echter Link für die URL-Schicht)")
    print(f"Modell: {pipeline.get_classifier().name}  |  "
          f"Schwellen: gelb ab p>={pipeline.YELLOW_P}, rot ab p>={pipeline.RED_P}\n")

    for cap in (False, True):
        res = run(de, cap)
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
    a = ap.parse_args()
    main(yellow_p=a.yellow_p, red_p=a.red_p)
