import { useEffect, useState } from 'react'
import api, { getErrorMessage } from '../services/api'
import LoadingState from '../components/LoadingState'
import ErrorBanner from '../components/ErrorBanner'
import EmptyState from '../components/EmptyState'

export default function Accounts() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/accounts', { params: { page: 1, page_size: 50 } })
      setItems(res.data.items)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  if (loading) return <LoadingState />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-slate-900">Accounts</h1>
      {items.length === 0 ? (
        <EmptyState title="No accounts yet" subtitle="Accounts are created automatically when leads come in." />
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
                <th className="px-4 py-2 font-medium">Name</th>
                <th className="px-4 py-2 font-medium">Domain</th>
                <th className="px-4 py-2 font-medium">Industry</th>
                <th className="px-4 py-2 font-medium">Tier</th>
                <th className="px-4 py-2 font-medium">Credit Flag</th>
                <th className="px-4 py-2 font-medium">Owner</th>
              </tr>
            </thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-800">{a.name}</td>
                  <td className="px-4 py-3 text-slate-500">{a.domain || '-'}</td>
                  <td className="px-4 py-3 capitalize text-slate-500">{a.industry || '-'}</td>
                  <td className="px-4 py-3 capitalize text-slate-500">{a.tier || '-'}</td>
                  <td className="px-4 py-3">
                    {a.credit_flag ? (
                      <span className="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-700">Overdue</span>
                    ) : (
                      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">Clear</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-500">{a.owner || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
