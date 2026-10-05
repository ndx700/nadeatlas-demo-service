#!/usr/bin/env python3
import re,urllib.request,urllib.parse,html
BASE="https://cs.rlin.dev"; UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
def get(u,limit=30_000_000):
 q=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/json,text/html,*/*"})
 with urllib.request.urlopen(q,timeout=30) as r:return r.status,r.geturl(),r.headers,r.read(limit)
u=BASE+"/viewer?match=hltv-2396950-m1"
st,fin,h,b=get(u);s=html.unescape(b.decode("utf-8","ignore"))
print("VIEWER",st,len(b),fin)
for key in ["hltv-2396950-m1",".dem","demoUrl","download","s3","cloudfront","match-data","rounds","positions","api/"]:
 print("\nKEY",key)
 for m in list(re.finditer(re.escape(key),s,re.I))[:30]:
  print("CTX",re.sub(r"\\s+"," ",s[max(0,m.start()-700):m.start()+1800])[:2500])
scripts=[urllib.parse.urljoin(BASE,x) for x in re.findall(r'<script[^>]+src=[\"\']([^\"\']+)',s,re.I)]
for su in scripts:
 st,fi,hh,bb=get(su);js=bb.decode("utf-8","ignore")
 if any(k in js for k in ["/api/","match-data","demoUrl","hltv-"]):
  hits=[]
  for m in re.finditer(r'/api/',js):
   ctx=js[max(0,m.start()-800):m.start()+2200]
   if any(k in ctx.lower() for k in ["match","demo","round","position","viewer"]): hits.append(ctx)
  if hits:
   print("\nSCRIPT",su,len(bb))
   for x in hits[:30]:print("APICTX",x)
