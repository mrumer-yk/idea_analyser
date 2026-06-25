"""HTTP API routes (mounted under /api)."""
from __future__ import annotations

import json
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, model_validator

from . import repository, runner
from .config import get_settings

router = APIRouter()


class CreateRun(BaseModel):
    input_type: Literal["text", "url"]
    raw_input: Optional[str] = None
    source_url: Optional[str] = None

    @model_validator(mode="after")
    def _check(self):
        if self.input_type == "text" and not (self.raw_input and self.raw_input.strip()):
            raise ValueError("raw_input is required when input_type='text'")
        if self.input_type == "url" and not (self.source_url and self.source_url.strip()):
            raise ValueError("source_url is required when input_type='url'")
        return self


@router.post("/runs")
async def create_run(body: CreateRun):
    run_id = uuid.uuid4().hex
    provider = get_settings().llm_provider
    repository.create_run(run_id, body.input_type, body.raw_input, body.source_url, provider)
    runner.launch(run_id, body.input_type, body.raw_input, body.source_url)
    return {"run_id": run_id}


@router.get("/runs")
async def list_runs():
    return {"runs": repository.list_runs()}


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    run = repository.get_run(run_id)
    if not run:
        raise HTTPException(404, "run not found")
    report = repository.get_report(run_id)
    return {
        "run": run,
        "status": run["status"],
        "report_md": report["report_md"] if report else None,
        "report_json": report["report_json"] if report else None,
        "evidence": repository.list_evidence(run_id),
        "events": repository.list_events(run_id),
    }


@router.get("/runs/{run_id}/report.json")
async def get_report_json(run_id: str):
    report = repository.get_report(run_id)
    if not report or not report["report_json"]:
        raise HTTPException(404, "report not ready")
    return JSONResponse(report["report_json"])


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


@router.get("/runs/{run_id}/stream")
async def stream(run_id: str):
    if not repository.get_run(run_id):
        raise HTTPException(404, "run not found")

    async def gen():
        q = runner.subscribe(run_id)
        try:
            max_id = 0
            for ev in repository.list_events(run_id):  # replay history
                max_id = max(max_id, ev["id"])
                yield _sse(ev)
            run = repository.get_run(run_id)
            if run and run["status"] in ("done", "error"):
                yield _sse(runner.END)
                return
            while True:  # follow live
                ev = await q.get()
                if ev.get("phase") == "__end__":
                    yield _sse(ev)
                    break
                if ev.get("id") and ev["id"] <= max_id:
                    continue  # already replayed
                yield _sse(ev)
        finally:
            runner.unsubscribe(run_id, q)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
