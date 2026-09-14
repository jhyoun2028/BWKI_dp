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
| Bildschirm prüfen: Assistenten-Geste | Mit DoppelCheck als digitalem Assistenten: Startknopf lange drücken bzw. bei Gestensteuerung von einer unteren Ecke schräg nach oben wischen |

Jede Anfrage trägt den Kopfzeileneintrag `ngrok-skip-browser-warning: true`. Ohne ihn
antwortet ein kostenloser ngrok-Tunnel mit einer HTML-Warnseite statt mit unserem JSON.

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
- Ausnahme nur für Entwickler: In **Debug-Builds** schreibt `ApiClient` Anfrage und Antwort
  (also auch den gelesenen Text) nach Logcat. Release-Builds tun das nicht.

## Bildschirm prüfen einrichten (einmalig)

Vorher die Serveradresse eintragen (nächster Abschnitt). Alle drei Schalter sind auch in der
App erreichbar: **Zahnrad → „Bildschirm prüfen einrichten“** zeigt, was schon erledigt ist,
und öffnet mit je einem Knopf die richtige Systemseite. Die Menünamen unten stammen von
Android ohne Herstelleroberfläche; bei Samsung & Co. heißen sie teils etwas anders
(Hinweise in Klammern).

**1. Bedienungshilfe einschalten** (Pflicht – ohne sie kann nichts gelesen werden)

1. *Einstellungen → Bedienungshilfen* öffnen.
2. *Installierte Apps* bzw. *Heruntergeladene Apps* antippen
   (Samsung: *Installierte Apps*).
3. **DoppelCheck – Bildschirm prüfen** antippen und den Schalter einschalten.
4. Den Warnhinweis „volle Kontrolle“ mit **Zulassen** bestätigen.
   Android 13 und neuer: Ist der Schalter ausgegraut („Eingeschränkte Einstellung“), weil die
   APK nicht aus dem Play Store kommt: *Einstellungen → Apps → DoppelCheck* → oben rechts ⋮ →
   **Eingeschränkte Einstellungen zulassen**, dann Schritt 3 wiederholen.

**2. Über anderen Apps anzeigen erlauben** (Pflicht für den runden Knopf)

1. *Einstellungen → Apps → DoppelCheck* öffnen.
2. *Über anderen Apps einblenden* bzw. *Über anderen Apps anzeigen* antippen
   (Samsung: unter *Apps → ⋮ → Spezieller Zugriff → Über anderen Apps anzeigen*).
3. Schalter für DoppelCheck einschalten.

Danach erscheint der runde Knopf am rechten Rand. Er lässt sich an eine beliebige Stelle
ziehen und in den DoppelCheck-Einstellungen mit „Runden Knopf anzeigen“ ausblenden.
Ab Android 13 zusätzlich beim ersten App-Start **Benachrichtigungen zulassen**.

**3. Als Assistent festlegen** (freiwillig – für die Geste)

1. *Einstellungen → Apps → Standard-Apps* öffnen
   (Samsung: *Apps → Standard-Apps auswählen*).
2. *Digitaler Assistent* bzw. *Assistent & Spracheingabe* antippen
   (Samsung: *Digitale Assistenz-App*).
3. *Digitale Assistent-App* → **DoppelCheck** auswählen und bestätigen.
4. Auslösen: bei drei Navigationsknöpfen **Startknopf lange drücken**, bei Gestensteuerung
   **von einer unteren Bildschirmecke schräg nach oben wischen**.

Wichtig: Es gibt nur **einen** Assistenten. Wer DoppelCheck wählt, ersetzt damit Google
Assistant/Gemini bzw. Bixby für diese Geste („Hey Google“ funktioniert dann nicht mehr).
Rückgängig: dieselbe Einstellung wieder auf den bisherigen Assistenten stellen. Die Kachel
und der runde Knopf funktionieren auch ganz ohne diesen Schritt.

Technisch meldet sich DoppelCheck **nur** über eine unsichtbare Activity mit dem
Intent-Filter `android.intent.action.ASSIST` an (`assist/AssistActivity.kt`), bewusst
**ohne** `VoiceInteractionService`: Ein solcher Dienst muss einen Spracherkenner mitbringen,
und Android macht den Spracherkenner des Assistenten zum Systemstandard – die Spracheingabe
anderer Apps ginge dann kaputt. Laut Android-Quelltext (`AssistantRoleBehavior`) reicht die
exportierte ASSIST-Activity, um in der Auswahl zu erscheinen. Die Activity liest selbst
nichts; sie ruft dieselbe Prüfung der Bedienungshilfe auf wie der Knopf und schließt sich
sofort. Ist die Bedienungshilfe aus, erscheint ein Hinweis und die Bedienungshilfen-Seite
öffnet sich.

