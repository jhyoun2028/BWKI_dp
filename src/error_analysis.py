"""Generate results/error_analysis.md from the REAL misclassified German test rows.

Sources, all from executed runs:
  - baseline / baseline_nourl : re-scored here from models/*.joblib on data/processed/test.csv
  - distilbert_multilingual   : misclassified rows stored in results/metrics.json by the Colab run
  - headline metrics          : results/metrics.json
  - product-level verdicts    : the full pipeline via src/eval_pipeline.py

    python src/error_analysis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_pipeline  # noqa: E402
import pipeline  # noqa: E402
from data_prep import LINK_PLACEHOLDER  # noqa: E402
from train_baseline import METRICS_PATH, PROCESSED, RESULTS, log, strip_url_token  # noqa: E402
from url_check import URL_MASK  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = RESULTS / "error_analysis.md"
MODELS = ROOT / "models"

# One comment per misclassified row, keyed by the first 40 characters of the (masked) text.
# The numbers come from the run; only these interpretations are written by the team.
COMMENTS = {
    "Begrenztes Angebot gefällig, Nina? Jetzt":
        "Werbe-SMS mit Link und Handlungsaufforderung – formal kaum von einer Gewinnspiel-Masche zu unterscheiden.",
    "Herr Neumann, Ihre Bestellung von Elektro":
        "Echte Versandbenachrichtigung; „Ihre Bestellung“ + Uhrzeit reicht dem Modell schon für Verdacht.",
    "Hallo Frau Schneider! Antworten Sie mit „":
        "Opt-in-Bestätigung. „Antworten Sie mit Ja“ ist eine Handlungsaufforderung wie im Phishing – hier aber legitim.",
    "Waren Sie zufrieden mit uns, Frau Meyer?":
        "Feedback-Anfrage mit Link. Höfliche Sie-Anrede plus <URL> ist genau die gelernte Phishing-Signatur.",
    "Danke für Ihre Bestellung bei Weinhandel":
        "Bestellbestätigung. Knapp über der Schwelle (0.54) – solche Grenzfälle kippen mit jedem neuen Trainingslauf.",
    "Aufregende Neuigkeiten, Jonas! Deine Best":
        "Der einzige Fehlalarm, den BEIDE Modelle machen: Paketankündigung mit Link, du-Anrede, Ausrufezeichen.",
    "Bald ist Valentinstag, Frau Schulz! Erhal":
        "Rabattaktion. „Erhalten Sie 15% Rabatt“ liegt lexikalisch nah an Gewinnspiel-Phishing.",
    "Verpasster Anruf. Die aufgezeichnete Nach":
        "Von BEIDEN Modellen übersehen: Voicemail-Masche, sehr kurz, Link im Original als *Link* maskiert – kein Signal übrig.",
    "Sehr geehrter Kunde, Ihre VR-SecureGo App":
        "Klassisches Banking-Phishing, das DistilBERT für harmlos hält (p=0.03) – liest sich wie echte Bankpost.",
    "Am 08.02. um 20:10 Uhr wurde eine Voicema":
        "Voicemail-Masche mit Datum und Uhrzeit; genau die Merkmale, die sonst legitime Termin-SMS auszeichnen.",
    "Neue Nachricht des Mobilfunkbetreibers":
        "Fünf Wörter, kein Link, keine Dringlichkeit – zu wenig Text für eine Textklassifikation.",
    "Hallo Anna Berger, wir möchten dich an de":
        "DistilBERT-Fehlalarm auf einer echten Terminerinnerung (p=0.91); Telefonnummer und Datum wirken offiziell.",
    "Deutsche Bank: Der Zugang zu Ihrer photoT":
        "Ablauf-Masche („läuft aus, jetzt aktualisieren“) – von DistilBERT übersehen, obwohl Marke + Link vorhanden.",
    "Ankunft heute: Ihr Amazon-Paket. & Weiter":
        "Paket-Phishing, das wie eine echte Amazon-Benachrichtigung formuliert ist; p=0.01.",
    "Anruf von 017... Sprachnachricht 48s von ":
        "„KLICKEN SIE HIER“ statt echtem Link – die URL-Schicht hat nichts zu prüfen, der Text ist zu generisch.",
    "Neue Voicemail: https://[Link]":
        "Der Link ist im Quelltext unbrauchbar notiert; p=0.46 liegt knapp unter der Schwelle.",
    "Sie . - haben zwei neue . Sprachnachricht":
        "Absichtlich mit Punkten zerstückelt, um Filter zu umgehen – bei p=0.42 funktioniert das gegen DistilBERT.",
}
MISSING = "(kein Kommentar hinterlegt)"
PROBE_WORDS = ["sie", "ihre", "ihr", "konto", "url", "uhr", "termin", "call", "txt", "free"]


def key(text: str) -> str:
    """Stable lookup key: first 40 characters, whitespace normalised."""
    return " ".join(str(text).split())[:40]


COMMENTS_BY_KEY = {key(k): v for k, v in COMMENTS.items()}


def short(text: str, n: int = 90) -> str:
    t = " ".join(str(text).split())
    return (t[: n - 1] + "…") if len(t) > n else t


def score(path: Path, texts: pd.Series, strip: bool) -> pd.Series | None:
    if not path.exists():
        log(f"[warn] {path.relative_to(ROOT)} fehlt – Modell wird übersprungen")
        return None
    pipe = joblib.load(path)
    return pd.Series(pipe.predict_proba(strip_url_token(texts) if strip else texts)[:, 1], index=texts.index)


def traffic_light(de: pd.DataFrame, normalise_placeholder: bool) -> dict:
    """German traffic-light counts with the shipped config; optionally without the *Link* fix."""
    rows = de.copy()
    if not normalise_placeholder:                      # reproduce the pre-fix behaviour
        rows["text_raw"] = rows["text_raw_original"]
    res = eval_pipeline.run(rows, cap=True)
    legit, phish = res[res.label == 0], res[res.label == 1]
    return {"legit": legit.verdict.value_counts().reindex(["green", "yellow", "red"], fill_value=0).to_dict(),
            "phish": phish.verdict.value_counts().reindex(["green", "yellow", "red"], fill_value=0).to_dict(),
            "false_alarm": float((legit.verdict != "green").mean()),
            "legit_red": float((legit.verdict == "red").mean()),
            "phish_red": float((phish.verdict == "red").mean())}


def main() -> None:
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    test = pd.read_csv(PROCESSED / "test.csv")
    de = test[test.lang == "de"].copy()
    if de.empty:
        raise SystemExit("Keine deutschen Testzeilen – error_analysis.md nicht erzeugt")

    de["p_baseline"] = score(MODELS / "baseline.joblib", de.text, strip=False)
    de["p_nourl"] = score(MODELS / "baseline_nourl.joblib", de.text, strip=True)
    db_rows = metrics.get("distilbert_multilingual", {}).get("misclassified_test", [])
    db_map = {r["text"]: r["p_phishing"] for r in db_rows if r["lang"] == "de"}
    de["p_distilbert"] = de.text.map(db_map)          # only misclassified rows are stored

    wrong_base = de[(de.p_baseline >= 0.5) != (de.label == 1)] if de.p_baseline.notna().all() else de.iloc[:0]
    wrong_db = de[de.p_distilbert.notna()]
    union = de.loc[sorted(set(wrong_base.index) | set(wrong_db.index))]
    both = sorted(set(wrong_base.index) & set(wrong_db.index))

    # original (unnormalised) texts for the *Link* section and the product-level tables
    lookup = eval_pipeline.masked_to_raw()
    de["text_raw_original"] = de.text.map(lookup).fillna(de.text)
    de["text_raw"] = de.text_raw_original.map(lambda t: LINK_PLACEHOLDER.sub(URL_MASK, t))
    n_placeholder = int(de.text_raw_original.str.contains(r"\*Link\*", case=False).sum())
    n_ph_phish = int(de[(de.label == 1)].text_raw_original.str.contains(r"\*Link\*", case=False).sum())
    with_fix = traffic_light(de, True)
    without_fix = traffic_light(de, False)

    # feature weights as evidence for the formal-address bias
    pipe = joblib.load(MODELS / "baseline.joblib")
    names = pipe.named_steps["features"].get_feature_names_out()
    coef = pipe.named_steps["clf"].coef_[0]
    widx = {n: i for i, n in enumerate(names)}
    weights = {w: float(coef[widx[f"word__{w}"]]) for w in PROBE_WORDS if f"word__{w}" in widx}

    legit = de[de.label == 0]
    formal = legit.text.str.contains(r"\b(?:Sie|Ihre|Ihrer|Ihren|Ihnen)\b")
    b, d = metrics["baseline_tfidf_logreg"]["test_de"], metrics["distilbert_multilingual"]["test_de"]
    thr_key = "baseline_tfidf_logreg_thr0.22"
    thr = metrics.get(thr_key, {})

    L = []
    L.append("# Fehleranalyse (deutscher Testteil)\n")
    L.append(f"Alle Zahlen stammen aus ausgeführten Läufen (`results/metrics.json`, Modelle in `models/`). "
             f"Grundlage: **{len(de)} deutsche Testzeilen** ({int(de.label.sum())} Phishing, {int((de.label == 0).sum())} legitim). "
             "Erzeugt von `src/error_analysis.py`.\n")

    L.append("## Fehler pro Modell\n")
    L.append("| Modell | Fehlalarme (legit → Phishing) | Übersehen (Phishing → legit) | FPR | Recall |")
    L.append("|---|---|---|---|---|")
    L.append(f"| baseline_tfidf_logreg | {b['fp']} / {b['fp'] + b['tn']} | {b['fn']} / {b['fn'] + b['tp']} | {b['fpr']} | {b['recall']} |")
    nu = metrics["baseline_tfidf_logreg_nourl"]["test_de"]
    L.append(f"| baseline_tfidf_logreg_nourl | {nu['fp']} / {nu['fp'] + nu['tn']} | {nu['fn']} / {nu['fn'] + nu['tp']} | {nu['fpr']} | {nu['recall']} |")
    L.append(f"| distilbert_multilingual | {d['fp']} / {d['fp'] + d['tn']} | {d['fn']} / {d['fn'] + d['tp']} | {d['fpr']} | {d['recall']} |")
    L.append(f"\nDie Fehler überschneiden sich kaum: Baseline und DistilBERT liegen bei **{len(both)} von "
             f"{len(union)}** Zeilen gemeinsam falsch. Beide Modelle irren also an verschiedenen Stellen.\n")

    L.append(f"## Die {len(union)} falsch eingeordneten Zeilen\n")
    L.append("`p` = Wahrscheinlichkeit für Phishing. „–“ bei DistilBERT heißt: Zeile war dort korrekt "
             "(gespeichert sind nur die Fehler des Colab-Laufs).\n")
    for i, r in union.iterrows():
        truth = "PHISHING" if r.label == 1 else "legitim"
        pdb = f"{r.p_distilbert:.2f}" if pd.notna(r.p_distilbert) else "–"
        L.append(f"**{truth}** · p_baseline {r.p_baseline:.2f} · p_nourl {r.p_nourl:.2f} · p_distilbert {pdb}  ")
        L.append(f"> {short(r.text, 160)}  ")
        L.append(f"{COMMENTS_BY_KEY.get(key(r.text), MISSING)}\n")

    L.append("## (a) „Sie/Ihre“ = Phishing – der eingebaute Höflichkeits-Bias\n")
    L.append("Die Baseline hat gelernt, dass förmliches Deutsch verdächtig ist. Das lässt sich direkt an den "
             "Gewichten der logistischen Regression ablesen (positiv = Phishing):\n")
    L.append("| Merkmal | Gewicht |")
    L.append("|---|---|")
    for w in PROBE_WORDS:
        if w in weights:
            L.append(f"| `{w}` | {weights[w]:+.3f} |")
    L.append(f"\n`sie` ({weights.get('sie', 0):+.3f}) wiegt fast so schwer wie `call` ({weights.get('call', 0):+.3f}) – "
             f"das englische Spam-Wort schlechthin. `ihre` ({weights.get('ihre', 0):+.3f}) kommt dazu, während typische "
             f"Alltagswörter wie `uhr` ({weights.get('uhr', 0):+.3f}) dagegenhalten. In den Testdaten zeigt sich der Effekt "
             f"unmittelbar: von den {int(formal.sum())} legitimen deutschen Nachrichten mit Sie-Anrede werden "
             f"{int(((legit.p_baseline >= 0.5) & formal).sum())} als Phishing markiert, von den {int((~formal).sum())} ohne Sie-Anrede nur "
             f"{int(((legit.p_baseline >= 0.5) & ~formal).sum())}. Die mittlere Phishing-Wahrscheinlichkeit liegt bei "
             f"{legit.p_baseline[formal].mean():.2f} gegenüber {legit.p_baseline[~formal].mean():.2f}. "
             "Die Ursache ist die Datenlage, nicht das Modell: unsere echten deutschen Phishing-Texte sind fast alle "
             "förmlich, unsere echten Legit-Texte überwiegend Werbe- und Terminvorlagen. Wer höflich schreibt, wirkt "
             "für dieses Modell verdächtig – für eine App für ältere Menschen, die genau solche Post bekommen, ist das "
             "der schlechteste denkbare Bias.\n")

    L.append("## (b) Baseline gegen DistilBERT – ein echter Zielkonflikt\n")
    L.append(f"Auf demselben Testteil: die Baseline erkennt fast jedes Phishing (Recall {b['recall']}, nur {b['fn']} übersehen), "
             f"schlägt aber bei {b['fp']} von {b['fp'] + b['tn']} legitimen Nachrichten falsch Alarm (FPR {b['fpr']}). "
             f"DistilBERT dreht das um: nur noch {d['fp']} Fehlalarme (FPR {d['fpr']}), dafür {d['fn']} übersehene "
             f"Phishing-Nachrichten (Recall {d['recall']}). Für unser Produkt zählt die Fehlalarmrate mehr – eine App, "
             "die bei fast jeder zweiten echten Paketbenachrichtigung warnt, wird nach einer Woche ignoriert, und dann "
             "schützt sie gar nicht mehr. Trotzdem sind die übersehenen Fälle keine Kleinigkeit: darunter sind "
             "Banking-Maschen wie die VR-SecureGo- und die photoTAN-Nachricht, die DistilBERT mit p unter 0.20 "
             f"durchwinkt. Weil sich die Fehler beider Modelle kaum überschneiden ({len(both)} gemeinsame Fehler), "
             "wäre eine Kombination der beiden naheliegend. Getestet haben wir bisher nur ein ODER der zwei "
             "Baseline-Varianten (`ensemble_or_tuned` in `experiments.csv`); da beide dieselbe Merkmalsfamilie nutzen, "
             "hat das nur Fehlalarme addiert. **Baseline + DistilBERT ist noch offen** – dafür brauchen wir die "
             "Wahrscheinlichkeiten von DistilBERT für alle Testzeilen (`results/distilbert_test_probs.csv`).\n")

    L.append("## (c) Der Schwellenwert aus den englischen Validierungsdaten überträgt sich nicht\n")
    if thr:
        t_de, t_par = thr["test_de"], thr["params"]
        L.append(f"Wir haben den Entscheidungs-Schwellenwert auf der Validierungsmenge gesucht (Kriterium: maximaler Recall "
                 f"bei FPR ≤ 0.02) und **{t_par['threshold']}** erhalten statt der üblichen 0.50. Auf dem deutschen Testteil "
                 f"wurde damit alles schlechter: die Fehlalarmrate stieg von {b['fpr']} auf **{t_de['fpr']}** "
                 f"({t_de['fp']} von {t_de['fp'] + t_de['tn']} legitimen Nachrichten). Der Grund steht in "
                 "`data_summary.md`: **die Validierungsmenge enthält ausschließlich englische Zeilen.** Ein Schwellenwert, "
                 "der auf englischen SMS sicher ist, ist für förmliches Deutsch viel zu niedrig, weil die deutschen "
                 "Legit-Texte ohnehin hohe Werte bekommen (siehe (a)). Die Lehre daraus ist methodisch: **man darf einen "
                 "Schwellenwert nur auf Daten tunen, die zur Zielsprache passen.** Solange keine deutschen Zeilen in der "
                 "Validierungsmenge sind, bleibt 0.50 die ehrlichere Wahl.\n")
    else:
        L.append("(Kein Eintrag mit getuntem Schwellenwert in metrics.json gefunden.)\n")

    L.append("## (d) Der `*Link*`-Platzhalter und der Auswertungsfehler, den er verursacht hat\n")
    ph_note = ("alle davon Phishing" if n_placeholder == n_ph_phish else f"{n_ph_phish} davon Phishing")
    L.append(f"Die Warnmeldungen der Verbraucherzentrale zeigen die betrügerischen Links nicht im Klartext, sondern "
             f"schreiben `*Link*`. **{n_placeholder} unserer {len(de)} deutschen Testzeilen** ({ph_note}) "
             "haben deshalb gar keinen echten Link. Das hat zwei Folgen. Erstens kann die URL-Prüfung – unsere zweite, "
             "vom Modell unabhängige Sicherheitsebene – bei diesen Nachrichten grundsätzlich nichts finden; die "
             "Bewertung hängt allein am Text. Zweitens hat der Platzhalter einen echten Fehler in unserer Auswertung "
             "verursacht: `data_prep.py` ersetzt beim Training sowohl echte Links als auch `*Link*` durch das Token "
             f"`{URL_MASK}`, `eval_pipeline.py` reichte aber die Originaltexte mit `*Link*` an den Klassifikator weiter. "
             "Das Modell sah also ein Zeichenmuster, das es nie gelernt hatte, und die Produkt-Auswertung fiel zu "
             "schlecht aus. Der Unterschied ist messbar: als Rot erkanntes Phishing "
             f"**{without_fix['phish_red']:.3f} vor der Korrektur gegenüber {with_fix['phish_red']:.3f} danach** "
             f"({without_fix['phish']['red']} statt {with_fix['phish']['red']} von {int(de.label.sum())} Nachrichten). "
             f"Die legitime Seite blieb unverändert (Fehlalarmrate {with_fix['false_alarm']:.3f}). Aufgefallen ist der "
             "Fehler nur, weil wir den Weg über gespeicherte Wahrscheinlichkeiten (`--probs`) gegen den Weg über das "
             "geladene Modell geprüft haben und beide Wege verschiedene Tabellen ergaben. Für den echten Einsatz spielt "
             "der Platzhalter keine Rolle – niemand bekommt eine SMS mit `*Link*` –, aber er verzerrt jede Messung, die "
             "wir mit diesen Daten machen.\n")

    L.append("## Ampel-Tabelle (volle Logik, deutscher Testteil)\n")
    L.append("| wahres Label | grün | gelb | rot |")
    L.append("|---|---|---|---|")
    L.append(f"| legitim (n={int((de.label == 0).sum())}) | {with_fix['legit']['green']} | {with_fix['legit']['yellow']} | {with_fix['legit']['red']} |")
    L.append(f"| Phishing (n={int(de.label.sum())}) | {with_fix['phish']['green']} | {with_fix['phish']['yellow']} | {with_fix['phish']['red']} |")
    L.append(f"\nFehlalarmrate (legitim nicht grün) {with_fix['false_alarm']:.3f} · legitim → rot {with_fix['legit_red']:.3f} · "
             f"Phishing → rot {with_fix['phish_red']:.3f}. Aktives Modell: `{pipeline.get_classifier().name}`.\n")

    OUT.write_text("\n".join(L), encoding="utf-8")
    n_missing = sum(1 for _, r in union.iterrows() if key(r.text) not in COMMENTS_BY_KEY)
    unused = [k for k in COMMENTS_BY_KEY if k not in {key(r.text) for _, r in union.iterrows()}]
    log(f"[out] {OUT.relative_to(ROOT)} ({len(union)} Beispiele, {len(both)} gemeinsame Fehler)")
    if n_missing:
        log(f"[warn] {n_missing} Zeile(n) ohne Kommentar")
    if unused:
        log(f"[warn] {len(unused)} Kommentar(e) passen zu keiner Zeile: {unused}")


if __name__ == "__main__":
    main()
