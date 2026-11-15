"""Render frame.html frame by frame. python3 render.py stills 2.8 4.8 ...  |  python3 render.py full  -> out/hlid-trailer-16x9.mp4"""
import sys, os, subprocess
from playwright.sync_api import sync_playwright
D=os.path.dirname(os.path.abspath(__file__)); FPS=30; DUR=15.0
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=["--allow-file-access-from-files"]); VERT='v' in os.environ.get('Q',''); pg=b.new_page(viewport={'width':1080,'height':1920} if VERT else {'width':1920,'height':1080})
    Q=os.environ.get('Q',''); pg.goto('file://'+D+'/frame.html'+Q); pg.wait_for_function('window.READY===true')
    if sys.argv[1]=="stills":
        os.makedirs(D+'/stills',exist_ok=True)
        for t in sys.argv[2:]:
            pg.evaluate(f'draw({t})'); pg.screenshot(path=f'{D}/stills/t{t}.jpg',type='jpeg',quality=92)
    else:
        os.makedirs(D+'/out',exist_ok=True); NAME=os.environ.get('NAME','hlid-trailer-16x9'); tmp=D+'/out/'+NAME+'.tmp.mp4'
        ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',tmp],stdin=subprocess.PIPE)
        DUR=pg.evaluate('window.DUR'); print('dur',DUR)
        for i in range(int(round(DUR*FPS))):
            pg.evaluate(f'draw({i/FPS})'); ff.stdin.write(pg.screenshot(type='jpeg',quality=92))
        ff.stdin.close(); assert ff.wait()==0; os.replace(tmp,D+'/out/'+NAME+'.mp4'); print('done')
    b.close()
