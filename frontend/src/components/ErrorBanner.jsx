export default function ErrorBanner({ message, onRetry }) {
  if (!message) return null
  return (
    <div className="flex items-center justify-between rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      <span>{message}</span>
      {onRetry && (
        <button onClick={onRetry} className="ml-4 shrink-0 font-medium underline hover:no-underline">
          Retry
        </button>
      )}
    </div>
  )
}
