#!/usr/bin/env python3
import urllib.request,urllib.error
base="https://hk-demo.5eplaycdn.com/game_tv/g201-20260922154948491976189"
for n in range(1284,1311):
 vals=[]
 for kind in ["full","delta"]:
  try:
   req=urllib.request.Request(f"{base}/{n}/{kind}",headers={"User-Agent":"Mozilla/5.0","Range":"bytes=0-0"})
   with urllib.request.urlopen(req,timeout=10) as r: vals.append(f"{kind}:OK:{r.headers.get('content-range')}")
  except urllib.error.HTTPError as e: vals.append(f"{kind}:HTTP{e.code}")
  except Exception as e: vals.append(f"{kind}:ERR")
 print("EDGE",n,*vals)
