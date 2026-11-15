"""Hlid canvas V2: re-shoot the live site boards from site/ (served on :8765).
16 hero + 17-22, 44 = the seven home sections at 1440 x 900; 23-25 full How it works, About, Privacy at 1440; 45-48 the same four pages full length at 390."""
import sys
from playwright.sync_api import sync_playwright
from PIL import Image
OUT=sys.argv[1]; U="http://localhost:8765/"
def save(png,name): Image.open(png).convert("RGB").save(f"{OUT}/V2-{name}.jpg",quality=88)
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_page(viewport={"width":1440,"height":900},device_scale_factor=2,reduced_motion="reduce")
    pg.goto(U); pg.wait_for_timeout(1500)
    pg.screenshot(path="/tmp/s.png"); save("/tmp/s.png","16")
    tops=pg.evaluate("[...document.querySelectorAll('section.step')].map(s=>{const r=s.getBoundingClientRect();return [r.top+scrollY,r.height]})")
    for (t,h),n in zip(tops,["17","18","19","20","21","22","44"]):
        pg.evaluate(f"scrollTo(0,{t+(h-900)/2})"); pg.wait_for_timeout(500); pg.screenshot(path="/tmp/s.png"); save("/tmp/s.png",n)
    sizes={}
    for path,n in [("how-it-works","23"),("about","24"),("privacy","25")]:
        pg.goto(U+path+".html"); pg.wait_for_timeout(800); pg.screenshot(path="/tmp/s.png",full_page=True); save("/tmp/s.png",n); sizes[n]=Image.open("/tmp/s.png").size
    m=b.new_page(viewport={"width":390,"height":844},device_scale_factor=2,reduced_motion="reduce")
    for path,n in [("","45"),("how-it-works.html","46"),("about.html","47"),("privacy.html","48")]:
        m.goto(U+path); m.wait_for_timeout(1200); m.screenshot(path="/tmp/s.png",full_page=True); save("/tmp/s.png",n); sizes[n]=Image.open("/tmp/s.png").size
    print({k:(v[0]//2,v[1]//2) for k,v in sizes.items()})
    b.close()
