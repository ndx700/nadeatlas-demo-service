#!/usr/bin/env python3
import re,json,html,urllib.request,urllib.parse
BASE="https://cs.rlin.dev"; UA="Mozilla/5.0"
def get(u,limit=30_000_000):
 q=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/json,text/html,*/*"})
 with urllib.request.urlopen(q,timeout=30) as r:return r.status,r.headers,r.read(limit)
_,_,b=get(BASE+"/pro-games?event=8249&series=2396950");s=html.unescape(b.decode("utf-8","ignore"))
s=s.replace("\\u0026","&").replace("\\"","\"")
# Find the event covering Sep 17-20 2026.
events=[]
for m in re.finditer(r'"eventId":"([^"]+)","eventName":"([^"]+)"',s):
 chunk=s[m.start():m.start()+15000]
 fm=re.search(r'"firstMatchTime":(\d+)',chunk);lm=re.search(r'"lastMatchTime":(\d+)',chunk)
 if fm and lm:
  events.append((m.group(1),m.group(2),int(fm.group(1)),int(lm.group(1))))
print("EVENTS")
for e in events:
 if 1789400000<=e[2]<=1790200000: print("RECENT_EVENT",e)
target=next((e for e in events if 1789400000<=e[2]<=1790200000),None)
if not target: raise SystemExit("no Sep17-20 event found")
eid=target[0]
_,_,b=get(BASE+f"/pro-games?event={eid}");p=html.unescape(b.decode("utf-8","ignore")).replace("\\u0026","&").replace("\\"","\"")
# Extract match IDs around de_dust2 entries and prefer whitelist teams via surrounding series data.
ids=[]
for m in re.finditer(r'"matchId":"(hltv-[^"]+)","mapName":"de_dust2"',p):
 mid=m.group(1)
 if mid not in ids: ids.append(mid)
print("DUST2_IDS",ids)
for mid in ids[:10]:
 try:
  st,h,b=get(BASE+"/api/matches/"+urllib.parse.quote(mid),2_000_000)
  o=json.loads(b)
  print("MATCH",mid,o.get("name"),o.get("mapName"),o.get("score"),o.get("matchTime"))
  print("DEMO",o.get("demoUrl"))
  du=o.get("demoUrl")
  if du:
   q=urllib.request.Request(du,headers={"User-Agent":UA,"Range":"bytes=0-31"})
   with urllib.request.urlopen(q,timeout=30) as r:
    head=r.read(32)
    print("VERIFY",r.status,r.headers.get("content-range"),repr(head[:8]),head.startswith(b"PBDEMS2"))
 except Exception as e: print("ERR",mid,repr(e))
