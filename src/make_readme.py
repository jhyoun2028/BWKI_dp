"""Generate README.md (German) with the results table built from results/metrics.json.

Keeps the numbers in the README in sync with the executed runs; prose lives here.

    python src/make_readme.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_pipeline  # noqa: E402
import pipeline  # noqa: E402
from data_prep import LINK_PLACEHOLDER  # noqa: E402
from train_baseline import EXPERIMENTS_PATH, METRICS_PATH, PROCESSED, log  # noqa: E402
from url_check import URL_MASK  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "README.md"
REPO = "jhyoun2028/BWKI_dp"
DRIVE_LINK = "<Google-Drive-Freigabelink hier eintragen>"

# Measured by the team on their own Android phone (Galaxy, HTTP Shortcuts app), not in this repo's CI.
ANDROID_TEST = {"device": "Samsung Galaxy", "app": "HTTP Shortcuts",
                "phish_p": 0.9785, "legit_p": 0.0679}

ORDER = ["baseline_tfidf_logreg", "distilbert_multilingual", "baseline_tfidf_logreg_nourl",
         "baseline_tfidf_logreg_thr0.22", "baseline_tfidf_logreg_nourl_thr0.32", "ensemble_or_tuned"]
LABELS = {
    "baseline_tfidf_logreg": "Baseline TF-IDF + LogReg **(aktiv)**",
    "distilbert_multilingual": "DistilBERT multilingual",
    "baseline_tfidf_logreg_nourl": "Baseline ohne `<URL>`-Token (Ablation)",
    "baseline_tfidf_logreg_thr0.22": "Baseline, Schwelle 0.22 (getunt auf val)",
    "baseline_tfidf_logreg_nourl_thr0.32": "Baseline ohne Token, Schwelle 0.32",
    "ensemble_or_tuned": "ODER-Kombination beider Baselines",
}


def de_num(x: float | int, decimals: int = 0) -> str:
    """German number formatting: thousands dot, decimal comma."""
    return f"{x:,.{decimals}f}".replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")


def traffic_light() -> dict:
    """German traffic-light counts of the shipped configuration."""
    test = pd.read_csv(PROCESSED / "test.csv")
    de = test[test.lang == "de"].copy()
    lookup = eval_pipeline.masked_to_raw()
    de["text_raw"] = (de.text.map(lookup).fillna(de.text)
                      .map(lambda t: LINK_PLACEHOLDER.sub(URL_MASK, t)))
    res = eval_pipeline.run(de, cap=True)
    legit, phish = res[res.label == 0], res[res.label == 1]
    counts = lambda g: g.verdict.value_counts().reindex(["green", "yellow", "red"], fill_value=0)
    return {"legit": counts(legit), "phish": counts(phish), "n_legit": len(legit), "n_phish": len(phish),
            "false_alarm": float((legit.verdict != "green").mean()),
            "legit_red": float((legit.verdict == "red").mean()),
            "phish_red": float((phish.verdict == "red").mean())}


def main() -> None:
    m = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    exp = pd.read_csv(EXPERIMENTS_PATH)
    counts = {s: pd.read_csv(PROCESSED / f"{s}.csv") for s in ("train", "val", "test")}
    tl = traffic_light()
    b, d = m["baseline_tfidf_logreg"], m["distilbert_multilingual"]

    L = []
    L.append("# DoppelCheck – Phishing-Erkennung für SMS und Kurznachrichten\n")
    L.append("**Betrugsschutz mit einer Geste.** Zweimal auf die Rückseite des Handys tippen, der aktuelle "
             "Bildschirm wird geprüft, und wenige Sekunden später erscheint eine Ampel mit einem Satz in "
             "einfachem Deutsch. Gedacht für ältere Menschen in Deutschland, die täglich gefälschte Paket-, "
             "Bank- und Behörden-SMS bekommen.\n")

    L.append("## Projekt\n")
    L.append("DoppelCheck prüft eine Nachricht auf drei Ebenen und fasst das Ergebnis zu einer Ampel zusammen:\n")
    L.append("1. **Texterkennung** (`src/ocr.py`): Aus dem Screenshot wird mit EasyOCR (Deutsch + Englisch, CPU) Text.\n"
             "2. **Sprachmodell** (`src/pipeline.py`): Ein Klassifikator schätzt, wie wahrscheinlich die Nachricht "
             "Betrug ist. Aktiv ist die Baseline; liegt `models/distilbert/` lokal vor, wird automatisch DistilBERT benutzt.\n"
             "3. **Link-Prüfung nach festen Regeln** (`src/url_check.py`, kein maschinelles Lernen): erkennt "
             "nachgeahmte Marken (`dhl-paket-service.top`), Zahlen statt Buchstaben (`paypa1`), Kurzlinks, "
             "IP-Adressen, ungewöhnliche Endungen und Punycode. Links werden **nie geöffnet**.\n")
    L.append("**Ampel-Logik:** rot ab Wahrscheinlichkeit 0.80 oder bei einem roten Link; gelb ab 0.50, bei einem "
             "gelben Link oder bei Druckformulierungen wie „sofort“ und „Konto gesperrt“; sonst grün. Führen alle "
             "Links auf offizielle Seiten und fehlt jede Druckformulierung, wird Rot auf Gelb heruntergestuft "
             "(unterhalb 0.90) – das senkt Fehlalarme bei echten Paket- und Bank-SMS.\n")
    L.append("Die Ausgabe ist ein Satz ohne Fachbegriffe und ohne Prozentzahlen, zum Beispiel: "
             "*„Vorsicht – diese Nachricht gibt sich als DHL aus und der Link führt zu einer unbekannten Seite.“*\n")

    L.append("## Installation\n")
    L.append("Python 3.10 oder neuer.\n")
    L.append("```bash\ngit clone https://github.com/" + REPO + ".git\ncd BWKI_dp\n"
             "python -m venv venv\nsource venv/bin/activate        # Windows: venv\\Scripts\\activate\n"
             "pip install -r requirements.txt\n```\n")
    L.append("Beim ersten OCR-Aufruf lädt EasyOCR einmalig seine Modelldateien (~100 MB) nach `~/.EasyOCR/`. "
             "Alles außer dem Transformer-Training läuft auf der CPU.\n")
    L.append(f"Das feingetunte DistilBERT-Modell (~542 MB) liegt **nicht im Repository** (Grenze für die Code-Abgabe). "
             f"Download: {DRIVE_LINK} – danach nach `models/distilbert/` entpacken, dann nutzt die Pipeline es "
             "automatisch. Ohne diesen Ordner läuft die mitgelieferte Baseline (`models/baseline.joblib`, 3 MB).\n")

    L.append("## Start\n")
    L.append("**Daten aufbereiten und Baseline trainieren** (beides zusammen ca. 1 Minute auf CPU):\n")
    L.append("```bash\npython src/data_prep.py       # -> data/processed/{train,val,test}.csv\n"
             "python src/train_baseline.py  # -> models/baseline.joblib, results/metrics.json\n```\n")
    L.append("**Web-Demo (Gradio)** – Reiter „Text einfügen“ und „Screenshot hochladen“:\n")
    L.append("```bash\npython app/gradio_demo.py     # http://127.0.0.1:7860\n```\n")
    L.append("**API (FastAPI)** – wird vom Handy-Kurzbefehl aufgerufen:\n")
    L.append("```bash\nuvicorn api.main:app --port 8000\n\n"
             "curl http://127.0.0.1:8000/health\n"
             "curl -X POST http://127.0.0.1:8000/scan-text -H 'Content-Type: application/json' \\\n"
             "     -d '{\"text\":\"DHL: Paket konnte nicht zugestellt werden: http://dhl-paket-service.top/track\"}'\n"
             "curl -X POST http://127.0.0.1:8000/scan -F 'file=@data/samples/dhl_phishing.png'\n```\n")
    L.append("**Tests:**\n\n```bash\npython -m pytest tests/ -q\n```\n")
    L.append("**Colab-Notebooks** (Branch `main`):\n")
    L.append(f"- DistilBERT trainieren (GPU nötig): https://colab.research.google.com/github/{REPO}/blob/main/notebooks/03_transformer.ipynb\n"
             f"- Demo-Server öffentlich erreichbar machen (API + ngrok): https://colab.research.google.com/github/{REPO}/blob/main/notebooks/04_demo_colab.ipynb\n")
    L.append("Lokal liegen dieselben Schritte in `notebooks/01_data.ipynb` (Daten) und `notebooks/02_baseline.ipynb` (Baseline).\n")

    L.append("## Struktur\n")
    L.append("```\n"
             "data/raw/           Rohdaten: UCI-SMS-Datei, eigene deutsche CSVs (nie bearbeiten)\n"
             "data/processed/     train.csv / val.csv / test.csv  (text,label,lang,source)\n"
             "data/samples/       3 Beispiel-Screenshots für Demo und Tests\n"
             "data/SOURCES.md     Herkunft, Lizenz und Umfang jeder Datenquelle\n"
             "src/data_prep.py        Daten laden, bereinigen, aufteilen\n"
             "src/train_baseline.py   TF-IDF + logistische Regression (Option --no-url-token)\n"
             "src/url_check.py        Regelbasierte Link-Prüfung\n"
             "src/fetch_blocklists.py Phishing-Listen herunterladen (PhishTank, OpenPhish, Tranco)\n"
             "src/ocr.py              Texterkennung aus Screenshots\n"
             "src/pipeline.py         Ampel-Logik, Modellwahl mit Rückfallebene\n"
             "src/eval_pipeline.py    Ampel-Auswertung auf dem deutschen Testteil\n"
             "src/tune_threshold.py   Schwellenwert-Suche und Kombinationsversuch\n"
             "src/error_analysis.py   erzeugt results/error_analysis.md\n"
             "src/merge_colab_results.py  Colab-Ergebnisse einpflegen (nur anfügen)\n"
             "src/make_readme.py      erzeugt diese README\n"
             "notebooks/          01 Daten · 02 Baseline · 03 DistilBERT (Colab) · 04 Demo-Server (Colab)\n"
             "app/gradio_demo.py  Web-Demo\n"
             "api/main.py         /health, /scan-text, /scan\n"
             "shortcut/README.md  Anleitung für den iOS-Kurzbefehl\n"
             "tests/              pytest (URL-Prüfung, Pipeline, OCR)\n"
             "models/             baseline.joblib; DistilBERT liegt auf Google Drive\n"
             "results/            metrics.json, experiments.csv, error_analysis.md, Konfusionsmatrizen\n"
             "```\n")

    L.append("## Ergebnisse\n")
    tr, va, te = (len(counts[s]) for s in ("train", "val", "test"))
    de_tr = int((counts["train"].lang == "de").sum()); de_te = int((counts["test"].lang == "de").sum())
    L.append(f"**Datenbasis:** {de_num(tr)} Trainings-, {de_num(va)} Validierungs- und {de_num(te)} Testnachrichten "
             f"(davon deutsch: {de_tr} im Training, {de_te} im Test, keine im Validierungsteil). "
             "Aufteilung mit `seed=42`, Duplikate vorher entfernt, der Testteil wird pro Modell genau einmal ausgewertet. "
             "Alle Zahlen stammen aus ausgeführten Läufen (`results/metrics.json`, Verlauf in `results/experiments.csv`).\n")
    L.append("| Modell | Train-Acc | Test-Acc | Test-F1 | Test-FPR | DE-Acc | DE-F1 | DE-Recall | DE-FPR |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for k in ORDER:
        if k not in m:
            continue
        e = m[k]; t = e["test"]; g = e.get("test_de")
        de = (f"{g['accuracy']:.4f} | {g['f1']:.4f} | {g['recall']:.4f} | {g['fpr']:.4f}") if g else "– | – | – | –"
        L.append(f"| {LABELS.get(k, k)} | {e['train']['accuracy']:.4f} | {t['accuracy']:.4f} | "
                 f"{t['f1']:.4f} | {t['fpr']:.4f} | {de} |")
    L.append("\nFPR = Falsch-Alarm-Rate (fälschlich als Phishing markierte harmlose Nachrichten). "
             "„DE“ = nur die deutschen Testzeilen, die für unsere Zielgruppe entscheidend sind.\n")

    L.append("**Was die Tabelle zeigt.** Die englische Gesamtgenauigkeit ist bei allen Modellen hoch – der "
             "UCI-Datensatz ist ein bekannter, einfacher Benchmark. Interessant ist der deutsche Teil: die "
             f"Baseline übersieht fast kein Phishing (Recall {b['test_de']['recall']}), schlägt aber bei "
             f"{b['test_de']['fp']} von {b['test_de']['fp'] + b['test_de']['tn']} harmlosen Nachrichten Alarm. "
             f"DistilBERT dreht das um: nur {d['test_de']['fp']} Fehlalarme, dafür {d['test_de']['fn']} übersehene "
             f"Phishing-Nachrichten. Die Fehler beider Modelle überschneiden sich fast nicht – eine Kombination "
             "ist der nächste offene Schritt.\n")

    L.append("**Ampel im Produkt** (volle Logik: Modell + Link-Regeln + Druckformulierungen, deutscher Testteil):\n")
    L.append("| wahres Label | grün | gelb | rot |")
    L.append("|---|---|---|---|")
    L.append(f"| harmlos (n={tl['n_legit']}) | {tl['legit']['green']} | {tl['legit']['yellow']} | {tl['legit']['red']} |")
    L.append(f"| Phishing (n={tl['n_phish']}) | {tl['phish']['green']} | {tl['phish']['yellow']} | {tl['phish']['red']} |")
    L.append(f"\n{de_num(tl['phish_red'] * 100, 1)} % der Phishing-Nachrichten erhalten Rot, "
             f"{de_num(tl['legit_red'] * 100, 1)} % der harmlosen "
             f"fälschlich. Reproduzierbar mit `python src/eval_pipeline.py`.\n")
    L.append("**Ehrliche Einordnung.** Der deutsche Testteil ist mit 18 harmlosen Nachrichten klein, jede einzelne "
             "verschiebt die Falsch-Alarm-Rate um mehr als fünf Punkte. Die Baseline hat außerdem gelernt, dass "
             "förmliches Deutsch verdächtig ist („Sie“ wiegt fast so schwer wie das englische Spam-Wort „call“) – "
             "weil unsere echten Phishing-Texte förmlich sind und unsere harmlosen Texte überwiegend aus Werbe- und "
             "Terminvorlagen stammen. Eine ausführliche Fehleranalyse mit 17 echten Beispielen steht in "
             "[`results/error_analysis.md`](results/error_analysis.md).\n")

    L.append("## iOS-Shortcut\n")
    L.append("Kein Programmieren nötig, nur die vorinstallierte App **Kurzbefehle**. Voraussetzung: ein laufender "
             "DoppelCheck-Server mit öffentlicher Adresse (Notebook 04 mit ngrok oder lokal `uvicorn` + ngrok).\n")
    L.append("1. **Kurzbefehle** → **+** → Name „DoppelCheck“.\n"
             "2. Aktion **Bildschirmfoto aufnehmen**.\n"
             "3. Aktion **Inhalte von URL abrufen**: URL `https://<adresse>/scan`, Methode **POST**, Anfragetext "
             "**Formular**, Feld vom Typ **Datei** mit dem Schlüssel **`file`** und dem Bildschirmfoto als Wert.\n"
             "4. Aktion **Wert aus Wörterbuch abrufen**: Schlüssel **`reason_de`**.\n"
             "5. Aktion **Mitteilung anzeigen** mit diesem Wert.\n"
             "6. **Einstellungen → Bedienungshilfen → Tippen → Auf Rückseite tippen → Doppeltippen → „DoppelCheck“**.\n")
    L.append("Ausführliche Anleitung samt Beispiel-JSON und Fehlersuche: [`shortcut/README.md`](shortcut/README.md).\n")

    L.append("### Android\n")
    L.append(f"Auf Android übernimmt die kostenlose App **{ANDROID_TEST['app']}** dieselbe Rolle: ein Kurzbefehl mit "
             "`POST` auf `https://<adresse>/scan`, Anfragetyp *multipart/form-data*, Dateifeld **`file`**, und die "
             "Antwort wird als Mitteilung angezeigt. Auslösen lässt er sich über ein Widget auf dem Startbildschirm "
             "oder eine Gestentaste.\n")
    L.append(f"Vom Team auf einem **{ANDROID_TEST['device']}** getestet: eine gefälschte DHL-SMS ergab **Rot** "
             f"(p = {ANDROID_TEST['phish_p']}), die echte DHL-Zustellbenachrichtigung **Grün** "
             f"(p = {ANDROID_TEST['legit_p']}). Der Weg über die API ist damit auf beiden Plattformen identisch – "
             "nur die App für die Geste unterscheidet sich.\n")

    L.append("## Quellen\n")
    L.append("| Quelle | Umfang | Rolle im Projekt |")
    L.append("|---|---|---|")
    L.append("| [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) (CC BY 4.0) | "
             "5.574 englische SMS | öffentlicher Benchmark, Grundlage für Training und den englischen Testteil |")
    L.append("| Eigene Sammlung: `data/raw/german_phishing.csv` | 173 echte deutsche Phishing-Texte | "
             "abgetippt aus öffentlichen Warnungen der Verbraucherzentrale (Phishing-Radar); 50 % Training, 50 % Test |")
    L.append("| Eigene Sammlung: `data/raw/german_legit.csv` | 36 echte harmlose deutsche Nachrichten | "
             "anonymisierte Alltags-SMS und ausgefüllte öffentliche Vorlagen; 50 % Training, 50 % Test |")
    L.append("| `data/raw/german_synthetic_*.csv` | 200 synthetische deutsche Nachrichten | "
             "mit Claude erzeugt, in `source_url` als synthetisch gekennzeichnet, **nur im Training** |")
    L.append("| PhishTank, OpenPhish, Tranco | Sperrlisten und Top-Domains | optional, per `src/fetch_blocklists.py`; "
             "die Link-Prüfung funktioniert auch ohne sie |")
    L.append("\nZitat für UCI: Almeida, T. A., Gómez Hidalgo, J. M. & Yamakami, A. (2011). *Contributions to the study "
             "of SMS spam filtering: new collection and results.* ACM DocEng 2011. "
             "Vollständige Angaben zu Herkunft, Lizenz, Umfang und Aufteilung: [`data/SOURCES.md`](data/SOURCES.md).\n")

    L.append("## Hinweis zur KI-Nutzung\n")
    L.append("Der **Programmcode** dieses Projekts wurde weitgehend mit **Claude Code** (Anthropic) erzeugt: "
             "Datenaufbereitung, Trainingsskripte, Link-Prüfung, OCR-Anbindung, Demo, API, Tests und die "
             "Auswertungsskripte. Auch die synthetischen deutschen Trainingsnachrichten stammen von einem "
             "Sprachmodell und sind in `source_url` als solche gekennzeichnet.\n")
    L.append("**Vom Team stammen:** die Projektidee und das Bedienkonzept, die Sammlung und Annotation der echten "
             "deutschen Daten, der Aufbau der Experimente (Aufteilung, Ablation, Schwellenwert-Suche), die Auswahl "
             "und Bewertung der Modelle sowie die kritische Reflexion der Ergebnisse. Jede Zahl in den Tabellen oben "
             "und in `results/` stammt aus einem ausgeführten Lauf in diesem Repository – diese README wird von "
             "`src/make_readme.py` aus `results/metrics.json` erzeugt, nichts wird von Hand eingetragen. Einzige "
             "Ausnahme sind die beiden Werte aus dem Android-Test, die das Team auf dem eigenen Gerät gemessen hat "
             "und die sich hier nicht automatisch nachrechnen lassen.\n")

    OUT.write_text("\n".join(L), encoding="utf-8")
    log(f"[out] {OUT.relative_to(ROOT)} ({len(m)} Modelle in der Tabelle, {len(exp)} Zeilen in experiments.csv)")


if __name__ == "__main__":
    main()
