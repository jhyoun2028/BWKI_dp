"""Schritt 1: Daten laden, bereinigen, aufteilen.

Erzeugt data/processed/{train,val,test}.csv (Spalten: text,label,lang,source)
und results/data_summary.md.

Aufruf:  python src/data_prep.py
"""
from __future__ import annotations

import csv
import io
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent))
from url_check import URL_MASK, mask_urls  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"

SEED = 42
MIN_CHARS = 5

# --- Quelle 1: UCI SMS Spam Collection -------------------------------------
UCI_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
# Wortgetreue Spiegel der Datei "SMSSpamCollection" (Tab-getrennt, 5.574 Zeilen),
# falls archive.ics.uci.edu nicht erreichbar ist.
UCI_MIRRORS = [
    "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv",
    "https://raw.githubusercontent.com/justmarkham/DAT8/master/data/sms.tsv",
]
UCI_FILE = RAW / "SMSSpamCollection"

# --- Quelle 2: eigene deutsche Daten ---------------------------------------
# real: hand-collected (Phishing-Radar, filled-in public templates) -> 50/50 train/test
GERMAN_FILES = {
    "german_phishing": RAW / "german_phishing.csv",
    "german_legit": RAW / "german_legit.csv",
}
# synthetic: LLM-generated, marked in source_url -> TRAIN ONLY, never test
SYNTHETIC_FILES = {
    "german_synthetic_phishing": RAW / "german_synthetic_phishing.csv",
    "german_synthetic_legit": RAW / "german_synthetic_legit.csv",
    "german_synthetic_legit_v2": RAW / "german_synthetic_legit_v2.csv",   # formal legit messages WITH official links
}
GERMAN_COLUMNS = ["text", "label", "source_url", "category"]
TEMPLATE_MARKER = "BEISPIEL"   # Zeilen mit dieser source_url sind nur Vorlage
LINK_PLACEHOLDER = re.compile(r"\*\s*link\s*\*", re.I)   # "*Link*" in collected texts = masked URL
DE_REAL_TEST_SHARE = 0.5


def log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------------------
def download_uci() -> pd.DataFrame:
    """Lädt die UCI-Sammlung (zuerst Original-ZIP, sonst Spiegel) und parst sie."""
    RAW.mkdir(parents=True, exist_ok=True)
    if not UCI_FILE.exists():
        try:
            log(f"[uci] lade {UCI_URL}")
            r = requests.get(UCI_URL, timeout=60)
            r.raise_for_status()
            (RAW / "sms_spam_collection.zip").write_bytes(r.content)
            with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                UCI_FILE.write_bytes(zf.read("SMSSpamCollection"))
        except Exception as e:  # Netz gesperrt o. ä.
            log(f"[uci] Original nicht erreichbar ({type(e).__name__}: {e}) – nutze Spiegel")
            for url in UCI_MIRRORS:
                try:
                    r = requests.get(url, timeout=60)
                    r.raise_for_status()
                    UCI_FILE.write_bytes(r.content)
                    log(f"[uci] geladen von {url}")
                    break
                except Exception as e2:
                    log(f"[uci] Spiegel fehlgeschlagen: {url} ({e2})")
            else:
                raise RuntimeError("UCI SMS Spam Collection konnte nicht geladen werden")

    df = pd.read_csv(
        UCI_FILE, sep="\t", header=None, names=["label", "text"],
        quoting=csv.QUOTE_NONE, encoding="utf-8", dtype=str,
    )
    df["label"] = df["label"].str.strip().map({"ham": 0, "spam": 1})
    assert df["label"].notna().all(), "unbekanntes Label in UCI-Daten"
    df["lang"] = "en"
    df["source"] = "uci_sms"
    log(f"[uci] {len(df)} Zeilen, davon spam={int(df.label.sum())}")
    return df[["text", "label", "lang", "source"]]


