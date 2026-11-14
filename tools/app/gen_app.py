# Woden app.html: the V1 app in a phone frame, clickable end to end (13 Nov). Run from ~/Woden: python3 app/gen_app.py
# Light screens are written here (copied from the V1 canvas boards). Map screens are pulled from the newest build outputs
# (build/r2 and build/maps), which hold the drawn routes and relief. Type: Zalando Sans Expanded 600 headings, Inter UI.
import re, os, html, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pub import pub_section, done_patch, PUB_JS
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
INK = "#1A1A1A"; META = "#1A1A1A"; RULE = "#DDD8CD"  # text is black and white only (Tony, 13 Nov)
ROOTST = f"width: 390px; height: 844px; box-sizing: border-box; background: #FFFFFF; color: {INK}; display: flex; flex-direction: column; position: relative; overflow: hidden; padding: 48px 24px 32px"
BTN = f"width: 100%; height: 56px; border: 0; border-radius: 999px; background: {INK}; color: #FFFFFF; font-family: inherit; font-size: 18px; font-weight: 600"
ICONB = "width: 48px; height: 48px; padding: 0; border: 0; background: transparent; display: flex; align-items: center; justify-content: center"
def back(label, right=""):
    return (f'<div style="display: flex; justify-content: space-between; align-items: center; height: 48px"><button type="button" class="back" aria-label="{label}" style="{ICONB}; margin-left: -12px"><span class="ms" aria-hidden="true">arrow_back</span></button>{right}</div>')
def h1(t, mt=32): return f'<h1 style="margin: {mt}px 0 0">{t}</h1>'
CHECK = '<span class="ms" aria-hidden="true">check</span>'
def opts(items, sel):
    # selectors (13 Nov pm): 56px pills, the same shape as the Setting off from field; the picked one fills ink with a white tick
    out = []
    for it in items:
        on = it == sel
        out.append(f'<button type="button" class="opt" aria-pressed="{str(on).lower()}"><span>{it}</span></button>')
    return '<div style="display: flex; flex-direction: column; gap: 8px; margin-top: 40px">' + "".join(out) + '</div>'
def rows(pairs, mt=40):
    return (f'<div style="display: flex; flex-direction: column; margin-top: {mt}px">' + "".join(
        f'<button type="button" class="row" style="display: flex; justify-content: space-between; align-items: center; height: 64px; padding: 0; border: 0; border-bottom: 1px solid {RULE}; background: transparent; font-family: inherit; font-size: 16px; color: {INK}"><span>{a}</span><span style="color: {META}">{b}</span></button>' for a, b in pairs) + '</div>')
def scr(i, body): return f'<section class="scr" data-id="{i}"><div style="{ROOTST}">{body}</div></section>'
FILL = '<div style="flex: 1"></div>'
SET = [("Home", "SW20"), ("Drive", "Up to 1h 15"), ("Walk", "2 to 3 hours"), ("Prefer", "Quiet over busy")]
cards = ('<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><rect x="9.5" y="3.5" width="11" height="17" rx="3" fill="none" stroke="#1A1A1A" stroke-width="2"></rect>'
         '<path d="M7 5.6 C5.7 5.7 4.8 6.8 4.9 8.1 L5.9 17.6 C6 18.6 6.5 19.3 7.3 19.6" fill="none" stroke="#1A1A1A" stroke-width="2"></path></svg>')
