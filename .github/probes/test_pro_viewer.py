#!/usr/bin/env python3
import re, urllib.request, urllib.parse, json
BASE="https://cs.rlin.dev"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
def fetch(u,limit=12_000_000):
 q=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"*/*"})
 with urllib.request.urlopen(q,timeout=30) as r:return r.status,r.geturl(),r.headers,r.read(limit)
u=BASE+"/pro-games?event=8249&series=2396950"
st,final,h,b=fetch(u);s=b.decode("utf-8","ignore")
print("PAGE",st,final,len(b),h.get("content-type"))
print("DEMS",sorted(set(re.findall(r'https?[^\\\"\'<> ]+?\\.dem(?:\\?[^\\\"\'<> ]*)?',s,re.I)))[:100])
print("API_HINTS")
for x in sorted(set(re.findall(r'[^\\\"\']{0,100}(?:api|demo|series|pro-games|s3|cloudfront)[^\\\"\']{0,180}',s,re.I))):
 if len(x)<500: print("HINT",x)
scripts=[]
for src in re.findall(r'<script[^>]+src=[\"\']([^\"\']+)',s,re.I):
 scripts.append(urllib.parse.urljoin(BASE,src))
print("SCRIPTS",len(scripts))
for su in scripts:
 try:
  st,fin,hh,bb=fetch(su,20_000_000);js=bb.decode("utf-8","ignore")
  if any(k in js.lower() for k in ["pro-games","demo","2396950","series"]):
   print("\nSCRIPT",su,"BYTES",len(bb))
   for pat in [r'https?[^\\\"\' ]+',r'/api/[^\\\"\' ]+',r'[^\\\"\']{0,120}2396950[^\\\"\']{0,200}',r'[^\\\"\']{0,120}demo[^\\\"\']{0,240}']:
    for x in list(dict.fromkeys(re.findall(pat,js,re.I)))[:100]: print("JS",x[:600])
 except Exception as e: print("SCRIPT_ERR",su,repr(e))
