"""Shared run state passed between agents (the 'blackboard')."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional

from ..config import Settings
from ..llm.base import LLMClient
from ..research.base import SearchProvider
from ..research.fetcher import PageFetcher

# emit(agent, phase, message, payload) -> awaitable
EmitFn = Callable[[str, str, str, Optional[dict]], Awaitable[None]]


@dataclass
class Evidence:
    title: str
    url: str
    snippet: str
    source_type: str = "other"


async def _noop_emit(agent: str, phase: str, message: str, payload: Optional[dict]) -> None:
    return None


@dataclass
class RunContext:
    run_id: str
    input_type: str  # 'text' | 'url'
    raw_input: str
    source_url: Optional[str]
    llm: LLMClient
    search: SearchProvider
    fetcher: PageFetcher
    settings: Settings
    emit: EmitFn = _noop_emit
    evidence: list[Evidence] = field(default_factory=list)
    state: dict = field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    fetch_budget: int = 8

    def add_evidence(self, items: list[Evidence]) -> None:
        seen = {e.url for e in self.evidence}
        for it in items:
            if it.url and it.url not in seen:
                self.evidence.append(it)
                seen.add(it.url)

    def evidence_urls(self) -> set[str]:
        return {e.url for e in self.evidence}

    def account(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
