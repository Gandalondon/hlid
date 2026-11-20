"""Woden picker, first pass. Works anywhere in Great Britain.
Usage: python3 engine/pick.py LAT LON DRIVE_H WALK_H   (e.g. 51.405 -0.226 1 2)
Walk data: routes.py for now; the GB-wide set replaces it (docs/walk-data.md)."""
import sys, os, io, math, zipfile, functools
from pyproj import Transformer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import routes

# Windows set from Tony's real walks (14 Nov): drives 56-85 min, walks 63-88 min plus one of 169.
# Drive minutes are OSRM (no traffic). Each window is "about" the pick.
DRIVE = {1: (40, 86), 1.5: (86, 115), 2: (115, 140)}
WALK = {1: (45, 95), 2: (95, 150), 3: (150, 210), 4: (210, 300)}
TO_OS = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
Z = zipfile.ZipFile(os.path.join(ROOT, "data/terr50_gagg_gb.zip"))
NAMES = {n.split("/")[-1][:4].upper(): n for n in Z.namelist() if n.endswith(".zip")}

def tile_name(e, n):
    e100, n100 = int(e // 100000), int(n // 100000)
    l1 = (19 - n100) // 5 * 5 + (e100 + 10) // 5
    l2 = (19 - n100) * 5 % 25 + e100 % 5
    L = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    return f"{L[l1]}{L[l2]}{int(e % 100000 // 10000)}{int(n % 100000 // 10000)}"

@functools.lru_cache(maxsize=64)
def tile(name):
    if name not in NAMES: return None
    inner = zipfile.ZipFile(io.BytesIO(Z.read(NAMES[name])))
    asc = [x for x in inner.namelist() if x.endswith(".asc")][0]
    lines = inner.read(asc).decode().split("\n")
    hdr = {l.split()[0]: float(l.split()[1]) for l in lines[:5]}
    rows = [list(map(float, l.split())) for l in lines[5:] if l.strip()]
    return hdr, rows

def elevation(lat, lon):
    e, n = TO_OS.transform(lon, lat)
    t = tile(tile_name(e, n))
    if not t: return None
    h, rows = t
    c = int((e - h["xllcorner"]) // 50); r = int(len(rows) - 1 - (n - h["yllcorner"]) // 50)
    return rows[max(0, min(r, len(rows)-1))][max(0, min(c, 199))]

def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 6371 * 2 * math.asin(math.sqrt(math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))

def walk(key):
    pts = [tuple(map(float, p.split(",")))[::-1] for p in routes.LOOPS[key].split()]
    length = sum(km(pts[i], pts[i+1]) for i in range(len(pts)-1))
    els = [elevation(*p) for p in pts]
    ascent = sum(max(0, els[i+1]-els[i]) for i in range(len(els)-1) if None not in (els[i], els[i+1]))
    return {"id": key, "name": routes.META[key][0], "car_park": pts[0], "length_km": round(length, 1),
            "ascent_m": round(ascent), "top_m": round(max(e for e in els if e is not None)),
            "walk_min": round(length / 5.0 * 60 + ascent / 10)}

def drive_min(start, end):
    d = km(start, end) * 1.35
    speed = 70  # effective km/h on the road distance; rough until real routing (OSRM)
    return round(d / speed * 60)

def osrm_min(start, end):
    import subprocess, json as J
    u = f"https://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=false"
    try: return round(J.loads(subprocess.run(["curl","-s","-m","20",u],capture_output=True,text=True).stdout)["routes"][0]["duration"]/60)
    except Exception: return drive_min(start, end)

def walks():
    import json as J
    p = os.path.join(ROOT, "data/tracks/walks.json")
    if os.path.exists(p):
        return [dict(w, top_m=round(max(e for e in (elevation(*q) for q in J.load(open(os.path.join(ROOT, f"data/tracks/{w['id']}-route.json")))["points"][::10]) if e is not None))) for w in J.load(open(p))]
    return [walk(k) for k in routes.LOOPS]

def pick(lat, lon, drive_h, walk_h):
    lo, hi = DRIVE[drive_h]; wlo, whi = WALK[int(walk_h)]
    out = []
    for r in walks():
        r["drive_min"] = osrm_min((lat, lon), tuple(r["car_park"]))
        r["fits"] = lo <= r["drive_min"] < hi and wlo <= r["walk_min"] < whi
        out.append(r)
    return sorted(out, key=lambda r: (not r["fits"], -r["top_m"]))

if __name__ == "__main__":
    lat, lon, dh, wh = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    dh = int(dh) if dh == int(dh) else dh
    for r in pick(lat, lon, dh, wh):
        print(("YES " if r["fits"] else "    ") + f'{r["name"]:32} drive {r["drive_min"]:>3} min  walk {r["walk_min"]:>3} min  {r.get("km", r.get("length_km"))} km  top {r["top_m"]} m')
