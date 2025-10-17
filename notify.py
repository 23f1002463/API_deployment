import time, os, requests

def _extra_header():
    h = os.getenv("EVAL_AUTH_HEADER")
    if not h:
        return None, None
    if ": " in h:
        k, v = h.split(": ", 1)
        return k, v
    return None, None

async def notify_evaluator_with_backoff(url: str, payload: dict):
    delay = 1
    for _ in range(8):
        try:
            headers = {"Content-Type": "application/json"}
            k, v = _extra_header()
            if k:
                headers[k] = v
            r = requests.post(url, json=payload, headers=headers, timeout=20)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(delay)
        delay = min(delay * 2, 60)
    return False

