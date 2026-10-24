// frontend/src/App.jsx
import { useCallback, useEffect, useState } from 'react'
import { fetchDashboard } from './api.js'
import Header from './components/Header.jsx'
import Hero from './components/Hero.jsx'
import Controls, { MIN_DELIVERY, MAX_DELIVERY } from './components/Controls.jsx'
import Metrics from './components/Metrics.jsx'
import MainChart from './components/MainChart.jsx'
import { ErrorHistogram, HorizonChart } from './components/SupportCharts.jsx'
import Footer from './components/Footer.jsx'
import { EmptyState, ErrorState, Skeleton } from './components/States.jsx'

const DEFAULTS = {
  from: '2026-01-02',
  to: '2026-02-01',
  focus: '2026-01-14',
  mode: 'dayahead',
  cutoff: 9,
  horizon: 24,
}

export default function App() {
  const [params, setParams] = useState(DEFAULTS)
  const [view, setView] = useState(null)
  const [status, setStatus] = useState('loading')
  const [retryTick, setRetryTick] = useState(0)

  const set = useCallback((patch) => {
    setParams((p) => {
      const n = { ...p, ...patch }
      if (n.from > n.to) n.to = n.from
      if (patch.focus && (n.focus < n.from || n.focus > n.to)) {
        // Choosing a focus day outside the current range expands range to full 31-day scope
        n.from = MIN_DELIVERY
        n.to = MAX_DELIVERY
      } else if (n.focus < n.from) n.focus = n.from
      else if (n.focus > n.to) n.focus = n.to
      return n
    })
  }, [])

  useEffect(() => {
    let live = true
    setStatus((s) => (s === 'ready' || s === 'refreshing' ? 'refreshing' : 'loading'))
    fetchDashboard(params, { retry: retryTick > 0 })
      .then((v) => {
        if (live) {
          setView(v)
          setStatus('ready')
        }
      })
      .catch((err) => {
        console.error('Failed to fetch dashboard:', err)
        if (live) setStatus('error')
      })
    return () => {
      live = false
    }
  }, [params, retryTick])

  const reset = () => setParams(DEFAULTS)
  const chip =
    params.mode === 'dayahead'
      ? `Day-ahead · cutoff ${String(params.cutoff).padStart(2, '0')}:00 UTC on D−1`
      : `Fixed horizon · ${params.horizon} h ahead`
  const scopeLabel = params.from === params.to ? 'Focus day' : 'Analysis range'

  let body
  if (status === 'error') {
    body = <ErrorState onRetry={() => { setStatus('loading'); setRetryTick((t) => t + 1) }} />
  } else if (!view) {
    body = <Skeleton />
  } else {
    const noForecast = view.coverage && view.coverage.noForecast === view.coverage.total
    body = (
      <div className={`grid grid-cols-[minmax(0,1fr)] gap-6 transition-opacity duration-200 ${status === 'refreshing' ? 'opacity-75' : ''}`}>
        <Hero
          view={view}
          params={params}
          onFocus={(focus) => set({ focus })}
          modeLabel={params.mode === 'dayahead' ? 'Day-ahead' : `${params.horizon} h ahead`}
        />
        <Controls params={params} set={set} reset={reset} />
        {view.empty ? (
          <EmptyState message="No data for the selected range" onReset={reset} />
        ) : noForecast ? (
          <EmptyState message="No forecasts available before this cutoff" onReset={reset} />
        ) : (
          <>
            {view.stats && <Metrics view={view} params={params} scopeLabel={scopeLabel} />}
            <MainChart view={view} params={params} chip={chip} onFocus={(focus) => set({ focus })} />
            <div className="grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-2">
              <HorizonChart view={view} params={params} />
              <ErrorHistogram view={view} />
            </div>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#F1EEE7]">
      <main className="mx-auto grid max-w-[1360px] grid-cols-[minmax(0,1fr)] gap-6 px-4 py-6 sm:px-6 lg:px-10 lg:py-8">
        <Header />
        {body}
        <Footer />
      </main>
    </div>
  )
}
