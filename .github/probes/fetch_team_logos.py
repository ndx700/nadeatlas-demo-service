#!/usr/bin/env python3
import os, urllib.request
from PIL import Image
from io import BytesIO

LOGOS = {
 "natus-vincere": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Navi%20Logo.png",
 "vitality": "https://logotyp.us/file/team-vitality.png",
 "furia": "https://logos-download.com/wp-content/uploads/2019/11/Furia_Esports_Logo.png",
 "g2": "https://logos-download.com/wp-content/uploads/2019/11/G2_Esports_Logo.png",
}
os.makedirs("logos", exist_ok=True)
for slug,url in LOGOS.items():
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 NadeAtlasLogoFetcher/1.0"})
        data=urllib.request.urlopen(req,timeout=60).read()
        im=Image.open(BytesIO(data)).convert("RGBA")
        im.thumbnail((440,440), Image.Resampling.LANCZOS)
        canvas=Image.new("RGBA",(512,512),(0,0,0,0))
        canvas.alpha_composite(im,((512-im.width)//2,(512-im.height)//2))
        canvas.save(f"logos/{slug}.png","PNG",optimize=True)
        print("OK",slug,len(data),im.size)
    except Exception as e:
        print("FAIL",slug,repr(e))
