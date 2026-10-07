#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode, urljoin

from playwright.sync_api import sync_playwright

BASE = "https://www.hltv.org"
RLIN = "https://cs.rlin.dev"
UA = "NadeAtlas-HLTV-Discovery/1.0"


def body_text(page) -> str:
    try:
        return page.evaluate("() => document.body ? document.body.innerText : ''")
    except Exception:
        return ""


def ensure_hltv_page(page, label: str, timeout_ms: int = 45000) -> None:
    deadline = time.time() + timeout_ms / 1000
    last = ""
    while time.time() < deadline:
        title = page.title()
        text = body_text(page)
        low = (title + "\n" + text[:1000]).lower()
        last = low[:500]
        if "you have been blocked" in low:
            raise RuntimeError(f"{label}: HLTV IP block page")
        if "just a moment" not in low and "performing security verification" not in low:
            return
        page.wait_for_timeout(3000)
    raise RuntimeError(f"{label}: Cloudflare challenge did not clear: {last!r}")


def goto_hltv(page, url: str, label: str) -> None:
    last_exc = None
    for attempt in range(3):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            ensure_hltv_page(page, label)
            return
        except Exception as exc:
            last_exc = exc
            page.wait_for_timeout(4000 + attempt * 3000)
    raise RuntimeError(f"{label}: navigation failed: {last_exc}")


def parse_team_id(href: str) -> int | None:
    m = re.search(r"/team/(\d+)/", href or "")
    return int(m.group(1)) if m else None


def parse_match_id(href: str) -> int | None:
    m = re.search(r"/matches/(\d+)/", href or "")
    return int(m.group(1)) if m else None


def hltv_top20(page) -> tuple[str, list[dict]]:
    goto_hltv(page, f"{BASE}/ranking/teams/", "ranking")
    ranking_url = page.url
    teams = page.evaluate(
        """() => Array.from(document.querySelectorAll('.ranked-team')).slice(0, 20).map((el) => ({
            place: Number((el.querySelector('.position')?.textContent || '').replace('#','')),
            name: (el.querySelector('.name')?.textContent || '').trim(),
            href: el.querySelector('.moreLink')?.getAttribute('href') || ''
        }))"""
    )
    out = []
    for x in teams:
        tid = parse_team_id(x.get("href", ""))
        if tid and x.get("name"):
            out.append({"place": x.get("place"), "name": x["name"], "id": tid})
    if len(out) != 20:
        raise RuntimeError(f"ranking parse expected 20 teams, got {len(out)}")
    return ranking_url, out


def result_rows(page, start: str, end: str, offset: int) -> list[dict]:
    query = urlencode([
        ("startDate", start),
        ("endDate", end),
        ("map", "de_dust2"),
        ("content", "demo"),
        ("offset", str(offset)),
    ])
    url = f"{BASE}/results?{query}"
    goto_hltv(page, url, f"results offset {offset}")
    rows = page.evaluate(
        """() => Array.from(document.querySelectorAll('.result-con')).map((el) => {
            const a = el.querySelector('a');
            const teams = Array.from(el.querySelectorAll('div.team')).map(x => (x.textContent || '').trim());
            return {
                href: a?.getAttribute('href') || '',
                unix: el.getAttribute('data-zonedgrouping-entry-unix') || '',
                team1: teams[0] || '',
                team2: teams[teams.length - 1] || '',
                format: (el.querySelector('.map-text')?.textContent || '').trim()
            };
        })"""
    )
    return rows


def iso_from_unix_ms(v: str) -> str:
    try:
        n = int(v)
        if n > 10_000_000_000:
            n //= 1000
        return dt.datetime.fromtimestamp(n, dt.timezone.utc).date().isoformat()
    except Exception:
        return ""


def match_details(page, match_id: int, href: str) -> dict:
    url = urljoin(BASE, href)
    goto_hltv(page, url, f"match {match_id}")
    data = page.evaluate(
        """() => ({
            title: document.title,
            dateUnix: document.querySelector('.timeAndEvent .date')?.getAttribute('data-unix') || '',
            event: (document.querySelector('.timeAndEvent .event a')?.textContent || '').trim(),
            team1: (document.querySelector('.team1-gradient .teamName')?.textContent || '').trim(),
            team2: (document.querySelector('.team2-gradient .teamName')?.textContent || '').trim(),
            demoLink: document.querySelector('[data-demo-link]')?.getAttribute('data-demo-link') || '',
            maps: Array.from(document.querySelectorAll('.mapholder')).map((el, i) => ({
                index: i + 1,
                name: (el.querySelector('.mapname')?.textContent || '').trim(),
                score1: (el.querySelector('.results-left .results-team-score')?.textContent || '').trim(),
                score2: (el.querySelector('.results-right .results-team-score')?.textContent || '').trim()
            }))
        })"""
    )
    dust = [m for m in data["maps"] if m.get("name", "").lower() in ("dust2", "dust 2")]
    if len(dust) != 1:
        raise RuntimeError(f"match {match_id}: expected exactly one Dust2 map, got {len(dust)}")
    data["matchId"] = match_id
    data["url"] = url
    data["dust2"] = dust[0]
    data["date"] = iso_from_unix_ms(data.get("dateUnix", ""))
    return data


