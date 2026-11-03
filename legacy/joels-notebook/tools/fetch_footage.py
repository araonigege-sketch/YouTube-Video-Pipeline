"""For each beat, search Pixabay videos and download N unused clips.
Usage: python3 fetch_footage.py <beats.json> <outdir> [per_beat]
Writes outdir/manifest.json: [{beat, files:[{path,id,page,user,duration}]}] and a contact sheet of first frames.
"""
import sys, json, os, time, urllib.error, pathlib, urllib.request, urllib.parse, concurrent.futures as cf

beats = json.load(open(sys.argv[1]))
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
per = int(sys.argv[3]) if len(sys.argv) > 3 else 2
key = open(os.path.expanduser("~/.secrets/pixabay_key")).read().strip()
used, cache = set(), {}
opener = urllib.request.build_opener(); opener.addheaders = [("User-Agent", "Mozilla/5.0 (pipeline)")]
urllib.request.install_opener(opener)

def search(q):
    if q not in cache:
        url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode(
            {"key": key, "q": q, "per_page": 30, "safesearch": "true", "video_type": "film", "order": "popular"})
        for attempt in range(6):
            try:
                cache[q] = json.load(urllib.request.urlopen(url, timeout=30)).get("hits", []); break
            except urllib.error.HTTPError as e:
                if e.code != 429: raise
                time.sleep(15 * (attempt + 1))
    return cache[q]

def pick(q):
    hits = search(q)
    if len(hits) < per:  # broaden: drop the last word
        hits += search(" ".join(q.split()[:-1]) or q)
    chosen = []
    for h in hits:
        v = h["videos"]
        f = v.get("medium") if v.get("medium", {}).get("width", 0) >= 1280 else v.get("large")
        if not f or not f.get("url") or f["width"] < 1280 or f["width"] < f["height"] * 1.3 or h["duration"] < 5:
            continue
        if h["id"] in used:
            continue
        used.add(h["id"])
        chosen.append({"id": h["id"], "url": f["url"], "page": h["pageURL"], "user": h["user"],
                       "duration": h["duration"], "w": f["width"], "h": f["height"]})
        if len(chosen) == per:
            break
    return chosen

manifest, jobs = [], []
for i, b in enumerate(beats):
    files = pick(b["q"])
    for j, f in enumerate(files):
        f["path"] = str(out / f"b{i:02d}_{j}.mp4")
        jobs.append(f)
    manifest.append({"beat": i, "q": b["q"], "files": files})
    if len(files) < per:
        print(f"beat {i} '{b['q']}': only {len(files)} clips", flush=True)

def dl(f):
    for attempt in range(8):
        if os.path.exists(f["path"]): break
        try:
            urllib.request.urlretrieve(f["url"], f["path"] + ".part"); os.rename(f["path"] + ".part", f["path"])
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(10 * (attempt + 1))
    return f["path"]

with cf.ThreadPoolExecutor(3) as ex:
    list(ex.map(dl, jobs))
json.dump(manifest, open(out / "manifest.json", "w"), indent=1)
print(f"downloaded {len(jobs)} clips")
