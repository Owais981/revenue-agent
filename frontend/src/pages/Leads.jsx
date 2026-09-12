import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { getErrorMessage } from '../services/api'
import LoadingState from '../components/LoadingState'
import ErrorBanner from '../components/ErrorBanner'
import EmptyState from '../components/EmptyState'
import ScoreBadge from '../components/ScoreBadge'
import StatusBadge from '../components/StatusBadge'

const STATUS_OPTIONS = [
  'NEW', 'PROCESSING', 'QUALIFIED', 'NURTURE', 'DISQUALIFIED',
  'FINANCE_HOLD', 'ROUTED_TO_PROPOSAL', 'CLOSED_WON', 'CLOSED_LOST',
]
const SOURCE_OPTIONS = ['website', 'email', 'whatsapp', 'referral', 'outbound', 'manual']
const SORT_OPTIONS = [
  { value: 'composite_desc', label: 'Highest Composite' },
  { value: 'fit_desc', label: 'Highest Fit' },
  { value: 'intent_desc', label: 'Highest Intent' },
  { value: 'newest', label: 'Newest' },
  { value: 'oldest', label: 'Oldest' },
]

export default function Leads() {
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [status, setStatus] = useState('')
  const [source, setSource] = useState('')
  const [sort, setSort] = useState('composite_desc')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const params = { page, page_size: pageSize, sort }
      if (status) params.status = status
      if (source) params.source = source
      const res = await api.get('/leads', { params })
      setItems(res.data.items)
      setTotal(res.data.total)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, status, source, sort])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-slate-900">Leads</h1>
        <Link to="/leads/new" className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          + New Lead
        </Link>
      </div>

      <div className="flex flex-wrap gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
        <select
          value={status}
          onChange={(e) => {
            setPage(1)
            setStatus(e.target.value)
          }}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="">All Statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s.replaceAll('_', ' ')}
            </option>
          ))}
        </select>
        <select
          value={source}
          onChange={(e) => {
            setPage(1)
            setSource(e.target.value)
          }}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="">All Sources</option>
          {SOURCE_OPTIONS.map((s) => (
            <option key={s} value={s} className="capitalize">
              {s}
            </option>
          ))}
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm">
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorBanner message={error} onRetry={load} />
      ) : items.length === 0 ? (
        <EmptyState title="No leads match these filters" />
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
                <th className="px-4 py-2 font-medium">Company</th>
                <th className="px-4 py-2 font-medium">Source</th>
                <th className="px-4 py-2 font-medium">Fit</th>
                <th className="px-4 py-2 font-medium">Intent</th>
                <th className="px-4 py-2 font-medium">Delivery</th>
                <th className="px-4 py-2 font-medium">Composite</th>
                <th className="px-4 py-2 font-medium">Next Action</th>
                <th className="px-4 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((lead) => (
                <tr
                  key={lead.id}
                  onClick={() => navigate(`/leads/${lead.id}`)}
                  className="cursor-pointer border-b border-slate-50 last:border-0 hover:bg-slate-50"
                >
                  <td className="px-4 py-3 font-medium text-slate-800 whitespace-nowrap">{lead.company || 'Unknown company'}</td>
                  <td className="px-4 py-3 capitalize text-slate-500">{lead.source}</td>
                  <td className="px-4 py-3">
                    <ScoreBadge score={lead.fit} showLabel={false} size="sm" />
                  </td>
                  <td className="px-4 py-3">
                    <ScoreBadge score={lead.intent} showLabel={false} size="sm" />
                  </td>
                  <td className="px-4 py-3">
                    <ScoreBadge score={lead.deliverability} showLabel={false} size="sm" />
                  </td>
                  <td className="px-4 py-3">
                    <ScoreBadge score={lead.composite} size="sm" />
                  </td>
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{lead.next_action?.replaceAll('_', ' ') || '-'}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={lead.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="flex items-center justify-between text-sm text-slate-500">
          <span>
            Page {page} of {totalPages} ({total} total)
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
