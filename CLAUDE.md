# DoppelCheck — CLAUDE.md (project spec for AI-assisted development, v2 — 2026-09-09)

> Read this file completely before doing anything. It is the working agreement for this repo.

## Context

- Two-person student team, German national AI competition (BWKI). **Hard deadline: 20 September 2026. Internal target: everything submitted on 19 September.**
- Required deliverables: runnable code as ZIP with README (≤ 100 MB), REAL evaluation metrics for the documentation form, a 2–4 min demo video.
- Priority order: **working + honestly evaluated core > feature breadth > polish.** Never add features not listed here.
- Product idea: "Betrugsschutz mit einer Geste" — the user double-taps the back of the phone, the current screen is analyzed, and a traffic-light verdict with a plain-German explanation appears within seconds. Target group: older adults in Germany.

## Current status (keep this section updated after every step)

- ✅ **Step 1** — repo layout, venv (pandas numpy scikit-learn matplotlib seaborn requests datasets jupyter joblib), .gitignore, requirements.txt, German README skeleton.
- ✅ **Step 2** — `src/data_prep.py` + `notebooks/01_data.ipynb`. UCI SMS Spam Collection loaded from a byte-identical GitHub mirror (archive.ics.uci.edu is blocked in this sandbox). After cleaning: 5,130 messages, split 4,104 / 513 / 513, spam share 12.3 % per split. German CSVs exist only as templates (rows marked `BEISPIEL` are skipped).
- ✅ **Step 3** — `src/train_baseline.py` + `notebooks/02_baseline.ipynb`. TF-IDF + LogisticRegression (C=3). Test: acc 0.9922, F1 0.9677, FPR 0.0022 (1 false alarm / 450 legit). Train acc 0.9995. Saved: `models/baseline.joblib`, `results/metrics.json` (key `baseline_tfidf_logreg`), `results/experiments.csv`, `results/confusion_matrix_baseline.png`.
- ⚠️ **Key finding:** top spam features are "call", "txt", "uk", "free", UK premium numbers ("08", "087") → the baseline learned 2012 British SMS spam, not German phishing. **Integrating the team's own German dataset is the top data priority.**
- ❌ **Decision:** the second English dataset is DROPPED. Data = UCI + own German data. Mark the unused `SetFit/enron_spam` loader as "nicht verwendet" in `data/SOURCES.md`.
- ✅ **Step 4** — `notebooks/03_transformer.ipynb` written and syntax-validated here, **NOT run** (no GPU, Hugging Face blocked). Runs on Colab: clone repo → same splits → DistilBERT 3 epochs / lr 2e-5 / batch 16 / max_len 128 / seed 42, best checkpoint by val F1 → one test evaluation → merges `distilbert_multilingual` into `results/metrics.json`, appends `experiments.csv`, saves `confusion_matrix_distilbert.png`, model to Drive `DoppelCheck/models/distilbert/`, pushes `results/` back (needs Colab secret `GITHUB_TOKEN`). **Colab run done on 2026-09-10, results merged (see below).**
- ✅ **Step 5** — `src/fetch_blocklists.py` (PhishTank, OpenPhish, Tranco → `data/blocklists/`, fails gracefully; blocked here, run on Colab/locally), `src/url_check.py` (extract_urls with hxxp/`[.]`/missing scheme; check_url: blocklist + 25-brand look-alike rules → red, shortener/IP/odd TLD/@/subdomains/punycode → yellow, official domain or Tranco top-10k → green; works without lists), `tests/test_url_check.py`: **39 tests pass** (16 phishing-style, 14 legit, extraction + list fixtures). pytest and tldextract pinned in requirements.txt.
- ❌ **GitHub push still fails (403)** for both git and the GitHub connector – all commits exist only in the sandbox branch `claude/doppelcheck-repo-setup-li83sn`. Grant the Claude GitHub App access to the repo, then push.
- ✅ **Step 6** — `src/ocr.py` (easyocr de+en, CPU, lazy reader; weights DID download here via GitHub releases; 3 OCR repair rules for links: `http:ll`, dropped dot before TLD, `/` read as `l`), `src/pipeline.py` (baseline fallback active, DistilBERT loaded if `models/distilbert/` exists; verdict rules + `reason_de` ≤ 120 chars), `src/make_samples.py` → 3 screenshots in `data/samples/` (1080×1920). `tests/test_pipeline.py`: 13 tests incl. 3 real OCR tests → **52 tests pass** overall. Sample verdicts via OCR: DHL → red, Sparkasse → red, Familie → green.
- ✅ **GitHub push works** since 2026-09-09 (Claude GitHub App installed).
- ✅ **Step 7** — `app/gradio_demo.py` (tabs „Text einfügen“ / „Screenshot hochladen“, big colored verdict box, reason sentence 28 px, URL list with levels, recognized OCR text). Launched on :7860 and both tabs called via gradio_client: DHL text → ROT, family_ok.png → GRÜN, bank_phishing.png → ROT.
- ✅ **Step 8** — `api/main.py` (GET /health, POST /scan-text, POST /scan multipart `file`; 400 for non-images, 503 if OCR missing). Tested with curl: health ok (model baseline, ocr true), Sparkasse text → red (score only 0.14 – the URL rule catches it, the UCI-trained model does not), family text → green, dhl_phishing.png → red with OCR text. `notebooks/04_demo_colab.ipynb` (clone, install, optional Drive model, uvicorn in background, ngrok tunnel via secret `NGROK_AUTHTOKEN`, prints public `/scan` URL; written + syntax-validated, not run here). `shortcut/README.md` with the exact iOS Shortcut steps and the JSON the shortcut receives.
- 🛠️ **Known issue (fixed 2026-09-09, Colab test of notebook 04):** `models/baseline.joblib` was gitignored (`models/*`, `*.joblib`) and therefore missing after `git clone` → API could not start on Colab. Fix: `.gitignore` now has `!models/baseline.joblib` and the file (3.1 MB) is committed; notebook 04 additionally runs `src/train_baseline.py` if the file is missing (appends a row to `experiments.csv`) and supports an optional Colab secret `NGROK_DOMAIN` for a fixed ngrok address.
- ✅ **German data integrated (2026-09-09)** — `data/raw/`: german_phishing.csv 173 real (Verbraucherzentrale), german_legit.csv 36 real (filled-in public templates + real notices), german_synthetic_{phishing,legit}.csv 70 + 70 (LLM-generated, marked in `source_url`). Files are tracked (`!data/raw/german_*.csv`). `data_prep.py`: real DE rows 50/50 train/test stratified by label × category (104/104), synthetic DE rows train only, val = English only; real URLs and the `*Link*` placeholder → same token `<URL>` (`url_check.mask_urls`, also applied in `pipeline.py` at inference). Splits now 4,348 / 513 / 617.
- ✅ **Baseline retrained** (C=1): train acc 0.9945 · test acc 0.9757, F1 0.9511, FPR 0.0256 · **German-only test (n=104): acc 0.8942, F1 0.9399, recall 1.0, FPR 0.6111 (11 of 18 legit flagged)**. Top spam features now `url`, `call`, `sie`, `txt`, `ihre`: the model learned „formal German + link = phishing“ – exactly the trap predicted for a legit set that is too small and template-heavy. Old rows kept in `experiments.csv`. Verdict-rule tests now pin the classifier score (monkeypatch) → 54 tests pass.
- ✅ **Synthetic legit v2 + ablation + product-level eval (2026-09-09)** — `german_synthetic_legit_v2.csv` (60 formal legit messages WITH official links, train only) → train 4,408 / val 513 / test 617 (German test unchanged: 86 phishing / 18 legit). Baseline retrained (C=3): test acc 0.9789, F1 0.9568, FPR 0.0171 · **German-only: acc 0.9231, F1 0.9551, recall 0.9884, FPR 0.3889 (7/18)** – down from 11/18. Ablation `train_baseline.py --no-url-token` (key `baseline_tfidf_logreg_nourl`, `models/baseline_nourl.joblib` stays gitignored): German FPR 0.5000 (9/18), test F1 0.9539 → the `<URL>` token is NOT the problem; top features are now `sie`, `ihre` (formal address), i.e. the legit set still lacks formal German. Both variants in `metrics.json` + `experiments.csv`.
- ✅ **`src/eval_pipeline.py`** runs the FULL verdict logic on the 104 German test rows (original texts looked up from `data/raw`; 33 phishing rows carry `*Link*` and reach the URL layer without a real link). Without the new rule: legit 10 green / 5 yellow / 3 red, phishing 2 / 11 / 73 → product false-alarm rate (legit not green) 0.444, legit→red 0.167, phishing→red 0.849. **New rule in `pipeline.py`** (`TRUSTED_LINK_CAP`): if every link is an official brand domain or Tranco top-10k site and no urgency phrase is found, red-by-probability is capped at yellow unless p ≥ 0.90. With rule: legit 10 / 6 / 2 → legit→red 0.111, phishing unchanged (0.849). `check_url` now also returns `trusted: bool`. 58 tests pass.
- ✅ **Colab DistilBERT results merged (2026-09-10)** — was missing earlier the same day, arrived as `results/colab/{metrics.json,experiments.csv,data_summary.md}` (kept in the repo as provenance). `results/colab/data_summary.md` is **identical** to ours → the Colab run used the SAME splits (4,408 / 513 / 617). New `src/merge_colab_results.py` merges **append-only**: 1 new key `distilbert_multilingual`, 1 new row in `experiments.csv`, the 4 existing rows and 2 existing keys untouched. The exported confusion-matrix PNG was 0 bytes, so `results/confusion_matrix_distilbert.png` was rebuilt from the run's own tn/fp/fn/tp (466/2/13/136 – matches the Colab image).
- ✅ **Experiment: threshold tuning (2026-09-10, `src/tune_threshold.py`)** — sweep 0.10–0.90 (step 0.01) on val, criterion max recall subject to FPR ≤ 0.02. Chosen: baseline **0.22**, baseline_nourl **0.32**. German-only test at those thresholds got clearly WORSE: baseline FPR 0.3889 (7/18) → **0.7778 (14/18)**, nourl 0.5000 → 0.7222; German recall rose to 1.0, test F1 fell 0.9568 → 0.9216. Reason: **val contains English rows only**, so a threshold that is safe on English SMS is far too low for formal German. Keys `baseline_tfidf_logreg_thr0.22`, `baseline_tfidf_logreg_nourl_thr0.32`.
- ✅ **Experiment: ensemble (OR of both tuned models)** — key `ensemble_or_tuned`: test acc 0.9579, F1 0.9187, FPR 0.0513; German acc 0.8654, F1 0.9247, recall 1.0, FPR 0.7778 (14/18). No better than its worst member – both members are the same feature family, so OR only adds false alarms.
- ✅ **Best configuration is unchanged: baseline_tfidf_logreg at the DEFAULT boundaries (yellow ≥ 0.50, red ≥ 0.80) + trusted-link cap.** `eval_pipeline.py` now takes `--yellow-p` / `--red-p` / `--probs`. Best config: legit 10 green / 6 yellow / 2 red, phishing 1 / 7 / 78 → product false-alarm rate 0.444, legit→red 0.111, phishing→red 0.907 (numbers corrected 2026-09-10, see the `*Link*` fix below; before the fix 0.849). With the tuned 0.22 boundary the false-alarm rate rises to **0.778** without catching more phishing as red. Both experiments appended to `experiments.csv`; 58 tests pass.
- ⭐ **DistilBERT vs. baseline (same splits, one test evaluation each):** test acc 0.9757, F1 0.9477, FPR **0.0043** (2 false alarms / 468) · **German-only: acc 0.8942, F1 0.9333, precision 0.9747, recall 0.8953, FPR 0.1111 (2 / 18)**, val F1 0.992. → **German false alarms drop from 7/18 (baseline) to 2/18**, but German recall falls 0.9884 → 0.8953 (**9 of 86 phishing missed** vs 1). The trade is precision for recall; for a product aimed at older adults the low false-alarm rate is the more valuable half, but the 9 misses matter. Most missed German rows are voicemail/bank texts whose link was already `*Link*` in the source, so the URL layer cannot rescue them either.
- ✅ **DistilBERT without the 542 MB model (2026-09-10):** the weights stay OUT of the repo (over the ZIP limit). Instead `notebooks/03_transformer.ipynb` has a new **cell 9** (before the commit/push cell, so its output is pushed) that uses the model still in memory to (a) write `results/distilbert_test_probs.csv` (`index,text,lang,label,p_phishing`, one row per test example) and (b) run the SAME threshold sweep as the baseline by importing `tune`/`append_entry` from `src/tune_threshold.py`, appending `distilbert_multilingual_thr<t>` to `metrics.json` and `experiments.csv`. `tldextract` added to the notebook's pip install (needed by that import). **Not run here – needs the Colab GPU.**
- ✅ **`eval_pipeline.py --probs <csv>`** recomputes the traffic-light table from stored probabilities, so DistilBERT can be evaluated at product level WITHOUT the model. Verified with a control: a probability CSV written from the baseline reproduces the model-driven table **exactly** (identical byte for byte). Guards reject a CSV with missing columns, missing test rows, or texts that do not match `test.csv`.
- 🛠️ **Bug found by that control and fixed:** `eval_pipeline.py` fed the ORIGINAL collected texts to the classifier, but the collected German texts contain the literal `*Link*` placeholder, which `data_prep.py` had converted to the `<URL>` token before training. The classifier therefore saw a token it never learned. Fixed by applying the same normalisation in `eval_pipeline.py` (the URL layer is unaffected – neither string is a real link). **This corrects previously reported product-level numbers:** phishing→red is **0.907 (78/86)**, not 0.849 (73/86). The legit side is unchanged (10 green / 6 yellow / 2 red, false-alarm rate 0.444, legit→red 0.111).
- ⏭️ To switch the product itself to DistilBERT, `models/distilbert/` must still be copied from Drive – `pipeline.py` picks it up automatically, nothing else changes.
- ℹ️ **Threshold tuning + ensemble were already run** (commit `453e090`, 2026-09-10) and were NOT re-run – re-running would only duplicate rows in `experiments.csv`. Product-level table (`eval_pipeline.py`) is unchanged because the active classifier is unchanged. 58 tests pass.
- ❌ **Colab run of 2026-09-10 (evening) did NOT finish** — the pushed notebook (`359a854 Created using Colab`) shows cells 1–4 executed and **cell 5 stopped while downloading `model.safetensors` (542 MB)**; cells 6–11 never ran. Therefore: **no `results/distilbert_test_probs.csv`**, no new keys, `results/colab/` unchanged. `merge_colab_results.py` was run and correctly reported **0 new models, 0 new rows** (idempotent). `eval_pipeline.py --probs results/distilbert_test_probs.csv` could NOT be run – the file does not exist. The DistilBERT numbers we have are still those of the FIRST, successful Colab run (merged in `9064a88`).
- ✅ **Step 9 done: `results/error_analysis.md`** — generated by the new `src/error_analysis.py` (no hand-written numbers). **17 real misclassified German test rows** with one comment each: 7 baseline false alarms, 1 baseline miss, 2 DistilBERT false alarms, 9 DistilBERT misses. **Only 2 rows are wrong in BOTH models**, so their errors are largely disjoint. Four discussion sections: (a) the „Sie/Ihre“ bias with real coefficients (`sie` +3.044 ≈ `call` +3.140, `ihre` +1.757, `uhr` −1.397; 5 of 10 formal legit rows flagged vs 2 of 8 informal, mean p 0.53 vs 0.33), (b) the baseline-vs-DistilBERT trade-off (FPR 0.3889 → 0.1111 against recall 0.9884 → 0.8953), (c) the failed threshold transfer (0.22 from English-only val pushes German FPR to 0.7778), (d) the `*Link*` artifact (33 of 104 German test rows, all phishing) and the evaluation bug it caused, with both product-level numbers recomputed here (phishing→red 0.849 before the fix, 0.907 after).
- ℹ️ **Colab run 2026-09-12:** DistilBERT trained again on the SAME splits (4,408 / 513 / 617; de 304 train / 104 test) and the model is on Drive, but the `GITHUB_TOKEN` secret did not load, so nothing was pushed and the later cells (probability CSV, threshold sweep) did not run. **No new data needed** – the DistilBERT metrics from the first successful run are already merged. `results/distilbert_test_probs.csv` is therefore still missing.
- ✅ **Results files verified complete (2026-09-12):** `metrics.json` holds all **6** keys (baseline, baseline_nourl, both tuned-threshold variants, ensemble, distilbert), each with `date/seed/params/train/test/test_de`; `experiments.csv` has **8 rows, no missing values**. Nothing lost.
- ✅ **Current product table (baseline, after the `*Link*` fix, deutscher Testteil):** harmlos 10 grün / 6 gelb / 2 rot · Phishing 1 / 7 / 78 → Fehlalarmrate 0.444, legit→rot 0.111, Phishing→rot 0.907. Reproduzierbar mit `python src/eval_pipeline.py`.
- ✅ **Step 10 done: `README.md`** — generated by the new `src/make_readme.py` from `results/metrics.json` (results table + traffic-light table computed live, German number formatting). Sections: Projekt (3-Ebenen-Erklärung + Ampel-Logik), Installation, Start (data/training, Gradio, API with curl, pytest, both Colab links), Struktur, Ergebnisse (6-model table, product table, honest caveats, link to error_analysis.md), iOS-Shortcut (6 steps + link to shortcut/README.md), **Android** (HTTP Shortcuts, Galaxy test: fake DHL rot p=0.9785, echte DHL grün p=0.0679 – measured by the team on device, marked as such), Quellen (from SOURCES.md), Hinweis zur KI-Nutzung. **Open TODO in the README: the Google-Drive share link for `models/distilbert/` is still a placeholder** (`<Google-Drive-Freigabelink hier eintragen>`).
- ✅ **Synthetic legit v3.1 integriert (2026-09-18)** — `german_synthetic_legit_v3_1.csv`: **482** formelle deutsche Alltagsnachrichten, train only, keine Überschneidung mit v1/v2; nach Duplikat-Entfernung **467** im Training. Splits jetzt **4.875 / 513 / 617**, deutscher Testteil unverändert (86 Phishing / 18 legitim), also voll vergleichbar. Synthetisch gesamt im Training: 667 (davon 597 legitim). **Echte legitime Zeilen bleiben 36** – der Test enthält weiterhin nur echte Texte.
- ⚖️ **Baseline neu trainiert (C=1): der Zielkonflikt kippt.** Test acc 0.9773, F1 0.9527, FPR 0.0128 · **Deutsch: acc 0.9231, F1 0.9540, recall 0.9651, FPR 0.2778 (5/18)** – Fehlalarme runter von 7/18, dafür 3 statt 1 übersehene Phishing-Nachricht. **Produkt-Ampel (deutscher Testteil): harmlos 12 grün / 6 gelb / 0 rot · Phishing 3 / 23 / 60** → Fehlalarmrate 0.444 → **0.333**, legit→rot 0.111 → **0.000**, aber Phishing→rot **0.907 → 0.698** (60 statt 78 von 86). Keine harmlose Nachricht bekommt mehr Rot, dafür rutschen 18 Phishing-Nachrichten von Rot auf Gelb. **Das ist eine Produktentscheidung, keine reine Metrikfrage.**
- ℹ️ **Bias messbar schwächer:** `sie` +3.044 → **+2.179**, `ihre` +1.757 → **+0.938** (`call` +2.570). Die synthetischen formellen Texte dämpfen den „Sie/Ihre = Phishing“-Effekt, beseitigen ihn aber nicht.
- 🔄 **Abgeleitete Dateien neu erzeugt:** `results/error_analysis.md` (jetzt 15 Beispiele, 4 gemeinsame Fehler) und `README.md`. `make_readme.py` liest die Beispielanzahl und die Wortgewichte jetzt aus den echten Artefakten statt sie fest zu verdrahten.
- 🔤 **Mixed-Script-Erkennung (2026-09-18, `src/script_check.py`)** — findet Wörter, die lateinische Buchstaben mit kyrillischen/griechischen Zwillingen mischen (`Pakеt` mit kyrillischem е). Gemischt heißt: mindestens ein lateinischer Buchstabe UND ein Verwechslungszeichen im selben Wort – rein kyrillischer Text (z. B. „Привет“) löst nichts aus. Zusätzlich zur vorgegebenen Liste ist **ѕ (CYRILLIC DZE)** aufgenommen, weil es in unserem eigenen echten Beispiel steht (`daѕs`, `verlaѕѕen`). Unsichtbare Steuerzeichen (ZWJ/ZWSP/Soft-Hyphen) werden vor der Worttrennung entfernt – sonst zerreißt `P\u200d\u200dakеt` zu `akеt`. In `pipeline.py` neben der Dringlichkeitsprüfung verdrahtet: hebt das Urteil auf **mindestens Gelb**, liefert `reason_de` = „Der Text enthält versteckte fremde Schriftzeichen …“ (außer bei Rot, da gewinnt der stärkere Grund) und **hebt die Trusted-Link-Regel auf**. Neues Feld **`mixed_script`** in der Antwort (Vertrag in `tests/test_pipeline.py`, `pipeline.py` und `api/main.py` nachgezogen; für Gson/iOS-Shortcut abwärtskompatibel). `tests/test_script_check.py`: 20 Tests, darunter der echte vzhh.de-Text → **78 Tests gesamt**.
- ⚠️ **Wirkung auf den Testteil: 0 von 86.** Die einzige echte Zeile mit versteckten Zeichen (Verbraucherzentrale Hamburg, Paket-Smishing) liegt durch den Split mit seed 42 im **Trainings**teil. Die Regel verändert daher **keine** gemessene Metrik – weder positiv noch negativ (auch 0 Fehlalarme auf den 18 legitimen Zeilen). Sie ist durch ein real dokumentiertes Angriffsmuster begründet, **nicht** durch eine gemessene Verbesserung. Das gehört so in die Reflexion.
- 🟡 **Gelb neu gestaltet (2026-09-18):** Überschrift **„UNKLAR“** statt „VORSICHT“ auf Bernstein `#bf8700`, weiße Schrift, plus eine Zeile unter `reason_de`: „Wir sind nicht sicher. Öffnen Sie keine Links und fragen Sie im Zweifel bei der Firma nach – über eine Nummer, die Sie selbst kennen.“ Rot (GEFAHR) und Grün (SICHER) unverändert. Die Demo zeigt außerdem einen Abschnitt „Versteckte Schriftzeichen“ mit den betroffenen Wörtern.
- 🔍 **Erklärbarkeit: Feld `signale` (2026-09-19)** — `pipeline.py` liefert bis zu **5** Wörter/Wortpaare aus der Nachricht, die den Wert nach oben gedrückt haben. Berechnet als **tf-idf-Wert × Koeffizient für genau diesen Text**, nicht als globale Top-Gewichte – dadurch kann nur auftauchen, was wirklich im Text steht. Nur Wort-n-Gramme (Zeichen-n-Gramme wie `xt ` sind für Menschen sinnlos), ohne das `<URL>`-Token, ohne Tokens unter 3 Zeichen, und **jedes Wort nur einmal** (sonst stünde dort „Sie“, „Sie Ihre“, „bestätigen Sie“ – dreimal dasselbe Signal). Die Anzeige übernimmt die Schreibweise aus der Nachricht. **Nur bei aktiver Baseline**; unter DistilBERT ist das Feld leer, weil dort keine Wortgewichte existieren. Feld ist additiv, Formprüfung in `tests/test_pipeline.py` nachgezogen. 6 neue Tests → **84 Tests gesamt**.
- 🖥️ **In der Demo als „Auffällig: …“** unter der Ampelbox – **aber nur bei Gelb und Rot**. Bei Grün wären es harmlose Alltagswörter („ich“, „Hallo“, „komme“), das würde die Zielgruppe nur verunsichern. Beispiel Rot: „Sie“, „bestätigen“, „Paket“, „Ihre“, „Adresse“.
- ℹ️ **Nebenbefund für die Reflexion:** Bei deutschen Phishing-Texten steht **„Sie“ regelmäßig an erster Stelle** der Signale. Die Erklärfunktion macht den dokumentierten Höflichkeits-Bias damit für die Jury unmittelbar sichtbar, statt ihn zu verstecken.
- ⏭️ Remaining before submission: fill in the Drive link; optionally re-run notebook 03 to completion for `distilbert_test_probs.csv` (then `eval_pipeline.py --probs …` and the untested baseline+DistilBERT combination become possible); more REAL German legit messages and German rows in val; demo video.

