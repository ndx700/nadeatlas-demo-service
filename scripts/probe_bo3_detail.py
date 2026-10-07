#!/usr/bin/env python3
import json, urllib.request
from pathlib import Path

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
urls=[
 "https://api.bo3.gg/api/v1/matches/130784",
 "https://api.bo3.gg/api/v1/matches/130784?with=teams,tournament,games,streams",
 "https://api.bo3.gg/api/v1/games/187819",
 "https://api.bo3.gg/api/v1/games/187819?with=match,teams,players",
]
def interesting(obj,path="$",out=None):
 if out is None: out=[]
 if isinstance(obj,dict):
  for k,v in obj.items():
   p=f"{path}.{k}"
   if any(x in str(k).lower() for x in ("demo","hltv","source","replay","download","url","external")):
    out.append((p,v))
   interesting(v,p,out)
 elif isinstance(obj,list):
  for i,v in enumerate(obj[:100]): interesting(v,f"{path}[{i}]",out)
 return out

result={}
for u in urls:
 req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/json","Origin":"https://bo3.gg","Referer":"https://bo3.gg/"})
 try:
  with urllib.request.urlopen(req,timeout=40) as r:
   raw=r.read(); status=r.status
  obj=json.loads(raw.decode())
  result[u]={
   "status":status,"bytes":len(raw),
   "topKeys":list(obj.keys()) if isinstance(obj,dict) else None,
   "interesting":[{"path":p,"value":v} for p,v in interesting(obj)[:100]],
   "sample":obj,
  }
 except Exception as e:
  result[u]={"error":f"{type(e).__name__}: {e}"}
 print(u,result[u].get("status"),result[u].get("error"),"interesting",len(result[u].get("interesting",[])))
Path("data/probes/bo3-detail.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
