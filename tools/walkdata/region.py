"""Hlid walk data for any region (20 Nov 2026). Same gates and scoring as the south-east pass (shortlist.py, sw_routes.py,
sw_parks.py, sw_loops.py, sw_merge.py, name_loops.py, loop_honeypot.py, build_all.py), driven by a region file instead of
hard-coded counties. Personal vetoes only apply where the region file names one (Tony's are SW London only).

Region file: data/regions/<r>.json  {"id","label","prefix","home":[lon,lat],"box":[s,w,n,e],"pbf":"<file in data/gb>",
  "straight_km":[min,max] (car park loops), "route_km":max straight km for OSM routes, "drive_max":minutes, "veto":null|"veto-x.json"}
Outputs in data/regions/<r>/: foot.json, named.json, walks.json (ranked, like sw-walks-v3), maps/<id>.json, allwalks.json, log.txt

Steps, from ~/Hlid (each step is resumable; long ones run under nohup):
  python3 tools/walkdata/region.py extract <r>     OSM -> foot.json + named.json (ways, car parks, pois, walking routes)
  python3 tools/walkdata/region.py routes <r>      OSM circular walking routes -> routes.json (shortlist + checks)
  python3 tools/walkdata/region.py parks <r>       free car parks worth a loop -> parks.json
  python3 tools/walkdata/region.py loops <r>       footpath loops round them -> loops.json
  python3 tools/walkdata/region.py merge <r>       OSRM drive times from home, one score, names, busy tiers -> walks.json
  python3 tools/walkdata/region.py areas <r>       map extracts per walk -> data/areas/<id>.json, OS Terrain 50 tiles
  python3 tools/walkdata/region.py build <r>       build8 maps -> maps/<id>.json
  python3 tools/walkdata/region.py pack <r>        quality gate (length within 30%, under 2% off a foot way) -> allwalks.json
  python3 tools/walkdata/region.py all <r>         everything above in order"""
import json, os, sys, math, re, time, io, zipfile, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE)); G = f"{ROOT}/data/gb"
sys.path.insert(0, f"{ROOT}/engine")

def cfg(r):
    C = json.load(open(f"{ROOT}/data/regions/{r}.json")); D = f"{ROOT}/data/regions/{r}"
    os.makedirs(f"{D}/maps", exist_ok=True); return C, D
def srcpbf(C, r):   # the region's own extract if the workflow made one, else the whole of GB
    for f in (C.get("pbf"), f"{r}.osm.pbf", "great-britain-latest.osm.pbf"):
        if f and os.path.exists(f"{G}/{f}"): return f"{G}/{f}"
    raise SystemExit("no OSM file in data/gb")
def log(D, *a):
    s = time.strftime("%Y-%m-%d %H:%M ") + " ".join(str(x) for x in a); print(s, flush=True)
    open(f"{D}/log.txt", "a").write(s + "\n")
def m(a, b):  # metres between (lon,lat) points
    kx = 111320 * math.cos(math.radians((a[1] + b[1]) / 2)); return math.hypot((a[0] - b[0]) * kx, (a[1] - b[1]) * 111200)
def inbox(B, lon, lat): return B[0] <= lat <= B[2] and B[1] <= lon <= B[3]
def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]
BIG = {"motorway", "trunk", "primary", "secondary", "tertiary", "trunk_link", "primary_link"}

