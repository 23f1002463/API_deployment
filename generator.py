import os, shutil, tempfile
from pathlib import Path
from typing import Dict

from utils import write_text, http_get_data_uri, git_init_and_push
from github import create_public_repo
from pages import write_pages_workflow, wait_for_pages_ok

def _owner() -> str:
    owner = os.getenv("GITHUB_USERNAME")
    if not owner:
        raise RuntimeError("Missing GITHUB_USERNAME in .env")
    return owner

KNOWN_TASKS = ["captcha-solver", "sum-of-sales", "markdown-to-html", "github-user-created"]

def _index_html_for(template: str) -> str:
    if template == "captcha-solver":
        return """<!doctype html><html lang="en"><head><meta charset="utf-8"/>
<title>Captcha Solver</title><meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>body{font-family:system-ui,Arial;margin:2rem} img{max-width:320px}</style></head>
<body><h1>Captcha Solver</h1><div id="status">Idle</div>
<img id="captcha" alt="captcha"/><p>Result: <strong id="captcha-text"></strong></p>
<script src="https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"></script>
<script>
const qs=new URLSearchParams(location.search);
const url=qs.get('url')||'attachments/sample.png';
const img=document.getElementById('captcha');
const out=document.getElementById('captcha-text');
const status=document.getElementById('status');
img.src=url; status.textContent='Loading image…';
const timeout=setTimeout(()=>{status.textContent='Timed out'},15000);
Tesseract.recognize(url,'eng',{logger:m=>status.textContent=m.status+' '+(m.progress||'')})
  .then(({data:{text}})=>{out.textContent=text.trim(); status.textContent='Done';})
  .catch(e=>{out.textContent=''; status.textContent='Failed: '+e.message;})
  .finally(()=>clearTimeout(timeout));
</script></body></html>"""
    if template == "markdown-to-html":
        return """<!doctype html><html><head><meta charset="utf-8"/><title>Markdown</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/default.min.css"/></head>
<body><div id="markdown-output"></div>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>(async()=>{const qs=new URLSearchParams(location.search);
const src=qs.get('url')||'attachments/input.md';
const md=await fetch(src).then(r=>r.text());
const html=marked.parse(md,{gfm:true});
document.querySelector('#markdown-output').innerHTML=html;
document.querySelectorAll('pre code').forEach(el=>hljs.highlightElement(el));})();</script>
</body></html>"""
    if template == "sum-of-sales":
        return """<!doctype html><html><head><meta charset="utf-8"/><title>Sales Summary</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5/dist/css/bootstrap.min.css"/></head>
<body class="container py-4"><h1>Sales Summary</h1><p>Total: <span id="total-sales">0</span></p>
<table class="table" id="product-sales" hidden><tbody></tbody></table>
<script>
(async function(){const url=new URL(location);
const att=url.searchParams.get('data')||'attachments/data.csv';
const txt=await fetch(att).then(r=>r.text());
const rows=txt.trim().split(/\\r?\\n/).map(r=>r.split(','));
const header=rows.shift();
const idx=header.findIndex(h=>/sales/i.test(h));
const total=rows.reduce((a,r)=>a+parseFloat(r[idx]||0),0);
document.querySelector('#total-sales').textContent=total.toFixed(2);}());
</script></body></html>"""
    # github-user-created
    return """<!doctype html><html><head><meta charset="utf-8"/><title>GitHub User Lookup</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5/dist/css/bootstrap.min.css"/></head>
<body class="container py-4"><form id="github-user-seed" class="row gy-2">
<div class="col-auto"><input class="form-control" name="user" placeholder="octocat" required/></div>
<div class="col-auto"><input class="form-control" name="token" placeholder="token (optional)"/></div>
<div class="col-auto"><button class="btn btn-primary">Lookup</button></div></form>
<p>Created at (UTC): <span id="github-created-at"></span></p>
<script>
const form=document.getElementById('github-user-seed');
form.addEventListener('submit',async(e)=>{e.preventDefault();
const u=form.user.value.trim();
const t=form.token.value.trim()||new URLSearchParams(location.search).get('token');
const h=t?{Authorization:`Bearer ${t}`}:{};
const r=await fetch(`https://api.github.com/users/${u}`,{headers:h});
const j=await r.json(); const d=new Date(j.created_at||0);
document.getElementById('github-created-at').textContent=d.toISOString().slice(0,10);});
</script></body></html>"""

def _readme(task: str, brief: str, rnd: int) -> str:
    return f"""# {task}

**Round {rnd}**

## Summary
{brief}

## Setup
Static site – no build step. Deployed with GitHub Pages via Actions.

## Usage
Open the Pages URL in a browser. Some apps accept query params (see page source).

## Code Explanation
Single-file `index.html` with minimal JS and CDN libraries to satisfy checks.

## License
MIT – see `LICENSE`.
"""

MIT = """MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
"""

def _pick_template(req) -> str:
    b = (req.brief or "").lower()
    t = (req.task or "").lower()
    for k in KNOWN_TASKS:
        if k in b or k in t:
            return k
    if "captcha" in b: return "captcha-solver"
    if "markdown" in b: return "markdown-to-html"
    if "sales" in b: return "sum-of-sales"
    if "github" in b: return "github-user-created"
    return "captcha-solver"

async def generate_or_update_repo(req) -> Dict[str, str]:
    owner = _owner()
    repo_name = f"{req.task}".replace("/", "-")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # write web app
        web = root
        template = _pick_template(req)
        write_text(web / "index.html", _index_html_for(template))

        # attachments
        if req.attachments:
            att_dir = web / "attachments"
            att_dir.mkdir(exist_ok=True)
            for att in req.attachments:
                data = http_get_data_uri(att.url)
                (att_dir / att.name).write_bytes(data)

        # README & LICENSE
        write_text(root / "README.md", _readme(req.task, req.brief, req.round))
        write_text(root / "LICENSE", MIT)

        # GitHub Pages workflow
        wf = root / ".github" / "workflows"
        wf.mkdir(parents=True, exist_ok=True)
        write_pages_workflow(wf / "pages.yml")

        # Create repo & push
        repo_url = create_public_repo(repo_name)
        commit_sha = git_init_and_push(root, repo_url, f"feat: {req.task} round {req.round}")

    pages_url = f"https://{owner}.github.io/{repo_name}/"
    await wait_for_pages_ok(pages_url)
    return {"repo_url": repo_url, "commit_sha": commit_sha, "pages_url": pages_url}
