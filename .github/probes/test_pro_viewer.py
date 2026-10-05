#!/usr/bin/env python3
import re,json,html,urllib.request,urllib.parse
BASE="https://cs.rlin.dev";UA="Mozilla/5.0"
def get(u,limit=30_000_000):
 q=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/json,text/html,*/*"})
 with urllib.request.urlopen(q,timeout=30) as r:return r.status,r.headers,r.read(limit)
_,_,b=get(BASE+"/pro-games?event=8057");p=html.unescape(b.decode("utf-8","ignore"))
# Pull all hltv map IDs paired with dust2 from the server-rendered payload.
ids=[]
patterns=[
 r'\\\"matchId\\\":\\\"(hltv-[^\\\"]+)\\\",\\\"mapName\\\":\\\"de_dust2\\\"',
 r'"matchId":"(hltv-[^"]+)","mapName":"de_dust2"'
]
for pat in patterns:
 for m in re.finditer(pat,p):
  if m.group(1) not in ids:ids.append(m.group(1))
print("DUST2_IDS",ids)
for mid in ids[:20]:
 try:
  st,h,b=get(BASE+"/api/matches/"+urllib.parse.quote(mid),2_000_000);o=json.loads(b)
  print("MATCH",mid,o.get("name"),o.get("mapName"),o.get("score"),o.get("matchTime"))
  print("DEMO",o.get("demoUrl"))
  du=o.get("demoUrl")
  if du:
   q=urllib.request.Request(du,headers={"User-Agent":UA,"Range":"bytes=0-31"})
   with urllib.request.urlopen(q,timeout=30) as r:
    head=r.read(32);print("VERIFY",r.status,r.headers.get("content-range"),repr(head[:8]),head.startswith(b"PBDEMS2"))
 except Exception as e:print("ERR",mid,repr(e))
