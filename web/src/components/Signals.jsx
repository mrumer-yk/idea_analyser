import { useMemo, useState } from 'react'
import { hostOf } from '../lib/amount'

const STYLE = {
  fact: { label: 'Fact', border: 'border-l-emerald-500', text: 'text-emerald-400', chip: 'bg-emerald-500/15 text-emerald-300' },
  assumption: { label: 'Assumption', border: 'border-l-amber-500', text: 'text-amber-400', chip: 'bg-amber-500/15 text-amber-300' },
  hypothesis: { label: 'Hypothesis', border: 'border-l-sky-500', text: 'text-sky-400', chip: 'bg-sky-500/15 text-sky-300' },
}
const ORDER = ['fact', 'assumption', 'hypothesis']

function LinkIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M7 17L17 7M17 7H8M17 7v9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function VerifyBadge({ v }) {
  if (v === 'verified')
    return <span title="Corroborated by an independent source" className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300">✓ verified</span>
  if (v === 'conflicting')
    return <span title="Sources disagree" className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300">⚠ conflicting</span>
  if (v === 'unverified')
    return <span title="Only one source; not independently corroborated" className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-600/20 text-zinc-400">unverified</span>
  return null
}

export default function Signals({ signals }) {
  const list = signals || []
  const [filter, setFilter] = useState('all')

  const counts = useMemo(() => {
    const c = { all: list.length, fact: 0, assumption: 0, hypothesis: 0 }
    list.forEach((s) => { if (c[s.classification] != null) c[s.classification]++ })
    return c
  }, [list])

  const rows = filter === 'all' ? list : list.filter((s) => s.classification === filter)

  return (
    <div>
      <div className="flex items-center gap-1.5 mb-3 flex-wrap">
        <button
          onClick={() => setFilter('all')}
          className={`text-xs px-2.5 py-1 rounded-md ${filter === 'all' ? 'bg-amber-500 text-black' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'}`}
        >
          All <span className="opacity-70">{counts.all}</span>
        </button>
        {ORDER.map((k) => (
          <button
            key={k}
            onClick={() => setFilter(k)}
            className={`text-xs px-2.5 py-1 rounded-md ${filter === k ? STYLE[k].chip : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'}`}
          >
            {STYLE[k].label}s <span className="opacity-70">{counts[k]}</span>
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {rows.map((s, i) => {
          const st = STYLE[s.classification] || STYLE.hypothesis
          return (
            <div key={i} className={`border-l-2 ${st.border} bg-zinc-900/40 rounded-r-md pl-3 pr-3 py-2`}>
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm text-zinc-200 leading-relaxed">{s.claim}</p>
                <div className="flex items-center gap-1.5 shrink-0">
                  <VerifyBadge v={s.verification} />
                  <span className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded ${st.chip}`}>
                    {st.label}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-3 mt-1 flex-wrap">
                {s.source_url && (
                  <a href={s.source_url} target="_blank" rel="noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-amber-400">
                    <LinkIcon /> {hostOf(s.source_url) || 'source'}
                  </a>
                )}
                {s.corroborating_url && (
                  <a href={s.corroborating_url} target="_blank" rel="noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-emerald-500/70 hover:text-emerald-400">
                    <LinkIcon /> {hostOf(s.corroborating_url) || '2nd source'}
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
