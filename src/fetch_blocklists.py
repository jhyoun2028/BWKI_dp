"""Download URL blocklists and the Tranco top list into data/blocklists/.

This sandbox blocks these hosts, so run it on Colab or locally:
    python src/fetch_blocklists.py

Every source fails independently with a clear message; url_check.py works
without the files and picks them up when present.
"""
from __future__ import annotations

import io
import sys
import zipfile
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BLOCKLIST_DIR = ROOT / "data" / "blocklists"

SOURCES = {
    # name: (url, target filename)
    "phishtank": ("https://data.phishtank.com/data/online-valid.csv", "phishtank.csv"),
    "openphish": ("https://openphish.com/feed.txt", "openphish.txt"),
    "tranco": ("https://tranco-list.eu/top-1m.csv.zip", "tranco_top1m.csv"),
}
HEADERS = {"User-Agent": "DoppelCheck/0.1 (student project; BWKI)"}


def fetch(name: str, url: str, target: Path) -> bool:
    """Download one source; returns True on success, prints a reason otherwise."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        r.raise_for_status()
        data = r.content
        if name == "tranco":
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                data = zf.read(zf.namelist()[0])
        target.write_bytes(data)
        lines = data.count(b"\n")
        print(f"[{name}] ok: {target.relative_to(ROOT)} ({len(data) / 1e6:.1f} MB, ~{lines:,} Zeilen)")
        return True
    except Exception as e:  # network blocked, rate-limited, bad zip ...
        print(f"[{name}] FEHLER: {url} konnte nicht geladen werden ({type(e).__name__}: {e})")
        return False


def main() -> int:
    BLOCKLIST_DIR.mkdir(parents=True, exist_ok=True)
    ok = {name: fetch(name, url, BLOCKLIST_DIR / fname) for name, (url, fname) in SOURCES.items()}
    if any(ok.values()):
        (BLOCKLIST_DIR / "download_date.txt").write_text(
            f"{date.today().isoformat()}\n" + "".join(f"{n}: {'ok' if v else 'fehlt'}\n" for n, v in ok.items()))
    failed = [n for n, v in ok.items() if not v]
    if failed:
        print(f"\nNicht geladen: {', '.join(failed)}. url_check.py läuft trotzdem (nur Heuristiken). "
              "Bitte auf Colab oder lokal erneut ausführen.")
        return 1
    print("\nAlle Listen geladen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
