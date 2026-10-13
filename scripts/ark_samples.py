"""Draw sample images with Volcano Ark (Seedream) for comparing models.

Reads ARK_API_KEY from the environment; writes PNG/JPEG files to samples/ark/.
Each model is tried under a few spellings of its id; the first that the API accepts is used.
"""
import base64, json, os, sys, urllib.request, urllib.error

BASE = os.environ.get("ARK_BASE", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
KEY = os.environ.get("ARK_API_KEY", "")
OUT = "samples/ark"

PROMPTS = [
    ("xiaoke", "二次元动漫立绘，全身像，纯白背景。一位傲娇的理工科大小姐少女“小克”，橙色的超长直发垂到小腿，"
               "发间别着橙色花朵发饰和黑色缎带，琥珀色眼睛，微微抬起下巴、表情骄傲又有点不服气。"
               "身穿白色维多利亚风长裙，荷叶边高领，黑色领结，黑色高腰束腹，裙摆层层叠叠，饰有橙色和金色刺绣、流苏和蝴蝶结；"
               "左臂戴着写有“风纪委员”的红色袖章，一手抱着一本厚厚的数学书，一手轻提裙摆；白色系带短靴。"
               "精致线稿，干净的赛璐璐上色，高质量角色设定图"),
    ("girl", "二次元动漫风格，一个白发蓝眼的少女站在樱花树下，微风吹起长发，柔和的春日阳光，精致的线条和上色，高质量插画"),
    ("cs2", "日系动漫风格插画，一个戴耳机的少女在电竞房里打 CS 游戏，屏幕的光照在脸上，表情专注，霓虹灯氛围，细节丰富"),
    ("whale", "可爱的二次元鲸鱼少女，水蓝色长发，身边环绕着小鱼和气泡，海底光束，梦幻治愈的画风"),
]

def spellings(name):
    n = name.strip()
    low = n.lower()
    return list(dict.fromkeys([n, low, low.replace(".", "-")]))

def call(model, prompt):
    body = json.dumps({"model": model, "prompt": prompt, "size": "2K",
                       "response_format": "b64_json", "watermark": False}).encode()
    req = urllib.request.Request(BASE + "/images/generations", data=body, method="POST",
                                 headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return 200, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")[:500]

def main():
    if not KEY:
        print("::error::ARK_API_KEY is not set"); sys.exit(1)
    os.makedirs(OUT, exist_ok=True)
    models = sys.argv[1:] or ["Doubao-Seedream-5.0-pro", "Doubao-Seedream-5.0-flash"]
    ok = 0
    for name in models:
        chosen = None
        for tag, prompt in PROMPTS:
            ids = [chosen] if chosen else spellings(name)
            for mid in ids:
                code, res = call(mid, prompt)
                if code == 200:
                    chosen = mid
                    data = res["data"][0]
                    raw = base64.b64decode(data["b64_json"])
                    ext = "png" if raw[:4] == b"\x89PNG" else "jpg"
                    path = f"{OUT}/{name.lower().replace('.', '-')}_{tag}.{ext}"
                    open(path, "wb").write(raw)
                    print(f"::notice::OK {name} as {mid}: {path} ({len(raw)//1024} KB) usage={res.get('usage')}")
                    ok += 1
                    break
                print(f"::warning::FAIL {name} as {mid} [{tag}]: HTTP {code} {res}")
            if not chosen:
                break
    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
