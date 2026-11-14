"""Hlid: one sync command. Edit tokens.json (ink, greys, day ramp, map style, guidance), then run from ~/Hlid:
    python3 tools/sync_all.py
Generate (runs here, on the Mac):
  1. test walks + demo map data  tools/walkdata/build8.py, build8.py demo   (needs data/areas, data/terr50)
  2. demo map screens            build/maps.py                              (style B, from demo8.json)
  3. hero walls and lines        build/site_art.py                          (SVGs in build/site_art)
  4. app                         app/gen_app.py                             (app-c.html with walks8 + tokens)
Render (needs Playwright + Chrome, which the Mac shell does not have, so Claude runs these in its workspace from staged copies):
  5. site screens    portfolio/tools/sync_site_screens.py app/app-c.html version-hlid/screens   (then copy into the repo's site/screens)
  6. folio pairs     portfolio/tools/folio_screens.py app/app-c.html <tmp>; portfolio/tools/folio_pairs.py portfolio/woden_pair-walk-v4.jpg <tmp> portfolio
  7. giant logo      portfolio/tools/hlid-logo.html (2048 x 1052 screenshot)
  8. style guide     docs/style-guide.html from tools/style-guide/template.html (day ramp + map tokens)
  9. canvas V2 boards, Play graphics (Relay format)  - re-shoot from the outputs above
  10. APK asset      app-c.html + the Android app-mode block -> repo app/src/main/assets/index.html
Steps 1-4 run with no arguments; --skip-data skips step 1 (slowest)."""
import os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEPS = [("test walks", ["tools/walkdata/build8.py"]), ("demo map data", ["tools/walkdata/build8.py", "demo"]),
         ("demo map screens", ["build/maps.py"]), ("hero walls", ["build/site_art.py"]), ("app", ["app/gen_app.py"])]
skip = "--skip-data" in sys.argv
for name, cmd in STEPS:
    if skip and cmd[0].startswith("tools/walkdata"): continue
    t = time.time(); r = subprocess.run([sys.executable] + cmd, cwd=ROOT, capture_output=True, text=True)
    print(f"{'ok ' if r.returncode == 0 else 'FAIL'} {name} ({time.time() - t:.0f}s)" + ("" if r.returncode == 0 else "\n" + r.stderr[-800:]))
    if r.returncode: sys.exit(1)
print("Generated. Render steps 5-10 need Playwright: ask Claude to run them (see this file's notes).")
