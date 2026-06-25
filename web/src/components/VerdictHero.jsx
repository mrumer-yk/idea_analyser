const REC = {
  pursue: { label: 'PURSUE', dot: 'bg-emerald-500', ring: '#34d399', text: 'text-emerald-400' },
  pivot: { label: 'PIVOT', dot: 'bg-amber-500', ring: '#fbbf24', text: 'text-amber-400' },
  reject: { label: 'REJECT', dot: 'bg-red-500', ring: '#f87171', text: 'text-red-400' },
}

function ScoreRing({ score, color }) {
  const pct = Math.max(Math.min((Number(score) || 0) / 10, 1), 0)
  const r = 26
  const c = 2 * Math.PI * r
  return (
    <svg width="64" height="64" viewBox="0 0 64 64" className="shrink-0">
      <circle cx="32" cy="32" r={r} fill="none" stroke="#27272a" strokeWidth="6" />
      <circle
        cx="32" cy="32" r={r} fill="none" stroke={color} strokeWidth="6" strokeLinecap="round"
        strokeDasharray={c} strokeDashoffset={c * (1 - pct)} transform="rotate(-90 32 32)"
      />
      <text x="32" y="34" textAnchor="middle" className="fill-zinc-100" fontSize="15" fontWeight="600">
        {score != null ? score : '–'}
      </text>
      <text x="32" y="46" textAnchor="middle" className="fill-zinc-500" fontSize="8">/ 10</text>
    </svg>
  )
}

export default function VerdictHero({ report, streaming }) {
  const fit = report.india_market_fit || {}
  const rec = REC[report.recommendation]
  const why = (fit.rationale || report.problem_and_pain || '').split(/(?<=\.)\s/)[0]

  return (
    <div className="bg-gradient-to-br from-zinc-900 to-zinc-900/40 border border-zinc-800 rounded-xl p-5 flex items-center gap-5">
      <ScoreRing score={fit.score} color={rec?.ring || '#fbbf24'} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-3 flex-wrap">
          {rec ? (
            <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-md font-bold text-sm bg-zinc-800 ${rec.text}`}>
              <span className={`w-2.5 h-2.5 rounded-full ${rec.dot}`} />
              {rec.label}
            </span>
          ) : (
            <span className="px-3 py-1 rounded-md text-sm bg-zinc-800 text-zinc-400">
              {streaming ? 'Analyzing…' : 'Pending'}
            </span>
          )}
          {report.confidence && (
            <span className="text-xs text-zinc-400">confidence: {report.confidence}</span>
          )}
        </div>
        {why && <p className="text-sm text-zinc-300 mt-2 line-clamp-2">{why}</p>}
      </div>
    </div>
  )
}
