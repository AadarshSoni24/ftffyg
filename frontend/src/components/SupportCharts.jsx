import { Bar, BarChart, CartesianGrid, Cell, ComposedChart, Line, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { mw, signedMw } from '../lib/format.js'

const axis = { tick: { fill: '#5C6A68', fontSize: 12 }, tickLine: false }
const box = 'num rounded-[2px] border border-[#D6D0C2] bg-[#FBFAF6] px-3 py-2 text-[12px] shadow-[0_8px_24px_-12px_rgba(19,43,50,0.3)]'

function Card({ title, sub, children, foot }) {
  return (
    <section className="rounded-[2px] border border-[#D6D0C2] bg-[#FBFAF6] p-5 sm:p-6" aria-label={title}>
      <h3 className="display text-[20px] text-[#15262B]">{title}</h3>
      <p className="mt-1 text-[13px] text-[#5C6A68]">{sub}</p>
      <div className="mt-4 h-[260px]">{children}</div>
      {foot && <p className="mt-2 text-[12px] text-[#5C6A68]">{foot}</p>}
    </section>
  )
}

export function HorizonChart({ view, params }) {
  const span = params.mode === 'dayahead' ? view.ageSpan : null
  return (
    <Card title="Error by forecast horizon" sub="MAE (MW) by effective forecast age, target time − publish time. Each published vintage scored independently." foot={span ? `Shaded: effective ages used by the current day-ahead cutoff (${span[0].toFixed(1)}–${span[1].toFixed(1)} h).` : `Dashed: requested ${params.horizon} h. Effective age can be older because forecasts publish every 3 h.`}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={view.horizon} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="#E4DFD2" vertical={false} />
          {span && <ReferenceArea x1={span[0]} x2={span[1]} fill="#14B8A6" fillOpacity={0.1} />}
          {!span && <ReferenceLine x={params.horizon} stroke="#0F766E" strokeDasharray="3 3" />}
          <XAxis dataKey="mid" type="number" domain={[0, 48]} ticks={[0, 6, 12, 18, 24, 30, 36, 42, 48]} {...axis} axisLine={{ stroke: '#D6D0C2' }} tickFormatter={(v) => `${v} h`} />
          <YAxis {...axis} axisLine={false} width={48} tickFormatter={(v) => mw(v)} />
          <Tooltip isAnimationActive={false} cursor={{ stroke: '#15262B', strokeOpacity: 0.25 }} content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const b = payload[0].payload
            return <div className={box}><p className="font-semibold text-[#15262B]">{b.from}–{b.to} h ahead</p><p className="text-[#5C6A68]">MAE {b.mae != null ? `${mw(b.mae)} MW` : 'no samples'}</p><p className="text-[#5C6A68]">{mw(b.n)} forecast–actual pairs</p></div>
          }} />
          <Line dataKey="mae" type="linear" stroke="#0F766E" strokeWidth={2} dot={{ r: 2.5, fill: '#0F766E', strokeWidth: 0 }} connectNulls={false} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </Card>
  )
}

export function ErrorHistogram({ view }) {
  const { bins, limit } = view.histogram
  const mean = view.stats?.bias
  return (
    <Card title="Forecast error distribution" sub="Matched half-hours by signed error, forecast − actual (MW)." foot={`500 MW bins. Outer bars include errors beyond ±${mw(limit)} MW. Dashed line: mean error ${signedMw(mean)} MW.`}>
      <div className="flex h-full flex-col">
        <div className="flex justify-between pl-12 pr-2 text-[12px] font-medium">
          <span className="text-[#3F7A5C]">← Forecast too low</span>
          <span className="text-[#A4505B]">Forecast too high →</span>
        </div>
        <div className="min-h-0 flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bins} margin={{ top: 12, right: 8, bottom: 0, left: 0 }} barCategoryGap={1}>
              <CartesianGrid stroke="#E4DFD2" vertical={false} />
              <XAxis dataKey="mid" type="number" domain={[-limit, limit]} ticks={[-4000, -2000, 0, 2000, 4000]} {...axis} axisLine={{ stroke: '#D6D0C2' }} tickFormatter={(v) => signedMw(v)} />
              <YAxis {...axis} axisLine={false} width={40} allowDecimals={false} />
              <Tooltip isAnimationActive={false} cursor={{ fill: '#15262B', fillOpacity: 0.04 }} content={({ active, payload }) => {
                if (!active || !payload?.length) return null
                const b = payload[0].payload
                const rangeLabel = b.overflow === 'low' || b.x0 === -Infinity || b.x0 <= -limit
                  ? `≤ −${mw(limit)} MW`
                  : b.overflow === 'high' || b.x1 === Infinity || (b.x0 >= limit)
                  ? `≥ +${mw(limit)} MW`
                  : `${signedMw(b.x0)} to ${signedMw(b.x1)} MW`
                return <div className={box}><p className="font-semibold text-[#15262B]">{rangeLabel}</p><p className="text-[#5C6A68]">{b.count} half-hours · forecast too {b.mid < 0 ? 'low' : 'high'}</p></div>
              }} />
              <Bar dataKey="count" isAnimationActive={false} radius={[3, 3, 0, 0]}>
                {bins.map((b) => <Cell key={b.mid} fill={b.mid < 0 ? '#7FAE95' : '#D19AA2'} />)}
              </Bar>
              <ReferenceLine x={0} stroke="#15262B" strokeOpacity={0.6} />
              {mean != null && <ReferenceLine x={mean} stroke="#15262B" strokeDasharray="4 3" />}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Card>
  )
}
