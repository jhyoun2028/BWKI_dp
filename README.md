# DoppelCheck – Phishing-Erkennung für SMS und Kurznachrichten

**Betrugsschutz mit einer Geste.** Zweimal auf die Rückseite des Handys tippen, der aktuelle Bildschirm wird geprüft, und wenige Sekunden später erscheint eine Ampel mit einem Satz in einfachem Deutsch. Gedacht für ältere Menschen in Deutschland, die täglich gefälschte Paket-, Bank- und Behörden-SMS bekommen.

## Projekt

DoppelCheck prüft eine Nachricht auf drei Ebenen und fasst das Ergebnis zu einer Ampel zusammen:

1. **Texterkennung** (`src/ocr.py`): Aus dem Screenshot wird mit EasyOCR (Deutsch + Englisch, CPU) Text.
2. **Sprachmodell** (`src/pipeline.py`): Ein Klassifikator schätzt, wie wahrscheinlich die Nachricht Betrug ist. Aktiv ist die Baseline; liegt `models/distilbert/` lokal vor, wird automatisch DistilBERT benutzt.
3. **Link-Prüfung nach festen Regeln** (`src/url_check.py`, kein maschinelles Lernen): erkennt nachgeahmte Marken (`dhl-paket-service.top`), Zahlen statt Buchstaben (`paypa1`), Kurzlinks, IP-Adressen, ungewöhnliche Endungen und Punycode. Links werden **nie geöffnet**.

**Ampel-Logik:** rot ab Wahrscheinlichkeit 0.80 oder bei einem roten Link; gelb ab 0.50, bei einem gelben Link oder bei Druckformulierungen wie „sofort“ und „Konto gesperrt“; sonst grün. Führen alle Links auf offizielle Seiten und fehlt jede Druckformulierung, wird Rot auf Gelb heruntergestuft (unterhalb 0.90) – das senkt Fehlalarme bei echten Paket- und Bank-SMS.

Die Ausgabe ist ein Satz ohne Fachbegriffe und ohne Prozentzahlen, zum Beispiel: *„Vorsicht – diese Nachricht gibt sich als DHL aus und der Link führt zu einer unbekannten Seite.“*

## Installation

Python 3.10 oder neuer.

```bash
git clone https://github.com/jhyoun2028/BWKI_dp.git
cd BWKI_dp
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Beim ersten OCR-Aufruf lädt EasyOCR einmalig seine Modelldateien (~100 MB) nach `~/.EasyOCR/`. Alles außer dem Transformer-Training läuft auf der CPU.

Das feingetunte DistilBERT-Modell (~542 MB) liegt **nicht im Repository** (Grenze für die Code-Abgabe). Download: <Google-Drive-Freigabelink hier eintragen> – danach nach `models/distilbert/` entpacken, dann nutzt die Pipeline es automatisch. Ohne diesen Ordner läuft die mitgelieferte Baseline (`models/baseline.joblib`, 3 MB).

## Start

**Daten aufbereiten und Baseline trainieren** (beides zusammen ca. 1 Minute auf CPU):

```bash
python src/data_prep.py       # -> data/processed/{train,val,test}.csv
python src/train_baseline.py  # -> models/baseline.joblib, results/metrics.json
```

**Web-Demo (Gradio)** – Reiter „Text einfügen“ und „Screenshot hochladen“:

```bash
python app/gradio_demo.py     # http://127.0.0.1:7860
```

**API (FastAPI)** – wird vom Handy-Kurzbefehl aufgerufen:

```bash
uvicorn api.main:app --port 8000

curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/scan-text -H 'Content-Type: application/json' \
     -d '{"text":"DHL: Paket konnte nicht zugestellt werden: http://dhl-paket-service.top/track"}'
