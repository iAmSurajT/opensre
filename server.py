"""Self-hosted OpenSRE API server — no LangGraph Platform license required.

Wraps the open-source agent graph in a FastAPI app with thread management
backed by local state (in-memory or Postgres if configured).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel

from app.config import LLMSettings, get_environment
from app.graph_pipeline import build_graph
from app.state import make_initial_state, make_chat_state, ChatMessage
from app.version import get_version
from app.webapp import HealthResponse, get_health_response

app = FastAPI(title="OpenSRE Self-Hosted API", version="0.1.0")

graph = build_graph()

threads: dict[str, dict[str, Any]] = {}


class CreateThreadResponse(BaseModel):
    thread_id: str
    created_at: str


class RunRequest(BaseModel):
    input: dict[str, Any]
    mode: str = "investigation"


class RunResponse(BaseModel):
    run_id: str
    thread_id: str
    status: str
    result: dict[str, Any] | None = None


class ThreadStateResponse(BaseModel):
    thread_id: str
    runs: list[dict[str, Any]]
    latest_result: dict[str, Any] | None = None


@app.get("/ok")
def health_check():
    return {"ok": True}


@app.get("/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    health_response = get_health_response()
    response.status_code = (
        status.HTTP_200_OK if health_response.ok else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return health_response


@app.post("/threads", response_model=CreateThreadResponse)
def create_thread():
    thread_id = str(uuid.uuid4())
    threads[thread_id] = {
        "id": thread_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runs": [],
    }
    return CreateThreadResponse(
        thread_id=thread_id,
        created_at=threads[thread_id]["created_at"],
    )


@app.post("/threads/{thread_id}/runs", response_model=RunResponse)
async def create_run(thread_id: str, request: RunRequest):
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    run_id = str(uuid.uuid4())
    user_input = request.input

    if request.mode == "investigation":
        raw_alert = user_input.get("alert", user_input.get("raw_alert", user_input))
        alert_name = user_input.get("name", user_input.get("monitor", {}).get("name", "Manual Investigation"))
        severity = user_input.get("severity", "warning")

        initial_state = make_initial_state(
            alert_name=alert_name,
            pipeline_name="self-hosted",
            severity=severity,
            raw_alert=raw_alert,
        )
    else:
        raw_messages = user_input.get("messages", [])
        chat_messages: list[ChatMessage] = [
            ChatMessage(role=m.get("role", "user"), content=m.get("content", ""))
            for m in raw_messages
        ]
        initial_state = make_chat_state(messages=chat_messages)

    try:
        result = await asyncio.to_thread(graph.invoke, initial_state)

        run_record = {
            "run_id": run_id,
            "status": "completed",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "result": {
                "root_cause": result.get("root_cause", ""),
                "root_cause_category": result.get("root_cause_category", ""),
                "remediation_steps": result.get("remediation_steps", []),
                "report": result.get("report", ""),
                "evidence": result.get("evidence", {}),
                "hypotheses": result.get("hypotheses", []),
                "investigation_recommendations": result.get("investigation_recommendations", []),
            },
        }
    except Exception as e:
        run_record = {
            "run_id": run_id,
            "status": "failed",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "result": None,
        }

    threads[thread_id]["runs"].append(run_record)

    return RunResponse(
        run_id=run_id,
        thread_id=thread_id,
        status=run_record["status"],
        result=run_record.get("result"),
    )


@app.get("/threads/{thread_id}/state", response_model=ThreadStateResponse)
def get_thread_state(thread_id: str):
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread = threads[thread_id]
    latest = thread["runs"][-1] if thread["runs"] else None

    return ThreadStateResponse(
        thread_id=thread_id,
        runs=thread["runs"],
        latest_result=latest.get("result") if latest else None,
    )


@app.post("/investigate")
async def investigate_direct(request: RunRequest):
    """Convenience endpoint — creates a thread and runs investigation in one call."""
    thread_resp = create_thread()
    run_resp = await create_run(thread_resp.thread_id, request)
    return {
        "thread_id": thread_resp.thread_id,
        "run_id": run_resp.run_id,
        "status": run_resp.status,
        "result": run_resp.result,
    }
