#!/usr/bin/env python3
"""Team crests and player photos for the team library, from HLTV's image CDN.

HLTV's CDN refuses plain HTTP clients (GitHub runners get 403), so the images are fetched in a real browser:
an Apify playwright-scraper run loads every URL in scripts/data/hltv-image-urls.json and stores each image as
a data: URL (PNG) or the SVG source. This turns that run's dataset (JSON with "items") into:
- hltv/img/teams/<id>.png: transparent PNG trimmed to the crest's edges, scaled so the short side is at least 256
  px (long side at least 512). SVG crests are rendered; a leftover <id>.png.raw is removed. Preference: SVG,
  then the widest PNG, original colours before HLTV's inverted night variant.
- hltv/img/players/<id>.png: the body shot, at least 200x200, for players without a photo (all with --all).

usage: hltv_images.py DATASET.json [DATASET2.json ...] [--all]
"""
import base64, io, json, os, re, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "scripts", "data", "hltv-image-urls.json")
TEAMS = os.path.join(ROOT, "hltv", "img", "teams")
PLAYERS = os.path.join(ROOT, "hltv", "img", "players")


def width(u):
    m = re.search(r"[?&]w=(\d+)", u)
    return int(m.group(1)) if m else 9999


def decode(item):
    d = item.get("data")
    if not d:
        return None
    if item.get("kind") == "svg":
        if "<svg" not in d[:400]:
            return None
        import cairosvg
        d = cairosvg.svg2png(bytestring=d.encode(), output_width=1024)
        im = Image.open(io.BytesIO(d))
    else:
        im = Image.open(io.BytesIO(base64.b64decode(d.split(",", 1)[1])))
    im.load()
    return im.convert("RGBA")


def trim(im):
    box = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(box) if box else None


def fit(im, short=256, long_=512):
    w, h = im.size
    s = max(short / min(w, h), long_ / max(w, h))
    return im.resize((round(w * s), round(h * s)), Image.LANCZOS) if s > 1 else im


def main(files, every):
    spec = json.load(open(DATA, encoding="utf-8"))
    got = {}
    for f in files:
        for it in json.load(open(f, encoding="utf-8"))["items"]:
            if it.get("url") and it.get("data") and it.get("status") in (200, None):
                got[it["url"]] = it
    os.makedirs(TEAMS, exist_ok=True)
    done, small, missing = 0, [], []
    for tid, urls in sorted(spec.get("teams", {}).items(), key=lambda kv: int(kv[0])):
        order = sorted(urls, key=lambda x: ("invert=true" in x[1], ".svg" not in x[1], -width(x[1]), x[0] != "night"))
        out = None
        for _, u in order:
            if u not in got:
                continue
            try:
                t = trim(decode(got[u]))
            except Exception as e:
                print(f"team {tid}: {type(e).__name__} {e}")
                continue
            if t is not None:
                out = (u, t)
                break
        if not out:
            missing.append(tid)
            continue
        u, t = out
        if ".svg" not in u and max(t.size) < 256:
            small.append(tid)
        fit(t).save(os.path.join(TEAMS, f"{tid}.png"), optimize=True)
        raw = os.path.join(TEAMS, f"{tid}.png.raw")
        if os.path.exists(raw):
            os.remove(raw)
        done += 1
    print(f"team crests {done}, no image {len(missing)} {missing}, upscaled from a small PNG {len(small)}")
    os.makedirs(PLAYERS, exist_ok=True)
    pdone, pmiss = 0, []
    for pid, u in sorted(spec.get("players", {}).items(), key=lambda kv: int(kv[0])):
        path = os.path.join(PLAYERS, f"{pid}.png")
        if os.path.exists(path) and not every:
            continue
        if u not in got:
            pmiss.append(pid)
            continue
        im = decode(got[u])
        w, h = im.size
        if min(w, h) < 200:
            s = 200 / min(w, h)
            im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
        im.save(path, optimize=True)
        pdone += 1
    print(f"player photos {pdone}, no image {len(pmiss)} {pmiss}")


if __name__ == "__main__":
    main([a for a in sys.argv[1:] if not a.startswith("--")], "--all" in sys.argv)
