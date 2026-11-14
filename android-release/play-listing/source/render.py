"""Render shot.html to the Play files (24-bit PNG, no alpha). Usage: python3 render.py <out dir>"""
import asyncio, os, sys
from playwright.async_api import async_playwright
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=sys.argv[1]
NAMES={"s1":"hlid-play-screenshot-1-today","s2":"hlid-play-screenshot-2-drive","s3":"hlid-play-screenshot-3-walk","s4":"hlid-play-screenshot-4-day","fg":"hlid-play-feature-graphic"}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("CHROME","/usr/bin/google-chrome")); pg=await b.new_page(viewport={"width":1200,"height":2000})
        await pg.goto("file://"+os.path.join(HERE,"shot.html")); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(400)
        if not await pg.evaluate("[...document.fonts].some(f=>f.status==='loaded')"): sys.exit("Fonts did not load. Nothing rendered.")
        w=await pg.evaluate("Math.max(...[...document.querySelectorAll('.s h1')].map(h=>{const r=document.createRange();r.selectNodeContents(h);return r.getBoundingClientRect().width}))")
        print("widest title",round(w))
        for k,n in NAMES.items():
            png=os.path.join(OUT,n+".png"); await pg.locator("#"+k).screenshot(path=png)
            Image.open(png).convert("RGB").save(png); print(n,Image.open(png).size)
        await b.close()
asyncio.run(main())
