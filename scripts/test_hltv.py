#!/usr/bin/env python3
import urllib.request, urllib.error

URL="https://www.hltv.org/download/demo/106303"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
req=urllib.request.Request(URL,headers={"User-Agent":UA,"Accept":"*/*","Range":"bytes=0-1023"})
try:
    with urllib.request.urlopen(req,timeout=30) as r:
        chunk=r.read(1024)
        print("STATUS",r.status)
        print("FINAL_URL",r.geturl())
        print("TYPE",r.headers.get("content-type"))
        print("LENGTH",r.headers.get("content-length"))
        print("DISPOSITION",r.headers.get("content-disposition"))
        print("FIRST_BYTES",chunk[:32].hex())
except urllib.error.HTTPError as e:
    print("HTTP_ERROR",e.code)
    print("TYPE",e.headers.get("content-type"))
    print("BODY",e.read(500).decode("utf-8","ignore"))
    raise
