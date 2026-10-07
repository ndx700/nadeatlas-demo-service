#!/usr/bin/env python3
import json, urllib.parse, urllib.request
from pathlib import Path

BASE="https://api.bo3.gg/api/v1/matches"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
common=[
 ("scope","widget-matches"),("page[offset]","0"),("page[limit]","1"),
 ("sort","-start_date,tier_rank"),
 ("filter[matches.status][in]","finished"),
 ("filter[matches.discipline_id][eq]","1"),
 ("with","teams,tournament,games"),
]
variants={
 "baseline":[],
 "start_gte":[("filter[matches.start_date][gte]","2026-08-07")],
 "start_ge":[("filter[matches.start_date][ge]","2026-08-07")],
 "start_from":[("filter[matches.start_date][from]","2026-08-07")],
 "start_between":[("filter[matches.start_date][between]","2026-08-07,2026-10-07")],
 "team1_legacy":[("filter[matches.team1_id][eq]","8118")],
 "team2_legacy":[("filter[matches.team2_id][eq]","8118")],
 "team_id_legacy":[("filter[matches.team_id][eq]","8118")],
 "teams_id_legacy":[("filter[teams.id][eq]","8118")],
}
out={}
for name,extra in variants.items():
 url=BASE+"?"+urllib.parse.urlencode(common+extra)
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json","Origin":"https://bo3.gg","Referer":"https://bo3.gg/"})
 try:
  with urllib.request.urlopen(req,timeout=30) as r:
   obj=json.loads(r.read().decode())
  out[name]={
   "http":200,
   "total":obj.get("total"),
   "first":[{"id":x.get("id"),"date":x.get("start_date"),"t1":(x.get("team1") or {}).get("name"),"t2":(x.get("team2") or {}).get("name")} for x in (obj.get("results") or [])[:2]]
  }
 except Exception as e:
  out[name]={"error":f"{type(e).__name__}: {e}"}
 print(name,out[name])
Path("data/probes/bo3-filters.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
