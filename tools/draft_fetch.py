"""Download assets of a (draft) release. Usage: draft_fetch.py RELEASE [--prefix P] [name ...]"""
import json, os, sys, urllib.request, time
tok = os.environ["GH_TOKEN"]; repo = os.environ["GITHUB_REPOSITORY"]
args = sys.argv[1:]; rel_name = args[0]; names = []; prefix = None
i = 1
while i < len(args):
    if args[i] == "--prefix": prefix = args[i + 1]; i += 2
    else: names.append(args[i]); i += 1
def req(url, accept="application/vnd.github+json"):
    for k in range(5):
        try:
            r = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}", "Accept": accept})
            with urllib.request.urlopen(r, timeout=600) as resp:
                return resp.read()
        except Exception as e:
            print("retry", url, e); time.sleep(5 * (k + 1))
    raise RuntimeError(url)
rels = json.loads(req(f"https://api.github.com/repos/{repo}/releases?per_page=100"))
rel = next(r for r in rels if r["name"] == rel_name)
for a in rel["assets"]:
    if a["name"] in names or (prefix and a["name"].startswith(prefix)):
        data = req(a["url"], "application/octet-stream")
        open(a["name"], "wb").write(data); print("got", a["name"], len(data))
