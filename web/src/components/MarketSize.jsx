import { useState } from 'react'
import { parseAmount } from '../lib/amount'

const CARDS = [
  ['TAM', 'tam', 'Total addressable', 'from-amber-500/20', 'bg-amber-500'],
  ['SAM', 'sam', 'Serviceable', 'from-amber-400/20', 'bg-amber-400'],
  ['SOM', 'som', 'Obtainable', 'from-emerald-400/20', 'bg-emerald-400'],
]

export default function MarketSize({ marketSize, sized }) {
  const ms = marketSize || {}
  const [open, setOpen] = useState(false)
  const tamVal = parseAmount(ms.tam)

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {CARDS.map(([label, key, sub, grad, bar]) => {
          const raw = ms[key]
          const val = parseAmount(raw)
          const pct = val != null && tamVal ? Math.min((val / tamVal) * 100, 100) : null
          return (
            <div key={key} className={`rounded-lg border border-zinc-800 bg-gradient-to-br ${grad} to-transparent p-3`}>
              <div className="flex items-baseline justify-between">
                <span className="text-xs font-semibold text-zinc-400">{label}</span>
                <span className="text-[10px] text-zinc-500">{sub}</span>
              </div>
              <div className="text-lg font-semibold text-zinc-100 mt-1 break-words">{raw || 'n/a'}</div>
              <div className="mt-2 h-1.5 bg-zinc-800/80 rounded overflow-hidden">
                {pct != null && <div className={`${bar} h-full rounded`} style={{ width: `${Math.max(pct, 3)}%` }} />}
              </div>
              {pct != null && key !== 'tam' && (
                <div className="text-[10px] text-zinc-500 mt-1">{pct.toFixed(1)}% of TAM</div>
              )}
            </div>
          )
        })}
      </div>

      <div className="text-xs text-zinc-500 mt-2">
        {sized
          ? 'Estimate — built on a cited anchor figure + the stated assumptions.'
          : 'Not sized — no credible market-size anchor found in the evidence.'}
      </div>

      {!!(ms.assumptions || []).length && (
        <div className="mt-2">
          <button
            onClick={() => setOpen((o) => !o)}
            className="text-xs text-amber-400 hover:text-amber-300 inline-flex items-center gap-1"
          >
            <span className={`transition-transform ${open ? 'rotate-90' : ''}`}>▸</span>
            Methodology & assumptions ({ms.assumptions.length})
          </button>
          {open && (
            <ol className="mt-2 space-y-1.5 border-l-2 border-zinc-800 pl-3">
              {ms.assumptions.map((a, i) => (
                <li key={i} className="text-xs text-zinc-400 leading-relaxed break-words">{a}</li>
              ))}
            </ol>
          )}
        </div>
      )}
    </div>
  )
}
