// Normalize a field that may arrive as an array or a "; "-joined string.
function toList(v) {
  if (Array.isArray(v)) return v.filter(Boolean)
  if (typeof v === 'string' && v.trim()) return v.split(/;\s*/).filter(Boolean)
  return []
}

function BulletList({ items, dot }) {
  if (!items.length) return null
  return (
    <ul className="space-y-1">
      {items.map((it, i) => (
        <li key={i} className="flex gap-2 text-xs text-zinc-300 leading-relaxed">
          <span className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${dot}`} />
          <span>{it}</span>
        </li>
      ))}
    </ul>
  )
}

export default function Segments({ segments }) {
  const list = segments || []
  return (
    <div className="grid sm:grid-cols-2 gap-3">
      {list.map((s, i) => {
        const pains = toList(s.pains)
        const jtbd = toList(s.jtbd)
        return (
          <div key={i} className="border border-zinc-800 rounded-xl p-4 bg-zinc-900/40 flex flex-col">
            <div className="flex items-start gap-3 mb-3">
              <span className="w-8 h-8 rounded-lg bg-amber-500/15 text-amber-300 font-semibold flex items-center justify-center shrink-0">
                {i + 1}
              </span>
              <div className="min-w-0">
                <div className="font-semibold text-zinc-100 leading-snug">{s.segment}</div>
                {s.persona && <div className="text-xs text-zinc-500 mt-0.5">{s.persona}</div>}
              </div>
            </div>

            {!!pains.length && (
              <div className="mb-3">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <span className="w-2 h-2 rounded-full bg-red-400" />
                  <span className="text-[11px] uppercase tracking-wide text-zinc-500 font-medium">Pains</span>
                </div>
                <BulletList items={pains} dot="bg-red-400/70" />
              </div>
            )}

            {!!jtbd.length && (
              <div>
                <div className="flex items-center gap-1.5 mb-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="text-[11px] uppercase tracking-wide text-zinc-500 font-medium">Jobs to be done</span>
                </div>
                <BulletList items={jtbd} dot="bg-emerald-400/70" />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
