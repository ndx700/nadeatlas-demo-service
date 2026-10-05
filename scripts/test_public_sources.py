#!/usr/bin/env python3
import re, urllib.request, html as H
UA="Mozilla/5.0"
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=30) as r:
        return r.read().decode("utf-8","ignore")
page=get("https://cs2replays.com/library/?map=de_dust2")
print("PAGE_LINKS")
for x in sorted(set(re.findall(r'href=["\\\']([^"\\\']+)["\\\']',page,re.I))):
    if any(k in x.lower() for k in ["library","replay","match","demo"]): print(x)
print("\nPAGE_DATA_ATTRS")
for m in re.finditer(r'data-[a-z0-9_-]+=["\\\'][^"\\\']+["\\\']',page,re.I):
    s=m.group(0)
    if any(k in s.lower() for k in ["match","replay","demo","dust"]): print(H.unescape(s)[:1000])
print("\nPAGE_CONTEXT_DUST2")
for m in list(re.finditer("dust2",page,re.I))[:20]:
    print(H.unescape(page[max(0,m.start()-700):m.start()+1200]).replace("\n"," ")[:1900])
js=get("https://cs2replays.com/js/app.js")
print("\nJS_LIBRARY_CONTEXT")
for needle in ["pro library","pro matches","pro-match","pro_match","libraryData","/library","demoUrl"]:
    print("\nNEEDLE",needle)
    for m in list(re.finditer(re.escape(needle),js,re.I))[:10]:
        print(js[max(0,m.start()-700):m.start()+1600].replace("\n"," ")[:2300])
