import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { getErrorMessage } from '../services/api'
import KpiCard from '../components/KpiCard'
import LoadingState from '../components/LoadingState'
import ErrorBanner from '../components/ErrorBanner'
import ScoreBadge from '../components/ScoreBadge'
import StatusBadge from '../components/StatusBadge'
import EmptyState from '../components/EmptyState'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const [statsRes, leadsRes] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/leads', { params: { page: 1, page_size: 8, sort: 'composite_desc' } }),
      ])
      setStats(statsRes.data)
      setLeads(leadsRes.data.items)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  if (loading) return <LoadingState label="Loading dashboard..." />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  const kpis = [
    { label: 'Total Leads', value: stats.total_leads },
    { label: 'New Leads', value: stats.new_leads },
    { label: 'Qualified', value: stats.qualified_leads },
    { label: 'High Priority', value: stats.high_priority_leads, accent: 'text-rose-600' },
    { label: 'Nurture', value: stats.nurture, accent: 'text-amber-600' },
    { label: 'Finance Holds', value: stats.finance_holds, accent: 'text-rose-600' },
    { label: 'Won', value: stats.won, accent: 'text-emerald-600' },
    { label: 'Lost', value: stats.lost, accent: 'text-slate-500' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900">Dashboard</h1>
        <Link
          to="/leads/new"
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          + New Lead
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {kpis.map((k) => (
          <KpiCard key={k.label} {...k} />
        ))}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
          <h2 className="font-medium text-slate-800">Top Worklist</h2>
          <Link to="/leads" className="text-sm font-medium text-brand-600 hover:underline">
            View all
          </Link>
        </div>
        {leads.length === 0 ? (
          <EmptyState title="No leads yet" subtitle="Create your first lead to see it scored here." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
                  <th className="px-4 py-2 font-medium">Company</th>
                  <th className="px-4 py-2 font-medium">Source</th>
                  <th className="px-4 py-2 font-medium">Composite</th>
                  <th className="px-4 py-2 font-medium">Next Action</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead) => (
                  <tr
                    key={lead.id}
                    className="cursor-pointer border-b border-slate-50 last:border-0 hover:bg-slate-50"
                    onClick={() => (window.location.href = `/leads/${lead.id}`)}
                  >
                    <td className="px-4 py-3 font-medium text-slate-800">{lead.company || 'Unknown company'}</td>
                    <td className="px-4 py-3 capitalize text-slate-500">{lead.source}</td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={lead.composite} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-slate-600">{lead.next_action?.replaceAll('_', ' ') || '-'}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={lead.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
