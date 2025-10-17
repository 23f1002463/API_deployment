import subprocess, base64, re, requests
from pathlib import Path

def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True)
    return r.stdout.strip()

def write_text(path: Path, content: str):
    path.write_text(content, encoding="utf-8")

def http_get_data_uri(url: str) -> bytes:
    if url.startswith("data:"):
        m = re.match(r"data:.*?;base64,(.*)", url)
        return base64.b64decode(m.group(1)) if m else b""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content

def git_init_and_push(root: Path, repo_url: str, message: str):
    run(["git", "init"], cwd=root)
    run(["git", "checkout", "-b", "main"], cwd=root)
    run(["git", "add", "."], cwd=root)
    run(["git", "commit", "-m", message], cwd=root)
    run(["git", "remote", "add", "origin", repo_url], cwd=root)
    run(["git", "push", "-u", "origin", "main"], cwd=root)
    sha = run(["git", "rev-parse", "HEAD"], cwd=root)
    return sha
