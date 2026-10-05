#!/usr/bin/env python3
import urllib.request, urllib.error
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
ids=["g201-20260922154948491976189","g201-20260922165611262612321","g201-20260922154931086591845"]
paths=[
 "/sync",
 "/sync?fragment=1",
 "/sync?fragment=0",
 "/1/start","/1/full","/1/delta",
 "/0/start","/0/full","/0/delta",
]
for gid in ids:
 print("\nGAME",gid)
 base="https://hk-demo.5eplaycdn.com/game_tv/"+gid
 for p in paths:
  u=base+p
  try:
   req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"*/*","Range":"bytes=0-4095"})
   with urllib.request.urlopen(req,timeout=20) as r:
    b=r.read(4096)
    print("OK",p,"STATUS",r.status,"TYPE",r.headers.get("content-type"),"LEN",r.headers.get("content-length"),"RANGE",r.headers.get("content-range"),"FINAL",r.geturl())
    print("BODY",repr(b[:500]))
  except urllib.error.HTTPError as e:
   b=e.read(300)
   print("HTTP",p,e.code,e.headers.get("content-type"),e.headers.get("content-length"),repr(b[:100]))
  except Exception as e: print("ERR",p,repr(e))
