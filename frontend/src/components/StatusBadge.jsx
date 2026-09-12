const STATUS_STYLES = {
  NEW: 'bg-slate-100 text-slate-700',
  PROCESSING: 'bg-blue-100 text-blue-700',
  QUALIFIED: 'bg-brand-100 text-brand-700',
  NURTURE: 'bg-amber-100 text-amber-700',
  DISQUALIFIED: 'bg-slate-200 text-slate-500',
  FINANCE_HOLD: 'bg-rose-100 text-rose-700',
  ROUTED_TO_PROPOSAL: 'bg-violet-100 text-violet-700',
  CLOSED_WON: 'bg-emerald-100 text-emerald-700',
  CLOSED_LOST: 'bg-slate-200 text-slate-500',
  PENDING: 'bg-amber-100 text-amber-700',
  APPROVED: 'bg-emerald-100 text-emerald-700',
  REJECTED: 'bg-rose-100 text-rose-700',
  SENT: 'bg-brand-100 text-brand-700',
}

export default function StatusBadge({ status }) {
  const classes = STATUS_STYLES[status] || 'bg-slate-100 text-slate-600'
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium whitespace-nowrap ${classes}`}>
      {status?.replaceAll('_', ' ') || 'Unknown'}
    </span>
  )
}
