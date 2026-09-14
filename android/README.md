# DoppelCheck für Android

Minimale Android-App (Kotlin, Jetpack Compose) als Gegenstück zum iOS-Kurzbefehl.
Sie enthält **keine eigene Erkennungslogik** – sie schickt Text oder Screenshot an die
FastAPI aus diesem Repository (`api/main.py`) und zeigt die Ampel groß und lesbar an.

- **minSdk 29** (Android 10), targetSdk 34, Jetpack Compose, Material 3
- Schrift nirgends kleiner als **20 sp**, Schaltflächen mindestens **64 dp** hoch,
  Ampelfarben dunkel genug für weiße Schrift – gedacht für ältere Nutzerinnen und Nutzer

## Was die App kann

| Funktion | Wie |
|---|---|
| Text prüfen | Nachricht einfügen oder tippen → **Prüfen** → `POST /scan-text` |
| Geteilten Text prüfen | In einer anderen App „Teilen“ → DoppelCheck → wird sofort geprüft |
| Geteilten Screenshot prüfen | Bild teilen → DoppelCheck → `POST /scan` als `multipart/form-data`, Feld **`file`** |
| Bildschirm prüfen: runder Knopf | Schwebender Knopf über allen Apps (Erlaubnis „Über anderen Apps anzeigen“) – antippen liest den sichtbaren Text, ziehen verschiebt ihn |
| Bildschirm prüfen: Kachel | Kachel in den Schnelleinstellungen (oben herunterwischen → Stift → DoppelCheck hinzufügen). Antippen schließt das Feld und liest den Bildschirm; ist die Bedienungshilfe aus, öffnet sich stattdessen die App |

## Bildschirm prüfen – nichts wird im Hintergrund erfasst

Die Bedienungshilfe `DoppelCheckAccessibilityService` liest den **sichtbaren Text** der App,
die gerade im Vordergrund ist (`text` und `contentDescription` jedes sichtbaren Elements,
der Reihe nach, doppelte Zeilen entfernt).

- **Nur auf ausdrücklichen Auslöser.** `res/xml/accessibility_service_config.xml` meldet
  **keine** Ereignistypen an (`accessibilityEventTypes` fehlt absichtlich). Android schickt
  dem Dienst daher keine Ereignisse – er beobachtet nichts, protokolliert nichts und reagiert
  auf nichts, solange Sie keine Prüfung starten.
- **Nichts wird gespeichert.** Der gelesene Text liegt nur im Arbeitsspeicher, bis die Prüfung
  abgeschlossen ist.
- Android zeigt beim Einschalten trotzdem den allgemeinen Warnhinweis „volle Kontrolle über
  das Gerät“ – dieser Text ist für alle Bedienungshilfen gleich und lässt sich nicht ändern.

Jede Anfrage trägt den Kopfzeileneintrag `ngrok-skip-browser-warning: true`. Ohne ihn
antwortet ein kostenloser ngrok-Tunnel mit einer HTML-Warnseite statt mit unserem JSON.

## Serveradresse eintragen (einmalig)

Die App startet **ohne** Adresse. Zahnrad oben rechts → Adresse eintragen → **Speichern** →
**Verbindung testen**. Gespeichert wird sie in den SharedPreferences (`doppelcheck/base_url`).

- Server über Colab + ngrok starten: `notebooks/04_demo_colab.ipynb`, die ausgegebene Adresse
  sieht aus wie `https://xxxx.ngrok-free.app`.
- Die ngrok-Adresse **ändert sich bei jedem Serverstart** – dann in der App neu eintragen.
  Mit dem Colab-Secret `NGROK_DOMAIN` bleibt sie gleich.
- `https://` darf fehlen, wird ergänzt. Ein Schrägstrich am Ende ist egal.

Nur HTTPS ist erlaubt (`res/xml/network_security_config.xml`). Ausnahmen bestehen für
`10.0.2.2` (Emulator), `127.0.0.1` und `localhost`. Wer den Server unverschlüsselt im eigenen
WLAN betreibt (`http://192.168.…`), muss diese Adresse dort als weitere `<domain>`-Zeile
eintragen – sonst blockiert Android die Verbindung wortlos.

## Bauen und installieren

Voraussetzungen: **JDK 17**, Android SDK mit **Platform 34** und Build-Tools.
Am einfachsten über Android Studio (Giraffe oder neuer), das beides mitbringt.

### Mit Android Studio

1. Android Studio → *Open* → den Ordner **`android/`** auswählen (nicht das Repo-Wurzelverzeichnis).
2. Gradle-Sync abwarten (lädt beim ersten Mal Gradle 8.7 und die Abhängigkeiten).
3. Handy per USB anschließen, USB-Debugging einschalten, auf *Run* drücken.

### Auf der Kommandozeile

```bash
cd android
echo "sdk.dir=$ANDROID_HOME" > local.properties   # oder Pfad zum SDK eintragen

./gradlew assembleDebug                 # APK bauen
./gradlew installDebug                  # direkt auf ein angeschlossenes Gerät installieren
```

Die fertige Datei liegt danach unter `app/build/outputs/apk/debug/app-debug.apk` und lässt
sich auch von Hand übertragen (`adb install -r app/build/outputs/apk/debug/app-debug.apk`)
oder auf dem Handy aus dem Dateimanager öffnen (Installation aus unbekannter Quelle erlauben).

### Signierung

