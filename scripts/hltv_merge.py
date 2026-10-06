#!/usr/bin/env python3
"""Merge the HLTV replays the app uploaded (data/hltv/<matchId>.json) into the public indexes.

The phone's online build finds each demo on HLTV through a real WebView, parses it there and puts one replay
(.nar) per map into the "hltv-replays" release, plus a record here. This turns those records into index entries:
Dust2 into index.json, every map into index-all-maps.json. An entry with the same matchId that came from another
source keeps its data and gains the replay link. Newest first. Prints how many were added.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data" / "hltv"
FIELDS = ("date", "event", "team1", "team2", "score", "map", "url", "matchId", "replay", "replaySize", "source", "hltvMatch")


def load(p):
    return json.loads(p.read_text("utf-8")) if p.exists() else []


def merge(index, rec):
    for x in index:
        if x.get("matchId") == rec["matchId"]:
            changed = False
            for k in ("replay", "replaySize"):
                if rec.get(k) and x.get(k) != rec[k]:
                    x[k] = rec[k]; changed = True
            for k in ("score", "event"):
                if rec.get(k) and not x.get(k):
                    x[k] = rec[k]; changed = True
            return changed, False
    index.append({k: rec[k] for k in FIELDS if rec.get(k) not in (None, "")})
    return True, True


def main():
    records = []
    for p in sorted(RECORDS.glob("hltv-*.json")):
        try:
            r = json.loads(p.read_text("utf-8"))
        except ValueError as e:
            print(f"skip {p.name}: {e}"); continue
        ok = (str(r.get("matchId", "")) == p.stem and str(r.get("replay", "")).startswith("https://github.com/")
              and str(r.get("map", "")).startswith("de_") and r.get("team1") and r.get("team2") and r.get("date"))
        if not ok:
            print(f"skip {p.name}: incomplete"); continue
        records.append(r)
    dust2 = load(ROOT / "index.json")
    every = load(ROOT / "index-all-maps.json")
    added = changed_any = 0
    for r in records:
        c1, a1 = merge(every, r)
        c2, a2 = (merge(dust2, r) if r["map"] == "de_dust2" else (False, False))
        added += a1 or a2
        changed_any += c1 or c2
    if changed_any:
        for name, idx in (("index.json", dust2), ("index-all-maps.json", every)):
            idx.sort(key=lambda x: x.get("date", ""), reverse=True)   # the same order sync.py keeps
            (ROOT / name).write_text(json.dumps(idx, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"hltv records {len(records)}, new entries {added}, changed {changed_any}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
