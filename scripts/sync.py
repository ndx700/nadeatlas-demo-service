#!/usr/bin/env python3
# sync trigger: corrected API secret configured
from __future__ import annotations
import datetime as dt, json, os, re, shutil, subprocess, tempfile, time
import urllib.error, urllib.parse, urllib.request, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"index.json"; STATUS=ROOT/"status.json"
TEAMS=set(json.loads((ROOT/"config/teams.json").read_text("utf-8")))
API="https://api.better-cs-api.com"
KEY=os.getenv("BETTER_CS_API_KEY","").strip()
REPO=os.getenv("GITHUB_REPOSITORY","ndx700/nadeatlas-demo-service")
UA="NadeAtlas-Demo-Service/1.0"

def api(method,path,query=None,body=None,timeout=60):
    url=API+path
    if query: url+="?"+urllib.parse.urlencode(query,doseq=True)
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(url,data=data,method=method,headers={
        "Authorization":f"Bearer {KEY}","Accept":"application/json","User-Agent":UA})
    if data is not None: req.add_header("Content-Type","application/json")
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read()
        return json.loads(raw.decode()) if raw else {}

def status(state,message,**extra):
    obj={"state":state,"message":message,
         "updatedAt":dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z"),**extra}
    STATUS.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n","utf-8")

def arr(obj):
    if isinstance(obj,list): return obj
    if isinstance(obj,dict):
        for k in ("results","matches","data","items"):
            if isinstance(obj.get(k),list): return obj[k]
    return []

def name(v): return v.get("name","") if isinstance(v,dict) else str(v or "")

def day(ms):
    try: return dt.datetime.fromtimestamp(int(ms)/1000,dt.timezone.utc).date().isoformat()
    except Exception: return str(ms or "")[:10]

def results(start,end):
    try: return arr(api("GET","/hltv/results",{"startDate":start,"endDate":end}))
    except Exception: return arr(api("GET","/hltv/results"))

def create_demo(demo_id):
    obj=api("POST","/hltv/demo",body={"demoId":demo_id})
    if isinstance(obj,dict):
        for k in ("taskId","task_id","id"):
            if obj.get(k) is not None: return str(obj[k]),obj
    raise RuntimeError("demo task id missing")

def demo_url(task_id,obj):
    for _ in range(30):
        if isinstance(obj,dict):
            for k in ("url","downloadUrl","download_url"):
                if obj.get(k): return str(obj[k])
            if str(obj.get("status","")).lower() in ("failed","error","cancelled"):
                raise RuntimeError("demo task failed")
        time.sleep(4)
        obj=api("GET",f"/hltv/demo/{urllib.parse.quote(task_id)}")
    raise TimeoutError("demo task timeout")

def download(url,out):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=180) as r,out.open("wb") as f:
        if "text/html" in (r.headers.get("Content-Type") or "").lower():
            raise RuntimeError("download returned HTML")
        shutil.copyfileobj(r,f)
    if out.stat().st_size<1024: raise RuntimeError("download too small")

def dust2_dem(src,work,only_completed_map):
    if zipfile.is_zipfile(src):
        with zipfile.ZipFile(src) as z:
            c=[n for n in z.namelist() if n.lower().endswith(".dem") and "dust2" in n.lower()]
            if len(c)!=1: raise RuntimeError(f"Dust2 members: {len(c)}")
            out=work/Path(c[0]).name
            with z.open(c[0]) as r,out.open("wb") as w: shutil.copyfileobj(r,w)
            return out
    head=src.read_bytes()[:16]
    if only_completed_map and (head.startswith(b"PBDEMS2") or head.startswith(b"HL2DEMO")):
        return src
    listing=subprocess.run(["7z","l","-ba",str(src)],capture_output=True,text=True)
    c=[]
    for line in listing.stdout.splitlines():
        m=re.search(r"([^\\/\s]*dust2[^\\/\s]*\.dem)\s*$",line,re.I)
        if m: c.append(m.group(1))
    c=list(dict.fromkeys(c))
    if len(c)!=1: raise RuntimeError(f"Dust2 members: {len(c)}")
    subprocess.run(["7z","e","-y",f"-o{work}",str(src),c[0]],check=True)
    return work/Path(c[0]).name

