#!/usr/bin/env python3
import re,urllib.request,urllib.parse,json,html
BASE="https://cs.rlin.dev"; UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
def get(u,limit=25_000_000):
 q=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/json,text/html,*/*"})
 with urllib.request.urlopen(q,timeout=30) as r:return r.status,r.geturl(),r.headers,r.read(limit)
u=BASE+"/pro-games?event=8249&series=2396950"
st,fin,h,b=get(u);s=html.unescape(b.decode("utf-8","ignore"))
print("PAGE",st,len(b))
for key in ["initialSeriesId","2396950","demos","matchId","de_dust2","Dust2","demoId","fileKey","s3","cloudfront"]:
 print("\nKEY",key)
 for m in list(re.finditer(re.escape(key),s,re.I))[:40]:
  print("CTX",re.sub(r"\\s+"," ",s[max(0,m.start()-800):m.start()+1800])[:2600])
scripts=[urllib.parse.urljoin(BASE,x) for x in re.findall(r'<script[^>]+src=[\"\']([^\"\']+)',s,re.I)]
for su in scripts:
 st,fi,hh,bb=get(su);js=bb.decode("utf-8","ignore")
 if "/api/pro-games/" in js or "series-stats" in js:
  print("\nTARGET_SCRIPT",su,len(bb))
  for m in re.finditer(r'/api/pro-games/',js):
   print("APICTX",js[max(0,m.start()-1200):m.start()+3000])
