"""Name walks still called "Free car park near <region>" (21 Nov 2026): nothing named was close enough to the loop for the
normal rule (merge in region.py), so take the nearest named hill, peak, ridge, wood, moor, reserve or valley within 3 km of the
loop, else the nearest village, hamlet or locality within 5 km of the car park. Updates the region's walks.json and
allwalks.json, the app list and the walk's map file in hlid-walks. Run from the repo root."""
import json, math, os, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WD = os.environ.get("HLID_WALKS", os.path.join(os.path.dirname(ROOT), "hlid-walks"))
def m(a, b): return math.hypot((a[0] - b[0]) * 111320 * math.cos(math.radians(a[1])), (a[1] - b[1]) * 111200)
LAND = {"peak": 0, "hill": 0, "hillfort": 0, "ridge": 1, "heath": 1, "common": 1, "reserve": 2, "wood": 3, "valley": 4}
PLACE = {"locality": 0, "hamlet": 1, "village": 2, "isolated_dwelling": 3}
def better_name(r, w):
    NF = json.load(open(f"{ROOT}/data/regions/{r}/named.json"))
    pts = [tuple(map(float, p.split(","))) for p in w["loop"].split()][::3] if "loop" in w else []
    lat, lon = w["car_park"]; cp = (lon, lat)
    c = [(LAND[k], min(m((x, y), p) for p in pts), nm) for x, y, k, nm, size in NF if k in LAND and pts and abs(x - lon) < 0.1 and abs(y - lat) < 0.06]
    c = [x for x in c if x[1] <= 3000]
    if c: return sorted(c, key=lambda x: (x[0], x[1]))[0][2]
    c = [(m((x, y), cp), nm) for x, y, k, nm, size in NF if k in PLACE and abs(x - lon) < 0.12 and abs(y - lat) < 0.07]
    c = [x for x in c if x[0] <= 5000]
    return sorted(c)[0][1] if c else None
P = f"{ROOT}/app/src/main/assets/index.html"; s = open(P).read()
mm = re.search(r'id="w8walks">(.*?)</script>', s, re.S); data = json.loads(mm.group(1)); byid = {w["id"]: w for w in data["walks"]}
fixed = []
for f in glob.glob(f"{ROOT}/data/regions/*/walks.json"):
    r = f.split("/")[-2]; WS = json.load(open(f)); changed = False
    for w in WS:
        nm = w.get("name_auto") or w["name"]
        if not re.match(r"free car park near", nm, re.I): continue
        new = better_name(r, w)
        if not new: continue
        w["name_auto"] = new; changed = True; fixed.append((r, w["rank"], nm, new))
    if changed:
        json.dump(WS, open(f, "w"), indent=1)
        aw = f"{ROOT}/data/regions/{r}/allwalks.json"
        if os.path.exists(aw):
            A = json.load(open(aw)); ranks = {w["rank"]: (w.get("name_auto") or w["name"]) for w in WS}
            for x in A["walks"]:
                if re.match(r"free car park near", x["name"], re.I) and x["meta"]["rank"] in ranks: x["name"] = ranks[x["meta"]["rank"]]
            json.dump(A, open(aw, "w"), separators=(",", ":"))
            for x in A["walks"]:
                if x["id"] in byid and byid[x["id"]]["name"] != x["name"]:
                    byid[x["id"]]["name"] = x["name"]; d = byid[x["id"]]["meta"].get("dir")
                    fp = f"{WD}/{d}/{x['id']}.json"
                    if d and os.path.exists(fp):
                        j = json.load(open(fp)); j["name"] = x["name"]; json.dump(j, open(fp, "w"), separators=(",", ":"))
s = s[:mm.start(1)] + json.dumps(data, separators=(",", ":")) + s[mm.end(1):]; open(P, "w").write(s)
for x in fixed: print(*x)
print(len(fixed), "renamed;", sum(1 for w in data["walks"] if re.match(r"free car park", w["name"], re.I)), "still unnamed in the app")
