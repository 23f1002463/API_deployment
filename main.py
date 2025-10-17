from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

# Load .env once at startup
load_dotenv()

from models import TaskRequest, Ack
from generator import generate_or_update_repo
from notify import notify_evaluator_with_backoff

app = FastAPI(title="LLM Code Deployment")

def get_required_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}. Did you create .env?")
    return val

EXPECTED_SECRET = get_required_env("STUDENT_SECRET")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/api/task", response_model=Ack)
async def receive_task(req: TaskRequest, background: BackgroundTasks):
    if req.secret != EXPECTED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    ack = Ack(status="ok", message="Task accepted", task=req.task, round=req.round, nonce=req.nonce)
    background.add_task(process_task, req)  # don’t block the HTTP 200
    return JSONResponse(ack.model_dump())

async def process_task(req: TaskRequest):
    # build repo + deploy pages
    repo_meta = await generate_or_update_repo(req)
    # notify evaluator
    payload = {
        "email": req.email,
        "task": req.task,
        "round": req.round,
        "nonce": req.nonce,
        **repo_meta,
    }
    await notify_evaluator_with_backoff(req.evaluation_url, payload)
