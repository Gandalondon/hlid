# Woden: end of walk (14) gets Drive home and Find a pub; Find a pub opens one pub (19) with Show another.
# Pub rule (Tony, 13 Nov): any decent pub nearby, no car park needed. The walk's own car park is always free.
import math, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from routes import LOOPS, parse
INK = "#1A1A1A"; LAND = "#F0F0F0"
BTN = f"width: 100%; height: 56px; border: 0; border-radius: 999px; background: {INK}; color: #FFFFFF; font-family: inherit; font-size: 18px; font-weight: 600"
BTN2 = f"width: 100%; height: 48px; border: 0; background: transparent; color: {INK}; font-family: inherit; font-size: 18px; font-weight: 600"
CAR = (-0.3725, 50.8994)
WALK = parse(LOOPS["chanctonbury"])
# drive routes on real roads (OSRM, 14 Nov; Tony: the hand-drawn ones were far too angular). Refresh: see pub_routes.json
import json, os
ROUTES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pub_routes.json")))
PUBS = [  # name, drive, rating line, route from the car park (lon, lat); ratings from Google, 13 Nov
    ("The Fountain, Ashurst", "12 min drive", "4.4 on Google",
     [CAR] + [tuple(c) for c in ROUTES["fountain"]["coords"]]),
    ("The Frankland Arms, Washington", "5 min drive", "4.4 on Google",
     [CAR] + [tuple(c) for c in ROUTES["frankland"]["coords"]]),
]
W, H, PAD = 342, 360, 48
def mapsvg(route):
    k = math.cos(math.radians(50.9))
    pts = route + WALK
    xs = [p[0] * k for p in pts]; ys = [p[1] for p in pts]
    sc = min((W - 2 * PAD) / (max(xs) - min(xs)), (H - 2 * PAD) / (max(ys) - min(ys)))
    cx = (max(xs) + min(xs)) / 2; cy = (max(ys) + min(ys)) / 2
    def P(p): return (W / 2 + (p[0] * k - cx) * sc, H / 2 - (p[1] - cy) * sc)
    def d(ps): return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in map(P, ps))
    ex, ey = P(route[-1]); sx, sy = P(CAR)
    return (f'<rect width="{W}" height="{H}" fill="{LAND}"></rect>'
            f'<path d="{d(WALK)}" fill="none" stroke="#8C8C8C" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"></path>'
            f'<path d="{d(route)}" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></path>'
            f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7" fill="#FFFFFF" stroke="{INK}" stroke-width="3"></circle>'
            f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="9" fill="{INK}"></circle>')
MAPS = [mapsvg(p[3]) for p in PUBS]
def pub_section():
    n, dr, rt, _ = PUBS[0]
    return ('<section class="scr" data-id="pub"><div style="width: 390px; height: 844px; box-sizing: border-box; background: #FFFFFF; color: #1A1A1A; display: flex; flex-direction: column; position: relative; overflow: hidden; padding: 48px 24px 32px">'
            '<div style="display: flex; align-items: center; height: 48px"><button type="button" class="back" aria-label="Back to your walk" style="width: 48px; height: 48px; padding: 0; border: 0; background: transparent; display: flex; align-items: center; justify-content: center; margin-left: -12px"><span class="ms" aria-hidden="true">arrow_back</span></button></div>'
            f'<div style="margin-top: 16px; border-radius: 24px; overflow: hidden; height: {H}px"><svg id="pubmap" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Drive from the car park to the pub">{MAPS[0]}</svg></div>'
            f'<h1 id="pubname" style="margin: 24px 0 0">{n}</h1>'
            f'<p id="publine" style="margin: 12px 0 0; font-size: 16px; line-height: 1.4">{dr}. {rt}.</p>'
            '<div style="flex: 1"></div>'
            f'<button type="button" style="{BTN}">Drive there</button>'
            '<button type="button" style="width: 100%; height: 48px; margin-top: 12px; border: 0; background: transparent; color: #1A1A1A; font-family: inherit; font-size: 18px">Show another</button>'
            '</div></section>')
def done_patch(h):
    # the picture stays the ta-da; Download lives in Your walks (every finished walk is saved there)
    h = h.replace("height: 560px", "height: 520px").replace('height="560" viewBox="0 0 342 560"', 'height="520" viewBox="0 0 342 560" preserveAspectRatio="xMidYMid slice"')
    a = h.index('<button type="button" style="width: 100%; height: 56px')
    b = h.index("Not now</button>") + len("Not now</button>")
    return h[:a] + f'<button type="button" style="{BTN}">Drive home</button><button type="button" style="{BTN2}">Find a pub</button>' + h[b:]
import json
PUB_JS = """
  /* end of walk: Drive home, or one pub nearby (Show another swaps in the next) */
  var PUBS=%s, pubI=0;
  function showPub(i){ pubI=i; var p=PUBS[i]; document.getElementById("pubmap").innerHTML=p.m; document.getElementById("pubname").textContent=p.n; document.getElementById("publine").textContent=p.d+". "+p.r+"."; }
  byText["Drive home"]=function(){ toast("Google Maps would open here",1100,function(){ reset("home"); }); };
  byText["Find a pub"]=function(){ showPub(0); go("pub"); };
  byText["Show another"]=function(){ showPub((pubI+1)%%PUBS.length); };
  byText["Drive there"]=function(){ toast("Google Maps would open here",1100,function(){ reset("home"); }); };
""" % json.dumps([{"n": n, "d": dr, "r": rt, "m": m} for (n, dr, rt, _), m in zip(PUBS, MAPS)])
