#!/usr/bin/env python3
"""Write site/index.html (free slice) and private/bundle/full.json.gz (the paid list) from
private/rows.json (pipeline/build.py). Every number on the page is computed here."""
import json, datetime as dt, re
from sitekit import render
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
D = json.load(open(ROOT / "private" / "rows.json"))
rows = D["rows"]
ORDER = ["Dispensary", "Grow or manufacturing", "Transport, wholesale, delivery", "Testing or events"]
STAGES = ["Opening soon", "Newly licensed", "Built out, not on the state list", "Licensed"]
PAID = ["contact", "email", "legal", "license", "by"]
for r in rows:
    r["so"] = STAGES.index(r["stage"])
    r["title"] = r["name"] or r["addr"].split(",")[0]
    r["place"] = (r["addr"].split(",")[0] if r["name"] and r["addr"] else "") or ""
n = len(rows); cnt = lambda s: sum(r["stage"] == s for r in rows)
mail = sum(bool(r["email"]) for r in rows); cities = len({r["city"] for r in rows})
pulled = dt.date.fromisoformat(D["pulled"]).strftime("%b %-d, %Y")
ocm = re.search(r"_(\d{6})", D["ocm_file"]).group(1); ocm = dt.date(2000 + int(ocm[4:]), int(ocm[:2]), int(ocm[2:4])).strftime("%b %-d, %Y")
pick = lambda st, k=None, m=2: [r for r in sorted(rows, key=lambda r: r["latest"], reverse=True) if r["stage"] == st and (k is None or r["kind"] == k)][:m]
sample = pick("Opening soon", m=3) + pick("Newly licensed", "Dispensary", 3) + pick("Newly licensed", "Grow or manufacturing", 1) + pick("Newly licensed", "Transport, wholesale, delivery", 1)
sample += [r for r in pick("Licensed", "Transport, wholesale, delivery", 2) if r not in sample][:2]
COLS = [("stage","Stage"),("name","Business (D.B.A.)"),("legal","Legal name"),("kind","Kind"),("btype","State business type"),("addr","Site address"),("city","City"),("county","County"),("contact","Site contact"),("email","Email"),("issued","State license issued"),("expires","License expires"),("license","License #"),("ltype","License type"),("pstage","Minneapolis permit stage"),("pdate","Permit date"),("pwhat","Permit description"),("by","Builder on the permit"),("permit","Permit #")]
cfg = """{chipKey:"kind",chipOrder:%s,csv:"twin-cities-cannabis-openings.csv",cols:%s,
 stats:[["%d","opening soon: a Minneapolis build-out at or near final inspection"],["%d","newly licensed by the state in the last 90 days"],["%d","with a named site contact and email"]],
 legend:[["var(--hot)","Opening soon"],["var(--accent)","Newly licensed"],["var(--done)","Licensed earlier"]],
 dotColor:["var(--accent)","var(--grow)","var(--move)","var(--done)"],
 labels:[[45.005,-93.33,"Minneapolis"],[44.915,-93.04,"Saint Paul"]],
 color:r=>r.stage==="Opening soon"?"var(--hot)":r.stage==="Newly licensed"?"var(--accent)":"var(--done)",
 title:r=>r.title, what:r=>r.pwhat?("Permit: "+r.pwhat):(r.btype||r.kind),
 tag:r=>`<span class="tag ${r.so===0?"hot":""}">${r.stage}</span>`,
 meta:r=>[r.place,r.city,r.issued?("State license "+fmt(r.issued)):"",r.pstage?(r.pstage+" "+fmt(r.pdate)):""],
 paid:r=>[r.contact?`Contact: ${esc(r.contact)}`:"",r.email?r.email.split(/[;,\\s]+/).filter(Boolean).map(e=>`<a href="mailto:${esc(e)}">${esc(e)}</a>`).join(" "):"",r.legal&&r.legal!==r.name?`Entity: ${esc(r.legal)}`:"",r.by?`Builder: ${esc(r.by)}`:""].filter(Boolean).join(" · "),
 sorts:[["newest","Newest first",false],["open","Closest to opening",true],["city","By city",true]],
 sortFn:{newest:r=>r.sort((a,b)=>b.latest.localeCompare(a.latest)),open:r=>r.sort((a,b)=>(a.so-b.so)||b.latest.localeCompare(a.latest)),city:r=>r.sort((a,b)=>a.city.localeCompare(b.city)||a.so-b.so)},
 lockText:n=>`${n} more businesses, every site contact's name and email, and the closest-to-opening sort`}""" % (json.dumps(ORDER), json.dumps(COLS), cnt("Opening soon"), cnt("Newly licensed"), mail)