light = {
 "welcome": '<div style="height: 48px"></div>' + h1("A country walk, picked for you.<br>Drive,&nbsp;walk,&nbsp;home.") + FILL + '<div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 32px; font-size: 16px; line-height: 1.4"><p style="margin: 0">Well-known routes on public footpaths.</p><p style="margin: 0">Free car parks you can reach on A and B roads.</p><p style="margin: 0">No single-track lanes on the drive.</p></div>' + f'<button type="button" data-go="from" style="{BTN}">Get started</button>',
 "from": back("Back to Welcome", f'<span style="font-size: 14px; color: {META}">1 of 4</span>') + h1("Setting off from?") +
   '<div class="fld" style="margin-top: 40px; display: flex; align-items: center; height: 56px; box-sizing: border-box; padding: 0 4px 0 24px; border: 1px solid #B5B1A5; border-radius: 28px"><label for="wdHome" class="sr">Postcode or town</label><input id="wdHome" type="text" value="SW20" placeholder="Postcode or town" style="flex: 1; min-width: 0; height: 100%; padding: 0; border: 0; background: transparent; font-family: inherit; font-size: 18px; color: #1A1A1A; outline: none">'
   f'<button type="button" aria-label="Use my location" style="{ICONB}; border-radius: 24px"><span class="ms" aria-hidden="true">my_location</span></button></div>' + FILL + f'<button type="button" class="next" data-go="drive" style="{BTN}">Next</button>',
 "drive": back("Back to Setting off from", f'<span style="font-size: 14px; color: {META}">2 of 4</span>') + h1("Drive length?") + opts(["Up to 45 min", "Up to 1h", "Up to 1h 15", "Up to 1h 30"], "Up to 1h 15") + FILL + f'<button type="button" class="next" data-go="walk" style="{BTN}">Next</button>',
 "walk": back("Back to Drive length", f'<span style="font-size: 14px; color: {META}">3 of 4</span>') + h1("Walk length?") + opts(["1 to 2 hours", "2 to 3 hours", "3 to 4 hours", "Most of the day"], "2 to 3 hours") + FILL + f'<button type="button" class="next" data-go="quiet" style="{BTN}">Next</button>',
 "quiet": back("Back to Walk length", f'<span style="font-size: 14px; color: {META}">4 of 4</span>') + h1("Quiet or busy?") + opts(["Quiet over busy", "Don’t mind", "Popular spots"], "Quiet over busy") + FILL + f'<button type="button" class="next" data-go="today" data-root="home" style="{BTN}">Find my walk</button>',
 "check": back("Back to Quiet or busy") + h1("Set it once") + rows(SET) + FILL + f'<button type="button" data-go="today" data-root="home" style="{BTN}">Find my walk</button>',
 "home": f'<div style="height: 48px; display: flex; justify-content: flex-end; align-items: center"><div style="display: flex; margin-right: -12px"><button type="button" data-go="walks" aria-label="Your walks" style="{ICONB}">{cards}</button><button type="button" data-go="settings" aria-label="Settings" style="{ICONB}"><span class="ms" aria-hidden="true">person</span></button></div></div>'
   + h1("Morning.<br>Where to today?") + FILL + '<p id="homeSum" style="margin: 0 0 32px; font-size: 16px; line-height: 1.4">Up to 1h 15 drive. 2 to 3 hours walking. Quiet over busy.</p>' + f'<button type="button" data-go="today" style="{BTN}">Find a walk</button>',
 "settings": back("Back to home") + h1("Settings") + '<div style="display: flex; flex-direction: column; margin-top: 32px">' + "".join(
    f'<button type="button" class="row" data-edit="{e}" style="display: flex; justify-content: space-between; align-items: center; height: 64px; padding: 0; border: 0; border-bottom: 1px solid {RULE}; background: transparent; font-family: inherit; font-size: 16px; color: {INK}"><span>{a}</span><span data-val="{e}">{b}</span></button>'
    for (a, b), e in zip(SET, ["from", "drive", "walk", "quiet"])) + '</div>',
 "walks-empty": back("Back to home") + h1("Your walks") + '<p style="margin: 12px 0 0; font-size: 16px; line-height: 1.5">Each walk you finish becomes a picture of the day, coloured by its weather. They collect here.</p>' + FILL + f'<button type="button" data-go="today" style="{BTN}">Find a walk</button>',
}
heavy = [("today-1", "build/r2/Today-1.dc.html"), ("today-2", "build/r2/Today-2.dc.html"), ("today-3", "build/r2/Today-3.dc.html"), ("today-4", "build/r2/Today-4.dc.html"),
         ("carpark", "build/maps/Arrived.dc.html"), ("walking", "build/maps/Walk.dc.html"), ("done", "build/r2/Done.dc.html"), ("walks", "build/r2/Walks.dc.html")]
