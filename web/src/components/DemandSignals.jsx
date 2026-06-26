import { useMemo, useState } from 'react'
import { hostOf } from '../lib/amount'

const STYLE = {
  pain: { label: 'Pain', border: 'border-l-red-500', chip: 'bg-red-500/15 text-red-300' },
  desire: { label: 'Desire', border: 'border-l-emerald-500', chip: 'bg-emerald-500/15 text-emerald-300' },
  objection: { label: 'Objection', border: 'border-l-amber-500', chip: 'bg-amber-500/15 text-amber-300' },
  neutral: { label: 'Neutral', border: 'border-l-zinc-600', chip: 'bg-zinc-600/20 text-zinc-300' },
}
const ORDER = ['pain', 'desire', 'objection', 'neutral']

export default function DemandSignals({ signals }) {
  const list = signals || []
  const [filter, setFilter] = useState('all')

  const counts = useMemo(() => {
    const c = { all: list.length, pain: 0, desire: 0, objection: 0, neutral: 0 }
    list.forEach((s) => { if (c[s.sentiment] != null) c[s.sentiment]++ })
    return c
  }, [list])

  const present = ORDER.filter((k) => counts[k] > 0)
  const rows = filter === 'all' ? list : list.filter((s) => s.sentiment === filter)

  return (
    <div>
      <p className="text-xs text-zinc-500 mb-3">Real pain points & demand from Indian community discussions (Reddit, Quora, forums).</p>
      {present.length > 1 && (
        <div className="flex items-center gap-1.5 mb-3 flex-wrap">
          <button
            onClick={() => setFilter('all')}
            className={`text-xs px-2.5 py-1 rounded-md ${filter === 'all' ? 'bg-amber-500 text-black' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'}`}
          >
            All <span className="opacity-70">{counts.all}</span>
          </button>
          {present.map((k) => (
            <button
              key={k}
              onClick={() => setFilter(k)}
              className={`text-xs px-2.5 py-1 rounded-md ${filter === k ? STYLE[k].chip : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'}`}
            >
              {STYLE[k].label} <span className="opacity-70">{counts[k]}</span>
            </button>
          ))}
        </div>
      )}

      <div className="space-y-2">
        {rows.map((s, i) => {
          const st = STYLE[s.sentiment] || STYLE.pain
          return (
            <div key={i} className={`border-l-2 ${st.border} bg-zinc-900/40 rounded-r-md pl-3 pr-3 py-2`}>
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm text-zinc-200 leading-relaxed">{s.observation}</p>
                <span className={`shrink-0 text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded ${st.chip}`}>{st.label}</span>
              </div>
              <div className="flex items-center gap-3 mt-1">
                {s.theme && <span className="text-[11px] text-zinc-500">#{s.theme}</span>}
                {s.source_url && (
                  <a href={s.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-amber-400">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M7 17L17 7M17 7H8M17 7v9" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    {hostOf(s.source_url) || 'source'}
                  </a>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
