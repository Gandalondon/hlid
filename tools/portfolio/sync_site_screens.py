"""Woden: copy the current app screens onto the concept site (13 Nov). Renders screens from app/app-c.html
(C from 18:15: set = Today 2 with the Drive sheet open, today = Today 1) at 780 x 1688 and writes site/screens/{set,today,carpark,walk,done}.webp.
Run after any app change. Needs Chrome + Playwright (Claude runs it in its workspace, then copies the files to the Mac)."""
import asyncio, sys, os
from playwright.async_api import async_playwright
from PIL import Image
APP, OUT = sys.argv[1], sys.argv[2]
MAP = {"set": "today-2+drive", "today": "today-1", "carpark": "carpark", "walk": "walking", "offline": "walking", "done": "done", "walks": "walks"}
# offline: the walking screen with the line the app shows when there is no signal (Tony 15:04, build 8 profile kept)
OFFLINE = "4.3 km to go. Offline, map saved."
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROME","/usr/bin/google-chrome"))
        pg = await b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        await pg.goto("file://" + os.path.abspath(APP)); await pg.wait_for_timeout(800)
        ok = await pg.evaluate("async()=>{await document.fonts.ready;var l=[...document.fonts];return l.some(f=>f.family.indexOf('Zalando')>=0&&f.status==='loaded')&&l.some(f=>f.family.indexOf('DM Sans')>=0&&f.status==='loaded')}")
        if not ok: sys.exit("Fonts did not load (the app's fonts/ folder must sit next to the app file). Nothing rendered.")
        await pg.add_style_tag(content=".stage{display:block;padding:0;min-height:0}.under,.toast,.perm{display:none!important}html body .sheet .opt[aria-pressed=true],html body .sheet .chip[aria-pressed=true]{box-shadow:none!important}.phone{width:390px!important;height:844px!important}.frame{transform:none!important;background:none!important;border-radius:0!important;left:0;top:0}.view{left:0!important;top:0!important;border-radius:0!important}")
        for name, sid in MAP.items():
            sid, _, chip = sid.partition("+")
            await pg.evaluate("id=>{document.querySelectorAll('.scr').forEach(s=>s.classList.toggle('on',s.dataset.id===id));document.getElementById('sheet').classList.remove('on')}", sid)
            if chip: await pg.click(f'.scr.on .cchip[data-k="{chip}"]')
            if name == "offline": await pg.evaluate("t=>{var p=document.querySelector('.scr.on p.lab');if(p)p.textContent=t}", OFFLINE)
            await pg.wait_for_timeout(150)
            png = os.path.join(OUT, name + ".png")
            await pg.screenshot(path=png, clip={"x": 0, "y": 0, "width": 390, "height": 844})
            Image.open(png).convert("RGB").save(os.path.join(OUT, name + ".webp"), quality=86); os.remove(png)
        await b.close()
asyncio.run(main())
