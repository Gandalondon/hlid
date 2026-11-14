"""Hlid portfolio pairs: two app screens in the Pixel frame, same canvas (3560 x 1717), phone size and spacing as the Relay/Woden pairs.
The frame is reused from an existing pair image (frame colour fill, 52 px screen corners), so no Relay files are needed.
Usage: python3 folio_pairs.py <base pair jpg> <screens dir (390x844 renders)> <out dir>"""
import sys, os
from PIL import Image, ImageDraw
BASE, SCR, OUT = sys.argv[1:4]
PAIRS={"hlid_pair-start":["today-1","today-2+drive"],"hlid_pair-today":["today-3","today-4"],"hlid_pair-walk":["carpark","walking"],"hlid_pair-end":["done","pub"]}
W,H,PW,STEP=3560,1717,837.457,907.514; x0=(W-(STEP+PW))/2
SX,SY,SW,SH,R=44.077,42.073,751.307,1626.830,52
S=4
base=Image.open(BASE).convert("RGB")
for name,shots in PAIRS.items():
    im=base.copy()
    for i,s in enumerate(shots):
        L=x0+i*STEP+SX
        box=(round(L),round(SY),round(L+SW),round(SY+SH)); w,h=box[2]-box[0],box[3]-box[1]
        shot=Image.open(os.path.join(SCR,s+".png")).convert("RGB").resize((w,h),Image.LANCZOS)
        m=Image.new("L",(w*S,h*S),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w*S-1,h*S-1),radius=R*S,fill=255); m=m.resize((w,h),Image.LANCZOS)
        im.paste(shot,box[:2],m)
    im.save(os.path.join(OUT,name+".jpg"),quality=90); print(name)
