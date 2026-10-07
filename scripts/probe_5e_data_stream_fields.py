#!/usr/bin/env python3
import json, urllib.request
from pathlib import Path

IDS=[2398746,2398743,2398742,2398738]
BASE="https://esports-data.5eplaycdn.com/v1/api/csgo/matches"
UA="Mozilla/5.0"
def walk(x,path="$",out=None):
    if out is None: out=[]
    if isinstance(x,dict):
        for k,v in x.items():
            p=f"{path}.{k}"
            kl=k.lower()
            if any(q in kl for q in ("url","stream","live","video","demo","replay","record","tv","gotv","cstv","download","source")):
                out.append({"path":p,"value":v})
            walk(v,p,out)
    elif isinstance(x,list):
        for i,v in enumerate(x[:200]):
            walk(v,f"{path}[{i}]",out)
    return out

res={}
for mid in IDS:
    match=f"csgo_mc_{mid}"
    u=f"{BASE}/{match}/data"
    try:
        req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/json","Referer":f"https://event.5eplay.com/csgo/matches/{match}"})
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read()
        obj=json.loads(raw.decode())
        hits=walk(obj)
        print("\n",match,"bytes",len(raw),"hits",len(hits))
        for h in hits[:100]: print(h["path"],repr(h["value"])[:1200])
        res[match]={"bytes":len(raw),"topKeys":list(obj.keys()) if isinstance(obj,dict) else None,"interesting":hits[:200]}
    except Exception as e:
        print(match,"ERR",repr(e));res[match]={"error":f"{type(e).__name__}: {e}"}
Path("data/probes/5e-data-stream-fields.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n","utf-8")
