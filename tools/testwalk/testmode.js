/* ===== Woden test walk: Cannon Hill Common (APK only; in a browser add ?test to try it with taps as GPS).
   Real loop from OpenStreetMap (footpaths round the common, 1.9 km), OS Terrain 50 shading, live GPS, compass heading-up,
   km to go along the route, GPS trace saved as GPX to Downloads/Woden. Screens: t-today, t-start, t-walk, t-done. ===== */
(function(){
  var N=window.WodenNative, SIM=!N&&/[?&]test/.test(location.search);
  if(!N&&!SIM) return;
  var D=JSON.parse(document.getElementById("w4walk").textContent);
  var view=document.getElementById("view"), INK="#1A1A1A", LAND="#F0F0EE", WALKED="#8C8C88", NS="http://www.w3.org/2000/svg";
  var LOOP=D.loop, CUM=[0]; for(var i=1;i<LOOP.length;i++) CUM.push(CUM[i-1]+Math.hypot(LOOP[i][0]-LOOP[i-1][0],LOOP[i][1]-LOOP[i-1][1]));
  var LEN=CUM[CUM.length-1];
  var st={me:null,acc:null,head:null,perm:null,prog:0,walking:false,t0:0,trace:[],arrived:false,back:false,file:""};
  function m2ll(x,y){ return [D.lat0+y/D.ky, D.lon0+x/D.kx]; }
  function ll2m(lat,lon){ return [(lon-D.lon0)*D.kx,(lat-D.lat0)*D.ky]; }
  function nb(s){ return s.replace(/ (km|m|min)\b/g," $1"); }
  function dist(m){ return m>=1000? (m/1000).toFixed(1)+" km" : (Math.max(10,Math.round(m/10)*10))+" m"; }

  /* ---------- map layers, built once in metres (x east, y south) ---------- */
  function d(lines,close){ var s=""; lines.forEach(function(l){ s+="M"+l.map(function(p){ return p[0]+" "+(-p[1]); }).join("L")+(close?"Z":""); }); return s; }
  var F=D.f, R=D.relief;
  var BASE='<image href="'+R.uri+'" x="'+R.box[0]+'" y="'+(-R.box[3])+'" width="'+(R.box[2]-R.box[0])+'" height="'+(R.box[3]-R.box[1])+'" preserveAspectRatio="none"/>'+
    '<path d="'+d(F.wood,1)+'" fill="'+INK+'" fill-opacity="0.06"/>'+
    '<path d="'+d(F.bld,1)+'" fill="'+INK+'" fill-opacity="0.07"/>'+
    '<path d="'+d(F.water,1)+'" fill="#FFFFFF"/>'+
    '<path d="'+d(F.path,0)+'" fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'+
    '<path d="'+d(F.road,0)+'" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>';
  var LOOPD=d([LOOP],0);
  function routeLayers(id){ return '<path class="'+id+'-ahead" d="'+LOOPD+'" fill="none" stroke="'+INK+'" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'+
    '<path class="'+id+'-done" d="" fill="none" stroke="'+WALKED+'" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'; }
  var START='<circle cx="'+LOOP[0][0]+'" cy="'+(-LOOP[0][1])+'" r="8" fill="'+INK+'" stroke="#FFFFFF" stroke-width="3" vector-effect="non-scaling-stroke" class="tstart"/>';
  var ARROW='<path d="M0 -20 L16 20 L0 12 L-16 20 Z" fill="'+INK+'" stroke="#FFFFFF" stroke-width="3" stroke-linejoin="round"/>';
  var DOT='<circle r="9" fill="'+INK+'" stroke="#FFFFFF" stroke-width="3"/>';

  /* ---------- screens ---------- */
  var BACK='<svg class="ic" width="24" height="24" viewBox="0 -960 960 960" aria-hidden="true"><path fill="currentColor" d="m274-450 227 227q9 9 9 21t-9 21q-9 9-21 9t-21-9L181-459q-5-5-7-10t-2-11q0-6 2-11t7-10l278-278q9-9 21-9t21 9q9 9 9 21t-9 21L274-510h496q13 0 21.5 8.5T800-480q0 13-8.5 21.5T770-450H274Z"></path></svg>';
  var BTN='width: 100%; height: 56px; border: 0; border-radius: 999px; background: '+INK+'; color: #FFFFFF; font-size: 18px';
  var TBTN='width: 100%; height: 48px; border: 0; background: transparent; color: '+INK+'; font-size: 18px';
  var COL='padding: 24px 24px 32px; display: flex; flex-direction: column; gap: 12px; flex: none';
  var H1='margin: 0; font-size: 32px';
  var P='margin: 0; font-size: 16px; line-height: 1.5';
  var ROOT='width: 390px; height: 844px; box-sizing: border-box; background: #FFFFFF; font-family: Inter, sans-serif; color: '+INK+'; display: flex; flex-direction: column; position: relative; overflow: hidden';
  var CARDS=view.querySelector('.scr[data-id="today-1"] [data-go="walks"]').outerHTML;
  function sec(id,html){ var s=document.createElement("section"); s.className="scr"; s.dataset.id=id; s.dataset.t="1"; s.innerHTML=html; view.insertBefore(s,document.getElementById("sheet")); return s; }
  /* Today, test walk: the loop drawn like the Today line art, no drive */
  sec("t-today",'<div style="'+ROOT+'"><div class="cbar"><span class="sp"></span>'+CARDS+'</div>'+
    '<svg class="tmap" style="flex:1 1 auto;min-height:0;margin-top:96px" width="390" height="100%" role="img" aria-label="The walk loop round Cannon Hill Common"></svg>'+
    '<div style="'+COL+'; padding-top: 24px"><h1 style="'+H1+'; font-size: 44px">Cannon Hill Common</h1>'+
    '<p style="'+P+'">'+nb("No drive. "+(LEN/1000).toFixed(1)+" km walk. Test walk.")+'</p>'+
    '<button type="button" data-t="there" style="'+BTN+'; margin-top: 28px">Walk there</button>'+
    '<button type="button" data-t="another" style="'+TBTN+'">Another walk</button></div></div>');
  /* Getting to the start: north up, you and the start, distance live. Arrives by GPS. */
  sec("t-start",'<div style="'+ROOT+'"><button type="button" class="tback" data-t="home" aria-label="Return to today" style="position: absolute; top: 48px; left: 12px; z-index: 2; width: 48px; height: 48px; padding: 0; border: 0; background: transparent; display: flex; align-items: center; justify-content: center">'+BACK+'</button>'+
    '<svg class="tmap" style="flex:1 1 auto;min-height:0;background:'+LAND+'" width="390" height="100%" role="img" aria-label="Map to the start of the walk, north up"></svg>'+
    '<div style="'+COL+'"><h1 style="'+H1+'" class="th">Head to the start</h1><p style="'+P+'" class="tl">Finding you…</p>'+
    '<button type="button" data-t="go" style="'+BTN+'; margin-top: 28px">Start walk</button></div></div>');
  /* Walking: heading-up, you fixed low in the middle, km to go */
  sec("t-walk",'<div style="'+ROOT+'; background: '+LAND+'"><svg class="tmap" style="position:absolute;inset:0" width="390" height="100%" role="img" aria-label="Map of the path ahead, turned so the way you face is up"></svg>'+
    '<div class="tpanel" style="position: absolute; left: 0; right: 0; bottom: 0; padding: 24px 24px 32px; background: #FFFFFF; display: flex; flex-direction: column; gap: 16px">'+
    '<p style="'+P+'" class="lab tl">'+dist(LEN)+' to go</p><button type="button" data-t="end" style="'+BTN+'">End walk</button></div></div>');
  /* End: your trace over the route */
  sec("t-done",'<div style="'+ROOT+'; padding: 48px 0 32px"><div style="margin: 0 24px; border-radius: 24px; overflow: hidden; flex: 1 1 auto; min-height: 0; background: '+LAND+'">'+
    '<svg class="tmap" width="342" height="100%" style="display:block;width:100%;height:100%" role="img" aria-label="Your GPS trace over the walk"></svg></div>'+
    '<div style="padding: 16px 24px 0; display: flex; flex-direction: column; gap: 12px; flex: none"><p style="'+P+'" class="tl"></p>'+
    '<button type="button" data-t="home" style="'+BTN+'; margin-top: 28px">Done</button></div></div>');

  function el(id){ return view.querySelector('.scr[data-id="'+id+'"]'); }
  var cur=null;
  function showT(id){ cur=id; view.querySelectorAll(".scr").forEach(function(s){ s.classList.toggle("on",s.dataset.id===id); });
    if(N){ N.keepAwake(id==="t-start"||id==="t-walk"); }
    if(id==="t-start"||id==="t-walk"){ gpsOn(); if(N) N.startCompass(); } else { if(N) N.stopCompass(); if(!st.walking) gpsOff(); }
    draw(); }
  function gpsOn(){ if(N) N.startGps(); }
  function gpsOff(){ if(N) N.stopGps(); }
  /* leave test mode for the prototype's Today, and come back to it after Today 4 */
  function toPrototype(){ cur=null; document.getElementById("returning").click(); }
  window.wodenTestBack=function(){ if(!cur) return false;
    if(cur==="t-walk") return true;                     /* no accidental exit mid-walk: End walk ends it */
    if(cur==="t-today") return false;
    showT("t-today"); return true; };
  window.wodenPermHook=function(ok){ st.perm=ok; draw(); };
  view.addEventListener("click",function(e){
    var b=e.target.closest("button"); if(!b) return;
    var s=b.closest(".scr");
    if(s&&s.dataset.t){ if(b.dataset.go) { cur=null; return; } e.stopPropagation(); act(b.dataset.t); return; }
    if(s&&s.dataset.id==="today-4"&&b.textContent.trim()==="Another walk"){ e.stopPropagation(); showT("t-today"); }
  },true);
  function act(a){
    if(a==="another") toPrototype();
    else if(a==="there"){ showT("t-start"); }
    else if(a==="home"){ showT("t-today"); }
    else if(a==="go"){ startWalk(); }
    else if(a==="end"){ endWalk(); }
  }
  function startWalk(){ st.walking=true; st.t0=Date.now(); st.trace=[]; st.back=false;
    st.prog = st.me && Math.hypot(st.me[0]-LOOP[0][0],st.me[1]-LOOP[0][1])>60 ? project(st.me,0,LEN).p : 0;
    if(N) N.startTrace("Cannon Hill Common"); showT("t-walk"); }
  function endWalk(){ st.walking=false; st.file=N? N.endTrace() : "Downloads/Woden/woden-test.gpx";
    if(N) N.stopCompass(); showT("t-done"); }

  /* ---------- position along the route ---------- */
  function project(p,from,to){ var best={dd:1e9,p:0};
    for(var i=1;i<LOOP.length;i++){ if(CUM[i]<from||CUM[i-1]>to) continue;
      var a=LOOP[i-1], b=LOOP[i], vx=b[0]-a[0], vy=b[1]-a[1], L2=vx*vx+vy*vy||1;
      var t=Math.max(0,Math.min(1,((p[0]-a[0])*vx+(p[1]-a[1])*vy)/L2)), qx=a[0]+t*vx, qy=a[1]+t*vy, dd=Math.hypot(p[0]-qx,p[1]-qy);
      if(dd<best.dd) best={dd:dd,p:CUM[i-1]+t*Math.sqrt(L2)}; }
    return best; }
  function pointAt(s){ for(var i=1;i<LOOP.length;i++) if(CUM[i]>=s){ var t=(s-CUM[i-1])/((CUM[i]-CUM[i-1])||1); return [LOOP[i-1][0]+t*(LOOP[i][0]-LOOP[i-1][0]),LOOP[i-1][1]+t*(LOOP[i][1]-LOOP[i-1][1])]; } return LOOP[LOOP.length-1]; }
  function walkedLine(s){ var pts=[]; for(var i=0;i<LOOP.length&&CUM[i]<s;i++) pts.push(LOOP[i]); if(s>0) pts.push(pointAt(s)); return pts.length>1? d([pts],0) : ""; }
  function bearingAt(s){ var a=pointAt(Math.max(0,s-5)), b=pointAt(Math.min(LEN,s+25)); return (Math.atan2(b[0]-a[0],b[1]-a[1])*180/Math.PI+360)%360; }

  window.wodenFix=function(lat,lon,acc,t){ st.me=ll2m(lat,lon); st.acc=acc;
    if(st.walking){ st.trace.push(st.me);
      var r=project(st.me,st.prog-40,st.prog+250); if(r.dd<50&&r.p>st.prog) st.prog=r.p;
      if(!st.back&&st.prog>LEN-60&&Math.hypot(st.me[0]-LOOP[0][0],st.me[1]-LOOP[0][1])<40){ st.back=true; if(N) N.vibrate(300); } }
    else if(cur==="t-start"){ var near=Math.hypot(st.me[0]-LOOP[0][0],st.me[1]-LOOP[0][1])<=30;
      if(near&&!st.arrived){ st.arrived=true; if(N) N.vibrate(300); } }
    draw(); };
  var lastHead=null;
  window.wodenHeading=function(h){ st.head=h; if(cur==="t-walk"||cur==="t-start") draw(); };

  /* ---------- drawing ---------- */
  function svgSize(svg){ var r=svg.parentNode.getBoundingClientRect(), s=svg.getBoundingClientRect(), k=(s.width||390)/390; return [390, Math.max(100,(s.height||600)/k)]; }
  function frame(svg,cx,cy,scale,rot,ax,ay,extra){
    var sz=svgSize(svg); svg.setAttribute("viewBox","0 0 "+sz[0]+" "+sz[1]);
    if(!svg.dataset.built){ svg.innerHTML='<rect class="bg" width="100%" height="100%" fill="'+LAND+'"/><g class="w"><g class="m">'+BASE+routeLayers("r")+START+'</g></g><g class="you"></g>'; svg.dataset.built=1; }
    svg.querySelector(".bg").setAttribute("width",sz[0]+40); svg.querySelector(".bg").setAttribute("height",sz[1]+40);
    var X=(ax==null?sz[0]/2:ax), Y=(ay==null?sz[1]/2:ay);
    svg.querySelector(".tstart").setAttribute("r",8/scale);   /* start dot stays 8px whatever the zoom */
    svg.querySelector(".w").setAttribute("transform","translate("+X+" "+Y+") rotate("+rot+") scale("+scale+") translate("+(-cx)+" "+(cy)+")");
    return {w:sz[0],h:sz[1],X:X,Y:Y}; }
  function fitBox(pts,w,h,pad){ var x0=1e9,x1=-1e9,y0=1e9,y1=-1e9; pts.forEach(function(p){ x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]); });
    var sc=Math.min((w-2*pad)/Math.max(x1-x0,1),(h-2*pad)/Math.max(y1-y0,1)); return {cx:(x0+x1)/2,cy:(y0+y1)/2,sc:Math.min(sc,1.4)}; }
  function youMark(svg,f,x,y,rot){ var g=svg.querySelector(".you");
    if(!st.me){ g.innerHTML=""; return; }
    g.innerHTML=(st.head==null? DOT : ARROW); g.setAttribute("transform","translate("+x+" "+y+") rotate("+(st.head==null?0:rot)+")"); }
  function draw(){
    if(!cur) return;
    var s=el(cur), svg=s.querySelector(".tmap");
    if(cur==="t-today"){ var sz=svgSize(svg); svg.setAttribute("viewBox","0 0 "+sz[0]+" "+sz[1]);
      var fb=fitBox(LOOP,sz[0],sz[1],64), tr="translate("+sz[0]/2+" "+sz[1]/2+") scale("+fb.sc+") translate("+(-fb.cx)+" "+(fb.cy)+")";
      svg.innerHTML='<g transform="'+tr+'"><path d="'+LOOPD+'" fill="none" stroke="'+INK+'" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'+
        '<circle cx="'+LOOP[0][0]+'" cy="'+(-LOOP[0][1])+'" r="7" fill="#FFFFFF" stroke="'+INK+'" stroke-width="3" vector-effect="non-scaling-stroke"/></g>'; return; }
    if(cur==="t-start"){
      var pts=LOOP.slice(); var far=st.me? Math.hypot(st.me[0]-LOOP[0][0],st.me[1]-LOOP[0][1]) : null;
      if(st.me&&far<2500) pts.push(st.me);
      var sz2=svgSize(svg), fb2=fitBox(pts,sz2[0],sz2[1],48), f=frame(svg,fb2.cx,fb2.cy,fb2.sc,0);
      svg.querySelector(".r-done").setAttribute("d","");
      if(st.me) youMark(svg,f,f.X+(st.me[0]-fb2.cx)*fb2.sc,f.Y-(st.me[1]-fb2.cy)*fb2.sc,st.head||0); else youMark(svg,f);
      var h=s.querySelector(".th"), l=s.querySelector(".tl");
      if(st.perm===false){ h.textContent="Head to the start"; l.textContent="Location is off. Allow it in Settings to test the walk."; }
      else if(!st.me){ h.textContent="Head to the start"; l.textContent="Finding you…"; }
      else if(far<=30||st.arrived){ h.textContent="You’re here"; l.textContent=nb((LEN/1000).toFixed(1)+" km loop, about "+Math.round(LEN/1000*18/5)*5+" min."); }
      else { h.textContent="Head to the start"; l.textContent=dist(far)+" to the start."; }
      return; }
    if(cur==="t-walk"){
      var pos=st.me||pointAt(st.prog), rot=-(st.head!=null? st.head : bearingAt(st.prog));
      var sz3=svgSize(svg), panel=s.querySelector(".tpanel").getBoundingClientRect().height/((svg.getBoundingClientRect().width||390)/390);
      var f3=frame(svg,pos[0],pos[1],0.6,rot,sz3[0]/2,(sz3[1]-panel)*0.68);
      svg.querySelector(".r-done").setAttribute("d",walkedLine(st.prog));
      var g=svg.querySelector(".you"); g.innerHTML=ARROW; g.setAttribute("transform","translate("+f3.X+" "+f3.Y+")");
      var left=Math.max(0,LEN-st.prog);
      s.querySelector(".tl").textContent= st.back? "You’re back" : (!st.me? "Finding you…" : dist(left)+" to go");
      return; }
    if(cur==="t-done"){
      var sz4=svgSize(svg); svg.setAttribute("viewBox","0 0 "+sz4[0]+" "+sz4[1]);
      var all=LOOP.concat(st.trace), fb4=fitBox(all,sz4[0],sz4[1],40);
      var tr4="translate("+sz4[0]/2+" "+sz4[1]/2+") scale("+fb4.sc+") translate("+(-fb4.cx)+" "+(fb4.cy)+")";
      svg.innerHTML='<rect width="'+(sz4[0]+40)+'" height="'+(sz4[1]+40)+'" fill="'+LAND+'"/><g transform="'+tr4+'">'+BASE+
        '<path d="'+LOOPD+'" fill="none" stroke="'+WALKED+'" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'+
        (st.trace.length>1? '<path d="'+d([st.trace],0)+'" fill="none" stroke="'+INK+'" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>' : '')+'</g>';
      var walked=0; for(var k=1;k<st.trace.length;k++) walked+=Math.hypot(st.trace[k][0]-st.trace[k-1][0],st.trace[k][1]-st.trace[k-1][1]);
      var mins=Math.round((Date.now()-st.t0)/60000), day=new Date().toLocaleDateString("en-GB",{day:"numeric",month:"short"});
      s.querySelector(".tl").innerHTML=nb("Cannon Hill Common, "+day+". "+(walked/1000).toFixed(2)+" km in "+mins+" min.")+"<br>"+
        (st.file? "GPS trace saved to "+st.file.replace("Downloads/","Downloads/")+"." : "No GPS trace was recorded.");
      return; }
  }
  addEventListener("resize",function(){ draw(); });

  /* browser try-out: tap the map to be there; arrow keys turn you */
  if(SIM){ view.addEventListener("click",function(e){ var svg=e.target.closest(".tmap"); if(!svg||!(cur==="t-start"||cur==="t-walk")) return;
      var r=svg.getBoundingClientRect(), vb=svg.viewBox.baseVal, x=(e.clientX-r.left)/r.width*vb.width, y=(e.clientY-r.top)/r.height*vb.height;
      var w=svg.querySelector(".w").getCTM().inverse(), p=svg.createSVGPoint(); p.x=x*(r.width/vb.width); p.y=y*(r.height/vb.height);
      var q=p.matrixTransform(svg.getScreenCTM().inverse()); q=q.matrixTransform(svg.querySelector(".w").getCTM().inverse());
      var ll=m2ll(q.x,-q.y); window.wodenFix(ll[0],ll[1],5,Date.now()); });
    addEventListener("keydown",function(e){ if(e.key==="ArrowLeft"||e.key==="ArrowRight"){ window.wodenHeading(((st.head||0)+(e.key==="ArrowLeft"?-15:15)+360)%360); } }); }

  window.wodenTest={st:st,showT:showT,LEN:LEN,LOOP:LOOP,m2ll:m2ll};
  showT("t-today");
})();
