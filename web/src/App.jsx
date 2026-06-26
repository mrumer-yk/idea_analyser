import { useEffect, useRef, useState } from 'react'
import { createRun, deleteRun, getRun, listRuns, streamRun } from './api'
import IdeaForm from './components/IdeaForm'
import ProgressPanel from './components/ProgressPanel'
import ReportView from './components/ReportView'
import HistoryList from './components/HistoryList'

const blank = () => ({ events: [], detail: null, status: 'running' })

// Assemble a partial report from streamed section fragments so the report can
// fill in section-by-section while the run is still in progress.
function buildPartial(events) {
  const r = {}
  for (const e of events) {
    if (e.phase === 'section' && e.payload && e.payload.fragment) Object.assign(r, e.payload.fragment)
    if (e.agent === 'synthesizer' && e.phase === 'finished' && e.payload) {
      if (e.payload.recommendation) r.recommendation = e.payload.recommendation
      if (e.payload.confidence) r.confidence = e.payload.confidence
    }
  }
  return r
}

export default function App() {
  // Each run is tracked independently so multiple analyses can run at once
  // without intermixing. `runId` is just which one we're currently viewing.
  const [runsMap, setRunsMap] = useState({}) // id -> {events, detail, status}
  const [runId, setRunId] = useState(null) // null = composing a new analysis
  const [runs, setRuns] = useState([]) // history (server)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [formKey, setFormKey] = useState(0)
  const streamsRef = useRef({}) // id -> EventSource (one live stream per run)

  const refreshHistory = () => listRuns().then((d) => setRuns(d.runs || [])).catch(() => {})
  useEffect(() => { refreshHistory() }, [])
  // Close every open stream when the app unmounts.
  useEffect(() => () => Object.values(streamsRef.current).forEach((es) => es.close()), [])

  const patchRun = (id, patch) =>
    setRunsMap((prev) => ({ ...prev, [id]: { ...(prev[id] || blank()), ...patch } }))

  const appendEvent = (id, ev) =>
    setRunsMap((prev) => {
      const cur = prev[id] || blank()
      return { ...prev, [id]: { ...cur, events: [...cur.events, ev] } }
    })

  // Open a live SSE stream for a run (no-op if one is already open).
  const attachStream = (id) => {
    if (streamsRef.current[id]) return
    const es = streamRun(
      id,
      (ev) => appendEvent(id, ev),
      async () => {
        delete streamsRef.current[id]
        try {
          const d = await getRun(id)
          patchRun(id, { detail: d, status: d.status })
        } catch { /* ignore */ }
        refreshHistory()
      },
    )
    streamsRef.current[id] = es
  }

  const start = async (payload) => {
    setError(null)
    setSubmitting(true)
    try {
      const { run_id } = await createRun(payload)
      const prompt = payload.input_type === 'url' ? payload.source_url : payload.raw_input
      patchRun(run_id, { ...blank(), prompt, inputType: payload.input_type })
      setRunId(run_id) // view the run we just started
      refreshHistory()
      attachStream(run_id)
    } catch (e) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const openRun = async (id) => {
    setError(null)
    setRunId(id)
    if (!runsMap[id]) {
      try {
        const d = await getRun(id)
        patchRun(id, { detail: d, status: d.status, events: d.events || [] })
        if (d.status === 'running') attachStream(id)
      } catch (e) {
        setError(e.message)
      }
    }
  }

  const removeRun = async (id) => {
    try {
      await deleteRun(id)
    } catch (e) {
      setError(e.message)
      return
    }
    // tear down any live stream + local state for this run
    if (streamsRef.current[id]) { streamsRef.current[id].close(); delete streamsRef.current[id] }
    setRunsMap((prev) => { const next = { ...prev }; delete next[id]; return next })
    if (runId === id) setRunId(null)
    refreshHistory()
  }

  // Never blocked — just returns to a fresh, empty form. Running analyses keep
  // streaming in the background and remain accessible from History.
  const newAnalysis = () => {
    setRunId(null)
    setError(null)
    setFormKey((k) => k + 1)
  }

  const current = runId ? runsMap[runId] : null
  const activeCount = Object.values(runsMap).filter((r) => r.status === 'running').length
  const promptText =
    current?.prompt || current?.detail?.run?.raw_input || current?.detail?.run?.source_url || ''
  const promptIsUrl =
    current?.inputType === 'url' || current?.detail?.run?.input_type === 'url'

  const events = current?.events || []
  const fullReport = current?.detail?.report_json
  const streaming = !!current && current.status !== 'done' && !fullReport
  const partialReport = fullReport || buildPartial(events)
  const hasReport = !!fullReport || Object.keys(partialReport).length > 0

  return (
    <div className="min-h-screen">
      <header className="border-b border-zinc-800 px-6 py-4 flex items-center justify-between gap-3">
        <h1 className="text-lg font-semibold">
          🇮🇳 India Idea Validator
          <span className="text-zinc-500 font-normal text-sm ml-2">market research & validation agents</span>
        </h1>
        <div className="flex items-center gap-3">
          {activeCount > 0 && (
            <span className="text-xs text-amber-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              {activeCount} running
            </span>
          )}
          <button
            onClick={newAnalysis}
            className="px-3 py-1.5 rounded-lg bg-amber-500 text-black text-sm font-medium"
          >
            ＋ New analysis
          </button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-6 grid lg:grid-cols-[1fr_280px] gap-6">
        <main className="space-y-5 min-w-0">
          {error && (
            <div className="text-red-400 text-sm bg-red-950/40 border border-red-900 rounded-lg p-3">{error}</div>
          )}

          {runId === null ? (
            <IdeaForm key={formKey} onSubmit={start} busy={submitting} />
          ) : (
            <>
              <div className="flex items-center justify-between">
                <h2 className="text-sm text-zinc-400">
                  Analysis <span className="font-mono text-zinc-300">{runId.slice(0, 8)}</span>
                  <span className="ml-2 text-xs text-zinc-500">{current?.status}</span>
                </h2>
              </div>
              {promptText && (
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
                  <div className="text-xs uppercase tracking-wide text-zinc-500 mb-1">
                    {promptIsUrl ? 'Submitted URL' : 'Your idea'}
                  </div>
                  {promptIsUrl ? (
                    <a href={promptText} target="_blank" rel="noreferrer" className="text-sm text-amber-400 break-all">
                      {promptText}
                    </a>
                  ) : (
                    <p className="text-sm text-zinc-200 whitespace-pre-wrap">{promptText}</p>
                  )}
                </div>
              )}
              {streaming && <ProgressPanel events={events} />}
              {hasReport && (
                <ReportView
                  report={partialReport}
                  reportMd={current?.detail?.report_md}
                  runId={runId}
                  streaming={streaming}
                />
              )}
              {!hasReport && !streaming && <ProgressPanel events={events} />}
            </>
          )}
        </main>

        <aside>
          <button
            onClick={newAnalysis}
            className="w-full mb-3 px-3 py-2 rounded-lg border border-amber-500/60 text-amber-400 text-sm font-medium hover:bg-amber-500/10"
          >
            ＋ New analysis
          </button>
          <h2 className="text-sm font-semibold text-zinc-400 mb-2">History</h2>
          <HistoryList runs={runs} activeId={runId} onSelect={openRun} onDelete={removeRun} />
        </aside>
      </div>
    </div>
  )
}
