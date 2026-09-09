# Datenquellen

## 1. UCI SMS Spam Collection (verwendet)

| Feld | Wert |
|---|---|
| Name | SMS Spam Collection |
| URL | https://archive.ics.uci.edu/dataset/228/sms+spam+collection |
| Download | https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip |
| Lizenz | CC BY 4.0 |
| Größe | 5.574 SMS (4.827 ham, 747 spam), Englisch |
| Zitat | Almeida, T. A., Gómez Hidalgo, J. M. & Yamakami, A. (2011). *Contributions to the study of SMS spam filtering: new collection and results.* ACM DocEng 2011. |
| Im Projekt | `source="uci_sms"`, `lang="en"`, ham→0, spam→1 |

Fallback: Ist `archive.ics.uci.edu` nicht erreichbar, lädt `src/data_prep.py`
die wortgetreu gespiegelte Datei `SMSSpamCollection` (5.574 Zeilen, Tab-getrennt)
von GitHub (`justmarkham/pycon-2016-tutorial`, `justmarkham/DAT8`).
Beim Erstlauf am 2026-09-09 wurde der Spiegel benutzt (Original per Netzwerkrichtlinie gesperrt).

## 2. Zweite englische Quelle: HuggingFace Hub (NICHT verifiziert)

| Feld | Wert |
|---|---|
| Name | `SetFit/enron_spam` (E-Mail-Spam, Enron-Korpus) |
| URL | https://huggingface.co/datasets/SetFit/enron_spam |
| Lizenz | unbekannt – auf der Hub-Seite prüfen, bevor die Daten verwendet werden |
| Größe | laut Hub ca. 31.700 Train + 2.000 Test (nicht selbst geprüft) |
| Im Projekt | `source="hf_setfit_enron_spam"`, `lang="en"`, Texte auf 512 Zeichen gekürzt |

**Status:** Der Hub (`huggingface.co`) war aus der Entwicklungsumgebung per
Netzwerkrichtlinie gesperrt (HTTP 403). `load_hf_dataset()` in `src/data_prep.py`
fängt den Fehler ab und das Projekt lief **nur mit UCI** weiter. Der Code-Pfad
für den Hub-Datensatz ist geschrieben, aber **ungetestet**. Beim ersten Lauf
auf einem Rechner mit Internet bitte prüfen: Zeilenzahl, Spalten `text`/`label`,
Lizenz – und diese Tabelle danach korrigieren.

## 3. Eigene deutsche Daten (Vorlagen)

| Datei | Inhalt |
|---|---|
| `data/raw/german_phishing.csv` | Phishing-Nachrichten, `label=1` (z. B. aus Phishing-Radar der Verbraucherzentrale) |
| `data/raw/german_legit.csv` | echte, anonymisierte Alltagsnachrichten, `label=0` |

Spalten: `text,label,source_url,category` (category z. B. Paket, Bank, Behörde,
Gewinnspiel, Familie). Beide Dateien wurden am 2026-09-09 als **Vorlagen** mit je
2 Beispielzeilen angelegt (`source_url=BEISPIEL`); solche Beispielzeilen werden
vom Skript ignoriert. `data/raw/` ist in `.gitignore` – die gesammelten Texte
bleiben lokal.
