#!/usr/bin/env python3
"""Team crests and player photos for the team library, straight from HLTV's image CDN.

scripts/data/hltv-image-urls.json lists, per HLTV team id, the crest URLs seen on HLTV event pages (SVG or PNG,
day/night variants) and, per HLTV player id, a body-shot URL from the player's page. This writes:
- hltv/img/teams/<id>.png: transparent PNG trimmed to the crest's edges, scaled so the short side is at least 256
  px (long side at least 512). SVG crests are rendered rather than saved raw; a leftover <id>.png.raw is removed.
- hltv/img/players/<id>.png: the body shot, at least 200x200 (only for players without a photo, unless --all).
A crest whose largest available source is small is upscaled; the log says which ones.
"""
import io, json, os, re, sys, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "scripts", "data", "hltv-image-urls.json")
TEAMS = os.path.join(ROOT, "hltv", "img", "teams")
PLAYERS = os.path.join(ROOT, "hltv", "img", "players")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.hltv.org/"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def width(u):
    m = re.search(r"[?&]w=(\d+)", u)
    return int(m.group(1)) if m else 0


def candidates(urls):
    """Best first: night SVG, day SVG, the PNG without size parameters, then the widest signed PNG."""
    svg = [u for k, u in urls if ".svg" in u]
    svg.sort(key=lambda u: 0 if any(k == "night" and x == u for k, x in urls) else 1)
    png = sorted({u for _, u in urls if ".svg" not in u}, key=width, reverse=True)
    bare = sorted({u.split("?")[0] for u in png})
    return [u.split("?")[0] for u in svg] + svg + bare + png


def load(url, data):
    if ".svg" in url.split("?")[0]:
        import cairosvg
        data = cairosvg.svg2png(bytestring=data, output_width=1024)
    im = Image.open(io.BytesIO(data))
    im.load()
    return im.convert("RGBA")


def trim(im):
    a = im.getchannel("A").point(lambda v: 255 if v > 8 else 0)
    box = a.getbbox()
    return im.crop(box) if box else None


def fit(im, short=256, long_=512):
    w, h = im.size
    s = max(short / min(w, h), long_ / max(w, h))
    if s > 1:
        im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    return im


def teams(spec):
    os.makedirs(TEAMS, exist_ok=True)
    done, small, failed = 0, [], []
    for tid, urls in sorted(spec.items(), key=lambda kv: int(kv[0])):
        got = None
        for u in candidates([tuple(x) for x in urls]):
            try:
                im = load(u, get(u))
            except Exception as e:
                print(f"team {tid}: {u[:90]} -> {type(e).__name__} {str(e)[:60]}")
                continue
            t = trim(im)
            if t is None:
                continue
            got = (u, im.size, t)
            break
        if not got:
            failed.append(tid)
            continue
        u, src, t = got
        if max(t.size) < 256:
            small.append(f"{tid}({max(t.size)}px)")
        out = fit(t)
        out.save(os.path.join(TEAMS, f"{tid}.png"), optimize=True)
        raw = os.path.join(TEAMS, f"{tid}.png.raw")
        if os.path.exists(raw):
            os.remove(raw)
        done += 1
        print(f"team {tid}: {out.size[0]}x{out.size[1]} from {u.split('?')[0].rsplit('/', 1)[-1]} {'(svg)' if '.svg' in u else 'w=' + str(width(u) or 'orig')}")
    print(f"::notice::team crests written {done}, failed {len(failed)} {failed}, upscaled from small sources {len(small)} {small}")


def players(spec, every):
    os.makedirs(PLAYERS, exist_ok=True)
    done, failed = 0, []
    for pid, url in sorted(spec.items(), key=lambda kv: int(kv[0])):
        path = os.path.join(PLAYERS, f"{pid}.png")
        if os.path.exists(path) and not every:
            continue
        try:
            im = load(url, get(url))
        except Exception as e:
            failed.append(pid)
            print(f"player {pid}: {type(e).__name__} {str(e)[:60]}")
            continue
        w, h = im.size
        if min(w, h) < 200:
            s = 200 / min(w, h)
            im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
        im.save(path, optimize=True)
        done += 1
    print(f"::notice::player photos written {done}, failed {len(failed)} {failed}")


if __name__ == "__main__":
    spec = json.load(open(DATA, encoding="utf-8"))
    teams(spec.get("teams", {}))
    players(spec.get("players", {}), "--all" in sys.argv)
