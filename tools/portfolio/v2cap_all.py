"""Hlid canvas V2: re-shoot the app boards (1-15, 50, 51) from app/src/main/assets/index.html at 390 x 844 @2x.
Usage: python3 v2cap_all.py <app index.html> <out dir>   (Playwright + Chrome). Board 49 (map download failed) is not a live state, so it is not shot."""
import asyncio, sys, os
from playwright.async_api import async_playwright
from PIL import Image
APP,OUT=sys.argv[1],sys.argv[2]
B=[("01","today-1","perm"),("02","today-1",""),("03","today-1","sheet:from"),("04","today-1","sheet:drive"),("05","today-1","sheet:walk"),
   ("06","today-2",""),("07","today-3",""),("08","today-4",""),("09","carpark",""),("10","walking",""),("11","walking","offline"),
   ("12","done",""),("13","pub",""),("14","walks",""),("15","walks-empty",""),("S50","x-outside",""),("S51","x-nofit","")]
CSS=(".stage{display:block;padding:0;min-height:0}.under,.toast{display:none!important}.phone{width:390px!important;height:844px!important}"
     ".frame{transform:none!important;background:none!important;border-radius:0!important;left:0;top:0}.view{left:0!important;top:0!important;border-radius:0!important}")
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("CHROME","/usr/bin/google-chrome")); pg=await b.new_page(viewport={"width":390,"height":844},device_scale_factor=2)
        await pg.goto("file://"+os.path.abspath(APP)+"?test"); await pg.wait_for_timeout(1200); await pg.add_style_tag(content=CSS)
        ok=await pg.evaluate("async()=>{await document.fonts.ready;return [...document.fonts].some(f=>f.family.indexOf('DM Sans')>=0&&f.status==='loaded')}")
        if not ok: sys.exit("DM Sans did not load")
        for n,sid,extra in B:
            have=await pg.evaluate("id=>!!document.querySelector('.scr[data-id=\"'+id+'\"]')",sid)
            if not have: print("missing",n,sid); continue
            await pg.evaluate("id=>{document.querySelectorAll('.scr').forEach(s=>s.classList.toggle('on',s.dataset.id===id));document.getElementById('sheet').classList.remove('on');(function(e){e.classList.remove('on');e.style.removeProperty('display')})(document.getElementById('perm'))}",sid)
            await pg.evaluate("o=>{var p=document.querySelector('.scr.on p.lab');if(p&&p.dataset.t==null)p.dataset.t=p.innerHTML;if(p)p.innerHTML=o?'4.3&nbsp;km to go. Offline, map saved.':p.dataset.t}",extra=="offline")
            if extra=="perm": await pg.evaluate("()=>{var e=document.getElementById('perm');e.classList.add('on');e.style.setProperty('display','flex','important')}")
            if extra.startswith("sheet:"): await pg.evaluate("k=>window.hlidOpenSheet(k)",extra[6:])
            await pg.wait_for_timeout(300); png=f"{OUT}/V2-{n}.png"
            await pg.screenshot(path=png,clip={"x":0,"y":0,"width":390,"height":844}); Image.open(png).convert("RGB").save(png[:-4]+".jpg",quality=88); os.remove(png); print("shot",n)
        await b.close()
asyncio.run(main())
