# Fehleranalyse (deutscher Testteil)

Alle Zahlen stammen aus ausgeführten Läufen (`results/metrics.json`, Modelle in `models/`). Grundlage: **104 deutsche Testzeilen** (86 Phishing, 18 legitim). Erzeugt von `src/error_analysis.py`.

## Fehler pro Modell

| Modell | Fehlalarme (legit → Phishing) | Übersehen (Phishing → legit) | FPR | Recall |
|---|---|---|---|---|
| baseline_tfidf_logreg | 5 / 18 | 3 / 86 | 0.2778 | 0.9651 |
| baseline_tfidf_logreg_nourl | 9 / 18 | 0 / 86 | 0.5 | 1.0 |
| distilbert_multilingual | 2 / 18 | 9 / 86 | 0.1111 | 0.8953 |

Die Fehler überschneiden sich kaum: Baseline und DistilBERT liegen bei **4 von 15** Zeilen gemeinsam falsch. Beide Modelle irren also an verschiedenen Stellen.

## Die 15 falsch eingeordneten Zeilen

`p` = Wahrscheinlichkeit für Phishing. „–“ bei DistilBERT heißt: Zeile war dort korrekt (gespeichert sind nur die Fehler des Colab-Laufs).

**PHISHING** · p_baseline 0.77 · p_nourl 0.82 · p_distilbert 0.03  
> Sehr geehrter Kunde, Ihre VR-SecureGo App endet am 29.05.2026. Besuchen Sie: <URL> zur Reaktivierung. Herzliche Grüße Ihre Volksbank  
Klassisches Banking-Phishing, das DistilBERT für harmlos hält (p=0.03) – liest sich wie echte Bankpost.

**PHISHING** · p_baseline 0.63 · p_nourl 0.85 · p_distilbert 0.04  
> Am 08.02. um 20:10 Uhr wurde eine Voicemail-Nachricht fur Sie hinterlassen. Bitte besuchen Sie  
Voicemail-Masche mit Datum und Uhrzeit; genau die Merkmale, die sonst legitime Termin-SMS auszeichnen.

**legitim** · p_baseline 0.60 · p_nourl 0.51 · p_distilbert –  
> Begrenztes Angebot gefällig, Nina? Jetzt zuschlagen! Spare mit Sportwelt Aktiv auf <URL> STOP senden zum Abmelden.  
Werbe-SMS mit Link und Handlungsaufforderung – formal kaum von einer Gewinnspiel-Masche zu unterscheiden.

**PHISHING** · p_baseline 0.46 · p_nourl 0.59 · p_distilbert 0.02  
> Neue Nachricht des Mobilfunkbetreibers  
Fünf Wörter, kein Link, keine Dringlichkeit – zu wenig Text für eine Textklassifikation.

**legitim** · p_baseline 0.28 · p_nourl 0.45 · p_distilbert 0.91  
> Hallo Anna Berger, wir möchten dich an deinen Termin morgen, 11.09.2026, um 15.30 Uhr erinnern. Solltest du den Termin absagen oder verschieben wollen, dann er…  
DistilBERT-Fehlalarm auf einer echten Terminerinnerung (p=0.91); Telefonnummer und Datum wirken offiziell.

**legitim** · p_baseline 0.78 · p_nourl 0.88 · p_distilbert –  
> Hallo Frau Schneider! Antworten Sie mit „Ja", um zu bestätigen, dass Sie spezielle Angebote von Sportpark Mitte erhalten wollen. STOP senden zum Abmelden.  
Opt-in-Bestätigung. „Antworten Sie mit Ja“ ist eine Handlungsaufforderung wie im Phishing – hier aber legitim.

**PHISHING** · p_baseline 0.33 · p_nourl 0.62 · p_distilbert 0.13  
> Verpasster Anruf. Die aufgezeichnete Nachricht ist verfuegbar unter  
Von BEIDEN Modellen übersehen: Voicemail-Masche, sehr kurz, Link im Original als *Link* maskiert – kein Signal übrig.

**PHISHING** · p_baseline 0.86 · p_nourl 0.81 · p_distilbert 0.20  
> Deutsche Bank: Der Zugang zu Ihrer photoTAN-App läuft am 29. April aus. Jetzt Aktualisieren: <URL>  
Ablauf-Masche („läuft aus, jetzt aktualisieren“) – von DistilBERT übersehen, obwohl Marke + Link vorhanden.

