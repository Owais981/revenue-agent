import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { getErrorMessage } from '../services/api'
import LoadingState from '../components/LoadingState'
import ErrorBanner from '../components/ErrorBanner'
import EmptyState from '../components/EmptyState'
import ClaimList from '../components/ClaimList'

export default function Research() {
  const [leads, setLeads] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [pack, setPack] = useState(null)
  const [loading, setLoading] = useState(true)
  const [packLoading, setPackLoading] = useState(false)
  const [error, setError] = useState('')

  async function loadLeads() {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/leads', { params: { page: 1, page_size: 50, sort: 'newest' } })
      setLeads(res.data.items)
      if (res.data.items.length > 0) setSelectedId(res.data.items[0].id)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLeads()
  }, [])

  useEffect(() => {
    if (!selectedId) return
    setPackLoading(true)
    api
      .get(`/leads/${selectedId}/research`)
      .then((res) => setPack(res.data))
      .catch(() => setPack(null))
      .finally(() => setPackLoading(false))
  }, [selectedId])

  if (loading) return <LoadingState />
  if (error) return <ErrorBanner message={error} onRetry={loadLeads} />

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-slate-900">Research</h1>
      {leads.length === 0 ? (
        <EmptyState title="No leads yet" subtitle="Research packs are generated automatically when a lead is analyzed." />
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm lg:col-span-1">
            <p className="mb-2 px-2 text-xs font-medium uppercase text-slate-400">Select a lead</p>
            <div className="max-h-[60vh] space-y-1 overflow-y-auto scrollbar-thin">
              {leads.map((l) => (
                <button
                  key={l.id}
                  onClick={() => setSelectedId(l.id)}
                  className={`block w-full rounded-lg px-3 py-2 text-left text-sm ${
                    selectedId === l.id ? 'bg-brand-50 text-brand-700' : 'hover:bg-slate-50 text-slate-600'
                  }`}
                >
                  {l.company || 'Unknown company'}
                  <span className="ml-2 text-xs text-slate-400 capitalize">{l.source}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-medium text-slate-800">Research Pack</h2>
              <Link to={`/leads/${selectedId}`} className="text-sm font-medium text-brand-600 hover:underline">
                Open lead
              </Link>
            </div>
            {packLoading ? (
              <LoadingState label="Loading research..." />
            ) : pack ? (
              <ClaimList claims={pack.claims} />
            ) : (
              <p className="text-sm text-slate-400">No research pack generated for this lead yet.</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