### Ablauf einer Prüfung

1. Auslöser (runder Knopf, Kachel oder Assistenten-Geste) → der Dienst liest den Text der Vordergrund-App.
   Die eigenen Fenster von DoppelCheck werden dabei übersprungen.
2. **Bedienelemente herausfiltern** (`scan/ChromeFilter.kt`, abschaltbar in den Einstellungen):
   weg fallen Button/ImageButton/ImageView/EditText, antippbare Elemente mit Beschreibungstext
   (Bedienhinweise), IDs mit Endung `_btn`, `_button`, `toolbar`, `_icon`, `photo`, `divider`,
   `date`, `entry`, `overflow` sowie eine Liste bekannter WhatsApp-Kopf-/Eingabe-IDs. Die Regeln
   stammen aus echten WhatsApp-Mitschnitten; die Nachricht selbst steht dort in `top_message`,
   `bottom_message`, `message_text` bzw. `conversation_row_text`.
3. **Ist das überhaupt eine Nachricht?** (`scan/MessageGate.kt`) Nur wenn mindestens ein
   Textblock ≥ 25 Zeichen aus einem nicht antippbaren Element kommt, das kein
   Button/ImageButton/ImageView/EditText ist – oder ein Link oder eine Telefonnummer
   vorkommt. Sonst (z. B. Startbildschirm) **keine Anfrage an den Server** und statt einer
   Ampel die graue Anzeige „Keine Nachricht erkannt. Öffnen Sie eine Nachricht und tippen
   Sie erneut.“ Keine Serveradresse → verständliche Meldung.
4. **Sprache** (`scan/ScriptCheck.kt`): Sind mehr als 20 % der Buchstaben Hangul, chinesische/
   japanische Schriftzeichen oder Kyrillisch, wird ebenfalls **nicht** gesendet – grau:
   „Diese Sprache unterstützt DoppelCheck noch nicht (nur Deutsch und Englisch).“ Der Klassifikator
   kennt nur Deutsch und Englisch. Geprüft wird nach Schritt 3, damit ein koreanischer
   Startbildschirm „Keine Nachricht erkannt“ meldet.
5. Sonst `POST /scan-text` über den vorhandenen `ApiClient`. Währenddessen deckt eine
   Vollbild-Anzeige „Prüfe …“ den Bildschirm ab (schließbar – das Ergebnis kommt dann nur
   als Benachrichtigung).
6. Ergebnis **zweifach**:
   - **Vollbild-Ampel** über der aktuellen App: Hintergrund in Ampelfarbe, darauf groß
     **SICHER** (grün), **VORSICHT** (gelb) oder **GEFAHR** (rot) und darunter `reason_de`
     in 30 sp. Nichts auf dieser Anzeige ist kleiner als 24 sp. „Schließen“ oder die
     Zurück-Taste blenden sie aus, „Details in der App“ öffnet das Ergebnis mit Linkliste.
   - **Benachrichtigung** mit demselben Wort und Satz; Antippen öffnet die Details in der App.
     Ab Android 13 fragt die App beim ersten Start nach der Erlaubnis dafür.