**PHISHING** · p_baseline 0.48 · p_nourl 0.55 · p_distilbert 0.01  
> Ankunft heute: Ihr Amazon-Paket. & Weitere + Infos unter <URL>  
Paket-Phishing, das wie eine echte Amazon-Benachrichtigung formuliert ist; p=0.01.

**legitim** · p_baseline 0.68 · p_nourl 0.80 · p_distilbert –  
> Waren Sie zufrieden mit uns, Frau Meyer? Wir freuen uns über Ihre Meinung! Geben Sie uns auf <URL> Feedback. Ihre Meinung zählt!  
Feedback-Anfrage mit Link. Höfliche Sie-Anrede plus <URL> ist genau die gelernte Phishing-Signatur.

**PHISHING** · p_baseline 0.60 · p_nourl 0.76 · p_distilbert 0.01  
> Anruf von 017... Sprachnachricht 48s von 017... Nachricht verfügbar auf: KLICKEN SIE HIER  
„KLICKEN SIE HIER“ statt echtem Link – die URL-Schicht hat nichts zu prüfen, der Text ist zu generisch.

**PHISHING** · p_baseline 0.58 · p_nourl 0.58 · p_distilbert 0.46  
> Neue Voicemail: https://[Link]  
Der Link ist im Quelltext unbrauchbar notiert; p=0.46 liegt knapp unter der Schwelle.

**legitim** · p_baseline 0.72 · p_nourl 0.78 · p_distilbert 0.96  
> Aufregende Neuigkeiten, Jonas! Deine Bestellung von Skateshop Rollbrett ist auf dem Weg. Verfolge ihre Reise hier: <URL>  
Der einzige Fehlalarm, den BEIDE Modelle machen: Paketankündigung mit Link, du-Anrede, Ausrufezeichen.

**PHISHING** · p_baseline 0.76 · p_nourl 0.85 · p_distilbert 0.42  
> Sie . - haben zwei neue . Sprachnachrichten erhalten  
Absichtlich mit Punkten zerstückelt, um Filter zu umgehen – bei p=0.42 funktioniert das gegen DistilBERT.

**legitim** · p_baseline 0.53 · p_nourl 0.67 · p_distilbert –  
> Bald ist Valentinstag, Frau Schulz! Erhalten Sie 15% Rabatt auf Ihre Bestellung bei Blumen Rosenhof mit Code LIEBE15 auf <URL>. STOP senden zum Abmelden.  
Rabattaktion. „Erhalten Sie 15% Rabatt“ liegt lexikalisch nah an Gewinnspiel-Phishing.

## (a) „Sie/Ihre“ = Phishing – der eingebaute Höflichkeits-Bias

Die Baseline hat gelernt, dass förmliches Deutsch verdächtig ist. Das lässt sich direkt an den Gewichten der logistischen Regression ablesen (positiv = Phishing):

| Merkmal | Gewicht |
|---|---|
| `sie` | +2.179 |
| `ihre` | +0.938 |
| `ihr` | +0.336 |
| `konto` | +0.882 |
| `url` | +1.722 |
| `uhr` | -1.433 |
| `termin` | -0.700 |
| `call` | +2.570 |
| `txt` | +2.142 |
| `free` | +1.950 |

`sie` (+2.179) wiegt fast so schwer wie `call` (+2.570) – das englische Spam-Wort schlechthin. `ihre` (+0.938) kommt dazu, während typische Alltagswörter wie `uhr` (-1.433) dagegenhalten. In den Testdaten zeigt sich der Effekt unmittelbar: von den 10 legitimen deutschen Nachrichten mit Sie-Anrede werden 3 als Phishing markiert, von den 8 ohne Sie-Anrede nur 2. Die mittlere Phishing-Wahrscheinlichkeit liegt bei 0.42 gegenüber 0.33. Die Ursache ist die Datenlage, nicht das Modell: unsere echten deutschen Phishing-Texte sind fast alle förmlich, unsere echten Legit-Texte überwiegend Werbe- und Terminvorlagen. Wer höflich schreibt, wirkt für dieses Modell verdächtig – für eine App für ältere Menschen, die genau solche Post bekommen, ist das der schlechteste denkbare Bias.

## (b) Baseline gegen DistilBERT – ein echter Zielkonflikt

