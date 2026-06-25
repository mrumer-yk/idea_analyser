const PHASE_COLOR = {
  started: 'text-amber-400',
  finished: 'text-emerald-400',
  info: 'text-zinc-400',
  error: 'text-red-400',
  done: 'text-emerald-400',
}

export default function ProgressPanel({ events }) {
  events = (events || []).filter((e) => e.phase !== 'section') // hide data-only events
  if (!events.length) return null
  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-zinc-300 mb-2">Agent progress</h3>
      <ul className="space-y-1 font-mono text-xs max-h-72 overflow-auto">
        {events.map((e, i) => (
          <li key={i} className="flex gap-2">
            <span className={`${PHASE_COLOR[e.phase] || 'text-zinc-400'} w-20 shrink-0`}>
              {e.agent}
            </span>
            <span className="text-zinc-500 w-14 shrink-0">{e.phase}</span>
            <span className="text-zinc-300">{e.message}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
