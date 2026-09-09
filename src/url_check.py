"""Rule-based URL analysis (no ML): extract URLs from text and rate each one.

    extract_urls(text) -> list[str]
    check_url(url, lists=None) -> {"level": "red"|"yellow"|"green", "reasons": [...]}

Works without downloaded lists (heuristics only). If data/blocklists/ holds
phishtank.csv / openphish.txt / tranco_top1m.csv (see fetch_blocklists.py),
they are used automatically. Reasons are plain German (shown to the user).
"""
from __future__ import annotations

import csv
import ipaddress
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import tldextract

ROOT = Path(__file__).resolve().parents[1]
BLOCKLIST_DIR = ROOT / "data" / "blocklists"
TRANCO_TOP_N = 10_000

# Offline extractor: uses the public-suffix snapshot bundled with tldextract
# (no network call on first use).
_extract = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)

# brand key -> official registered domains
BRANDS: dict[str, set[str]] = {
    "dhl": {"dhl.de", "dhl.com"},
    "hermes": {"myhermes.de", "hermesworld.com"},
    "dpd": {"dpd.de", "dpd.com"},
    "deutschepost": {"deutschepost.de"},
    "sparkasse": {"sparkasse.de"},
    "volksbank": {"volksbank.de", "vr.de"},
    "postbank": {"postbank.de"},
    "commerzbank": {"commerzbank.de"},
    "dkb": {"dkb.de"},
    "ing": {"ing.de", "ing.com"},
    "paypal": {"paypal.com", "paypal.de"},
    "amazon": {"amazon.de", "amazon.com"},
    "netflix": {"netflix.com"},
    "kleinanzeigen": {"kleinanzeigen.de", "ebay-kleinanzeigen.de"},
    "ebay": {"ebay.de", "ebay.com"},
    "telekom": {"telekom.de", "t-online.de"},
    "vodafone": {"vodafone.de", "vodafone.com"},
    "o2": {"o2online.de", "o2.de"},
    "finanzamt": {"finanzamt.de", "bzst.de"},
    "elster": {"elster.de"},
    "bundesagentur": {"arbeitsagentur.de"},
    "krankenkasse": {"tk.de", "aok.de", "barmer.de", "dak.de"},
    "bundesbank": {"bundesbank.de"},
    "zoll": {"zoll.de"},
    "targobank": {"targobank.de"},
}
OFFICIAL_DOMAINS: set[str] = {d for ds in BRANDS.values() for d in ds}
_MIN_LEN_FOR_LEVENSHTEIN = 5     # short names (dhl, ing, ebay) only via token/digit rules
_MIN_LEN_FOR_SUBSTRING = 5       # "ing" must not match "booking"

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "rb.gy", "shorturl.at",
    "ow.ly", "buff.ly", "tiny.cc", "s.id", "t.ly", "rebrand.ly", "bl.ink", "lnkd.in",
    "u.to", "v.gd", "clck.ru", "qr.ae", "short.io", "tny.im", "1url.cz",
}
UNCOMMON_TLDS = {
    "top", "xyz", "icu", "click", "live", "cfd", "buzz", "rest", "monster", "quest", "sbs",
    "cyou", "cam", "gq", "ml", "cf", "tk", "ga", "work", "zip", "mov", "lol", "beauty",
    "bond", "surf", "fit", "win", "bid", "loan", "men", "stream", "download", "review",
    "party", "date", "kim", "lat", "pw", "cc", "su", "ws", "vip", "online", "site",
    "website", "space", "fun", "wang", "link", "hair", "skin", "boats", "yachts",
}
DIGIT_TO_LETTER = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "9": "g"})


# ---------------------------------------------------------------------------
# Lists (optional)
# ---------------------------------------------------------------------------
@dataclass
class Lists:
    blocked_urls: set[str] = field(default_factory=set)
    blocked_hosts: set[str] = field(default_factory=set)
    tranco_top: set[str] = field(default_factory=set)

    @property
    def available(self) -> bool:
        return bool(self.blocked_urls or self.tranco_top)


def _norm_url(url: str) -> str:
    return url.strip().lower().rstrip("/")


