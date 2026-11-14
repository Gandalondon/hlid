"""Cut small areas out of the GB OSM extract (data/gb/great-britain-latest.osm.pbf) into JSON, for building walks and maps.
Usage (from ~/Hlid): python3 tools/walkdata/extract_areas.py [area]  -> data/areas/<name>.json
Two passes: nodes in the boxes, then ways and relations that use them. Needs: pip3 install --user osmium"""
import osmium, json, os, sys, time
AREAS={  # name: (south, west, north, east)
 "cannon-morden": (51.383, -0.245, 51.412, -0.185),
 "ranmore": (51.215, -0.405, 51.272, -0.320),
 "chanctonbury": (50.870, -0.430, 50.925, -0.340),   # demo walk on the site and in the prototype
}
# County extracts from Geofabrik (fast, each run fits in one shell call). Falls back to the GB file.
SOURCE={"cannon-morden":"greater-london-latest.osm.pbf","ranmore":"surrey-latest.osm.pbf","chanctonbury":"west-sussex-latest.osm.pbf"}
ONLY=sys.argv[1:]  # e.g. python3 extract_areas.py ranmore
if ONLY: AREAS={k:v for k,v in AREAS.items() if k in ONLY}
KEYS=("highway","landuse","natural","leisure","amenity","waterway","building","railway","designation","access","foot","name","fee","parking","route","type","surface","sac_scale","barrier","prow_ref","ref","informal","footway","trail_visibility","tracktype","natural","water","wetland")
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_src={SOURCE.get(k,"great-britain-latest.osm.pbf") for k in AREAS}
PBF=os.path.join(ROOT,"data","gb",_src.pop() if len(_src)==1 else "great-britain-latest.osm.pbf"); OUT=os.path.join(ROOT,"data","areas"); os.makedirs(OUT,exist_ok=True)
S=min(a[0] for a in AREAS.values()); W=min(a[1] for a in AREAS.values()); N=max(a[2] for a in AREAS.values()); E=max(a[3] for a in AREAS.values())
nodes={}; nodetags={}
class NH(osmium.SimpleHandler):
    def node(self,n):
        l=n.location
        if not l.valid(): return
        lat,lon=l.lat,l.lon
        if S<=lat<=N and W<=lon<=E:
            for k,(s,w,nn,e) in AREAS.items():
                if s<=lat<=nn and w<=lon<=e:
                    nodes[n.id]=(round(lon,6),round(lat,6))
                    if n.tags: nodetags[n.id]={t.k:t.v for t in n.tags if t.k in KEYS}
                    break
t=time.time(); NH().apply_file(PBF); print("nodes",len(nodes),round(time.time()-t),"s",flush=True)
ways={}; rels=[]
class WH(osmium.SimpleHandler):
    def way(self,w):
        refs=[r.ref for r in w.nodes]
        if not any(r in nodes for r in refs[:: max(1,len(refs)//8)]+refs[-1:]): return
        tg={t.k:t.v for t in w.tags if t.k in KEYS}
        if not tg: return
        ways[w.id]={"t":tg,"nd":refs,"p":[nodes.get(r) for r in refs]}
    def relation(self,r):
        tg={t.k:t.v for t in r.tags}
        if tg.get("type") in ("route","multipolygon") and any(m.type=="w" and m.ref in ways for m in r.members):
            rels.append({"id":r.id,"t":{k:v for k,v in tg.items() if k in KEYS or k in ("route","network","operator")},"m":[[m.type,m.ref,m.role] for m in r.members]})
t=time.time(); WH().apply_file(PBF,locations=False); print("ways",len(ways),"rels",len(rels),round(time.time()-t),"s",flush=True)
for k,(s,w,n,e) in AREAS.items():
    def inb(p): return p and s<=p[1]<=n and w<=p[0]<=e
    wk={i:v for i,v in ways.items() if any(inb(p) for p in v["p"])}
    rk=[r for r in rels if any(m[0]=="w" and m[1] in wk for m in r["m"])]
    nt={i:v for i,v in nodetags.items() if inb(nodes[i])}
    json.dump({"box":[s,w,n,e],"ways":wk,"rels":rk,"nodetags":{i:[nodes[i],v] for i,v in nt.items()}},open(os.path.join(OUT,k+".json"),"w"))
    print(k,len(wk),"ways",len(rk),"rels",flush=True)
print("done",flush=True)