## Repository layout

```
doppelcheck/
  CLAUDE.md
  data/raw/              uci mirror file, german_phishing.csv, german_legit.csv (never edit raw files)
  data/processed/        train.csv / val.csv / test.csv  (text,label,lang,source)
  data/blocklists/       Step 5: downloaded lists + download_date.txt (gitignored except a small sample)
  data/samples/          Step 6: 3–5 test screenshots (PNG)
  data/SOURCES.md        every dataset: name, original URL, mirror URL if used, license, size, download date
  notebooks/
    01_data.ipynb ✅  02_baseline.ipynb ✅  03_transformer.ipynb (written here, RUN ON COLAB)
  src/
    data_prep.py ✅  train_baseline.py ✅
    fetch_blocklists.py  url_check.py  ocr.py  pipeline.py
  tests/                 pytest: test_url_check.py, test_pipeline.py
  app/gradio_demo.py     web demo
  api/main.py            FastAPI: POST /scan (image) → JSON verdict — used by the iOS Shortcut
  shortcut/              iOS Shortcut instructions (README + screenshots)
  models/                baseline.joblib ✅ ; distilbert lives on Google Drive (too large for ZIP)
  results/               metrics.json ✅ experiments.csv ✅ data_summary.md ✅ confusion_matrix_*.png error_analysis.md
  requirements.txt ✅    README.md (skeleton ✅, finished in Step 10)
```

