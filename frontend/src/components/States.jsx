import { AlertCircle } from 'lucide-react'

const block = 'rounded-[2px] bg-[#E6EDEB] animate-pulse motion-reduce:animate-none'

export function Skeleton() {
  return (
    <div className="grid gap-6" aria-busy="true" aria-label="Loading dashboard">
      <div className={`${block} h-[420px]`} />
      <div className={`${block} h-[84px]`} />
      <div className={`${block} h-[170px]`} />
      <div className={`${block} h-[520px]`} />
    </div>
  )
}

export function ErrorState({ onRetry }) {
  return (
    <div role="alert" className="grid place-items-center gap-3 rounded-[2px] border border-[#D6D0C2] bg-[#FBFAF6] px-6 py-20 text-center">
      <AlertCircle className="text-[#A4505B]" size={22} aria-hidden="true" />
      <p className="text-[16px] font-medium text-[#15262B]">We couldn't load this view.</p>
      <button type="button" onClick={onRetry} className="focus-ring rounded-[2px] bg-[#15262B] px-4 py-2 text-[13px] font-medium text-white hover:bg-[#1E3D46]">Retry</button>
    </div>
  )
}

export function EmptyState({ message, onReset }) {
  return (
    <div className="grid place-items-center gap-3 rounded-[2px] border border-[#D6D0C2] bg-[#FBFAF6] px-6 py-16 text-center">
      <p className="text-[16px] font-medium text-[#15262B]">{message}</p>
      <button type="button" onClick={onReset} className="focus-ring rounded-[2px] border border-[#D6D0C2] px-4 py-2 text-[13px] font-medium text-[#15262B] hover:bg-[#F1EEE7]">Reset</button>
    </div>
  )
}
