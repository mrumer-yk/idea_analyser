# Deployment

This app is **two services**, deployed separately:

| Part | What | Where it can run |
|---|---|---|
| **Frontend** | Static React/Vite SPA (`web/`) | **Vercel** ✅ |
| **Backend** | FastAPI + long-running async pipeline + SSE + SQLite | A **persistent host** (Render / Railway / Fly) — **not** Vercel |

### Why the backend can't go on Vercel

Vercel runs serverless functions that are killed once the HTTP response returns,
are ephemeral/isolated per invocation, and have a read-only filesystem. This
backend needs the opposite:

- A run starts the 9-agent pipeline as a background `asyncio` task that keeps
  working **after** `POST /api/runs` returns — a serverless function would kill it.
- SSE progress uses **in-process** pub/sub (`runner._subscribers`); the streaming
  request and the worker must share one long-lived process.
- History is stored in **local SQLite** (`data/app.db`) — needs a writable, durable disk.

So: frontend on Vercel, backend on a container host. They talk over HTTPS + CORS.

---

## 1. Deploy the backend first (Render example)

You need the backend URL before configuring the frontend.

1. Push this repo to GitHub (the repo root contains `Dockerfile` + `render.yaml`).
2. Render → **New → Blueprint** → select the repo. It reads `render.yaml`.
3. In the service's **Environment**, fill the secrets (left `sync:false` in the blueprint):
   - `AZURE_FOUNDRY_ENDPOINT`, `AZURE_FOUNDRY_API_KEY`, `AZURE_FOUNDRY_DEPLOYMENT`
   - `TAVILY_API_KEY`
   - `CORS_ORIGINS` → your Vercel URL, e.g. `https://your-app.vercel.app`
     (you can set a placeholder now and update it after step 2 below).
4. Deploy. Verify: `https://<your-service>.onrender.com/healthz` → `{"status":"ok","provider":"azure"}`.

> **Free plan note:** Render's free tier has no persistent disk and spins down when
> idle. To use it, remove the `disk:` block from `render.yaml` and set
> `DATABASE_PATH=/tmp/app.db` — run history is lost on restart, but live runs work.
> Railway and Fly.io work too; the `Dockerfile` is host-agnostic.

## 2. Deploy the frontend (Vercel)

1. Vercel → **New Project** → import the same repo.
2. Set **Root Directory** to `web`. Vercel auto-detects Vite (`vercel.json` pins
    the build to `npm run build` → `dist` and adds the SPA fallback).
3. Add an **Environment Variable**:
   - `VITE_API_BASE` = your backend origin from step 1, e.g. `https://<your-service>.onrender.com`
     (no trailing slash; Vite inlines this at build time).
4. Deploy. Open the Vercel URL.

## 3. Close the CORS loop

Set the backend's `CORS_ORIGINS` to the final Vercel domain (e.g.
`https://your-app.vercel.app`) and redeploy the backend. If you use a custom domain,
add it as a comma-separated value.

---

## Local development (unchanged)

`VITE_API_BASE` stays empty locally, so the frontend uses relative `/api` and the
Vite dev proxy forwards to `http://localhost:8000`:

```bash
# backend
.venv/Scripts/python.exe -m uvicorn backend.main:app --reload --port 8000
# frontend
cd web && npm run dev
```
