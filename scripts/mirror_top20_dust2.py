#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"index.json"
TEAMS=ROOT/"config/teams.json"
OUT=ROOT/"data/top20-dust2-mirrored.json"
REPO=os.getenv("GITHUB_REPOSITORY","ndx700/nadeatlas-demo-service")
TAG="demos"
UA="NadeAtlas-Demo-Mirror/1.0"


def slug(s:str)->str:
    return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-") or "team"


def gh(*args, check=True):
    return subprocess.run(["gh",*args],check=check,text=True,capture_output=True)


def ensure_release():
    if gh("release","view",TAG,check=False).returncode != 0:
        subprocess.run([
            "gh","release","create",TAG,
            "--title","NadeAtlas verified demos",
            "--notes","Verified CS2 professional demos."
        ],check=True)


def existing_assets():
    r=gh("release","view",TAG,"--json","assets")
    obj=json.loads(r.stdout)
    return {x["name"]:int(x.get("size") or 0) for x in obj.get("assets",[])}


def download(url: str, path: Path):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=240) as r, path.open("wb") as f:
        while True:
            b=r.read(4*1024*1024)
            if not b:
                break
            f.write(b)


def validate(path: Path):
    size=path.stat().st_size
    with path.open("rb") as f:
        head=f.read(16)
    if size < 100_000_000:
        raise RuntimeError(f"demo too small: {size}")
    if not head.startswith((b"PBDEMS2",b"HL2DEMO")):
        raise RuntimeError(f"bad demo header: {head!r}")
    return size,head


def main():
    top20=json.loads(TEAMS.read_text("utf-8"))[:20]
    top20_set={x.casefold() for x in top20}
    entries=json.loads(INDEX.read_text("utf-8"))
    today=dt.datetime.now(dt.timezone.utc).date()
    start=today-dt.timedelta(days=61)

    selected=[]
    for x in entries:
        try:
            day=dt.date.fromisoformat(x["date"])
        except Exception:
            continue
        if not (start <= day <= today):
            continue
        if x.get("map")!="de_dust2":
            continue
        if x.get("team1","").casefold() not in top20_set and x.get("team2","").casefold() not in top20_set:
            continue
        selected.append(x)

    selected.sort(key=lambda x:x["date"])
    print(f"Top20={top20}")
    print(f"Range={start}..{today}")
    print(f"Selected verified mirrors={len(selected)}")

    ensure_release()
    assets=existing_assets()
    manifest=[]

    with tempfile.TemporaryDirectory() as td:
        work=Path(td)
        for i,x in enumerate(selected,1):
            filename=f"{x['date']}-{slug(x['team1'])}-vs-{slug(x['team2'])}-dust2.dem"
            public=f"https://github.com/{REPO}/releases/download/{TAG}/{urllib.parse.quote(filename)}"
            expected=int(x.get("size") or 0)
            print(f"[{i}/{len(selected)}] {filename}")
            if filename in assets and (not expected or assets[filename]==expected):
                print(f"  already uploaded ({assets[filename]} bytes)")
                size=assets[filename]
                state="already"
            else:
                path=work/filename
                download(x["url"],path)
                size,head=validate(path)
                print(f"  downloaded {size} bytes head={head!r}")
                subprocess.run(["gh","release","upload",TAG,str(path),"--clobber"],check=True)
                path.unlink(missing_ok=True)
                assets[filename]=size
                state="uploaded"
            manifest.append({
                "date":x["date"],
                "event":x.get("event",""),
                "team1":x.get("team1",""),
                "team2":x.get("team2",""),
                "score":x.get("score",""),
                "map":"de_dust2",
                "matchId":x.get("matchId"),
                "sourceUrl":x.get("url"),
                "githubUrl":public,
                "size":size,
                "state":state,
            })

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "generatedAt":dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z"),
        "range":{"start":start.isoformat(),"end":today.isoformat()},
        "top20":top20,
        "count":len(manifest),
        "items":manifest,
    },ensure_ascii=False,indent=2)+"\n","utf-8")
    print(f"WROTE {OUT} count={len(manifest)}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
