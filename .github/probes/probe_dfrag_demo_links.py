#!/usr/bin/env python3
import re, urllib.request, html as H
PAGES=[
"https://dfrag.gg/counterstrike/events/iem-cologne-major-2026/matches/quarter-final-falcons-vs-vitality-bo3/",
"https://dfrag.gg/counterstrike/events/iem-cologne-major-2026/matches/round-5-natus-vincere-vs-g2-bo3/",
"https://dfrag.gg/counterstrike/events/iem-cologne-major-2026/matches/semi-final-spirit-vs-falcons-bo3/",
"https://dfrag.gg/counterstrike/events/pgl-astana-2026/matches/round-4-the-mongolz-vs-falcons-bo3/",
]
for p in PAGES:
 print("\nPAGE",p)
 raw=urllib.request.urlopen(urllib.request.Request(p,headers={"User-Agent":"Mozilla/5.0"}),timeout=45).read().decode("utf-8","ignore")
 print("BYTES",len(raw),"DUST2", "de_dust2" in raw.lower())
 # extract absolute/relative endpoints and RSC contexts
 vals=set(re.findall(r'https?:\\?/\\?/[^"\\\'<>\\s]+',raw))
 vals |= set(re.findall(r'["\\\']([^"\\\']*(?:demo|download)[^"\\\']*)["\\\']',raw,re.I))
 for v in sorted(vals):
  u=H.unescape(v).replace("\\/","/")
  if any(k in u.lower() for k in ("demo","download",".rar",".zip",".dem","api/")):
   print("CAND",u[:1500])
 for key in ("Download demo","demoUrl","demo_url","downloadUrl","download_url"):
  pos=0
  while True:
   i=raw.lower().find(key.lower(),pos)
   if i<0: break
   print("CTX",re.sub(r'\\s+',' ',H.unescape(raw[max(0,i-1000):i+1800]))[:2800])
   pos=i+len(key)