def inner(path):
    s = open(os.path.join(ROOT, path), encoding="utf-8").read()
    s = s[s.index("<x-dc>") + 6: s.index("</x-dc>")]
    s = re.sub(r"<helmet>.*?</helmet>", "", s, flags=re.S).strip()
    s = s.replace('stroke="#F3F0E8"', 'stroke="#FFFFFF"')   # picture lines are White, not cream (Tony, 13 Nov)
    s = s.replace(">Save wallpaper<", ">Download<")
    return done_patch(s) if path.endswith("Done.dc.html") else s
order = ["welcome", "from", "drive", "walk", "quiet", "check", "home"]
secs = [scr(k, light[k]) for k in order]
BACKBTN = ('<button type="button" class="back" aria-label="Back to today" style="position: absolute; top: 48px; left: 12px; z-index: 2; ' + ICONB + '">'
           '<span class="ms" aria-hidden="true">arrow_back</span></button>')
def addback(i, h):
    # the car park screen had no way back: same back arrow as Today, over the map, top left
    if i != "carpark": return h
    k = h.index(">") + 1
    return h[:k] + BACKBTN + h[k:]
secs += [f'<section class="scr" data-id="{i}">{addback(i, inner(p))}</section>' for i, p in heavy]
secs.append(pub_section())
secs += [scr(k, light[k]) for k in ("settings", "walks-empty")]
shell = open(os.path.join(HERE, "shell.html"), encoding="utf-8").read()
shell = shell.replace('  view.addEventListener("click",function(e){', PUB_JS + '  view.addEventListener("click",function(e){', 1).replace('"walk-detail":16};', '"walk-detail":16,"pub":19};', 1)
import json, datetime, sys
sys.path.insert(0, ROOT); from routes import META
# demo days spread across the weather ramp (14 Nov): Chanctonbury is its real day (13 Jul, as on the About page)
SAVED = [("chanctonbury", (7, 13), 22, "Clear"), ("kithurst", (10, 30), 9, "Rain"), ("bignor", (1, 10), 3, "Cloudy"), ("harting", (9, 25), 18, "Clear")]
def hm(m): return f"{m // 60}h {m % 60:02d}"
INFO = {META[k][0]: f"{datetime.date(2026, *d).strftime('%A')} {d[1]} {datetime.date(2026, *d).strftime('%B')}. {w}, {t}°. {META[k][2]} km walk, {hm(META[k][1])} drive." for k, d, t, w in SAVED}

# ---- consistency pass (14 Nov): one stroke system, day colours from the weather rule only ----
STOPS=[(t,tuple(int(h[i:i+2],16) for i in (1,3,5))) for t,h,_ in __import__('json').load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'tokens.json')))['day']['stops']]  # from tokens.json (3b, Tony 14 Nov 16:22)
def _lin(c): c/=255; return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def _unlin(c): c=max(0,min(1,c)); return round(255*(12.92*c if c<=0.0031308 else 1.055*c**(1/2.4)-0.055))
def _cr(c): r,g,b=[_lin(x) for x in c]; return 1.05/(.2126*r+.7152*g+.0722*b+.05)
def day_colour(temp,sky):
    if temp<=STOPS[0][0]: c=STOPS[0][1]
    elif temp>=STOPS[-1][0]: c=STOPS[-1][1]
    else:
        for (t0,c0),(t1,c1) in zip(STOPS,STOPS[1:]):
            if t0<=temp<=t1: f=(temp-t0)/(t1-t0); c=tuple(_unlin(_lin(a)*(1-f)+_lin(b)*f) for a,b in zip(c0,c1)); break
    k={"Clear":0,"Cloudy":0.15,"Rain":0.30}[sky]
    c=tuple(round(x*(1-k)) for x in c)
    while _cr(c)<3.0: c=tuple(max(0,round(x*0.99)) for x in c)  # 3:1 floor against white
    return "#%02X%02X%02X"%c
