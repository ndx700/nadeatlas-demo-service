#!/usr/bin/env python3
"""World ranking, upcoming matches and recent results for the app's "赛事" screen.

The data comes from HLTV's public pages through the open-source hltv-api library
(https://github.com/SocksPls/hltv-api, AGPL-3.0), which this script downloads and runs unchanged;
none of its code is kept in this repository. The library asks for a handful of pages like a browser
would and does nothing to get past Cloudflare: when HLTV turns the request away, the previous files
are left as they are and feed/status.json says so.

Output, all UTF-8 JSON:
  feed/ranking.json  {"updatedAt", "teams":   [{"rank", "name", "points", "players": [..]}]}
  feed/matches.json  {"updatedAt", "matches": [{"at" (UTC epoch seconds), "team1", "team2", "event"}]}
  feed/results.json  {"updatedAt", "results": [{"date", "team1", "team2", "score1", "score2", "event"}]}
"""
from __future__ import annotations
import datetime as dt, importlib.util, json, os, sys, time, urllib.request, zoneinfo
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "feed"
SOURCE = "https://raw.githubusercontent.com/SocksPls/hltv-api/master/main.py"
HLTV_ZONE = zoneinfo.ZoneInfo("Europe/Copenhagen")


def library():
    """The library, fetched fresh and loaded from a temporary file."""
    target = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "hltv_api_main.py"
    with urllib.request.urlopen(SOURCE, timeout=30) as r:
        target.write_bytes(r.read())
    spec = importlib.util.spec_from_file_location("hltv_api_main", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write(name, key, rows):
    (FEED / name).write_text(json.dumps({"updatedAt": now(), key: rows}, ensure_ascii=False, indent=1) + "\n", "utf-8")


def ranking(api):
    rows = []
    for t in api.top30teams() or []:
        name = (t.get("name") or "").strip()
        if not name:
            continue
        rows.append({"rank": t.get("rank"), "name": name, "points": t.get("rank-points"),
                     "players": [p.get("name") for p in t.get("team-players") or [] if p.get("name")]})
    if len(rows) < 10:
        raise RuntimeError(f"ranking page gave {len(rows)} teams")
    return sorted(rows, key=lambda r: r["rank"] or 999)


def matches(api):
    rows = []
    for m in api.get_matches() or []:
        if not m.get("team1") or not m.get("team2") or not m.get("date") or not m.get("time"):
            continue
        # The library gives the day and time as HLTV shows them (Danish time, which is also this process's time zone).
        at = dt.datetime.strptime(m["date"] + " " + m["time"], "%Y-%m-%d %H:%M").replace(tzinfo=HLTV_ZONE)
        rows.append({"at": int(at.timestamp()), "team1": m["team1"], "team2": m["team2"], "event": m.get("event") or ""})
    return sorted(rows, key=lambda r: r["at"])[:80]


def results(api):
    rows = []
    for r in api.get_results() or []:
        if not r.get("team1") or not r.get("team2") or r.get("team1score") is None:
            continue
        rows.append({"date": r.get("date") or "", "team1": r["team1"], "team2": r["team2"],
                     "score1": r.get("team1score"), "score2": r.get("team2score"), "event": (r.get("event") or "").strip()})
    return rows[:80]


def main():
    FEED.mkdir(exist_ok=True)
    os.environ["TZ"] = "Europe/Copenhagen"
    time.tzset()
    status = {"updatedAt": now(), "sections": {}}
    try:
        api = library()
    except Exception as e:  # noqa: BLE001
        status["sections"]["library"] = {"state": "error", "message": f"{type(e).__name__}: {e}"[:200]}
        (FEED / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1) + "\n", "utf-8")
        return 0
    for name, key, make in (("ranking.json", "teams", ranking), ("matches.json", "matches", matches), ("results.json", "results", results)):
        try:
            rows = make(api)
            if not rows:
                raise RuntimeError("no rows (the page was probably refused)")
            write(name, key, rows)
            status["sections"][key] = {"state": "ok", "count": len(rows)}
        except Exception as e:  # noqa: BLE001
            # Blocked or changed page: keep what was published before and say what happened.
            status["sections"][key] = {"state": "error", "message": f"{type(e).__name__}: {e}"[:200]}
        time.sleep(2)
    (FEED / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(json.dumps(status, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
