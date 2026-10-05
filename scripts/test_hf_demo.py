#!/usr/bin/env python3
import hashlib, json, os, urllib.request

BASE="https://huggingface.co/datasets/blanchon/cs2_dataset_demo/resolve/main/demos/shard-europe-0436c5b3/2392290/"
META=BASE+"meta.json"
DEMO=BASE+"100-thieves-vs-lavked-m3-dust2.dem?download=true"
UA="nadeatlas-demo-service/1.0 (HF validation)"

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=120)

with get(META) as r:
    meta=json.load(r)
print("META",json.dumps(meta,ensure_ascii=False))

out="/tmp/100-thieves-vs-lavked-m3-dust2.dem"
h=hashlib.sha256()
n=0
with get(DEMO) as r, open(out,"wb") as f:
    print("HTTP_STATUS",r.status)
    print("CONTENT_TYPE",r.headers.get("content-type"))
    print("CONTENT_LENGTH",r.headers.get("content-length"))
    while True:
        b=r.read(1024*1024)
        if not b: break
        f.write(b); h.update(b); n+=len(b)
        if n and n%(100*1024*1024)<1024*1024:
            print("DOWNLOADED",n)
with open(out,"rb") as f:
    head=f.read(16)
print("FINAL_BYTES",n)
print("HEADER_ASCII",repr(head))
print("HEADER_HEX",head.hex())
print("SHA256",h.hexdigest())
ok=head.startswith(b"PBDEMS2") or head.startswith(b"HL2DEMO")
print("VALID_SOURCE_DEMO_HEADER",ok)
if not ok or n<10_000_000:
    raise SystemExit("INVALID_DEMO")
