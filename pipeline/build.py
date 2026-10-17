"""Twin Cities cannabis businesses newly licensed or about to open.
Sources: MN Office of Cannabis Management licensed-business list (xlsx, private/cache/), and the
Minneapolis permit register (pipeline/pull_permits.py -> private/permits_raw.json) for dispensary
and grow build-outs. Geocodes addresses with the free Census batch geocoder (cached).
Writes private/rows.json.

    python3 pipeline/pull_permits.py private/permits_raw.json && python3 pipeline/build.py
"""
import json, re, csv, io, datetime as dt, subprocess, collections
from pathlib import Path
import openpyxl
ROOT = Path(__file__).resolve().parent.parent
PRIV = ROOT / "private"; CACHE = PRIV / "cache"
XL = sorted(CACHE.glob("ocm_licensed_*.xlsx"))[-1]
METRO = {"Hennepin", "Ramsey", "Dakota", "Anoka", "Washington", "Scott", "Carver"}
TODAY = dt.date.today(); NEW = (TODAY - dt.timedelta(days=90)).isoformat()
wb = openpyxl.load_workbook(XL, read_only=True)
raw = list(wb.worksheets[0].iter_rows(values_only=True)); H = raw[0]
lic = [dict(zip(H, r)) for r in raw[1:] if r[0]]
lic = [r for r in lic if r["County"] in METRO]
def DT(v):
    if v is None or v=="N/A": return ""
    if hasattr(v,"date"): return v.date().isoformat()
    import datetime as _d
    for f in ("%m/%d/%Y","%Y-%m-%d"):
        try: return _d.datetime.strptime(str(v).strip()[:10],f).date().isoformat()
        except ValueError: pass
    return ""
NA = lambda v: "" if v in (None, "N/A", "n/a") else str(v).strip()
def kind(bt):
    bt = bt or ""
    if "Retail" in bt: return "Dispensary"
    if re.search(r"Cultivation|Manufactur", bt): return "Grow or manufacturing"
    if re.search(r"Transport|Wholesal|Delivery", bt): return "Transport, wholesale, delivery"
    return "Testing or events"
SUF = {"AVENUE": "AVE", "STREET": "ST", "ROAD": "RD", "BOULEVARD": "BLVD", "PARKWAY": "PKWY", "DRIVE": "DR", "PLACE": "PL", "LANE": "LN", "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W", "NORTHEAST": "NE", "SOUTHEAST": "SE"}
DIRS = {"N", "S", "E", "W", "NE", "SE", "NW", "SW", "NORTH", "SOUTH", "EAST", "WEST", "NORTHEAST", "SOUTHEAST"}
def key(a):
    """house number + first street word, directionals dropped: '5 E 38th Street' == '5 38TH ST E'."""
    a = re.sub(r",.*$", "", (a or "").upper()).replace(".", "")
    t = [x for x in a.split() if x not in DIRS]
    return " ".join(t[:2])
rows = []
for r in lic:
    addr = NA(r["Retail Site Address"])
    issued = DT(r["Site License Issued Date"])
    rows.append(dict(name=NA(r["D.B.A. (Doing Business As)"]) or NA(r["Legal Business Name"]), legal=NA(r["Legal Business Name"]),
                     kind=kind(r["Business Type"]), btype=NA(r["Business Type"]), ltype=NA(r["License Type"]), addr=addr,
                     city=NA(r["City"]), county=NA(r["County"]), issued=issued,
                     expires=DT(r["License Expiration Date"]),
                     contact=NA(r["Site Contact"]), email=NA(r["Email"]).replace(" ", ""), license=NA(r["License Number"]),
                     equity=NA(r["Social Equity Classified"]) == "Yes", medical=NA(r["Medical Cannabis Retail"]) == "Yes",
                     permit="", pstage="", pdate="", pwhat="", by=""))
# Minneapolis build-out permits
P = json.load(open(PRIV / "permits_raw.json"))["rows"]
CAN = re.compile(r"cannab|cannib|dispensar|dispenser", re.I)
D = lambda ms: dt.datetime.utcfromtimestamp(ms / 1000).date().isoformat() if ms else ""
def what(c):
    c = re.split(r"certificate of occupancy|CERTIFICATE OF OCCUPANCY|const type|Building Code|\(JJL\)|-ACW|\*\*\*|MECHANICAL PERMIT|mechanical plans|A MECHANICAL|PRIOR TO|SUBMIT A|A LETTER|LETTER FROM", c or "")[0]
    return re.sub(r"\s+", " ", c).strip(" .-")[:110]
