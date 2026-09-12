import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api, { getErrorMessage } from '../services/api'
import { useToast } from '../context/ToastContext'
import LoadingState from '../components/LoadingState'
import ErrorBanner from '../components/ErrorBanner'
import ScoreBar from '../components/ScoreBar'
import ScoreBadge from '../components/ScoreBadge'
import StatusBadge from '../components/StatusBadge'
import FactorList from '../components/FactorList'
import ClaimList from '../components/ClaimList'

const ACTION_CATALOGUE = [
  'CALL_NOW', 'SEND_INTRO_EMAIL', 'SEND_CASE_STUDY', 'REQUEST_BRIEF_DETAIL',
  'ROUTE_TO_PROPOSAL_AGENT', 'CHECK_CAPACITY', 'FINANCE_HOLD', 'NURTURE', 'DISQUALIFY',
]

const LEAD_FIELDS = [
  ['service', 'Service'], ['deliverables', 'Deliverables'], ['location', 'Location'],
  ['target_dates', 'Dates'], ['budget', 'Budget'], ['deadline', 'Deadline'], ['language', 'Language'],
]

export default function LeadDetail() {
  const { id } = useParams()
  const { push } = useToast()
  const [lead, setLead] = useState(null)
  const [account, setAccount] = useState(null)
  const [score, setScore] = useState(null)
  const [research, setResearch] = useState(null)
  const [actions, setActions] = useState([])
  const [tab, setTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [analyzing, setAnalyzing] = useState(false)

  const [overrideFor, setOverrideFor] = useState(null)
  const [overrideType, setOverrideType] = useState('')
  const [overrideReason, setOverrideReason] = useState('')
  const [draftEdits, setDraftEdits] = useState({})

  const [outcomeStage, setOutcomeStage] = useState('contacted')
  const [outcomeValue, setOutcomeValue] = useState('')
  const [outcomeMargin, setOutcomeMargin] = useState('')
  const [outcomeReason, setOutcomeReason] = useState('')
  const [savingOutcome, setSavingOutcome] = useState(false)

  async function load() {
    setLoading(true)
    setError('')
    try {
      const leadRes = await api.get(`/leads/${id}`)
      setLead(leadRes.data)

      const [scoreRes, researchRes, actionsRes] = await Promise.allSettled([
        api.get(`/leads/${id}/score`),
        api.get(`/leads/${id}/research`),
        api.get(`/leads/${id}/actions`),
      ])
      if (scoreRes.status === 'fulfilled') setScore(scoreRes.value.data)
      if (researchRes.status === 'fulfilled') setResearch(researchRes.value.data)
      if (actionsRes.status === 'fulfilled') setActions(actionsRes.value.data)

      if (leadRes.data.account_id) {
        try {
          const accountRes = await api.get(`/accounts/${leadRes.data.account_id}`)
          setAccount(accountRes.data)
        } catch {
          /* account fetch is best-effort */
        }
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  async function handleAnalyze() {
    setAnalyzing(true)
    try {
      await api.post(`/leads/${id}/analyze`)
      push('Lead re-analyzed', 'success')
      await load()
    } catch (err) {
      push(getErrorMessage(err), 'error')
    } finally {
      setAnalyzing(false)
    }
  }

  async function handleApprove(actionId) {
    try {
      await api.post(`/leads/${id}/actions/${actionId}/approve`)
      push('Action approved', 'success')
      load()
    } catch (err) {
      push(getErrorMessage(err), 'error')
    }
  }

  async function handleReject(actionId) {
    try {
      await api.post(`/leads/${id}/actions/${actionId}/reject`)
      push('Action rejected', 'success')
      load()
    } catch (err) {
      push(getErrorMessage(err), 'error')
    }
  }

  async function handleSaveDraft(actionId) {
    try {
      await api.post(`/leads/${id}/actions/${actionId}/edit-draft`, { draft_artifact: draftEdits[actionId] })
      push('Draft updated', 'success')
      load()
    } catch (err) {
      push(getErrorMessage(err), 'error')
    }
  }

  async function handleOverride(actionId) {
    if (!overrideType || !overrideReason.trim()) {
      push('Choose a new action and explain why', 'error')
      return
    }
    try {
      await api.post(`/leads/${id}/actions/${actionId}/override`, {
        new_action_type: overrideType,
        reason: overrideReason,
      })
      push('Action overridden', 'success')
      setOverrideFor(null)
      setOverrideType('')
      setOverrideReason('')
      load()
    } catch (err) {
      push(getErrorMessage(err), 'error')
    }
  }

  async function handleOutcomeSubmit(e) {
    e.preventDefault()
    if (outcomeStage === 'lost' && !outcomeReason.trim()) {
      push('Loss reason is required', 'error')
      return
    }
    setSavingOutcome(true)
    try {
      await api.post(`/leads/${id}/outcome`, {
        stage: outcomeStage,
        won: outcomeStage === 'won' ? true : outcomeStage === 'lost' ? false : null,
        value: outcomeValue ? Number(outcomeValue) : null,
        margin: outcomeMargin ? Number(outcomeMargin) : null,
        reason: outcomeReason || null,
      })
      push('Outcome recorded', 'success')
      load()
    } catch (err) {
      push(getErrorMessage(err), 'error')
    } finally {
      setSavingOutcome(false)
    }
  }

  if (loading) return <LoadingState label="Loading lead..." />
  if (error) return <ErrorBanner message={error} onRetry={load} />
  if (!lead) return null

  const latestAction = actions[0]

  const TABS = [
    { key: 'overview', label: 'Overview' },
    { key: 'score', label: 'Score' },
    { key: 'research', label: 'Research' },
    { key: 'action', label: 'Next Action' },
    { key: 'outcome', label: 'Outcome' },
  ]

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/leads" className="text-sm text-brand-600 hover:underline">
            ← Back to leads
          </Link>
          <h1 className="mt-1 text-xl font-semibold text-slate-900">{account?.name || 'Unknown company'}</h1>
          <div className="mt-1 flex items-center gap-2">
            <StatusBadge status={lead.status} />
            {lead.ai_degraded && (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                AI unavailable — degraded mode
              </span>
            )}
          </div>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {analyzing ? 'Analyzing...' : 'Re-analyze Lead'}
        </button>
      </div>

      <div className="flex gap-1 overflow-x-auto rounded-lg border border-slate-200 bg-white p-1 w-fit">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`whitespace-nowrap rounded-md px-4 py-1.5 text-sm font-medium ${
              tab === t.key ? 'bg-brand-600 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 font-medium text-slate-800">Lead Information</h2>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              {LEAD_FIELDS.map(([key, label]) => (
                <div key={key}>
                  <dt className="text-slate-400">{label}</dt>
                  <dd className="font-medium text-slate-800">{lead[key] ?? <span className="text-slate-300">Not provided</span>}</dd>
                </div>
              ))}
              <div>
                <dt className="text-slate-400">Source</dt>
                <dd className="font-medium capitalize text-slate-800">{lead.source}</dd>
              </div>
            </dl>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 font-medium text-slate-800">Raw Enquiry</h2>
            <p className="whitespace-pre-wrap text-sm text-slate-600">{lead.raw_text || 'No raw text captured.'}</p>
          </div>
        </div>
      )}

      {tab === 'score' && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 font-medium text-slate-800">Score Breakdown</h2>
            {score ? (
              <div className="space-y-4">
                <ScoreBar label="Fit" value={score.fit} />
                <ScoreBar label="Intent" value={score.intent} />
                <ScoreBar label="Deliverability" value={score.deliverability} />
                <div className="border-t border-slate-100 pt-3">
                  <ScoreBar label="Composite" value={score.composite} />
                </div>
                {score.degraded && <p className="text-xs text-amber-600">Computed in degraded mode: {score.degraded}</p>}
              </div>
            ) : (
              <p className="text-sm text-slate-400">No score computed yet. Click "Re-analyze Lead".</p>
            )}
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 font-medium text-slate-800">Why this score?</h2>
            {score ? <FactorList factors={score.factors} /> : <p className="text-sm text-slate-400">No factors yet.</p>}
          </div>
        </div>
      )}

      {tab === 'research' && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 font-medium text-slate-800">Research Pack</h2>
          {research ? <ClaimList claims={research.claims} /> : <p className="text-sm text-slate-400">No research pack yet.</p>}
        </div>
      )}

      {tab === 'action' && (
        <div className="space-y-4">
          {latestAction ? (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-400">Recommended Action</p>
                  <p className="text-lg font-semibold text-slate-900">{latestAction.action_type.replaceAll('_', ' ')}</p>
                </div>
                <StatusBadge status={latestAction.status} />
              </div>
              <p className="mt-3 text-sm text-slate-600">
                <span className="font-medium text-slate-800">Reason: </span>
                {latestAction.reason}
              </p>
              <p className="mt-1 text-sm text-slate-500">Confidence: {Math.round((latestAction.confidence || 0) * 100)}%</p>
              {latestAction.evidence?.length > 0 && (
                <ul className="mt-2 list-disc pl-5 text-sm text-slate-500">
                  {latestAction.evidence.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              )}

              {latestAction.draft_artifact !== null && latestAction.draft_artifact !== undefined && (
                <div className="mt-4">
                  <p className="mb-1 text-sm font-medium text-slate-700">Draft (requires human approval before sending)</p>
                  <textarea
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    rows={5}
                    value={draftEdits[latestAction.id] ?? latestAction.draft_artifact ?? ''}
                    onChange={(e) => setDraftEdits((d) => ({ ...d, [latestAction.id]: e.target.value }))}
                  />
                  <button
                    onClick={() => handleSaveDraft(latestAction.id)}
                    className="mt-2 rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
                  >
                    Save edited draft
                  </button>
                </div>
              )}

              <div className="mt-5 flex flex-wrap gap-2">
                <button
                  onClick={() => handleApprove(latestAction.id)}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                >
                  Approve
                </button>
                <button
                  onClick={() => handleReject(latestAction.id)}
                  className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700"
                >
                  Reject
                </button>
                <button
                  onClick={() => setOverrideFor(overrideFor === latestAction.id ? null : latestAction.id)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Override
                </button>
              </div>

              {overrideFor === latestAction.id && (
                <div className="mt-4 space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-medium text-slate-700">Why is this score/action wrong?</p>
                  <select
                    value={overrideType}
                    onChange={(e) => setOverrideType(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="">Choose new action</option>
                    {ACTION_CATALOGUE.map((a) => (
                      <option key={a} value={a}>
                        {a.replaceAll('_', ' ')}
                      </option>
                    ))}
                  </select>
                  <textarea
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    rows={3}
                    placeholder="Explain why..."
                    value={overrideReason}
                    onChange={(e) => setOverrideReason(e.target.value)}
                  />
                  <button
                    onClick={() => handleOverride(latestAction.id)}
                    className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
                  >
                    Submit override
                  </button>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-400">No action recommended yet.</p>
          )}

          {actions.length > 1 && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="mb-3 font-medium text-slate-800">Action History</h3>
              <div className="space-y-2">
                {actions.slice(1).map((a) => (
                  <div key={a.id} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2 text-sm">
                    <span className="font-medium text-slate-700">{a.action_type.replaceAll('_', ' ')}</span>
                    <StatusBadge status={a.status} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'outcome' && (
        <form onSubmit={handleOutcomeSubmit} className="max-w-lg space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="font-medium text-slate-800">Record Outcome</h2>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-600">Stage</label>
            <select
              value={outcomeStage}
              onChange={(e) => setOutcomeStage(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {['contacted', 'qualified', 'proposal_sent', 'won', 'lost'].map((s) => (
                <option key={s} value={s}>
                  {s.replaceAll('_', ' ')}
                </option>
              ))}
            </select>
          </div>
          {outcomeStage === 'won' && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-600">Final Value</label>
                <input
                  type="number"
                  value={outcomeValue}
                  onChange={(e) => setOutcomeValue(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-600">Final Margin</label>
                <input
                  type="number"
                  value={outcomeMargin}
                  onChange={(e) => setOutcomeMargin(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
          )}
          {outcomeStage === 'lost' && (
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-600">Loss Reason (required)</label>
              <input
                value={outcomeReason}
                onChange={(e) => setOutcomeReason(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          )}
          <button
            type="submit"
            disabled={savingOutcome}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {savingOutcome ? 'Saving...' : 'Save Outcome'}
          </button>
        </form>
      )}
    </div>
  )
}
