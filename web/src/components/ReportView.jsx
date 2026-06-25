import { useEffect, useMemo, useState } from 'react'
import VerdictHero from './VerdictHero'
import CompetitorTable from './CompetitorTable'
import MarketSize from './MarketSize'
import Signals from './Signals'
import Sources from './Sources'
import Segments from './Segments'
import RevenueGTM from './RevenueGTM'
import FitBars from './charts/FitBars'
import RiskHeatmap from './charts/RiskHeatmap'

function download(filename, text, type) {
  const blob = new Blob([text], { type })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

function Section({ id, title, children, empty, streaming }) {
  return (
    <section id={id} className="scroll-mt-24">
      <h3 className="text-sm uppercase tracking-wide text-zinc-500 mb-2">{title}</h3>
      {empty ? (
        <p className="text-zinc-600 text-sm italic">{streaming ? 'Awaiting analysis…' : 'No data.'}</p>
      ) : (
        children
      )}
    </section>
  )
}

export default function ReportView({ report, reportMd, runId, streaming }) {
  if (!report) return null
  const fit = report.india_market_fit || {}
  const ms = report.market_size || {}
  const sized = ms.tam || ms.sam || ms.som

  // Build nav only for sections that exist (or always, while streaming).
  const nav = useMemo(() => {
    const items = [
      ['overview', 'Overview', true],
      ['segments', 'Segments', (report.target_segments || []).length || streaming],
      ['competitors', 'Competitors', (report.competitors || []).length || streaming],
      ['market', 'Market', (report.market_signals || []).length || sized || streaming],
      ['money', 'Revenue', (report.revenue_models || []).length || streaming],
      ['risks', 'Risks', (report.risks || []).length || streaming],
      ['sources', 'Sources', (report.sources || []).length],
    ]
    return items.filter(([, , show]) => show).map(([id, label]) => ({ id, label }))
  }, [report, streaming, sized])

  const [active, setActive] = useState('overview')
  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: '-15% 0px -75% 0px' },
    )
    nav.forEach((n) => { const el = document.getElementById(n.id); if (el) obs.observe(el) })
    return () => obs.disconnect()
  }, [nav.length])

  const go = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })

  return (
    <div className="min-w-0 break-words space-y-4">
      <VerdictHero report={report} streaming={streaming} />

      {/* sticky section nav */}
      <div className="sticky top-0 z-10 -mx-1 px-1 py-2 bg-[#0c0c0d]/90 backdrop-blur border-b border-zinc-800 flex items-center justify-between gap-2">
        <nav className="flex gap-1 overflow-x-auto">
          {nav.map((n) => (
            <button
              key={n.id}
              onClick={() => go(n.id)}
              className={`px-2.5 py-1 rounded-md text-xs whitespace-nowrap ${
                active === n.id ? 'bg-amber-500 text-black' : 'text-zinc-400 hover:bg-zinc-800'
              }`}
            >
              {n.label}
            </button>
          ))}
        </nav>
        <div className="flex gap-1.5 shrink-0">
          <button
            onClick={() => download(`report-${runId}.json`, JSON.stringify(report, null, 2), 'application/json')}
            className="px-2.5 py-1 text-xs rounded-md bg-zinc-800 text-zinc-200"
          >
            JSON
          </button>
          {reportMd && (
            <button
              onClick={() => download(`report-${runId}.md`, reportMd, 'text/markdown')}
              className="px-2.5 py-1 text-xs rounded-md bg-zinc-800 text-zinc-200"
            >
              MD
            </button>
          )}
        </div>
      </div>

      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-6 space-y-6">
        <Section id="overview" title="Overview" streaming={streaming} empty={!report.idea_summary && !report.problem_and_pain}>
          {report.idea_summary && <p className="text-zinc-200 mb-3">{report.idea_summary}</p>}
          {report.problem_and_pain && (
            <>
              <div className="text-xs uppercase tracking-wide text-zinc-600 mb-1">Problem & pain</div>
              <p className="text-zinc-300 mb-4">{report.problem_and_pain}</p>
            </>
          )}
          {!!(fit.factors || []).length && (
            <>
              <div className="text-xs uppercase tracking-wide text-zinc-600 mb-2">India-fit factors</div>
              <FitBars factors={fit.factors} />
            </>
          )}
        </Section>

        <Section id="segments" title="Target Segments" streaming={streaming} empty={!(report.target_segments || []).length}>
          <Segments segments={report.target_segments} />
        </Section>

        <Section id="competitors" title="Competitor Landscape" streaming={streaming} empty={!(report.competitors || []).length}>
          <CompetitorTable competitors={report.competitors} />
        </Section>

        <Section id="market" title="Market Size & Signals" streaming={streaming} empty={!(report.market_signals || []).length && !sized}>
          <div className="text-xs uppercase tracking-wide text-zinc-600 mb-2">Market size (TAM / SAM / SOM)</div>
          <MarketSize marketSize={ms} sized={sized} />
          {!!(report.market_signals || []).length && (
            <>
              <div className="text-xs uppercase tracking-wide text-zinc-600 mt-5 mb-2">Signals & evidence</div>
              <Signals signals={report.market_signals} />
            </>
          )}
        </Section>

        <Section id="money" title="Revenue & GTM" streaming={streaming} empty={!(report.revenue_models || []).length && !(report.gtm_channels || []).length}>
          <RevenueGTM models={report.revenue_models} channels={report.gtm_channels} />
        </Section>

        <Section id="risks" title="Risks, Blockers & Compliance" streaming={streaming} empty={!(report.risks || []).length}>
          <RiskHeatmap risks={report.risks} />
        </Section>

        <Section id="sources" title="Sources" streaming={false} empty={!(report.sources || []).length}>
          <Sources sources={report.sources} />
        </Section>
      </div>
    </div>
  )
}