# ---------- extract ----------
def extract(r):
    import osmium; from build8 import is_foot
    C, D = cfg(r); B = C["box"]; pbf = srcpbf(C, r); t0 = time.time()
    KEYS = ("highway", "designation", "foot", "access", "informal", "footway", "name", "fee", "operator", "capacity", "amenity", "parking",
            "tourism", "information", "leisure", "route", "type", "network", "surface", "tracktype", "ref", "prow_ref", "sac_scale")
    # pass 1: walking route relations and their member ways (relations come last in the file, so they need their own pass)
    rels = []; need = set()
    class R(osmium.SimpleHandler):
        def relation(self, rr):
            if rr.tags.get("route") in ("hiking", "foot", "walking"):
                mm = [["w", x.ref, x.role] for x in rr.members if x.type == "w"]
                rels.append({"id": rr.id, "t": {"route": rr.tags.get("route"), "name": rr.tags.get("name", ""), "roundtrip": rr.tags.get("roundtrip", ""),
                             "fee": rr.tags.get("fee", "")}, "m": mm}); need.update(x[1] for x in mm)
    R().apply_file(pbf, locations=False); log(D, "extract: pass 1", len(rels), "walking routes", round(time.time() - t0), "s")
    ways = {}; parks = []; pois = []; named = []
    def kind(t):
        n = t.get("natural")
        if n in ("peak", "hill", "wood", "heath", "ridge", "valley", "scrub", "grassland", "moor"): return "heath" if n == "moor" else n
        if t.get("landuse") == "forest": return "wood"
        if t.get("leisure") == "nature_reserve": return "reserve"
        if t.get("leisure") == "common" or t.get("designation") == "common": return "common"
        if t.get("place") in ("village", "hamlet", "locality", "isolated_dwelling"): return t.get("place")
        if t.get("historic") == "hillfort" or t.get("archaeological_site") == "hillfort": return "hillfort"
        return None
    class H(osmium.SimpleHandler):
        def node(self, n):
            l = n.location
            if not l.valid() or not inbox(B, l.lon, l.lat): return
            t = n.tags; a = t.get("amenity")
            if a == "parking" or a in ("cafe", "ice_cream", "toilets", "restaurant") or t.get("information") == "visitor_centre" or t.get("leisure") == "playground":
                d = {k: v for k, v in t if k in KEYS}; (parks if a == "parking" else pois).append([round(l.lon, 6), round(l.lat, 6), d])
            nm = t.get("name")
            if nm:
                k = kind(dict(t))
                if k: named.append([round(l.lon, 6), round(l.lat, 6), k, nm, 0])
        def way(self, w):
            try: ps = [(nn.lon, nn.lat) for nn in w.nodes]
            except Exception: return
            if not any(inbox(B, x, y) for x, y in ps[::max(1, len(ps) // 8)] + ps[-1:]): return
            t = {k: v for k, v in w.tags if k in KEYS}; full = dict(w.tags)
            nm = full.get("name"); k = kind(full)
            if nm and k and len(ps) > 2:
                xs = [p[0] for p in ps]; ys = [p[1] for p in ps]
                named.append([round(sum(xs) / len(xs), 6), round(sum(ys) / len(ys), 6), k, nm, round((max(xs) - min(xs)) * 69000 * (max(ys) - min(ys)) * 111000)])
            if t.get("amenity") == "parking" or t.get("amenity") in ("cafe", "ice_cream", "toilets", "restaurant") or t.get("leisure") == "playground" or t.get("information") == "visitor_centre":
                cx = sum(p[0] for p in ps) / len(ps); cy = sum(p[1] for p in ps) / len(ps)
                (parks if t.get("amenity") == "parking" else pois).append([round(cx, 6), round(cy, 6), t]); return
            foot = is_foot(t); big = t.get("highway") in BIG
            if not (foot or big or w.id in need): return
            ways[w.id] = {"t": t if (foot or w.id in need) else {"highway": t["highway"]}, "nd": [nn.ref for nn in w.nodes], "p": [[round(x, 6), round(y, 6)] for x, y in ps]}
    idx = f"sparse_file_array,/tmp/hlid-{r}-nodes.idx"
    H().apply_file(pbf, locations=True, idx=idx)
    try: os.remove(f"/tmp/hlid-{r}-nodes.idx")
    except OSError: pass
    rels = [x for x in rels if any(str(y[1]) in ways or y[1] in ways for y in x["m"])]
    ways = {str(k): v for k, v in ways.items()}
    json.dump({"ways": ways, "parks": parks, "pois": pois, "rels": rels}, open(f"{D}/foot.json", "w"), separators=(",", ":"))
    json.dump(named, open(f"{D}/named.json", "w"))
    log(D, "extract:", len(ways), "ways", len(parks), "car parks", len(pois), "pois", len(rels), "routes", len(named), "named places", round(time.time() - t0), "s")

def load_foot(D): return json.load(open(f"{D}/foot.json"))

# ---------- shared checks (from sw_routes.py / loop_honeypot.py, minus the SE name lists) ----------
def honeypot_start(F, p, park):
    sig = []
    near = [t for x, y, t in F["pois"] if abs(x - p[0]) < 0.008 and abs(y - p[1]) < 0.004 and m((x, y), p) < 350]
    kinds = sorted({t.get("amenity") or t.get("leisure") or t.get("information") for t in near} - {None})
    if any(k in kinds for k in ("cafe", "ice_cream", "visitor_centre", "playground", "restaurant")): sig.append("at the car park: " + ", ".join(kinds))
    cap = (park or {}).get("capacity", "")
    if cap.isdigit() and int(cap) >= 80: sig.append(f"big car park ({cap} spaces)")
    return sig
PAID = re.compile(r"national trust|forestry|english heritage|country park|rspb|forest and land scotland|nts\b|historic environment scotland", re.I)
def veto_list(C):
    if not C.get("veto"): return []
    return json.load(open(f"{G}/{C['veto']}"))["veto"]

# ---------- routes (shortlist.py + sw_routes.py) ----------
def routes(r):
    import pick; from build8 import is_foot
    C, D = cfg(r); F = load_foot(D); W = F["ways"]; home = tuple(C["home"])
    BAD = re.compile(r"play|butterfly|lizard|bluebell|sensory|access|buggy|family|children|kids|trail for|train|station|town|heritage|history|past and present|tree trail|nature trail|easy|short|wheelchair|dog", re.I)
    def free(fee): fee = (fee or "").lower().strip(); return fee in ("", "no", "free", "donation") or fee.startswith(("no", "free"))
    PK = [(x, y, t) for x, y, t in F["parks"] if free(t.get("fee")) and t.get("access") not in ("private", "customers", "no", "permit")]
    out = []; why = {}
    for rel in F["rels"]:
        mem = [W[str(ref)] for typ, ref, role in rel["m"] if str(ref) in W and role in ("", "main", "forward", "backward")]
        if not mem: why["no ways"] = why.get("no ways", 0) + 1; continue
        L = sum(m(a, b) for w in mem for a, b in zip(w["p"], w["p"][1:])) / 1000
        # circular: every member-way end is shared by an even number of ways (two loose ends allowed if within 300 m)
        ends = {}
        for w in mem:
            for nd, p in ((w["nd"][0], w["p"][0]), (w["nd"][-1], w["p"][-1])): ends.setdefault(nd, [0, p]); ends[nd][0] += 1
        odd = [p for c, p in ends.values() if c % 2]
        circ = rel["t"].get("roundtrip") != "no" and (not odd or (len(odd) == 2 and m(odd[0], odd[1]) < 300))
        pts = [tuple(p) for w in mem for p in w["p"]]
        c0 = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        reason = None
        if not circ: reason = "not a loop"
        elif m(c0, home) / 1000 > C["route_km"]: reason = "too far"
        elif m(c0, home) / 1000 < C.get("route_km_min", 0): reason = "too near (inner ring)"
        elif L < 4: reason = "too short"
        elif L > 16: reason = "too long"
        elif BAD.search(rel["t"]["name"] or ""): reason = "not a country walk (name)"
        if reason: why[reason] = why.get(reason, 0) + 1; continue
        s = pts[::4]; best = None
        for x, y, t in PK:
            if abs(y - c0[1]) > 0.15 or abs(x - c0[0]) > 0.3: continue
            d = min(m((x, y), p) for p in s)
            if d < 400 and (best is None or d < best[0]): best = (d, (x, y), t)
        if not best: why["no free car park within 400 m"] = why.get("no free car park within 400 m", 0) + 1; continue
        up = 0
        for w in mem:
            e = [pick.elevation(p[1], p[0]) for p in w["p"][::2]]
            up += sum(max(0, b - a) for a, b in zip(e, e[1:]) if a is not None and b is not None)
        climb = up  # loop: up = down
        els = [pick.elevation(p[1], p[0]) for p in pts[::5]]; top = max([x for x in els if x is not None] or [0])
        if climb < 60: why["too flat"] = why.get("too flat", 0) + 1; continue
        foot = road = 0.0; roads = {}
        for w in mem:
            Lw = sum(m(a, b) for a, b in zip(w["p"], w["p"][1:]))
            if is_foot(w["t"]): foot += Lw
            else: road += Lw; k = w["t"].get("name") or w["t"].get("highway") or "untagged"; roads[k] = roads.get(k, 0) + Lw
        park = best[2]; fee = (park.get("fee") or "unknown").lower(); op = park.get("operator", "")
        feecheck = "free" if fee in ("no", "free") else ("probably paid (" + op + ")" if PAID.search(op + " " + (park.get("name") or "")) else ("paid" if fee == "yes" else "unknown"))
        cp = best[1]; hp = honeypot_start(F, cp, park)
        drop = []
        if road > 1000: drop.append(f"{road / 1000:.1f} km on roads")
        if feecheck.startswith(("paid", "probably")): drop.append("car park " + feecheck)
        out.append(dict(source="osm route", id=rel["id"], name=rel["t"]["name"] or "Unnamed walk", km=round(L, 1), climb=round(climb), top_m=round(top),
                        walk_min=round(L / 5 * 60 + climb / 10), car_park=[cp[1], cp[0]], car_park_name=park.get("name"), car_park_check=feecheck,
                        car_park_operator=op, foot_m=round(foot), road_m=round(road), honeypot=hp, keep=not drop, drop=drop,
                        roads={k: round(v) for k, v in sorted(roads.items(), key=lambda x: -x[1])[:4]}))
    json.dump(out, open(f"{D}/routes.json", "w"), indent=1)
    log(D, "routes:", len(F["rels"]), "relations ->", len(out), "checked,", sum(w["keep"] for w in out), "kept; out:", why,
        "; dropped:", {d: sum(1 for w in out if d in "; ".join(w["drop"])) for d in ("roads", "car park")})

# ---------- parks (sw_parks.py) ----------
def parks(r):
    import pick
    C, D = cfg(r); F = load_foot(D); home = tuple(C["home"]); lo, hi = C["straight_km"]
    bad = [(x, y) for x, y, t in F["pois"] if (t.get("amenity") in ("cafe", "ice_cream", "restaurant") or t.get("information") == "visitor_centre" or t.get("leisure") == "playground")]
    grid = {}
    for w in F["ways"].values():
        if w["t"].get("highway") in BIG and "designation" not in w["t"]: continue
        for x, y in w["p"][::3]: k = (round(x * 50), round(y * 80)); grid[k] = grid.get(k, 0) + 1
    Cs = []; why = {}
    for x, y, t in F["parks"]:
        def no(k): why[k] = why.get(k, 0) + 1
        if (t.get("fee") or "").lower() not in ("no", "free"): no("fee not no"); continue
        if t.get("access") in ("private", "customers", "no", "permit", "permissive_no") or t.get("parking") in ("street_side", "lane", "on_street"): no("access"); continue
        d = m((x, y), home) / 1000
        if not lo <= d <= hi: no("distance"); continue
        if re.search(r"pub|inn\b|arms|hotel|hall|school|church|station|mcdonald|tesco|sainsbury|asda|co-op|garden centre|horse|hounds|customers|golf|caravan|distillery|castle", (t.get("name", "") + " " + t.get("operator", "")), re.I): no("customers only"); continue
        if any(abs(bx - x) < 0.008 and abs(by - y) < 0.004 and m((bx, by), (x, y)) < 350 for bx, by in bad): no("honeypot at start"); continue
        h0 = pick.elevation(y, x)
        if h0 is None: no("no height"); continue
        ring = [pick.elevation(y + rr / 111.2 * math.sin(a), x + rr / (111.32 * math.cos(math.radians(y))) * math.cos(a)) for rr in (0.5, 1, 1.5, 2) for a in [i * math.pi / 6 for i in range(12)]]
        ring = [v for v in ring if v is not None]; top = max(ring); rel = top - h0
        if rel < 70 and h0 < 150: no("too flat"); continue
        dens = sum(grid.get((round(x * 50) + i, round(y * 80) + j), 0) for i in (-1, 0, 1) for j in (-1, 0, 1))
        if dens < 60: no("thin path network"); continue
        Cs.append(dict(lon=x, lat=y, name=t.get("name"), operator=t.get("operator", ""), capacity=t.get("capacity", ""), straight_km=round(d, 1), h=round(h0),
                       top=round(top), relief=round(rel), foot_density=dens, score=round(min(rel, 200) / 2 + min(dens, 400) / 8 + min(h0, 200) / 10, 1)))
    Cs.sort(key=lambda c: -c["score"]); out = []
    for c in Cs:
        if all(m((c["lon"], c["lat"]), (o["lon"], o["lat"])) > 2000 for o in out): out.append(c)
    json.dump(out, open(f"{D}/parks.json", "w"), indent=1)
    log(D, "parks:", len(F["parks"]), "car parks ->", len(Cs), "pass ->", len(out), "after 2 km spacing; out:", why)

# ---------- loops (sw_loops.py) ----------
def loops(r):
    import networkx as nx, build8, pick
    C, D = cfg(r); P = json.load(open(f"{D}/parks.json")); OUT = f"{D}/loops.json"
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    F = load_foot(D); GRID = {}
    for k, w in F["ways"].items():   # 0.05 x 0.1 degree cells, so each car park only scans the ways near it
        for p in w["p"][::4] + w["p"][-1:]: GRID.setdefault((int(p[1] // 0.05), int(p[0] // 0.1)), set()).add(k)
    for i, c in enumerate(P):
        key = f"{c['lat']:.5f},{c['lon']:.5f}"
        if key in res: continue
        lat0, lon0 = c["lat"], c["lon"]; KX = 111320 * math.cos(math.radians(lat0)); KY = 111200
        def mm(p): return ((p[0] - lon0) * KX, (p[1] - lat0) * KY)
        box = 0.05
        near = set().union(*[GRID.get((int(lat0 // 0.05) + a, int(lon0 // 0.1) + b), set()) for a in (-2, -1, 0, 1, 2) for b in (-2, -1, 0, 1, 2)])
        ways = {k: F["ways"][k] for k in near if any(abs(p[0] - lon0) < box * 1.9 and abs(p[1] - lat0) < box for p in F["ways"][k]["p"][::4] + F["ways"][k]["p"][-1:])}
        A = {"ways": ways, "rels": F["rels"]}; Gr = nx.Graph(); pos = {}
        for wid, w in ways.items():
            if not build8.is_foot(w["t"]): continue
            for (na, pa), (nb, pb) in zip(zip(w["nd"], w["p"]), list(zip(w["nd"], w["p"]))[1:]):
                pos[na] = mm(pa); pos[nb] = mm(pb); Gr.add_edge(na, nb, w=math.dist(mm(pa), mm(pb)), way=wid)
        Wd = {"km": (6, 11), "prefer": [x["id"] for x in F["rels"]]}
        try: nodes, info = build8.carpark_loop(Gr, pos, A, Wd, mm)
        except Exception as e:
            res[key] = dict(c, ok=False, why=f"no loop ({type(e).__name__})"); json.dump(res, open(OUT, "w")); print(i, "no loop", c.get("name"), flush=True); continue
        gap = math.hypot(*pos[nodes[0]])
        pts = [(lon0 + pos[n][0] / KX, lat0 + pos[n][1] / KY) for n in nodes] + [(lon0 + pos[nodes[0]][0] / KX, lat0 + pos[nodes[0]][1] / KY)]
        L = sum(math.dist(pos[u], pos[v]) for u, v in zip(nodes, nodes[1:] + nodes[:1]))
        hs = []; acc = 0; last = None
        for j, (u, v) in enumerate(zip(nodes, nodes[1:] + nodes[:1])):
            acc += math.dist(pos[u], pos[v])
            if last is None or acc - last >= 50: last = acc; p = pts[j]; hs.append(pick.elevation(p[1], p[0]))
        hs = [h for h in hs if h is not None]; sm = [sum(hs[max(0, j - 2):j + 3]) / len(hs[max(0, j - 2):j + 3]) for j in range(len(hs))]
        climb = sum(max(0, y - x) for x, y in zip(sm, sm[1:]))
        rep = float(info.split("repeated ")[1].split(" m")[0]); wm = float(info.split("waymarked ")[1].split("%")[0]) / 100
        ok = gap <= 150 and rep <= 0.12 * L
        res[key] = dict(c, ok=ok, why="" if ok else (f"car park {gap:.0f} m from the nearest path" if gap > 150 else f"{rep:.0f} m walked twice"),
                        km=round(L / 1000, 1), climb=round(climb), top_m=round(max(hs)) if hs else None, repeat_m=round(rep), waymarked=round(wm, 2),
                        walk_min=round(L / 1000 / 5 * 60 + climb / 10), gap_m=round(gap), loop=" ".join(f"{x:.5f},{y:.5f}" for x, y in pts))
        print(i, ("ok " if ok else "-- ") + f"{L / 1000:.1f} km +{climb:.0f} m rep {rep:.0f} wm {wm:.0%} gap {gap:.0f}", c.get("name") or "", flush=True)
        json.dump(res, open(OUT, "w"))
    log(D, "loops:", len(res), "car parks tried,", sum(v.get("ok", False) for v in res.values()), "ok")

# ---------- merge (sw_merge.py + name_loops.py + loop_honeypot.py) ----------
def osrm(home, pts):
    out = []
    for i in range(0, len(pts), 90):
        ch = pts[i:i + 90]
        u = "https://router.project-osrm.org/table/v1/driving/" + ";".join(f"{x:.5f},{y:.5f}" for x, y in [home] + ch) + "?sources=0"
        for k in range(3):
            try: d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Hlid/0.1 (hello@gethlid.app)"}), timeout=60))["durations"][0][1:]; break
            except Exception: time.sleep(5 * (k + 1)); d = [None] * len(ch)
        out += [round(x / 60) if x else None for x in d]; time.sleep(1)
    return out
def score(km, climb, dm, wm, road_share, honey, free, drive=True):
    s = min(climb, 350) / 350 * 35
    if not drive: dm = 60   # regions away from Tony's home: the drive from the region's centre means nothing, so every walk gets the same drive points
    s += 20 if 6 <= km <= 11 else (12 if 4.5 <= km <= 13 else 4)
    s += 20 if dm and 45 <= dm <= 90 else (10 if dm and 30 <= dm <= 110 else 0)
    s += 10 * wm
    s -= 30 * road_share
    s -= 15 * len(honey) + (25 if any("known busy" in h for h in honey) else 0)
    s += 5 if free else 0
    return round(s, 1)
def merge(r):
    C, D = cfg(r); home = tuple(C["home"]); F = load_foot(D)
    R = [w for w in json.load(open(f"{D}/routes.json")) if w["keep"]]
    L = [v for v in json.load(open(f"{D}/loops.json")).values() if v.get("ok") and v["climb"] >= 100]
    dr = osrm(home, [(w["car_park"][1], w["car_park"][0]) for w in R]); dl = osrm(home, [(v["lon"], v["lat"]) for v in L])
    out = []; far = 0
    for w, dm in zip(R, dr):
        if dm is None or dm > C["drive_max"] or dm < C.get("drive_min", 0): far += 1; continue
        rs = w["road_m"] / max(1, w["foot_m"] + w["road_m"])
        out.append(dict(source="osm route", name=w["name"], km=w["km"], climb=w["climb"], top_m=w["top_m"], walk_min=w["walk_min"], drive_min=dm,
                        car_park=w["car_park"], car_park_check=w["car_park_check"], road_m=w["road_m"], waymarked=1.0, honeypot=w["honeypot"], osm_relation=w["id"],
                        score=score(w["km"], w["climb"], dm, 1.0, rs, w["honeypot"], w["car_park_check"] == "free", C.get("score_drive", True))))
    for v, dm in zip(L, dl):
        if dm is None or dm > C["drive_max"] or dm < C.get("drive_min", 0): far += 1; continue
        out.append(dict(source="car park loop", name=v.get("name") or f"Free car park near {C['label']}", km=v["km"], climb=v["climb"], top_m=v["top_m"],
                        walk_min=v["walk_min"], drive_min=dm, car_park=[v["lat"], v["lon"]], car_park_check="free", road_m=0, waymarked=v["waymarked"], honeypot=[],
                        repeat_m=v["repeat_m"], loop=v["loop"], score=score(v["km"], v["climb"], dm, v["waymarked"], 0, [], True, C.get("score_drive", True))))
    # same car park twice (route + loop): keep the higher score
    out.sort(key=lambda w: -w["score"]); ded = []
    for w in out:
        if all(m((w["car_park"][1], w["car_park"][0]), (o["car_park"][1], o["car_park"][0])) > 300 for o in ded): ded.append(w)
    out = ded
    # names (name_loops.py)
    NF = json.load(open(f"{D}/named.json"))
    PRI = {"peak": 0, "hill": 0, "hillfort": 0, "ridge": 1, "common": 1, "heath": 1, "reserve": 2, "wood": 3, "valley": 4, "grassland": 4, "scrub": 5, "locality": 5, "hamlet": 6, "village": 7, "isolated_dwelling": 8}
    def geo(w):
        if "loop" in w: return [tuple(map(float, p.split(","))) for p in w["loop"].split()]
        rel = [x for x in F["rels"] if x["id"] == w["osm_relation"]][0]
        return [tuple(p) for typ, ref, role in rel["m"] if str(ref) in F["ways"] for p in F["ways"][str(ref)]["p"]]
    for w in out:
        pts = geo(w)[::3] or [(w["car_park"][1], w["car_park"][0])]
        if w["source"] == "car park loop":
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; bb = (min(xs) - .01, max(xs) + .01, min(ys) - .01, max(ys) + .01); near = {}
            for x, y, k, nm, size in NF:
                if k not in PRI or not (bb[0] < x < bb[1] and bb[2] < y < bb[3]): continue
                dd = min(m((x, y), p) for p in pts)
                lim = 150 if k in ("hamlet", "village", "isolated_dwelling", "locality") else (300 if size == 0 else 600)
                if dd <= lim and (nm.lower() not in near or near[nm.lower()][0] > PRI[k]): near[nm.lower()] = (PRI[k], -size, round(dd), k, nm)
            c = sorted(near.values())
            w["name_auto"] = c[0][4] if c else w["name"]; w["name_why"] = "; ".join(f"{n} ({k}, {mm} m)" for _, _, mm, k, n in c[:6]) or "nothing named nearby"
        else:
            w["name_auto"] = re.split(r",| at | walk", w["name"], flags=re.I)[0].strip() or w["name"]
        # whole-loop honeypot and busy tier (loop_honeypot.py, 15 Nov rules)
        def cap(t):
            try: return int(t.get("capacity", "0"))
            except Exception: return 0
        hpl = []; pp = pts[::2] or pts
        xs = [p[0] for p in pp]; ys = [p[1] for p in pp]; bb = (min(xs) - .01, max(xs) + .01, min(ys) - .01, max(ys) + .01)
        for x, y, t in F["pois"]:
            if not (bb[0] < x < bb[1] and bb[2] < y < bb[3]): continue
            dd = min(m((x, y), p) for p in pp)
            if dd > 150: continue
            if t.get("information") == "visitor_centre":
                hk = any(cap(t2) >= 200 and m((x, y), (x2, y2)) < 300 for x2, y2, t2 in F["parks"])
                hpl.append(f"visitor centre {t.get('name', '')} {round(dd)} m" + (", by a 200+ car park" if hk else ""))
            elif t.get("amenity") in ("cafe", "ice_cream"):
                if any((cap(t2) >= 80 or "national trust" in t2.get("operator", "").lower()) and m((x, y), (x2, y2)) < 300 for x2, y2, t2 in F["parks"]):
                    hpl.append(f"{t.get('name', 'cafe')} {round(dd)} m, by a big car park")
        w["honeypot_loop"] = hpl; w["busy"] = "always" if any("200+" in x for x in hpl) else ("busy_days" if hpl else "none")
    V = veto_list(C)
    for w in out:
        if V and any(v in ((w.get("name_auto") or "") + " " + w["name"]).lower() for v in V): w["dropped"] = "personal veto"
    for i, w in enumerate(out): w["rank"] = i + 1; w["region"] = r
    json.dump(out, open(f"{D}/walks.json", "w"), indent=1)
    log(D, "merge:", len(out), "walks (", sum(w["source"] == "osm route" for w in out), "routes,", sum(w["source"] == "car park loop" for w in out),
        "car park loops ),", far, "over", C["drive_max"], "min drive (or under drive_min); busy:", {k: sum(w["busy"] == k for w in out) for k in ("always", "busy_days", "none")})

# ---------- areas + terrain (extract_areas.py + build_all.py prep) ----------
def wid(C, w): return slug(f"{C['prefix']}-{w['rank']}-{w.get('name_auto') or w['name']}")
def walks_ok(C, D):
    return [w for w in json.load(open(f"{D}/walks.json")) if not w.get("dropped") and w.get("busy") != "always"]
def areas(r):
    import osmium, pick
    C, D = cfg(r); WS = walks_ok(C, D); F = load_foot(D); t0 = time.time()
    AR = {}
    for w in WS:
        if "loop" in w: pts = [tuple(map(float, p.split(","))) for p in w["loop"].split()]
        else:
            rel = [x for x in F["rels"] if x["id"] == w["osm_relation"]][0]
            pts = [tuple(p) for typ, ref, role in rel["m"] if str(ref) in F["ways"] for p in F["ways"][str(ref)]["p"]]
        lat, lon = w["car_park"]; xs = [p[0] for p in pts] + [lon]; ys = [p[1] for p in pts] + [lat]
        AR[wid(C, w)] = (min(ys) - 0.025, min(xs) - 0.04, max(ys) + 0.025, max(xs) + 0.04)
    todo = {k: v for k, v in AR.items() if not os.path.exists(f"{ROOT}/data/areas/{k}.json")}
    # terrain tiles (OS Terrain 50) for every box
    Z = zipfile.ZipFile(f"{ROOT}/data/terr50_gagg_gb.zip"); NAMES = {n.split("/")[-1][:4].upper(): n for n in Z.namelist() if n.endswith(".zip")}
    os.makedirs(f"{ROOT}/data/terr50", exist_ok=True); got = 0
    for s, w_, n, e in AR.values():
        E0, N0 = pick.TO_OS.transform(w_, s); E1, N1 = pick.TO_OS.transform(e, n)
        E0b, N0b = pick.TO_OS.transform(w_, n); E1b, N1b = pick.TO_OS.transform(e, s)
        for ee in range(int(min(E0, E0b) // 10000), int(max(E1, E1b) // 10000) + 1):
            for nn in range(int(min(N0, N1b) // 10000), int(max(N1, N0b) // 10000) + 1):
                nm = pick.tile_name(ee * 10000 + 5, nn * 10000 + 5); dst = f"{ROOT}/data/terr50/{nm}.asc"
                if os.path.exists(dst) or nm not in NAMES: continue
                zi = zipfile.ZipFile(io.BytesIO(Z.read(NAMES[nm]))); asc = [x for x in zi.namelist() if x.lower().endswith(".asc")]
                if asc: open(dst, "wb").write(zi.read(asc[0])); got += 1
    log(D, "areas:", len(AR), "walks,", len(todo), "to extract,", got, "new terrain tiles")
    if not todo: return
    KEYS = ("highway", "landuse", "natural", "leisure", "amenity", "waterway", "building", "railway", "designation", "access", "foot", "name", "fee", "parking", "route", "type",
            "surface", "sac_scale", "barrier", "prow_ref", "ref", "informal", "footway", "trail_visibility", "tracktype", "water", "wetland")
    S = min(a[0] for a in todo.values()); Wb = min(a[1] for a in todo.values()); N = max(a[2] for a in todo.values()); E = max(a[3] for a in todo.values())
    nodes = {}; nodetags = {}; pbf = srcpbf(C, r)
    class NH(osmium.SimpleHandler):
        def node(self, n):
            l = n.location
            if not l.valid(): return
            lat, lon = l.lat, l.lon
            if S <= lat <= N and Wb <= lon <= E:
                for (s, w_, nn, e) in todo.values():
                    if s <= lat <= nn and w_ <= lon <= e:
                        nodes[n.id] = (round(lon, 6), round(lat, 6))
                        if n.tags: nodetags[n.id] = {t.k: t.v for t in n.tags if t.k in KEYS}
                        break
    NH().apply_file(pbf); log(D, "areas: nodes", len(nodes), round(time.time() - t0), "s")
    ways = {}; rels = []
    class WH(osmium.SimpleHandler):
        def way(self, w):
            refs = [x.ref for x in w.nodes]
            if not any(x in nodes for x in refs[::max(1, len(refs) // 8)] + refs[-1:]): return
            tg = {t.k: t.v for t in w.tags if t.k in KEYS}
            if not tg: return
            ways[w.id] = {"t": tg, "nd": refs, "p": [nodes.get(x) for x in refs]}
        def relation(self, rr):
            tg = {t.k: t.v for t in rr.tags}
            if tg.get("type") in ("route", "multipolygon") and any(x.type == "w" and x.ref in ways for x in rr.members):
                rels.append({"id": rr.id, "t": {k: v for k, v in tg.items() if k in KEYS or k in ("route", "network", "operator")}, "m": [[x.type, x.ref, x.role] for x in rr.members]})
    WH().apply_file(pbf, locations=False)
    for k, (s, w_, n, e) in todo.items():
        def inb(p): return p and s <= p[1] <= n and w_ <= p[0] <= e
        wk = {i: v for i, v in ways.items() if any(inb(p) for p in v["p"])}
        rk = [x for x in rels if any(y[0] == "w" and y[1] in wk for y in x["m"])]
        nt = {i: v for i, v in nodetags.items() if inb(nodes[i])}
        json.dump({"box": [s, w_, n, e], "ways": wk, "rels": rk, "nodetags": {i: [nodes[i], v] for i, v in nt.items()}}, open(f"{ROOT}/data/areas/{k}.json", "w"))
    log(D, "areas: extracted", len(todo), round(time.time() - t0), "s")

# ---------- build + pack (build_all.py) ----------
def build(r):
    import build8, glob, numpy as np
    for f in glob.glob(f"{ROOT}/data/terr50/*.asc"):   # tiles written by areas() after build8 was first imported
        fh = open(f); h = {}
        for _ in range(5): k, v = fh.readline().split(); h[k] = float(v)
        key = (int(h["xllcorner"]), int(h["yllcorner"]))
        if key not in build8.TILES: build8.TILES[key] = np.loadtxt(fh)
    C, D = cfg(r); n_ok = n_fail = 0
    for w in walks_ok(C, D):
        i = wid(C, w); out = f"{D}/maps/{i}.json"
        if os.path.exists(out) or os.path.exists(out + ".fail"): continue
        lat, lon = w["car_park"]; W = {"id": i, "name": w.get("name_auto") or w["name"], "area": i, "start": (lat, lon)}
        if "loop" in w: W.update(how="pts", pts=[tuple(map(float, p.split(","))) for p in w["loop"].split()])
        else: W.update(how="rel", rel=int(w["osm_relation"]))
        check = []
        try: res = build8.build(W, check)
        except Exception as e:
            open(out + ".fail", "w").write(f"{type(e).__name__}: {e}"); n_fail += 1; print("FAIL", i, type(e).__name__, e, flush=True); continue
        line = [c for c in check if "metres off a path" in c][-1]; mm = re.search(r"metres off a path (\d+)/(\d+)", line)
        res["off_path"] = [int(mm.group(1)), int(mm.group(2))]
        json.dump(res, open(out, "w"), separators=(",", ":")); n_ok += 1; print("ok", i, round(os.path.getsize(out) / 1e3), "KB", flush=True)
    log(D, "build:", n_ok, "built,", n_fail, "failed this run")
def pack(r):
    C, D = cfg(r); keep = []; drop = []
    for w in walks_ok(C, D):
        i = wid(C, w); f = f"{D}/maps/{i}.json"
        if not os.path.exists(f):
            drop.append((i, open(f + ".fail").read()[:80] if os.path.exists(f + ".fail") else "not built")); continue
        res = json.load(open(f)); L = res["len"] / 1000; off, n = res.get("off_path", [0, 1])
        if abs(L - w["km"]) / w["km"] > 0.3 or off > 0.02 * n: drop.append((i, f"{L:.1f} km vs {w['km']}, {off} of {n} m off a path")); continue
        h = res["prof"]["h"]; climb = round(sum(max(0, b - a) for a, b in zip(h, h[1:])))
        res["meta"] = {"car_park": w["car_park"], "km": round(L, 1), "climb": climb, "walk_min": round(L / 5 * 60 + climb / 10), "busy": w.get("busy", "none"),
                       "rank": w["rank"], "score": w.get("score", 0), "source": w["source"], "region": r}
        res["name"] = w.get("name_auto") or w["name"]; keep.append(res)
    json.dump({"walks": keep}, open(f"{D}/allwalks.json", "w"), separators=(",", ":"))
    json.dump([{"id": i, "why": y} for i, y in drop], open(f"{D}/failed.json", "w"), indent=1)
    log(D, "pack:", len(keep), "kept,", len(drop), "failed the gates", round(os.path.getsize(f"{D}/allwalks.json") / 1e6, 1), "MB")
    for d in drop: log(D, "  failed", *d)

STEPS = {"extract": extract, "routes": routes, "parks": parks, "loops": loops, "merge": merge, "areas": areas, "build": build, "pack": pack}
if __name__ == "__main__":
    step, r = sys.argv[1], sys.argv[2]
    for s in (list(STEPS) if step == "all" else [step]):
        t = time.time(); STEPS[s](r); cfg(r); log(cfg(r)[1], f"step {s} done in {round(time.time() - t)} s")
