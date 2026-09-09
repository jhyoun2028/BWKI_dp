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

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"

SEED = 42
MIN_CHARS = 5
MAX_CHARS_EMAIL = 512

# --- Quelle 1: UCI SMS Spam Collection -------------------------------------
UCI_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
# Wortgetreue Spiegel der Datei "SMSSpamCollection" (Tab-getrennt, 5.574 Zeilen),
# falls archive.ics.uci.edu nicht erreichbar ist.
UCI_MIRRORS = [
    "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv",
    "https://raw.githubusercontent.com/justmarkham/DAT8/master/data/sms.tsv",
]
UCI_FILE = RAW / "SMSSpamCollection"

# --- Quelle 2: zweiter englischer Datensatz vom HuggingFace Hub -------------
HF_DATASET = "SetFit/enron_spam"   # E-Mail-Spam (Enron), Spalten text/label
HF_SOURCE_NAME = "hf_setfit_enron_spam"

# --- Quelle 3: eigene deutsche Daten ---------------------------------------
GERMAN_FILES = {
    "german_phishing": RAW / "german_phishing.csv",
    "german_legit": RAW / "german_legit.csv",
}
GERMAN_COLUMNS = ["text", "label", "source_url", "category"]
TEMPLATE_MARKER = "BEISPIEL"   # Zeilen mit dieser source_url sind nur Vorlage


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


def load_hf_dataset() -> pd.DataFrame:
    """Zweite englische Quelle vom HuggingFace Hub (ohne Login).

    Schlägt der Download fehl (kein Netz, Hub gesperrt), wird ein leerer
    DataFrame zurückgegeben und das Projekt läuft nur mit UCI weiter.
    """
    try:
        from datasets import load_dataset
        log(f"[hf] lade {HF_DATASET}")
        ds = load_dataset(HF_DATASET)
        frames = [ds[split].to_pandas() for split in ds.keys()]
        df = pd.concat(frames, ignore_index=True)
    except Exception as e:
        log(f"[hf] NICHT geladen ({type(e).__name__}: {e}) – weiter nur mit UCI")
        return pd.DataFrame(columns=["text", "label", "lang", "source"])

    if "text" not in df.columns:
        raise ValueError(f"[hf] Spalte 'text' fehlt, vorhanden: {list(df.columns)}")
    if "label_text" in df.columns:
        df["label"] = df["label_text"].str.lower().map({"ham": 0, "spam": 1})
    df["label"] = pd.to_numeric(df["label"], errors="coerce")
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    df["text"] = df["text"].astype(str).str.slice(0, MAX_CHARS_EMAIL)  # E-Mails kürzen
    df["lang"] = "en"
    df["source"] = HF_SOURCE_NAME
    log(f"[hf] {len(df)} Zeilen, davon spam={int(df.label.sum())}")
    return df[["text", "label", "lang", "source"]]


def _write_template(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(GERMAN_COLUMNS)
        w.writerows(rows)


def load_german() -> pd.DataFrame:
    """Eigene deutsche CSVs laden; fehlen sie, Vorlagen anlegen."""
    frames = []
    for name, path in GERMAN_FILES.items():
        if not path.exists():
            if name == "german_phishing":
                rows = [
                    ["Ihr Paket konnte nicht zugestellt werden. Bitte bestätigen Sie Ihre Adresse: hxxp://beispiel-link.de", "1", TEMPLATE_MARKER, "Paket"],
                    ["Ihr Konto wurde vorübergehend gesperrt. Verifizieren Sie sich jetzt unter hxxp://beispiel-bank.de", "1", TEMPLATE_MARKER, "Bank"],
                ]
            else:
                rows = [
                    ["Hallo Mama, bin gut angekommen. Melde mich später nochmal!", "0", TEMPLATE_MARKER, "Familie"],
                    ["Ihre Sendung wird heute zwischen 14 und 16 Uhr zugestellt.", "0", TEMPLATE_MARKER, "Paket"],
                ]
            _write_template(path, rows)
            log(f"[de] {path.relative_to(ROOT)} fehlte – VORLAGE mit 2 Beispielzeilen angelegt "
                f"(source_url={TEMPLATE_MARKER}; Beispielzeilen werden NICHT trainiert)")
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
        df["source"] = name
        log(f"[de] {path.name}: {len(df)} echte Zeilen"
            + (f" ({n_template} Vorlagenzeilen ignoriert)" if n_template else ""))
        frames.append(df[["text", "label", "lang", "source"]])
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
_PUNCT = re.compile(r"[^\w\s]", flags=re.UNICODE)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", _PUNCT.sub("", text.lower())).strip()


def clean(df: pd.DataFrame) -> pd.DataFrame:
    n0 = len(df)
    df = df.copy()
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() >= MIN_CHARS]
    n1 = len(df)
    df = df.drop_duplicates(subset="text")
    n2 = len(df)
    df = df.assign(_key=df["text"].map(normalize)).drop_duplicates(subset="_key").drop(columns="_key")
    n3 = len(df)
    log(f"[clean] {n0} → kurz entfernt: {n0 - n1} → exakte Duplikate: {n1 - n2} "
        f"→ Fast-Duplikate: {n2 - n3} → übrig: {n3}")
    return df.reset_index(drop=True)


def split(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Stratifizierter 80/10/10-Split nach label (und lang, falls genug Zeilen)."""
    strata = df["label"].astype(str) + "_" + df["lang"]
    if strata.value_counts().min() >= 10:
        strat_key = strata
        log("[split] stratifiziert nach label × lang")
    else:
        strat_key = df["label"].astype(str)
        log("[split] zu wenige Zeilen pro label × lang – stratifiziert nur nach label")
    train, rest = train_test_split(df, test_size=0.2, stratify=strat_key, random_state=SEED)
    rest_key = strat_key.loc[rest.index]
    val, test = train_test_split(rest, test_size=0.5, stratify=rest_key, random_state=SEED)
    return {"train": train.reset_index(drop=True),
            "val": val.reset_index(drop=True),
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
    lines += ["", "## Quellen", "", "| source | n |", "|---|---|"]
    all_df = pd.concat(splits.values())
    for src, n in all_df["source"].value_counts().items():
        lines.append(f"| {src} | {n} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    parts = [download_uci(), load_hf_dataset(), load_german()]
    df = pd.concat([p for p in parts if len(p)], ignore_index=True)
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