LIGHT = '--bg:#f3f4f1;--panel:#e7e9e3;--ink:#141a17;--ink2:#333c37;--muted:#626c66;--rule:#d0d5cd;--accent:#1d6b4f;--onaccent:#f3f4f1;--hot:#c0392b;--grow:#7a6a1f;--move:#2c4f8a;--done:#8d958f;--ghost:#c3c9c1;--water:#8fb0bf;--tagbg:#e1e5de;--tagfg:#45504a;--hotbg:#f3d8d3;--hotfg:#8e2418;--display:"Archivo Narrow","Arial Narrow",sans-serif;--body:"Archivo",system-ui,sans-serif;--h1w:700;'
DARK = '--bg:#0f1311;--panel:#171d1a;--ink:#e5ebe7;--ink2:#c0c9c4;--muted:#8a948e;--rule:#27302b;--accent:#5fc49b;--onaccent:#0f1311;--hot:#f07a6a;--grow:#d1bb5c;--move:#86a8e6;--done:#68716c;--ghost:#2a332e;--water:#3d6176;--tagbg:#1f2723;--tagfg:#adb8b2;--hotbg:#45201a;--hotfg:#f7b0a6;'
counts = render(rows=rows, sample=sample, paid_fields=PAID, chip_key="kind", chip_order=ORDER, cfg_js=cfg, site="mn-cannabis-openings", subs={
 "__TITLE__": "Twin Cities Cannabis Openings",
 "__DESC__": f"{n} Twin Cities cannabis businesses newly licensed or about to open, from the state license list and Minneapolis build-out permits.",
 "__FONTS__": "family=Archivo+Narrow:wght@700&family=Archivo:wght@400;500;600",
 "__LIGHT__": LIGHT, "__DARK__": DARK,
 "__EYEBROW__": f"For security, transport and service firms · Minnesota public records · updated {pulled}",
 "__H1__": f"{n} Twin Cities cannabis businesses licensed or about to open",
 "__LEDE__": f"Every dispensary needs guards at the door and every grow needs product moved. These are the seven-county metro's licensed cannabis businesses, plus the Minneapolis dispensaries and grows building out right now. <b>{cnt('Opening soon')} are at or near final inspection</b>, {cnt('Newly licensed')} got their state license in the last 90 days, and the state lists a named contact and email for {mail}.",
 "__MAPLABEL__": "Map of the Twin Cities with each cannabis business as a dot",
 "__NOTE__": f"<p>Sources, all public: the Minnesota Office of Cannabis Management's licensed-business list (published {ocm}), and the City of Minneapolis building permit register (pulled {pulled}).</p><p>How the stage is read. Opening soon: a Minneapolis permit for a dispensary or grow is under construction or at final inspection. Newly licensed: the state license was issued in the last 90 days. Built out, not on the state list: a finished Minneapolis cannabis permit at an address the state list doesn't carry yet. Only Minneapolis publishes its permits, so suburban and Saint Paul rows carry the state license alone. Businesses with no site address on the state list sit at the middle of their city on the map.</p><p>Hemp-edible (LPHE) retailers are left out. From Aidan Jude at Brick &amp; Mortar (aidan@brickandmortar.dev).</p>"})
print("rows", n, {s: cnt(s) for s in STAGES}, counts, "email", mail, "cities", cities, "sample", len(sample))
