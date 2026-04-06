from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.agents import my_finance_agent_persistent
from app.schema import BriefRequest, BriefResponse
from app.db import (
    init_db,
    create_thread,
    list_threads,
    get_thread,
    save_message,
    get_messages,
    delete_thread,
)
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(
    title="FinBot",
    description="FinBot is a financial analysis agent that provides stock analysis and insights.",
    version="1.0.0",
)

# CORS — allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# ── Health ───────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


# ── Chat / Brief ────────────────────────────────────────
@app.post("/brief", response_model=BriefResponse)
async def get_brief(request: BriefRequest):
    # Save user message
    save_message(request.thread_id, "user", request.query)

    # Invoke the persistent agent
    result = my_finance_agent_persistent.invoke(
        {"messages": [{"role": "user", "content": request.query}]},
        {"configurable": {"thread_id": request.thread_id}},
    )

    assistant_content = result["messages"][-1].content
    # Save assistant message
    save_message(request.thread_id, "assistant", assistant_content)

    return BriefResponse(result=assistant_content)


# ── Thread management ───────────────────────────────────
class ThreadCreate(BaseModel):
    title: Optional[str] = None


class ThreadResponse(BaseModel):
    id: str
    title: str
    created_at: str


class MessageResponse(BaseModel):
    id: int
    thread_id: str
    role: str
    content: str
    created_at: str


@app.post("/threads", response_model=ThreadResponse)
def api_create_thread(body: ThreadCreate):
    thread_id = str(uuid.uuid4())
    title = body.title or "New Chat"
    create_thread(thread_id, title)
    thread = get_thread(thread_id)
    return ThreadResponse(id=thread["id"], title=thread["title"], created_at=thread["created_at"])


@app.get("/threads", response_model=list[ThreadResponse])
def api_list_threads():
    threads = list_threads()
    return [
        ThreadResponse(id=t["id"], title=t["title"], created_at=t["created_at"])
        for t in threads
    ]


@app.get("/threads/{thread_id}/messages", response_model=list[MessageResponse])
def api_get_messages(thread_id: str):
    msgs = get_messages(thread_id)
    return [
        MessageResponse(
            id=m["id"],
            thread_id=m["thread_id"],
            role=m["role"],
            content=m["content"],
            created_at=m["created_at"],
        )
        for m in msgs
    ]


@app.delete("/threads/{thread_id}")
def api_delete_thread(thread_id: str):
    delete_thread(thread_id)
    return {"status": "deleted"}
