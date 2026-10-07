#!/usr/bin/env python3
"""Full-history sync from the public cs.rlin.dev pro-demo archive.

Covers every event the archive lists (not just the newest few), every map,
and every team. Dust2 entries keep feeding index.json (the app's existing
contract); every map goes to index-all-maps.json. Team logos come from the
logoUrl in each match's metadata and are stored in logos/ with a gradient
color pair in team_colors.json.
"""
from __future__ import annotations
import colorsys, datetime as dt, io, json, re, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RLIN = "https://cs.rlin.dev"
REPO_RAW = "https://raw.githubusercontent.com/ndx700/nadeatlas-demo-service/main"
BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
MAX_NEW_PER_RUN = 400          # new map entries verified per run; the rest wait for the next run
# matchIds already looked at and settled (added, or unusable for good). v2: the first list also held recent
# matches whose demo was simply not uploaded yet, so they were never looked at again.
CHECKED = ROOT / "data" / "rlin_checked_v2.json"
DEMO_WAIT_DAYS = 30            # a match without a demo is looked at again until it is this old


def _get(url, accept="*/*", timeout=45, limit=None, extra=None):
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, "Accept": accept, **(extra or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.headers, (r.read() if limit is None else r.read(limit))


def _json(path):
    _, _, raw = _get(RLIN + path, "application/json", 45, 3_000_000)
    return json.loads(raw.decode("utf-8"))


def discover_events(errors):
    """All event ids the archive lists, newest first."""
    _, _, raw = _get(RLIN + "/pro-games", "text/html", 60, 8_000_000)
    page = raw.decode("utf-8", "ignore")
    ids = re.findall(r'eventId\\*"\s*:\s*\\*"(\d+)', page)
    ids += re.findall(r'[?&]event=(\d+)', page)
    ids = list(dict.fromkeys(ids))
    if not ids:
        raise RuntimeError("no public event IDs discovered")
    return ids


def event_map_ids(eid):
    _, _, raw = _get(RLIN + f"/pro-games?event={urllib.parse.quote(eid)}", "text/html", 60, 12_000_000)
    return list(dict.fromkeys(re.findall(r"hltv-\d+-m\d+", raw.decode("utf-8", "ignore"))))


def verify_dem(url, map_name):
    short = map_name.replace("de_", "")
    if short not in urllib.parse.unquote(url).lower():
        raise RuntimeError(f"demo URL is not labelled {short}")
    code, h, head = _get(url, "*/*", 45, 4096, {"Range": "bytes=0-4095"})
    if code not in (200, 206):
        raise RuntimeError(f"demo probe HTTP {code}")
    if not (head.startswith(b"PBDEMS2") or head.startswith(b"HL2DEMO")):
        raise RuntimeError("invalid CS2 demo header")
    size = 0
    m = re.search(r"/(\d+)\s*$", h.get("Content-Range") or "")
    if m:
        size = int(m.group(1))
    if size < 1_000_000:
        q = urllib.request.Request(url, method="HEAD", headers={"User-Agent": BROWSER_UA, "Accept": "*/*"})
        with urllib.request.urlopen(q, timeout=45) as r:
            try:
                size = int(r.headers.get("Content-Length") or 0)
            except ValueError:
                size = 0
    if size < 1_000_000:
        raise RuntimeError(f"demo size suspicious: {size}")
    return size


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "team"


# ---------------------------------------------------------------- logos / colors

def _to_png(data, url):
    from PIL import Image
    if b"<svg" in data[:2048].lower() or url.lower().split("?")[0].endswith(".svg"):
        import cairosvg
        data = cairosvg.svg2png(bytestring=data, output_width=512)
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    im.thumbnail((440, 440), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((512 - im.width) // 2, (512 - im.height) // 2))
    return canvas


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(int(c) for c in rgb)


def logo_colors(img):
    """Primary = most common colourful pixel; secondary = next distinct colour,
    falling back to a darkened primary, so the card fades e.g. green -> black."""
    small = img.copy()
    small.thumbnail((96, 96))
    px = [p[:3] for p in small.getdata() if p[3] > 200]
    if not px:
        return "#3A3A3A", "#101010"
    buckets = {}
    for r, g, b in px:
        k = (r // 24, g // 24, b // 24)
        buckets.setdefault(k, [0, 0, 0, 0])
        e = buckets[k]; e[0] += r; e[1] += g; e[2] += b; e[3] += 1
    cols = sorted(((e[3], (e[0] / e[3], e[1] / e[3], e[2] / e[3])) for e in buckets.values()), reverse=True)

    def sat(c):
        h, l, s = colorsys.rgb_to_hls(*(x / 255 for x in c))
        return s, l

    colourful = [c for n, c in cols if sat(c)[0] > 0.25 and 0.12 < sat(c)[1] < 0.88 and n >= len(px) * 0.03]
    neutral = [c for n, c in cols if c not in colourful and n >= len(px) * 0.03]
    primary = colourful[0] if colourful else (neutral[0] if neutral else cols[0][1])
    secondary = None
    for c in colourful[1:] + neutral:
        if sum(abs(a - b) for a, b in zip(c, primary)) > 120:
            secondary = c
            break
    if secondary is None:
        secondary = tuple(x * 0.25 for x in primary)
    return _hex(primary), _hex(secondary)


def ensure_logo(team, url, logos, colors, errors):
    s = slug(team)
    path = ROOT / "logos" / f"{s}.png"
    if team in colors and path.exists():
        return
    try:
        if not path.exists():
            _, _, data = _get(url, "image/*,*/*", 45, 5_000_000, {"Referer": "https://www.hltv.org/"})
            img = _to_png(data, url)
            path.parent.mkdir(exist_ok=True)
            img.save(path, "PNG", optimize=True)
        else:
            from PIL import Image
            img = Image.open(path).convert("RGBA")
        p, q = logo_colors(img)
        logos[team] = f"{REPO_RAW}/logos/{s}.png"
        colors[team] = {"logo": logos[team], "primary": p, "secondary": q}
    except Exception as e:
        errors.append(f"logo {team}: {type(e).__name__}: {e}")


# ---------------------------------------------------------------- main sync

def sync(dust2_index, all_index, logos, colors, now):
    errors = []
    checked_ids = set(json.loads(CHECKED.read_text("utf-8"))) if CHECKED.exists() else set()
    known = {x.get("matchId") for x in all_index if x.get("matchId")}
    known |= {x.get("matchId") for x in dust2_index if x.get("matchId")}
    known_url = {x.get("url") for x in all_index} | {x.get("url") for x in dust2_index}
    try:
        events = discover_events(errors)
    except Exception as e:
        return {"state": "error", "message": f"{type(e).__name__}: {e}", "added": 0}, errors

    map_ids = []
    for eid in events:
        try:
            for mid in event_map_ids(eid):
                if mid not in map_ids:
                    map_ids.append(mid)
        except Exception as e:
            errors.append(f"rlin event {eid}: {type(e).__name__}: {e}")

    # Logo backfill: teams already in the index but without a logo/colour yet.
    need = {}
    for x in all_index:
        for t in (x.get("team1"), x.get("team2")):
            if t and t not in colors and x.get("matchId") and t not in need:
                need[t] = x["matchId"]
    for mid in list(dict.fromkeys(need.values()))[:80]:
        try:
            meta = _json("/api/matches/" + urllib.parse.quote(mid, safe="")).get("metadata") or {}
            for t in meta.get("teams") or []:
                if isinstance(t, dict) and t.get("name") and t.get("logoUrl"):
                    ensure_logo(t["name"], t["logoUrl"], logos, colors, errors)
        except Exception as e:
            errors.append(f"logo backfill {mid}: {type(e).__name__}: {e}")

    todo = [m for m in map_ids if m not in known and m not in checked_ids]
    added = added_d2 = looked = 0
    for mid in todo[:MAX_NEW_PER_RUN]:
        try:
            m = _json("/api/matches/" + urllib.parse.quote(mid, safe=""))
            looked += 1
            meta = m.get("metadata") if isinstance(m.get("metadata"), dict) else {}
            teams = meta.get("teams") if isinstance(meta.get("teams"), list) else []
            for t in teams:
                if isinstance(t, dict) and t.get("name") and t.get("logoUrl"):
                    ensure_logo(t["name"], t["logoUrl"], logos, colors, errors)
            mp = str(m.get("mapName") or "")
            url = str(m.get("demoUrl") or meta.get("uploadedDemoUrl") or "")
            ts = m.get("matchTime")
            if not (mp.startswith("de_") and url.startswith("https://") and ts and len(teams) >= 2):
                # The archive often lists a match before its demo is uploaded: keep looking while it is recent.
                recent = bool(ts) and (now - dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).date()).days < DEMO_WAIT_DAYS
                if not (mp.startswith("de_") and not url.startswith("https://") and recent):
                    checked_ids.add(mid)
                continue
            date = dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).date()
            if date > now or url in known_url:
                checked_ids.add(mid)
                continue
            size = verify_dem(url, mp)
            entry = {"date": date.isoformat(), "event": str(meta.get("eventName") or ""),
                     "team1": str(teams[0].get("name", "")), "team2": str(teams[1].get("name", "")),
                     "score": str(m.get("score") or ""), "map": mp, "url": url, "size": size,
                     "matchId": mid}
            if m.get("statsUrl"):
                entry["statsUrl"] = str(m["statsUrl"])
            all_index.append(entry)
            known.add(mid); known_url.add(url); added += 1
            if mp == "de_dust2":
                dust2_index.append(dict(entry)); added_d2 += 1
        except urllib.error.HTTPError as e:
            if e.code == 404:
                checked_ids.add(mid)
            else:
                errors.append(f"rlin {mid}: HTTP {e.code}")
        except RuntimeError as e:
            checked_ids.add(mid)   # wrong label / bad header: don't retry every 5 minutes
            errors.append(f"rlin {mid}: {e}")
        except Exception as e:
            errors.append(f"rlin {mid}: {type(e).__name__}: {e}")
        time.sleep(0.15)

    CHECKED.parent.mkdir(exist_ok=True)
    CHECKED.write_text(json.dumps(sorted(checked_ids), indent=0) + "\n", "utf-8")
    remaining = max(0, len(todo) - MAX_NEW_PER_RUN)
    return {"state": "ok", "events": len(events), "mapsListed": len(map_ids), "looked": looked,
            "added": added, "addedDust2": added_d2, "remaining": remaining}, errors
