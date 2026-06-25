import pytest

from backend.agents import base
from backend.agents.base import Agent
from backend.agents.context import RunContext
from backend.config import Settings
from backend.llm.base import LLMResponse

from .fakes import FakeFetcher, FakeSearch


class FlakyLLM:
    """Fails `fail_times` times, then returns valid JSON."""
    name = "flaky"

    def __init__(self, fail_times):
        self.fail_times = fail_times
        self.calls = 0

    async def complete(self, system, user, *, json_mode=False, max_tokens=4096, temperature=0.3):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("transient 503")
        return LLMResponse(text='{"ok": true}', input_tokens=5, output_tokens=2)


class _Probe(Agent):
    name = "probe"

    async def run(self, ctx):
        return await self.complete_json(ctx, "sys", "user")


def _ctx(llm):
    return RunContext(
        run_id="t", input_type="text", raw_input="x", source_url=None,
        llm=llm, search=FakeSearch(), fetcher=FakeFetcher(), settings=Settings(),
    )


async def test_retry_recovers_after_transient_failures(monkeypatch):
    async def _no_sleep(_):
        return None
    monkeypatch.setattr(base.asyncio, "sleep", _no_sleep)

    llm = FlakyLLM(fail_times=2)
    result = await _Probe().run(_ctx(llm))
    assert result == {"ok": True}
    assert llm.calls == 3  # 2 failures + 1 success


async def test_retry_gives_up_after_max_attempts(monkeypatch):
    async def _no_sleep(_):
        return None
    monkeypatch.setattr(base.asyncio, "sleep", _no_sleep)

    llm = FlakyLLM(fail_times=99)
    with pytest.raises(RuntimeError):
        await _Probe().run(_ctx(llm))
    assert llm.calls == 3  # capped at 3 attempts
