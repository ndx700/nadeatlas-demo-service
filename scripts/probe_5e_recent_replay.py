#!/usr/bin/env python3
import html, json, re, urllib.parse, urllib.request
from pathlib import Path

IDS=[2398746,2398743,2398742,2398738]
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
out={}
for mid in IDS:
    u=f"https://event.5eplay.com/csgo/matches/csgo_mc_{mid}"
    print("\nPAGE",mid,u)
    try:
        req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"text/html,*/*","Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8"})
        with urllib.request.urlopen(req,timeout=45) as r:
            raw=r.read(12_000_000)
            status=r.status
            final=r.geturl()
        s=raw.decode("utf-8","ignore")
        d=html.unescape(s)
        for _ in range(2):
            d=urllib.parse.unquote(d)
        candidates=set()
        pats=[
          r'https?://[^\s\\"\'<>]+',
          r'["\']([^"\']*(?:game_tv|5eplaycdn|demo|replay|playback|cstv|record)[^"\']*)["\']',
          r'(g\d+-\d{20,})',
        ]
        for pat in pats:
            for m in re.finditer(pat,d,re.I):
                v=m.group(1) if m.lastindex else m.group(0)
                v=v.replace("\\/","/")
                if any(k in v.lower() for k in ("game_tv","5eplaycdn","demo","replay","playback","cstv")) or re.fullmatch(r'g\d+-\d{20,}',v):
                    candidates.add(v[:2000])
        contexts=[]
        for needle in ("game_tv","5eplaycdn","本场回放","全场回放","demo","replay","playback","cstv"):
            for m in list(re.finditer(needle,d,re.I))[:20]:
                ctx=re.sub(r"\s+"," ",d[max(0,m.start()-1000):m.start()+2200])
                contexts.append({"needle":needle,"text":ctx[:3200]})
        print("STATUS",status,"BYTES",len(raw),"CANDS",len(candidates))
        for v in sorted(candidates):
            print("CAND",v)
        out[str(mid)]={"url":u,"status":status,"final":final,"bytes":len(raw),"candidates":sorted(candidates),"contexts":contexts[:80]}
    except Exception as e:
        print("ERR",repr(e))
        out[str(mid)]={"url":u,"error":f"{type(e).__name__}: {e}"}
Path("data/probes/5e-recent-replay.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n","utf-8")
