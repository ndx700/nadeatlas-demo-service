import urllib.request,urllib.parse,re,json
urls=[
 "https://docs.qq.com/dop-api/opendoc?tab=BB08J2&id=DZmdydmpxYURyREtZ&outformat=1&normal=1",
 "https://docs.qq.com/dop-api/opendoc?id=DZmdydmpxYURyREtZ&tab=BB08J2&outformat=1"
]
for u in urls:
 print("URL",u)
 try:
  q=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0","Referer":"https://docs.qq.com/"})
  with urllib.request.urlopen(q,timeout=30) as r:
   b=r.read(10_000_000);s=b.decode("utf-8","ignore")
   print("STATUS",r.status,"TYPE",r.headers.get("content-type"),"BYTES",len(b))
   d=s
   for _ in range(4): d=urllib.parse.unquote(d)
   ids=sorted(set(re.findall(r"g201-\\d{20,30}",d)))
   print("GAMEIDS",len(ids));print("\n".join(ids[:200]))
   for key in ["Dust2","Rare Atom","Chaos","Just Swing","Kaleido","09-20","09-25","09-27"]:
    print("KEY",key,"COUNT",d.lower().count(key.lower()))
 except Exception as e: print("ERROR",repr(e))
