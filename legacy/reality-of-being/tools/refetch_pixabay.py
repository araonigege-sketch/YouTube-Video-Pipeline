"""Re-download only the Pixabay clips a project's pools.json uses (from the saved manifests).
Usage: python3 refetch_pixabay.py <projdir>    (needs ~/.secrets/pixabay_key not required: URLs are direct CDN links)
"""
import sys, json, os, time, pathlib, urllib.request, urllib.error
P = pathlib.Path(sys.argv[1])
opener = urllib.request.build_opener(); opener.addheaders = [("User-Agent", "Mozilla/5.0 (pipeline)")]
urllib.request.install_opener(opener)
pools = json.load(open(P / "pools.json"))
need = {c for v in pools.values() for c in v if ":" not in c}
urls = {}
for sub, prefix in (("footage", ""), ("extra", "x")):
    for m in json.load(open(P / sub / "manifest.json")):
        for j, f in enumerate(m["files"]):
            urls[f"{prefix}b{m['beat']:02d}_{j}"] = (f["url"], P / sub / f"b{m['beat']:02d}_{j}.mp4")
for c in sorted(need):
    url, dest = urls[c]
    for attempt in range(8):
        if dest.exists(): break
        try:
            urllib.request.urlretrieve(url, str(dest) + ".part"); os.rename(str(dest) + ".part", dest)
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(10 * (attempt + 1))
    time.sleep(0.3)
print(f"{len(need)} Pixabay clips ready")
