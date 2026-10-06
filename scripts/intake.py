#!/usr/bin/env python3
"""File line-up feedback sent from the NadeAtlas online build.

The app opens an issue titled "[NadeAtlas] <用途|问题|删除> ..." whose body ends with a ```json block.
Only issues opened by the repository owner are taken. Each one is appended to data/grenade_feedback.json
(deletions and purposes are applied by the next grenade-library build; problems are for Claude to read),
then answered and closed.
"""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEEDBACK = ROOT / "data" / "grenade_feedback.json"
OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "ndx700")


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def pending():
    out = gh("issue", "list", "--state", "open", "--search", "[NadeAtlas] in:title", "--limit", "100",
             "--json", "number,title,body,author,createdAt")
    return [i for i in json.loads(out) if i["title"].startswith("[NadeAtlas]") and i["author"]["login"] == OWNER]


def main():
    entries = json.loads(FEEDBACK.read_text("utf-8")) if FEEDBACK.exists() else []
    seen = {e.get("issue") for e in entries}
    taken = []
    for issue in pending():
        n = issue["number"]
        m = re.search(r"```json\s*(\{.*?\})\s*```", issue["body"] or "", re.S)
        if not m:
            gh("issue", "comment", str(n), "--body", "没找到道具数据（```json 块），没有记录。")
            continue
        try:
            rec = json.loads(m.group(1))
            assert rec.get("action") in ("delete", "purpose", "issue", "note")
            for k in ("type", "side"):
                assert isinstance(rec.get(k), str) and rec[k]
            for k in ("foot", "detonate"):
                assert isinstance(rec.get(k), list) and len(rec[k]) == 3
        except Exception as e:
            gh("issue", "comment", str(n), "--body", f"道具数据读不出来：{e}")
            continue
        if n not in seen:
            rec["issue"] = n
            rec["at"] = issue["createdAt"]
            entries.append(rec)
            taken.append((n, rec["action"]))
    if taken:
        FEEDBACK.parent.mkdir(exist_ok=True)
        FEEDBACK.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n", "utf-8")
    Path(os.environ.get("GITHUB_OUTPUT", "/dev/null")).open("a").write(
        "taken=" + " ".join(f"{n}:{a}" for n, a in taken) + "\n")
    print("taken", taken)


if __name__ == "__main__":
    sys.exit(main())
