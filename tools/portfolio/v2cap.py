import asyncio, sys, os, sys
from playwright.async_api import async_playwright
from PIL import Image
APP,OUT=sys.argv[1],sys.argv[2]
B={"02":"today-1","06":"today-2","07":"today-3","08":"today-4","09":"carpark","10":"walking","11":"walking!","12":"done","13":"pub","14":"walks"}
CSS=(".stage{display:block;padding:0;min-height:0}.under,.toast,.perm{display:none!important}.phone{width:390px!important;height:844px!important}"
     ".frame{transform:none!important;background:none!important;border-radius:0!important;left:0;top:0}.view{left:0!important;top:0!important;border-radius:0!important}")
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("CHROME","/usr/bin/google-chrome")); pg=await b.new_page(viewport={"width":390,"height":844},device_scale_factor=2)
        await pg.goto("file://"+os.path.abspath(APP)); await pg.wait_for_timeout(800); await pg.add_style_tag(content=CSS)
        ok = await pg.evaluate("async()=>{await document.fonts.ready;var l=[...document.fonts];return l.some(f=>f.family.indexOf('Zalando')>=0&&f.status==='loaded')&&l.some(f=>f.family.indexOf('Inter')>=0&&f.status==='loaded')}")
        if not ok: sys.exit("Fonts did not load (the app's fonts/ folder must sit next to the app file). Nothing rendered.")
        for n,sid in B.items():
            off=sid.endswith("!"); sid=sid.rstrip("!")
            await pg.evaluate("id=>{document.querySelectorAll('.scr').forEach(s=>s.classList.toggle('on',s.dataset.id===id));document.getElementById('sheet').classList.remove('on')}",sid)
            await pg.evaluate("o=>{var p=document.querySelector('.scr.on p.lab');if(p&&p.dataset.t==null)p.dataset.t=p.innerHTML;if(p)p.innerHTML=o?'4.3&nbsp;km to go. Offline, map saved.':p.dataset.t}",off)
            await pg.wait_for_timeout(200); png=f"{OUT}/V2-{n}.png"
            await pg.screenshot(path=png,clip={"x":0,"y":0,"width":390,"height":844}); Image.open(png).convert("RGB").save(png[:-4]+".webp",quality=86); os.remove(png)
        await b.close()
asyncio.run(main())
