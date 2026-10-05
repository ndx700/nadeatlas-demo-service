#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, json, os, re, shutil, subprocess, tempfile, time
import urllib.parse, urllib.request, zipfile
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

def main():
    existing=json.loads(INDEX.read_text("utf-8"))
    if not KEY:
        status("needs_api_key","BETTER_CS_API_KEY is not configured",published=len(existing))
        return 2
    known={(x.get("date"),x.get("team1"),x.get("team2"),x.get("map")) for x in existing}
    now=dt.datetime.now(dt.timezone.utc).date()
    found=results((now-dt.timedelta(days=62)).isoformat(),now.isoformat())
    candidates=[x for x in found if isinstance(x,dict) and
                (name(x.get("team1")) in TEAMS or name(x.get("team2")) in TEAMS)]
    added=0; errors=[]
    for s in candidates[:100]:
        mid=s.get("id") or s.get("matchId")
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
                known.add(key); added+=1
        except Exception as e:
            errors.append(f"match {mid}: {type(e).__name__}: {e}")
    existing.sort(key=lambda x:x.get("date",""),reverse=True)
    INDEX.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+"\n","utf-8")
    status("ok","sync completed",scanned=len(found),candidates=len(candidates),
           added=added,published=len(existing),errors=errors[:10])
    return 0

if __name__=="__main__": raise SystemExit(main())