## Data

| Source | Use | Notes |
|---|---|---|
| UCI SMS Spam Collection (5,574 EN) | phishing/spam text | cite UCI as original; mirror documented in SOURCES.md |
| `data/raw/german_phishing.csv` | own German phishing data | hand-collected from Verbraucherzentrale Phishing-Radar, exported from Google Sheets; columns `text,label,source_url,category`; label=1 |
| `data/raw/german_legit.csv` | German negative class | anonymized everyday messages (parcel notices, bank info, family chat); label=0; target ≥ 100 |
| PhishTank + OpenPhish feeds | URL blocklist | download via `fetch_blocklists.py` (will only work outside this sandbox) |
| Tranco top list | legitimate domains | same |

Rules:
- Dedupe exact and near-duplicates BEFORE splitting. Stratified 80/10/10 by label AND lang, `seed=42`.
- **When the German CSVs arrive: re-run `data_prep.py`, then re-run `train_baseline.py`** so every model uses identical splits. Append new rows to `experiments.csv`; never delete old rows (history is evidence).
- Test set is evaluated exactly once per model. Always report **train AND test** metrics plus **FPR** — the competition form asks for both.
- Report German-only test metrics separately whenever `lang=="de"` rows exist.

## Models

1. **Baseline (done):** TF-IDF word 1–2-grams + char_wb 3–5-grams → LogisticRegression(class_weight="balanced"). Runs on CPU in seconds. Always keep it as the fallback model.
2. **Main:** fine-tune `distilbert-base-multilingual-cased`, binary classification, HF Trainer: 3 epochs, lr 2e-5, batch 16, max_len 128, seed 42, best checkpoint by val F1. **Train only on Google Colab GPU.** The fine-tuned model (~540 MB) is stored on Google Drive and linked in the README — it must NOT go into the code ZIP.
3. `pipeline.py` loads `models/distilbert/` if present locally, otherwise `models/baseline.joblib`, and prints which model is active.
4. If train ≫ test, or the German slice is much weaker than the English slice, say so in `results/error_analysis.md`. That is expected and is good material for the "kritische Reflexion".

