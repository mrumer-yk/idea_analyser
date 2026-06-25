# India Idea Validator

An agentic market-research system. Submit a startup idea (plain text, bullets, or a
website URL) and a pipeline of agents researches it against the **Indian market** and
returns a decision-ready report — target customers, competitors, TAM/SAM/SOM, revenue
models, risks, and a **pursue / pivot / reject** recommendation — plus a machine-readable
JSON summary.

Hard rules enforced by the system: prioritize Indian sources, cite only pages actually
retrieved, separate **facts / assumptions / hypotheses**, and **never invent numbers or
citations** (a validator downgrades unsupported numeric "facts" and drops uncited sources).

## Architecture

```
React SPA (Vite + Tailwind)  ──>  FastAPI
                                   ├─ Orchestrator (asyncio, 9 agents)
                                   ├─ LLMClient   (Azure AI Foundry | Anthropic)  ← LLM_PROVIDER
                                   ├─ Research     (Tavily search + httpx/trafilatura fetch)
                                   ├─ Validators   (evidence discipline)
                                   └─ SQLite       (runs, events, evidence, reports)
```

Agents: Intake → Researcher → Competitor → Segmentation → Sizing → Monetization →
India-Fit Scorer → Red-Team → Synthesizer. Progress streams to the UI over SSE.

## Setup

Run all commands from the repository root unless noted otherwise.

### Backend

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt # macOS/Linux

cp .env.example .env        # then fill in the keys below
```

Set in `.env`:
- `LLM_PROVIDER=azure` (default) or `anthropic`
- Azure: `AZURE_FOUNDRY_ENDPOINT`, `AZURE_FOUNDRY_API_KEY`, `AZURE_FOUNDRY_DEPLOYMENT`
- Anthropic (later): `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`
- `TAVILY_API_KEY` (web search)

Run the API:

```bash
.venv/Scripts/python.exe -m uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd web
npm install
npm run dev          # http://localhost:5173 (proxies /api to :8000)
```

## Tests

```bash
 .venv/Scripts/python.exe -m pytest        # 26 tests, fully mocked (no network/keys needed)
```

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/runs` | start a run — `{input_type:"text"\|"url", raw_input?, source_url?}` |
| GET  | `/api/runs/{id}/stream` | SSE live agent progress |
| GET  | `/api/runs/{id}` | run status + report (md + json) + evidence |
| GET  | `/api/runs/{id}/report.json` | machine-readable report download |
| GET  | `/api/runs` | history |
| GET  | `/healthz` | liveness + active provider |

## Switching providers

Set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY`. The report schema is identical
across providers — no other code changes.
