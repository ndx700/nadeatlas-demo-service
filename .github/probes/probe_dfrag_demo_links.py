#!/usr/bin/env python3
import re, urllib.request, json, html as H
PAGES=[
"https://dfrag.gg/counterstrike/events/iem-cologne-major-2026/matches/quarter-final-falcons-vs-vitality-bo3/",
"https://dfrag.gg/counterstrike/events/iem-cologne-major-2026/matches/round-5-natus-vincere-vs-g2-bo3/",
"https://dfrag.gg/counterstrike/events/iem-cologne-major-2026/matches/semi-final-spirit-vs-falcons-bo3/",
"https://dfrag.gg/counterstrike/events/cs-asia-championships-2026/matches/final-falcons-vs-legacy-bo5/",
"https://dfrag.gg/counterstrike/events/pgl-astana-2026/matches/round-4-the-mongolz-vs-falcons-bo3/",
"https://dfrag.gg/counterstrike/events/pgl-astana-2026/matches/quarter-final-furia-vs-falcons-bo3/",
"https://dfrag.gg/counterstrike/events/cs-asia-championships-2026/matches/semi-final-falcons-vs-mouz-bo3/",
]
KEYS=("demo","download","match","hltv","file","storage","bucket","url")
for p in PAGES:
 print("\nPAGE",p)
 raw=urllib.request.urlopen(urllib.request.Request(p,headers={"User-Agent":"Mozilla/5.0"}),timeout=45).read().decode("utf-8","ignore")
 print("BYTES",len(raw))
 # Next/RSC payloads and script sources
 for m in re.finditer(r'<script[^>]*>(.*?)</script>',raw,re.S|re.I):
  s=H.unescape(m.group(1))
  if any(k in s.lower() for k in ("demo","download")):
   print("SCRIPT_MATCH",s[:5000].replace("\n"," ")[:5000])
 for u in sorted(set(re.findall(r'https?:\\?/\\?/[^"\\\'<> ]+',raw))):
  uu=u.replace("\\/","/")
  if any(k in uu.lower() for k in KEYS): print("URL",uu[:1000])
 for pat in [r'.{0,300}demo.{0,500}',r'.{0,300}download.{0,500}']:
  vals=re.findall(pat,raw,re.I|re.S)
  for v in vals[:12]: print("CTX",re.sub(r'\\s+',' ',H.unescape(v))[:900])