def load_lists(directory: Path = BLOCKLIST_DIR) -> Lists:
    """Load whatever list files exist in `directory`; missing files are fine."""
    lists = Lists()
    pt = directory / "phishtank.csv"
    if pt.exists():
        with pt.open(encoding="utf-8", errors="ignore", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("url"):
                    _add_blocked(lists, row["url"])
    op = directory / "openphish.txt"
    if op.exists():
        for line in op.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip():
                _add_blocked(lists, line)
    tr = directory / "tranco_top1m.csv"
    if tr.exists():
        with tr.open(encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= TRANCO_TOP_N:
                    break
                parts = line.strip().split(",")
                if len(parts) == 2:
                    lists.tranco_top.add(parts[1].lower())
    return lists


def _add_blocked(lists: Lists, url: str) -> None:
    lists.blocked_urls.add(_norm_url(url))
    host = urlsplit(url if "://" in url else "http://" + url).hostname
    if host:
        lists.blocked_hosts.add(host.lower())


_DEFAULT_LISTS: Lists | None = None


def default_lists() -> Lists:
    global _DEFAULT_LISTS
    if _DEFAULT_LISTS is None:
        _DEFAULT_LISTS = load_lists()
    return _DEFAULT_LISTS


# ---------------------------------------------------------------------------
# URL extraction
# ---------------------------------------------------------------------------
_OBFUSCATIONS = [
    (re.compile(r"hxxps?://", re.I), lambda m: m.group(0).lower().replace("hxxp", "http")),
    (re.compile(r"\s*[\[\(\{]\s*(?:\.|dot)\s*[\]\)\}]\s*", re.I), lambda m: "."),
    (re.compile(r"\s+dot\s+", re.I), lambda m: "."),
]
_URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"']+"                       # with scheme or www
    r"|(?<![\w@.-])(?:[a-z0-9-]+\.)+[a-z]{2,63}(?:/[^\s<>\"']*)?",  # bare domain(/path)
    re.I,
)
_TRAILING = ".,;:!?)]}>\"'"


def _hostname(url: str) -> str:
    """Hostname of a URL-like string; '' if urlsplit rejects it (e.g. stray '[')."""
    try:
        return urlsplit(url).hostname or ""
    except ValueError:
        return ""


def _deobfuscate(text: str) -> str:
    for pattern, repl in _OBFUSCATIONS:
        text = pattern.sub(repl, text)
    return text


def extract_urls(text: str) -> list[str]:
    """Find URLs in free text; returns them normalized with a scheme, in order, unique."""
    found: list[str] = []
    for m in _URL_RE.finditer(_deobfuscate(text)):
        raw = m.group(0).rstrip(_TRAILING)
        # strip an unbalanced closing paren, e.g. "(see dhl.de/track)" -> already handled by rstrip
        url = raw if re.match(r"https?://", raw, re.I) else "http://" + raw
        ext = _extract(_hostname(url))
        if not ext.suffix or not ext.domain:      # "z.B." / "e.g." / version numbers
            continue
        if url not in found:
            found.append(url)
    return found


URL_MASK = "<URL>"


def mask_urls(text: str) -> str:
    """Replace every URL (same detection as extract_urls) with URL_MASK.

    Used for classifier input in training AND inference, so the model learns
    "contains a link" instead of memorizing domains; the URL itself is judged
    separately by check_url.
    """
    def repl(m: re.Match) -> str:
        raw = m.group(0).rstrip(_TRAILING)
        trailing = m.group(0)[len(raw):]
        url = raw if re.match(r"https?://", raw, re.I) else "http://" + raw
        ext = _extract(_hostname(url))
        return (URL_MASK + trailing) if (ext.suffix and ext.domain) else m.group(0)
    return _URL_RE.sub(repl, _deobfuscate(text))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _brand_lookalike(host: str, registered: str, domain: str) -> list[str]:
    """Return red reasons for brand look-alikes; empty list if none."""
    reasons: list[str] = []
    if registered in OFFICIAL_DOMAINS:
        return reasons
    host_wo_suffix = host[: -len(_extract(host).suffix) - 1] if _extract(host).suffix else host
    tokens = [t for t in re.split(r"[.\-_]+", host_wo_suffix) if t]
    compact = host_wo_suffix.replace(".", "").replace("-", "").replace("_", "")
    deleeted = domain.translate(DIGIT_TO_LETTER)
    has_digits = any(ch.isdigit() for ch in domain)

    for brand, officials in BRANDS.items():
        official_names = {o.split(".")[0] for o in officials} | {brand}
        # 1) brand name as a whole token, or as substring for long names
        if brand in tokens or (len(brand) >= _MIN_LEN_FOR_SUBSTRING and brand in compact):
            reasons.append(f"Gibt sich als {_display(brand)} aus, ist aber nicht die offizielle Seite")
            continue
        # 2) digits replacing letters: paypa1, amaz0n
        if has_digits and any(deleeted == n or deleeted in tokens or n in re.split(r"[\-_]+", deleeted)
                              for n in official_names):
            reasons.append(f"Zahlen statt Buchstaben im Namen von {_display(brand)} (Tarnung)")
            continue
        # 3) typo-squatting: Levenshtein <= 2 to an official name (long names only)
        for n in official_names:
            if len(n) < _MIN_LEN_FOR_LEVENSHTEIN:
                continue
            limit = 2 if len(n) >= 6 else 1
            if domain != n and levenshtein(domain, n) <= limit:
                reasons.append(f"Sieht aus wie {_display(brand)}, ist aber leicht verändert geschrieben")
                break
    return reasons


def _display(brand: str) -> str:
    return {"deutschepost": "Deutsche Post", "kleinanzeigen": "Kleinanzeigen", "dhl": "DHL",
            "dpd": "DPD", "dkb": "DKB", "ing": "ING", "elster": "ELSTER", "o2": "O2",
            "bundesagentur": "Bundesagentur für Arbeit", "paypal": "PayPal", "ebay": "eBay"
            }.get(brand, brand.capitalize())


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def check_url(url: str, lists: Lists | None = None) -> dict:
    """Rate one URL. Returns {"level": "red"|"yellow"|"green", "reasons": [...], "trusted": bool}.

    trusted = official brand domain or Tranco top-10k hit without any warning sign."""
    lists = default_lists() if lists is None else lists
    url = _deobfuscate(url.strip())
    if not re.match(r"[a-z][a-z0-9+.-]*://", url, re.I):
        url = "http://" + url
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    ext = _extract(host)
    registered = (ext.top_domain_under_public_suffix or host).lower()
    red: list[str] = []
    yellow: list[str] = []
    green: list[str] = []

    if not host:
        return {"level": "yellow", "reasons": ["Link konnte nicht gelesen werden"], "trusted": False}

    # --- red: blocklists ---------------------------------------------------
    in_tranco = registered in lists.tranco_top
    if _norm_url(url) in lists.blocked_urls or (host in lists.blocked_hosts and not in_tranco):
        red.append("Link steht auf einer bekannten Phishing-Liste (PhishTank/OpenPhish)")

    # --- red: brand look-alikes (skip well-known sites) --------------------
    if not _is_ip(host) and not in_tranco:
        red.extend(_brand_lookalike(host, registered, ext.domain.lower()))

    # --- yellow ------------------------------------------------------------
    if registered in SHORTENERS:
        yellow.append("Kurzlink – das eigentliche Ziel ist nicht sichtbar")
    if _is_ip(host):
        yellow.append("Link führt zu einer nackten IP-Adresse statt zu einem Namen")
    if ext.suffix.split(".")[-1] in UNCOMMON_TLDS:
        yellow.append(f"Ungewöhnliche Endung .{ext.suffix.split('.')[-1]}")
    if parts.username is not None or "@" in parts.netloc:
        yellow.append("Enthält ein @-Zeichen – das echte Ziel steht dahinter versteckt")
    if ext.subdomain and len(ext.subdomain.split(".")) > 3:
        yellow.append("Sehr viele Unter-Adressen vor dem eigentlichen Namen")
    if "xn--" in host:
        yellow.append("Enthält versteckte Sonderzeichen (Punycode)")

    # --- green signals -----------------------------------------------------
    if registered in OFFICIAL_DOMAINS:
        green.append("Offizielle Seite einer bekannten Firma oder Behörde")
    elif in_tranco:
        green.append("Bekannte, viel besuchte Seite (Tranco Top 10.000)")

    trusted = bool(green) and not red and not yellow
    if red:
        return {"level": "red", "reasons": red + yellow, "trusted": False}
    if yellow:
        return {"level": "yellow", "reasons": yellow, "trusted": False}
    return {"level": "green", "reasons": green or ["Keine Auffälligkeiten gefunden"], "trusted": trusted}


if __name__ == "__main__":  # quick manual check
    import sys
    text = " ".join(sys.argv[1:]) or "Ihr Paket wartet: hxxp://dhl-paket-service[.]top/track"
    for u in extract_urls(text):
        print(u, "→", check_url(u))
