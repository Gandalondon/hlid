"""Recent rain at every Hlid walk (21 Nov 2026), for the mud check. Runs on GitHub a few times a day (.github/workflows/mud.yml)
and writes mud.json, which the app reads from the repo's weather branch. If anything here fails, the app simply has no mud note.
Sources (free, commercial use allowed, no key): Environment Agency rain gauges (England), SEPA rain gauges (Scotland).
Wales: the nearest English gauge if one is within 20 km, else nothing yet (NRW's API needs a key).
Today's forecast: Met Office DataHub (repo secret MET_OFFICE_KEY), first run of the day only.
Output: mud.json {"updated": ISO time, "walks": {walk id: [today so far, yesterday, 2 days ago, 3 days ago] in mm}}"""
import json, math, os, re, sys, time, datetime, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = sys.argv[1] if len(sys.argv) > 1 else "mud.json"
UA = {"User-Agent": "Hlid/0.1 (hello@gethlid.app)"}
def get(u, t=60):
    for k in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t))
        except Exception as e: err = e; time.sleep(3 * (k + 1))
    print("failed", u[:120], err, flush=True); return None
def km(a, b): return math.hypot((a[1] - b[1]) * 111.32 * math.cos(math.radians(a[0])), (a[0] - b[0]) * 111.2)
s = open(f"{ROOT}/app/src/main/assets/index.html").read()
W = json.loads(re.search(r'id="w8walks">(.*?)</script>', s, re.S).group(1))["walks"]
now = datetime.datetime.now(datetime.timezone.utc); day0 = now.date()
def dayidx(ts):   # 0 = today, 1 = yesterday...
    return (day0 - datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).date()).days

# England: Environment Agency flood-monitoring API
EA = []
j = get("https://environment.data.gov.uk/flood-monitoring/id/stations?parameter=rainfall&_limit=5000")
for st in (j or {}).get("items", []):
    try: EA.append((float(st["lat"]), float(st["long"]), st["notation"]))
    except Exception: pass
print(len(EA), "EA rain gauges", flush=True)
# Scotland: SEPA KiWIS, daily totals
SE = []
q = urllib.parse.urlencode({"service": "kisters", "type": "queryServices", "request": "getTimeseriesList", "datasource": "0", "format": "json",
                            "parametertype_name": "Precip", "ts_name": "Day.Total", "returnfields": "ts_id,station_latitude,station_longitude"})
j = get("https://timeseries.sepa.org.uk/KiWIS/KiWIS?" + q)
if j and len(j) > 1:
    hdr = j[0]
    for row in j[1:]:
        r = dict(zip(hdr, row))
        try: SE.append((float(r["station_latitude"]), float(r["station_longitude"]), r["ts_id"]))
        except Exception: pass
print(len(SE), "SEPA rain gauges", flush=True)

need = {}; pick = {}
for w in W:
    cp = tuple(w["meta"]["car_park"]); best = None
    for src, L in (("ea", EA), ("sepa", SE)):
        for lat, lon, sid in L:
            if abs(lat - cp[0]) > 0.25 or abs(lon - cp[1]) > 0.4: continue
            d = km(cp, (lat, lon))
            if d <= 20 and (best is None or d < best[0]): best = (d, src, sid)
    if best: pick[w["id"]] = (best[1], best[2]); need[(best[1], best[2])] = None
print(len(pick), "of", len(W), "walks have a gauge within 20 km;", len(need), "gauges to read", flush=True)

since = (now - datetime.timedelta(days=4)).strftime("%Y-%m-%dT00:00:00Z")
def read(key):
    src, sid = key; tot = [0.0, 0.0, 0.0, 0.0]; ok = False
    if src == "ea":
        j = get(f"https://environment.data.gov.uk/flood-monitoring/id/stations/{sid}/readings?since={since}&_sorted&_limit=2000", 30)
        for r in (j or {}).get("items", []):
            try:
                i = dayidx(r["dateTime"])
                if 0 <= i <= 3 and isinstance(r.get("value"), (int, float)) and r["value"] >= 0: tot[i] += r["value"]; ok = True
            except Exception: pass
    else:
        q = urllib.parse.urlencode({"service": "kisters", "type": "queryServices", "request": "getTimeseriesValues", "datasource": "0",
                                    "format": "json", "ts_id": sid, "period": "P4D"})
        j = get("https://timeseries.sepa.org.uk/KiWIS/KiWIS?" + q, 30)
        try:
            for ts, v in j[0]["data"]:
                i = dayidx(ts)
                if 0 <= i <= 3 and v is not None and v >= 0: tot[i] += float(v); ok = True
        except Exception: pass
    return key, ([round(x, 1) for x in tot] if ok else None)
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(8) as ex:   # 21 Nov: 8 at a time (one by one took 24 min)
    for key, val in ex.map(read, list(need)): need[key] = val

walks = {wid: list(need[k]) for wid, k in pick.items() if need.get(k)}
# Today's forecast rain (Met Office DataHub, Global Spot hourly, free plan: 360 calls a day). Walks are grouped into ~20 km
# cells and only the first run of the day calls the Met Office (about 150 calls); later runs reuse that forecast.
KEY = os.environ.get("MET_OFFICE_KEY", "")
fc = {}
try:
    old = json.load(urllib.request.urlopen(urllib.request.Request("https://raw.githubusercontent.com/Gandalondon/hlid/weather/mud.json", headers=UA), timeout=30))
    if old.get("fc_day") == day0.isoformat(): fc = old.get("fc", {})
except Exception: pass
if KEY and not fc:
    cells = {}
    for w in W:
        lat, lon = w["meta"]["car_park"]; cells.setdefault((round(lat * 5) / 5, round(lon * 3) / 3), []).append(w["id"])
    print(len(cells), "forecast cells", flush=True)
    def fetch(c):
        u = f"https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly?latitude={c[0]}&longitude={c[1]}&excludeParameterMetadata=true"
        try:
            j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"apikey": KEY, "accept": "application/json", **UA}), timeout=30))
            ts = j["features"][0]["properties"]["timeSeries"]
            return c, round(sum(t.get("totalPrecipAmount", 0) or 0 for t in ts if t["time"][:10] == day0.isoformat()), 1)
        except Exception as e: print("met office", c, e, flush=True); return c, None
    with ThreadPoolExecutor(4) as ex:
        for c, mm in ex.map(fetch, list(cells)):
            if mm is not None:
                for wid in cells[c]: fc[wid] = mm
    print(len(fc), "walks with today's forecast", flush=True)
for wid, mm in fc.items():   # today's slot = rain so far today or today's forecast, whichever is bigger
    if wid in walks: walks[wid][0] = max(walks[wid][0], mm)
    else: walks[wid] = [mm, 0.0, 0.0, 0.0]
json.dump({"updated": now.isoformat(timespec="minutes"), "fc_day": day0.isoformat() if fc else None, "fc": fc, "walks": walks}, open(OUT, "w"), separators=(",", ":"))
print(len(walks), "walks with recent rain written to", OUT)
