"""Build 8 test walks from OpenStreetMap footpaths only, with map style B data.
Run from ~/Hlid: python3 tools/walkdata/build8.py [walk ...]  -> data/testwalk/walks8.json + data/testwalk/check8.txt
Needs data/areas/*.json (tools/walkdata/extract_areas.py), OS Terrain 50 tiles in data/terr50, tokens.json.
Every loop is built only from foot ways (footway, path, bridleway, track, steps, pedestrian, cycleway; no pavements,
no informal paths, nothing private) and then checked metre by metre against those ways."""
import os, sys, json, math, io, base64, glob
import numpy as np, networkx as nx
from shapely.geometry import Polygon, LineString, Point, box, MultiLineString
from shapely.ops import polygonize, unary_union, linemerge
from shapely.strtree import STRtree
from scipy.ndimage import gaussian_filter, map_coordinates
from pyproj import Transformer
from PIL import Image
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOK=json.load(open(os.path.join(ROOT,"tokens.json"))); MAP=TOK["map"]
OUT=os.path.join(ROOT,"data","testwalk"); os.makedirs(OUT,exist_ok=True)

WALKS=[  # id, name, area, how, args
 {"id":"cannon-hill","name":"Cannon Hill Common","area":"cannon-morden","how":"park","park":699121062,"start":(51.40394,-0.21599)},
 {"id":"morden-park","name":"Morden Park","area":"cannon-morden","how":"park","park":23680892,"start":(51.39432,-0.20627)},
 {"id":"ranmore","name":"Ranmore Common","area":"ranmore","how":"carpark","km":(7,10),"prefer":[8127,5569381,20062671,20584203,20584204,20443504],"start":(51.25952,-0.34129)},
]
FOOT={"footway","path","bridleway","track","steps","pedestrian","cycleway"}
def is_foot(t):
    if t.get("informal")=="yes": return False
    if t.get("designation","").startswith(("public_footpath","public_bridleway","restricted_byway","byway","permissive")) or t.get("foot")=="designated":
        return True   # a right of way, even where OSM draws it as a farm or estate road
    if t.get("highway") not in FOOT: return False
    if t.get("footway") in ("sidewalk","crossing","traffic_island"): return False
    if t.get("informal")=="yes": return False
    if t.get("foot") in ("no","private"): return False
    if t.get("access") in ("private","no") and t.get("foot") not in ("yes","designated","permissive"): return False
    return True

TR=Transformer.from_crs("EPSG:4326","EPSG:27700",always_xy=True)
TILES={}
for f in glob.glob(os.path.join(ROOT,"data","terr50","*.asc")):
    fh=open(f); h={}
    for _ in range(5): k,v=fh.readline().split(); h[k]=float(v)
    TILES[(int(h["xllcorner"]),int(h["yllcorner"]))]=np.loadtxt(fh)
def heights_bng(e,n):
    e=np.asarray(e,float); n=np.asarray(n,float); z=np.zeros(e.shape)
    for (x0,y0),a in TILES.items():
        m=(e>=x0)&(e<x0+10000)&(n>=y0)&(n<y0+10000)
        if m.any(): z[m]=map_coordinates(a,[(y0+10000-n[m])/50-0.5,(e[m]-x0)/50-0.5],order=3,mode="nearest")
    return z

