# Hlid handover addendum, 14 Nov 2026, 17:40-19:05
Written to the repo because the Mac was offline. Next chat: append this to ~/Hlid/HANDOVER.md, then delete this file.

## Done since the last HANDOVER.md entry
- Portfolio (gandalondon.com/work/hlid, Storyblok story Hlid): PUBLISHED. Top image is now hlid-home-blue.jpg (~/Hlid/portfolio): blue hero (456985, Bignor line), orange on Keep the day (D87F30, Chanctonbury), green on the last step (4E685F). Colours are forced with CSS in the capture (wash/walls animation off, one walls img shown) because the page's lock() script restarts the colour animations. Typography paragraph now ends "Inter for the rest." (wider W line removed).
- Site copy (repo 0312ad9, live; version-hlid synced): "Hlid sends the route to Google Maps and always ends it at a free car park at the start of the walk, so you don't have to work out where to park." Tony plans his own copy pass.
- Rule change (Tony 19:03): a burger icon is fine when needed (e.g. when the phone header also holds a button). Hlid's two-line icon stays. Saved to memory; working-with-tony skill updated (proposed).
- Known glitch: device_commit_files can write a stale copy when the same staged path is reused; give each new output a fresh staged filename and check it on the Mac.

## Agreed, not built yet (Tony 19:03: do them all)
1. Play listings: 1024x500 feature graphic + four 1080x1920 screenshots (Relay format), description, from the new screens.
2. SW London walk data pass: honeypot penalty, footpath-only check (tools/walkdata/build8.py is_foot + metre check), real drive times from SW20 (OSRM from the Mac), car park fees for "unknown", footpath loops round free car parks (build8 carpark_loop()).
3. Kithurst and Old Winchester Hill demo routes are not loops: rebuild with carpark_loop (needs west-sussex/hampshire extracts), then re-render Today, Your walks, site screens and the hlid_pair-today folio image.
4. Canvas V2 boards (maps, lines) and the style guide map section: re-shoot in map style B.
5. Demo walking screen: move the demo point earlier so the line reads about 4.2 km to go, about 120 m still to climb (build/maps.py prog), then re-render site walk.webp and hlid_pair-walk.jpg.
(Mobile menu item dropped: burger stays.)

## Tony's own to-dos
- Check the Ranmore loop against his usual route.
- Copy the Cannon Hill GPX (phone Downloads/Hlid/hlid-2026-11-14-1550.gpx) to ~/Hlid.
- Copy pass on the site.
