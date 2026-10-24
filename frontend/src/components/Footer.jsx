// frontend/src/components/Footer.jsx
import { SOURCE } from '../api.js'

export default function Footer() {
  return (
    <footer className="grid gap-4 border-t border-[#D6D0C2] pt-6 text-[12px] leading-[1.6] text-[#5C6A68]">
      <p>
        Data sources: Elexon BMRS {SOURCE.datasets.join(' and ')}. Resolution: 30-minute settlement periods, UTC. Metered wind reflects transmission-system metered wind generation reported by Elexon BMRS.
      </p>
      <details className="rounded-[2px] border border-[#D6D0C2] bg-[#FBFAF6] px-4 py-3">
        <summary className="focus-ring cursor-pointer rounded text-[13px] font-medium text-[#15262B]">Methodology & Scope Boundaries</summary>
        <ul className="mt-3 grid list-disc gap-1.5 pl-5">
          <li><strong>Scope:</strong> Evaluates delivery days whose Day D−1 procurement decision falls in January 2026: 2 January 2026 through 1 February 2026 (31 delivery days, 1,488 half-hours total).</li>
          <li><strong>Day-Ahead Decision Rule:</strong> For any delivery half-hour target time <em>t</em> on Day D, the procurement cutoff <em>c</em> is 09:00 UTC on Day D−1. The forecast assigned is the latest WINDFOR run with publishTime ≤ <em>c</em>.</li>
          <li><strong>Fixed Horizon Mode:</strong> Evaluates the latest forecast published at least <em>h</em> hours before delivery start (publishTime ≤ <em>t − h</em>).</li>
          <li><strong>Error Sign Convention:</strong> Signed error <em>e = forecast − actual</em>. Positive error indicates over-forecast (forecast exceeded metered generation); negative error indicates under-forecast.</li>
          <li><strong>Metrics:</strong> MAE = mean(|e|); RMSE = √(mean(e²)); Bias = mean(e); P90 = 90th percentile of |e| (nearest-rank); MAPE is computed safely over positive actuals.</li>
          <li><strong>Single Source of Truth:</strong> All metrics, histograms, and daily summaries are computed deterministically on the backend and mathematically reconciled.</li>
        </ul>
      </details>
    </footer>
  )
}
