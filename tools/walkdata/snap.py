"""Snap a demo loop from routes.py onto OSM foot ways, so every metre is on a path.
Run from ~/Hlid: python3 tools/walkdata/snap.py chanctonbury  -> data/routes_snapped.json (routes.py picks it up)"""
import os, sys, json, math
import networkx as nx
from shapely.geometry import LineString
from shapely.strtree import STRtree
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0,ROOT); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
os.environ["HLID_NO_SNAP"]="1"
import routes
from build8 import is_foot
key=sys.argv[1]; area=sys.argv[2] if len(sys.argv)>2 else key
A=json.load(open(os.path.join(ROOT,"data","areas",area+".json")))
old=routes.parse(routes.LOOPS[key]); lat0=old[0][1]; lon0=old[0][0]; KX=111320*math.cos(math.radians(lat0)); KY=111200
def m(p): return ((p[0]-lon0)*KX,(p[1]-lat0)*KY)
G=nx.Graph(); pos={}; ll={}; lines=[]
for w in A["ways"].values():
    if not is_foot(w["t"]): continue
    for (a,pa),(b,pb) in zip(zip(w["nd"],w["p"]),list(zip(w["nd"],w["p"]))[1:]):
        if pa and pb: pos[a]=m(pa); pos[b]=m(pb); ll[a]=pa; ll[b]=pb; G.add_edge(a,b,w=math.dist(m(pa),m(pb))); lines.append(LineString([m(pa),m(pb)]))
nodes=list(pos); tree=STRtree([LineString([pos[n],pos[n]]) for n in nodes])
oldm=[m(p) for p in old]; L0=LineString(oldm)
samp=[L0.interpolate(s) for s in range(0,int(L0.length),80)]+[L0.interpolate(L0.length)]
wp=[]
for p in samp:
    j=tree.nearest(p); n=nodes[j]
    if math.dist(pos[n],(p.x,p.y))<80 and (not wp or wp[-1]!=n): wp.append(n)
# off-path detour cost: prefer staying near the old line
for a,b,d in G.edges(data=True):
    mid=LineString([pos[a],pos[b]]).interpolate(0.5,normalized=True); d["c"]=d["w"]*(1+L0.distance(mid)/40)
path=[wp[0]]
for a,b in zip(wp,wp[1:]): path+=nx.shortest_path(G,a,b,weight="c")[1:]
# drop out-and-back spurs (a b a)
ch=True
while ch:
    ch=False
    for i in range(1,len(path)-1):
        if path[i-1]==path[i+1]: del path[i:i+2]; ch=True; break
pts=[pos[n] for n in path]; L=sum(math.dist(a,b) for a,b in zip(pts,pts[1:]))
on=sum(1 for a,b in zip(path,path[1:]) if G.has_edge(a,b))
far=max(L0.distance(LineString([p,p])) for p in pts)
print(f"{key}: old {L0.length/1000:.2f} km, snapped {L/1000:.2f} km, edges on foot ways {on}/{len(path)-1}, furthest from old line {far:.0f} m, gap start-end {math.dist(pts[0],pts[-1]):.0f} m")
f=os.path.join(ROOT,"data","routes_snapped.json"); D=json.load(open(f)) if os.path.exists(f) else {}
D[key]=" ".join(f"{ll[n][0]:.5f},{ll[n][1]:.5f}" for n in path); json.dump(D,open(f,"w"),indent=0)
