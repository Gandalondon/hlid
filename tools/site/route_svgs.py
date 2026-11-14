"""Hlid home (14 Nov): site/screens/route-*.svg = build/site_art line-*.svg without the home ring, with the drive trimmed
so its round cap meets the OUTSIDE of the ring (r 28 in the 780 grid; Bignor 28/.85 because the page draws it at 85%).
The page draws one fixed ring (.hdot) under the s of How it works and fades only these routes in and out.
Usage: python3 route_svgs.py <dir with line-0..4.svg> <out dir>"""
import re, math, sys, os
SRC, OUT = sys.argv[1], sys.argv[2]
for i in range(5):
    s = open(os.path.join(SRC, f"line-{i}.svg")).read()
    cx, cy = map(float, re.search(r'<circle cx="([\d.]+)" cy="([\d.]+)"', s).groups())
    rad = 28 / (.85 if i == 4 else 1)
    d = re.findall(r'<path d="([^"]+)"', s)[0]          # the drive starts at home
    n = list(map(float, re.findall(r'-?[\d.]+', d))); P = list(zip(n[0::2], n[1::2]))
    for j in range(1, len(P)):
        if math.dist(P[j], (cx, cy)) >= rad:
            a, b = P[j-1], P[j]; da, db = math.dist(a, (cx, cy)), math.dist(b, (cx, cy)); t = (rad-da)/(db-da) if db != da else 0
            P = [(a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)] + P[j:]; break
    out = s.replace(d, 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in P), 1)
    open(os.path.join(OUT, f"route-{i}.svg"), "w").write(re.sub(r'<circle[^>]*/>', '', out))