STG = {"Final Inspection": "Final inspection", "Inspection": "Under construction", "Closed": "Finished"}
perm = {}
for p in P:
    if not CAN.search(p["comments"] or "") or p["milestone"] not in STG or not p["Display"]:
        continue
    if re.search(r"nurses station|exam room", p["comments"] or "", re.I):
        continue
    k = key(p["Display"])
    rank = ["Final Inspection", "Inspection", "Closed"].index(p["milestone"])
    if k not in perm or rank < perm[k]["rank"]:
        perm[k] = dict(rank=rank, addr=p["Display"], stage=STG[p["milestone"]], date=D(p["issueDate"]), done=D(p["completeDate"]),
                       what=what(p["comments"]), permit=p["permitNumber"], lat=p["Latitude"], lon=p["Longitude"],
                       by=p["applicantName"] if re.search(r"\b(INC|LLC|CONSTRUCTION|BUILDERS|COMPANY|CO|CORP|GROUP|CONTRACTING|DESIGN)\b", (p["applicantName"] or "").upper()) else "")
used = set()
for r in rows:
    if r["city"] == "Minneapolis" and r["addr"] and key(r["addr"]) in perm:
        p = perm[key(r["addr"])]; used.add(key(r["addr"]))
        r.update(permit=p["permit"], pstage=p["stage"], pdate=p["done"] or p["date"], pwhat=p["what"], by=p["by"], lat=p["lat"], lon=p["lon"])
for k, p in perm.items():
    if k in used: continue
    rows.append(dict(name="", legal="", kind="Grow or manufacturing" if re.search(r"cultivat|manufactur|processing|warehouse|grow|laborator|testing", p["what"], re.I) else "Dispensary",
                     btype="", ltype="", addr=re.sub(r"(\d)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), re.sub(r"\s*#.*$", "", p["addr"]).title()).replace(" Ne", " NE").replace(" Se", " SE"), city="Minneapolis", county="Hennepin", issued="", expires="", contact="", email="", license="",
                     equity=False, medical=False, permit=p["permit"], pstage=p["stage"], pdate=p["done"] or p["date"], pwhat=p["what"], by=p["by"], lat=p["lat"], lon=p["lon"]))
# geocode the rest (Census batch, free, cached)
GC = CACHE / "geocode.json"; G = json.load(open(GC)) if GC.exists() else {}
need = [r["addr"] for r in rows if r["addr"] and not r.get("lat") and r["addr"] not in G]
if need:
    buf = io.StringIO(); w = csv.writer(buf)
    for i, a in enumerate(need):
        m = re.match(r"(.*?),\s*([^,]+),\s*MN\s*(\d{5})?", a)
        w.writerow([i, m.group(1), m.group(2), "MN", m.group(3) or ""] if m else [i, a, "", "MN", ""])
    (CACHE / "geo_in.csv").write_text(buf.getvalue())
    out = subprocess.run(["curl", "-s", "--form", f"addressFile=@{CACHE/'geo_in.csv'}", "--form", "benchmark=Public_AR_Current",
                          "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"], capture_output=True, text=True, timeout=300).stdout
    for row in csv.reader(io.StringIO(out)):
        if len(row) >= 6 and row[2] == "Match":
            lon, lat = map(float, row[5].split(","))
            G[need[int(row[0])]] = [lat, lon]
        elif row:
            G.setdefault(need[int(row[0])], None)
    json.dump(G, open(GC, "w"))
cent = collections.defaultdict(list)
for r in rows:
    if not r.get("lat") and G.get(r["addr"]): r["lat"], r["lon"] = G[r["addr"]]
    if r.get("lat"): cent[r["city"]].append((r["lat"], r["lon"]))
for r in rows:
    if not r.get("lat") and cent.get(r["city"]):
        v = cent[r["city"]]; r["lat"], r["lon"] = sum(x for x, _ in v) / len(v), sum(y for _, y in v) / len(v); r["approx"] = True
    if r.get("lat"): r["lat"], r["lon"] = round(r["lat"], 5), round(r["lon"], 5)
# stage: how close to open
for r in rows:
    if r["pstage"] in ("Final inspection", "Under construction"):
        r["stage"] = "Opening soon"
    elif r["issued"] and r["issued"] >= NEW:
        r["stage"] = "Newly licensed"
    elif r["issued"]:
        r["stage"] = "Licensed"
    else:
        r["stage"] = "Built out, not on the state list"
    r["latest"] = max(r["issued"], r["pdate"])
json.dump({"pulled": TODAY.isoformat(), "ocm_file": XL.name, "rows": rows}, open(PRIV / "rows.json", "w"))
print("rows", len(rows), collections.Counter(r["stage"] for r in rows), collections.Counter(r["kind"] for r in rows))
print("no location", sum(not r.get("lat") for r in rows), "approx", sum(bool(r.get("approx")) for r in rows), "with email", sum(bool(r["email"]) for r in rows), "permits", len(perm), "joined", len(used))
