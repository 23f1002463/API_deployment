# github.py
import os, requests, urllib.parse

GH = "https://api.github.com"

def _token() -> str:
    t = os.getenv("GITHUB_TOKEN")
    if not t:
        raise RuntimeError("Missing GITHUB_TOKEN in .env / Render env")
    return t

def _owner() -> str:
    o = os.getenv("GITHUB_USERNAME")
    if not o:
        raise RuntimeError("Missing GITHUB_USERNAME in .env / Render env")
    return o

def _headers():
    return {"Authorization": f"Bearer {_token()}", "Accept": "application/vnd.github+json"}

def _auth_remote(owner: str, name: str) -> str:
    # use x-access-token to avoid username/password prompts
    tok = urllib.parse.quote(_token(), safe="")
    return f"https://x-access-token:{tok}@github.com/{owner}/{name}.git"

def create_public_repo(name: str) -> str:
    owner = _owner()
    h = _headers()

    # Reuse repo if it already exists
    r = requests.get(f"{GH}/repos/{owner}/{name}", headers=h, timeout=30)
    if r.status_code == 200:
        return _auth_remote(owner, name)

    # Create new public repo
    r = requests.post(f"{GH}/user/repos", headers=h,
                      json={"name": name, "private": False, "auto_init": False},
                      timeout=30)
    r.raise_for_status()
    return _auth_remote(owner, name)

# (optional) auto-enable Pages via API so actions don't 404
def enable_pages_for_repo(owner: str, name: str):
    h = _headers()
    r = requests.post(f"{GH}/repos/{owner}/{name}/pages", headers=h,
                      json={"build_type": "workflow"}, timeout=30)
    if r.status_code not in (201, 204):
        print(f"[warn] pages enable failed ({r.status_code}): {r.text}")

