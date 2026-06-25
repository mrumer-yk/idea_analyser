function PriceIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0">
      <path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ChannelIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0">
      <path d="M3 11l18-5v12L3 14v-3zM11.6 16.8a3 3 0 1 1-5.8-1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export default function RevenueGTM({ models, channels }) {
  const list = models || []
  const chans = channels || []
  return (
    <div className="space-y-5">
      {!!list.length && (
        <div className="grid sm:grid-cols-2 gap-3">
          {list.map((r, i) => (
            <div key={i} className="border border-zinc-800 rounded-xl p-4 bg-zinc-900/40 flex flex-col">
              <div className="font-semibold text-zinc-100 leading-snug">{r.model}</div>
              {r.pricing_band && (
                <div className="flex items-center gap-1.5 mt-2 text-amber-300">
                  <PriceIcon />
                  <span className="text-sm font-medium">{r.pricing_band}</span>
                </div>
              )}
              {r.rationale && (
                <p className="text-xs text-zinc-400 leading-relaxed mt-2">{r.rationale}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {!!chans.length && (
        <div>
          <div className="text-xs uppercase tracking-wide text-zinc-600 mb-2">Distribution & GTM channels</div>
          <div className="grid sm:grid-cols-2 gap-2">
            {chans.map((c, i) => (
              <div key={i} className="flex items-start gap-2 border border-zinc-800 rounded-lg px-3 py-2 bg-zinc-900/30">
                <span className="text-amber-400 mt-0.5"><ChannelIcon /></span>
                <span className="text-xs text-zinc-300 leading-relaxed">{c}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
