// frontend/src/api.js
// Single data-access boundary communicating with FastAPI backend.
// Backend is the single source of truth; no client-side metrics recalculation.

const API_BASE = import.meta.env.VITE_API_URL || ''

export async function fetchDashboard(query, { retry = false } = {}) {
  const params = new URLSearchParams({
    from: query.from,
    to: query.to,
    focus: query.focus,
    mode: query.mode || 'dayahead',
    cutoff: String(query.cutoff ?? 9),
    horizon: String(query.horizon ?? 24),
  })

  const url = `${API_BASE}/api/dashboard?${params.toString()}`
  
  const res = await fetch(url, {
    headers: {
      'Accept': 'application/json',
    },
  })

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`)
  }

  const data = await res.json()
  return data
}

export const SOURCE = {
  datasets: ['FUELHH (fuelType WIND)', 'WINDFOR'],
  note: 'Official Elexon BMRS datasets: GB National Wind Generation Actuals and Day-Ahead Forecasts.',
}
