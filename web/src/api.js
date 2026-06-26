// Thin client over the backend API.
//
// In dev, VITE_API_BASE is unset, so requests go to relative `/api/...` and the
// Vite proxy (vite.config.js) forwards them to the local FastAPI server.
// In production (e.g. frontend on Vercel), set VITE_API_BASE at build time to
// the deployed backend origin, e.g. https://idea-validator-api.onrender.com
const DEFAULT_PROD_API_BASE = 'https://idea-analyser.onrender.com'
const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname)
const API_BASE = (
  import.meta.env.VITE_API_BASE ||
  (isLocalHost ? '' : DEFAULT_PROD_API_BASE)
).replace(/\/$/, '')

export async function createRun(payload) {
  const res = await fetch(`${API_BASE}/api/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error((await res.json()).detail || 'failed to start run')
  return res.json()
}

export async function getRun(runId) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}`)
  if (!res.ok) throw new Error('run not found')
  return res.json()
}

export async function listRuns() {
  const res = await fetch(`${API_BASE}/api/runs`)
  return res.json()
}

export async function deleteRun(runId) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('failed to delete run')
  return res.json()
}

// Subscribe to the SSE progress stream. Returns the EventSource so the caller
// can close it. onEvent(event) fires per agent event; onEnd() when finished.
export function streamRun(runId, onEvent, onEnd) {
  const es = new EventSource(`${API_BASE}/api/runs/${runId}/stream`)
  es.onmessage = (e) => {
    const data = JSON.parse(e.data)
    if (data.phase === '__end__') {
      es.close()
      onEnd && onEnd()
      return
    }
    onEvent(data)
  }
  es.onerror = () => {
    es.close()
    onEnd && onEnd()
  }
  return es
}
