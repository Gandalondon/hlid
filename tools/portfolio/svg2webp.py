import asyncio,sys,os
from playwright.async_api import async_playwright
from PIL import Image
SRC,OUT=sys.argv[1],sys.argv[2]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("CHROME","/usr/bin/google-chrome")); pg=await b.new_page(viewport={"width":780,"height":1688})
        for n in sorted(os.listdir(SRC)):
            if not (n.startswith("wall-") or n.startswith("line-")): continue
            await pg.goto("file://"+os.path.abspath(os.path.join(SRC,n))); await pg.wait_for_timeout(100)
            png=os.path.join(OUT,n[:-4]+".png"); await pg.screenshot(path=png,omit_background=n.startswith("line-"))
            (lambda im: im.convert("RGBA" if n.startswith("line-") else "RGB"))(Image.open(png)).save(png[:-4]+".webp",quality=86); os.remove(png)
        await b.close()
asyncio.run(main())
