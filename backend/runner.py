"""Background pipeline execution + in-process event pub/sub for SSE.

A run executes as an asyncio task. Each agent event is persisted to SQLite and
published to any live SSE subscribers for that run. Persistence means a client
can connect late and replay the full history, then follow live.
"""
from __future__ import annotations

import asyncio

from . import repository
from .agents.context import RunContext
from .agents.orchestrator import run_pipeline
from .config import get_settings
from .llm.factory import get_llm_client
from .research.factory import get_search_provider
from .research.fetcher import PageFetcher

_subscribers: dict[str, set[asyncio.Queue]] = {}
_tasks: set[asyncio.Task] = set()
END = {"phase": "__end__"}


def subscribe(run_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(run_id, set()).add(q)
    return q


def unsubscribe(run_id: str, q: asyncio.Queue) -> None:
    subs = _subscribers.get(run_id)
    if subs:
        subs.discard(q)
        if not subs:
            _subscribers.pop(run_id, None)


async def _publish(run_id: str, event: dict) -> None:
    for q in list(_subscribers.get(run_id, ())):
        await q.put(event)


def launch(run_id: str, input_type: str, raw_input: str | None, source_url: str | None) -> None:
    task = asyncio.create_task(_run(run_id, input_type, raw_input, source_url))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def _run(run_id: str, input_type: str, raw_input: str | None, source_url: str | None) -> None:
    settings = get_settings()
    repository.set_run_status(run_id, "running")

    async def emit(agent: str, phase: str, message: str | None, payload: dict | None) -> None:
        ev = await asyncio.to_thread(repository.add_event, run_id, agent, phase, message, payload)
        await _publish(run_id, ev)

    try:
        ctx = RunContext(
            run_id=run_id,
            input_type=input_type,
            raw_input=raw_input or "",
            source_url=source_url,
            llm=get_llm_client(settings),
            search=get_search_provider(settings),
            fetcher=PageFetcher(),
            settings=settings,
            emit=emit,
            fetch_budget=settings.max_fetch_per_run,
        )
        out = await run_pipeline(ctx)
        report = out["report"]

        await asyncio.to_thread(
            repository.add_evidence_bulk, run_id,
            [{"title": e.title, "url": e.url, "snippet": e.snippet,
              "source_type": e.source_type} for e in ctx.evidence],
        )
        await asyncio.to_thread(
            repository.save_report, run_id, out["report_md"], report.model_dump(),
            report.india_market_fit.score, report.recommendation, report.confidence,
        )
        await asyncio.to_thread(repository.set_run_status, run_id, "done")
        await emit("pipeline", "done", "Run complete",
                   {"recommendation": report.recommendation,
                    "tokens": {"input": ctx.input_tokens, "output": ctx.output_tokens}})
    except Exception as exc:  # pipeline-level failure
        await asyncio.to_thread(repository.set_run_status, run_id, "error", str(exc))
        await emit("pipeline", "error", str(exc), None)
    finally:
        await _publish(run_id, END)
