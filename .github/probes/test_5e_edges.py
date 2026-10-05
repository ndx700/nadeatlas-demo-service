import urllib.request,urllib.error
base="https://hk-demo.5eplaycdn.com/game_tv/g201-20260922154948491976189"
for n in [1310,1320,1350,1400,1500,1600,1800,2048,4096,8192]:
 try:
  q=urllib.request.Request(f"{base}/{n}/delta",headers={"User-Agent":"Mozilla/5.0","Range":"bytes=0-0"})
  with urllib.request.urlopen(q,timeout=10) as r:
   r.read(1); print("EDGE",n,"OK",r.status,r.headers.get("content-range"),r.headers.get("content-length"))
 except urllib.error.HTTPError as e: print("EDGE",n,"HTTP",e.code,e.headers.get("content-length"))
 except Exception as e: print("EDGE",n,"ERR",repr(e))
