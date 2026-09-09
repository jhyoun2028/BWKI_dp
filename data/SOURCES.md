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

## 2. Zweite englische Quelle – NICHT VERWENDET

Ein zweiter englischer Datensatz vom HuggingFace Hub (`SetFit/enron_spam`,
https://huggingface.co/datasets/SetFit/enron_spam) war ursprünglich vorgesehen.
**Entscheidung vom 2026-09-09:** nicht verwendet. Die Daten des Projekts sind
ausschließlich UCI (öffentlicher Benchmark) + eigene deutsche Sammlung. Der Hub
war aus der Entwicklungsumgebung ohnehin gesperrt (HTTP 403); der Lade-Code wurde
aus `src/data_prep.py` entfernt.

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
