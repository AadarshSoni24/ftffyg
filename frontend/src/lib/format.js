// Explicit UTC formatting; never uses the viewer's local timezone.
const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const DOW_LONG = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const MON_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
const p2 = (n) => String(n).padStart(2, '0')

export const mw = (v) => (v == null || Number.isNaN(v) ? '—' : Math.round(v).toLocaleString('en-GB'))
export const signedMw = (v) => (v == null ? '—' : (v > 0 ? '+' : v < 0 ? '−' : '') + mw(Math.abs(v)))
export const hm = (ms) => { const d = new Date(ms); return `${p2(d.getUTCHours())}:${p2(d.getUTCMinutes())}` }
export const dayShort = (ms) => { const d = new Date(ms); return `${DOW[d.getUTCDay()]} ${d.getUTCDate()} ${MON[d.getUTCMonth()]}` }
export const full = (ms) => `${dayShort(ms)} ${new Date(ms).getUTCFullYear()}, ${hm(ms)} UTC`
export const longDate = (ms) => { const d = new Date(ms); return { dow: DOW_LONG[d.getUTCDay()], day: d.getUTCDate(), month: MON_LONG[d.getUTCMonth()], year: d.getUTCFullYear() } }
export const isoShort = (iso) => { const d = new Date(iso + 'T00:00:00Z'); return `${d.getUTCDate()} ${MON[d.getUTCMonth()]}` }
export const hours = (h) => (h == null ? '—' : `${Number.isInteger(h) ? h : h.toFixed(1)} h`)
