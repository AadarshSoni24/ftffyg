import { useEffect, useState } from 'react'
import { Area, ComposedChart, CartesianGrid, Line, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { DAY, dayMs } from '../lib/analysis.js'
import { dayShort, full, hm, hours, mw, signedMw } from '../lib/format.js'

function useWidth() {
  const [w, setW] = useState(typeof window !== 'undefined' ? window.innerWidth : 1440)
  useEffect(() => {
    const f = () => setW(window.innerWidth)
    window.addEventListener('resize', f)
    return () => window.removeEventListener('resize', f)
  }, [])
  return w
}

function ticksFor(start, end, width) {
  const days = (end - start) / DAY
  const out = []
  if (days <= 1) {
    const step = width < 640 ? 6 : 3
    for (let t = start; t <= end; t += step * 3600e3) out.push(t)
  } else {
    const maxTicks = width < 640 ? 4 : width < 1024 ? 7 : 11
    const step = Math.max(1, Math.ceil(days / maxTicks))
    for (let t = start; t < end; t += step * DAY) out.push(t)
  }
  return out
}

function HoverCard({ active, payload }) {
  if (!active || !payload?.length) return null
  const r = payload[0].payload
  return (
    <div className="w-[256px] rounded-[2px] border border-[#D6D0C2] bg-[#FBFAF6] p-3.5 text-[12px] shadow-[0_12px_32px_-12px_rgba(19,43,50,0.3)]">
      <p className="num text-[13px] font-semibold text-[#15262B]">{full(r.t)}</p>
      <dl className="num mt-2.5 grid grid-cols-[1fr_auto] gap-x-4 gap-y-1.5">
        <dt className="flex items-center gap-2 text-[#5C6A68]"><span className="h-0.5 w-3 bg-[#0F766E]" />Forecast</dt>
        <dd className="text-right font-medium text-[#15262B]">{r.forecast != null ? `${mw(r.forecast)} MW` : 'Unavailable'}</dd>
        <dt className="flex items-center gap-2 text-[#5C6A68]"><span className="w-3 border-t-2 border-dashed border-[#B86B12]" />Actual</dt>
        <dd className="text-right font-medium text-[#15262B]">{r.actual != null ? `${mw(r.actual)} MW` : 'Missing'}</dd>
        <dt className="text-[#5C6A68]">Error (F − A)</dt>
        <dd className={`text-right font-semibold ${r.error == null ? 'text-[#5C6A68]' : r.error < 0 ? 'text-[#3F7A5C]' : 'text-[#A4505B]'}`}>{r.error != null ? `${signedMw(r.error)} MW · too ${r.error < 0 ? 'low' : 'high'}` : 'Not matched'}</dd>
      </dl>
      <div className="num mt-2.5 border-t border-[#E4DFD2] pt-2.5 text-[#5C6A68]">
        <p>Published {r.publish ? full(r.publish) : '—'}</p>
        <p className="mt-0.5">Effective horizon {hours(r.age)}</p>
      </div>
    </div>
  )
}

export default function MainChart({ view, params, chip, onFocus }) {
  const width = useWidth()
  const start = dayMs(params.from)
  const end = dayMs(params.to) + DAY
  const ticks = ticksFor(start, end, width)
  const single = end - start <= DAY
  const fStart = dayMs(params.focus)
  const c = view.coverage
  const gaps = [c.noActual && `${c.noActual} without metered actual`, c.noForecast && `${c.noForecast} without an eligible forecast`].filter(Boolean).join(', ')
  return (
    <section aria-label="Forecast versus actual wind generation" className="rounded-[2px] border border-[#D6D0C2] bg-[#FBFAF6] p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="display text-[26px] text-[#15262B]">Forecast vs actual wind generation</h3>
          <p className="mt-1 text-[13px] text-[#5C6A68]">Half-hourly MW by UTC target time.{!single && ' Shaded band marks the focus day; click the chart to move it.'}</p>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-[12px] text-[#5C6A68]">
          <span className="inline-flex items-center gap-2"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#0F766E" strokeWidth="2.25" /></svg>Forecast</span>
          <span className="inline-flex items-center gap-2"><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="#B86B12" strokeWidth="2" strokeDasharray="4 3" /></svg>Actual</span>
          <span className="rounded-full border border-[#CFE3DF] bg-[#F1F8F6] px-2.5 py-1 font-medium text-[#0F5F58]">{chip}</span>
        </div>
      </div>
      <div className="mt-5 h-[340px] sm:h-[420px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={view.rows} margin={{ top: 12, right: 8, bottom: 0, left: 0 }} onClick={(e) => { const t = view.rows[Number(e?.activeTooltipIndex)]?.t; if (t != null) onFocus(new Date(Math.floor(t / DAY) * DAY).toISOString().slice(0, 10)) }}>
            <defs>
              <linearGradient id="fc-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor="#14B8A6" stopOpacity="0.16" />
                <stop offset="1" stopColor="#14B8A6" stopOpacity="0" />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#E4DFD2" vertical={false} />
            {!single && <ReferenceArea x1={fStart} x2={fStart + DAY} fill="#15262B" fillOpacity={0.04} stroke="none" ifOverflow="hidden" />}
            <XAxis dataKey="t" type="number" scale="time" domain={[start, end]} ticks={ticks} tickFormatter={(t) => (single ? hm(t) : dayShort(t))} tick={{ fill: '#5C6A68', fontSize: 12 }} tickLine={false} axisLine={{ stroke: '#D6D0C2' }} tickMargin={10} />
            <YAxis domain={[0, 20000]} ticks={[0, 5000, 10000, 15000, 20000]} tickFormatter={(v) => mw(v)} tick={{ fill: '#5C6A68', fontSize: 12 }} tickLine={false} axisLine={false} width={56} allowDataOverflow />
            <Tooltip content={<HoverCard />} cursor={{ stroke: '#15262B', strokeOpacity: 0.35, strokeWidth: 1 }} isAnimationActive={false} wrapperStyle={{ outline: 'none' }} />
            <Area dataKey="forecast" type="monotoneX" stroke="none" fill="url(#fc-fill)" connectNulls={false} isAnimationActive={false} activeDot={false} tooltipType="none" />
            <Line dataKey="forecast" type="monotoneX" stroke="#0F766E" strokeWidth={2.25} dot={false} connectNulls={false} isAnimationActive={false} activeDot={{ r: 4, fill: '#0F766E', stroke: '#fff', strokeWidth: 2 }} />
            <Line dataKey="actual" type="monotoneX" stroke="#B86B12" strokeWidth={2} strokeDasharray="4 3" dot={false} connectNulls={false} isAnimationActive={false} activeDot={{ r: 4, fill: '#B86B12', stroke: '#fff', strokeWidth: 2 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-[12px] text-[#5C6A68]">
        All {mw(view.rows.length)} half-hours drawn, no aggregation. {gaps ? `Line breaks show missing values (${gaps}); ` : 'Missing values would appear as line breaks; '}never interpolated or set to zero.
      </p>
    </section>
  )
}
