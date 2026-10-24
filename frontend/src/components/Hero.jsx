// frontend/src/components/Hero.jsx
import WindField from './WindField.jsx'
import { dayMs } from '../lib/analysis.js'
import { full, hm, hours, longDate, mw } from '../lib/format.js'

const MAX = 22000

export default function Hero({ view, params, onFocus, modeLabel }) {
  const { focus, daily = [] } = view
  const d = longDate(dayMs(params.focus))
  const pubs = focus?.publishTimesIso || focus?.publishTimes || []
  const asOf = focus?.asOfPublishTime || focus?.asOf || (pubs.length ? pubs[pubs.length - 1] : null)

  return (
    <section className="grid grid-cols-[minmax(0,1fr)] overflow-hidden rounded-[2px] border border-[#D6D0C2] bg-[#E9ECE4]" aria-label="Selected delivery day overview">
      <div className="pointer-events-none min-w-0 overflow-hidden [grid-area:1/1]">
        <WindField />
      </div>
      <div className="relative min-w-0 [grid-area:1/1] flex flex-col gap-8 p-6 sm:p-8 lg:p-10">
        <div className="grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[1.3fr_1fr] lg:items-end">
          <div>
            <p className="eyebrow">Focus delivery day</p>
            <h2 className="mt-3 display text-[44px] leading-[1] text-[#15262B] sm:text-[64px]">
              {d.dow} {d.day} {d.month}
              <span className="italic text-[#7A8A84]"> {d.year}</span>
            </h2>
            <div className="mt-8 flex flex-wrap items-end gap-x-10 gap-y-6">
              <div>
                <p className="text-[13px] text-[#5C6A68]">Average forecast</p>
                <p className="display num mt-1 text-[56px] font-light leading-none text-[#0F5F58]">
                  {mw(focus?.avgForecast)}<span className="ml-1.5 text-[16px] font-normal text-[#5C6A68]">MW</span>
                </p>
                <p className="mt-2 text-[12px] text-[#5C6A68]">
                  {focus?.available ? `Mean of ${focus.available} half-hourly forecasts` : 'No eligible forecasts'}
                </p>
              </div>
              <div>
                <p className="text-[13px] text-[#5C6A68]">Actual average</p>
                <p className="display num mt-1 text-[34px] leading-none text-[#A8610F]">
                  {mw(focus?.avgActual)}<span className="ml-1 text-[14px] font-normal text-[#5C6A68]">MW</span>
                </p>
                <p className="mt-2 text-[12px] text-[#5C6A68]">
                  {focus?.avgActual != null ? 'Metered, known after delivery' : 'No metered values'}
                </p>
              </div>
              <div>
                <p className="text-[13px] text-[#5C6A68]">Peak half-hour forecast</p>
                <p className="display num mt-1 text-[34px] leading-none text-[#15262B]">
                  {mw(focus?.peak?.forecast)}<span className="ml-1 text-[14px] font-normal text-[#5C6A68]">MW</span>
                </p>
                <p className="mt-2 text-[12px] text-[#5C6A68]">
                  {focus?.peak ? `at ${hm(focus.peak.t || dayMs(focus.peak.startTime))} UTC` : 'Unavailable'}
                </p>
              </div>
            </div>
          </div>
          <dl className="grid gap-4 rounded-[2px] border border-[#D6D0C2] bg-[#FBFAF6]/80 p-5 text-[13px]">
            <div className="flex items-center justify-between gap-3">
              <dt className="eyebrow">Decision context</dt>
              <dd className="border border-[#0F5F58]/30 px-2 py-0.5 font-mono text-[11px] font-normal text-[#0F5F58]">{modeLabel}</dd>
            </div>
            <div>
              <dt className="text-[#5C6A68]">As of publish time</dt>
              <dd className="num mt-0.5 text-[16px] font-medium text-[#15262B]">{asOf ? full(asOf) : 'No eligible forecast'}</dd>
              {pubs.length > 1 && (
                <dd className="mt-1 text-[12px] text-[#5C6A68]">
                  Latest of {pubs.length} forecast runs used across this day’s half-hours
                </dd>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4 border-t border-[#E4DFD2] pt-4">
              <div>
                <dt className="text-[#5C6A68]">Effective horizon</dt>
                <dd className="num mt-0.5 font-medium text-[#15262B]">
                  {focus?.effectiveHorizonRange || (focus?.ages ? `${hours(focus.ages[0])} – ${hours(focus.ages[1])}` : '—')}
                </dd>
              </div>
              <div>
                <dt className="text-[#5C6A68]">Day MAE (observed)</dt>
                <dd className="num mt-0.5 font-medium text-[#15262B]">
                  {focus?.stats ? `${mw(focus.stats.mae)} MW` : '—'}
                </dd>
              </div>
            </div>
          </dl>
        </div>

        <div>
          <div className="mb-2 flex items-baseline justify-between gap-3">
            <p className="eyebrow">January 2026 decision deliveries (2 Jan – 1 Feb 2026) · daily average · choose focus day</p>
            <p className="hidden items-center gap-3 text-[12px] text-[#5C6A68] sm:flex">
              <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2 rounded-[2px] bg-[#14B8A6]/70" />Forecast</span>
              <span className="inline-flex items-center gap-1.5"><span className="h-0.5 w-3 bg-[#B86B12]" />Actual</span>
            </p>
          </div>
          <div className="flex h-[76px] items-end gap-[3px]" role="group" aria-label="31-day focus day selector">
            {daily.map((day) => {
              const fc = day.avgForecast ?? day.forecast
              const act = day.avgActual ?? day.actual
              const sel = day.date === params.focus
              const inRange = day.date >= params.from && day.date <= params.to
              const fh = fc ? (fc / MAX) * 100 : 0
              const ah = act ? (act / MAX) * 100 : null
              const isFeb = day.date.startsWith('2026-02')
              const dayNum = isFeb ? '1 Feb' : `${Number(day.date.slice(8))}`

              return (
                <button
                  key={day.date}
                  type="button"
                  onClick={() => onFocus(day.date)}
                  aria-pressed={sel}
                  aria-label={`${day.date}: average forecast ${mw(fc)} MW, actual ${mw(act)} MW`}
                  className={`focus-ring relative flex h-full min-w-0 flex-1 flex-col justify-end rounded-[5px] transition-colors duration-200 ${sel ? 'bg-[#15262B]/[0.07]' : 'hover:bg-[#15262B]/[0.05]'}`}
                >
                  <span className={`mx-auto w-[70%] rounded-t-[3px] transition-all duration-200 ${sel ? 'bg-[#0F766E]' : inRange ? 'bg-[#14B8A6]/70' : 'bg-[#14B8A6]/25'}`} style={{ height: `${Math.max(fh, 3)}%` }} />
                  {ah != null && <span className="pointer-events-none absolute left-[8%] right-[8%] h-[2px] rounded bg-[#B86B12]" style={{ bottom: `${ah}%` }} />}
                </button>
              )
            })}
          </div>
          <div className="mt-1.5 flex gap-[3px] text-[10px] text-[#5C6A68]">
            {daily.map((day, i) => {
              const isFeb = day.date.startsWith('2026-02')
              const dayLabel = isFeb ? '1 Feb' : `${Number(day.date.slice(8))}`
              const isSel = day.date === params.focus
              return (
                <span
                  key={day.date}
                  className={`num min-w-0 flex-1 text-center ${isSel ? 'font-bold text-[#15262B]' : ''} ${!isSel && i % 2 !== 0 && !isFeb ? 'max-sm:invisible' : ''}`}
                >
                  {dayLabel}
                </span>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