## URL analysis (`src/url_check.py`) — rule-based, no ML

- `extract_urls(text)`: handles missing scheme, `hxxp`, obfuscated dots (`dhl[.]de`), trailing punctuation.
- `check_url(url) -> {"level": "red|yellow|green", "reasons": [...]}`
  - **red:** blocklist hit; brand look-alike for a built-in list of ~25 German-relevant brands (DHL, Hermes, DPD, Deutsche Post, Sparkasse, Volksbank, Postbank, Commerzbank, DKB, ING, PayPal, Amazon, Netflix, eBay Kleinanzeigen, Telekom, Vodafone, Finanzamt, ELSTER, Bundesagentur, Krankenkasse …): Levenshtein ≤ 2 to the brand domain, digit-for-letter (`paypa1`), or brand name inside a non-official domain (`dhl-paket-service.top`).
  - **yellow:** URL shortener, IP-address host, uncommon TLD (.top .xyz .icu .click .live .cfd …), `@` in URL, > 3 subdomains, punycode.
  - **green signal:** official brand domain or Tranco top-10k hit (when lists are available).
- Must work WITHOUT downloaded lists (heuristics only) and use them when present.
- Never open links from the user's device. Server-side redirect following is optional (HEAD, timeout 5 s) and off by default.

## Verdict logic (`src/pipeline.py`)

