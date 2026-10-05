#!/usr/bin/env python3
import re,urllib.request
u="https://cs.rlin.dev/pro-games?event=8249"
s=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=30).read().decode("utf-8","ignore")
patterns=[r'eventId\\\":\\\"(\d+)',r'event=(\d+)',r'matchId\\\":\\\"(hltv-[^\\\"]+)\\\",\\\"mapName\\\":\\\"de_dust2']
for p in patterns:
 x=list(dict.fromkeys(re.findall(p,s)))
 print("PATTERN",p,"COUNT",len(x),"FIRST",x[:30])
