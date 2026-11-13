import json,math,networkx as nx
from shapely.geometry import Polygon,Point,LineString
d=json.load(open('osm2.json'))
LAT0=51.400; LON0=-0.220; KX=111320*math.cos(math.radians(LAT0)); KY=111200
def m(p): return ((p[0]/1e5-LON0)*KX,(p[1]/1e5-LAT0)*KY)
park=[w for w in d if w.get('n')=='Cannon Hill Common' and w['k']=='lei:park'][0]
P=Polygon([m(p) for p in park['p']]).buffer(20)
FOOT={'hw:footway','hw:path','hw:cycleway','hw:track','hw:bridleway'}
G=nx.Graph(); pos={}
for w in d:
    if w['k'] in FOOT and 'nd' in w and len(w['nd'])==len(w['p']):
        pts=[m(p) for p in w['p']]
        for i,(a,b) in enumerate(zip(w['nd'],w['nd'][1:])):
            pa,pb=pts[i],pts[i+1]
            if P.contains(Point(pa)) and P.contains(Point(pb)):
                G.add_edge(a,b,w=math.dist(pa,pb)); pos[a]=pa; pos[b]=pb
print('nodes',G.number_of_nodes(),'edges',G.number_of_edges(),'comps',[len(c) for c in nx.connected_components(G)])
G=G.subgraph(max(nx.connected_components(G),key=len)).copy()
K=nx.k_core(G,2)
print('2core',K.number_of_nodes())
# faces via angular ordering
def ang(u,v): return math.atan2(pos[v][1]-pos[u][1],pos[v][0]-pos[u][0])
nbr={u:sorted(K[u],key=lambda v:ang(u,v)) for u in K}
seen=set(); faces=[]
for u in K:
    for v in K[u]:
        if (u,v) in seen: continue
        f=[]; a,b=u,v
        while (a,b) not in seen:
            seen.add((a,b)); f.append(a)
            L=nbr[b]; i=L.index(a); c=L[(i-1)%len(L)]  # next edge: clockwise turn
            a,b=b,c
        faces.append(f)
def area(f): return sum(pos[f[i]][0]*pos[f[(i+1)%len(f)]][1]-pos[f[(i+1)%len(f)]][0]*pos[f[i]][1] for i in range(len(f)))/2
faces.sort(key=lambda f:abs(area(f)),reverse=True)
outer=faces[0]; print('outer len',len(outer),'area',area(outer), 'unique',len(set(outer)))
L=sum(math.dist(pos[outer[i]],pos[outer[(i+1)%len(outer)]]) for i in range(len(outer))); print('length m',round(L))
json.dump({'loop':[[round(pos[n][0],1),round(pos[n][1],1)] for n in outer],'nodes':outer},open('loop_raw.json','w'))
