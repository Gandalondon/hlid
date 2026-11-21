"""Pubs for Hlid's end-of-walk screen (21 Nov 2026). Uncurated, like back in the day: the nearest few pubs to each walk's car
park, from OpenStreetMap, no ratings. Worked out once here, so the app needs no extra service and works offline.

  python3 tools/walkdata/pubs.py extract   GB OSM file -> data/gb/pubs.json  ([lon, lat, name] for every named amenity=pub)
  python3 tools/walkdata/pubs.py walks     every walk in the app -> data/gb/walk-pubs.json  ({walk id: [{n, lat, lon, min}, ...]})
                                           nearest 3 within 10 km of the car park, drive minutes from the public OSRM router
                                           (straight line x 1.35 at 45 km/h if it can't be reached)
tools/walkdata/inject.py then copies them into each walk's meta.pubs."""
import json, math, os, re, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); G = f"{ROOT}/data/gb"
def m(a, b): return math.hypot((a[0] - b[0]) * 111320 * math.cos(math.radians(a[1])), (a[1] - b[1]) * 111200)

if sys.argv[1] == "extract":
    import osmium
    out = []
    def ok(t): return t.get("amenity") == "pub" and t.get("name") and t.get("access") not in ("private", "no") and not re.search(r"closed|disused", t.get("name", ""), re.I)
    class H(osmium.SimpleHandler):
        def node(self, n):
            t = n.tags
            if t.get("amenity") == "pub" and ok(dict(t)): out.append([round(n.location.lon, 6), round(n.location.lat, 6), t.get("name")])
        def way(self, w):
            t = w.tags
            if t.get("amenity") != "pub" or not ok(dict(t)): return
            try: ps = [(x.lon, x.lat) for x in w.nodes]
            except Exception: return
            out.append([round(sum(p[0] for p in ps) / len(ps), 6), round(sum(p[1] for p in ps) / len(ps), 6), t.get("name")])
    t0 = time.time()
    H().apply_file(f"{G}/great-britain-latest.osm.pbf", locations=True, idx="sparse_file_array,/tmp/hlid-pubs-nodes.idx")
    try: os.remove("/tmp/hlid-pubs-nodes.idx")
    except OSError: pass
    json.dump(out, open(f"{G}/pubs.json", "w"))
    print(len(out), "pubs", round(time.time() - t0), "s")

if sys.argv[1] == "walks":
    P = json.load(open(f"{G}/pubs.json")); grid = {}
    for p in P: grid.setdefault((int(p[1] * 10), int(p[0] * 10)), []).append(p)
    s = open(f"{ROOT}/app/src/main/assets/index.html").read()
    W = json.loads(re.search(r'id="w8walks">(.*?)</script>', s, re.S).group(1))["walks"]
    OUT = f"{G}/walk-pubs.json"; res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for w in W:
        if w["id"] in res: continue
        lat, lon = w["meta"]["car_park"]; cp = (lon, lat)
        near = [p for a in range(-1, 2) for b in range(-2, 3) for p in grid.get((int(lat * 10) + a, int(lon * 10) + b), [])]
        near = sorted((p for p in near if m(cp, p) <= 10000), key=lambda p: m(cp, p))
        seen = set(); pick = []
        for p in near:   # one per name (chains and duplicates in OSM)
            if p[2].lower() in seen: continue
            seen.add(p[2].lower()); pick.append(p)
            if len(pick) == 3: break
        mins = [None] * len(pick)
        if pick:
            u = "https://router.project-osrm.org/table/v1/driving/" + ";".join(f"{x:.5f},{y:.5f}" for x, y in [cp] + [(p[0], p[1]) for p in pick]) + "?sources=0"
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Hlid/0.1 (hello@gethlid.app)"}), timeout=30))["durations"][0][1:]
                mins = [round(x / 60) if x is not None else None for x in d]
            except Exception: pass
            time.sleep(1)
        res[w["id"]] = [{"n": p[2], "lat": p[1], "lon": p[0], "min": mm if mm is not None else max(1, round(m(cp, p) * 1.35 / 750))} for p, mm in zip(pick, mins)]
        json.dump(res, open(OUT, "w"))
    print(len(res), "walks,", sum(1 for v in res.values() if v), "with a pub within 10 km")
