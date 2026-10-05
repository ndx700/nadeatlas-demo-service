import urllib.request,urllib.parse,re,json,base64,zlib,gzip
u="https://docs.qq.com/dop-api/opendoc?tab=BB08J2&id=DZmdydmpxYURyREtZ&outformat=1&normal=1"
q=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0","Referer":"https://docs.qq.com/"})
with urllib.request.urlopen(q,timeout=30) as r:o=json.loads(r.read())
cv=o["clientVars"]["collab_client_vars"]
items=cv["initialAttributedText"]["text"]
print("ITEMS",len(items))
alltext=""
for i,item in enumerate(items):
 for k,v in item.items():
  if not isinstance(v,str) or len(v)<20: continue
  try:
   raw=base64.b64decode(v)
   try: dec=zlib.decompress(raw)
   except: dec=zlib.decompress(raw,-zlib.MAX_WBITS)
   s=dec.decode("utf-8","ignore")
   print("DECODED",i,k,"BYTES",len(dec),"HEAD",repr(s[:500]))
   alltext+="\n"+s
  except Exception as e: print("SKIP",i,k,repr(e))
ids=sorted(set(re.findall(r"g201-\\d{20,30}",alltext)))
print("GAMEIDS",len(ids))
for x in ids: print("ID",x)
for key in ["Dust2","Rare Atom","Chaos","Just Swing","Kaleido","09-19","09-20","09-21","09-22","09-25","09-27"]:
 print("KEY",key,"COUNT",alltext.lower().count(key.lower()))
 for m in list(re.finditer(re.escape(key),alltext,re.I))[:10]:
  print("CTX",re.sub(r"\\s+"," ",alltext[max(0,m.start()-500):m.start()+1000])[:1500])
