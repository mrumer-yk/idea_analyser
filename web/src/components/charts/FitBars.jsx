// Horizontal bars for each weighted India-fit factor (score 0-10).
function barColor(score) {
  if (score >= 7) return 'bg-emerald-400'
  if (score >= 4) return 'bg-amber-400'
  return 'bg-red-400'
}

export default function FitBars({ factors }) {
  if (!factors || !factors.length) return null
  return (
    <div className="space-y-2">
      {factors.map((f, i) => {
        const score = Number(f.score) || 0
        const pct = Math.max(Math.min(score / 10, 1) * 100, 2)
        return (
          <div key={i} className="flex items-center gap-3">
            <span className="w-28 shrink-0 text-xs text-zinc-400 capitalize">
              {String(f.name || '').replace(/_/g, ' ')}
            </span>
            <div className="flex-1 bg-zinc-800/60 rounded h-5 overflow-hidden">
              <div className={`${barColor(score)} h-full rounded`} style={{ width: `${pct}%` }} />
            </div>
            <span className="w-16 shrink-0 text-xs text-zinc-300 text-right">
              {score}/10 {f.weight ? <span className="text-zinc-600">·w{f.weight}</span> : null}
            </span>
          </div>
        )
      })}
    </div>
  )
}
