#!/usr/bin/env python3
import json, urllib.request, urllib.error
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"

def req(url, range_=False):
    h={"User-Agent":UA,"Accept":"application/json,*/*"}
    if range_: h["Range"]="bytes=0-1023"
    with urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=25) as r:
        return r.status,r.geturl(),r.headers,r.read(2000000 if not range_ else 1024)

for mid in ["2392279","csgo_mc_2392279","2398738","csgo_mc_2398738","2396053","csgo_mc_2396053","2374325","csgo_mc_2374325"]:
    u="https://gate.5eplay.com/crane/http/api/data/match/"+mid
    print("\nDETAIL",mid)
    try:
        st,final,h,b=req(u)
        print("STATUS",st,"TYPE",h.get("content-type"),"BYTES",len(b))
        o=json.loads(b)
        data=o.get("data") if isinstance(o,dict) else None
        print("SUCCESS",o.get("success") if isinstance(o,dict) else None,"ERR",o.get("errcode") if isinstance(o,dict) else None,"MESSAGE",o.get("message") if isinstance(o,dict) else None)
        if isinstance(data,dict):
            print("DATA_KEYS",list(data.keys())[:80])
            main=data.get("main")
            if isinstance(main,dict):
                wanted={k:v for k,v in main.items() if any(x in k.lower() for x in ["demo","map","match","time","url","game"])}
                print("MAIN_WANTED",json.dumps(wanted,ensure_ascii=False)[:12000])
                du=main.get("demo_url")
                if isinstance(du,str) and du.startswith("http"):
                    print("DEMO_URL_FOUND",du)
                    try:
                        ds,df,dh,db=req(du,True)
                        print("DEMO_PROBE",ds,df,dh.get("content-type"),dh.get("content-length"),dh.get("content-range"),db[:32].hex())
                    except Exception as e: print("DEMO_PROBE_ERROR",repr(e))
    except urllib.error.HTTPError as e:
        print("HTTP_ERROR",e.code,e.read(1000).decode("utf-8","ignore"))
    except Exception as e: print("ERROR",repr(e))
