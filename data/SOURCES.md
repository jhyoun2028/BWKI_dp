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

## 3. Eigene deutsche Daten (seit 2026-09-09 im Repo)

| Datei | Zeilen | Inhalt | Verwendung |
|---|---|---|---|
| `data/raw/german_phishing.csv` | 173 | echte Phishing-SMS/-Mails, abgetippt aus Warnungen der Verbraucherzentrale (Phishing-Radar, Paketdienst-SMS, Fake-Banking-SMS, „Hallo Mama“-Betrug, Voicemail-Betrug); `source_url` = Artikel-URL; Links dort als `*Link*` maskiert | 50 % Training, 50 % Test |
| `data/raw/german_legit.csv` | 36 | normale deutsche Nachrichten: öffentliche SMS-Vorlagen (Marketing, Terminerinnerung) mit ausgefüllten Platzhaltern sowie echte Paket-/Shop-/Verifizierungs-SMS (anonymisiert); Quelle in `source_url` | 50 % Training, 50 % Test |
| `data/raw/german_synthetic_phishing.csv` | 70 | **synthetisch**, mit Claude (Anthropic) am 2026-09-09 erzeugt, so in `source_url` vermerkt | **nur Training** |
| `data/raw/german_synthetic_legit.csv` | 70 | **synthetisch**, ebenso | **nur Training** |
| `data/raw/german_synthetic_legit_v2.csv` | 60 | **synthetisch** (v2, 2026-09-09): formelle Nachrichten mit offiziellem Link (Paket, Bank, Termin, Behörde, Telekom, Familie), so in `source_url` vermerkt | **nur Training** |

Spalten: `text,label,source_url,category` (Kategorien Phishing: paket, bank, telekom, behoerde,
whatsapp_familie, …; Legit: marketing, termin, paket_echt, shopping_echt, verifizierung, …).
Lizenz: eigene Sammlung des Teams; Verbraucherzentrale-Texte sind kurze Zitate aus öffentlichen
Warnmeldungen zu Bildungszwecken.

**Aufteilung (seed 42):** echte deutsche Zeilen 50/50 in train/test, stratifiziert nach label × category
(104 / 104 nach Duplikat-Entfernung); synthetische Zeilen (200) ausschließlich im Training; kein deutscher Anteil
in val. **Vorverarbeitung:** echte URLs und der Platzhalter `*Link*` werden vor dem Training durch dasselbe
Token `<URL>` ersetzt (`src/url_check.py: mask_urls`), damit das Modell nicht den Platzhalter lernt.

**Bekannte Schwäche:** nur 36 echte Legit-Zeilen (Ziel ≥ 100), davon 28 aus Marketing-Vorlagen einer
Quelle. Der deutsche Test enthält daher nur 18 Legit-Zeilen – die deutsche Falsch-Alarm-Rate ist grob.
Mehr echte Alltagsnachrichten (Paket, Bank, Arzt, Familie) sind die wichtigste offene Datenaufgabe.

## 4. Vorlagen (historisch)

Bis zum 2026-09-09 lagen die deutschen CSVs nur als Vorlagen mit je 2 Beispielzeilen vor
(`source_url=BEISPIEL`, vom Skript ignoriert). `data_prep.py` legt solche Vorlagen weiterhin an,
falls die Dateien fehlen.
