export default function ScoreBar({ label, value }) {
  const pct = Math.max(0, Math.min(100, value ?? 0))
  const color = pct >= 85 ? 'bg-emerald-500' : pct >= 70 ? 'bg-brand-500' : pct >= 40 ? 'bg-amber-500' : 'bg-rose-500'
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-slate-600">{label}</span>
        <span className="text-sm font-semibold text-slate-900">{value === null || value === undefined ? '-' : Math.round(value)}</span>
      </div>
      <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
