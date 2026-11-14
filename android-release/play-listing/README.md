# Hlid Play listing (14 Nov 2026)

Relay format, Hlid's look. Files in this folder:
- hlid-play-screenshot-1-today.png ... -4-day.png: 1080 x 1920, 24-bit PNG, no alpha. Site headlines (two lines, Zalando Sans Expanded 600, 104 px, white) on full-bleed day colours (1 456985 blue, 2 4E685F, 3 618993, 4 D87F30 orange to match the day card; all 3:1 or more against white) over the real app screen in an off-black phone frame.
- hlid-play-feature-graphic.png: 1024 x 500. More walk. Less app. on 456985 beside the 3D phone showing Today (same angle as Relay's).
- hlid-play-listing-text.txt: title, short description (78/80), full description, split by ---.
- hlid-play-alt-text.txt: alt text per image.
- source/: shot.html lays it out, render.py renders it (needs Playwright + Chrome: Claude runs it in its workspace). Screens are copies of the site captures (version-hlid/screens/{today,carpark,walk,done}.webp). Re-run after the app or site screens change.
Not uploaded to Play Console yet (store listing is a draft).
