"""Stiahne Poly Haven modely (CC0) ako .blend + textúry.
Použitie: python3 polyhaven_fetch.py catalog OUT_DIR
          python3 polyhaven_fetch.py ids "id1,id2" RES OUT_DIR"""
import json, os, sys, urllib.request, time

UA = {"User-Agent": "nasflix-intro-ci/1.0"}

def get(url, retries=4):
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except Exception as e:
            print("retry", url, e); time.sleep(3 * (i + 1))
    raise RuntimeError(url)

def catalog(out):
    os.makedirs(out, exist_ok=True)
    for t in ("models", "textures"):
        d = json.loads(get(f"https://api.polyhaven.com/assets?t={t}"))
        slim = {k: {"name": v.get("name"), "categories": v.get("categories"), "tags": v.get("tags"),
                    "dimensions": v.get("dimensions"), "polycount": v.get("polycount")} for k, v in d.items()}
        json.dump(slim, open(f"{out}/{t}.json", "w"), indent=0, ensure_ascii=False)
        print(t, len(slim))

def fetch(ids, res, out):
    for aid in [x.strip() for x in ids.split(",") if x.strip()]:
        files = json.loads(get(f"https://api.polyhaven.com/files/{aid}"))
        dest = os.path.join(out, aid); os.makedirs(dest, exist_ok=True)
        fmt = "blend" if "blend" in files else "gltf"
        entry = files[fmt]
        r = res if res in entry else sorted(entry.keys())[0]
        e = entry[r][fmt]
        main = e["url"]
        open(os.path.join(dest, os.path.basename(main)), "wb").write(get(main))
        for rel, inc in (e.get("include") or {}).items():
            p = os.path.join(dest, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(get(inc["url"]))
        print("OK", aid, fmt, r)

if __name__ == "__main__":
    if sys.argv[1] == "catalog":
        catalog(sys.argv[2])
    else:
        fetch(sys.argv[2], sys.argv[3], sys.argv[4])
