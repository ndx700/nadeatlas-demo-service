#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, json, re, time, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/top20-dust2-bo3.json"
MIRROR=ROOT/"data/top20-dust2-mirrored.json"
TEAMS=ROOT/"config/teams.json"
API="https://api.bo3.gg/api/v1/matches"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"

def norm(s):
    s=re.sub(r"[^a-z0-9]+","",str(s or "").lower())
    for token in ("team","esports","gaming","csgo","cs2"):
        s=s.replace(token,"")
    return s

def is_top(name, tops):
    n=norm(name)
    for t in tops:
        q=norm(t)
        if n==q:
            return t
        # Known branding extensions such as BetBoom Team / Team Falcons.
        if len(q)>=4 and (n.startswith(q) or q.startswith(n)):
            return t
    return None

def fetch_page(offset, limit=100):
    params=[
        ("scope","widget-matches"),
        ("page[offset]",str(offset)),
        ("page[limit]",str(limit)),
        ("sort","-start_date,tier_rank"),
        ("filter[matches.status][in]","finished"),
        ("filter[matches.discipline_id][eq]","1"),
        ("with","teams,tournament,games"),
    ]
    url=API+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={
        "User-Agent":UA,"Accept":"application/json, text/plain, */*",
        "Accept-Language":"en-US,en;q=0.9","Origin":"https://bo3.gg",
        "Referer":"https://bo3.gg/","Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors","Sec-Fetch-Site":"same-site",
    })
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def key(date,a,b):
    return (date,tuple(sorted((norm(a),norm(b)))))

def main():
    today=dt.datetime.now(dt.timezone.utc).date()
    cutoff=today-dt.timedelta(days=61)
    tops=json.loads(TEAMS.read_text("utf-8"))[:20]
    mirrored=json.loads(MIRROR.read_text("utf-8")) if MIRROR.exists() else {"items":[]}
    mirror_keys={key(x.get("date",""),x.get("team1",""),x.get("team2","")):x for x in mirrored.get("items",[])}

    found=[]
    offset=0
    page_no=0
    total_api=None
    while page_no<100:
        obj=fetch_page(offset)
        page_no+=1
        if isinstance(obj.get("total"),dict):
            total_api=obj["total"]
        rows=obj.get("results") or []
        print(f"page={page_no} offset={offset} rows={len(rows)}")
        if not rows:
            break

        page_dates=[]
        for m in rows:
            raw_date=str(m.get("start_date") or "")[:10]
            try:
                day=dt.date.fromisoformat(raw_date)
            except Exception:
                continue
            page_dates.append(day)
            if day<cutoff or day>today:
                continue
            t1=(m.get("team1") or {}).get("name") or ""
            t2=(m.get("team2") or {}).get("name") or ""
            hit1=is_top(t1,tops); hit2=is_top(t2,tops)
            if not (hit1 or hit2):
                continue
            dust=[g for g in (m.get("games") or []) if g.get("map_name")=="de_dust2"]
            if not dust:
                continue
            found.append({
                "date":raw_date,
                "bo3MatchId":m.get("id"),
                "slug":m.get("slug"),
                "url":"https://bo3.gg/matches/"+str(m.get("slug") or ""),
                "event":(m.get("tournament") or {}).get("name") or "",
                "team1":t1,"team2":t2,
                "currentTop20Matched":sorted(set(x for x in (hit1,hit2) if x)),
                "seriesScore":f"{m.get('team1_score','')}-{m.get('team2_score','')}",
                "dust2Maps":[{
                    "bo3GameId":g.get("id"),
                    "number":g.get("number"),
                    "winner":g.get("winner_clan_name"),
                    "loser":g.get("loser_clan_name"),
                    "winnerScore":g.get("winner_clan_score"),
                    "loserScore":g.get("loser_clan_score"),
                } for g in dust],
            })
        oldest=min(page_dates) if page_dates else None
        print(" oldest",oldest,"matchedDust2",len(found))
        if oldest and oldest<cutoff:
            break
        offset += len(rows)
        if len(rows)<100:
            break
        time.sleep(0.25)

    # Deduplicate API duplicates by BO3 id.
    dedup={str(x["bo3MatchId"]):x for x in found}
    found=sorted(dedup.values(),key=lambda x:(x["date"],x["bo3MatchId"] or 0),reverse=True)

    covered=[]; missing=[]
    for x in found:
        mk=key(x["date"],x["team1"],x["team2"])
        mir=mirror_keys.get(mk)
        if mir:
            x["mirror"]={"githubUrl":mir.get("githubUrl"),"matchId":mir.get("matchId"),"size":mir.get("size")}
            covered.append(x)
        else:
            missing.append(x)

    doc={
        "generatedAt":dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z"),
        "range":{"start":cutoff.isoformat(),"end":today.isoformat()},
        "top20":tops,
        "apiTotal":total_api,
        "pagesFetched":page_no,
        "dust2MatchesInvolvingCurrentTop20":len(found),
        "alreadyMirrored":len(covered),
        "missingMirror":len(missing),
        "matches":found,
        "missing":missing,
    }
    OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n","utf-8")
    print("RESULT",json.dumps({
        "dust2Matches":len(found),"alreadyMirrored":len(covered),"missingMirror":len(missing),
        "pagesFetched":page_no
    }))
    for x in missing:
        print("MISSING",x["date"],x["team1"],"vs",x["team2"],"map",x["dust2Maps"][0]["number"],x["url"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
