import { useMemo } from 'react'

// Decorative streamlines: an abstract wind-field texture, not measured geography.
export default function WindField() {
  const paths = useMemo(() => {
    let s = 7
    const r = () => ((s = (s * 16807) % 2147483647) / 2147483647)
    const out = []
    for (let i = 0; i < 34; i++) {
      let x = -80 + r() * 900
      let y = r() * 420
      let d = `M${x.toFixed(1)} ${y.toFixed(1)}`
      for (let k = 0; k < 70; k++) {
        const a = Math.sin(x * 0.0042 + y * 0.0021) * 0.55 + Math.cos(y * 0.0065 + 1.3) * 0.28 - 0.12
        x += Math.cos(a) * 9
        y += Math.sin(a) * 9
        d += ` L${x.toFixed(1)} ${y.toFixed(1)}`
      }
      out.push({ d, o: 0.1 + r() * 0.22, w: 0.6 + r() * 1.1, delay: (i % 9) * 60 })
    }
    return out
  }, [])
  return (
    <svg viewBox="0 0 1200 420" preserveAspectRatio="xMidYMid slice" className="h-full w-full" aria-hidden="true">
      <defs>
        <linearGradient id="wf-fade" x1="0" x2="1">
          <stop offset="0" stopColor="#0F766E" stopOpacity="0" />
          <stop offset="0.35" stopColor="#0F766E" stopOpacity="1" />
          <stop offset="1" stopColor="#0F766E" stopOpacity="0.5" />
        </linearGradient>
      </defs>
      {paths.map((p, i) => (
        <path key={i} d={p.d} fill="none" stroke="url(#wf-fade)" strokeOpacity={p.o} strokeWidth={p.w} strokeLinecap="round" className="wf-line" style={{ animationDelay: `${p.delay}ms` }} pathLength="1" />
      ))}
    </svg>
  )
}
