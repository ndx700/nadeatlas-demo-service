#!/usr/bin/env python3
import urllib.request,hashlib
u="https://videoscdn-cs.rlin.dev/demos/hltv-2396950-m1-mouz-vs-vitality-m1-dust2.dem"
for rng in ["bytes=0-4095",None]:
 h={"User-Agent":"Mozilla/5.0","Accept":"*/*"}
 if rng:h["Range"]=rng
 q=urllib.request.Request(u,headers=h)
 with urllib.request.urlopen(q,timeout=60) as r:
  if rng:
   b=r.read(4096)
   print("RANGE_STATUS",r.status)
   print("TYPE",r.headers.get("content-type"))
   print("LENGTH",r.headers.get("content-length"))
   print("CONTENT_RANGE",r.headers.get("content-range"))
   print("ACCEPT_RANGES",r.headers.get("accept-ranges"))
   print("HEAD_ASCII",repr(b[:32]))
   print("VALID_HEADER",b.startswith(b"PBDEMS2") or b.startswith(b"HL2DEMO"))
   break
