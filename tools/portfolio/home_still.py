"""Hlid portfolio: the tall still of the homepage for gandalondon.com/work/hlid (top image).
One 1728 x 1080 frame per section, stacked (hero, then each row). Colours are forced so the still is calm and varied:
blue hero with Bignor (456985), the end screen stays orange, the last phone shows the green day (4E685F).
Usage: serve site/ (python3 -m http.server 8765 in site/), then python3 home_still.py <out.jpg>   (needs Playwright + Chrome)"""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
OUT=sys.argv[1]; W,H=1728,1080
CSS=("*,*::before,*::after{animation:none!important;transition:none!important}"
     ".wash{background:#456985!important;opacity:1!important}.hdr .btn{color:#456985!important}"
     ".hmap img{opacity:0!important}.hmap img:nth-child(5){opacity:1!important}"
     ".cyc img{opacity:0!important}.cyc img:nth-child(3){opacity:1!important}"
     ".reveal{opacity:1!important;transform:none!important}")
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get("CHROME","/usr/bin/google-chrome"))
    pg=b.new_page(viewport={"width":W,"height":H})
    pg.goto("http://localhost:8765/index.html"); pg.wait_for_timeout(1200); pg.add_style_tag(content=CSS)
    ok=pg.evaluate("async()=>{await document.fonts.ready;return [...document.fonts].some(f=>f.family.indexOf('Zalando')>=0&&f.status==='loaded')}")
    if not ok: sys.exit("Fonts did not load")
    tops=pg.evaluate("""()=>{const out=[0];document.querySelectorAll('.step').forEach(s=>{const r=s.getBoundingClientRect();out.push(Math.round(r.top+scrollY+r.height/2-innerHeight/2))});
      out[out.length-1]=document.documentElement.scrollHeight-innerHeight;return out}""")
    frames=[]
    for i,y in enumerate(tops):
        if i==len(tops)-1: pg.evaluate("document.querySelectorAll('.step')[document.querySelectorAll('.step').length-2].style.visibility='hidden'")  # no sliver of the row above in the last frame
        pg.evaluate(f"scrollTo(0,{y})"); pg.wait_for_timeout(300); f=f"/tmp/hs{i}.png"; pg.screenshot(path=f); frames.append(Image.open(f).convert("RGB"))
    b.close()
sheet=Image.new("RGB",(W,H*len(frames)),"white")
for i,f in enumerate(frames): sheet.paste(f,(0,i*H))
sheet.save(OUT,quality=88); print(OUT,sheet.size)