def slug(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-") or "team"

def upload(path):
    tag="demos"
    if subprocess.run(["gh","release","view",tag],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
        subprocess.run(["gh","release","create",tag,"--title","NadeAtlas verified demos",
                        "--notes","Verified CS2 demos for NadeAtlas."],check=True)
    subprocess.run(["gh","release","upload",tag,str(path),"--clobber"],check=True)
    return f"https://github.com/{REPO}/releases/download/{tag}/{urllib.parse.quote(path.name)}"

RLIN="https://cs.rlin.dev"

def http_bytes(url,headers=None,timeout=45,limit=None):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*",**(headers or {})})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return r.status,r.headers,r.read() if limit is None else r.read(limit)

def rlin_json(path):
    _,_,raw=http_bytes(RLIN+path,{"Accept":"application/json"},45,2_000_000)
    return json.loads(raw.decode("utf-8"))

def verify_direct_dem(url):
    # Reject suspicious map-label mismatches rather than risk publishing the wrong map.
    if "dust2" not in urllib.parse.unquote(url).lower():
        raise RuntimeError("direct demo URL is not labelled dust2")
    code,h,head=http_bytes(url,{"Range":"bytes=0-31"},45,32)
    if code not in (200,206):
        raise RuntimeError(f"demo probe HTTP {code}")
    if not (head.startswith(b"PBDEMS2") or head.startswith(b"HL2DEMO")):
        raise RuntimeError("invalid CS2 demo header")
    ctype=(h.get("Content-Type") or "").lower()
    if "text/html" in ctype:
        raise RuntimeError("demo probe returned HTML")
    size=0
    cr=h.get("Content-Range") or ""
    m=re.search(r"/(\\d+)\\s*$",cr)
    if m: size=int(m.group(1))
    elif h.get("Content-Length"): size=int(h.get("Content-Length"))
    if size<1_000_000:
        raise RuntimeError(f"demo size suspicious: {size}")
    return size

def sync_rlin(existing,known,now):
    errors=[];added=0;checked=0
    try:
        _,_,raw=http_bytes(RLIN+"/pro-games?event=8249",{"Accept":"text/html"},45,5_000_000)
        page=raw.decode("utf-8","ignore")
        event_ids=list(dict.fromkeys(re.findall(r'eventId\\\\\\":\\\\\\"(\\d+)',page)))
        # The server-rendered event list is newest-first. Limit requests and still cover
        # the rolling recent window; individual matches are date-filtered again below.
        event_ids=event_ids[:8]
        if not event_ids:
            raise RuntimeError("no public event IDs discovered")
    except Exception as e:
        return {"state":"error","message":f"{type(e).__name__}: {e}","checked":0,"added":0},errors

    cutoff=now-dt.timedelta(days=62)
    match_ids=[]
    for eid in event_ids:
        try:
            _,_,raw=http_bytes(RLIN+f"/pro-games?event={urllib.parse.quote(eid)}",
                               {"Accept":"text/html"},45,8_000_000)
            text=raw.decode("utf-8","ignore")
            ids=re.findall(r'matchId\\\\\\":\\\\\\"(hltv-[^\\\\\\"]+)\\\\\\",\\\\\\"mapName\\\\\\":\\\\\\"de_dust2',text)
            for mid in ids:
                if mid not in match_ids: match_ids.append(mid)
        except Exception as e:
            errors.append(f"rlin event {eid}: {type(e).__name__}: {e}")

    for mid in match_ids[:120]:
        try:
            m=rlin_json("/api/matches/"+urllib.parse.quote(mid,safe=""))
            checked+=1
            if m.get("mapName")!="de_dust2": continue
            ts=m.get("matchTime")
            if not ts: continue
            date_obj=dt.datetime.fromtimestamp(int(ts),dt.timezone.utc).date()
            if date_obj<cutoff or date_obj>now: continue
            meta=m.get("metadata") if isinstance(m.get("metadata"),dict) else {}
            teams=meta.get("teams") if isinstance(meta.get("teams"),list) else []
            if len(teams)<2: continue
            a=name(teams[0]); b=name(teams[1])
            if a not in TEAMS and b not in TEAMS: continue
            date=date_obj.isoformat(); key=(date,a,b,"de_dust2")
            if key in known: continue
            url=str(m.get("demoUrl") or meta.get("uploadedDemoUrl") or "")
            if not url.startswith("https://"): continue
            size=verify_direct_dem(url)
            existing.append({"date":date,"event":str(meta.get("eventName") or ""),
                             "team1":a,"team2":b,"score":str(m.get("score") or ""),
                             "map":"de_dust2","url":url,"size":size})
            known.add(key);added+=1
        except urllib.error.HTTPError as e:
            if e.code!=404: errors.append(f"rlin {mid}: HTTP {e.code}")
        except Exception as e:
            errors.append(f"rlin {mid}: {type(e).__name__}: {e}")
    state="ok" if checked or added else ("partial" if match_ids else "empty")
    return {"state":state,"events":len(event_ids),"dust2Candidates":len(match_ids),
            "checked":checked,"added":added},errors

def main():
    existing=json.loads(INDEX.read_text("utf-8"))
    known={(x.get("date"),x.get("team1"),x.get("team2"),x.get("map")) for x in existing}
    now=dt.datetime.now(dt.timezone.utc).date()
    sources={}; all_errors=[]

    # Free public source first. It exposes one direct .dem per map, which matches
    # NadeAtlas' contract and avoids downloading an entire BO3 just to keep Dust2.
    rlin_state,rlin_errors=sync_rlin(existing,known,now)
    sources["public_pro_demo"]=rlin_state
    all_errors.extend(rlin_errors)

    better_added=0
    if not KEY:
        sources["better_cs"]={"state":"needs_api_key","added":0}
    else:
        try:
            found=results((now-dt.timedelta(days=62)).isoformat(),now.isoformat())
            candidates=[x for x in found if isinstance(x,dict) and
                        (name(x.get("team1")) in TEAMS or name(x.get("team2")) in TEAMS)]
            for item in candidates[:100]:
                mid=item.get("id") or item.get("matchId")
                if not mid: continue
                try:
                    m=api("GET",f"/hltv/matches/{mid}")
                    if str(m.get("status","")).lower() not in ("over","finished","ended"): continue
                    a,b=name(m.get("team1")),name(m.get("team2"))
                    if a not in TEAMS and b not in TEAMS: continue
                    maps=[x for x in m.get("maps",[]) if isinstance(x,dict) and isinstance(x.get("result"),dict)]
                    d2=[x for x in maps if x.get("name")=="de_dust2"]
                    if len(d2)!=1 or not m.get("hasDemo") or m.get("demoId") is None: continue
                    date=day(m.get("date")); key=(date,a,b,"de_dust2")
                    if key in known: continue
                    tid,obj=create_demo(m["demoId"]); url=demo_url(tid,obj)
                    with tempfile.TemporaryDirectory() as td:
                        work=Path(td); src=work/"download.bin"; download(url,src)
                        dem=dust2_dem(src,work,len(maps)==1)
                        filename=f"{date}-{slug(a)}-vs-{slug(b)}-dust2.dem"
                        final=work/filename
                        if dem!=final: shutil.copy2(dem,final)
                        public=upload(final)
                        r=d2[0]["result"]; score=f"{r.get('team1TotalRounds','')}-{r.get('team2TotalRounds','')}".strip("-")
                        ev=m.get("event") if isinstance(m.get("event"),dict) else {}
                        existing.append({"date":date,"event":ev.get("name",""),"team1":a,"team2":b,
                                         "score":score,"map":"de_dust2","url":public,"size":final.stat().st_size})
                        known.add(key);better_added+=1
                except Exception as e:
                    all_errors.append(f"better match {mid}: {type(e).__name__}: {e}")
            sources["better_cs"]={"state":"ok","scanned":len(found),"candidates":len(candidates),
                                  "added":better_added}
        except urllib.error.HTTPError as e:
            if e.code==402: sources["better_cs"]={"state":"payment_required","added":0}
            else: sources["better_cs"]={"state":"api_error","http":e.code,"added":0}
        except Exception as e:
            sources["better_cs"]={"state":"api_error","error":type(e).__name__,"added":0}

    existing.sort(key=lambda x:x.get("date",""),reverse=True)
    INDEX.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+"\n","utf-8")
    total_added=int(rlin_state.get("added",0))+better_added
    usable=rlin_state.get("state") in ("ok","partial") or sources["better_cs"].get("state")=="ok"
    status("ok" if usable else "degraded",
           "multi-source sync completed",sources=sources,added=total_added,
           published=len(existing),errors=all_errors[:20])
    return 0

if __name__=="__main__": raise SystemExit(main())
