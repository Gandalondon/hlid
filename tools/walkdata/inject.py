"""Put region walks into the app (20 Nov 2026).
The app (app/src/main/assets/index.html, block w8walks) holds only the list: id, name and meta (car park, km, climb, score,
busy) for every walk. Each walk's map is its own file, walks/<id>.json at the repo root, which the app fetches from GitHub the
first time the walk is picked and keeps on the phone. Test walks (meta.source "test walk") stay built in so the app always opens.

Usage (repo root): python3 tools/walkdata/inject.py [region ...]
  Adds data/regions/<r>/allwalks.json for each region named (re-running replaces that region's walks). A walk whose car park is
  within 300 m of one already in the app is skipped (same walk). With no regions it just moves any built-in maps out to walks/."""
import json, math, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = f"{ROOT}/app/src/main/assets/index.html"; WD = f"{ROOT}/walks"; os.makedirs(WD, exist_ok=True)
def m(a, b): return math.hypot((a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])), (a[0] - b[0]) * 111200)
s = open(P).read()
pat = re.compile(r'(<script type="application/json" id="w8walks">)(.*?)(</script>)', re.S)
mm = pat.search(s); data = json.loads(mm.group(2)); W = data["walks"]
for r in sys.argv[1:]:
    W = [w for w in W if w.get("meta", {}).get("region") != r]
    new = json.load(open(f"{ROOT}/data/regions/{r}/allwalks.json"))["walks"]; add = skip = 0
    for w in new:
        if any(m(w["meta"]["car_park"], o["meta"]["car_park"]) < 300 for o in W): skip += 1; continue
        W.append(w); add += 1
    print(r, "added", add, "skipped (already in the app)", skip)
moved = 0
for i, w in enumerate(W):
    if w.get("meta", {}).get("source") == "test walk" or "loop" not in w: continue
    json.dump(w, open(f"{WD}/{w['id']}.json", "w"), separators=(",", ":"))
    W[i] = {"id": w["id"], "name": w["name"], "meta": w["meta"]}; moved += 1
data["walks"] = W
s = s[:mm.start(2)] + json.dumps(data, separators=(",", ":")) + s[mm.end(2):]
open(P, "w").write(s)
print(len(W), "walks in the app,", moved, "maps moved to walks/,", len(os.listdir(WD)), "map files,", round(len(s) / 1e6, 1), "MB index.html")
