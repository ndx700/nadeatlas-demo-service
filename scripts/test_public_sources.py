#!/usr/bin/env python3
import urllib.request, urllib.error
UA="nadeatlas-demo-service/1.0"
urls=[
 "https://r2-demos.hltv.org/",
 "https://r2-demos.hltv.org/?list-type=2&prefix=demos/&max-keys=10",
 "https://r2-demos.hltv.org/demos/",
 "https://r2-demos.hltv.org/demos/123212/parken-challenger-championship-season-1-masonic-vs-bcgame-nuke-BiFiPdO20WDjOb7rgyXZUv.rar",
]
for u in urls:
 print("\nURL",u)
 try:
  h={"User-Agent":UA}
  if u.endswith(".rar"): h["Range"]="bytes=0-31"
  req=urllib.request.Request(u,headers=h)
  with urllib.request.urlopen(req,timeout=30) as r:
   b=r.read(5000)
   print("STATUS",r.status,"FINAL",r.geturl(),"TYPE",r.headers.get("content-type"),"LEN",r.headers.get("content-length"),"RANGE",r.headers.get("content-range"))
   print("BODY_HEX",b[:32].hex())
   print("BODY_TEXT",b[:2000].decode("utf-8","ignore"))
 except urllib.error.HTTPError as e:
  b=e.read(3000)
  print("HTTP_ERROR",e.code,"TYPE",e.headers.get("content-type"))
  print("BODY",b.decode("utf-8","ignore"))
 except Exception as e: print("ERROR",repr(e))
