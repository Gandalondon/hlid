"""Builds frame.html (Hlid type trailer, 16:9). Routes and screens are the site's own files. Render: render.py. Usage: python3 build_page.py"""
import re, os, base64
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); S=os.path.join(ROOT,"site")
def inner(f):
    s=open(os.path.join(S,"screens",f)).read(); return re.sub(r'^<svg[^>]*>|</svg>\s*$','',s.strip())
C={1:(668,681),2:(668,626.1)}
routes="".join(f'<svg class="rt" id="r{i}" viewBox="0 0 780 1688">{inner(f"route-{i}.svg")}<circle class="ring" cx="{C[i][0]}" cy="{C[i][1]}" r="22" fill="none" stroke="#FFFFFF" stroke-width="6"/></svg>' for i in C)
done=base64.b64encode(open(os.path.join(S,"screens","done.webp"),"rb").read()).decode()
html=open(os.path.join(os.path.dirname(__file__),"frame.tpl.html")).read().replace("{{ROUTES}}",routes).replace("{{DONE}}",done).replace("{{FONTS}}","../../site/fonts")
open(os.path.join(os.path.dirname(__file__),"frame.html"),"w").write(html); print("ok")
