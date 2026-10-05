#!/usr/bin/env python3
import re, urllib.request
from urllib.parse import urljoin
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"

def fetch(url, limit=2000000):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=30) as r:
        b=r.read(limit)
        return r.status,r.geturl(),r.headers.get("content-type",""),b

def probe(name,url):
    print("\n###",name,url)
    try:
        st,final,ct,b=fetch(url)
        print("STATUS",st,"FINAL",final,"TYPE",ct,"BYTES",len(b))
        txt=b.decode("utf-8","ignore")
        urls=re.findall(r"https?://[^\\s\\\"'<>]+",txt,re.I)
        print("DEMO_URLS",[u for u in sorted(set(urls)) if any(x in u.lower() for x in [".dem",".rar",".zip","r2-demos.hltv.org"])][:30])
        print("API_HINTS",sorted(set(re.findall(r"/api/[A-Za-z0-9_?&=./:{}-]+",txt)))[:50])
        scripts=re.findall(r"<script[^>]+src=[\\\"']([^\\\"']+)[\\\"']",txt,re.I)
        print("SCRIPTS",scripts[-15:])
        return scripts
    except Exception as e:
        print("ERROR",type(e).__name__,str(e))
        return []

scripts=probe("CS2REPLAYS_DUST2","https://cs2replays.com/library/?map=de_dust2")
for s in scripts[-10:]:
    u=urljoin("https://cs2replays.com/library/",s)
    try:
        st,final,ct,b=fetch(u)
        txt=b.decode("utf-8","ignore")
        low=txt.lower()
        if any(k in low for k in ["pro-match","pro_match","library","demo_url","demourl"]):
            print("\nSCRIPT_MATCH",u,"bytes",len(b))
            print("API_HINTS",sorted(set(re.findall(r"/api/[A-Za-z0-9_?&=./:{}-]+",txt)))[:100])
            urls=re.findall(r"https?://[^\\s\\\"'<>]+",txt,re.I)
            print("DEMO_URLS",[x for x in sorted(set(urls)) if any(k in x.lower() for k in [".dem","r2-demos.hltv.org"])][:30])
    except Exception as e: print("SCRIPT_ERROR",u,e)

probe("NADES","https://nades.ai/matches")
probe("BLAST_MATCH","https://api.blast.tv/v2/games/cs/matches/867dd193")
