#!/usr/bin/env python3
import urllib.request,urllib.error,json
UA="Mozilla/5.0"
base="https://hk-demo.5eplaycdn.com/game_tv/g201-20260922154948491976189"
with urllib.request.urlopen(urllib.request.Request(base+"/sync",headers={"User-Agent":UA}),timeout=20) as r:
 sync=json.loads(r.read()); print("SYNC",sync)
last=int(sync["fragment"])
for n in [1,last//2,last-1,last,last+1]:
 for kind in ["full","delta"]:
  u=f"{base}/{n}/{kind}"
  try:
   req=urllib.request.Request(u,headers={"User-Agent":UA,"Range":"bytes=0-31"})
   with urllib.request.urlopen(req,timeout=15) as r:
    b=r.read(32); print("FRAG",n,kind,"OK",r.status,"TOTAL",r.headers.get("content-range"),"HEAD",b.hex())
  except urllib.error.HTTPError as e: print("FRAG",n,kind,"HTTP",e.code)
  except Exception as e: print("FRAG",n,kind,"ERR",repr(e))
