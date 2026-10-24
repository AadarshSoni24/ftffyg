// frontend/src/components/Metrics.jsx
import { mw, isoShort } from '../lib/format.js'

function Kpi({ name, value, helper, accent }) {
  return (
    <div className="flex flex-col gap-1.5 border-[#E4DFD2] px-5 py-4 max-sm:[&:not(:first-child)]:border-t sm:max-lg:[&:nth-child(2n)]:border-l sm:max-lg:[&:nth-child(n+3)]:border-t lg:[&:not(:first-child)]:border-l">
      <p className="font-mono text-[11px] uppercase tracking-[0.1em] text-[#5C6A68]">{name}</p>
      <p className={`display num text-[40px] font-light leading-none ${accent || 'text-[#15262B]'}`}>
        {value}<span className="ml-1 text-[14px] font-normal text-[#5C6A68]">MW</span>
      </p>
      <p className="text-[12px] leading-snug text-[#5C6A68]">{helper}</p>
    </div>
  )
}

export default function Metrics({ view, params, scopeLabel }) {
  const s = view.stats
  const c = view.coverage || { matched: 0, total: 0 }
  if (!s) return null

  const isOverforecast = s.bias > 0
  const isUnderforecast = s.bias < 0
  const biasSign = isOverforecast ? '+' : isUnderforecast ? '−' : ''
  const biasLabel = isUnderforecast ? 'too low' : 'too high'

  return (
    <section aria-label="Forecast error metrics" className="grid grid-cols-[minmax(0,1fr)] gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
      <div className="rounded-[2px] border border-[#D6D0C2] bg-[#FBFAF6]">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E4DFD2] px-5 py-3">
          <h3 className="display text-[18px] text-[#15262B]">Historical forecast accuracy</h3>
          <p className="num text-[12px] text-[#5C6A68]">
            {scopeLabel} {isoShort(params.from)}{params.from !== params.to && `–${isoShort(params.to)}`} · {mw(c.matched)} of {mw(c.total)} half-hours matched ({c.total ? ((c.matched / c.total) * 100).toFixed(1) : 0}%)
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4">
          <Kpi name="MAE" value={mw(s.mae)} helper="Mean absolute forecast error" />
          <Kpi name="RMSE" value={mw(s.rmse)} helper="Root mean squared error" />
          <Kpi
            name="Bias"
            value={biasSign + mw(Math.abs(s.bias))}
            helper={`${mw(Math.abs(s.bias))} MW ${biasLabel} on average`}
            accent={isUnderforecast ? 'text-[#3F7A5C]' : 'text-[#A4505B]'}
          />
          <Kpi name="P90 error" value={mw(s.p90)} helper="90% of matched half-hours were within this error" />
        </div>
      </div>

      <aside className="flex flex-col justify-between gap-4 rounded-[2px] border border-[#D6D0C2] bg-[#EAE6DA] p-5">
        <div>
          <p className="text-[11px] font-medium tracking-[0.06em] text-[#5C6A68]">Evaluation summary</p>
          <p className="display mt-3 text-[19px] leading-[1.35] text-[#15262B]">
            Forecasts ran <strong className="num font-semibold">{mw(Math.abs(s.bias))} MW {biasLabel}</strong> on average. 90% of evaluated periods had error ≤ <strong className="num font-semibold">{mw(s.p90)} MW</strong>.
          </p>
          <p className="mt-3 text-[13px] leading-[1.5] text-[#5C6A68]">
            {view.insight || (isOverforecast
              ? 'Over-forecast bias: day-ahead forecasts sat above metered wind generation across the evaluated period.'
              : 'Under-forecast bias: day-ahead forecasts sat below metered wind generation across the evaluated period.')}
          </p>
        </div>
        <p className="text-[11px] text-[#5C6A68] border-t border-[#D6D0C2]/60 pt-2">
          Descriptive historical evaluation of the selected Elexon BMRS sample only. No root causes asserted; no trading or purchasing advice provided.
        </p>
      </aside>
    </section>
  )
}
