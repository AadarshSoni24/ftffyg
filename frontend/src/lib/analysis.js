// frontend/src/lib/analysis.js
// Display and time helpers for chart alignment.
// Calculation logic deleted: The FastAPI backend is the single source of truth for all metrics.

export const HALF = 30 * 60 * 1000
export const HOUR = 60 * 60 * 1000
export const DAY = 24 * HOUR

/** Parse ISO date string (YYYY-MM-DD) to UTC epoch milliseconds */
export const dayMs = (iso) => Date.parse(`${iso}T00:00:00Z`)