def _write_template(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(GERMAN_COLUMNS)
        w.writerows(rows)


def _read_german_csv(path: Path, source: str, group: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [c for c in GERMAN_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name}: Spalten fehlen: {missing}")
    n_template = int((df["source_url"] == TEMPLATE_MARKER).sum())
    df = df[df["source_url"] != TEMPLATE_MARKER]
    df = df[df["text"].str.strip() != ""]
    df["label"] = pd.to_numeric(df["label"], errors="coerce")
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    df["lang"] = "de"
    df["source"] = source
    df["group"] = group
    df["category"] = df["category"].str.strip().str.lower()
    log(f"[de] {path.name}: {len(df)} Zeilen ({group})"
        + (f", {n_template} Vorlagenzeilen ignoriert" if n_template else ""))
    return df[["text", "label", "lang", "source", "group", "category"]]


def load_german() -> pd.DataFrame:
    """Own German data: real CSVs (templates created if missing) + optional synthetic CSVs."""
    frames = []
    for name, path in GERMAN_FILES.items():
        if not path.exists():
            if name == "german_phishing":
                rows = [
                    ["Ihr Paket konnte nicht zugestellt werden. Bitte bestätigen Sie Ihre Adresse: *Link*", "1", TEMPLATE_MARKER, "paket"],
                    ["Ihr Konto wurde vorübergehend gesperrt. Verifizieren Sie sich jetzt: *Link*", "1", TEMPLATE_MARKER, "bank"],
                ]
            else:
                rows = [
                    ["Hallo Mama, bin gut angekommen. Melde mich später nochmal!", "0", TEMPLATE_MARKER, "familie"],
                    ["Ihre Sendung wird heute zwischen 14 und 16 Uhr zugestellt.", "0", TEMPLATE_MARKER, "paket_echt"],
                ]
            _write_template(path, rows)
            log(f"[de] {path.relative_to(ROOT)} fehlte – VORLAGE mit 2 Beispielzeilen angelegt "
                f"(source_url={TEMPLATE_MARKER}; Beispielzeilen werden NICHT trainiert)")
        frames.append(_read_german_csv(path, name, "de_real"))
    for name, path in SYNTHETIC_FILES.items():
        if path.exists():
            frames.append(_read_german_csv(path, name, "de_synth"))
        else:
            log(f"[de] {path.name} nicht vorhanden – ohne synthetische Daten")
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
_PUNCT = re.compile(r"[^\w\s]", flags=re.UNICODE)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", _PUNCT.sub("", text.lower())).strip()


def clean(df: pd.DataFrame) -> pd.DataFrame:
    n0 = len(df)
    df = df.copy()
    df["text"] = df["text"].astype(str).str.strip()
    # classifier input: real URLs and the "*Link*" placeholder become the same token
    df["text"] = df["text"].map(lambda t: mask_urls(LINK_PLACEHOLDER.sub(URL_MASK, t)))
    df = df[df["text"].str.len() >= MIN_CHARS]
    n1 = len(df)
    df = df.drop_duplicates(subset="text")
    n2 = len(df)
    df = df.assign(_key=df["text"].map(normalize)).drop_duplicates(subset="_key").drop(columns="_key")
    n3 = len(df)
    log(f"[clean] {n0} → kurz entfernt: {n0 - n1} → exakte Duplikate: {n1 - n2} "
        f"→ Fast-Duplikate: {n2 - n3} → übrig: {n3}")
    return df.reset_index(drop=True)


def _strata(df: pd.DataFrame, cols: list[str], min_count: int = 2) -> pd.Series:
    """Stratification key from `cols`; strata smaller than min_count fall back to label only."""
    key = df[cols].astype(str).agg("_".join, axis=1)
    small = key.map(key.value_counts()) < min_count
    return key.where(~small, df["label"].astype(str))


def split(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """en (UCI): 80/10/10 by label. de_real: 50/50 train/test by label × category.
    de_synth: train only. val therefore contains English rows only."""
    en = df[df["lang"] == "en"]
    de_real = df[df["group"] == "de_real"]
    de_synth = df[df["group"] == "de_synth"]

    en_train, rest = train_test_split(en, test_size=0.2, stratify=en["label"], random_state=SEED)
    en_val, en_test = train_test_split(rest, test_size=0.5, stratify=rest["label"], random_state=SEED)
    log(f"[split] en: {len(en_train)}/{len(en_val)}/{len(en_test)} (80/10/10, stratifiziert nach label)")

    if len(de_real):
        de_train, de_test = train_test_split(de_real, test_size=DE_REAL_TEST_SHARE,
                                             stratify=_strata(de_real, ["label", "category"]), random_state=SEED)
        log(f"[split] de_real: {len(de_train)} train / {len(de_test)} test (50/50, stratifiziert nach label × category)")
    else:
        de_train = de_test = de_real
    if len(de_synth):
        log(f"[split] de_synth: {len(de_synth)} nur train")

    train = pd.concat([en_train, de_train, de_synth]).sample(frac=1, random_state=SEED)
    test = pd.concat([en_test, de_test]).sample(frac=1, random_state=SEED)
    return {"train": train.reset_index(drop=True),
            "val": en_val.reset_index(drop=True),
            "test": test.reset_index(drop=True)}


def summarize(splits: dict[str, pd.DataFrame]) -> str:
    rows = []
    for name, d in splits.items():
        g = d.groupby(["label", "lang"], observed=True).agg(
            n=("text", "size"), mean_len=("text", lambda s: s.str.len().mean()))
        for (label, lang), r in g.iterrows():
            rows.append({"split": name, "label": int(label), "lang": lang,
                         "n": int(r["n"]), "mean_len": round(float(r["mean_len"]), 1)})
    table = pd.DataFrame(rows)
    lines = ["# Datenübersicht", "",
             "Zeilen pro Split × Label × Sprache (label 1 = Phishing/Spam), "
             "mean_len = mittlere Textlänge in Zeichen.", "",
             "| split | label | lang | n | mean_len |", "|---|---|---|---|---|"]
    for r in table.itertuples():
        lines.append(f"| {r.split} | {r.label} | {r.lang} | {r.n} | {r.mean_len} |")
    lines += ["", "## Gesamt pro Split", "", "| split | n | spam-Anteil | mean_len |", "|---|---|---|---|"]
    for name, d in splits.items():
        lines.append(f"| {name} | {len(d)} | {d.label.mean():.3f} | {d.text.str.len().mean():.1f} |")
    lines += ["", "## Quellen pro Split", "", "| source | train | val | test |", "|---|---|---|---|"]
    all_df = pd.concat([d.assign(split=n) for n, d in splits.items()])
    for src, g in all_df.groupby("source"):
        c = g["split"].value_counts()
        lines.append(f"| {src} | {c.get('train', 0)} | {c.get('val', 0)} | {c.get('test', 0)} |")
    lines += ["", f"Hinweis: URLs und der Platzhalter `*Link*` sind im Text durch `{URL_MASK}` ersetzt; "
              "synthetische deutsche Zeilen nur im Training; val enthält nur englische Zeilen."]
    return "\n".join(lines) + "\n"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    # Decision (CLAUDE.md): data = UCI + own German data only, no second English set.
    uci = download_uci().assign(group="en", category="")
    de = load_german()
    # order matters for dedupe (keep first): real German > UCI > synthetic
    df = pd.concat([de[de.group == "de_real"], uci, de[de.group == "de_synth"]], ignore_index=True)
    df["label"] = df["label"].astype(int)
    df = clean(df)

    splits = split(df)
    for name, d in splits.items():
        out = PROCESSED / f"{name}.csv"
        d[["text", "label", "lang", "source"]].to_csv(out, index=False)
        log(f"[out] {out.relative_to(ROOT)}: {len(d)} Zeilen")

    md = summarize(splits)
    (RESULTS / "data_summary.md").write_text(md, encoding="utf-8")
    log("")
    log(md)


if __name__ == "__main__":
    main()
