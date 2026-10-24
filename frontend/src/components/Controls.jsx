// frontend/src/components/Controls.jsx
import { RotateCcw } from 'lucide-react'

const CUTOFFS = [6, 9, 12, 15]
export const MIN_DELIVERY = '2026-01-02'
export const MAX_DELIVERY = '2026-02-01'

function shift(iso, n) {
  const d = new Date(iso + 'T00:00:00Z')
  d.setUTCDate(d.getUTCDate() + n)
  const s = d.toISOString().slice(0, 10)
  return s < MIN_DELIVERY ? MIN_DELIVERY : s > MAX_DELIVERY ? MAX_DELIVERY : s
}

export default function Controls({ params, set, reset }) {
  const presets = [
    { label: 'Focus day', from: params.focus, to: params.focus },
    { label: 'Focus week', from: shift(params.focus, -3), to: shift(params.focus, 3) },
    { label: 'All 31 delivery days', from: MIN_DELIVERY, to: MAX_DELIVERY },
  ]

  return (
    <section aria-label="Analysis controls" className="flex flex-wrap items-end gap-x-8 gap-y-5 rounded-[2px] border border-[#D6D0C2] bg-[#FBFAF6] px-5 py-4">
      <fieldset className="min-w-0">
        <legend className="label">Delivery date range (Jan 2026 decisions: 2 Jan – 1 Feb)</legend>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <div className="seg" role="group" aria-label="Range presets">
            {presets.map((p) => {
              const on = p.from === params.from && p.to === params.to
              return (
                <button
                  key={p.label}
                  type="button"
                  aria-pressed={on}
                  className={`seg-btn ${on ? 'seg-on' : ''}`}
                  onClick={() => set({ from: p.from, to: p.to })}
                >
                  {p.label}
                </button>
              )
            })}
          </div>
          <label className="sr-only" htmlFor="from">From</label>
          <input
            id="from"
            type="date"
            min={MIN_DELIVERY}
            max={params.to}
            value={params.from}
            onChange={(e) => e.target.value && set({ from: e.target.value })}
            className="field num"
          />
          <span className="text-[#5C6A68]" aria-hidden="true">–</span>
          <label className="sr-only" htmlFor="to">To</label>
          <input
            id="to"
            type="date"
            min={params.from}
            max={MAX_DELIVERY}
            value={params.to}
            onChange={(e) => e.target.value && set({ to: e.target.value })}
            className="field num"
          />
        </div>
      </fieldset>

      <fieldset>
        <legend className="label">Forecast vintage</legend>
        <div className="seg mt-2" role="radiogroup" aria-label="Mode">
          {[
            ['dayahead', 'Day-ahead'],
            ['fixed', 'Fixed horizon'],
          ].map(([v, l]) => (
            <button
              key={v}
              type="button"
              role="radio"
              aria-checked={params.mode === v}
              className={`seg-btn ${params.mode === v ? 'seg-on' : ''}`}
              onClick={() => set(v === 'fixed' && params.mode !== 'fixed' ? { mode: v, horizon: 24 } : { mode: v })}
            >
              {l}
            </button>
          ))}
        </div>
      </fieldset>

      <div className="min-w-[220px] flex-1 sm:flex-none">
        {params.mode === 'dayahead' ? (
          <>
            <label htmlFor="cutoff" className="label">Decision cutoff (D−1)</label>
            <select
              id="cutoff"
              value={params.cutoff}
              onChange={(e) => set({ cutoff: Number(e.target.value) })}
              className="field num mt-2 block w-full sm:w-[220px]"
            >
              {CUTOFFS.map((c) => (
                <option key={c} value={c}>
                  {String(c).padStart(2, '0')}:00 UTC on D−1
                </option>
              ))}
            </select>
          </>
        ) : (
          <>
            <div className="flex items-baseline justify-between gap-3">
              <label htmlFor="horizon" className="label">Forecast horizon</label>
              <output htmlFor="horizon" className="num text-[14px] font-semibold text-[#0F766E]">
                {params.horizon} h ahead
              </output>
            </div>
            <input
              id="horizon"
              type="range"
              min="0"
              max="48"
              step="3"
              value={params.horizon}
              onChange={(e) => set({ horizon: Number(e.target.value) })}
              className="mt-3 block w-full accent-[#0F766E]"
            />
          </>
        )}
      </div>

      <button
        type="button"
        onClick={reset}
        className="focus-ring inline-flex items-center gap-1.5 rounded-[2px] border border-[#D6D0C2] bg-white px-3 py-2 text-[12px] font-medium text-[#5C6A68] hover:border-[#15262B] hover:text-[#15262B]"
      >
        <RotateCcw size={13} aria-hidden="true" /> Reset defaults
      </button>
    </section>
  )
}
