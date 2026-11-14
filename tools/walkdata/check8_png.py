"""Quick look at the build 8 loops: python3 tools/walkdata/check8_png.py -> data/testwalk/check8-<id>.png"""
import json,os,io,base64
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from PIL import Image
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D=json.load(open(os.path.join(ROOT,"data/testwalk/walks8.json")))
for w in D["walks"]:
    xs=[p[0] for p in w["loop"]]; ys=[p[1] for p in w["loop"]]; pad=250
    fig,ax=plt.subplots(figsize=(10,10),dpi=110)
    X0,Y0,X1,Y1=w["relief"]["box"]; im=Image.open(io.BytesIO(base64.b64decode(w["relief"]["uri"].split(",")[1])))
    ax.imshow(im,extent=(X0,X1,Y0,Y1),cmap="gray",vmin=0,vmax=255)
    for c in w["f"]["wood"]: ax.fill(*zip(*c),color="#1A1A1A",alpha=0.06,lw=0)
    for c in w["con"]["c"]: ax.plot(*zip(*c),color="#C9C9C9",lw=0.6)
    for c in w["con"]["i"]: ax.plot(*zip(*c),color="#A8A8A8",lw=0.9)
    for c in w["f"]["road"]: ax.plot(*zip(*c),color="#BDBDBD",lw=2.5)
    for c in w["f"]["path"]: ax.plot(*zip(*c),color="#5C5C5C",lw=0.9,ls=(0,(4,3)))
    ax.plot(xs,ys,color="#1A1A1A",lw=3.5,alpha=0.85); ax.plot(xs[0],ys[0],"o",ms=12,color="#1A1A1A",mec="w",mew=2)
    for k in range(0,len(xs)-1,max(1,len(xs)//12)): ax.annotate("",xy=(xs[k+1],ys[k+1]),xytext=(xs[k],ys[k]),arrowprops=dict(arrowstyle="->",color="#E8642A",lw=2))
    ax.set_xlim(min(xs)-pad,max(xs)+pad); ax.set_ylim(min(ys)-pad,max(ys)+pad); ax.set_aspect("equal"); ax.set_title(f"{w['name']}  {w['len']/1000:.2f} km"); ax.axis("off")
    fig.savefig(os.path.join(ROOT,f"data/testwalk/check8-{w['id']}.png"),bbox_inches="tight"); plt.close(fig)
print("ok")
