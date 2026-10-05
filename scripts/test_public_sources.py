#!/usr/bin/env python3
import json, urllib.request
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json,*/*"})
    with urllib.request.urlopen(req,timeout=30) as r:
        b=r.read(3000000)
        print("\nURL",url,"STATUS",r.status,"TYPE",r.headers.get("content-type"),"BYTES",len(b))
        return b

b=get("https://cs2replays.com/api/matches?limit=10")
print("MATCHES_RAW",b.decode("utf-8","ignore")[:12000])
try:
    o=json.loads(b)
    items=o if isinstance(o,list) else next((o[k] for k in ["matches","data","items"] if isinstance(o.get(k),list)),[])
    print("COUNT",len(items))
    if items:
        print("FIRST",json.dumps(items[0],ensure_ascii=False)[:8000])
        mid=items[0].get("id") or items[0].get("_id") or items[0].get("match_id")
        if mid:
            d=get("https://cs2replays.com/api/matches/"+str(mid))
            print("DETAIL_RAW",d.decode("utf-8","ignore")[:20000])
except Exception as e: print("PARSE_ERROR",repr(e))
