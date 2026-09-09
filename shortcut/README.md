# iOS-Kurzbefehl „DoppelCheck“ – Betrugsschutz mit einer Geste

Doppeltippen auf die Rückseite des iPhones → Screenshot → Analyse auf dem DoppelCheck-Server →
Ampel-Ergebnis als Mitteilung. Kein Code nötig, nur die App **Kurzbefehle** (vorinstalliert).

## Voraussetzungen

- iPhone 8 oder neuer, iOS 14+ (Back Tap).
- Laufender DoppelCheck-Server mit öffentlicher Adresse, z. B. per Colab + ngrok
  (`notebooks/04_demo_colab.ipynb`) oder lokal mit `uvicorn api.main:app --port 8000` + `ngrok http 8000`.
  Die Adresse sieht so aus: `https://xxxx-xx-xx.ngrok-free.app` – sie ändert sich bei jedem Start!

## Schritt 1 – Kurzbefehl anlegen

App **Kurzbefehle** öffnen → **+** (neuer Kurzbefehl) → Name „DoppelCheck“. Dann diese vier Aktionen
nacheinander hinzufügen (oben über „Aktion hinzufügen“ suchen):

| # | Aktion | Einstellung |
|---|---|---|
| 1 | **Bildschirmfoto aufnehmen** (Take Screenshot) | – |
| 2 | **Inhalte von URL abrufen** (Get Contents of URL) | URL: `https://<ngrok-adresse>/scan` · Methode: **POST** · Anfragetext: **Formular** · Feld hinzufügen: Typ **Datei**, Schlüssel **`file`**, Wert: **Bildschirmfoto** (Variable aus Aktion 1) |
| 3 | **Wert aus Wörterbuch abrufen** (Get Dictionary Value) | Wert für Schlüssel **`reason_de`** in **Inhalte der URL** |
| 4 | **Mitteilung anzeigen** (Show Notification) | Text: **Wörterbuchwert** (aus Aktion 3) · Titel: „DoppelCheck“ |

Optional zwischen 3 und 4: noch ein **Wert aus Wörterbuch abrufen** mit Schlüssel `verdict` und die Mitteilung mit
„🔴/🟡/🟢“ ergänzen.

## Schritt 2 – Geste zuweisen

**Einstellungen → Bedienungshilfen → Tippen → Auf Rückseite tippen → Doppeltippen → „DoppelCheck“** auswählen.

## Schritt 3 – Ausprobieren

Eine verdächtige SMS öffnen, zweimal auf die Rückseite tippen, 3–10 Sekunden warten (OCR + Modell) → Mitteilung
erscheint. Beim ersten Start fragt iOS, ob der Kurzbefehl Bildschirmfotos machen und Daten an die Adresse senden
darf → **Immer erlauben**.

## Was der Server zurückschickt (JSON)

```json
{
  "verdict": "red",
  "score": 0.72,
  "reason_de": "Vorsicht – diese Nachricht gibt sich als DHL aus und der Link führt zu einer unbekannten Seite.",
  "urls": [
    {"url": "http://dhl-paket-service.top/track", "level": "red",
     "reasons": ["Gibt sich als DHL aus, ist aber nicht die offizielle Seite", "Ungewöhnliche Endung .top"]}
  ],
  "model": "baseline_tfidf_logreg",
  "text": "DHL: Ihr Paket konnte nicht zugestellt werden ..."
}
```

`verdict` ist `red`, `yellow` oder `green`; `reason_de` ist der eine Satz, der in der Mitteilung erscheint;
`text` ist der per OCR erkannte Bildschirmtext.

## Häufige Probleme

- **„Verbindung fehlgeschlagen“**: ngrok-Adresse abgelaufen → neue Adresse aus Colab/Terminal in Aktion 2 eintragen.
- **Mitteilung leer**: Feld-Schlüssel muss genau `file` heißen und der Typ **Datei** sein (nicht Text).
- **Dauert lange**: Beim ersten Aufruf lädt der Server das OCR-Modell (einmalig ~30 s).
- Datenschutz: Der Screenshot wird nur zur Analyse gesendet und nicht gespeichert; keine Links werden geöffnet.