```
p = classifier probability of phishing
red     if p >= 0.80 or url_level == "red"
yellow  if 0.50 <= p < 0.80 or url_level == "yellow" or urgency phrase found
green   otherwise
```
- Urgency phrases (DE): "sofort", "innerhalb von 24 Stunden", "Konto gesperrt", "Konto wird gesperrt", "eingeschränkt", "verifizieren", "Zustellung fehlgeschlagen", "konnte nicht zugestellt werden", "Zollgebühr", "Gewinn", "letzte Mahnung", "dringend". (EN): "urgent", "verify your account", "suspended", "claim", "prize".
- Output: `{"verdict": "red|yellow|green", "score": p, "reason_de": "<one plain-German sentence, ≤ 120 chars>", "urls": [...], "model": "<name>"}`
- `reason_de` must be understandable by a 75-year-old: no jargon, no percentages. Example: `"Vorsicht – diese Nachricht gibt sich als DHL aus und der Link führt zu einer unbekannten Seite."`

## Demo surfaces

- **Gradio** (`app/gradio_demo.py`): tabs "Text einfügen" and "Screenshot hochladen"; big traffic-light box, large font, the reason sentence, list of found URLs. German UI.
- **FastAPI** (`api/main.py`): `POST /scan` multipart image → OCR → pipeline → JSON; `POST /scan-text` for plain text; `GET /health`. Run: `uvicorn api.main:app --port 8000`. Expose with ngrok for the phone demo.
- **iOS Shortcut (no code, documented in `shortcut/README.md`):** Settings → Accessibility → Touch → Back Tap → Double Tap → Shortcut "DoppelCheck". Actions: *Take Screenshot* → *Get Contents of URL* (POST, form field `file` = screenshot, URL = ngrok URL + `/scan`) → *Get Dictionary Value* `reason_de` → *Show Notification*.