Auf demselben Testteil: die Baseline erkennt fast jedes Phishing (Recall 0.9651, nur 3 übersehen), schlägt aber bei 5 von 18 legitimen Nachrichten falsch Alarm (FPR 0.2778). DistilBERT dreht das um: nur noch 2 Fehlalarme (FPR 0.1111), dafür 9 übersehene Phishing-Nachrichten (Recall 0.8953). Für unser Produkt zählt die Fehlalarmrate mehr – eine App, die bei fast jeder zweiten echten Paketbenachrichtigung warnt, wird nach einer Woche ignoriert, und dann schützt sie gar nicht mehr. Trotzdem sind die übersehenen Fälle keine Kleinigkeit: darunter sind Banking-Maschen wie die VR-SecureGo- und die photoTAN-Nachricht, die DistilBERT mit p unter 0.20 durchwinkt. Weil sich die Fehler beider Modelle kaum überschneiden (4 gemeinsame Fehler), wäre eine Kombination der beiden naheliegend. Getestet haben wir bisher nur ein ODER der zwei Baseline-Varianten (`ensemble_or_tuned` in `experiments.csv`); da beide dieselbe Merkmalsfamilie nutzen, hat das nur Fehlalarme addiert. **Baseline + DistilBERT ist noch offen** – dafür brauchen wir die Wahrscheinlichkeiten von DistilBERT für alle Testzeilen (`results/distilbert_test_probs.csv`).

## (c) Der Schwellenwert aus den englischen Validierungsdaten überträgt sich nicht

Wir haben den Entscheidungs-Schwellenwert auf der Validierungsmenge gesucht (Kriterium: maximaler Recall bei FPR ≤ 0.02) und **0.22** erhalten statt der üblichen 0.50. Auf dem deutschen Testteil wurde damit alles schlechter: die Fehlalarmrate stieg von 0.2778 auf **0.7778** (14 von 18 legitimen Nachrichten). Der Grund steht in `data_summary.md`: **die Validierungsmenge enthält ausschließlich englische Zeilen.** Ein Schwellenwert, der auf englischen SMS sicher ist, ist für förmliches Deutsch viel zu niedrig, weil die deutschen Legit-Texte ohnehin hohe Werte bekommen (siehe (a)). Die Lehre daraus ist methodisch: **man darf einen Schwellenwert nur auf Daten tunen, die zur Zielsprache passen.** Solange keine deutschen Zeilen in der Validierungsmenge sind, bleibt 0.50 die ehrlichere Wahl.

## (d) Der `*Link*`-Platzhalter und der Auswertungsfehler, den er verursacht hat

Die Warnmeldungen der Verbraucherzentrale zeigen die betrügerischen Links nicht im Klartext, sondern schreiben `*Link*`. **33 unserer 104 deutschen Testzeilen** (alle davon Phishing) haben deshalb gar keinen echten Link. Das hat zwei Folgen. Erstens kann die URL-Prüfung – unsere zweite, vom Modell unabhängige Sicherheitsebene – bei diesen Nachrichten grundsätzlich nichts finden; die Bewertung hängt allein am Text. Zweitens hat der Platzhalter einen echten Fehler in unserer Auswertung verursacht: `data_prep.py` ersetzt beim Training sowohl echte Links als auch `*Link*` durch das Token `<URL>`, `eval_pipeline.py` reichte aber die Originaltexte mit `*Link*` an den Klassifikator weiter. Das Modell sah also ein Zeichenmuster, das es nie gelernt hatte, und die Produkt-Auswertung fiel zu schlecht aus. Der Unterschied ist messbar: als Rot erkanntes Phishing **0.663 vor der Korrektur gegenüber 0.698 danach** (57 statt 60 von 86 Nachrichten). Die legitime Seite blieb unverändert (Fehlalarmrate 0.333). Aufgefallen ist der Fehler nur, weil wir den Weg über gespeicherte Wahrscheinlichkeiten (`--probs`) gegen den Weg über das geladene Modell geprüft haben und beide Wege verschiedene Tabellen ergaben. Für den echten Einsatz spielt der Platzhalter keine Rolle – niemand bekommt eine SMS mit `*Link*` –, aber er verzerrt jede Messung, die wir mit diesen Daten machen.

## Ampel-Tabelle (volle Logik, deutscher Testteil)

| wahres Label | grün | gelb | rot |
|---|---|---|---|
| legitim (n=18) | 12 | 6 | 0 |
| Phishing (n=86) | 3 | 23 | 60 |

Fehlalarmrate (legitim nicht grün) 0.333 · legitim → rot 0.000 · Phishing → rot 0.698. Aktives Modell: `baseline_tfidf_logreg`.
