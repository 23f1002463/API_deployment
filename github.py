import os, requests

GH = "https://api.github.com"

def _headers():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Missing GITHUB_TOKEN in .env")
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

def _owner():
    owner = os.getenv("GITHUB_USERNAME")
    if not owner:
        raise RuntimeError("Missing GITHUB_USERNAME in .env")
    return owner

def create_public_repo(name: str) -> str:
    owner = _owner()
    h = _headers()

    # idempotent: if exists, reuse
    r = requests.get(f"{GH}/repos/{owner}/{name}", headers=h)
    if r.status_code == 200:
        return r.json()["clone_url"]

    data = {"name": name, "private": False, "auto_init": False}
    r = requests.post(f"{GH}/user/repos", headers=h, json=data, timeout=30)
    r.raise_for_status()
    return r.json()["clone_url"]
