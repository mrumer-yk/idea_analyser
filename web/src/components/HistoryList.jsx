const REC_DOT = {
  pursue: 'bg-emerald-500',
  pivot: 'bg-amber-500',
  reject: 'bg-red-500',
}

export default function HistoryList({ runs, activeId, onSelect }) {
  if (!runs.length) return <p className="text-zinc-600 text-sm">No past runs yet.</p>
  return (
    <ul className="space-y-1">
      {runs.map((r) => (
        <li key={r.id}>
          <button
            onClick={() => onSelect(r.id)}
            className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
              activeId === r.id ? 'bg-zinc-800' : 'hover:bg-zinc-900'
            }`}
          >
            <div className="flex items-start gap-2">
              {r.status === 'running' || r.status === 'queued' ? (
                <span className="w-2 h-2 mt-1.5 rounded-full bg-amber-400 animate-pulse shrink-0" />
              ) : (
                <span className={`w-2 h-2 mt-1.5 rounded-full shrink-0 ${REC_DOT[r.recommendation] || 'bg-zinc-600'}`} />
              )}
              <span className="text-zinc-300 leading-snug line-clamp-2">
                {(r.raw_input && r.raw_input.trim()) || r.source_url || `Analysis ${r.id.slice(0, 8)}`}
              </span>
            </div>
            <div className="text-xs text-zinc-600">
              {r.status} · {new Date(r.created_at).toLocaleString()}
            </div>
          </button>
        </li>
      ))}
    </ul>
  )
}
