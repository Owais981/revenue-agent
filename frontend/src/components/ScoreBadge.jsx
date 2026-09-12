function bandFor(score) {
  if (score === null || score === undefined) return { label: 'N/A', classes: 'bg-slate-100 text-slate-500' }
  if (score >= 85) return { label: 'Very High', classes: 'bg-emerald-100 text-emerald-700' }
  if (score >= 70) return { label: 'High', classes: 'bg-brand-100 text-brand-700' }
  if (score >= 40) return { label: 'Medium', classes: 'bg-amber-100 text-amber-700' }
  return { label: 'Low', classes: 'bg-rose-100 text-rose-700' }
}

export default function ScoreBadge({ score, showLabel = true, size = 'md' }) {
  const { label, classes } = bandFor(score)
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1'
  return (
    <span className={`inline-flex items-center gap-1 rounded-full font-medium ${classes} ${sizeClasses}`}>
      <span>{score === null || score === undefined ? '-' : Math.round(score)}</span>
      {showLabel && <span className="opacity-70">{label}</span>}
    </span>
  )
}
