#!/usr/bin/env python3
"""High-resolution team crests for the app's team library.

Collects every team name the hltv/ data mentions, finds each team's page on Liquipedia (dark-mode logo when there
is one), and writes it trimmed and centred on a 512x512 transparent square to logos-hd/<slug>.png, so every crest
fills the same box. hltv/img/teams SVGs saved as .png.raw are rendered as a fallback. logos-hd/index.json records
where each one came from; logos-hd/_sheet.png is a contact sheet for checking them by eye.
"""
import glob, gzip, urllib.error, io, json, os, re, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "logos-hd")
API = "https://liquipedia.net/counterstrike/api.php"
UA = "NadeAtlasLogoFetcher/1.0 (https://github.com/ndx700/nadeatlas-demo-service; personal non-commercial app)"
SIZE, FILL = 512, 0.92
last = [0.0]

def slug(n): return "".join(c for c in n.lower() if c.isalnum())

def get(url, api=False):
    for attempt in range(5):
        if api:
            wait = 4.0 - (time.time() - last[0])
            if wait > 0: time.sleep(wait)
            last[0] = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                if r.headers.get("Content-Encoding") == "gzip": data = gzip.decompress(data)
                return data
        except urllib.error.HTTPError as e:
            # Liquipedia asks for patience when it is asked too often: wait and try again.
            if e.code != 429 or attempt == 4: raise
            time.sleep(60 * (attempt + 1))

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

def resolve(titles):
    """The existing pages among [titles] (redirects followed), in the order asked."""
    q = api(action="query", titles="|".join(titles), redirects=1)
    have = {p["title"] for p in q["query"].get("pages", []) if not p.get("missing")}
    order = []
    for c in titles:
        t = c
        for r in q["query"].get("normalized", []):
            if r["from"] == t: t = r["to"]
        for r in q["query"].get("redirects", []):
            if r["from"] == t: t = r["to"]
        if t in have and t not in order: order.append(t)
    return order

def infobox_logo(title):
    """The team infobox's logo file: the dark-mode one when there is one."""
    q = api(action="query", titles=title, prop="revisions", rvprop="content", rvslots="main", rvsection=0)
    p = q["query"]["pages"][0]
    text = p.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("content", "")
    if "{{Infobox team" not in text and "{{infobox team" not in text.lower(): return None
    fields = dict(re.findall(r"^\|\s*(image|imagedark|image_dark|darkimage|imagedarkmode)\s*=\s*(.+?)\s*$", text, re.M | re.I))
    low = {k.lower(): v for k, v in fields.items()}
    for k in ("imagedark", "image_dark", "darkimage", "imagedarkmode", "image"):
        v = low.get(k, "").strip()
        if v and not v.startswith("{{"): return v.replace("File:", "").strip()
    return None

def logo_file(n):
    """(page, file name) of the team's logo on Liquipedia, or (None, None)."""
    order = resolve(candidates(n))
    if not order:
        s = api(action="query", list="search", srsearch=n, srlimit=5, srnamespace=0)
        order = [h["title"] for h in s["query"]["search"] if slug(n)[:4] in slug(h["title"])][:3]
    for t in order:
        img = infobox_logo(t)
        if img: return t, img
    if DEBUG[0] < 3:
        DEBUG[0] += 1
        print(f"::warning::{n}: no infobox logo on {order}")
    return None, None
DEBUG = [0]

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
            try:
                page, img = logo_file(n)
            except Exception as e:
                print("FAIL", n, repr(e)); page, img = None, None
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
            elif s in old and os.path.exists(os.path.join(OUT, s + ".png")):
                done[s] = old[s]; print("KEPT", n)
            else:
                missing.append(n); print("MISS", n)
        except Exception as e:
            missing.append(n); print("FAIL", n, repr(e))
            if len(missing) <= 5: print(f"::warning::{n}: {e!r}"[:900])
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
    print(f"::notice::{len(done)} crests, {len(missing)} missing: {', '.join(missing)}"[:4000])

if __name__ == "__main__":
    main()
