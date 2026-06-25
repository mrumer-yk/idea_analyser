// Thin client over the backend API.

export async function createRun(payload) {
  const res = await fetch('/api/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error((await res.json()).detail || 'failed to start run')
  return res.json()
}

export async function getRun(runId) {
  const res = await fetch(`/api/runs/${runId}`)
  if (!res.ok) throw new Error('run not found')
  return res.json()
}

export async function listRuns() {
  const res = await fetch('/api/runs')
  return res.json()
}

// Subscribe to the SSE progress stream. Returns the EventSource so the caller
// can close it. onEvent(event) fires per agent event; onEnd() when finished.
export function streamRun(runId, onEvent, onEnd) {
  const es = new EventSource(`/api/runs/${runId}/stream`)
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
