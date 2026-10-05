#!/usr/bin/env python3
import json, re, urllib.request, urllib.error
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"

def get(url, limit=3000000):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json,*/*"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.status,r.geturl(),r.headers, r.read(limit)

def walk(obj,path=""):
    if isinstance(obj,dict):
        for k,v in obj.items():
            p=f"{path}.{k}" if path else k
            if any(x in k.lower() for x in ["demo","game","tv","play","cstv","url","download","stream"]):
                s=json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else repr(v)
                print("FIELD",p,s[:1200])
            walk(v,p)
    elif isinstance(obj,list):
        for i,v in enumerate(obj[:30]): walk(v,f"{path}[{i}]")

for mid in ["csgo_mc_2392279","csgo_mc_2398738","csgo_mc_2396053"]:
    u=f"https://esports-data.5eplaycdn.com/v1/api/csgo/matches/{mid}/data"
    print("\n### DATA",mid)
    try:
        st,final,h,b=get(u)
        print("STATUS",st,"TYPE",h.get("content-type"),"BYTES",len(b))
        o=json.loads(b)
        print("TOP_KEYS",list(o.keys()) if isinstance(o,dict) else type(o).__name__)
        walk(o)
    except Exception as e: print("ERROR",repr(e))

for gid in ["2392279","csgo_mc_2392279","2398738"]:
    u=f"https://hk-demo.5eplaycdn.com/game_tv/{gid}"
    print("\n### PLAYCAST",u)
    try:
        req=urllib.request.Request(u,headers={"User-Agent":UA,"Range":"bytes=0-2047"})
        with urllib.request.urlopen(req,timeout=20) as r:
            b=r.read(2048)
            print("STATUS",r.status,"FINAL",r.geturl(),"TYPE",r.headers.get("content-type"),"LEN",r.headers.get("content-length"),"RANGE",r.headers.get("content-range"))
            print("HEAD_HEX",b[:64].hex())
            print("TEXT",b[:500].decode("utf-8","ignore"))
    except urllib.error.HTTPError as e:
        b=e.read(1000)
        print("HTTP_ERROR",e.code,"TYPE",e.headers.get("content-type"),"BODY",b[:500].decode("utf-8","ignore"))
    except Exception as e: print("ERROR",repr(e))
