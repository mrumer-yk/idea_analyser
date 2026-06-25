import asyncio

from backend import repository, runner

from .fakes import FakeFetcher, FakeLLM, FakeSearch


async def test_two_runs_stay_isolated(monkeypatch):
    monkeypatch.setattr(runner, "get_llm_client", lambda s=None: FakeLLM())
    monkeypatch.setattr(runner, "get_search_provider", lambda s=None: FakeSearch())
    monkeypatch.setattr(runner, "PageFetcher", lambda *a, **k: FakeFetcher())

    repository.create_run("A", "text", "idea A for india", None, "fake")
    repository.create_run("B", "url", None, "https://example.in", "fake")

    # Run both pipelines concurrently.
    await asyncio.gather(
        runner._run("A", "text", "idea A for india", None),
        runner._run("B", "url", None, "https://example.in"),
    )

    # Both completed independently.
    assert repository.get_run("A")["status"] == "done"
    assert repository.get_run("B")["status"] == "done"

    # Events are partitioned by run_id — no cross-contamination.
    ev_a = repository.list_events("A")
    ev_b = repository.list_events("B")
    assert all(e["run_id"] == "A" for e in ev_a)
    assert all(e["run_id"] == "B" for e in ev_b)
    assert ev_a and ev_b

    # Separate evidence pools and separate reports.
    assert repository.list_evidence("A")
    assert repository.list_evidence("B")
    assert repository.get_report("A") is not None
    assert repository.get_report("B") is not None
