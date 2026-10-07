#!/usr/bin/env python3
import json, urllib.error, urllib.request
from pathlib import Path

IDS=[2398746,2398743,2398742,2398738]
BASE="https://cs.rlin.dev/api/matches"
UA="Mozilla/5.0"
out={}
for mid in IDS:
    rows=[]
    for m in range(1,6):
        rid=f"hltv-{mid}-m{m}"
        u=f"{BASE}/{rid}"
        try:
            req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=30) as r:
                raw=r.read()
                status=r.status
            obj=json.loads(raw.decode("utf-8"))
            meta=obj.get("metadata") if isinstance(obj.get("metadata"),dict) else {}
            row={
              "id":rid,"status":status,
              "mapName":obj.get("mapName"),
              "demoUrl":obj.get("demoUrl") or meta.get("uploadedDemoUrl"),
              "matchTime":obj.get("matchTime"),
              "score":obj.get("score"),
              "team1":obj.get("team1"),
              "team2":obj.get("team2"),
            }
        except urllib.error.HTTPError as e:
            row={"id":rid,"status":e.code}
        except Exception as e:
            row={"id":rid,"error":f"{type(e).__name__}: {e}"}
        rows.append(row)
        print(row)
    out[str(mid)]=rows
Path("data/probes/rlin-exact-recent.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n","utf-8")
