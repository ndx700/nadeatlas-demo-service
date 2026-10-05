#!/usr/bin/env python3
import re, json, html, urllib.request, urllib.error
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
urls=[
 "https://docs.qq.com/sheet/DZmdydmpxYURyREtZ?no_promotion=1&is_blank_or_template=blank&tab=BB08J2",
 "https://docs.qq.com/sheet/DZmdydmpxYURyREtZ?tab=BB08J2",
]
for u in urls:
 print("\nQQDOC",u)
 try:
  req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"})
  with urllib.request.urlopen(req,timeout=30) as r:
   b=r.read(8_000_000); s=b.decode("utf-8","ignore")
   print("STATUS",r.status,"FINAL",r.geturl(),"TYPE",r.headers.get("content-type"),"BYTES",len(b))
   print("TITLE",re.findall(r"<title[^>]*>(.*?)</title>",s,re.I|re.S)[:3])
   pats=[
    r'https?[^"\\\s<>]{0,100}game_tv[^"\\\s<>]{0,200}',
    r'game_tv.{0,300}',
    r'GAMEID.{0,300}',
    r'playcast.{0,300}',
    r'Rare Atom.{0,500}',
    r'Kaleido.{0,500}',
    r'Just Swing.{0,500}',
   ]
   for p in pats:
    ms=re.findall(p,s,re.I|re.S)
    print("PATTERN",p,"COUNT",len(ms))
    for m in ms[:20]: print("HIT",html.unescape(re.sub(r"\\u([0-9a-fA-F]{4})",lambda x:chr(int(x.group(1),16)),m))[:1200])
   # interesting script/config endpoints and numeric IDs
   for key in ["padId","docId","sheetId","tabId","rev","localPadId","globalPadId"]:
    ms=re.findall(r'["\\\']?'+key+r'["\\\']?\s*[:=]\s*["\\\']?([^,"\\\'\s}<]+)',s,re.I)
    if ms: print("META",key,ms[:20])
 except Exception as e: print("ERROR",repr(e))
