#!/usr/bin/env python3
"""Copy the demo service's big files to the Aliyun OSS bucket nadeatlas-demo (cn-shanghai), for people in China.

What goes up (each file once; a file is sent again only when its size changes):
  dem/<matchId>.dem          every map demo in index-all-maps.json (its "url", e.g. the rlin CDN)
  replays/<name>.nar         the parsed replays in this repository's "replays" release
  series/<name>.rar          whole HLTV series in the "dust2-pilot-*" / "demo-*" releases

Then oss.json in this repository lists what is there, so the demo site (site/index.html) links to the OSS copy
first and to the original only when there is none:
  {"base": "https://nadeatlas-demo.oss-cn-shanghai.aliyuncs.com/", "files": {key: size}, "series": {hltv id: key}}

Env: ALIYUN_OSS_AK_ID, ALIYUN_OSS_AK_SECRET; GH_TOKEN (release listing); OSS_MAX_GB (default 20) per run;
OSS_KINDS (default "replays": which of replays, dem, series to send); OSS_ENDPOINT (the transfer acceleration
endpoint https://oss-accelerate.aliyuncs.com once it is turned on for the bucket). A GitHub runner reaches Shanghai
at only ~100 KB/s, so files go up OSS_JOBS (default 8) at a time, each through its own temporary file.
"""
import json, os, re, sys, tempfile, time, urllib.request
from pathlib import Path
import oss2

ROOT = Path(__file__).resolve().parents[1]
REPO = os.environ.get("GITHUB_REPOSITORY", "ndx700/nadeatlas-demo-service")
BUCKET = "nadeatlas-demo"
ENDPOINT = os.environ.get("OSS_ENDPOINT") or "https://oss-cn-shanghai.aliyuncs.com"
KINDS = set(os.environ.get("OSS_KINDS", "replays").split(","))
JOBS = int(os.environ.get("OSS_JOBS", "8"))
BASE = f"https://{BUCKET}.oss-cn-shanghai.aliyuncs.com/"
OUT = ROOT / "oss.json"
MAX_BYTES = int(float(os.environ.get("OSS_MAX_GB", "20")) * (1 << 30))
DEADLINE = time.time() + float(os.environ.get("OSS_MAX_MINUTES", "300")) * 60
UA = {"User-Agent": "Mozilla/5.0 NadeAtlas-OSS-Sync/1.0"}


def gh(path):
    req = urllib.request.Request("https://api.github.com/" + path, headers={"Accept": "application/vnd.github+json", **UA,
                                 **({"Authorization": "Bearer " + os.environ["GH_TOKEN"]} if os.environ.get("GH_TOKEN") else {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def releases():
    out, page = [], 1
    while True:
        batch = gh(f"repos/{REPO}/releases?per_page=100&page={page}")
        out += batch
        if len(batch) < 100: return out
        page += 1


def wanted():
    """(key, source url, size or None, hltv id or None) for everything that should be on OSS."""
    items = []
    for e in json.loads((ROOT / "index-all-maps.json").read_text("utf-8")):
        if e.get("url") and e.get("matchId") and str(e["url"]).endswith(".dem"):
            items.append((f"dem/{e['matchId']}.dem", e["url"], e.get("size"), None))
    for rel in releases():
        tag = rel.get("tag_name", "")
        assets = {a["name"]: a for a in rel.get("assets", []) if a.get("state") == "uploaded"}
        if tag == "replays":
            for a in assets.values():
                if a["name"].endswith(".nar"):
                    items.append((f"replays/{a['name']}", a["browser_download_url"], a["size"], None))
        elif tag.startswith("dust2-pilot") or tag.startswith("demo-"):
            ids = {}
            if "manifest.json" in assets:
                try:
                    with urllib.request.urlopen(urllib.request.Request(assets["manifest.json"]["browser_download_url"], headers=UA), timeout=60) as r:
                        for item in json.load(r).values():
                            m = re.search(r"/matches/(\d+)/", str(item.get("match_url", "")))
                            if m and item.get("asset_name"): ids[item["asset_name"]] = m.group(1)
                except Exception as ex:
                    print(f"::warning::{tag} manifest: {ex}")
            for a in assets.values():
                if a["name"].endswith(".rar"):
                    items.append((f"series/{a['name']}", a["browser_download_url"], a["size"], ids.get(a["name"])))
    return items


def main():
    ak, sk = os.environ.get("ALIYUN_OSS_AK_ID", ""), os.environ.get("ALIYUN_OSS_AK_SECRET", "")
    if not ak or not sk:
        sys.exit("::error::ALIYUN_OSS_AK_ID / ALIYUN_OSS_AK_SECRET missing")
    bucket = oss2.Bucket(oss2.Auth(ak, sk), ENDPOINT, BUCKET)
    have = {}
    for o in oss2.ObjectIterator(bucket):
        have[o.key] = o.size
    items = wanted()
    # Newest first: replays (small, what the app and site use most), then single maps, then whole series.
    order = {"replays": 0, "dem": 1, "series": 2}
    items.sort(key=lambda x: order[x[0].split("/")[0]])
    todo, budget = [], 0
    for key, url, size, _ in items:
        if key.split("/")[0] not in KINDS or (key in have and (size is None or have[key] == size)):
            continue
        if budget >= MAX_BYTES: break
        todo.append((key, url, size)); budget += size or 0
    import threading
    from concurrent.futures import ThreadPoolExecutor
    lock = threading.Lock(); stats = [0, 0]

    def one(job):
        key, url, size = job
        if time.time() > DEADLINE: return
        try:
            with tempfile.NamedTemporaryFile(dir=os.environ.get("RUNNER_TEMP"), delete=True) as tmp:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r:
                    while True:
                        chunk = r.read(1 << 22)
                        if not chunk: break
                        tmp.write(chunk)
                tmp.flush()
                n = os.path.getsize(tmp.name)
                if size and n != size:
                    print(f"::warning::{key}: got {n} bytes, expected {size}; skipped"); return
                oss2.resumable_upload(bucket, key, tmp.name, part_size=16 << 20, num_threads=4,
                                      store=oss2.ResumableStore(root=os.environ.get("RUNNER_TEMP", "/tmp")))
                with lock:
                    have[key] = n; stats[0] += 1; stats[1] += n
                print(f"up {key} {n >> 20} MB", flush=True)
        except Exception as ex:
            print(f"::warning::{key}: {ex}")

    with ThreadPoolExecutor(JOBS) as pool:
        list(pool.map(one, todo))
    sent, sent_bytes = stats
    keys = {k for k, _, _, _ in items}
    series = {hid: key for key, _, _, hid in items if hid and key in have}
    data = {"base": BASE, "files": {k: have[k] for k in sorted(have) if k in keys}, "series": series}
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", "utf-8")
    left = sum(1 for k, _, s, _ in items if k not in have and k.split("/")[0] in KINDS)
    print(f"::notice::OSS: sent {sent} files ({sent_bytes / (1 << 30):.1f} GB), {left} still to send, {len(data['files'])} on OSS")


if __name__ == "__main__":
    main()