Ohne die Erlaubnis „Über anderen Apps anzeigen“ zeigt die Bedienungshilfe die Vollbild-Ampel
trotzdem an (als Bedienungshilfen-Fenster); nur der runde Knopf braucht die Erlaubnis zwingend.

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
    scan/ChromeFilter.kt   entfernt Knöpfe, Uhrzeiten, Kopfzeile, Eingabefeld vor dem Senden
    scan/ScriptCheck.kt    Schriftsystem-Prüfung: Koreanisch/CJK/Kyrillisch wird nicht gesendet
    scan/MessageGate.kt    „Ist das eine Nachricht?“ – Sperre vor jeder Anfrage
    scan/ScanDebugLog.kt   nur Debug-Build: jeder gelesene Knoten nach Logcat (Tag DoppelCheckScan)
    scan/BubbleOverlay.kt  runder, verschiebbarer Knopf (SYSTEM_ALERT_WINDOW)
    scan/SystemSettings.kt öffnet die nötigen Systemeinstellungen, prüft die Assistenten-Rolle
    scan/ScreenScanTrigger.kt  Auslöser von außerhalb der Bedienungshilfe (Assistenten-Geste)
    assist/AssistActivity.kt  unsichtbare ACTION_ASSIST-Activity → dieselbe Bildschirmprüfung
    scan/ResultOverlay.kt  Vollbild-Fenster über der aktuellen App mit der Ampel
    scan/VerdictNotifier.kt  Ergebnis als Benachrichtigung
    ui/VerdictPanel.kt     große Ampel: SICHER / VORSICHT / GEFAHR + reason_de
    api/ErrorText.kt       Fehlertexte, gemeinsam für App und Bedienungshilfe
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

`verdict` ist `red`, `yellow` oder `green` und färbt die Box. Jeder andere Wert (geplant:
`unknown`, siehe unten) erscheint grau als „Nicht geprüft“ – nie als grün. `reason_de` ist der Satz in
großer Schrift. Bei `POST /scan` kommt zusätzlich `text` zurück – der per Texterkennung
gelesene Bildschirmtext, den die App unter dem Ergebnis anzeigt.

## Noch nötig auf dem Server (nicht Teil dieses Unterprojekts)

Die App prüft vor dem Senden, ob überhaupt eine Nachricht auf dem Bildschirm ist. Damit Web-Demo
und API sich genauso verhalten, braucht `api/main.py` **dieselbe Sperre** vor dem Klassifikator –
**noch nicht umgesetzt**, wird in der Python-Sitzung erledigt:

- Bestanden, wenn mindestens eins gilt: eine Zeile (Trennung an `\n`) mit ≥ 25 Zeichen,
  ein Link (`url_check.extract_urls` findet etwas) oder eine Telefonnummer
  (Muster wie in der App: beginnt mit `+` oder `0`, dann 7–15 Ziffern, einzelne Leerzeichen,
  `/` oder `-` dazwischen erlaubt).
- Nicht bestanden → Klassifikator **nicht** aufrufen, Antwort
  `{"verdict": "unknown", "score": null, "reason_de": "Kein Nachrichtentext erkannt.", "urls": [], "model": "<name>"}`.
- Der Server sieht nur den zusammengefügten Text, nicht welches Element antippbar oder ein
  Knopf war; die App-Regel ist daher etwas strenger. Die App zeigt `unknown` bereits grau an.

## Bekannte Einschränkungen

- **Hier nicht kompilierbar.** Die Entwicklungsumgebung dieses Repos hat kein Android SDK,
  der Code wird also geschrieben und geprüft, aber nicht gebaut. Der erste Build auf einem
  echten Rechner (2026-09-12) scheiterte an vier Kotlin-Fehlern in `ScanViewModel.kt`
  wegen der zu alten OkHttp-Version; behoben durch den Pin oben. Weitere Anpassungen beim
  nächsten Build sind möglich.
- **„Bildschirm prüfen“ ist gebaut, aber noch nicht auf einem Gerät getestet.**
  `./gradlew :app:assembleDebug` läuft fehlerfrei (2026-09-14), ein Handy oder Emulator stand
  dabei nicht zur Verfügung. Zu prüfen: Wartezeiten nach dem Schließen der Schnelleinstellungen
  (600 ms) und nach der Assistenten-Geste (400 ms), die Auswahl des richtigen Fensters bei
  geteiltem Bildschirm und die Menünamen bei Samsung.
- Gelesen wird nur, was die App als Text an Android meldet. Bilder, Text in Grafiken und
  Apps, die ihre Oberfläche selbst zeichnen (manche Spiele, einige Banking-Apps mit
  Bildschirmschutz), liefern wenig oder nichts – dann bleibt der Weg über „Screenshot teilen“.
- Beim Teilen mehrerer Bilder auf einmal (`ACTION_SEND_MULTIPLE`) passiert nichts; die App
  verarbeitet bewusst nur ein einzelnes Bild.
- Die App speichert nichts: keine Nachrichten, keine Bilder, keine Verläufe. Gesendet wird
  nur an die selbst eingetragene Serveradresse.
- Links werden nie geöffnet – weder von der App noch vom Server.
