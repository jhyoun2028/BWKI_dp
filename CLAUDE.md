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
- ✅ **Step 4** — `notebooks/03_transformer.ipynb` written and syntax-validated here, **NOT run** (no GPU, Hugging Face blocked). Runs on Colab: clone repo → same splits → DistilBERT 3 epochs / lr 2e-5 / batch 16 / max_len 128 / seed 42, best checkpoint by val F1 → one test evaluation → merges `distilbert_multilingual` into `results/metrics.json`, appends `experiments.csv`, saves `confusion_matrix_distilbert.png`, model to Drive `DoppelCheck/models/distilbert/`, pushes `results/` back (needs Colab secret `GITHUB_TOKEN`). **Waiting for the Colab run.**
- ⏭️ Next: Step 5 (URL module), then 6–10.

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
