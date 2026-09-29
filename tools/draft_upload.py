"""Nahrá súbory do skrytého (draft) releasu s daným názvom. Použitie: draft_upload.py NAME file..."""
import json, os, sys, urllib.request, urllib.parse, time

tok = os.environ["GH_TOKEN"]; repo = os.environ["GITHUB_REPOSITORY"]

def api(method, url, data=None, ctype="application/json"):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json", "Content-Type": ctype})
    for i in range(5):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                b = r.read(); return json.loads(b) if b else None
        except urllib.error.HTTPError as e:
            if e.code in (404, 422) or i == 4: raise
            print("retry", e); time.sleep(5 * (i + 1))

name = sys.argv[1]
rels = api("GET", f"https://api.github.com/repos/{repo}/releases?per_page=100")
rel = next((r for r in rels if r["name"] == name), None)
if not rel:
    rel = api("POST", f"https://api.github.com/repos/{repo}/releases",
              json.dumps({"tag_name": name, "name": name, "draft": True, "body": "internal"}).encode())
for f in sys.argv[2:]:
    base = os.path.basename(f)
    for a in rel.get("assets", []):
        if a["name"] == base:
            api("DELETE", f"https://api.github.com/repos/{repo}/releases/assets/{a['id']}")
    up = rel["upload_url"].split("{")[0] + "?name=" + urllib.parse.quote(base)
    api("POST", up, open(f, "rb").read(), "application/octet-stream")
    print("uploaded", base, os.path.getsize(f))
