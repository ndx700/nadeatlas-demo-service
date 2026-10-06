#!/usr/bin/env python3
import json, urllib.request, urllib.error, subprocess, time, os, signal

def req(url, timeout=45):
 try:
  r=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"NadeAtlas-Test/1.0","Accept":"application/json"}),timeout=timeout)
  b=r.read(200000)
  print("HTTP",url,r.status,r.headers.get("content-type"),"BYTES",len(b))
  print(b[:5000].decode("utf-8","ignore"))
 except Exception as e: print("ERR",url,repr(e))

print("=== CSAPI.DE LIVE ===")
for u in ["https://api.csapi.de/counts/","https://api.csapi.de/matches/?limit=3&offset=0","https://api.csapi.de/matches/2389666"]:
 req(u)

print("=== M3MONS LOCAL ===")
subprocess.run(["git","clone","--depth=1","https://github.com/M3MONs/hltv-scraper-api.git","/tmp/m3"],check=True)
subprocess.run(["python3","-m","pip","install","-q","-r","/tmp/m3/requirements.txt"],check=True)
p=subprocess.Popen(["python3","app.py"],cwd="/tmp/m3",stdout=open("/tmp/m3.log","w"),stderr=subprocess.STDOUT)
time.sleep(5)
for u in ["http://127.0.0.1:8000/api/v1/results/","http://127.0.0.1:8000/api/v1/matches/upcoming"]:
 req(u,90)
p.terminate()
print(open("/tmp/m3.log",errors="ignore").read()[-8000:])
