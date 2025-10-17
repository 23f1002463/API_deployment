import os, time, requests
from pathlib import Path

WORKFLOW = """
name: Deploy Pages
on:
  push:
    branches: [ main ]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Pages
        uses: actions/configure-pages@v5
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
  deploy:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
"""

def write_pages_workflow(path: Path):
    path.write_text(WORKFLOW, encoding="utf-8")

def _wait_seconds() -> int:
    try:
        return int(os.getenv("PAGES_WAIT_SECONDS", "120"))
    except Exception:
        return 120

async def wait_for_pages_ok(url: str):
    deadline = time.time() + _wait_seconds()
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(5)
    return False