## Constraints

- **This sandbox blocks most external downloads (UCI, Hugging Face, PhishTank …) but allows PyPI and raw.githubusercontent.com.** Write every downloader so it fails gracefully with a clear message; the team runs downloads on Colab or locally. Never fake data to work around a blocked download.
- Python 3.10+, pinned `requirements.txt`. Allowed deps: pandas, numpy, scikit-learn, joblib, torch, transformers, datasets, accelerate, easyocr, gradio, fastapi, uvicorn, python-multipart, tldextract, requests, matplotlib, seaborn, pytest. Ask before adding anything else.
- Everything except transformer training runs on CPU.
- Code comments and docstrings in English; README, UI text and `reason_de` in German.
- **Metrics must be REAL.** Never write numbers into `results/` by hand. Every number comes from an executed run.
- Small, readable code. One function per concern. No premature abstraction.
- Commit after every completed step with a message `step N: <what>`; push if GitHub access works, otherwise say so.

## Working agreement for the AI coding assistant

- Work strictly one step at a time. After each step: run it, show the actual output, list errors, then STOP and wait.
- If something fails or a download is blocked, say so and propose an alternative — never fake results or silently skip.
- Before adding a dependency or a feature not in this spec, ask.
- At the end of each step: update the **Current status** section above and give a 3-sentence plain-language explanation of what was built (the team must be able to explain every part to a jury).