def rlin_lookup(match_id: int, map_index: int) -> dict:
    rid = f"hltv-{match_id}-m{map_index}"
    url = f"{RLIN}/api/matches/{rid}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            obj = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"id": rid, "available": False, "http": 404}
        return {"id": rid, "available": False, "http": exc.code, "error": str(exc)}
    except Exception as exc:
        return {"id": rid, "available": False, "error": f"{type(exc).__name__}: {exc}"}

    meta = obj.get("metadata") if isinstance(obj.get("metadata"), dict) else {}
    direct = str(obj.get("demoUrl") or meta.get("uploadedDemoUrl") or "")
    map_name = str(obj.get("mapName") or "")
    return {
        "id": rid,
        "available": bool(direct.startswith("https://")) and map_name == "de_dust2",
        "mapName": map_name,
        "demoUrl": direct,
        "matchTime": obj.get("matchTime"),
        "score": obj.get("score"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=62)
    ap.add_argument("--out", default="data/top20-dust2-discovery.json")
    args = ap.parse_args()

    end = dt.datetime.now(dt.timezone.utc).date()
    start = end - dt.timedelta(days=args.days)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = browser.new_context(locale="en-US")
        page = ctx.new_page()

        print("[1] Establish HLTV session")
        goto_hltv(page, f"{BASE}/", "home")
        page.wait_for_timeout(3000)

        print("[2] Read current HLTV top 20")
        ranking_url, top20 = hltv_top20(page)
        top_names = {x["name"].casefold() for x in top20}
        print("TOP20:", ", ".join(x["name"] for x in top20))

        print(f"[3] Scan Dust2 results with demos: {start} .. {end}")
        candidates = {}
        total_rows = 0
        for offset in range(0, 1000, 100):
            rows = result_rows(page, start.isoformat(), end.isoformat(), offset)
            total_rows += len(rows)
            print(f"  offset={offset} rows={len(rows)}")
            if not rows:
                break
            for row in rows:
                if row.get("team1", "").casefold() not in top_names and row.get("team2", "").casefold() not in top_names:
                    continue
                mid = parse_match_id(row.get("href", ""))
                if mid:
                    row["matchId"] = mid
                    row["date"] = iso_from_unix_ms(row.get("unix", ""))
                    candidates[mid] = row
            if len(rows) < 100:
                break
            page.wait_for_timeout(1200)

        print(f"  candidate matches involving Top20: {len(candidates)}")

        print("[4] Resolve Dust2 map index + RLIN mirror coverage")
        matches = []
        for i, mid in enumerate(sorted(candidates, key=lambda x: candidates[x].get("unix", ""), reverse=True), 1):
            row = candidates[mid]
            try:
                detail = match_details(page, mid, row["href"])
                mirror = rlin_lookup(mid, int(detail["dust2"]["index"]))
                detail["resultRow"] = row
                detail["rlin"] = mirror
                matches.append(detail)
                print(
                    f"  {i:02d}/{len(candidates)} {detail['date']} "
                    f"{detail['team1']} vs {detail['team2']} "
                    f"Dust2=m{detail['dust2']['index']} "
                    f"mirror={'YES' if mirror.get('available') else 'NO'}"
                )
            except Exception as exc:
                matches.append({
                    "matchId": mid,
                    "url": urljoin(BASE, row.get("href", "")),
                    "resultRow": row,
                    "error": f"{type(exc).__name__}: {exc}",
                })
                print(f"  {i:02d}/{len(candidates)} match {mid} ERROR: {exc}")
            page.wait_for_timeout(900)

        browser.close()

    available = [m for m in matches if m.get("rlin", {}).get("available")]
    missing = [m for m in matches if not m.get("rlin", {}).get("available")]
    doc = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "range": {"start": start.isoformat(), "end": end.isoformat(), "days": args.days},
        "rankingUrl": ranking_url,
        "top20": top20,
        "resultsRowsScanned": total_rows,
        "candidateMatches": len(candidates),
        "mirrorAvailable": len(available),
        "mirrorMissing": len(missing),
        "matches": matches,
    }
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"RESULT candidates={len(candidates)} mirrorAvailable={len(available)} mirrorMissing={len(missing)}")
    print(f"WROTE {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
