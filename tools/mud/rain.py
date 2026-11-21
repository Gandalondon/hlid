"""Recent rain at every Hlid walk (21 Nov 2026), for the mud check. Runs on GitHub a few times a day (.github/workflows/mud.yml)
and writes mud.json, which the app reads from the repo's weather branch. If anything here fails, the app simply has no mud note.
Sources (free, commercial use allowed, no key): Environment Agency rain gauges (England), SEPA rain gauges (Scotland).
Wales: the nearest English gauge if one is within 20 km, else nothing yet (NRW's API needs a key).
Today's forecast (Met Office DataHub, needs Tony's free key) goes in the same file later: see MET_OFFICE_KEY below.
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
for (src, sid) in need:
    tot = [0.0, 0.0, 0.0, 0.0]; ok = False
    if src == "ea":
        j = get(f"https://environment.data.gov.uk/flood-monitoring/id/stations/{sid}/readings?since={since}&_sorted&_limit=2000")
        for r in (j or {}).get("items", []):
            try:
                i = dayidx(r["dateTime"])
                if 0 <= i <= 3 and isinstance(r.get("value"), (int, float)) and r["value"] >= 0: tot[i] += r["value"]; ok = True
            except Exception: pass
    else:
        q = urllib.parse.urlencode({"service": "kisters", "type": "queryServices", "request": "getTimeseriesValues", "datasource": "0",
                                    "format": "json", "ts_id": sid, "period": "P4D"})
        j = get("https://timeseries.sepa.org.uk/KiWIS/KiWIS?" + q)
        try:
            for ts, v in j[0]["data"]:
                i = dayidx(ts)
                if 0 <= i <= 3 and v is not None and v >= 0: tot[i] += float(v); ok = True
        except Exception: pass
    need[(src, sid)] = [round(x, 1) for x in tot] if ok else None
    time.sleep(0.2)

walks = {wid: need[k] for wid, k in pick.items() if need.get(k)}
# MET_OFFICE_KEY: when Tony has a DataHub key (repo secret), add today's forecast rain per walk here and fold it into today's slot.
json.dump({"updated": now.isoformat(timespec="minutes"), "walks": walks}, open(OUT, "w"), separators=(",", ":"))
print(len(walks), "walks with recent rain written to", OUT)