DAYWX={META[k][0]:(t,w) for k,_,t,w in SAVED}; DAYWX.setdefault("Old Winchester Hill",(6,"Clear"))
def consistency(h):
    def fix_svg(m):
        s=m.group(0); n=re.search(r'aria-label="([^":]+): drive and walk"',s)
        if not n or n.group(1) not in DAYWX: return s
        old=re.search(r'<rect[^>]*fill="(#[0-9A-Fa-f]{6})"',s)
        return s.replace(old.group(1),day_colour(*DAYWX[n.group(1)])) if old else s
    h=re.sub(r'<svg[^>]*aria-label="[^"]*: drive and walk".*?</svg>',fix_svg,h,flags=re.S)
    # cards behind the pictures carry the same colour in their wrapper div
    for old,name in (("6E9CC4","Chanctonbury Ring"),("6B7178","Kithurst Hill"),("9EA6A9","Bignor Hill"),("C49A4E","Harting Down"),("2F3B4C","Old Winchester Hill")):
        h=re.sub("#"+old+r"\b",day_colour(*DAYWX[name]),h,flags=re.I)
    # walk lines are 8px on every map: car park (scale 168.531), walking (scale 260)
    h=h.replace('Clear, 14°','Clear, 22°').replace('Chanctonbury Ring, 13 Nov','Chanctonbury Ring, 13 Jul')
    for w,n in (("F0F0EE","F0F0F0"),("8C8C88","8C8C8C"),("E5E5E3","E5E5E5")): h=re.sub("#"+w+r"\b","#"+n,h,flags=re.I)  # neutral greys only
    h=h.replace('stroke-width="0.0415"','stroke-width="0.0475"').replace('stroke-width="0.0269"','stroke-width="0.0308"')
    return h
ICONS = json.load(open(os.path.join(HERE, "icons.json")))
def svg(name): return f'<svg class="ic{" big" if name == "person" else ""}" width="24" height="24" viewBox="0 -960 960 960" aria-hidden="true"><path fill="currentColor" d="{ICONS[name]}"></path></svg>'
body = "\n".join(secs)
# icons: Material Symbols Rounded drawn inline as SVG, so they show offline and never fall back to their names
body = body.replace('<span>Clear, 14°</span>', '<span class="lab">Clear, 14°</span>').replace('>3.6 km to go<', ' class="lab">3.6 km to go<')
body = re.sub(r'(\d) (km|min|hours)\b', '\\1&nbsp;\\2', body)  # keep numbers with their units
body = re.sub(r'<span class="ms"[^>]*>([a-z_]+)</span>', lambda m: svg(m.group(1)), body)
out = shell.replace("<!--SCREENS-->", body).replace("/*CHECK_SVG*/", json.dumps(svg("check"))).replace("/*BACK_SVG*/", svg("arrow_back")).replace("/*INFO*/", json.dumps(INFO))
open(os.path.join(HERE, "app.html"), "w", encoding="utf-8").write(out)
print("app.html", len(out))

# ---------------------------------------------------------------------------------------------
# Exploration B (13 Nov pm): Sniff-style onboarding. One preferences screen with chips and
# switches instead of four question screens; Settings is the same screen, changes apply at once.
# Writes app-b.html; app.html (A) is untouched. Board numbers in B: 1 Welcome, 2 From, 3 Your walks prefs.
# ---------------------------------------------------------------------------------------------
GROUPS = [  # key, screen title, chips, picked, single choice?  (one question per screen, Tony 13 Nov pm)
    ("drive", "Drive length?", ["45 min", "1 hour", "1h 15", "1h 30"], ["1h 15"], True),
    ("walk", "Walk length?", ["1 to 2 hours", "2 to 3 hours", "3 to 4 hours", "All day"], ["2 to 3 hours"], True),
    ("busy", "Quiet or busy?", ["Quiet", "Don’t mind", "Popular"], ["Quiet"], True),
]
# free parking and avoiding narrow lanes are rules of the app, not settings (Tony, 13 Nov pm)
def chips(key, items, picked, single):
    cs = "".join(f'<button type="button" class="chip" aria-pressed="{str(i in picked).lower()}">{i}</button>' for i in items)
    return f'<div class="grp" data-key="{key}" data-single="{str(single).lower()}"><div class="chips">{cs}</div></div>'