curl -X POST http://127.0.0.1:8000/scan -F 'file=@data/samples/dhl_phishing.png'
```

**Tests:**

```bash
python -m pytest tests/ -q
```

**Colab-Notebooks** (Branch `main`):

- DistilBERT trainieren (GPU nötig): https://colab.research.google.com/github/jhyoun2028/BWKI_dp/blob/main/notebooks/03_transformer.ipynb
- Demo-Server öffentlich erreichbar machen (API + ngrok): https://colab.research.google.com/github/jhyoun2028/BWKI_dp/blob/main/notebooks/04_demo_colab.ipynb

Lokal liegen dieselben Schritte in `notebooks/01_data.ipynb` (Daten) und `notebooks/02_baseline.ipynb` (Baseline).

## Struktur

```
data/raw/           Rohdaten: UCI-SMS-Datei, eigene deutsche CSVs (nie bearbeiten)
data/processed/     train.csv / val.csv / test.csv  (text,label,lang,source)
data/samples/       3 Beispiel-Screenshots für Demo und Tests
data/SOURCES.md     Herkunft, Lizenz und Umfang jeder Datenquelle
src/data_prep.py        Daten laden, bereinigen, aufteilen
src/train_baseline.py   TF-IDF + logistische Regression (Option --no-url-token)
src/url_check.py        Regelbasierte Link-Prüfung
src/fetch_blocklists.py Phishing-Listen herunterladen (PhishTank, OpenPhish, Tranco)
src/ocr.py              Texterkennung aus Screenshots
src/pipeline.py         Ampel-Logik, Modellwahl mit Rückfallebene
src/eval_pipeline.py    Ampel-Auswertung auf dem deutschen Testteil
src/tune_threshold.py   Schwellenwert-Suche und Kombinationsversuch
src/error_analysis.py   erzeugt results/error_analysis.md
src/merge_colab_results.py  Colab-Ergebnisse einpflegen (nur anfügen)
src/make_readme.py      erzeugt diese README
notebooks/          01 Daten · 02 Baseline · 03 DistilBERT (Colab) · 04 Demo-Server (Colab)
app/gradio_demo.py  Web-Demo
api/main.py         /health, /scan-text, /scan
shortcut/README.md  Anleitung für den iOS-Kurzbefehl
tests/              pytest (URL-Prüfung, Pipeline, OCR)
models/             baseline.joblib; DistilBERT liegt auf Google Drive
results/            metrics.json, experiments.csv, error_analysis.md, Konfusionsmatrizen
```

## Ergebnisse

**Datenbasis:** 4.408 Trainings-, 513 Validierungs- und 617 Testnachrichten (davon deutsch: 304 im Training, 104 im Test, keine im Validierungsteil). Aufteilung mit `seed=42`, Duplikate vorher entfernt, der Testteil wird pro Modell genau einmal ausgewertet. Alle Zahlen stammen aus ausgeführten Läufen (`results/metrics.json`, Verlauf in `results/experiments.csv`).

| Modell | Train-Acc | Test-Acc | Test-F1 | Test-FPR | DE-Acc | DE-F1 | DE-Recall | DE-FPR |
|---|---|---|---|---|---|---|---|---|
| Baseline TF-IDF + LogReg **(aktiv)** | 0.9986 | 0.9789 | 0.9568 | 0.0171 | 0.9231 | 0.9551 | 0.9884 | 0.3889 |
| DistilBERT multilingual | 0.9959 | 0.9757 | 0.9477 | 0.0043 | 0.8942 | 0.9333 | 0.8953 | 0.1111 |
| Baseline ohne `<URL>`-Token (Ablation) | 0.9955 | 0.9773 | 0.9539 | 0.0214 | 0.9135 | 0.9503 | 1.0000 | 0.5000 |
| Baseline, Schwelle 0.22 (getunt auf val) | 0.9816 | 0.9595 | 0.9216 | 0.0491 | 0.8654 | 0.9247 | 1.0000 | 0.7778 |
| Baseline ohne Token, Schwelle 0.32 | 0.9766 | 0.9627 | 0.9274 | 0.0449 | 0.8750 | 0.9297 | 1.0000 | 0.7222 |
| ODER-Kombination beider Baselines | 0.9746 | 0.9579 | 0.9187 | 0.0513 | 0.8654 | 0.9247 | 1.0000 | 0.7778 |

FPR = Falsch-Alarm-Rate (fälschlich als Phishing markierte harmlose Nachrichten). „DE“ = nur die deutschen Testzeilen, die für unsere Zielgruppe entscheidend sind.

**Was die Tabelle zeigt.** Die englische Gesamtgenauigkeit ist bei allen Modellen hoch – der UCI-Datensatz ist ein bekannter, einfacher Benchmark. Interessant ist der deutsche Teil: die Baseline übersieht fast kein Phishing (Recall 0.9884), schlägt aber bei 7 von 18 harmlosen Nachrichten Alarm. DistilBERT dreht das um: nur 2 Fehlalarme, dafür 9 übersehene Phishing-Nachrichten. Die Fehler beider Modelle überschneiden sich fast nicht – eine Kombination ist der nächste offene Schritt.

**Ampel im Produkt** (volle Logik: Modell + Link-Regeln + Druckformulierungen, deutscher Testteil):

| wahres Label | grün | gelb | rot |
|---|---|---|---|
| harmlos (n=18) | 10 | 6 | 2 |
| Phishing (n=86) | 1 | 7 | 78 |

90,7 % der Phishing-Nachrichten erhalten Rot, 11,1 % der harmlosen fälschlich. Reproduzierbar mit `python src/eval_pipeline.py`.

**Ehrliche Einordnung.** Der deutsche Testteil ist mit 18 harmlosen Nachrichten klein, jede einzelne verschiebt die Falsch-Alarm-Rate um mehr als fünf Punkte. Die Baseline hat außerdem gelernt, dass förmliches Deutsch verdächtig ist („Sie“ wiegt fast so schwer wie das englische Spam-Wort „call“) – weil unsere echten Phishing-Texte förmlich sind und unsere harmlosen Texte überwiegend aus Werbe- und Terminvorlagen stammen. Eine ausführliche Fehleranalyse mit 17 echten Beispielen steht in [`results/error_analysis.md`](results/error_analysis.md).

## iOS-Shortcut

Kein Programmieren nötig, nur die vorinstallierte App **Kurzbefehle**. Voraussetzung: ein laufender DoppelCheck-Server mit öffentlicher Adresse (Notebook 04 mit ngrok oder lokal `uvicorn` + ngrok).

1. **Kurzbefehle** → **+** → Name „DoppelCheck“.
2. Aktion **Bildschirmfoto aufnehmen**.
3. Aktion **Inhalte von URL abrufen**: URL `https://<adresse>/scan`, Methode **POST**, Anfragetext **Formular**, Feld vom Typ **Datei** mit dem Schlüssel **`file`** und dem Bildschirmfoto als Wert.
4. Aktion **Wert aus Wörterbuch abrufen**: Schlüssel **`reason_de`**.
5. Aktion **Mitteilung anzeigen** mit diesem Wert.
6. **Einstellungen → Bedienungshilfen → Tippen → Auf Rückseite tippen → Doppeltippen → „DoppelCheck“**.

