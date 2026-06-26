export default function Pivots({ pivots }) {
  const list = pivots || []
  if (!list.length) return null
  return (
    <div className="space-y-3">
      <p className="text-xs text-zinc-500">If the straight path is hard to win, these are sharper directions to consider.</p>
      {list.map((p, i) => (
        <div key={i} className="border border-zinc-800 rounded-xl p-4 bg-zinc-900/40">
          <div className="flex items-start gap-3">
            <span className="w-7 h-7 rounded-lg bg-violet-500/15 text-violet-300 font-semibold flex items-center justify-center shrink-0 text-sm">
              {i + 1}
            </span>
            <div className="min-w-0">
              <div className="font-semibold text-zinc-100 leading-snug">{p.direction}</div>
              {p.rationale && (
                <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">
                  <span className="text-zinc-500">Why: </span>{p.rationale}
                </p>
              )}
              {p.why_better && (
                <p className="text-xs text-emerald-300/80 mt-1.5 leading-relaxed">
                  <span className="text-zinc-500">More winnable: </span>{p.why_better}
                </p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
