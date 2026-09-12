import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { getErrorMessage } from '../services/api'
import { useToast } from '../context/ToastContext'

const SOURCES = ['website', 'email', 'whatsapp', 'referral', 'outbound']

export default function LeadNew() {
  const navigate = useNavigate()
  const { push } = useToast()
  const [mode, setMode] = useState('intake')

  const [source, setSource] = useState('website')
  const [rawText, setRawText] = useState('')
  const [contactEmail, setContactEmail] = useState('')
  const [contactPhone, setContactPhone] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [progressStep, setProgressStep] = useState('')
  const [error, setError] = useState('')

  const [manual, setManual] = useState({
    company: '', contact_name: '', role: '', email: '', phone: '',
    service: '', deliverables: '', location: '', target_dates: '', budget: '', deadline: '',
  })
  const [savingManual, setSavingManual] = useState(false)

  async function handleAnalyze(e) {
    e.preventDefault()
    setError('')
    if (!rawText.trim()) {
      setError('Please paste the raw enquiry text.')
      return
    }
    setAnalyzing(true)
    setProgressStep('Extracting structured fields...')
    try {
      setTimeout(() => setProgressStep('Deduplicating and researching account...'), 800)
      setTimeout(() => setProgressStep('Scoring and selecting next action...'), 1800)
      const res = await api.post('/leads/intake', {
        source,
        raw_text: rawText,
        contact_email: contactEmail || null,
        contact_phone: contactPhone || null,
      })
      push('Lead analyzed successfully', 'success')
      navigate(`/leads/${res.data.lead.id}`)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setAnalyzing(false)
      setProgressStep('')
    }
  }

  async function handleManualSubmit(e) {
    e.preventDefault()
    setError('')
    setSavingManual(true)
    try {
      const payload = {
        source: 'manual',
        company: manual.company || null,
        contact_name: manual.contact_name || null,
        role: manual.role || null,
        email: manual.email || null,
        phone: manual.phone || null,
        service: manual.service || null,
        deliverables: manual.deliverables || null,
        location: manual.location || null,
        target_dates: manual.target_dates || null,
        budget: manual.budget ? Number(manual.budget) : null,
        deadline: manual.deadline || null,
      }
      const res = await api.post('/leads', payload)
      push('Lead created', 'success')
      navigate(`/leads/${res.data.id}`)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSavingManual(false)
    }
  }

  const inputClass = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-xl font-semibold text-slate-900">New Lead</h1>

      <div className="flex gap-2 rounded-lg border border-slate-200 bg-white p-1 w-fit">
        <button
          onClick={() => setMode('intake')}
          className={`rounded-md px-4 py-1.5 text-sm font-medium ${mode === 'intake' ? 'bg-brand-600 text-white' : 'text-slate-600'}`}
        >
          Paste Enquiry
        </button>
        <button
          onClick={() => setMode('manual')}
          className={`rounded-md px-4 py-1.5 text-sm font-medium ${mode === 'manual' ? 'bg-brand-600 text-white' : 'text-slate-600'}`}
        >
          Manual Entry
        </button>
      </div>

      {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-600">{error}</p>}

      {mode === 'intake' ? (
        <form onSubmit={handleAnalyze} className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-600">Source</label>
              <select value={source} onChange={(e) => setSource(e.target.value)} className={inputClass}>
                {SOURCES.map((s) => (
                  <option key={s} value={s} className="capitalize">
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-600">Contact email (optional)</label>
              <input value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-600">Contact phone (optional)</label>
              <input value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} className={inputClass} />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-600">Raw enquiry (email / WhatsApp / website form text)</label>
            <textarea
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              rows={8}
              className={inputClass}
              placeholder="Paste the enquiry text here, in English, Urdu, or Roman Urdu..."
            />
          </div>
          <button
            type="submit"
            disabled={analyzing}
            className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {analyzing ? progressStep || 'Analyzing...' : 'Analyze Lead'}
          </button>
          {analyzing && (
            <div className="text-xs text-slate-400">
              Extract → Deduplicate → Research → Score → Next Action
            </div>
          )}
        </form>
      ) : (
        <form onSubmit={handleManualSubmit} className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {[
              ['company', 'Company'],
              ['contact_name', 'Contact Name'],
              ['role', 'Role'],
              ['email', 'Email'],
              ['phone', 'Phone'],
              ['service', 'Service'],
              ['deliverables', 'Deliverables'],
              ['location', 'Location'],
              ['target_dates', 'Target Date'],
              ['budget', 'Budget'],
              ['deadline', 'Deadline'],
            ].map(([key, label]) => (
              <div key={key}>
                <label className="mb-1 block text-sm font-medium text-slate-600">{label}</label>
                <input
                  value={manual[key]}
                  onChange={(e) => setManual((m) => ({ ...m, [key]: e.target.value }))}
                  className={inputClass}
                  type={key === 'budget' ? 'number' : 'text'}
                />
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-400">All fields are optional. We never guess a value you didn't provide.</p>
          <button
            type="submit"
            disabled={savingManual}
            className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {savingManual ? 'Saving...' : 'Create Lead'}
          </button>
        </form>
      )}
    </div>
  )
}
