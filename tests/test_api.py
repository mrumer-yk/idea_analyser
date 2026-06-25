import pytest
from fastapi.testclient import TestClient

from backend import repository, runner
from backend.main import app

from .fakes import FakeFetcher, FakeLLM, FakeSearch


async def test_runner_persists_full_run(monkeypatch):
    monkeypatch.setattr(runner, "get_llm_client", lambda s=None: FakeLLM())
    monkeypatch.setattr(runner, "get_search_provider", lambda s=None: FakeSearch())
    monkeypatch.setattr(runner, "PageFetcher", lambda *a, **k: FakeFetcher())

    repository.create_run("r1", "text", "an idea for india", None, "fake")
    await runner._run("r1", "text", "an idea for india", None)

    run = repository.get_run("r1")
    assert run["status"] == "done"

    report = repository.get_report("r1")
    assert report["recommendation"] in {"pursue", "pivot", "reject"}
    assert report["report_json"]["india_market_fit"]["score"] == 6.5

    events = repository.list_events("r1")
    assert any(e["phase"] == "done" for e in events)
    assert repository.list_evidence("r1")  # evidence persisted


def test_post_run_validation():
    with TestClient(app) as client:
        # text without raw_input -> 422
        r = client.post("/api/runs", json={"input_type": "text"})
        assert r.status_code == 422
        # url without source_url -> 422
        r = client.post("/api/runs", json={"input_type": "url"})
        assert r.status_code == 422


def test_post_run_creates_row(monkeypatch):
    monkeypatch.setattr(runner, "launch", lambda *a, **k: None)  # don't spawn pipeline
    with TestClient(app) as client:
        r = client.post("/api/runs", json={"input_type": "text", "raw_input": "idea"})
        assert r.status_code == 200
        run_id = r.json()["run_id"]
        assert repository.get_run(run_id)["status"] == "queued"


def test_get_run_and_report_endpoints():
    repository.create_run("r2", "text", "idea", None, "fake")
    repository.save_report(
        "r2", "# Report\nbody", {"recommendation": "pursue", "idea_summary": "x"},
        7.0, "pursue", "high",
    )
    repository.set_run_status("r2", "done")
    with TestClient(app) as client:
        r = client.get("/api/runs/r2")
        assert r.status_code == 200
        assert r.json()["report_json"]["recommendation"] == "pursue"

        r = client.get("/api/runs/r2/report.json")
        assert r.status_code == 200
        assert r.json()["recommendation"] == "pursue"

        r = client.get("/api/runs/missing")
        assert r.status_code == 404

        r = client.get("/api/runs")
        assert any(run["id"] == "r2" for run in r.json()["runs"])


def test_sse_stream_replays_finished_run():
    repository.create_run("r3", "text", "idea", None, "fake")
    repository.add_event("r3", "intake", "started", "go", None)
    repository.set_run_status("r3", "done")
    with TestClient(app) as client:
        r = client.get("/api/runs/r3/stream")
        assert r.status_code == 200
        assert "data:" in r.text
        assert "__end__" in r.text
