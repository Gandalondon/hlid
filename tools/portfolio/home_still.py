"""Hlid portfolio: the tall still of the homepage for gandalondon.com/work/hlid (top image).
The whole page at 1728 wide in one piece, so the white gaps stay exactly as on the site (208 between every section).
Colours are forced so the still is calm and varied: blue hero with Bignor (456985), the end screen stays orange,
the last phone shows the green day (4E685F).
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
    pg.wait_for_timeout(300); pg.screenshot(path="/tmp/hs_full.png",full_page=True); b.close()
im=Image.open("/tmp/hs_full.png").convert("RGB"); im.save(OUT,quality=88); print(OUT,im.size)
