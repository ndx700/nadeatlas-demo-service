#!/usr/bin/env python3
import html, json, re, urllib.parse, urllib.request
from pathlib import Path

PAGE="https://event.5eplay.com/csgo/matches/csgo_mc_2398746"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
def get(u):
    req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read(),r.geturl()

raw,final=get(PAGE)
s=raw.decode("utf-8","ignore")
scripts=[]
for m in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']',s,re.I):
    scripts.append(urllib.parse.urljoin(final,html.unescape(m.group(1))))
print("PAGE",len(raw),"SCRIPTS",len(scripts))
out={"page":PAGE,"scripts":scripts,"hits":[]}
needles=("game_tv","5eplaycdn","cstv","replay","demo","playback","record","broadcast")
for i,u in enumerate(scripts):
    try:
        b,_=get(u)
        text=b.decode("utf-8","ignore")
        low=text.lower()
        matched=[n for n in needles if n in low]
        print(i+1,len(scripts),len(b),matched,u)
        if not matched: continue
        for n in matched:
            pos=0
            count=0
            while count<30:
                j=low.find(n,pos)
                if j<0: break
                ctx=text[max(0,j-1500):j+2500]
                out["hits"].append({"script":u,"needle":n,"context":ctx})
                pos=j+len(n);count+=1
    except Exception as e:
        print("ERR",u,repr(e))
        out["hits"].append({"script":u,"error":f"{type(e).__name__}: {e}"})
Path("data/probes/5e-bundle-replay.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n","utf-8")
print("HITS",len(out["hits"]))