Ausführliche Anleitung samt Beispiel-JSON und Fehlersuche: [`shortcut/README.md`](shortcut/README.md).

### Android

Auf Android übernimmt die kostenlose App **HTTP Shortcuts** dieselbe Rolle: ein Kurzbefehl mit `POST` auf `https://<adresse>/scan`, Anfragetyp *multipart/form-data*, Dateifeld **`file`**, und die Antwort wird als Mitteilung angezeigt. Auslösen lässt er sich über ein Widget auf dem Startbildschirm oder eine Gestentaste.

Vom Team auf einem **Samsung Galaxy** getestet: eine gefälschte DHL-SMS ergab **Rot** (p = 0.9785), die echte DHL-Zustellbenachrichtigung **Grün** (p = 0.0679). Der Weg über die API ist damit auf beiden Plattformen identisch – nur die App für die Geste unterscheidet sich.

## Quellen

| Quelle | Umfang | Rolle im Projekt |
|---|---|---|
| [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) (CC BY 4.0) | 5.574 englische SMS | öffentlicher Benchmark, Grundlage für Training und den englischen Testteil |
| Eigene Sammlung: `data/raw/german_phishing.csv` | 173 echte deutsche Phishing-Texte | abgetippt aus öffentlichen Warnungen der Verbraucherzentrale (Phishing-Radar); 50 % Training, 50 % Test |
| Eigene Sammlung: `data/raw/german_legit.csv` | 36 echte harmlose deutsche Nachrichten | anonymisierte Alltags-SMS und ausgefüllte öffentliche Vorlagen; 50 % Training, 50 % Test |
| `data/raw/german_synthetic_*.csv` | 200 synthetische deutsche Nachrichten | mit Claude erzeugt, in `source_url` als synthetisch gekennzeichnet, **nur im Training** |
| PhishTank, OpenPhish, Tranco | Sperrlisten und Top-Domains | optional, per `src/fetch_blocklists.py`; die Link-Prüfung funktioniert auch ohne sie |

Zitat für UCI: Almeida, T. A., Gómez Hidalgo, J. M. & Yamakami, A. (2011). *Contributions to the study of SMS spam filtering: new collection and results.* ACM DocEng 2011. Vollständige Angaben zu Herkunft, Lizenz, Umfang und Aufteilung: [`data/SOURCES.md`](data/SOURCES.md).

## Hinweis zur KI-Nutzung

Der **Programmcode** dieses Projekts wurde weitgehend mit **Claude Code** (Anthropic) erzeugt: Datenaufbereitung, Trainingsskripte, Link-Prüfung, OCR-Anbindung, Demo, API, Tests und die Auswertungsskripte. Auch die synthetischen deutschen Trainingsnachrichten stammen von einem Sprachmodell und sind in `source_url` als solche gekennzeichnet.

**Vom Team stammen:** die Projektidee und das Bedienkonzept, die Sammlung und Annotation der echten deutschen Daten, der Aufbau der Experimente (Aufteilung, Ablation, Schwellenwert-Suche), die Auswahl und Bewertung der Modelle sowie die kritische Reflexion der Ergebnisse. Jede Zahl in den Tabellen oben und in `results/` stammt aus einem ausgeführten Lauf in diesem Repository – diese README wird von `src/make_readme.py` aus `results/metrics.json` erzeugt, nichts wird von Hand eingetragen. Einzige Ausnahme sind die beiden Werte aus dem Android-Test, die das Team auf dem eigenen Gerät gemessen hat und die sich hier nicht automatisch nachrechnen lassen.