Das Projekt enthält **keine Signierungsschlüssel** und legt auch keine an; Debug-Builds
signiert Android automatisch mit dem lokalen Debug-Schlüssel. Für eine Release-Version
einen eigenen Keystore anlegen und **außerhalb des Repositories** aufbewahren –
`android/.gitignore` schließt `*.jks`, `*.keystore` und `keystore.properties` aus.

## Abhängigkeiten: warum OkHttp gepinnt ist

Retrofit 2.11.0 bringt von sich aus **okhttp 3.14.9** mit – die reine Java-Fassung.
Dort gibt es die Kotlin-Erweiterungen `toMediaTypeOrNull` und `toRequestBody` nicht
(die Klassen `MediaType$Companion` / `RequestBody$Companion` existieren schlicht nicht),
und die Version wird seit 2020 nicht mehr gepflegt. Der erste Build scheiterte genau
daran mit „Unresolved reference: Companion“.

Deshalb hebt `app/build.gradle.kts` die ganze OkHttp-Gruppe über die Stückliste (BOM)
auf **4.12.0** an:

```kotlin
implementation(platform("com.squareup.okhttp3:okhttp-bom:4.12.0"))
implementation("com.squareup.okhttp3:okhttp")
```

4.12.0 setzt Android 5.0 (API 21) voraus – unser `minSdk` ist 29, das passt. Mitgeliefert
werden dadurch Okio 3.6.0 und kotlin-stdlib-jdk8 (die Kotlin-Version des Projekts, 1.9.24,
gewinnt bei der Auflösung).

Nachprüfen statt raten:

```bash
./gradlew :app:okhttpVersion
# erwartet: com.squareup.okhttp3:okhttp:4.12.0 und com.squareup.okio:okio:3.6.0
```

## Aufbau

```
android/
  settings.gradle.kts, build.gradle.kts, gradle.properties, gradlew(.bat)
  app/build.gradle.kts
  app/src/main/AndroidManifest.xml        Berechtigung INTERNET, Teilen-Filter, Kachel-Dienst
  app/src/main/java/de/doppelcheck/app/
    MainActivity.kt        Compose-Einstieg, verarbeitet geteilten Text und geteilte Bilder
    ScanViewModel.kt       Zustand (Idle/Loading/Success/Failure), Anfragen, Fehlertexte
    SettingsStore.kt       Serveradresse in SharedPreferences, normalisiert die Eingabe
    api/Models.kt          Datenklassen passend zur JSON-Antwort der API
    api/DoppelCheckApi.kt  Retrofit-Schnittstelle (@Url, weil die Adresse zur Laufzeit feststeht)
    api/ApiClient.kt       OkHttp mit ngrok-Kopfzeile und großzügigen Zeitlimits
    ui/ScanScreen.kt       Hauptbildschirm: Eingabe, großer Knopf, Ampelbox, Linkliste
    ui/SettingsScreen.kt   Serveradresse eintragen und testen
    ui/Theme.kt            Farben und Schriftgrößen (nichts unter 20 sp)
    ui/ScreenScanSetup.kt  Einstellungen: Einrichtung von „Bildschirm prüfen“
    tile/ScanTileService.kt  Kachel in den Schnelleinstellungen: löst die Bildschirmprüfung aus
    scan/DoppelCheckAccessibilityService.kt  Bedienungshilfe, liest Text nur auf Auslöser
    scan/ScreenTextCollector.kt  Knotenbaum → Text (Tiefensuche, sichtbar, ohne Dopplungen)
    scan/BubbleOverlay.kt  runder, verschiebbarer Knopf (SYSTEM_ALERT_WINDOW)
    scan/SystemSettings.kt öffnet die nötigen Systemeinstellungen
```

## Antwort des Servers

```json
{
  "verdict": "red",
  "score": 0.9337,
  "reason_de": "Vorsicht – diese Nachricht gibt sich als DHL aus und der Link führt zu einer unbekannten Seite.",
  "urls": [
    {
      "url": "http://dhl-paket-service.top/track",
      "level": "red",
      "reasons": ["Gibt sich als DHL aus, ist aber nicht die offizielle Seite", "Ungewöhnliche Endung .top"],
      "trusted": false
    }
  ],
  "model": "baseline_tfidf_logreg"
}
```

`verdict` ist `red`, `yellow` oder `green` und färbt die Box. `reason_de` ist der Satz in
großer Schrift. Bei `POST /scan` kommt zusätzlich `text` zurück – der per Texterkennung
gelesene Bildschirmtext, den die App unter dem Ergebnis anzeigt.

## Bekannte Einschränkungen

- **Hier nicht kompilierbar.** Die Entwicklungsumgebung dieses Repos hat kein Android SDK,
  der Code wird also geschrieben und geprüft, aber nicht gebaut. Der erste Build auf einem
  echten Rechner (2026-09-12) scheiterte an vier Kotlin-Fehlern in `ScanViewModel.kt`
  wegen der zu alten OkHttp-Version; behoben durch den Pin oben. Weitere Anpassungen beim
  nächsten Build sind möglich.
- Beim Teilen mehrerer Bilder auf einmal (`ACTION_SEND_MULTIPLE`) passiert nichts; die App
  verarbeitet bewusst nur ein einzelnes Bild.
- Die App speichert nichts: keine Nachrichten, keine Bilder, keine Verläufe. Gesendet wird
  nur an die selbst eingetragene Serveradresse.
- Links werden nie geöffnet – weder von der App noch vom Server.
