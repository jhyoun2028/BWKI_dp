"""Tests for src/url_check.py (heuristics without lists + a tiny fixture blocklist)."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from url_check import Lists, check_url, extract_urls, levenshtein, load_lists  # noqa: E402

NO_LISTS = Lists()  # heuristics only, independent of files in data/blocklists/

PHISHING = [
    ("http://dhl-paket-service.top/track", "red"),              # brand token + odd TLD
    ("https://paypa1.com/login", "red"),                         # digit for letter
    ("http://sparkasse-sicherheit.de/verify", "red"),            # brand in non-official domain
    ("https://www.amaz0n-kundenservice.de/konto", "red"),        # digit + brand token
    ("http://netflix-konto-verifizieren.click", "red"),
    ("https://commerzbank.de.login-portal.icu/", "red"),         # brand hidden in subdomain
    ("http://volksbank-online-banking.live/", "red"),
    ("https://kleinanzeigen-zahlung.cfd/pay", "red"),
    ("http://www.dkb-sicherheit.de/", "red"),                    # short brand as token
    ("http://ing-diba-verify.top/", "red"),
    ("https://sparkasee.de/", "red"),                            # typo-squatting (Levenshtein 1)
    ("http://192.168.0.1/login", "yellow"),                      # IP host
    ("https://bit.ly/3xYzAbc", "yellow"),                        # shortener
    ("http://secure.login.account.update.example.xyz/", "yellow"),  # >3 subdomains + TLD
    ("https://user@evil-site.com/", "yellow"),                   # @ in URL
    ("http://xn--pypal-4ve.com/", "yellow"),                     # punycode
]

LEGIT = [
    "https://www.dhl.de/de/privatkunden.html",
    "https://www.sparkasse.de/",
    "https://www.paypal.com/signin",
    "https://www.amazon.de/dp/B08XYZ",
    "https://www.commerzbank.de/",
    "https://www.telekom.de/hilfe",
    "https://www.kleinanzeigen.de/s-anzeige/12345",
    "https://www.netflix.com/browse",
    "https://www.elster.de/eportal/start",
    "https://de.wikipedia.org/wiki/Phishing",
    "https://www.arbeitsagentur.de/",
    "https://www.tagesschau.de/inland/",
    "https://mail.google.com/",
    "https://www.bundesregierung.de/",
]


@pytest.mark.parametrize("url,expected", PHISHING)
def test_phishing_urls(url, expected):
    result = check_url(url, NO_LISTS)
    assert result["level"] == expected, result
    assert result["reasons"]


@pytest.mark.parametrize("url", LEGIT)
def test_legit_urls(url):
    result = check_url(url, NO_LISTS)
    assert result["level"] == "green", result


def test_extract_plain_and_missing_scheme():
    text = "Bitte hier bestätigen: dhl.de/track und https://www.paypal.com/signin."
    assert extract_urls(text) == ["http://dhl.de/track", "https://www.paypal.com/signin"]


def test_extract_hxxp_and_obfuscated_dots():
    text = "Ihr Paket: hxxp://dhl-paket-service[.]top/track – oder sparkasse(.)de"
    urls = extract_urls(text)
    assert urls == ["http://dhl-paket-service.top/track", "http://sparkasse.de"]


def test_extract_ignores_abbreviations_and_trailing_punctuation():
    text = "Das ist z.B. kein Link, aber www.amazon.de! Und (siehe telekom.de)."
    assert extract_urls(text) == ["http://www.amazon.de", "http://telekom.de"]


def test_extract_no_urls():
    assert extract_urls("Hallo Mama, bin gut angekommen.") == []


def test_extract_then_check_red():
    urls = extract_urls("Konto gesperrt! Sofort verifizieren: hxxps://paypa1-sicherheit[.]xyz/login")
    assert urls == ["https://paypa1-sicherheit.xyz/login"]
    assert check_url(urls[0], NO_LISTS)["level"] == "red"


def test_blocklist_hit_is_red(tmp_path):
    (tmp_path / "openphish.txt").write_text("http://harmless-looking-site.com/login\n")
    (tmp_path / "phishtank.csv").write_text(
        "phish_id,url,phish_detail_url,submission_time,verified,verification_time,online,target\n"
        "1,https://example-shop.de/pay,,,yes,,yes,Other\n")
    lists = load_lists(tmp_path)
    assert check_url("http://harmless-looking-site.com/login", lists)["level"] == "red"
    assert check_url("https://example-shop.de/pay", lists)["level"] == "red"
    # same URLs without lists are not red
    assert check_url("http://harmless-looking-site.com/login", NO_LISTS)["level"] == "green"


def test_tranco_gives_green_signal_and_suppresses_lookalike(tmp_path):
    (tmp_path / "tranco_top1m.csv").write_text("1,google.com\n2,alster.de\n")
    lists = load_lists(tmp_path)
    r = check_url("https://www.google.com/", lists)
    assert r["level"] == "green" and any("Tranco" in x for x in r["reasons"])
    # "alster" is 1 edit from "elster" but a known site, so no look-alike alarm
    assert check_url("https://alster.de/", lists)["level"] == "green"


def test_missing_lists_dir_is_fine(tmp_path):
    lists = load_lists(tmp_path / "does-not-exist")
    assert not lists.available
    assert check_url("https://www.dhl.de/", lists)["level"] == "green"


def test_levenshtein():
    assert levenshtein("paypal", "paypal") == 0
    assert levenshtein("paypal", "paypa1") == 1
    assert levenshtein("sparkasse", "sparkase") == 1
    assert levenshtein("amazon", "arnazon") == 2
