# How it works: running notes (for the page rework, week of 30 Nov)

Tony, 21 Nov: the How it works page should make people think "oh, that's why it's worth £3.99", without giving away the recipe.
Say what Hlid does for you, never how (no sources, thresholds, scores or rule lists). Keep it short. Not the same lines every walking app uses.
Core story: not a curated list, but every walk has passed the same rules, and the rules exist to get you out quickly and easily to somewhere quiet, on a proper loop, with a pub nearby.

## On the page (what it does for you)
- Every walk is a proper loop from a free car park. You end where you parked.
- On paths, not lanes. Walks that spend too long on roads don't make it in.
- Hills and views. Flat walks don't make it in.
- Quiet: busy spots are pushed down at weekends and in school holidays, not dropped.
- Mud: Hlid checks the weather on the day and the last few days of rain at the walk, and steers you away from walks that are likely to be muddy. If it's wet everywhere, it tells you. (Possible homepage USP.)
- Finish before dark: only walks you can finish in daylight (built 21 Nov, build 80).
- A pub nearby: at the end, Find a pub shows one close by, within about half an hour's drive. No ratings, no lists, like it used to be.
- Works offline once you've picked a walk (the map is saved on your phone).
- Drive and walk time chosen on the day, not set up once.
- One price, nothing to unlock (offline maps and the off-path buzz are paid extras elsewhere).

## Keep private (the recipe)
- Sources: OpenStreetMap routes and car parks, OS Terrain 50 heights, OSRM drive times, rain data (Environment Agency / SEPA gauges planned), Met Office forecast.
- The gates: built length within 30% of listed, under 2% off a foot way, under 1 km on roads, free car park (fee=no), relief rules for car park loops (70 m within 2 km or above 150 m), foot-path density, 6-11 km loops, under 12% walked twice.
- The score: climb, length, drive time, waymarking, road share, honeypots, free parking, and their weights.
- Busy rules: visitor centre or cafe by a big or National Trust car park, 200+ spaces = always out.
- Pub rule: 3 closest by drive within 30 min of the car park, one per name, router sanity check.
- Leave by: now + drive + walk + 15 min must be before sunset at the car park (worked out on the phone); not applied before sunrise or after sunset (you're planning for tomorrow).
- Region pipeline and tools (tools/walkdata/region.py, inject.py, pubs.py, fixnames.py).

## To build before the page claims it
- Mud check (agreed 17 Nov, not built): past few days' rain at the walk plus the day's weather; "may be muddy" note when wet everywhere.
- Weather and rain sources need fallbacks we control (Open-Meteo is non-commercial only).