B_CSS = """
/* B: Sniff-style chips, one question per screen. 48px, radius 24, picked = ink border plus 1px inset (labels never shift) */
.grp{margin-top:40px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{height:48px;padding:0 20px;border-radius:24px;border:1px solid #1A1A1A;background:#FFFFFF;color:#1A1A1A;font:500 16px/1 "Inter",sans-serif!important;cursor:pointer}
.chip[aria-pressed="true"]{border-color:#1A1A1A;box-shadow:none}
.sheet .grp{margin-top:0}
"""
B_JS = """
  /* B: chips (single or multi), Settings sheet uses the same chips, Home recaps */
  function grpVals(scr,key){ return [].slice.call(el(scr).querySelectorAll('.grp[data-key="'+key+'"] .chip[aria-pressed="true"]')).map(function(c){return c.textContent.trim();}); }
  view.addEventListener("click",function(e){ var b=e.target.closest(".chip"); if(!b) return;
    var g=b.closest(".grp"); if(g.dataset.single==="true"){ g.querySelectorAll(".chip").forEach(function(c){ c.setAttribute("aria-pressed","false"); }); b.setAttribute("aria-pressed","true"); }
    else b.setAttribute("aria-pressed", b.getAttribute("aria-pressed")==="true"?"false":"true");
    if(!b.closest(".sheet")){ var sv=view.querySelector('.scr[data-id="settings"] [data-val="'+g.dataset.key+'"]'); if(sv) sv.textContent=grpVals(cur(),g.dataset.key).join(", ")||"None"; }
    e.stopPropagation(); },true);
  openSheet=function(k){ sheetKey=k; var src=el(k);
    document.getElementById("sheetq").textContent=src.querySelector("h1").textContent;
    var body=document.getElementById("sheetbody"); body.innerHTML="";
    var part=k==="from"?src.querySelector(".fld"):src.querySelector(".grp"); var c=part.cloneNode(true); c.style.marginTop="0";
    if(c.querySelector("input")){ c.querySelector("input").id="sheetIn"; var l=c.querySelector("label"); if(l) l.htmlFor="sheetIn"; }
    body.appendChild(c); sheet.classList.add("on"); };
  saveSheet=function(){ var body=document.getElementById("sheetbody"), v;
    if(sheetKey==="from"){ v=body.querySelector("input").value.trim(); if(v) el("from").querySelector("input").value=v; }
    else { var on=[].slice.call(body.querySelectorAll('.chip[aria-pressed="true"]')).map(function(c){return c.textContent.trim();}); v=on.join(", ")||"None";
      el(sheetKey).querySelectorAll(".chip").forEach(function(c){ c.setAttribute("aria-pressed", on.indexOf(c.textContent.trim())>-1?"true":"false"); }); }
    var sv=view.querySelector('.scr[data-id="settings"] [data-val="'+sheetKey+'"]'); if(sv&&v) sv.textContent=v;
    closeSheet(); homeSum(); };
  homeSum=function(){ var d=grpVals("drive","drive")[0]||"", w=grpVals("walk","walk")[0]||"", q=grpVals("busy","busy")[0]||"";
    document.getElementById("homeSum").textContent="Up to "+d+" drive. "+w+" walking. "+(q==="Don’t mind"?"Quiet or busy.":q+"."); };
"""
NEXT = {"drive": "walk", "walk": "busy"}  # likes dropped (Tony, 13 Nov 17:30): four questions
BACKS = {"drive": "Back to Setting off from", "walk": "Back to Drive length", "busy": "Back to Walk length", "likes": "Back to Quiet or busy"}
def q_screen(n, key, title, items, picked, single):
    btn = (f'<button type="button" class="next" data-go="{NEXT[key]}" style="{BTN}">Next</button>' if key in NEXT
           else f'<button type="button" class="next" data-go="today" data-root="home" style="{BTN}">Find my walk</button>')
    return scr(key, back(BACKS[key], f'<span style="font-size: 14px">{n} of 4</span>') + h1(title) + chips(key, items, picked, single) + FILL + btn)
