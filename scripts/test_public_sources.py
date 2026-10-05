#!/usr/bin/env python3
import json,time,urllib.request,urllib.parse
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
TARGETS=["rare atom","secret","pressure monsters","the knockoutx","wept","chaos gaming"]
known=["g201-20260922154948491976189","g201-20260922165611262612321","g201-20260922154931086591845"]

def getj(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/json"}),timeout=20) as r:
  return json.loads(r.read())

found=[]
for status in [2,1,0]:
 for page in range(1,31):
  u=f"https://app.5eplay.com/api/tournament/session_list?game_status={status}&game_type=1&grades=&page={page}&limit=20"
  try:o=getj(u)
  except Exception as e:
   print("LIST_ERR",status,page,repr(e)); break
  data=o.get("data",{}); rows=data.get("matches",[]) if isinstance(data,dict) else []
  if not rows: break
  for row in rows:
   mc=row.get("mc_info",{})
   t1=(mc.get("t1_info") or {}).get("disp_name","")
   t2=(mc.get("t2_info") or {}).get("disp_name","")
   ts=mc.get("plan_ts",0)
   date=time.strftime("%Y-%m-%d %H:%M",time.localtime(int(ts))) if str(ts).isdigit() else str(ts)
   names=(str(t1)+" "+str(t2)).lower()
   if "2026-09-22" in date and any(x in names for x in TARGETS):
    rec=(mc.get("id"),date,t1,t2,mc.get("format"))
    if rec not in found: found.append(rec); print("MATCH",rec)
print("FOUND",len(found))
for mid,date,t1,t2,fmt in found:
 if not mid: continue
 u=f"https://esports-data.5eplaycdn.com/v1/api/csgo/matches/{mid}/data"
 try:
  o=getj(u); raw=json.dumps(o,ensure_ascii=False)
  print("\nDETAIL",mid,date,t1,"vs",t2,"BYTES",len(raw))
  for gid in known:
   if gid in raw: print("KNOWN_GAMEID_IN_DATA",gid)
  import re
  gs=sorted(set(re.findall(r'g201-[0-9A-Za-z-]+',raw)))
  print("G201_VALUES",gs[:30])
  data=o.get("data",{}); match=data.get("match",{}) if isinstance(data,dict) else {}
  mc=match.get("mc_info",{}) if isinstance(match,dict) else {}
  print("MC_KEYS",sorted(mc.keys()) if isinstance(mc,dict) else None)
  bouts=match.get("bouts_state",[]) if isinstance(match,dict) else []
  print("MAPS",[(b.get("bout_num"),b.get("map_name"),b.get("status"),b.get("t1_all_score"),b.get("t2_all_score")) for b in bouts if isinstance(b,dict)])
 except Exception as e: print("DETAIL_ERR",mid,repr(e))
