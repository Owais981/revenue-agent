export default function LoadingState({ label = 'Loading...' }) {
  return (
    <div className="flex items-center justify-center py-16 text-slate-400">
      <div className="flex items-center gap-3">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-brand-500" />
        <span className="text-sm">{label}</span>
      </div>
    </div>
  )
}
