#!/usr/bin/env python3
"""Decode one rlin stats file and describe its structure (keys, sizes, grenade-like records)."""
import gzip, json, sys, urllib.request, msgpack
URL=sys.argv[1]
raw=urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"}),timeout=120).read()
obj=msgpack.unpackb(gzip.decompress(raw),raw=False,strict_map_key=False)
out={"url":URL,"compressedBytes":len(raw)}
def shape(o,depth=0):
    if depth>4: return type(o).__name__
    if isinstance(o,dict): return {str(k):shape(v,depth+1) for k,v in list(o.items())[:60]}
    if isinstance(o,list): return {"list_len":len(o),"first":shape(o[0],depth+1) if o else None}
    return repr(o)[:80]
out["shape"]=shape(obj)
hits={}
def walk(o,path):
    if isinstance(o,dict):
        for k,v in o.items():
            p=f"{path}.{k}"
            if any(w in str(k).lower() for w in ("grenade","nade","smoke","flash","molotov","inferno","he_","projectile","utility","throw")):
                hits[p]=shape(v,2)
            walk(v,p)
    elif isinstance(o,list) and o:
        walk(o[0],path+"[0]")
walk(obj,"root")
out["grenadeLike"]=hits
open("stats-shape.json","w").write(json.dumps(out,ensure_ascii=False,indent=1))
print(json.dumps(hits,ensure_ascii=False)[:3000])
