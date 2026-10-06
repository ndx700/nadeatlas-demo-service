#!/usr/bin/env python3
import re, urllib.request, json
PAGES=[
"https://dfrag.gg/counterstrike/events/pgl-bucharest-2026/matches/final-astralis-vs-fut-bo5/",
"https://dfrag.gg/counterstrike/events/pgl-astana-2026/matches/semi-final-mouz-vs-spirit-bo3/",
"https://dfrag.gg/counterstrike/events/pgl-astana-2026/matches/round-3-furia-vs-spirit-bo3/",
"https://dfrag.gg/counterstrike/events/pgl-astana-2026/matches/quarter-final-furia-vs-falcons-bo3/",
"https://dfrag.gg/counterstrike/events/iem-cologne-major-2026/matches/semi-final-spirit-vs-falcons-bo3/",
"https://dfrag.gg/counterstrike/events/iem-cologne-major-2026/matches/quarter-final-falcons-vs-vitality-bo3/",
"https://dfrag.gg/counterstrike/events/iem-cologne-major-2026/matches/quarter-final-g2-vs-spirit-bo3/",
]
for page in PAGES:
  print("\nPAGE",page)
  req=urllib.request.Request(page,headers={"User-Agent":"Mozilla/5.0"})
  html=urllib.request.urlopen(req,timeout=30).read().decode("utf-8","ignore")
  print("HTML",len(html),"dust2", "de_dust2" in html)
  # print only URLs likely to be demo/archive endpoints, never cookies/tokens
  urls=set(re.findall(r'https?://[^"\'<> ]+',html))
  rel=set(re.findall(r'(?:href|src)=["\']([^"\']+)["\']',html,re.I))
  cand=sorted(u for u in urls|rel if any(k in u.lower() for k in ["demo",".dem",".zip",".rar","download"]))
  for u in cand[:50]: print("CAND",u[:500])
