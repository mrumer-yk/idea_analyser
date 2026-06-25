"""Agent base class + robust JSON-completion helper."""
from __future__ import annotations

import asyncio
import json
import re
from abc import ABC, abstractmethod

from ..config import get_settings
from ..llm.base import LLMResponse
from .context import RunContext

# Global cap on concurrent LLM calls, shared across all in-flight runs so many
# parallel analyses don't trigger provider rate limits. Keyed by event loop so
# it stays valid across test loops.
_sems: dict = {}


def _llm_semaphore() -> asyncio.Semaphore:
    loop = asyncio.get_running_loop()
    sem = _sems.get(loop)
    if sem is None:
        sem = asyncio.Semaphore(get_settings().max_concurrent_llm)
        _sems[loop] = sem
    return sem

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def parse_json_object(text: str) -> dict:
    """Best-effort extraction of a single JSON object from model output."""
    if not text:
        raise ValueError("empty model output")
    text = text.strip()

    # strip ```json ... ``` fences if present
    m = _FENCE_RE.search(text)
    if m:
        text = m.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # fall back to the first balanced {...} span
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("no JSON object found in model output")


def render_evidence(ctx: RunContext, limit: int = 30) -> str:
    """Compact, numbered evidence list the LLM may cite from (URLs only)."""
    if not ctx.evidence:
        return "(no evidence gathered yet)"
    lines = []
    for e in ctx.evidence[:limit]:
        snippet = (e.snippet or "").replace("\n", " ")[:280]
        lines.append(f"- [{e.source_type}] {e.title} | {e.url}\n  {snippet}")
    return "\n".join(lines)


async def _complete_with_retries(
    ctx: RunContext, system: str, user: str, *, max_tokens: int, temperature: float,
    attempts: int = 3,
) -> LLMResponse:
    """Call the LLM, retrying transient failures with exponential backoff."""
    last_exc: Exception | None = None
    sem = _llm_semaphore()
    for i in range(attempts):
        try:
            async with sem:
                return await ctx.llm.complete(
                    system, user, json_mode=True,
                    max_tokens=max_tokens, temperature=temperature,
                )
        except Exception as exc:  # network / rate-limit / 5xx
            last_exc = exc
            if i < attempts - 1:
                await asyncio.sleep(2 ** i)
    raise last_exc  # type: ignore[misc]


class Agent(ABC):
    name: str = "agent"

    @abstractmethod
    async def run(self, ctx: RunContext) -> dict:
        ...

    async def complete_json(
        self,
        ctx: RunContext,
        system: str,
        user: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> dict:
        """Call the LLM in JSON mode with retries + one parse-repair, w/ accounting."""
        resp = await _complete_with_retries(
            ctx, system, user, max_tokens=max_tokens, temperature=temperature
        )
        ctx.account(resp.input_tokens, resp.output_tokens)
        try:
            return parse_json_object(resp.text)
        except ValueError:
            repair = await _complete_with_retries(
                ctx, system,
                user + "\n\nYour previous reply was not valid JSON. Reply with ONLY "
                "a single valid JSON object, no prose.",
                max_tokens=max_tokens, temperature=0.0,
            )
            ctx.account(repair.input_tokens, repair.output_tokens)
            return parse_json_object(repair.text)