## Remaining step prompts (copy one at a time)

4. "Build notebooks/03_transformer.ipynb for Colab GPU per the Models section. Do not run it here; validate syntax only. Merge results into results/metrics.json under key distilbert_multilingual, save the model to Google Drive, add a top markdown cell explaining how to open it in Colab from GitHub."
5. "Install pytest. Build src/fetch_blocklists.py, src/url_check.py and tests/test_url_check.py per the URL analysis section, with ≥ 10 phishing-style and ≥ 10 legit test URLs. Run pytest and show the output."
6. "Build src/ocr.py (easyocr, languages de+en, CPU) and src/pipeline.py per the Verdict logic section, with model fallback. Create 3 sample screenshots in data/samples/ (render text images with PIL) and tests/test_pipeline.py. Run the tests."
7. "Build app/gradio_demo.py per the Demo surfaces section and run it; show that both tabs return a verdict."
8. "Build api/main.py per the Demo surfaces section, run it, test /health, /scan-text and /scan with curl and a sample screenshot. Write shortcut/README.md with the exact iOS Shortcut steps."
9. "Write results/error_analysis.md from the REAL misclassified test examples of every model in metrics.json: 10–20 examples with one comment each, plus a short paragraph on the English-vs-German gap and on the UK-spam feature bias."
10. "Finish README.md in German: Projekt, Installation, Start (Demo + API + Colab), Struktur, Ergebnistabelle generated from results/metrics.json, iOS-Shortcut-Anleitung, Quellen (from data/SOURCES.md), Hinweis zur KI-Nutzung (Claude Code for code generation; concept, data collection/annotation, experiment design, evaluation and reflection by the team)."
