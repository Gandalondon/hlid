import json,math
from shapely.geometry import box,Polygon,LineString,Point
d=json.load(open('osm2.json')); R=json.load(open('relief.json')); lp=json.load(open('loop_raw.json'))['loop']
LAT0=51.400; LON0=-0.220; KX=111320*math.cos(math.radians(LAT0)); KY=111200
def m(p): return ((p[0]/1e5-LON0)*KX,(p[1]/1e5-LAT0)*KY)
X0,Y0,X1,Y1=R['box']; B=box(X0,Y0,X1,Y1)
# loop: start at the most northerly point, go clockwise
if sum(lp[i][0]*lp[(i+1)%len(lp)][1]-lp[(i+1)%len(lp)][0]*lp[i][1] for i in range(len(lp)))>0: lp=lp[::-1]  # make clockwise (negative area)
i0=max(range(len(lp)),key=lambda i:lp[i][1]); lp=lp[i0:]+lp[:i0]+[lp[i0]]
L=sum(math.dist(a,b) for a,b in zip(lp,lp[1:])); print('loop m',round(L),'start',lp[0], 'lonlat',LON0+lp[0][0]/KX,LAT0+lp[0][1]/KY)
F={'wood':[],'water':[],'bld':[],'path':[],'road':[],'rail':[]}
def rnd(c): return [[round(x,1),round(y,1)] for x,y in c]
for w in d:
    k=w['k']; pts=[m(p) for p in w['p']]
    if len(pts)<2: continue
    if k in('nat:wood','nat:scrub','lei:nature_reserve') or k=='lu:forest': cls='wood'
    elif k=='nat:water': cls='water'
    elif k=='bld': cls='bld'
    elif k in('hw:footway','hw:path','hw:cycleway','hw:track','hw:bridleway','hw:steps','hw:pedestrian'): cls='path'
    elif k.startswith('hw:') and k not in ('hw:service',): cls='road'
    elif k=='hw:service': cls='path'
    elif k=='rw:rail': cls='rail'
    else: continue
    if cls in('wood','water','bld'):
        if len(pts)<4: continue
        g=Polygon(pts)
        if not g.is_valid: g=g.buffer(0)
        g=g.intersection(B)
        if g.is_empty: continue
        geoms=getattr(g,'geoms',[g])
        for gg in geoms:
            if gg.geom_type=='Polygon': F[cls].append(rnd(gg.exterior.coords))
    else:
        g=LineString(pts).intersection(B)
        if g.is_empty: continue
        for gg in getattr(g,'geoms',[g]):
            if gg.geom_type=='LineString': F[cls].append(rnd(gg.coords))
for k in F: print(k,len(F[k]))
out={'name':'Cannon Hill Common','lat0':LAT0,'lon0':LON0,'kx':KX,'ky':KY,'loop':rnd(lp),'len':round(L),'relief':R,'f':F}
s=json.dumps(out,separators=(',',':')); open('test_walk.json','w').write(s); print('bytes',len(s))
