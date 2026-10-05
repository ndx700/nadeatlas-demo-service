import urllib.request,urllib.parse,re,json,base64,gzip,zlib
u="https://docs.qq.com/dop-api/opendoc?tab=BB08J2&id=DZmdydmpxYURyREtZ&outformat=1&normal=1"
q=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0","Referer":"https://docs.qq.com/"})
with urllib.request.urlopen(q,timeout=30) as r:
 b=r.read(10_000_000);s=b.decode("utf-8","ignore")
 print("STATUS",r.status,"TYPE",r.headers.get("content-type"),"BYTES",len(b))
 print("RAW_HEAD",repr(s[:5000]))
 try:
  o=json.loads(s)
  print("JSON_TYPE",type(o).__name__)
  if isinstance(o,dict):
   print("JSON_KEYS",list(o.keys()))
   for k,v in o.items():
    print("FIELD",k,"TYPE",type(v).__name__,"LEN",len(v) if hasattr(v,"__len__") else None,"HEAD",repr(str(v)[:3000]))
 except Exception as e: print("JSON_ERROR",repr(e))
