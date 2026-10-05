#!/usr/bin/env python3
import re,html,urllib.parse,urllib.request
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
mids=["csgo_mc_2374325","csgo_mc_2373995","csgo_mc_2393086","csgo_mc_2394999"]
for mid in mids:
 u="https://event.5eplay.com/csgo/matches/"+mid
 print("\n###",mid,u)
 req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"text/html,*/*"})
 with urllib.request.urlopen(req,timeout=30) as r:
  b=r.read(8_000_000); s=b.decode("utf-8","ignore"); status=r.status
 print("HTML",len(s),"STATUS",status)
 d=html.unescape(s)
 for _ in range(2): d=urllib.parse.unquote(d)
 for needle in ["本场回放","直播回放","全场回放","Dust2","demo","replay","playback"]:
  hits=list(re.finditer(needle,d,re.I))[:20]
  print("\nNEEDLE",needle,"COUNT",len(hits))
  for m in hits:
   ctx=d[max(0,m.start()-1200):m.start()+2200]
   urls=sorted(set(re.findall(r"https?://[^\\s\\\"'<>\\\\]+",ctx)))
   hrefs=sorted(set(re.findall(r"href=[\\\"']([^\\\"']+)",ctx,re.I)))
   print("CTX",re.sub(r"\\s+"," ",ctx)[:3400])
   print("URLS",urls[:20]);print("HREFS",hrefs[:20])
