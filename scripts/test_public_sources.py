#!/usr/bin/env python3
import re, urllib.parse, urllib.request, urllib.error
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36"
sheet="https://docs.qq.com/sheet/DZmdydmpxYURyREtZ?tab=BB08J2"
req=urllib.request.Request(sheet,headers={"User-Agent":UA})
with urllib.request.urlopen(req,timeout=30) as r:
 s=r.read(8_000_000).decode("utf-8","ignore")
# decode URL-encoded embedded sheet payload repeatedly
d=s
for _ in range(3):
 nd=urllib.parse.unquote(d)
 if nd==d: break
 d=nd
ids=[]
for x in re.findall(r'g201-\d{14,}-?\d*',d):
 if x not in ids: ids.append(x)
print("GAMEIDS",len(ids))
for x in ids[:80]: print("ID",x)
for gid in ids[:12]:
 u="https://hk-demo.5eplaycdn.com/game_tv/"+gid
 print("\nPROBE",gid,u)
 try:
  h={"User-Agent":UA,"Range":"bytes=0-4095","Accept":"*/*"}
  with urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=30) as r:
   b=r.read(4096)
   print("STATUS",r.status,"FINAL",r.geturl())
   for k in ["content-type","content-length","content-range","accept-ranges","content-disposition","etag","last-modified","transfer-encoding"]:
    print("HDR",k,r.headers.get(k))
   print("HEAD_HEX",b[:96].hex())
   print("HEAD_ASCII",repr(b[:96]))
 except urllib.error.HTTPError as e:
  b=e.read(1000)
  print("HTTP_ERROR",e.code,"TYPE",e.headers.get("content-type"),"LEN",e.headers.get("content-length"),"BODY",repr(b[:300]))
 except Exception as e: print("ERROR",repr(e))
