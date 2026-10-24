// frontend/src/components/Header.jsx
import { Info, Wind } from 'lucide-react'
import { SOURCE } from '../api.js'

export default function Header() {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <span className="grid size-9 place-items-center border border-[#15262B] text-[#15262B]">
          <Wind size={18} strokeWidth={1.75} aria-hidden="true" />
        </span>
        <div>
          <h1 className="display text-[24px] leading-none text-[#15262B]">UK Wind Forecast Monitor</h1>
          <p className="mt-1.5 font-mono text-[11px] uppercase tracking-[0.08em] text-[#5C6A68]">
            National wind generation · delivery days for January 2026 purchase decisions (2 Jan – 1 Feb 2026) · all times UTC
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className="group relative inline-flex">
          <button
            type="button"
            className="focus-ring inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[12px] text-[#5C6A68] hover:text-[#15262B]"
            aria-describedby="tip-cutoff"
          >
            <Info size={14} aria-hidden="true" /> How forecasts are chosen
          </button>
          <span id="tip-cutoff" role="tooltip" className="tip right-0">
            For each delivery half-hour, selects the latest forecast vintage published on or before your decision cutoff.
          </span>
        </span>
        <span className="group relative inline-flex">
          <button
            type="button"
            className="focus-ring inline-flex items-center gap-1.5 rounded-full border border-[#0F766E]/40 px-2.5 py-1 font-mono text-[11px] text-[#0F766E]"
            aria-describedby="tip-demo"
          >
            <span className="size-1.5 rounded-full bg-[#0F766E]" aria-hidden="true" /> Elexon BMRS
          </button>
          <span id="tip-demo" role="tooltip" className="tip right-0">
            {SOURCE.note}
          </span>
        </span>
      </div>
    </header>
  )
}
