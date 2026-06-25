import { useMemo, useState } from 'react'
import { hostOf } from '../lib/amount'

const TYPE_STYLE = {
  pricing: 'bg-amber-500/15 text-amber-300',
  gov: 'bg-emerald-500/15 text-emerald-300',
  appstore: 'bg-violet-500/15 text-violet-300',
  forum: 'bg-sky-500/15 text-sky-300',
  news: 'bg-rose-500/15 text-rose-300',
  research: 'bg-teal-500/15 text-teal-300',
  social: 'bg-blue-500/15 text-blue-300',
  blog: 'bg-zinc-500/20 text-zinc-300',
}

function Favicon({ url, name }) {
  const host = hostOf(url)
  const [err, setErr] = useState(false)
  if (host && !err) {
    return (
      <img src={`https://www.google.com/s2/favicons?domain=${host}&sz=64`} alt="" width={18} height={18}
        className="rounded shrink-0 mt-0.5" onError={() => setErr(true)} />
    )
  }
  return (
    <span className="w-[18px] h-[18px] mt-0.5 rounded bg-zinc-700 text-zinc-200 text-[10px] flex items-center justify-center shrink-0">
      {(name || '?').trim().charAt(0).toUpperCase()}
    </span>
  )
}

export default function Sources({ sources }) {
  const list = sources || []
  const [q, setQ] = useState('')
  const [type, setType] = useState('all')

  const types = useMemo(() => {
    const m = {}
    list.forEach((s) => { const t = s.source_type || 'other'; m[t] = (m[t] || 0) + 1 })
    return m
  }, [list])

  const typeKeys = Object.keys(types).filter((t) => t !== 'other').sort((a, b) => types[b] - types[a])

  const rows = list.filter((s) => {
    if (type !== 'all' && (s.source_type || 'other') !== type) return false
    if (q) {
      const hay = `${s.title || ''} ${hostOf(s.url)}`.toLowerCase()
      if (!hay.includes(q.toLowerCase())) return false
    }
    return true
  })

  return (
    <div>
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={`Search ${list.length} sources…`}
          className="bg-zinc-950 border border-zinc-800 rounded-md px-2.5 py-1 text-xs outline-none focus:border-amber-500 w-48"
        />
        <button
          onClick={() => setType('all')}
          className={`text-xs px-2.5 py-1 rounded-md ${type === 'all' ? 'bg-amber-500 text-black' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'}`}
        >
          All <span className="opacity-70">{list.length}</span>
        </button>
        {typeKeys.map((t) => (
          <button
            key={t}
            onClick={() => setType(t)}
            className={`text-xs px-2.5 py-1 rounded-md capitalize ${type === t ? (TYPE_STYLE[t] || 'bg-zinc-700 text-zinc-100') : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'}`}
          >
            {t} <span className="opacity-70">{types[t]}</span>
          </button>
        ))}
      </div>

      <div className="grid sm:grid-cols-2 gap-2">
        {rows.map((s, i) => {
          const t = s.source_type || 'other'
          return (
            <a
              key={i}
              href={s.url}
              target="_blank"
              rel="noreferrer"
              className="group flex items-start gap-2.5 border border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800/30 rounded-lg p-2.5"
            >
              <Favicon url={s.url} name={s.title} />
              <div className="min-w-0 flex-1">
                <div className="text-sm text-zinc-200 group-hover:text-amber-400 leading-snug line-clamp-2">
                  {s.title || hostOf(s.url) || s.url}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[11px] text-zinc-500 truncate">{hostOf(s.url)}</span>
                  {t !== 'other' && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded capitalize ${TYPE_STYLE[t] || 'bg-zinc-700 text-zinc-200'}`}>{t}</span>
                  )}
                </div>
              </div>
            </a>
          )
        })}
      </div>
      {!rows.length && <p className="text-zinc-600 text-sm">No sources match.</p>}
    </div>
  )
}
