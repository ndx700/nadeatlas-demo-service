#!/usr/bin/env python3
import re, urllib.request, urllib.error

MATCH = "https://www.hltv.org/matches/2396021/spirit-vs-mouz-blast-bounty-2026-season-2-finals"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"

def req(url, method="GET", headers=None):
    h={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    if headers: h.update(headers)
    return urllib.request.urlopen(urllib.request.Request(url,headers=h,method=method),timeout=30)

try:
    with req(MATCH) as r:
        body=r.read().decode("utf-8","ignore")
        print("MATCH_STATUS",r.status)
        print("MATCH_TYPE",r.headers.get("content-type"))
        print("MATCH_BYTES",len(body))
    links=re.findall(r'href=["\']([^"\']*/download/demo/[^"\']+)["\']',body,re.I)
    print("DEMO_LINKS",links[:5])
    if not links:
        raise SystemExit("NO_DEMO_LINK_FOUND")
    u=links[0]
    if u.startswith("/"): u="https://www.hltv.org"+u
    try:
        with req(u,headers={"Range":"bytes=0-1023"}) as r:
            chunk=r.read(1024)
            print("DEMO_STATUS",r.status)
            print("DEMO_FINAL_URL",r.geturl())
            print("DEMO_TYPE",r.headers.get("content-type"))
            print("DEMO_LENGTH",r.headers.get("content-length"))
            print("DEMO_DISPOSITION",r.headers.get("content-disposition"))
            print("DEMO_FIRST_BYTES",chunk[:32].hex())
    except urllib.error.HTTPError as e:
        print("DEMO_HTTP_ERROR",e.code)
        print("DEMO_ERROR_TYPE",e.headers.get("content-type"))
        print("DEMO_ERROR_BODY",e.read(300).decode("utf-8","ignore"))
        raise
except urllib.error.HTTPError as e:
    print("MATCH_HTTP_ERROR",e.code)
    print("MATCH_ERROR_TYPE",e.headers.get("content-type"))
    print("MATCH_ERROR_BODY",e.read(300).decode("utf-8","ignore"))
    raise
