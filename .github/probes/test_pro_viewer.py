#!/usr/bin/env python3
import urllib.request,json
UA="Mozilla/5.0"
u="https://cs.rlin.dev/api/matches/hltv-2396950-m1"
q=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/json"})
with urllib.request.urlopen(q,timeout=30) as r:
 b=r.read(20_000_000);print("STATUS",r.status,"TYPE",r.headers.get("content-type"),"BYTES",len(b))
o=json.loads(b)
print("TOP_KEYS",sorted(o.keys()) if isinstance(o,dict) else type(o).__name__)
def walk(x,path="",depth=0):
 if depth>4:return
 if isinstance(x,dict):
  for k,v in x.items():
   p=path+"."+k if path else k
   kl=k.lower()
   if any(z in kl for z in ["url","demo","source","file","s3","bucket","key","download","map","name","score","time"]):
    if isinstance(v,(str,int,float,bool)) or v is None: print("FIELD",p,repr(v)[:2000])
   walk(v,p,depth+1)
 elif isinstance(x,list):
  for i,v in enumerate(x[:3]):walk(v,f"{path}[{i}]",depth+1)
walk(o)
