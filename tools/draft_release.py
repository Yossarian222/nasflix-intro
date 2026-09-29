"""Create (or find) a draft release by name. Usage: draft_release.py NAME"""
import json, os, sys, urllib.request
tok = os.environ["GH_TOKEN"]; repo = os.environ["GITHUB_REPOSITORY"]; name = sys.argv[1]
H = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json", "Content-Type": "application/json"}
def api(method, url, data=None):
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=H), timeout=120) as r:
        b = r.read(); return json.loads(b) if b else None
rels = api("GET", f"https://api.github.com/repos/{repo}/releases?per_page=100")
if not any(r["name"] == name for r in rels):
    api("POST", f"https://api.github.com/repos/{repo}/releases",
        json.dumps({"tag_name": name, "name": name, "draft": True, "body": "internal"}).encode())
print("draft release ready:", name)
