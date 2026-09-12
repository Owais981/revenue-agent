import { useEffect, useState } from 'react'
import api, { getErrorMessage } from '../services/api'
import { useToast } from '../context/ToastContext'
import LoadingState from '../components/LoadingState'
import ErrorBanner from '../components/ErrorBanner'

const NUMBER_FIELDS = [
  ['fit_weight', 'Fit Weight', '0-1'],
  ['intent_weight', 'Intent Weight', '0-1'],
  ['deliverability_weight', 'Deliverability Weight', '0-1'],
  ['proposal_threshold', 'Proposal Threshold', '0-100'],
  ['nurture_threshold', 'Nurture Threshold', '0-100'],
  ['min_project_value', 'Minimum Project Value', 'currency'],
  ['confidence_threshold', 'Confidence Threshold', '0-1'],
]

export default function Settings() {
  const { push } = useToast()
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/settings/scoring')
      setConfig(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    try {
      const res = await api.put('/settings/scoring', {
        fit_weight: Number(config.fit_weight),
        intent_weight: Number(config.intent_weight),
        deliverability_weight: Number(config.deliverability_weight),
        proposal_threshold: Number(config.proposal_threshold),
        nurture_threshold: Number(config.nurture_threshold),
        min_project_value: Number(config.min_project_value),
        confidence_threshold: Number(config.confidence_threshold),
      })
      setConfig(res.data)
      push('Scoring settings updated. Weights normalize to 100% automatically.', 'success')
    } catch (err) {
      push(getErrorMessage(err), 'error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <LoadingState />
  if (error) return <ErrorBanner message={error} onRetry={load} />
  if (!config) return null

  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-xl font-semibold text-slate-900">Scoring Settings</h1>
      <p className="text-sm text-slate-500">
        These weights and thresholds drive the deterministic scoring engine. Changes take effect immediately — no
        code deploy required.
      </p>

      <form onSubmit={handleSave} className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {NUMBER_FIELDS.map(([key, label, hint]) => (
            <div key={key}>
              <label className="mb-1 block text-sm font-medium text-slate-600">
                {label} <span className="text-slate-400">({hint})</span>
              </label>
              <input
                type="number"
                step="0.01"
                value={config[key]}
                onChange={(e) => setConfig((c) => ({ ...c, [key]: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          ))}
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-slate-600">Target Verticals</p>
          <div className="flex flex-wrap gap-2">
            {config.target_verticals.map((v) => (
              <span key={v} className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-medium text-brand-700">
                {v}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="mb-2 text-sm font-medium text-slate-600">Capability Set</p>
          <div className="flex flex-wrap gap-2">
            {config.capability_set.map((v) => (
              <span key={v} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                {v}
              </span>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </form>
    </div>
  )
}
