#!/usr/bin/env python3
"""Keep the round index (rounds/) in step with the replay list (index-all-maps.json).

The app's round filter asks questions like "rounds this team lost on the CT side after winning the pistol round" across
every parsed replay. The phone cannot download every replay to answer that, so the facts it needs are worked out here,
once per replay, with the app's own .nar reader (RoundIndex.kt, compiled by the workflow), and published as:

  rounds/m/<matchId>.json   one match: the list's fields plus every round's facts (kept so a replay is read only once)
  rounds/all.json           every match still in the list, newest first, in one compact file: what the app reads

  build_rounds.py --check   prints pending=<n> (replays not indexed yet) to $GITHUB_OUTPUT and exits
  build_rounds.py           downloads up to MAX_NEW of them, runs $ROUNDS_JAR on them and rewrites rounds/all.json

A replay that cannot be read is remembered in rounds/skipped.json (by its address) and tried again only when its
address changes. Prints ::notice:: / ::warning:: lines for the Actions summary.
"""
import json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "rounds"
MATCHES = OUT / "m"
SKIPPED = OUT / "skipped.json"
PLACES = Path(__file__).resolve().parent / "places"
# Bumped when the facts change shape or meaning: every replay is read again.
FORMAT = 2
MAX_NEW = int(os.environ.get("ROUNDS_MAX_NEW", "200"))
FIELDS = {"date": "date", "event": "event", "team1": "t1", "team2": "t2", "map": "map", "replay": "replay"}


def load(path, default):
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return default


def entries():
    out = []
    for e in load(ROOT / "index-all-maps.json", []):
        if isinstance(e, dict) and e.get("matchId") and str(e.get("replay", "")).startswith("https://") and e.get("team1") and e.get("team2"):
            out.append(e)
    return out


def done(e):
    m = load(MATCHES / f"{e['matchId']}.json", None)
    return isinstance(m, dict) and m.get("replay") == e["replay"] and m.get("v") == FORMAT


def pending(list_, skipped):
    return [e for e in list_ if not done(e) and skipped.get(e["matchId"]) != e["replay"]]


def output(**kv):
    path = os.environ.get("GITHUB_OUTPUT")
    lines = "".join(f"{k}={v}\n" for k, v in kv.items())
    if path:
        with open(path, "a") as f:
            f.write(lines)
    print(lines, end="")


def download(url, dest):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nadeatlas-round-index"})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
                while True:
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    f.write(chunk)
            return True
        except Exception as ex:  # network trouble: try again, then leave it for the next run
            print(f"download {url}: {ex}")
            time.sleep(3 * (attempt + 1))
    return False


def combine(list_):
    """rounds/all.json from the per-match files of matches still listed, newest first."""
    matches = []
    for e in sorted(list_, key=lambda x: x.get("date", ""), reverse=True):
        m = load(MATCHES / f"{e['matchId']}.json", None)
        if isinstance(m, dict) and m.get("replay") == e["replay"] and m.get("rounds"):
            matches.append(m)
    doc = {
        "v": FORMAT,
        "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        # How the facts were worked out, for anyone reading the file (see RoundIndex.kt).
        "about": {"buy": "0 pistol, 1 eco (<7000 team equipment at freeze end), 2 force, 3 full (>=17000 and >=3 rifles)",
                  "sides": "pairs are [CT, T]; 'al' is alive counts CT then T after each death",
                  "why": "e bomb exploded, d defused, k elimination, t time ran out, s surrender",
                  "atk": "T play on Dust II / Mirage: k default (控图), rush (爆弹), split (夹击), rotate (转点), none; site; t seconds to the hit; via ways in"},
        "matches": matches,
    }
    text = json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n"
    path = OUT / "all.json"
    old = path.read_text("utf-8") if path.exists() else ""
    # Only the time stamp differs: leave the file alone, so nothing is committed.
    strip = lambda t: t.split('"updated":', 1)[-1].split(",", 1)[-1]
    if old and strip(old) == strip(text):
        return False, len(matches), sum(len(m["rounds"]) for m in matches)
    path.write_text(text, "utf-8")
    return True, len(matches), sum(len(m["rounds"]) for m in matches)


def main():
    list_ = entries()
    skipped = load(SKIPPED, {})
    todo = pending(list_, skipped)
    if "--check" in sys.argv:
        output(pending=len(todo) or int(not (OUT / "all.json").exists()))
        return 0
    jar = os.environ.get("ROUNDS_JAR")
    MATCHES.mkdir(parents=True, exist_ok=True)
    batch = todo[:MAX_NEW]
    if batch and not jar:
        print("::error::ROUNDS_JAR is not set"); return 1
    read = failed = 0
    if batch:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); jobs = []
            for e in batch:
                nar = tmp / f"{e['matchId']}.nar"
                if download(e["replay"], nar):
                    jobs.append((e, nar))
                else:
                    print(f"::warning::{e['matchId']}: replay could not be downloaded, will retry")
            (tmp / "jobs.tsv").write_text("".join(f"{e['matchId']}\t{nar}\t{e['team1']}\t{e['team2']}\n" for e, nar in jobs), "utf-8")
            facts = tmp / "facts"
            os.environ.setdefault("ROUNDS_PLACES", str(PLACES))
            run = subprocess.run(["java", "-Xmx3g", "-cp", jar, "RoundIndexKt", str(facts), str(tmp / "jobs.tsv")], text=True, capture_output=True)
            print(run.stdout[-20000:]); print(run.stderr[-5000:], file=sys.stderr)
            for line in run.stdout.splitlines():
                if line.startswith("::warning::"):
                    print(line)
            for e, nar in jobs:
                f = facts / f"{e['matchId']}.json"
                if not f.exists() and run.returncode != 0:
                    failed += 1  # the reader itself failed: try again next run
                    continue
                if not f.exists():
                    skipped[e["matchId"]] = e["replay"]; failed += 1
                    continue
                m = {"v": FORMAT, "id": e["matchId"]}
                for k, short in FIELDS.items():
                    m[short] = e.get(k, "")
                m.update(json.loads(f.read_text("utf-8")))
                (MATCHES / f"{e['matchId']}.json").write_text(json.dumps(m, ensure_ascii=False, separators=(",", ":")) + "\n", "utf-8")
                skipped.pop(e["matchId"], None); read += 1
        SKIPPED.write_text(json.dumps(skipped, indent=1, sort_keys=True) + "\n", "utf-8")
    changed, n_matches, n_rounds = combine(list_)
    size = (OUT / "all.json").stat().st_size if (OUT / "all.json").exists() else 0
    print(f"::notice::round index: read {read}, failed {failed}, left {len(todo) - len(batch)}; all.json {n_matches} matches, {n_rounds} rounds, {size // 1024} KB")
    output(changed=int(changed or read > 0 or failed > 0), matches=n_matches, rounds=n_rounds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
