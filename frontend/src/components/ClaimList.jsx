export default function ClaimList({ claims }) {
  if (!claims || claims.length === 0) return <p className="text-sm text-slate-400">No research claims yet.</p>

  return (
    <div className="space-y-2">
      {claims.map((c, idx) => (
        <div key={idx} className="rounded-lg border border-slate-100 px-3 py-2">
          <p className="text-sm text-slate-700">{c.text}</p>
          <div className="mt-1 flex items-center gap-2 text-xs">
            {c.verified ? (
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 font-medium text-emerald-700">Verified</span>
            ) : (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 font-medium text-amber-700">Unverified</span>
            )}
            {c.source_url && (
              <a href={c.source_url} target="_blank" rel="noreferrer" className="text-brand-600 hover:underline">
                Source
              </a>
            )}
            {c.internal_record_id && <span className="text-slate-400">Ref: {c.internal_record_id}</span>}
          </div>
        </div>
      ))}
    </div>
  )
}
