import numpy as np, math, io, base64, json
from scipy.ndimage import map_coordinates, gaussian_filter
from pyproj import Transformer
from PIL import Image
LAT0=51.400; LON0=-0.220; KX=111320*math.cos(math.radians(LAT0)); KY=111200
TR=Transformer.from_crs("EPSG:4326","EPSG:27700",always_xy=True)
tiles=[]
for f in ['t50/TQ26.asc','t50/TQ27.asc']:
    fh=open(f); h={}
    for _ in range(5): k,v=fh.readline().split(); h[k]=float(v)
    tiles.append((h,np.loadtxt(fh)))
x0=520000; y1=180000; M=np.zeros((400,200))
for h,a in tiles:
    r=int((y1-(h['yllcorner']+200*50))/50); M[r:r+200,:]=a
# metre box (x east, y north) around the common
X0,X1,Y0,Y1=-900,700,-700,800
ppm=0.5; w=int((X1-X0)*ppm); hgt=int((Y1-Y0)*ppm); ss=2
xs=np.linspace(X0,X1,w*ss); ys=np.linspace(Y1,Y0,hgt*ss); X,Y=np.meshgrid(xs,ys)
lon=LON0+X/KX; lat=LAT0+Y/KY; e,n=TR.transform(lon,lat)
Z=map_coordinates(M,[(y1-n)/50-0.5,(e-x0)/50-0.5],order=3,mode='nearest')
px=1/(ppm*ss); Z=gaussian_filter(Z,sigma=60/px)
print('height range',Z.min(),Z.max(), np.percentile(Z,[10,50,90]))
BREAKS=json.loads(__import__('sys').argv[1]) if len(__import__('sys').argv)>1 else [20,25,30,35]
GREYS=[0xF0,0xE5,0xDA,0xCF,0xC4]
G=np.array(GREYS,float)[np.digitize(Z,BREAKS)]
dzdy,dzdx=np.gradient(Z,px)
alt=math.radians(45); az=math.radians(315)
L=[math.cos(alt)*math.sin(az), math.cos(alt)*math.cos(az), math.sin(alt)]
sh=(-dzdx*L[0]+dzdy*L[1]+L[2])/np.sqrt(dzdx**2+dzdy**2+1); sh=gaussian_filter(sh,2)
G=np.clip(G*(1+0.30*(sh-L[2])),0,255).astype(np.uint8)
im=Image.fromarray(G,'L').resize((w,hgt),Image.LANCZOS); im.save('relief.png',optimize=True)
b=io.BytesIO(); im.save(b,'PNG',optimize=True)
json.dump({'uri':'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode(),'box':[X0,Y0,X1,Y1]},open('relief.json','w'))
print(len(b.getvalue()))
