// Group risks by severity (high -> low), color-coded with counts.
const SEV = [
  ['high', 'High', 'border-red-500/50 bg-red-950/30', 'text-red-400'],
  ['med', 'Medium', 'border-amber-500/40 bg-amber-950/20', 'text-amber-400'],
  ['low', 'Low', 'border-emerald-500/40 bg-emerald-950/20', 'text-emerald-400'],
]

// tolerate synonyms the way the backend schema does
const norm = (s) => {
  const k = String(s || '').toLowerCase()
  if (['high', 'critical', 'severe', 'major'].includes(k)) return 'high'
  if (['low', 'minor'].includes(k)) return 'low'
  return 'med'
}

export default function RiskHeatmap({ risks }) {
  if (!risks || !risks.length) return <p className="text-zinc-600 text-sm">No risks listed.</p>
  const bySev = { high: [], med: [], low: [] }
  risks.forEach((r) => bySev[norm(r.severity)].push(r))

  return (
    <div className="space-y-3">
      <div className="flex gap-2 text-xs">
        {SEV.map(([key, label, , textColor]) => (
          <span key={key} className={`${textColor}`}>
            {label}: {bySev[key].length}
          </span>
        ))}
      </div>
      {SEV.map(([key, label, box]) =>
        bySev[key].length ? (
          <div key={key}>
            {bySev[key].map((r, i) => (
              <div key={i} className={`border ${box} rounded-lg p-2.5 mb-1.5`}>
                <div className="text-sm text-zinc-100">{r.risk}</div>
                <div className="text-xs text-zinc-500 mt-0.5">{r.type} · {label.toLowerCase()}</div>
              </div>
            ))}
          </div>
        ) : null,
      )}
    </div>
  )
}