if True:
    secs_b = [scr("welcome", light["welcome"]), scr("from", light["from"])]
    secs_b += [q_screen(n, *g) for n, g in enumerate(GROUPS, start=2)]
    secs_b.append(scr("home", light["home"]))
    secs_b += [f'<section class="scr" data-id="{i}">{addback(i, inner(p))}</section>' for i, p in heavy]
    SETB = [("Home", "SW20", "from"), ("Drive", "1h 15", "drive"), ("Walk", "2 to 3 hours", "walk"), ("Busy", "Quiet", "busy")]
    secs_b.append(scr("settings", back("Back to home") + h1("Settings") + '<div style="display: flex; flex-direction: column; margin-top: 32px">' + "".join(
        f'<button type="button" class="row" data-edit="{e}" style="display: flex; justify-content: space-between; align-items: center; gap: 16px; height: 64px; padding: 0; border: 0; border-bottom: 1px solid {RULE}; background: transparent; font-family: inherit; font-size: 16px; color: {INK}"><span>{a}</span><span data-val="{e}" style="text-align: right">{b}</span></button>'
        for a, b, e in SETB) + '</div>'))
    secs_b.append(pub_section())
    secs_b.append(scr("walks-empty", light["walks-empty"]))
    bb = "\n".join(secs_b)
    bb = bb.replace('<span>Clear, 14°</span>', '<span class="lab">Clear, 14°</span>').replace('>3.6 km to go<', ' class="lab">3.6 km to go<')
    bb = re.sub(r'(\d) (km|min|hours)\b', '\\1&nbsp;\\2', bb)
    bb = re.sub(r'<span class="ms"[^>]*>([a-z_]+)</span>', lambda m: svg(m.group(1)), bb)
    outb = (shell.replace("<!--SCREENS-->", bb).replace("/*CHECK_SVG*/", json.dumps(svg("check"))).replace("/*BACK_SVG*/", svg("arrow_back")).replace("/*INFO*/", json.dumps(INFO))
            .replace("</style>", B_CSS + "</style>", 1)
            .replace('  reset("welcome");', B_JS + '  reset("welcome");', 1)
            .replace('<title>Woden app</title>', '<title>Woden app B</title>').replace(':not(.opt):not(.row):not(.card)', ':not(.opt):not(.row):not(.card):not(.chip)')
            .replace('var NUM={', 'var NUM={"busy":5,', 1))
    open(os.path.join(HERE, "app-b.html"), "w", encoding="utf-8").write(outb)
    print("app-b.html", len(outb))

