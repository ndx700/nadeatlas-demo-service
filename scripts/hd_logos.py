#!/usr/bin/env python3
"""High-resolution team crests for the app's team library.

Collects every team name the hltv/ data mentions, finds each team's page on Liquipedia (dark-mode logo when there
is one), and writes it trimmed and centred on a 512x512 transparent square to logos-hd/<slug>.png, so every crest
fills the same box. hltv/img/teams SVGs saved as .png.raw are rendered as a fallback. logos-hd/index.json records
where each one came from; logos-hd/_sheet.png is a contact sheet for checking them by eye.
"""
import glob, gzip, io, json, os, re, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "logos-hd")
API = "https://liquipedia.net/counterstrike/api.php"
UA = "NadeAtlasLogoFetcher/1.0 (https://github.com/ndx700/nadeatlas-demo-service; personal non-commercial app)"
SIZE, FILL = 512, 0.92
last = [0.0]

def slug(n): return "".join(c for c in n.lower() if c.isalnum())

def get(url, api=False):
    if api:
        wait = 2.1 - (time.time() - last[0])
        if wait > 0: time.sleep(wait)
        last[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip": data = gzip.decompress(data)
        return data

def api(**p):
    p.update(format="json", formatversion="2")
    return json.loads(get(API + "?" + urllib.parse.urlencode(p), api=True))

def names():
    found = {}
    def add(i, n):
        if isinstance(n, str) and n.strip() and n not in ("TBD",) and "winner" not in n.lower() and "/" not in n:
            if n not in found or (i and not found[n]): found[n] = i
    h = os.path.join(ROOT, "hltv")
    for t in json.load(open(os.path.join(h, "index.json"))).get("teams", []): add(t.get("id"), t.get("name"))
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("team1", "team2", "opponent", "winner") and isinstance(v, str): add(None, v)
                elif isinstance(v, dict) and "name" in v and ("id" in v) and k in ("team1", "team2", "opponent", "team"): add(v.get("id"), v.get("name"))
                else: walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    for f in glob.glob(os.path.join(h, "*", "*.json")):
        try: walk(json.load(open(f)))
        except Exception: pass
    for f in glob.glob(os.path.join(h, "teams", "*.json")):
        try: t = json.load(open(f)); add(t.get("id"), t.get("name"))
        except Exception: pass
    return found

def candidates(n):
    c = [n, "Team " + n, n + " Esports", n + " Gaming", n + " Clan", n + " (team)"]
    if n.isupper() or n.islower(): c.insert(1, n.title())
    return list(dict.fromkeys(c))

def logo_file(n):
    """(page, File:...) of the team's logo on Liquipedia, or (None, None)."""
    q = api(action="query", titles="|".join(candidates(n)), redirects=1, prop="pageimages", piprop="name")
    pages = {p["title"]: p for p in q["query"].get("pages", []) if not p.get("missing")}
    order = []
    for c in candidates(n):
        t = c
        for r in q["query"].get("normalized", []):
            if r["from"] == t: t = r["to"]
        for r in q["query"].get("redirects", []):
            if r["from"] == t: t = r["to"]
        if t in pages and t not in order: order.append(t)
    if not order:
        s = api(action="query", list="search", srsearch=n, srlimit=5, srnamespace=0)
        hits = [h["title"] for h in s["query"]["search"] if slug(n) in slug(h["title"])]
        if hits:
            q = api(action="query", titles="|".join(hits[:3]), redirects=1, prop="pageimages", piprop="name")
            pages = {p["title"]: p for p in q["query"].get("pages", []) if not p.get("missing")}
            order = [h for h in hits if h in pages] or list(pages)
    for t in order:
        img = pages[t].get("pageimage")
        if img and "logo" in img.lower(): return t, img
    return None, None

def file_url(name):
    q = api(action="query", titles="File:" + name, prop="imageinfo", iiprop="url")
    p = q["query"]["pages"][0]
    return None if p.get("missing") else p["imageinfo"][0]["url"]

def square(im):
    im = im.convert("RGBA")
    box = im.split()[3].getbbox()
    if box: im = im.crop(box)
    k = SIZE * FILL / max(im.size)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.alpha_composite(im, ((SIZE - im.width) // 2, (SIZE - im.height) // 2))
    return out

def load(data):
    if data.lstrip()[:5] in (b"<?xml", b"<svg ") or b"<svg" in data[:400]:
        import cairosvg
        data = cairosvg.svg2png(bytestring=data, output_width=1024)
    return Image.open(io.BytesIO(data))

def main():
    os.makedirs(OUT, exist_ok=True)
    teams = names()
    index_path = os.path.join(OUT, "index.json")
    old = json.load(open(index_path)) if os.path.exists(index_path) else {}
    done, missing = {}, []
    for n in sorted(teams, key=str.lower):
        s = slug(n)
        if not s: continue
        if s in old and os.path.exists(os.path.join(OUT, s + ".png")) and "--all" not in sys.argv:
            done[s] = old[s]; continue
        try:
            page, img = logo_file(n)
            url = None
            if img:
                for alt in ([img.replace("lightmode", "darkmode")] if "lightmode" in img else []) + [img]:
                    url = file_url(alt)
                    if url: img = alt; break
            src = None
            if url:
                square(load(get(url))).save(os.path.join(OUT, s + ".png"), optimize=True); src = url
            else:
                raw = os.path.join(ROOT, "hltv", "img", "teams", f"{teams[n]}.png.raw") if teams[n] else ""
                if raw and os.path.exists(raw):
                    square(load(open(raw, "rb").read())).save(os.path.join(OUT, s + ".png"), optimize=True); src = "hltv svg"
            if src:
                done[s] = {"name": n, "id": teams[n], "page": page, "file": img, "source": src}
                print("OK  ", n, "->", page, img)
            else:
                missing.append(n); print("MISS", n)
        except Exception as e:
            missing.append(n); print("FAIL", n, repr(e))
    json.dump(done, open(index_path, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    # Contact sheet on the app's card colour.
    items = sorted(done.items(), key=lambda kv: kv[1]["name"].lower())
    cols, cell = 10, 128
    sheet = Image.new("RGBA", (cols * cell, ((len(items) + cols - 1) // cols) * (cell + 18) + 4), (0x1a, 0x27, 0x2e, 255))
    d = ImageDraw.Draw(sheet)
    for k, (s, v) in enumerate(items):
        x, y = (k % cols) * cell, (k // cols) * (cell + 18)
        d.rectangle([x + 4, y + 4, x + cell - 4, y + cell - 4], outline=(0x2d, 0x3e, 0x47, 255))
        sheet.alpha_composite(Image.open(os.path.join(OUT, s + ".png")).resize((cell - 24, cell - 24), Image.LANCZOS), (x + 12, y + 12))
        d.text((x + 6, y + cell - 2), v["name"][:20], fill=(220, 220, 220, 255))
    sheet.save(os.path.join(OUT, "_sheet.png"))
    print(f"{len(done)} crests, {len(missing)} missing: {missing}")

if __name__ == "__main__":
    main()
