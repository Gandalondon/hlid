"""Put region walks into the app (20 Nov 2026).
The app (app/src/main/assets/index.html, block w8walks) holds only the list: id, name and meta (car park, km, climb, score,
busy) for every walk. Each walk's map is its own file, <region folder>/<id>.json in the Gandalondon/hlid-walks repo, which the app fetches from GitHub the
first time the walk is picked and keeps on the phone. Test walks (meta.source "test walk") stay built in so the app always opens.

Usage (repo root): python3 tools/walkdata/inject.py [region ...]
  Adds data/regions/<r>/allwalks.json for each region named (re-running replaces that region's walks). A walk whose car park is
  within 300 m of one already in the app is skipped (same walk). With no regions it just moves any built-in maps out to walks/."""
import json, math, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = f"{ROOT}/app/src/main/assets/index.html"
WD = os.environ.get("HLID_WALKS", os.path.join(os.path.dirname(ROOT), "hlid-walks"))   # the Gandalondon/hlid-walks clone
# folder per region in hlid-walks (the London rings get readable names); the app reads meta.dir
DIRS = {"london": "london-inner", "ring60": "london-1h", "ring90": "london-1h30", "ring120": "london-2h", None: "south-east"}
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
    if w.get("meta", {}).get("source") != "test walk" and "loop" not in w and not w["meta"].get("dir"):   # moved out by an earlier run
        w2 = json.load(open(f"{ROOT}/walks/{w['id']}.json")); w2["meta"] = w["meta"]; W[i] = w = w2
    if w.get("meta", {}).get("source") == "test walk" or "loop" not in w: continue
    d = DIRS.get(w["meta"].get("region"), w["meta"].get("region")); w["meta"]["dir"] = d; os.makedirs(f"{WD}/{d}", exist_ok=True)
    json.dump(w, open(f"{WD}/{d}/{w['id']}.json", "w"), separators=(",", ":"))
    W[i] = {"id": w["id"], "name": w["name"], "meta": w["meta"]}; moved += 1
data["walks"] = W
s = s[:mm.start(2)] + json.dumps(data, separators=(",", ":")) + s[mm.end(2):]
open(P, "w").write(s)
print(len(W), "walks in the app,", moved, "maps written to", WD, round(len(s) / 1e6, 1), "MB index.html")