# ---------------------------------------------------------------------------------------------
# Exploration C (13 Nov, 18:00): no onboarding. Open the app, allow location (one tap, Android's
# own prompt), and Today shows a walk straight away. Three chips at the top are today's inputs:
# where from, how long to drive, how long to walk. Tap one, pick, and the walk changes. Last
# choice is remembered, so a returning user taps nothing. No Welcome, questions, Home or Settings.
# Writes app-c.html; A and B are untouched.
# ---------------------------------------------------------------------------------------------
C_DRIVE = [("Up to 30 min", "30 min"), ("Up to 1 hour", "1h"), ("Up to 1h 30", "1h 30"), ("Up to 2 hours", "2h")]
C_WALK = [("About 1 hour", "1h"), ("About 2 hours", "2h"), ("About 3 hours", "3h"), ("About 4 hours", "4h")]
C_CSS = """
/* C: today's inputs as chips in the top bar; picking in the sheet applies at once */
.cbar{position:absolute;top:48px;left:24px;right:24px;height:48px;display:flex;align-items:center;gap:8px;z-index:2}
.cchip{height:40px;padding:0 16px;border-radius:20px;border:1px solid #1A1A1A;background:#FFFFFF;color:#1A1A1A;font:500 14px/1 "Inter",sans-serif!important;white-space:nowrap;cursor:pointer}
.cbar .sp{flex:1}
.chip{height:48px;padding:0 20px;border-radius:24px;border:1px solid #1A1A1A;background:#FFFFFF;color:#1A1A1A;font:500 16px/1 "Inter",sans-serif!important;cursor:pointer}
.chip[aria-pressed="true"]{border-color:#1A1A1A;box-shadow:none}
.sheet .chips{display:flex;flex-wrap:wrap;gap:8px}
.sheet.pick .save{display:none}
.perm{position:absolute;inset:0;z-index:5;display:none;background:rgba(26,26,26,.4);align-items:center;justify-content:center;padding:0 32px}
.perm.on{display:flex}
.perm .box{background:#FFFFFF;border-radius:28px;padding:24px;width:100%;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;gap:16px;font-family:"Inter",sans-serif}
.perm p{margin:0;font-size:18px;line-height:1.35;text-align:center;text-wrap:balance}
.perm .pb{width:100%;height:48px;border:0;border-radius:24px;background:#F0F0F0;color:#1A1A1A;font:500 15px/1 "Inter",sans-serif!important;cursor:pointer}
"""
C_JS = """
  /* C: today's inputs. Chips open a sheet; picking applies at once and finds another walk. */
  var CV={from:"SW20",drive:"1h 30",walk:"2h"};
  var COPT={drive:%s,walk:%s};
  var CQ={from:"Setting off from?",drive:"Drive for how long?",walk:"Walk for how long?"};
  function cLabel(k){ return k==="from"?CV.from:k==="drive"?CV.drive+" drive":CV.walk+" walk"; }
  function cPaint(){ view.querySelectorAll(".cchip").forEach(function(c){ c.textContent=cLabel(c.dataset.k); }); }
  function cAgain(){ closeSheet(); cPaint(); toast("Finding a walk…",700,function(){ day=day%%4+1; go("today",true); }); }
  openSheet=function(k){ sheetKey=k; document.getElementById("sheetq").textContent=CQ[k];
    var body=document.getElementById("sheetbody"); body.innerHTML="";
    if(k==="from"){ sheet.classList.remove("pick"); sheet.querySelector(".save").textContent="Done";
      body.innerHTML='<div class="fld" style="display:flex;align-items:center;height:56px;box-sizing:border-box;padding:0 4px 0 24px;border:1px solid #1A1A1A;border-radius:28px"><label for="cFrom" class="sr">Postcode or town</label><input id="cFrom" type="text" value="'+CV.from+'" placeholder="Postcode or town" style="flex:1;min-width:0;height:100%%;padding:0;border:0;background:transparent;font:400 16px Inter,sans-serif;color:#1A1A1A;outline:none"><button type="button" class="cloc" aria-label="Use my location" style="width:48px;height:48px;padding:0;border:0;background:transparent;display:flex;align-items:center;justify-content:center">'+LOC+'</button></div>'; }
    else { sheet.classList.add("pick"); var h='<div class="chips">';
      COPT[k].forEach(function(o){ h+='<button type="button" class="chip" data-v="'+o[1]+'" aria-pressed="'+(o[1]===CV[k])+'">'+o[0]+'</button>'; });
      body.innerHTML=h+'</div>'; }
    sheet.classList.add("on"); };
  saveSheet=function(){ var v=document.getElementById("cFrom").value.trim(); if(v&&v!==CV.from){ CV.from=v; cAgain(); } else closeSheet(); };
  view.addEventListener("click",function(e){ var c=e.target.closest(".cchip"); if(c){ openSheet(c.dataset.k); e.stopPropagation(); } },true);
  sheet.addEventListener("click",function(e){ var b=e.target.closest(".chip"); if(b){ if(b.dataset.v===CV[sheetKey]){ closeSheet(); } else { CV[sheetKey]=b.dataset.v; cAgain(); } e.stopPropagation(); return; }  /* the option you already have just closes the sheet (Tony, 13 Nov) */
    if(e.target.closest(".cloc")){ document.getElementById("cFrom").value="SW20"; e.stopPropagation(); } },true);
  view.addEventListener("click",function(e){ var p=e.target.closest(".pb"); if(!p) return; e.stopPropagation();
    document.getElementById("perm").classList.remove("on"); if(p.dataset.deny) openSheet("from"); },true);
  function firstOpen(){ day=1; reset("today"); document.getElementById("perm").classList.add("on"); }
"""
def c_today(h):
    # top bar: the three inputs on the left, Your walks on the right; weather moves into the walk's line
    a = h.index('<div style="position: absolute; top: 48px'); b = h.index('</div></div>', a) + len('</div></div>')
    w = re.search(r'<span>([^<]+°)</span>', h[a:b]); wx = w.group(1) if w else ""
    bar = ('<div class="cbar"><button type="button" class="cchip" data-k="from">SW20</button><button type="button" class="cchip" data-k="drive">1h 30 drive</button>'
           f'<button type="button" class="cchip" data-k="walk">2h walk</button><span class="sp"></span><button type="button" data-go="walks" aria-label="Your walks" style="{ICONB}; margin-right: -12px">{cards}</button></div>')
    h = h[:a] + bar + h[b:]
    h = re.sub(r'(km walk\.)(</p>)', lambda m: m.group(1) + (f' {wx}.' if wx else '') + m.group(2), h, count=1)
    h = h.replace('<svg width="390" height="480" viewBox="0 0 390 480"', '<svg width="390" height="480" viewBox="0 -24 390 480"', 1)  # nudge the route below the chips
    return h