def carpark_loop(G,pos,A,W,pos_m):
    """A footpath-only loop from the car park: out to a far point, back a different way.
    Waymarked routes (W['prefer'] relations) count as shorter, paths already used count as much longer.
    Candidates are scored on length in range, how little the way back repeats the way out, and how much is waymarked."""
    lo,hi=W["km"][0]*1000,W["km"][1]*1000
    pref=set()
    for r in A["rels"]:
        if r["id"] in W.get("prefer",[]):
            for typ,ref,role in r["m"]:
                wy=A["ways"].get(str(ref))
                if typ=="w" and wy: pref.update(zip(wy["nd"],wy["nd"][1:]))
    # busy roads: paths within 40 m of an A or B road (or any road with a 40+ limit) cost 5x, so loops stay off verges
    big=[]
    for wy in A["ways"].values():
        if wy["t"].get("highway") in ("motorway","trunk","primary","secondary","tertiary","trunk_link","primary_link"):
            pts=[pos_m(p) for p in wy["p"] if p]
            if len(pts)>1: big.append(LineString(pts))
    bt=STRtree(big)
    for a,b,d in G.edges(data=True):
        mid=Point((pos[a][0]+pos[b][0])/2,(pos[a][1]+pos[b][1])/2)
        near=any(big[j].distance(mid)<40 for j in bt.query(mid.buffer(40)))
        d["c"]=d["w"]*(0.4 if (a,b) in pref or (b,a) in pref else 1.0)*(5 if near else 1)
    G0=G.subgraph(max(nx.connected_components(G),key=lambda c: 0 if not c else (1 if min(c,key=lambda n: math.hypot(*pos[n])) is None else -min(math.hypot(*pos[n]) for n in c)))).copy()
    S=min(G0.nodes,key=lambda n: math.hypot(*pos[n]))
    dS,pS=nx.single_source_dijkstra(G0,S,weight="c")
    best=None
    cands=[n for n,dd in dS.items() if lo*0.28<=dd<=hi*0.45]
    cands=cands[::max(1,len(cands)//400)]
    for F in cands:
        out=pS[F]; used=set(zip(out,out[1:]))|set(zip(out[1:],out))
        def cw(a,b,d): return d["c"]*(8 if (a,b) in used else 1)
        try: back=nx.dijkstra_path(G0,F,S,weight=cw)
        except nx.NetworkXNoPath: continue
        nodes=out+back[1:]
        L=sum(G0[a][b]["w"] for a,b in zip(nodes,nodes[1:]))
        if not (lo<=L<=hi): continue
        rep=sum(G0[a][b]["w"] for a,b in zip(back,back[1:]) if (a,b) in used)
        wm=sum(G0[a][b]["w"] for a,b in zip(nodes,nodes[1:]) if (a,b) in pref or (b,a) in pref)
        busy=sum(G0[a][b]["w"] for a,b in zip(nodes,nodes[1:]) if G0[a][b]["c"]>=4*G0[a][b]["w"])
        score=wm/L-2*rep/L-3*busy/L
        if not best or score>best[0]: best=(score,nodes,L,rep,wm)
    sc,nodes,L,rep,wm=best
    return nodes[:-1],f"  car park loop: {L/1000:.2f} km, waymarked {wm/L:.0%}, repeated {rep:.0f} m, {len(cands)} candidates tried"

def build(W,check):
    A=json.load(open(os.path.join(ROOT,"data","areas",W["area"]+".json")))
    ways=A["ways"]
    lat0,lon0=W["start"]; KX=111320*math.cos(math.radians(lat0)); KY=111200
    def m(p): return ((p[0]-lon0)*KX,(p[1]-lat0)*KY)
    # foot graph (only segments with both ends inside the extract)
    G=nx.Graph(); pos={}; footlines=[]
    for wid,w in ways.items():
        if not is_foot(w["t"]): continue
        seg=[]
        for nd,p in zip(w["nd"],w["p"]):
            if p is None: 
                if len(seg)>1: footlines.append(LineString([q for _,q in seg]))
                seg=[]; continue
            q=m(p); pos[nd]=q; seg.append((nd,q))
        if len(seg)>1: footlines.append(LineString([q for _,q in seg]))
        for (a,pa),(b,pb) in zip(zip(w["nd"],w["p"]),list(zip(w["nd"],w["p"]))[1:]):
            if pa and pb: G.add_edge(a,b,w=math.dist(m(pa),m(pb)),way=wid)
    if W["how"]=="park":
        pw=ways[str(W["park"])]; P=Polygon([m(p) for p in pw["p"] if p]).buffer(8)
        H=nx.Graph((a,b,d) for a,b,d in G.edges(data=True) if P.contains(Point(pos[a])) and P.contains(Point(pos[b])))
        H=H.subgraph(max(nx.connected_components(H),key=len)).copy(); K=nx.k_core(H,2)
        def ang(u,v): return math.atan2(pos[v][1]-pos[u][1],pos[v][0]-pos[u][0])
        nbr={u:sorted(K[u],key=lambda v:ang(u,v)) for u in K}; seen=set(); faces=[]
        for u in K:
            for v in K[u]:
                if (u,v) in seen: continue
                f=[]; a,b=u,v
                while (a,b) not in seen:
                    seen.add((a,b)); f.append(a); L=nbr[b]; i=L.index(a); c=L[(i-1)%len(L)]; a,b=b,c
                faces.append(f)
        def area(f): return sum(pos[f[i]][0]*pos[f[(i+1)%len(f)]][1]-pos[f[(i+1)%len(f)]][0]*pos[f[i]][1] for i in range(len(f)))/2
        outer=max(faces,key=lambda f:abs(area(f)))
        # the outer face can double back along spurs: keep the simple cycle through it
        nodes=outer
        # remove immediate back-and-forth (a,b,a)
        changed=True
        while changed:
            changed=False
            for i in range(2,len(nodes)+2):
                a,b=nodes[(i-2)%len(nodes)],nodes[i%len(nodes)]
                if len(nodes)>3 and a==b:
                    nodes=nodes[(i-1)%len(nodes):]+nodes[:(i-1)%len(nodes)]; nodes=nodes[2:]; changed=True; break
        loop=[pos[n] for n in nodes]; loopn=list(nodes)
    elif W["how"]=="carpark":
        loopn,info=carpark_loop(G,pos,A,W,m); check.append(info)
        loop=[pos[n] for n in loopn]
    else:
        rel=[r for r in A["rels"] if r["id"]==W["rel"]][0]
        mem=[str(mm[1]) for mm in rel["m"] if mm[0]=="w" and str(mm[1]) in ways and mm[2]!="approach"]
        notes=[]; chain=[]
        for wid in mem:
            w=ways[wid]; seq=[(nd,p) for nd,p in zip(w["nd"],w["p"]) if p]
            if not is_foot(w["t"]): notes.append(f"  relation way {wid} is {w['t'].get('highway') or w['t']} ({w['t'].get('name','')}): rerouted on footpaths if possible")
            if not chain: chain=seq; continue
            if chain[-1][0]==seq[0][0]: chain+=seq[1:]
            elif chain[-1][0]==seq[-1][0]: chain+=seq[::-1][1:]
            elif chain[0][0]==seq[-1][0] and len(chain)==len(ways[mem[0]]["nd"]): chain=chain[::-1]+seq[::-1][1:]
            elif chain[0][0]==seq[0][0] and len(chain)==len(ways[mem[0]]["nd"]): chain=chain[::-1]+seq[1:]
            else:
                # gap: join on footpaths
                try:
                    a=chain[-1][0]; b=min((seq[0][0],seq[-1][0]),key=lambda n: nx.shortest_path_length(G,a,n,weight="w") if n in G and a in G and nx.has_path(G,a,n) else 1e9)
                    sp=nx.shortest_path(G,a,b,weight="w"); chain+=[(n,None) for n in sp[1:]]
                    chain+= (seq[1:] if b==seq[0][0] else seq[::-1][1:]); notes.append(f"  gap before way {wid} joined on footpaths ({len(sp)} nodes)")
                except Exception as e: notes.append(f"  gap before way {wid} could not be joined: {e}")
        nodes=[nd for nd,_ in chain]
        nodeway={}
        for wid in mem:
            for nd in ways[wid]["nd"]: nodeway.setdefault(nd,set()).add(ways[wid]["t"].get("name") or ways[wid]["t"].get("highway"))
        def ways_of(ns):
            out=[]
            for a,b in zip(ns,ns[1:]): out+=list(nodeway.get(a,set())&nodeway.get(b,set()))
            return out or ["?"]
        # every node needs a position, foot or not
        for wid in mem:
            for nd,p in zip(ways[wid]["nd"],ways[wid]["p"]):
                if p: pos[nd]=m(p)
        # reroute any stretch on a non-foot edge over footpaths
        out=[nodes[0]]; i=0
        while i<len(nodes)-1:
            a,b=nodes[i],nodes[i+1]
            if G.has_edge(a,b): out.append(b); i+=1; continue
            j=i+1
            while j<len(nodes)-1 and not G.has_edge(nodes[j],nodes[j+1]): j+=1
            s,t=nodes[i],nodes[j]; road=sum(math.dist(pos.get(nodes[k]) or (0,0),pos.get(nodes[k+1]) or (0,0)) for k in range(i,j)) if all(n in pos for n in nodes[i:j+1]) else None
            sp=None
            if s in G and t in G and nx.has_path(G,s,t):
                sp=nx.shortest_path(G,s,t,weight="w"); L=nx.path_weight(G,sp,"w")
                if road is not None and L>max(2*road,road+300): sp=None
            if road is not None and road<=80 and sp is None:
                notes.append(f"  road crossing {i}-{j}: {round(road)} m on {', '.join(sorted(set(ways_of(nodes[i:j+1]))))}"); out+=nodes[i+1:j+1]
            elif sp:
                notes.append(f"  {round(road or 0)} m of road replaced by {round(L)} m of footpath"); out+=sp[1:]
            else: notes.append(f"  KEPT {round(road or 0)} m on road ({', '.join(sorted(set(ways_of(nodes[i:j+1]))))}): no footpath within 2x"); out+=nodes[i+1:j+1]
            i=j
        loopn=out
        # start at the point nearest the car park
        k=min(range(len(loopn)),key=lambda k: math.hypot(*pos[loopn[k]]) if loopn[k] in pos else 1e9)
        if loopn[0]==loopn[-1]: loopn=loopn[:-1]
        loopn=loopn[k:]+loopn[:k]
        loop=[pos[n] for n in loopn if n in pos]
        check.extend(notes)
    if W["how"] in ("park","carpark"):
        # start where the loop is nearest the start point (car park)
        k=min(range(len(loop)),key=lambda k: math.hypot(*loop[k])); loop=loop[k:]+loop[:k]; loopn=loopn[k:]+loopn[:k]
        if sum(loop[i][0]*loop[(i+1)%len(loop)][1]-loop[(i+1)%len(loop)][0]*loop[i][1] for i in range(len(loop)))>0: loop=[loop[0]]+loop[1:][::-1]; loopn=[loopn[0]]+loopn[1:][::-1]
    loop=loop+[loop[0]]; loopn=loopn+[loopn[0]]
    LEN=sum(math.dist(a,b) for a,b in zip(loop,loop[1:]))
    # ---- every-metre check: each metre of the loop must lie on a foot way (within 2 m of its line) ----
    tree=STRtree(footlines); line=LineString(loop); n=int(LEN); bad=0; worst=0; badruns=[]
    edges_ok=sum(1 for a,b in zip(loopn,loopn[1:]) if G.has_edge(a,b)); 
    for s in range(n+1):
        p=line.interpolate(s); idx=tree.query(p.buffer(3)); d=min((footlines[j].distance(p) for j in idx),default=99)
        worst=max(worst,d)
        if d>2: bad+=1
    check.append(f"{W['name']}: {LEN/1000:.2f} km, {len(loop)} points, edges on foot ways {edges_ok}/{len(loopn)-1}, metres off a path {bad}/{n+1}, worst {worst:.1f} m, start {lat0},{lon0}")
    # ---- map area: loop bbox + 1.5 km ----
    xs=[p[0] for p in loop]; ys=[p[1] for p in loop]; MG=1500
    X0,X1,Y0,Y1=min(xs)-MG,max(xs)+MG,min(ys)-MG,max(ys)+MG; B=box(X0,Y0,X1,Y1)
    # relief (style B: flat land + soft shade), 0.25 px per metre
    ppm=0.25; w=int((X1-X0)*ppm); hgt=int((Y1-Y0)*ppm)
    gx=np.linspace(X0,X1,w); gy=np.linspace(Y1,Y0,hgt); GX,GY=np.meshgrid(gx,gy)
    e,nn=TR.transform(lon0+GX/KX,lat0+GY/KY); Z=gaussian_filter(heights_bng(e,nn),sigma=60*ppm)
    px=1/ppm; dzdy,dzdx=np.gradient(Z,px); alt=math.radians(45); az=math.radians(315)
    Lv=[math.cos(alt)*math.sin(az),math.cos(alt)*math.cos(az),math.sin(alt)]
    sh=(-dzdx*Lv[0]+dzdy*Lv[1]+Lv[2])/np.sqrt(dzdx**2+dzdy**2+1); sh=gaussian_filter(sh,1.5)-Lv[2]
    land=int(MAP["land"][1:3],16); Gm=np.clip(land*(1+MAP["shade"]*sh),0,255).astype(np.uint8)
    im=Image.fromarray(Gm,"L"); b=io.BytesIO(); im.save(b,"PNG",optimize=True)
    im.save(os.path.join(OUT,f"relief8-{W['id']}.png"))
    relief={"uri":"data:image/png;base64,"+base64.b64encode(b.getvalue()).decode(),"box":[round(X0),round(Y0),round(X1),round(Y1)]}
    # contours every 10 m (index every 50 m), y north
    cs=plt.contour(gx,gy,Z,levels=np.arange(math.floor(Z.min()/10)*10,Z.max()+10,MAP["contour_step"]))
    con={"c":[],"i":[]}
    for lev,segs in zip(cs.levels,cs.allsegs):
        for s_ in segs:
            if len(s_)<3: continue
            ls=LineString(s_).simplify(3)
            if ls.length<40: continue
            con["i" if lev%MAP["index_step"]==0 else "c"].append([[round(x,1),round(y,1)] for x,y in ls.coords])
    plt.close("all")
    # features
    F={"wood":[],"water":[],"bld":[],"path":[],"road":[],"rail":[]}
    def rnd(c): return [[round(x,1),round(y,1)] for x,y in c]
    def add_poly(cls,g):
        g=g.intersection(B)
        for gg in getattr(g,"geoms",[g]):
            if gg.geom_type=="Polygon" and gg.area>50: F[cls].append(rnd(gg.simplify(1.5).exterior.coords))
    def add_line(cls,g):
        g=g.intersection(B)
        for gg in getattr(g,"geoms",[g]):
            if gg.geom_type=="LineString": F[cls].append(rnd(gg.simplify(1).coords))
    def poly_cls(t):
        if t.get("natural") in ("wood","scrub") or t.get("landuse")=="forest": return "wood"
        if t.get("natural")=="water" or t.get("waterway")=="riverbank" or t.get("landuse") in ("reservoir","basin"): return "water"
        if "building" in t: return "bld"
    for wid,wy in ways.items():
        t=wy["t"]; segs=[]; cur=[]
        for p in wy["p"]:
            if p is None:
                if len(cur)>1: segs.append(cur)
                cur=[]
            else: cur.append(m(p))
        if len(cur)>1: segs.append(cur)
        if not segs: continue
        pc=poly_cls(t)
        if pc and wy["nd"][0]==wy["nd"][-1] and len(segs)==1 and len(segs[0])>=4:
            g=Polygon(segs[0]); g=g if g.is_valid else g.buffer(0); add_poly(pc,g); continue
        h=t.get("highway")
        if h:
            cls="path" if is_foot(t) else ("road" if h not in ("service","footway","path","steps","proposed","construction","platform","corridor") else None)
            if cls:
                for sg in segs: add_line(cls,LineString(sg))
        elif t.get("railway")=="rail":
            for sg in segs: add_line("rail",LineString(sg))
    for r in A["rels"]:
        if r["t"].get("type")!="multipolygon": continue
        pc=poly_cls(r["t"])
        if not pc: continue
        ls=[]
        for typ,ref,role in r["m"]:
            wy=ways.get(str(ref))
            if typ=="w" and wy and role in ("outer",""):
                pts=[m(p) for p in wy["p"] if p]
                if len(pts)>1: ls.append(LineString(pts))
        for g in polygonize(unary_union(ls)): add_poly(pc,g)
    # elevation profile every 20 m
    st=np.arange(0,LEN,20); pts=[line.interpolate(s) for s in st]+[line.interpolate(LEN)]
    e,nn=TR.transform([lon0+p.x/KX for p in pts],[lat0+p.y/KY for p in pts])
    prof=gaussian_filter(heights_bng(e,nn),4)  # about 80 m: the 50 m terrain grid is noisy step to step
    climb=float(np.sum(np.clip(np.diff(prof),0,None)))
    check.append(f"  height {prof.min():.0f}-{prof.max():.0f} m, climb about {climb:.0f} m; contours {len(con['c'])}+{len(con['i'])}; paths {len(F['path'])}, roads {len(F['road'])}, woods {len(F['wood'])}")
    return {"id":W["id"],"name":W["name"],"lat0":lat0,"lon0":lon0,"kx":KX,"ky":KY,"loop":rnd(loop),"len":round(LEN),
            "prof":{"step":20,"h":[round(float(v),1) for v in prof]},"relief":relief,"con":con,"f":F}

if __name__=="__main__":
    only=sys.argv[1:]; check=[]; out=[]
    prev=os.path.join(OUT,"walks8.json")
    keep={w["id"]:w for w in json.load(open(prev))["walks"]} if (only and os.path.exists(prev)) else {}
    for W in WALKS:
        if only and W["id"] not in only: out.append(keep[W["id"]]) if W["id"] in keep else None; continue
        out.append(build(W,check)); print(check[-2] if len(check)>1 else "", flush=True)
    s=json.dumps({"walks":out},separators=(",",":")); open(prev,"w").write(s)
    open(os.path.join(OUT,"check8.txt"),"w").write("\n".join(check)+"\n"); print("\n".join(check)); print("bytes",len(s))
