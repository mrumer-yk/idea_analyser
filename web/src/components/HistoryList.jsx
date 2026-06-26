import { useState } from 'react'

const REC_DOT = {
  pursue: 'bg-emerald-500',
  pivot: 'bg-amber-500',
  reject: 'bg-red-500',
}

function TrashIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V6"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export default function HistoryList({ runs, activeId, onSelect, onDelete }) {
  const [confirmId, setConfirmId] = useState(null)
  if (!runs.length) return <p className="text-zinc-600 text-sm">No past runs yet.</p>

  return (
    <ul className="space-y-1">
      {runs.map((r) => {
        const title = (r.raw_input && r.raw_input.trim()) || r.source_url || `Analysis ${r.id.slice(0, 8)}`
        const confirming = confirmId === r.id
        return (
          <li key={r.id} className="group relative">
            <button
              onClick={() => onSelect(r.id)}
              className={`w-full text-left px-3 py-2 pr-9 rounded-lg text-sm ${
                activeId === r.id ? 'bg-zinc-800' : 'hover:bg-zinc-900'
              }`}
            >
              <div className="flex items-start gap-2">
                {r.status === 'running' || r.status === 'queued' ? (
                  <span className="w-2 h-2 mt-1.5 rounded-full bg-amber-400 animate-pulse shrink-0" />
                ) : (
                  <span className={`w-2 h-2 mt-1.5 rounded-full shrink-0 ${REC_DOT[r.recommendation] || 'bg-zinc-600'}`} />
                )}
                <span className="text-zinc-300 leading-snug line-clamp-2">{title}</span>
              </div>
              <div className="text-xs text-zinc-600">
                {r.status} · {new Date(r.created_at).toLocaleString()}
              </div>
            </button>

            {/* delete control */}
            {confirming ? (
              <div className="absolute inset-0 flex items-center justify-between gap-2 pl-3 pr-2 rounded-lg bg-zinc-900/95 backdrop-blur-sm border border-red-500/30 ring-1 ring-red-500/10">
                <span className="flex items-center gap-1.5 text-xs text-zinc-300 min-w-0">
                  <span className="text-red-400 shrink-0"><TrashIcon /></span>
                  <span className="truncate">Delete this analysis?</span>
                </span>
                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    onClick={(e) => { e.stopPropagation(); setConfirmId(null) }}
                    className="text-xs px-2 py-1 rounded-md text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
                  >Cancel</button>
                  <button
                    onClick={(e) => { e.stopPropagation(); setConfirmId(null); onDelete(r.id) }}
                    className="text-xs px-2 py-1 rounded-md bg-red-500/90 text-white font-medium hover:bg-red-500"
                  >Delete</button>
                </div>
              </div>
            ) : (
              <button
                onClick={(e) => { e.stopPropagation(); setConfirmId(r.id) }}
                className="absolute top-2 right-2 p-1 rounded-md text-zinc-600 hover:text-red-400 hover:bg-zinc-800 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
                aria-label="Delete analysis"
              >
                <TrashIcon />
              </button>
            )}
          </li>
        )
      })}
    </ul>
  )
}
