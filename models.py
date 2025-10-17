from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class Attachment(BaseModel):
    name: str
    url: str  # data: URI or http(s)

class TaskRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int
    nonce: str
    brief: str
    checks: List[str]
    evaluation_url: HttpUrl
    attachments: Optional[List[Attachment]] = []

class Ack(BaseModel):
    status: str
    message: str
    task: str
    round: int
    nonce: str