if True:
    # no splash (Tony, 18:10): the app lands on Today; first open shows Android's location prompt over it
    PERM = ('<div class="perm" id="perm"><div class="box"><span class="ms" aria-hidden="true">my_location</span>'
            '<p>Allow Hlid to access this device’s location?</p>'
            '<button type="button" class="pb">While using the app</button><button type="button" class="pb">Only this time</button><button type="button" class="pb" data-deny="1">Don’t allow</button></div></div>')
    secs_c = []
    for i, p in heavy:
        h = addback(i, inner(p))
        if i.startswith("today-"): h = c_today(h)
        secs_c.append(f'<section class="scr" data-id="{i}">{h}</section>')
    secs_c.append(pub_section())
    secs_c.append(scr("walks-empty", light["walks-empty"]))
    cc = "\n".join(secs_c) + PERM
    cc = cc.replace('<span>Clear, 14°</span>', '<span class="lab">Clear, 14°</span>').replace('>3.6 km to go<', ' class="lab">3.6 km to go<')
    cc = re.sub(r'(\d) (km|min|hours)\b', '\\1&nbsp;\\2', cc)
    cc = re.sub(r'<span class="ms"[^>]*>([a-z_]+)</span>', lambda m: svg(m.group(1)), cc)
    js = C_JS % (json.dumps(C_DRIVE), json.dumps(C_WALK))
    outc = (shell.replace("<!--SCREENS-->", cc).replace("/*CHECK_SVG*/", json.dumps(svg("check"))).replace("/*BACK_SVG*/", svg("arrow_back")).replace("/*INFO*/", json.dumps(INFO))
            .replace("</style>", C_CSS + "</style>", 1)
            .replace('  reset("welcome");', '  var LOC=' + json.dumps(svg("my_location")) + ';\n' + js + '  firstOpen();', 1)
            .replace('function go(id, replace){ if(id==="today")', 'function go(id, replace){ if(id==="home"||id==="today")', 1)
            .replace('day=1; reset("welcome"); };', 'firstOpen(); };').replace('>Skip to Home<', '>Skip to Today<').replace('day=1; reset("home");', 'day=1; reset("today");')
            .replace('<title>Woden app</title>', '<title>Hlid app</title>').replace(':not(.opt):not(.row):not(.card)', ':not(.opt):not(.row):not(.card):not(.chip):not(.cchip):not(.pb)')
            )
    # Build 4 fixes (13 Nov) and the test walk were added by hand after generation; keep them in app-c.build4-block.html so a re-run never drops them
    blk = open(os.path.join(HERE, "app-c.build4-block.html"), encoding="utf-8").read()
    k = outc.rindex("</body>"); outc = outc[:k] + blk + outc[k:]
    outc = consistency(outc)
    # build 8: the three test walks (tools/walkdata/build8.py) and the map/guidance tokens (tokens.json)
    outc = outc.replace("/*WALKS8*/", open(os.path.join(ROOT, "data", "testwalk", "walks8.json"), encoding="utf-8").read(), 1)
    outc = outc.replace("/*TOKENS*/", json.dumps(json.load(open(os.path.join(ROOT, "tokens.json"))), separators=(",", ":")), 1)
    open(os.path.join(HERE, "app-c.html"), "w", encoding="utf-8").write(outc)
    print("app-c.html", len(outc))
