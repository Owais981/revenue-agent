const CATEGORY_LABEL = { fit: 'Fit', intent: 'Intent', deliverability: 'Deliverability' }

export default function FactorList({ factors }) {
  if (!factors || factors.length === 0) return <p className="text-sm text-slate-400">No factors recorded.</p>

  return (
    <div className="space-y-2">
      {factors.map((f, idx) => (
        <div key={idx} className="flex items-start justify-between gap-3 rounded-lg border border-slate-100 px-3 py-2">
          <div>
            <p className="text-sm font-medium text-slate-700">
              {CATEGORY_LABEL[f.category] || f.category} {f.contribution >= 0 ? '+' : ''}
              {f.contribution}
              <span className="ml-2 text-slate-400 font-normal">{f.name}</span>
            </p>
            <p className="text-xs text-slate-400">{f.reason}</p>
          </div>
          <span
            className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${
              f.contribution > 0 ? 'bg-emerald-100 text-emerald-700' : f.contribution < 0 ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-500'
            }`}
          >
            {f.contribution >= 0 ? '+' : ''}
            {f.contribution}
          </span>
        </div>
      ))}
    </div>
  )
}
