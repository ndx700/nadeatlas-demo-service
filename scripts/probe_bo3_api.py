#!/usr/bin/env python3
import json, urllib.parse, urllib.request
from pathlib import Path

OUT=Path("data/probes/bo3-api.json")
BASE="https://api.bo3.gg/api/v1/matches"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
params=[
 ("scope","widget-matches"),
 ("page[offset]","0"),
 ("page[limit]","100"),
 ("sort","-start_date,tier_rank"),
 ("filter[matches.status][in]","finished"),
 ("filter[matches.discipline_id][eq]","1"),
 ("with","teams,tournament,ai_predictions,games,streams"),
]
url=BASE+"?"+urllib.parse.urlencode(params)
req=urllib.request.Request(url,headers={
 "User-Agent":UA,
 "Accept":"application/json, text/plain, */*",
 "Accept-Language":"en-US,en;q=0.9",
 "Origin":"https://bo3.gg",
 "Referer":"https://bo3.gg/",
 "Sec-Fetch-Dest":"empty",
 "Sec-Fetch-Mode":"cors",
 "Sec-Fetch-Site":"same-site",
})
with urllib.request.urlopen(req,timeout=60) as r:
 raw=r.read()
 status=r.status
 headers=dict(r.headers.items())
print("HTTP",status,"bytes",len(raw),"type",headers.get("Content-Type"))
obj=json.loads(raw.decode("utf-8"))
summary={"url":url,"http":status,"bytes":len(raw),"type":type(obj).__name__}
if isinstance(obj,dict):
 summary["topKeys"]=list(obj.keys())
 for k,v in obj.items():
  if isinstance(v,list):
   summary["listKey"]=k
   summary["count"]=len(v)
   summary["firstItems"]=v[:5]
   break
  if isinstance(v,dict):
   summary.setdefault("dictKeys",{})[k]=list(v.keys())[:30]
 # Preserve useful first page but cap huge structures by taking first 10 records.
 for key in ("data","results","matches","items"):
  if isinstance(obj.get(key),list):
   summary["records"]=obj[key][:10]
   break
elif isinstance(obj,list):
 summary["count"]=len(obj)
 summary["records"]=obj[:10]
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n","utf-8")
print(json.dumps({k:v for k,v in summary.items() if k not in ("firstItems","records")},ensure_ascii=False))
print("WROTE",OUT)
