"""The page prints counts straight from private/rows.json, and site/ ships only the free slice.
Pins the sibling bugs found in mpls-new-rentals on 2026-10-18 (address title-casing that turned
Newton into NEwton; a "pulled" date that was the day build.py ran, not the day the permits were
pulled; a rolling "last 90 days" measured from a different day than the page's "updated" date).
Run from the repo root: python3 -m pytest -q tests
"""
import datetime as dt, gzip, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.load(open(ROOT / "private" / "rows.json"))
ROWS = D["rows"]
PAGE = (ROOT / "site" / "index.html").read_text()
FREE = json.loads(re.search(r"\nconst FREE=(\{.*?\});\n", PAGE).group(1))
FULL = json.loads(gzip.open(ROOT / "private" / "bundle" / "full.json.gz", "rt").read())["rows"]
PAID = ["contact", "email", "legal", "license", "by"]
STAGES = ["Opening soon", "Newly licensed", "Built out, not on the state list", "Licensed"]


def test_pulled_is_the_permit_pull_date_not_the_build_day():
    assert D["pulled"] == json.load(open(ROOT / "private" / "permits_raw.json"))["pulled"]


def test_addresses_keep_street_names_whole():
    bad = [r["addr"] for r in ROWS if re.search(r"\b(NE|SE|NW|SW)[a-z]", r["addr"])]
    assert not bad, bad


def test_newly_licensed_is_ninety_days_before_the_pulled_date():
    cut = (dt.date.fromisoformat(D["pulled"]) - dt.timedelta(days=90)).isoformat()
    for r in ROWS:
        assert r["stage"] in STAGES, r
        if r["stage"] == "Newly licensed":
            assert r["issued"] >= cut, r
        if r["stage"] == "Licensed":
            assert r["issued"] and r["issued"] < cut, r
        if r["stage"] == "Opening soon":
            assert r["pstage"] in ("Final inspection", "Under construction"), r


def test_page_counts_are_the_data():
    n = len(ROWS)
    cnt = lambda s: sum(r["stage"] == s for r in ROWS)
    mail = sum(bool(r["email"]) for r in ROWS)
    assert FREE["total"] == n
    assert f"<h1>{n} Twin Cities cannabis businesses" in PAGE
    assert f'stats:[["{cnt("Opening soon")}","opening soon' in PAGE
    assert f'["{cnt("Newly licensed")}","newly licensed by the state in the last 90 days"]' in PAGE
    assert f'["{mail}","with a named site contact and email"]' in PAGE
    assert f"<b>{cnt('Opening soon')} are at or near final inspection</b>, {cnt('Newly licensed')} got their state license in the last 90 days, and the state lists a named contact and email for {mail}." in PAGE
    for k, v in FREE["counts"].items():
        assert v == sum(r["kind"] == k for r in ROWS), k
    assert len(FREE["dots"]) == sum(bool(r.get("lat")) for r in ROWS)


def test_site_ships_only_the_free_slice():
    assert 8 <= len(FREE["rows"]) <= 10 and len(FULL) == len(ROWS)
    keys = {k for r in FREE["rows"] for k in r}
    assert not keys & set(PAID), keys & set(PAID)
    for r in FREE["rows"]:
        assert any(f["addr"] == r["addr"] and f["name"] == r["name"] and f["stage"] == r["stage"] for f in FULL), r["title"]
    assert not list((ROOT / "site").rglob("*.gz")) and not (ROOT / "site" / "api" / "_full").exists()
    assert "_vercel/insights/script.js" in PAGE and "posthog" in PAGE
