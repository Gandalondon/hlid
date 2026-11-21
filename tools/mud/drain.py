"""How well each walk drains (21 Nov 2026), for the mud check. 0 = stays boggy, 1 = drains fast. Worked out once per walk.
- Path surface along the loop, from OpenStreetMap tags on the ways it follows (data/areas/<id>.json): gravel, compacted, rock,
  paved and good tracks drain; grass, dirt, earth, mud and ground don't; untagged paths count as neutral.
- How hilly it is: a walk that climbs a lot per km spends more time on slopes and tops, which shed water.
(Geology, e.g. chalk vs clay, would sharpen this later: BGS open data.)
Usage (repo root): python3 tools/mud/drain.py  -> data/gb/walk-drain.json {walk id: 0..1}; inject.py copies it to meta.drain."""
import json, math, os, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WD = os.environ.get("HLID_WALKS", os.path.join(os.path.dirname(ROOT), "hlid-walks"))
GOOD = {"gravel", "fine_gravel", "compacted", "rock", "asphalt", "paved", "paving_stones", "concrete", "sett", "pebblestone", "stone", "wood", "metal"}
POOR = {"grass", "dirt", "earth", "mud", "ground", "sand", "unpaved", "woodchips"}
def kind(t):
    s = t.get("surface")
    if s in GOOD: return 1
    if s in POOR: return -1
    if t.get("highway") == "track" and t.get("tracktype") in ("grade1", "grade2"): return 1
    if t.get("highway") == "track" and t.get("tracktype") in ("grade4", "grade5"): return -1
    if t.get("highway") in ("footway", "cycleway", "pedestrian", "steps"): return 1   # mostly made paths
    return 0
s = open(f"{ROOT}/app/src/main/assets/index.html").read()
W = json.loads(re.search(r'id="w8walks">(.*?)</script>', s, re.S).group(1))["walks"]
out = {}; tagged = 0
for w in W:
    m = w["meta"]; climb_km = (m.get("climb") or 0) / max(0.5, m.get("km") or 1)
    hill = min(1.0, max(0.0, (climb_km - 15) / 60))
    surf = 0.0
    f = f"{WD}/{m.get('dir', '')}/{w['id']}.json"; a = f"{ROOT}/data/areas/{w['id']}.json"
    if "loop" in w: J = w
    elif os.path.exists(f): J = json.load(open(f))
    else: J = None
    if J and os.path.exists(a):
        A = json.load(open(a)); lat0, lon0, kx, ky = J["lat0"], J["lon0"], J["kx"], J["ky"]
        grid = {}
        for wy in A["ways"].values():
            k = kind(wy["t"])
            for p in wy["p"]:
                if p: x, y = (p[0] - lon0) * kx, (p[1] - lat0) * ky; grid.setdefault((int(x // 25), int(y // 25)), []).append((x, y, k))
        pts = J["loop"][::4]; ks = []
        for x, y in pts:
            best = None
            for i in (-1, 0, 1):
                for j in (-1, 0, 1):
                    for q in grid.get((int(x // 25) + i, int(y // 25) + j), []):
                        d = math.hypot(q[0] - x, q[1] - y)
                        if d < 25 and (best is None or d < best[0]): best = (d, q[2])
            if best: ks.append(best[1])
        if ks: surf = sum(ks) / len(ks); tagged += 1
    out[w["id"]] = round(min(0.95, max(0.05, 0.45 + 0.3 * surf + 0.3 * hill)), 2)
json.dump(out, open(f"{ROOT}/data/gb/walk-drain.json", "w"), indent=0)
v = sorted(out.values()); print(len(out), "walks,", tagged, "with path surfaces; drain min/median/max", v[0], v[len(v) // 2], v[-1])
