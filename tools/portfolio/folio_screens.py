"""Hlid: render the app screens used by the portfolio pairs from app/app-c.html at 390 x 844 (@3x).
Usage: python3 folio_screens.py <app-c.html> <out dir>   (needs Playwright; Claude runs it in its workspace)
Then: python3 folio_pairs.py <portfolio/woden_pair-walk-v4.jpg> <out dir> <portfolio dir>"""
import asyncio, sys, os, sys
from playwright.async_api import async_playwright
APP, OUT = sys.argv[1], sys.argv[2]
SHOTS = ["today-1", "today-2+drive", "today-3", "today-4", "carpark", "walking", "done", "pub"]
CSS = (".stage{display:block;padding:0;min-height:0}.under,.toast,.perm{display:none!important}.phone{width:390px!important;height:844px!important}"
       ".frame{transform:none!important;background:none!important;border-radius:0!important;left:0;top:0}.view{left:0!important;top:0!important;border-radius:0!important}")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROME","/usr/bin/google-chrome")); pg = await b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3)
        await pg.goto("file://" + os.path.abspath(APP)); await pg.wait_for_timeout(800); await pg.add_style_tag(content=CSS)
        ok = await pg.evaluate("async()=>{await document.fonts.ready;var l=[...document.fonts];return l.some(f=>f.family.indexOf('Zalando')>=0&&f.status==='loaded')&&l.some(f=>f.family.indexOf('DM Sans')>=0&&f.status==='loaded')}")
        if not ok: sys.exit("Fonts did not load (the app's fonts/ folder must sit next to the app file). Nothing rendered.")
        for name in SHOTS:
            sid, _, chip = name.partition("+")
            await pg.evaluate("id=>{document.querySelectorAll('.scr').forEach(s=>s.classList.toggle('on',s.dataset.id===id));document.getElementById('sheet').classList.remove('on')}", sid)
            if chip: await pg.click(f'.scr.on .cchip[data-k="{chip}"]')
            await pg.wait_for_timeout(250)
            await pg.screenshot(path=os.path.join(OUT, name + ".png"), clip={"x": 0, "y": 0, "width": 390, "height": 844})
        await b.close()
asyncio.run(main())
