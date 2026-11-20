"""Put region walks into the app (20 Nov 2026). Reads data/regions/<r>/allwalks.json for each region named and adds its walks
to the w8walks block in app/src/main/assets/index.html. Walks already in the app stay as they are; a region walk whose car park
is within 300 m of one already in the app is skipped (same walk). Re-running replaces that region's walks.
Usage (repo root): python3 tools/walkdata/inject.py aberdeen [london ...]"""
import json, math, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = f"{ROOT}/app/src/main/assets/index.html"
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
data["walks"] = W
s = s[:mm.start(2)] + json.dumps(data, separators=(",", ":")) + s[mm.end(2):]
open(P, "w").write(s)
print(len(W), "walks in the app,", round(len(s) / 1e6, 1), "MB index.html")
