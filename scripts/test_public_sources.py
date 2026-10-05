#!/usr/bin/env python3
import re, urllib.request
UA="Mozilla/5.0"
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=30) as r: return r.read().decode("utf-8","ignore")
js=get("https://cs2replays.com/js/app.js")
for needle in ["/api/matches","API_BASE","apiBase","apiBaseUrl","BASE_URL","fetch("]:
    print("\n===",needle,"===")
    for m in list(re.finditer(re.escape(needle),js,re.I))[:15]:
        print(js[max(0,m.start()-500):m.start()+1000].replace("\n"," ")[:1500])
