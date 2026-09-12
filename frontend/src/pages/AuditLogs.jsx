import { useEffect, useState } from 'react'
import api, { getErrorMessage } from '../services/api'
import LoadingState from '../components/LoadingState'
import ErrorBanner from '../components/ErrorBanner'
import EmptyState from '../components/EmptyState'

export default function AuditLogs() {
  const [items, setItems] = useState([])
  const [eventType, setEventType] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const params = { page: 1, page_size: 100 }
      if (eventType) params.event_type = eventType
      const res = await api.get('/audit-logs', { params })
      setItems(res.data.items)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventType])

  const EVENT_TYPES = [
    'LEAD_CREATED', 'LEAD_EXTRACTED', 'RESEARCH_GENERATED', 'SCORE_COMPUTED',
    'ACTION_SELECTED', 'ACTION_APPROVED', 'ACTION_REJECTED', 'ACTION_OVERRIDDEN',
    'OUTCOME_UPDATED', 'SETTINGS_UPDATED',
  ]

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-slate-900">Audit Logs</h1>
        <select value={eventType} onChange={(e) => setEventType(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm">
          <option value="">All Events</option>
          {EVENT_TYPES.map((e) => (
            <option key={e} value={e}>
              {e.replaceAll('_', ' ')}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorBanner message={error} onRetry={load} />
      ) : items.length === 0 ? (
        <EmptyState title="No audit events yet" />
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
                <th className="px-4 py-2 font-medium">Timestamp</th>
                <th className="px-4 py-2 font-medium">Event</th>
                <th className="px-4 py-2 font-medium">Lead</th>
                <th className="px-4 py-2 font-medium">Actor</th>
                <th className="px-4 py-2 font-medium">Output</th>
              </tr>
            </thead>
            <tbody>
              {items.map((log) => (
                <tr key={log.id} className="border-b border-slate-50 last:border-0 align-top">
                  <td className="px-4 py-3 whitespace-nowrap text-slate-500">{new Date(log.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-3 font-medium text-slate-800">{log.event_type.replaceAll('_', ' ')}</td>
                  <td className="px-4 py-3 text-slate-400 font-mono text-xs">{log.lead_id ? log.lead_id.slice(0, 8) : '-'}</td>
                  <td className="px-4 py-3 text-slate-500">{log.actor || 'system'}</td>
                  <td className="px-4 py-3 max-w-xs truncate text-slate-500" title={log.output}>
                    {log.output || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
