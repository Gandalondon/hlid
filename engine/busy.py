"""Busy-spot rules (Tony, 15 Nov 2026). Works for any region without him:
- walk['busy'] == 'always'    -> never picked (visitor centre by a 200+ space car park on the route).
- walk['busy'] == 'busy_days' -> pushed to the bottom at weekends, bank holidays and school holidays; normal on other days.
- local veto list (data/gb/veto-<region>.json) -> never picked; overrides the rules, never copied to other regions.
Dates live in data/gb/busy-days.json so the app can work offline.
Usage: from busy import rank_key, allowed;  sorted(walks, key=lambda w: rank_key(w, date))"""
import json, os, re, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = json.load(open(os.path.join(ROOT, "data/gb/busy-days.json")))
VETO = json.load(open(os.path.join(ROOT, "data/gb/veto-sw-london.json")))["veto"]

def busy_day(d):
    s = d.isoformat()
    return d.weekday() >= 5 or s in DAYS["bank_holidays"] or any(a <= s <= b for a, b in DAYS["school_holidays"])

def allowed(w):
    n = (w.get("name_auto") or "") + " " + (w.get("name") or "")
    return not w.get("dropped") and w.get("busy") != "always" and not any(v in n.lower() for v in VETO)

def rank_key(w, d):
    """Sort key: allowed first, then on busy days the busy_days walks go last, then by score."""
    return (not allowed(w), busy_day(d) and w.get("busy") == "busy_days", -w.get("score", 0))

if __name__ == "__main__":
    import sys
    d = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today()
    W = json.load(open(os.path.join(ROOT, "data/gb/sw-walks-v3.json")))
    print(d, "busy day" if busy_day(d) else "quiet day")
    for w in sorted(W, key=lambda w: rank_key(w, d))[:12]:
        print(f"{w['rank']:3} {w.get('busy','?'):9} {'OUT ' if not allowed(w) else '    '}{(w.get('name_auto') or w['name'])[:50]}")
