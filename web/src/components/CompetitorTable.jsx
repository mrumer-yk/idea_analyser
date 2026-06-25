import { useMemo, useState } from 'react'

function hostOf(url) {
  try { return new URL(url).hostname.replace(/^www\./, '') } catch { return '' }
}

function Favicon({ url, name }) {
  const host = hostOf(url)
  const [err, setErr] = useState(false)
  if (host && !err) {
    return (
      <img
        src={`https://www.google.com/s2/favicons?domain=${host}&sz=64`}
        alt=""
        width={20}
        height={20}
        className="rounded shrink-0"
        onError={() => setErr(true)}
      />
    )
  }
  // fallback: initial avatar
  return (
    <span className="w-5 h-5 rounded bg-zinc-700 text-zinc-200 text-[10px] flex items-center justify-center shrink-0">
      {(name || '?').trim().charAt(0).toUpperCase()}
    </span>
  )
}

function TypeBadge({ type }) {
  const direct = type === 'direct'
  return (
    <span
      className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded font-medium ${
        direct ? 'bg-red-500/15 text-red-300' : 'bg-sky-500/15 text-sky-300'
      }`}
    >
      {type || 'direct'}
    </span>
  )
}

const FILTERS = [
  ['all', 'All'],
  ['direct', 'Direct'],
  ['indirect', 'Indirect'],
]

export default function CompetitorTable({ competitors }) {
  const list = competitors || []
  const [filter, setFilter] = useState('all')

  const counts = useMemo(() => ({
    all: list.length,
    direct: list.filter((c) => c.type === 'direct').length,
    indirect: list.filter((c) => c.type === 'indirect').length,
  }), [list])

  const rows = filter === 'all' ? list : list.filter((c) => c.type === filter)

  return (
    <div>
      <div className="flex items-center gap-1.5 mb-3">
        {FILTERS.map(([key, label]) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`text-xs px-2.5 py-1 rounded-md ${
              filter === key ? 'bg-amber-500 text-black' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {label} <span className="opacity-70">{counts[key]}</span>
          </button>
        ))}
      </div>

      <div className="rounded-lg border border-zinc-800 overflow-hidden">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-zinc-900 text-zinc-500 text-left text-xs uppercase tracking-wide">
              <th className="py-2.5 px-3 font-medium">Company</th>
              <th className="py-2.5 px-3 font-medium w-20">Type</th>
              <th className="py-2.5 px-3 font-medium">Positioning</th>
              <th className="py-2.5 px-3 font-medium w-40">Pricing</th>
              <th className="py-2.5 px-3 font-medium w-12"></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c, i) => (
              <tr key={i} className="border-t border-zinc-800/70 odd:bg-zinc-900/30 hover:bg-zinc-800/40 align-top">
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <Favicon url={c.url} name={c.name} />
                    <span className="text-zinc-100 font-medium">{c.name}</span>
                  </div>
                </td>
                <td className="py-3 px-3"><TypeBadge type={c.type} /></td>
                <td className="py-3 px-3 text-zinc-300 leading-relaxed">{c.positioning}</td>
                <td className="py-3 px-3 text-zinc-300">
                  {c.pricing ? c.pricing : <span className="text-zinc-600">—</span>}
                </td>
                <td className="py-3 px-3">
                  {c.url ? (
                    <a
                      href={c.url}
                      target="_blank"
                      rel="noreferrer"
                      title={hostOf(c.url)}
                      className="text-zinc-500 hover:text-amber-400 inline-flex"
                    >
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M7 17L17 7M17 7H8M17 7v9" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </a>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
